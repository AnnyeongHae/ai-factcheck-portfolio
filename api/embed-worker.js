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
const VOYAGE_MODEL = 'voyage-multilingual-2';
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

  const client = await pool.connect();
  try {
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
      // Check total remaining
      const countRes = await client.query('SELECT COUNT(*) FROM raw_trends_inbox WHERE embedding IS NULL;');
      return res.status(200).json({
        success: true,
        message: 'No unembedded items found.',
        processed_count: 0,
        merged_count: 0,
        remaining_unembedded: parseInt(countRes.rows[0].count, 10),
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

    // 4. Batch UPDATE embeddings into Aiven DB
    await client.query('BEGIN');

    // Build parameterized multi-row update
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      const embVector = embeddings[i].embedding;
      const vectorStr = `[${embVector.join(',')}]`;

      await client.query(
        `UPDATE raw_trends_inbox 
         SET embedding = $1::vector, updated_at = NOW() 
         WHERE id = $2;`,
        [vectorStr, item.id]
      );
    }

    // 5. Automatic Semantic Deduplication Check on recently updated items
    // Finds pairs with cosine similarity >= 0.78 within the past 7 days
    const dedupQuery = `
      SELECT a.id as primary_id, a.title as primary_title, a.raw_payload as primary_payload,
             b.id as dup_id, b.title as dup_title, b.raw_payload as dup_payload,
             b.source_platform as dup_platform, b.source_url as dup_url,
             (1 - (a.embedding <=> b.embedding)) as similarity
      FROM raw_trends_inbox a
      JOIN raw_trends_inbox b ON a.id < b.id
        AND a.created_at >= NOW() - INTERVAL '7 days'
        AND b.created_at >= NOW() - INTERVAL '7 days'
        AND (a.triage_status IS NULL OR a.triage_status != 'archived')
        AND (b.triage_status IS NULL OR b.triage_status != 'archived')
        AND (a.embedding <=> b.embedding) <= $1
      ORDER BY similarity DESC;
    `;
    const distanceThreshold = 1.0 - SIMILARITY_THRESHOLD; // <= 0.22
    const { rows: dupPairs } = await client.query(dedupQuery, [distanceThreshold]);

    let mergedCount = 0;
    const archivedIds = new Set();

    for (const pair of dupPairs) {
      if (archivedIds.has(pair.primary_id) || archivedIds.has(pair.dup_id)) {
        continue; // Already processed in this batch
      }

      // Merge secondary (dup_id) into primary (primary_id)
      const primaryPayload = pair.primary_payload || {};
      const dupPayload = pair.dup_payload || {};
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

      // Update primary with enriched multi-sources
      await client.query(
        `UPDATE raw_trends_inbox 
         SET raw_payload = $1, updated_at = NOW() 
         WHERE id = $2;`,
        [JSON.stringify(primaryPayload), pair.primary_id]
      );

      // Archive duplicate item so it doesn't clutter frontend
      await client.query(
        `UPDATE raw_trends_inbox 
         SET triage_status = 'archived', 
             curation_tier = 'duplicate',
             updated_at = NOW() 
         WHERE id = $1;`,
        [pair.dup_id]
      );

      archivedIds.add(pair.dup_id);
      mergedCount++;
    }

    await client.query('COMMIT');

    // 6. Count remaining unembedded
    const remainingRes = await client.query('SELECT COUNT(*) FROM raw_trends_inbox WHERE embedding IS NULL;');
    const remainingUnembedded = parseInt(remainingRes.rows[0].count, 10);

    return res.status(200).json({
      success: true,
      model: VOYAGE_MODEL,
      processed_count: items.length,
      merged_duplicates_count: mergedCount,
      remaining_unembedded: remainingUnembedded,
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
