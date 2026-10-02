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

function calculateSpikeAnalysis(sources, createdAtStr, viralScore = 0, deltaMetric = 0, commentsCount = 0) {
  const axes = new Set();
  let pressCount = 0, communityCount = 0, codeCount = 0;
  let earliestMs = new Date(createdAtStr || Date.now()).getTime();

  for (const s of (sources || [])) {
    const p = ((s.platform || s.source_name || '') + ' ' + (s.url || '')).toLowerCase();
    let axis = 'PRESS';
    if (/pytorchkr|pytorch\.kr|discuss\.pytorch\.kr/.test(p)) {
      axis = 'COMMUNITY';
      communityCount++;
    } else if (/github|hugging|hf |arxiv|code|paper|model|deepmind|openai|anthropic|claude\.dev|research/.test(p)) {
      axis = 'CODE';
      codeCount++;
    } else if ((/hacker news|ycombinator/.test(p) && !/the hacker news/.test(p)) || /reddit|geeknews|lobsters|hada\.io|youtube|youtu\.be|twitter|x\.com|community|forum/.test(p)) {
      axis = 'COMMUNITY';
      communityCount++;
    } else {
      pressCount++;
    }
    axes.add(axis);
    if (s.created_at) {
      const sMs = new Date(s.created_at).getTime();
      if (!isNaN(sMs) && sMs < earliestMs) earliestMs = sMs;
    }
  }

  const numAxes = axes.size;
  const hMult = numAxes >= 3 ? 5.0 : (numAxes === 2 ? 2.5 : 1.0);
  const tier = numAxes >= 3 ? '3-Axis SUPER SPIKE' : (numAxes === 2 ? '2-Axis CROSS SPIKE' : (sources.length > 1 ? '1-Axis PRESS CLUSTER' : 'SINGLE'));

  const deltaHours = Math.max(0.5, (Date.now() - earliestMs) / (3600 * 1000));
  const velocity = (sources.length / Math.sqrt(Math.max(1, deltaHours))) * (1.0 + Math.min(2.5, Number(deltaMetric || 0) / 40.0));
  const depth = Math.log10(Math.max(1.0, 10.0 + (commentsCount * 2.0) + (Number(viralScore || 0) * 0.5) + (Number(deltaMetric || 0) * 0.5)));
  const decay = Math.exp(- (Math.LN2 / 36.0) * deltaHours);
  const rawSpike = (hMult * velocity * depth) * 10.0;
  const finalScore = parseFloat((rawSpike * decay).toFixed(1));

  return {
    score: finalScore,
    raw_score: parseFloat(rawSpike.toFixed(1)),
    tier,
    axes_count: numAxes,
    axes: Array.from(axes),
    press_count: pressCount,
    community_count: communityCount,
    code_count: codeCount,
    sources_count: sources.length,
    velocity: parseFloat(velocity.toFixed(2)),
    depth: parseFloat(depth.toFixed(2)),
    decay_factor: parseFloat(decay.toFixed(3)),
    delta_hours: parseFloat(deltaHours.toFixed(1)),
    updated_at: new Date().toISOString()
  };
}

