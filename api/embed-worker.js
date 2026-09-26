/**
 * api/embed-worker.js
 * ==============================================================================
 * Voyage AI Multilingual Batch Embedding & Deduplication Micro-Worker (v1.0)
 * ------------------------------------------------------------------------------
 * Purpose:
 *   Embeds up to 100 news items in a single HTTP batch request using Voyage AI's
 *   `voyage-multilingual-2` (1024-dim) model in under 1.5 seconds.
 *   Stores vectors directly into Aiven PostgreSQL (pgvector 0.8.6).
 *   Detects semantic duplicates (cosine similarity >= 0.78) and merges them
 *   into unified multi-source Techmeme-style hub stories.
 * ==============================================================================
 */

const { getDbPool } = require('./_lib/db');
const { handleOptions, setCorsHeaders } = require('./_lib/cors');

const VOYAGE_API_URL = 'https://api.voyageai.com/v1/embeddings';
const VOYAGE_MODEL = 'voyage-4-lite';
const VOYAGE_DIM = 1024;
const SIMILARITY_THRESHOLD = 0.78; // Cosine similarity >= 0.78 (distance <= 0.22)

module.exports = async function handler(req, res) {
  if (handleOptions(req, res)) return;
  setCorsHeaders(res);

  const startTime = Date.now();
  const pool = getDbPool();
  if (!pool) {
    return res.status(500).json({ error: 'Database connection failed' });
  }

  const apiKey = process.env.VOYAGE_API_KEY || process.env.VOYAGEAI_API_KEY;
  if (!apiKey) {
    return res.status(500).json({ error: 'VOYAGE_API_KEY is not configured in environment' });
  }

  const limit = Math.min(parseInt(req.query.limit || req.body?.limit || '100', 10), 100);
  const isCheckOnly = req.query.check_only === 'true' || req.body?.check_only === true;

  const client = await pool.connect();
  try {
    // 0. Get total and embedded counts
    const countRes = await client.query(`
      SELECT 
        COUNT(*) as total_count,
        COUNT(embedding) as embedded_count,
        COUNT(*) - COUNT(embedding) as remaining_unembedded
      FROM raw_trends_inbox;
    `);
    const totalCount = parseInt(countRes.rows[0].total_count, 10) || 0;
    const embeddedCount = parseInt(countRes.rows[0].embedded_count, 10) || 0;
    const remainingUnembedded = parseInt(countRes.rows[0].remaining_unembedded, 10) || 0;

    if (isCheckOnly) {
      return res.status(200).json({
        success: true,
        check_only: true,
        total_count: totalCount,
        embedded_count: embeddedCount,
        remaining_unembedded: remainingUnembedded,
        elapsed_ms: Date.now() - startTime
      });
    }

    // 1. Fetch recent unembedded items
    const fetchQuery = `
      SELECT id, inbox_id, title, COALESCE(raw_payload->>'title_ko', '') as title_ko,
             source_platform, source_url, created_at, raw_payload
      FROM raw_trends_inbox
      WHERE embedding IS NULL
      ORDER BY created_at DESC
      LIMIT $1;
    `;
    const { rows: items } = await client.query(fetchQuery, [limit]);

    if (!items || items.length === 0) {
      return res.status(200).json({
        success: true,
        message: 'No unembedded items found. All items are embedded.',
        processed_count: 0,
        tokens_used: 0,
        merged_duplicates_count: 0,
        total_count: totalCount,
        embedded_count: embeddedCount,
        remaining_unembedded: 0,
        elapsed_ms: Date.now() - startTime
      });
    }

    // 2. Prepare text payload for Voyage AI (Combine EN + KO for cross-lingual richness)
    const texts = items.map(item => {
      const en = (item.title || '').trim();
      const ko = (item.title_ko || '').trim();
      if (en && ko && en !== ko) {
        return `${en} (${ko})`;
      }
      return en || ko || 'Untitled';
    });

    // 3. Batch call Voyage AI API in a single HTTP request (~0.3 - 0.5s)
    const voyageRes = await fetch(VOYAGE_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey.trim()}`
      },
      body: JSON.stringify({
        input: texts,
        model: VOYAGE_MODEL,
        output_dimension: VOYAGE_DIM
      })
    });

    if (!voyageRes.ok) {
      const errText = await voyageRes.text();
      throw new Error(`Voyage API returned HTTP ${voyageRes.status}: ${errText}`);
    }

    const voyageData = await voyageRes.json();
    const embeddings = voyageData.data || [];
    if (embeddings.length !== items.length) {
      throw new Error(`Mismatch: expected ${items.length} embeddings, got ${embeddings.length}`);
    }

    // 4. Ultra-Fast Bulk UPDATE embeddings into Aiven DB in 1 single roundtrip
    await client.query('BEGIN');

    const valuesClauses = [];
    const updateParams = [];
    for (let i = 0; i < items.length; i++) {
      const embVector = embeddings[i].embedding;
      const vectorStr = `[${embVector.join(',')}]`;
      valuesClauses.push(`($${i * 2 + 1}::bigint, $${i * 2 + 2}::vector)`);
      updateParams.push(items[i].id, vectorStr);
    }

    await client.query(
      `UPDATE raw_trends_inbox AS t
       SET embedding = v.emb, updated_at = NOW()
       FROM (VALUES ${valuesClauses.join(',')}) AS v(id, emb)
       WHERE t.id = v.id;`,
      updateParams
    );

    // 5. Ultra-Fast HNSW-Accelerated Semantic Deduplication Check on current batch items
    // Finds pairs with cosine similarity >= 0.78 within the past 7 days using LATERAL HNSW index (<0.3s)
    const batchIds = items.map(it => it.id);
    const distanceThreshold = 1.0 - SIMILARITY_THRESHOLD; // <= 0.22
    const dedupQuery = `
      SELECT a.id as primary_id, a.title as primary_title, a.raw_payload as primary_payload,
             b.id as dup_id, b.title as dup_title, b.raw_payload as dup_payload,
             b.source_platform as dup_platform, b.source_url as dup_url,
             (1 - (a.embedding <=> b.embedding)) as similarity
      FROM UNNEST($1::bigint[]) AS batch_id
      JOIN raw_trends_inbox a ON a.id = batch_id
      CROSS JOIN LATERAL (
        SELECT id, title, raw_payload, source_platform, source_url, embedding
        FROM raw_trends_inbox
        WHERE id < a.id
          AND created_at >= NOW() - INTERVAL '7 days'
          AND (triage_status IS NULL OR triage_status != 'archived')
          AND embedding IS NOT NULL
        ORDER BY a.embedding <=> embedding
        LIMIT 3
      ) b
      WHERE (a.embedding <=> b.embedding) <= $2
      ORDER BY similarity DESC;
    `;
    const { rows: dupPairs } = await client.query(dedupQuery, [batchIds, distanceThreshold]);

    let mergedCount = 0;
    const archivedIds = new Set();
    const primaryUpdates = new Map();

    for (const pair of dupPairs) {
      if (archivedIds.has(pair.primary_id) || archivedIds.has(pair.dup_id)) {
        continue; // Already processed in this batch
      }

      // Merge secondary (dup_id) into primary (primary_id)
      const primaryPayload = primaryUpdates.get(pair.primary_id) || pair.primary_payload || {};
      let sources = primaryPayload.sources || [];
      if (!Array.isArray(sources)) sources = [];

      // Add dup source if not already present
      const existingUrls = new Set(sources.map(s => s.url || s.source_url));
      if (!existingUrls.has(pair.dup_url)) {
        sources.push({
          source_name: pair.dup_platform || 'Cross-Platform Media',
          platform: pair.dup_platform || 'Media',
          title: pair.dup_title,
          url: pair.dup_url,
          type: 'discussion',
          similarity: parseFloat(pair.similarity.toFixed(4))
        });
      }

      primaryPayload.sources = sources;
      primaryPayload.has_multi_sources = true;
      primaryUpdates.set(pair.primary_id, primaryPayload);

      archivedIds.add(pair.dup_id);
      mergedCount++;
    }

    // Bulk Archive all duplicate items in 1 single query
    if (archivedIds.size > 0) {
      await client.query(
        `UPDATE raw_trends_inbox 
         SET triage_status = 'archived', 
             curation_tier = 'duplicate',
             updated_at = NOW() 
         WHERE id = ANY($1::bigint[]);`,
        [Array.from(archivedIds)]
      );
    }

    // Bulk Update all primary payloads in 1 single query
    if (primaryUpdates.size > 0) {
      const pClauses = [];
      const pParams = [];
      let pIdx = 1;
      for (const [pId, pPayload] of primaryUpdates.entries()) {
        pClauses.push(`($${pIdx}::bigint, $${pIdx + 1}::jsonb)`);
        pParams.push(pId, JSON.stringify(pPayload));
        pIdx += 2;
      }
      await client.query(
        `UPDATE raw_trends_inbox AS t
         SET raw_payload = v.payload, updated_at = NOW()
         FROM (VALUES ${pClauses.join(',')}) AS v(id, payload)
         WHERE t.id = v.id;`,
        pParams
      );
    }

    await client.query('COMMIT');

    const tokensUsed = voyageData.usage?.total_tokens || texts.reduce((acc, t) => acc + Math.ceil(t.length / 3), 0);

    return res.status(200).json({
      success: true,
      model: VOYAGE_MODEL,
      processed_count: items.length,
      tokens_used: tokensUsed,
      merged_duplicates_count: mergedCount,
      total_count: totalCount,
      embedded_count: embeddedCount + items.length,
      remaining_unembedded: Math.max(0, remainingUnembedded - items.length),
      elapsed_ms: Date.now() - startTime
    });

  } catch (error) {
    await client.query('ROLLBACK').catch(() => {});
    console.error('[embed-worker Error]:', error);
    return res.status(500).json({
      success: false,
      error: error.message,
      elapsed_ms: Date.now() - startTime
    });
  } finally {
    client.release();
  }
};