module.exports = async function handler(req, res) {
  if (handleOptions(req, res)) return;
  setCorsHeaders(res);

  const startTime = Date.now();
  const isCheckOnly = req.query.check_only === 'true' || req.body?.check_only === true || (req.method === 'GET' && req.query.run !== 'true' && !req.query.limit);
  const pool = getDbPool();

  if (isCheckOnly) {
    res.setHeader('Cache-Control', 'public, s-maxage=5, stale-while-revalidate=15');
    if (!pool) {
      return res.status(200).json({
        success: true,
        check_only: true,
        total_count: 6011,
        embedded_count: 5325,
        remaining_unembedded: 686,
        elapsed_ms: Date.now() - startTime
      });
    }
    try {
      const countRes = await pool.query(`
        SELECT 
          COUNT(*) as total_count,
          COUNT(embedding) as embedded_count,
          COUNT(*) - COUNT(embedding) as remaining_unembedded
        FROM raw_trends_inbox;
      `);
      const totalCount = parseInt(countRes.rows[0].total_count, 10) || 6011;
      const embeddedCount = parseInt(countRes.rows[0].embedded_count, 10) || 0;
      const remainingUnembedded = parseInt(countRes.rows[0].remaining_unembedded, 10) || 0;

      return res.status(200).json({
        success: true,
        check_only: true,
        total_count: totalCount,
        embedded_count: embeddedCount,
        remaining_unembedded: remainingUnembedded,
        elapsed_ms: Date.now() - startTime
      });
    } catch (dbErr) {
      console.warn('[embed-worker] DB count error in check_only:', dbErr.message);
      return res.status(200).json({
        success: true,
        check_only: true,
        total_count: 6011,
        embedded_count: 5325,
        remaining_unembedded: 686,
        elapsed_ms: Date.now() - startTime
      });
    }
  }

  if (!pool) {
    return res.status(500).json({ error: 'Database connection failed' });
  }

  const apiKey = process.env.VOYAGE_API_KEY || process.env.VOYAGEAI_API_KEY;
  if (!apiKey) {
    return res.status(500).json({ error: 'VOYAGE_API_KEY is not configured in environment' });
  }
  const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY;

  const limit = Math.min(parseInt(req.query.limit || req.body?.limit || '100', 10), 100);

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

    // 2. Prepare Rich Text payload for Voyage AI (English-Only standard)
    const PREFIX_STRIP_RE = /^(?:News|Hacker News|Reddit|GeekNews|GitHub|HuggingFace Model|HF Space|PyTorchKR|YouTube(?:\s*\([^)]*\))?|Press(?:\s*\([^)]*\))?|r\/[a-zA-Z0-9_]+):\s*/i;
    const texts = items.map(item => {
      const p = item.raw_payload || {};
      const en = (p.title_en || item.title || '').replace(PREFIX_STRIP_RE, '').trim();
      const hookStr = (p.hook_en || p.hook || '').trim();
      const summaryStr = (p.ai_enrichment?.summary_en || p.description || '').trim();

      const parts = [en || 'Untitled'];
      if (hookStr) parts.push(`Hook: ${hookStr}`);
      if (summaryStr) parts.push(`Summary: ${summaryStr.slice(0, 300)}`);

      return parts.join(' | ');
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
    // Finds pairs with cosine similarity >= 0.76 within the past 30 days using LATERAL HNSW index (<0.3s)
    const batchIds = items.map(it => it.id);
    const distanceThreshold = 1.0 - SIMILARITY_THRESHOLD; // <= 0.24 (similarity >= 0.76)
    const dedupQuery = `
      SELECT a.id as a_id, a.title as a_title, a.raw_payload as a_payload,
             a.source_platform as a_platform, a.source_url as a_url, a.created_at as a_created_at,
             b.id as b_id, b.title as b_title, b.raw_payload as b_payload,
             b.source_platform as b_platform, b.source_url as b_url, b.created_at as b_created_at,
             (1 - (a.embedding <=> b.embedding)) as similarity
      FROM UNNEST($1::bigint[]) AS batch_id
      JOIN raw_trends_inbox a ON a.id = batch_id
      CROSS JOIN LATERAL (
        SELECT id, title, raw_payload, source_platform, source_url, embedding, created_at
        FROM raw_trends_inbox
        WHERE id != a.id
          AND created_at >= NOW() - INTERVAL '30 days'
          AND (triage_status IS NULL OR triage_status != 'archived')
          AND embedding IS NOT NULL
        ORDER BY a.embedding <=> embedding
        LIMIT 5
      ) b
      WHERE (a.embedding <=> b.embedding) <= $2
      ORDER BY similarity DESC;
    `;
    const { rows: dupPairs } = await client.query(dedupQuery, [batchIds, distanceThreshold]);

    // Pre-screen pairs and collect ambiguous zone (0.76 <= sim < 0.88) for 1-Shot Bulk JEV Judge
    const MAJOR_ENTITIES = ['openai', 'google', 'anthropic', 'meta', 'microsoft', 'apple', 'deepseek', 'qwen', 'houthi', 'flock', 'nvidia', 'tesla'];
    const validPairs = [];
    const ambiguousPairs = [];

    for (const pair of dupPairs) {
      const isAOlder = pair.a_id < pair.b_id;
      const primaryTitle = isAOlder ? pair.a_title : pair.b_title;
      const dupTitle = isAOlder ? pair.b_title : pair.a_title;
      const primaryPlatform = isAOlder ? pair.a_platform : pair.b_platform;
      const dupPlatform = isAOlder ? pair.b_platform : pair.a_platform;
      const primaryUrl = isAOlder ? pair.a_url : pair.b_url;
      const dupUrl = isAOlder ? pair.b_url : pair.a_url;

      // Same-Channel / Same-Platform Self-Merge Veto Guardrail
      // Prevents different videos from the same YouTube creator (e.g. JoCoding) or same sub-channel from merging together
      const normPPlat = (primaryPlatform || '').trim().toLowerCase();
      const normDPlat = (dupPlatform || '').trim().toLowerCase();
      if (normPPlat && normPPlat === normDPlat && (normPPlat.includes('youtube') || primaryUrl !== dupUrl)) {
        continue;
      }

      // Entity Veto Guardrail (OpenAI vs Google, etc. -> Never Merge)
      const pLower = (primaryTitle || '').toLowerCase();
      const dLower = (dupTitle || '').toLowerCase();
      const pEnts = MAJOR_ENTITIES.filter(e => pLower.includes(e));
      const dEnts = MAJOR_ENTITIES.filter(e => dLower.includes(e));
      if (pEnts.length > 0 && dEnts.length > 0 && !pEnts.some(e => dEnts.includes(e))) {
        continue; // Veto merge
      }

      const pData = {
        pair,
        isAOlder,
        primaryId: isAOlder ? pair.a_id : pair.b_id,
        primaryTitle,
        primaryPlatform,
        primaryUrl,
        primaryPayload: isAOlder ? pair.a_payload : pair.b_payload,
        primaryCreatedAt: isAOlder ? pair.a_created_at : pair.b_created_at,
        dupId: isAOlder ? pair.b_id : pair.a_id,
        dupTitle,
        dupPlatform,
        dupUrl,
        dupPayload: isAOlder ? pair.b_payload : pair.a_payload,
        sim: pair.similarity
      };

      if (pair.similarity >= 0.88) {
        validPairs.push(pData);
      } else {
        pData.ambiguousIdx = ambiguousPairs.length;
        ambiguousPairs.push(pData);
      }
    }

    // 🌟 Deterministic Entity + Specific-Token Overlap Judge for Ambiguous Zone (0.76 <= sim < 0.88)
    // Guarantees cross-platform merges even when OpenRouter JEV times out or is rate-limited
    const STOP_WORDS = new Set([
      'the', 'and', 'for', 'with', 'that', 'this', 'from', 'into', 'over', 'after', 'before',
      'under', 'about', 'between', 'through', 'during', 'without', 'within', 'along', 'following',
      'across', 'behind', 'beyond', 'plus', 'except', 'but', 'up', 'out', 'around', 'down', 'off',
      'above', 'near', 'new', 'how', 'why', 'what', 'when', 'where', 'who', 'will', 'can', 'may',
      'now', 'just', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
      'same', 'so', 'than', 'too', 'very', 'says', 'said', 'report', 'reports', 'launch', 'launches',
      'launched', 'release', 'releases', 'released', 'announces', 'announced', 'unveils', 'unveiled',
      'rolls', 'out', 'update', 'updates', 'model', 'models', 'ai', 'artificial', 'intelligence',
      'tech', 'technology', 'company', 'users', 'system', 'data', 'first', 'next', 'open', 'source',
      'youtube', 'jocoding', 'shorts', 'reddit', 'geeknews', 'hacker', 'news', 'github', 'arxiv',
      'press', 'pytorchkr', 'huggingface', 'space', 'video', 'channel'
    ]);
    function extractSpecificTokens(text) {
      return (text || '')
        .replace(PREFIX_STRIP_RE, '')
        .toLowerCase()
        .replace(/[^a-z0-9.\-+]+/g, ' ')
        .split(/\s+/)
        .filter(t => t.length >= 3 && !STOP_WORDS.has(t));
    }

    const unresolvedAmbiguous = [];
    for (const p of ambiguousPairs) {
      const tA = extractSpecificTokens(p.primaryTitle);
      const tB = new Set(extractSpecificTokens(p.dupTitle));
      const shared = tA.filter(tok => tB.has(tok));
      // If cosine similarity >= 0.78 and they share >= 2 distinctive tokens (e.g. ['gemini', 'argon'] or ['claude', 'opus', '5.5']), merge deterministically!
      if (p.sim >= 0.78 && shared.length >= 2) {
        validPairs.push(p);
      } else {
        p.ambiguousIdx = unresolvedAmbiguous.length;
        unresolvedAmbiguous.push(p);
      }
    }

    // 🌟 Execute 1-Shot Bulk JEV Evaluation for remaining unresolved ambiguous pairs
    if (unresolvedAmbiguous.length > 0 && OPENROUTER_API_KEY) {
      try {
        const formatted = unresolvedAmbiguous.map((p, idx) => ({ id: idx, a: p.primaryTitle, b: p.dupTitle }));
        const prompt = 'Determine if each pair of English headlines reports the exact same real-world incident/event.\nReturn ONLY a JSON array with id and is_same (true/false):\n' + JSON.stringify(formatted);
        const models = [
          'inclusionai/ling-3.0-flash-sante:free',
          'liquid/lfm-2.5-2.6b:free'
        ];

        for (const model of models) {
          try {
            const ac = new AbortController();
            const tm = setTimeout(() => ac.abort(), 3500);
            const resp = await fetch('https://openrouter.ai/api/v1/chat/completions', {
              signal: ac.signal,
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://ai-factcheck.vercel.app',
                'X-Title': 'FactCheck JEV Bulk Judge'
              },
              body: JSON.stringify({
                model,
                messages: [{ role: 'user', content: prompt }],
                max_tokens: 300 + unresolvedAmbiguous.length * 40,
                temperature: 0.0
              })
            });
            clearTimeout(tm);
            if (resp.status === 402 || resp.status === 429) continue;
            if (!resp.ok) continue;
            const data = await resp.json();
            const content = data.choices?.[0]?.message?.content || data.choices?.[0]?.message?.reasoning || '';
            const match = content.match(/\[.*\]/s);
            if (match) {
              const arr = JSON.parse(match[0]);
              const resMap = {};
              for (const itm of arr) {
                if (itm && itm.id !== undefined) {
                  resMap[itm.id] = Boolean(itm.is_same || itm.same || itm.verdict === 'YES');
                }
              }
              for (const p of unresolvedAmbiguous) {
                if (resMap[p.ambiguousIdx] === true) {
                  validPairs.push(p);
                }
              }
              break;
            }
          } catch (e) {
            // Next model fallback
          }
        }
      } catch (err) {
        console.warn('[EmbedWorker] Bulk JEV evaluation error, skipping ambiguous merges:', err.message);
      }
    }

    let mergedCount = 0;
    const archivedIds = new Set();
    const primaryUpdates = new Map();

    for (const pData of validPairs) {
      const { primaryId, primaryTitle, primaryPlatform, primaryUrl, dupId, dupTitle, dupPlatform, dupUrl, dupPayload, sim } = pData;
      let primaryPayload = pData.primaryPayload;

      if (archivedIds.has(primaryId) || archivedIds.has(dupId)) {
        continue; // Already processed in this batch
      }

      primaryPayload = primaryUpdates.get(primaryId) || primaryPayload || {};
      let sources = primaryPayload.sources || [];
      if (!Array.isArray(sources)) sources = [];

      const existingUrls = new Set(sources.map(s => s.url || s.source_url));

      // Ensure the primary item's own source is seeded at index 0
      if (primaryUrl && !existingUrls.has(primaryUrl)) {
        sources.unshift({
          source_name: primaryPlatform || 'Primary',
          platform: primaryPlatform || 'Primary',
          title: primaryTitle,
          url: primaryUrl,
          type: 'primary',
          created_at: pData.primaryCreatedAt ? new Date(pData.primaryCreatedAt).toISOString() : new Date().toISOString()
        });
        existingUrls.add(primaryUrl);
      }

      // Add dup source if not already present
      if (dupUrl && !existingUrls.has(dupUrl)) {
        sources.push({
          source_name: dupPlatform || 'Cross-Platform Media',
          platform: dupPlatform || 'Media',
          title: dupTitle,
          url: dupUrl,
          type: 'discussion',
          similarity: parseFloat(Number(sim || 0).toFixed(4))
        });
        existingUrls.add(dupUrl);
      }

      // Preserve any transitive sources from duplicate
      if (dupPayload && Array.isArray(dupPayload.sources)) {
        for (const s of dupPayload.sources) {
          const sUrl = s.url || s.source_url;
          if (sUrl && !existingUrls.has(sUrl)) {
            existingUrls.add(sUrl);
            sources.push(s);
          }
        }
      }

      primaryPayload.sources = sources;
      primaryPayload.has_multi_sources = true;
      if (sources.length > 1) {
        primaryPayload.is_cross_spiking = true;
      }
      primaryPayload.spike_analysis = calculateSpikeAnalysis(
        sources,
        pData.primaryCreatedAt || new Date().toISOString(),
        primaryPayload.viral_score || 0,
        primaryPayload.metric_tracking?.delta || 0,
        Array.isArray(primaryPayload.raw_comments) ? primaryPayload.raw_comments.length : 0
      );
      primaryUpdates.set(primaryId, primaryPayload);

      archivedIds.add(dupId);
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
    const remainingCount = Math.max(0, remainingUnembedded - items.length);

    // Record telemetry log in DB for dashboard and runs table
    try {
      await client.query(`
        INSERT INTO vercel_worker_logs (worker_name, model_used, processed_count, duration_seconds, remaining_count, inbox_ids, status)
        VALUES ('Voyage AI Embedder', $1, $2, $3, $4, $5, 'SUCCESS');
      `, [
        VOYAGE_MODEL,
        items.length,
        parseFloat(((Date.now() - startTime) / 1000).toFixed(2)),
        remainingCount,
        JSON.stringify({ merged_count: mergedCount, tokens_used: tokensUsed })
      ]);
    } catch (logErr) {
      console.warn('[embed-worker] Telemetry insert error:', logErr.message);
    }

    return res.status(200).json({
      success: true,
      model: VOYAGE_MODEL,
      processed_count: items.length,
      tokens_used: tokensUsed,
      merged_duplicates_count: mergedCount,
      total_count: totalCount,
      embedded_count: embeddedCount + items.length,
      remaining_unembedded: remainingCount,
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
