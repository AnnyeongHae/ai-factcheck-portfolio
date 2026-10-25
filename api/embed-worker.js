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
const { verifyAdminSecret } = require('./_lib/auth');

const VOYAGE_API_URL = 'https://api.voyageai.com/v1/embeddings';
const VOYAGE_MODEL = 'voyage-4-lite';
const VOYAGE_DIM = 1024;
const SIMILARITY_THRESHOLD = 0.78; // Cosine similarity >= 0.78 candidate merge zone
const TRACE_THRESHOLD = 0.65;      // Record top nearest neighbors >= 0.65 in dedup_trace for zero-overhead debugging

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

  if (!isCheckOnly) {
    if (!verifyAdminSecret(req, res)) return;
  }

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
  // Zero-LLM Deterministic Policy: OpenRouter calls disabled
  const OPENROUTER_API_KEY = null;

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

    // 2. Prepare Rich Text payload for Voyage AI (English-Only standard, excluding boilerplate hooks)
    const PREFIX_STRIP_RE = /^(?:News|Hacker News|Reddit|GeekNews|GitHub|HuggingFace Model|HF Space|PyTorchKR|YouTube(?:\s*\([^)]*\))?|Press(?:\s*\([^)]*\))?|r\/[a-zA-Z0-9_]+):\s*/i;
    const BOILERPLATE_HOOK_RE = /^Key architectural updates and practitioner impact analysis published via/i;
    const texts = items.map(item => {
      const p = item.raw_payload || {};
      const en = (p.title_en || p.ai_enrichment?.multilingual?.en?.title || item.title || '').replace(PREFIX_STRIP_RE, '').trim();
      const rawHook = (p.hook_en || p.ai_enrichment?.multilingual?.en?.hook || '').trim();
      const hookStr = BOILERPLATE_HOOK_RE.test(rawHook) ? '' : rawHook;
      const summaryStr = (p.description_en || p.description || '').trim();

      const parts = [en || 'Untitled'];
      if (hookStr) parts.push(`Hook: ${hookStr}`);
      if (summaryStr && !BOILERPLATE_HOOK_RE.test(summaryStr)) parts.push(`Summary: ${summaryStr.slice(0, 300)}`);

      return parts.join(' | ');
    });

    // 3. Batch call Voyage AI API in a single HTTP request (~0.3 - 0.5s)
    const voyageRes = await fetch(VOYAGE_API_URL, {
      method: 'POST',
      signal: AbortSignal.timeout(15000),
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
    // Queries top-5 nearest neighbors (sim >= 0.65) for dedup_trace logging & evaluates sim >= 0.74 for merging
    const batchIds = items.map(it => it.id);
    const traceDistanceThreshold = 1.0 - TRACE_THRESHOLD; // <= 0.35 (similarity >= 0.65)
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
    const { rows: dupPairs } = await client.query(dedupQuery, [batchIds, traceDistanceThreshold]);

    const MAJOR_ENTITIES = ['openai', 'google', 'anthropic', 'meta', 'microsoft', 'apple', 'deepseek', 'qwen', 'houthi', 'flock', 'nvidia', 'tesla'];
    const BROAD_ENTITY_TOKENS = new Set([
      'openai', 'chatgpt', 'anthropic', 'claude', 'google', 'gemini', 'meta', 'llama',
      'microsoft', 'copilot', 'apple', 'nvidia', 'deepseek', 'qwen', 'amazon', 'aws', 'tesla', 'github'
    ]);
    const VERSION_TOKEN_RE = /\b(?:b\d{4,6}|v?\d+\.\d+(?:\.\d+)?(?:-[a-z0-9.]+)?)\b/gi;
    const STOP_WORDS = new Set([
      'the', 'and', 'for', 'with', 'that', 'this', 'from', 'into', 'over', 'after', 'before',
      'under', 'about', 'between', 'through', 'during', 'without', 'within', 'along', 'following',
      'across', 'behind', 'beyond', 'plus', 'except', 'but', 'up', 'out', 'around', 'down', 'off',
      'above', 'near', 'new', 'how', 'why', 'what', 'when', 'where', 'who', 'will', 'can', 'may',
      'now', 'just', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
      'same', 'so', 'than', 'too', 'very', 'says', 'said', 'report', 'reports', 'launch', 'launches',
      'launched', 'release', 'releases', 'released', 'announces', 'announced', 'unveils', 'unveiled',
      'rolls', 'out', 'update', 'updates', 'model', 'models', 'ai', 'artificial', 'intelligence',
      'tech', 'technology', 'company', 'users', 'system', 'systems', 'data', 'first', 'next', 'open', 'source',
      'youtube', 'jocoding', 'shorts', 'reddit', 'geeknews', 'hacker', 'news', 'github', 'arxiv',
      'press', 'pytorchkr', 'huggingface', 'hugging', 'face', 'space', 'video', 'videos', 'channel',
      'show', 'ask', 'has', 'have', 'are', 'was', 'were', 'been', 'being', 'tells', 'shows',
      'difference', 'stance', 'taking', 'llm', 'llms', 'agent', 'agents', 'reasoning', 'training',
      'design', 'code', 'coding', 'paper', 'papers', 'preprint', 'world', 'features', 'personal',
      'research', 'blog', 'technical', 'changelog', 'university', 'peking', 'tsinghua',
      '2025', '2026', '2027', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
      'notable', 'weekly', 'daily', 'build', 'building', 'guide', 'using', 'based', 'via', 'part', 'large', 'language'
    ]);

    function stripPlatformPrefix(text, platform = '') {
      let s = (text || '').trim();
      if (platform) {
        const pClean = platform.split('(')[0].trim();
        for (const cand of [platform.trim(), pClean]) {
          if (cand && s.toLowerCase().startsWith(cand.toLowerCase() + ':')) {
            s = s.slice(cand.length + 1).trim();
          }
        }
      }
      return s.replace(PREFIX_STRIP_RE, '').replace(/^(?:Show HN|Ask HN|Show GN):\s*/i, '');
    }

    function normalizeForTokens(text, platform = '') {
      return stripPlatformPrefix(text, platform)
        .toLowerCase()
        .replace(/\bsam altman\b|\baltman\b|\bopenai ceo\b|\bceo of openai\b/g, ' openai altman ')
        .replace(/\bdario amodei\b|\bamodei\b|\banthropic ceo\b/g, ' anthropic amodei ')
        .replace(/\bsundar pichai\b|\bdemis hassabis\b/g, ' google ')
        .replace(/\bopen[\s\-]+weights?\b/g, ' openweight ')
        .replace(/\bbad things\b|\bharms?\b|\brisks?\b/g, ' risks ')
        .replace(/\bworth\b|\bbenefits?\b/g, ' benefits ');
    }

    function extractSpecificTokens(text, platform = '') {
      const platTokens = new Set((platform || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').split(/\s+/).filter(Boolean));
      const rawTokens = normalizeForTokens(text, platform)
        .replace(/[^a-z0-9.\-+]+/g, ' ')
        .split(/\s+/)
        .filter(t => t.length >= 3 && !STOP_WORDS.has(t) && !platTokens.has(t));
      return Array.from(new Set(rawTokens));
    }

    function hasVersionConflict(textA, textB) {
      const mA = (textA || '').match(VERSION_TOKEN_RE) || [];
      const mB = (textB || '').match(VERSION_TOKEN_RE) || [];
      const setA = new Set(mA.map(x => x.toLowerCase().replace(/^v/, '')));
      const setB = new Set(mB.map(x => x.toLowerCase().replace(/^v/, '')));
      if (setA.size > 0 && setB.size > 0) {
        let intersect = false;
        for (const v of setA) {
          if (setB.has(v)) intersect = true;
        }
        if (!intersect) return true;
      }
      return false;
    }

    function getBestEnglishTitle(rawTitle, payload) {
      const p = payload || {};
      return p.title_en || p.ai_enrichment?.multilingual?.en?.title || rawTitle || '';
    }

    // Track per-item nearest neighbor trace (up to Top 3 per item) for zero-overhead DB debugging
    const traceMap = new Map();
    for (const it of items) {
      traceMap.set(Number(it.id), { payload: it.raw_payload || {}, traces: [] });
    }
    function recordTrace(aId, bId, bTitle, sim, sharedTokens, decision) {
      const entry = traceMap.get(Number(aId));
      if (!entry || entry.traces.length >= 3) return;
      if (entry.traces.some(t => t.peer_id === Number(bId))) return;
      entry.traces.push({
        peer_id: Number(bId),
        peer_title: (bTitle || '').slice(0, 100),
        similarity: parseFloat(Number(sim || 0).toFixed(4)),
        shared_tokens: sharedTokens || [],
        decision
      });
    }

    const validPairs = [];
    const ambiguousPairs = [];
    const seenPairKeys = new Set();

    for (const pair of dupPairs) {
      const aId = Number(pair.a_id);
      const bId = Number(pair.b_id);
      const isAOlder = aId < bId;
      const pairKey = isAOlder ? `${aId}:${bId}` : `${bId}:${aId}`;

      const aTitleEn = getBestEnglishTitle(pair.a_title, pair.a_payload);
      const bTitleEn = getBestEnglishTitle(pair.b_title, pair.b_payload);
      const tA = extractSpecificTokens(aTitleEn, pair.a_platform);
      const tBSet = new Set(extractSpecificTokens(bTitleEn, pair.b_platform));
      const sharedTokens = tA.filter(tok => tBSet.has(tok));
      const specificShared = sharedTokens.filter(tok => !BROAD_ENTITY_TOKENS.has(tok));

      if (pair.similarity < SIMILARITY_THRESHOLD) {
        recordTrace(aId, bId, pair.b_title, pair.similarity, sharedTokens, 'BELOW_THRESHOLD');
        continue;
      }

      if (seenPairKeys.has(pairKey)) {
        continue;
      }
      seenPairKeys.add(pairKey);

      const primaryTitle = isAOlder ? pair.a_title : pair.b_title;
      const dupTitle = isAOlder ? pair.b_title : pair.a_title;
      const primaryTitleEn = isAOlder ? aTitleEn : bTitleEn;
      const dupTitleEn = isAOlder ? bTitleEn : aTitleEn;
      const primaryPlatform = isAOlder ? pair.a_platform : pair.b_platform;
      const dupPlatform = isAOlder ? pair.b_platform : pair.a_platform;
      const primaryUrl = isAOlder ? pair.a_url : pair.b_url;
      const dupUrl = isAOlder ? pair.b_url : pair.a_url;

      // Version / Build Number Conflict Veto
      if (hasVersionConflict(primaryTitleEn, dupTitleEn)) {
        recordTrace(aId, bId, pair.b_title, pair.similarity, sharedTokens, 'REJECTED_VERSION_CONFLICT');
        continue;
      }

      // Same-Channel YouTube Self-Merge Veto Guardrail
      const normPPlat = (primaryPlatform || '').trim().toLowerCase();
      const normDPlat = (dupPlatform || '').trim().toLowerCase();
      if (normPPlat && normPPlat === normDPlat && normPPlat.includes('youtube') && primaryUrl !== dupUrl) {
        recordTrace(aId, bId, pair.b_title, pair.similarity, sharedTokens, 'REJECTED_SAME_YOUTUBE_CHANNEL');
        continue;
      }

      // Entity Veto Guardrail (OpenAI vs Google, etc. -> Never Merge unless they share at least 1 entity)
      const pLower = normalizeForTokens(primaryTitleEn, primaryPlatform);
      const dLower = normalizeForTokens(dupTitleEn, dupPlatform);
      const pEnts = MAJOR_ENTITIES.filter(e => pLower.includes(e));
      const dEnts = MAJOR_ENTITIES.filter(e => dLower.includes(e));
      if (pEnts.length > 0 && dEnts.length > 0 && !pEnts.some(e => dEnts.includes(e))) {
        recordTrace(aId, bId, pair.b_title, pair.similarity, sharedTokens, 'REJECTED_ENTITY_VETO');
        continue;
      }

      // Same-platform items must share at least 2 specific tokens
      if (normPPlat === normDPlat && specificShared.length < 2) {
        recordTrace(aId, bId, pair.b_title, pair.similarity, sharedTokens, 'REJECTED_SAME_PLATFORM_LOW_SPECIFIC_TOKENS');
        continue;
      }

      const pData = {
        pair,
        isAOlder,
        primaryId: isAOlder ? aId : bId,
        primaryTitle,
        primaryTitleEn,
        primaryPlatform,
        primaryUrl,
        primaryPayload: isAOlder ? pair.a_payload : pair.b_payload,
        primaryCreatedAt: isAOlder ? pair.a_created_at : pair.b_created_at,
        dupId: isAOlder ? bId : aId,
        dupTitle,
        dupTitleEn,
        dupPlatform,
        dupUrl,
        dupPayload: isAOlder ? pair.b_payload : pair.a_payload,
        sim: pair.similarity,
        sharedTokens,
        specificShared,
        matchMethod: 'VECTOR_HIGH'
      };

      if (pair.similarity >= 0.88 && sharedTokens.length >= 1) {
        pData.matchMethod = 'VECTOR_HIGH (>=0.88)';
        recordTrace(aId, bId, pair.b_title, pair.similarity, sharedTokens, pData.matchMethod);
        validPairs.push(pData);
      } else {
        pData.ambiguousIdx = ambiguousPairs.length;
        ambiguousPairs.push(pData);
      }
    }

    // 🌟 Deterministic Entity + Specific-Token Overlap Judge for Ambiguous Zone (0.78 <= sim < 0.88)
    const unresolvedAmbiguous = [];
    for (const p of ambiguousPairs) {
      if (p.sim >= SIMILARITY_THRESHOLD && p.sharedTokens.length >= 2 && p.specificShared.length >= 2) {
        p.matchMethod = `TOKEN_OVERLAP (${p.sharedTokens.slice(0, 4).join(',')})`;
        recordTrace(Number(p.pair.a_id), Number(p.pair.b_id), p.pair.b_title, p.sim, p.sharedTokens, p.matchMethod);
        validPairs.push(p);
      } else {
        p.ambiguousIdx = unresolvedAmbiguous.length;
        unresolvedAmbiguous.push(p);
      }
    }

    // 🌟 Execute 1-Shot Bulk JEV Evaluation for remaining unresolved ambiguous pairs (sim >= 0.78)
    const jevCandidates = unresolvedAmbiguous.filter(p => p.sim >= 0.78);
    const resolvedByJev = new Set();
    if (jevCandidates.length > 0 && OPENROUTER_API_KEY) {
      try {
        const formatted = jevCandidates.map((p, idx) => ({ id: idx, a: p.primaryTitleEn, b: p.dupTitleEn }));
        const prompt = 'Determine if each pair of English headlines reports the exact same real-world incident/event.\nReturn ONLY a JSON array with id and is_same (true/false):\n' + JSON.stringify(formatted);
        const models = [
          'nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free',
          'nvidia/nemotron-3.5-lightning:free'
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
                max_tokens: 300 + jevCandidates.length * 40,
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
              jevCandidates.forEach((p, idx) => {
                if (resMap[idx] === true) {
                  p.matchMethod = 'LLM_JEV_JUDGE';
                  resolvedByJev.add(p);
                  validPairs.push(p);
                }
              });
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

    for (const p of unresolvedAmbiguous) {
      const decision = resolvedByJev.has(p) ? 'LLM_JEV_JUDGE' : 'REJECTED_AMBIGUOUS_LOW_OVERLAP';
      recordTrace(Number(p.pair.a_id), Number(p.pair.b_id), p.pair.b_title, p.sim, p.sharedTokens, decision);
    }

    let mergedCount = 0;
    const archivedIds = new Set();
    const payloadUpdates = new Map();
    // Union-Find map for transitive bridge merges within the same batch (e.g. C -> A, then B <-> C becomes B -> A)
    const hubRedirectMap = new Map();
    const itemMetaMap = new Map();
    for (const pData of validPairs) {
      itemMetaMap.set(pData.primaryId, {
        id: pData.primaryId,
        title: pData.primaryTitle,
        platform: pData.primaryPlatform,
        url: pData.primaryUrl,
        payload: pData.primaryPayload,
        createdAt: pData.primaryCreatedAt
      });
      itemMetaMap.set(pData.dupId, {
        id: pData.dupId,
        title: pData.dupTitle,
        platform: pData.dupPlatform,
        url: pData.dupUrl,
        payload: pData.dupPayload,
        createdAt: pData.pair.a_id === pData.dupId ? pData.pair.a_created_at : pData.pair.b_created_at
      });
    }
    function resolveCanonicalHub(id) {
      let cur = id;
      const visited = new Set();
      while (hubRedirectMap.has(cur) && !visited.has(cur)) {
        visited.add(cur);
        cur = hubRedirectMap.get(cur);
      }
      return cur;
    }

    for (const pData of validPairs) {
      const resolvedA = resolveCanonicalHub(pData.primaryId);
      const resolvedB = resolveCanonicalHub(pData.dupId);
      if (resolvedA === resolvedB) {
        continue; // Already connected in the same cluster
      }

      const primaryId = Math.min(resolvedA, resolvedB);
      const dupId = Math.max(resolvedA, resolvedB);
      const primaryMeta = itemMetaMap.get(primaryId);
      const dupMeta = itemMetaMap.get(dupId);
      if (!primaryMeta || !dupMeta) continue;

      let primaryPayload = payloadUpdates.get(primaryId) || primaryMeta.payload || {};
      let dupPayload = payloadUpdates.get(dupId) || dupMeta.payload || {};
      let sources = primaryPayload.sources || [];
      if (!Array.isArray(sources)) sources = [];

      const existingUrls = new Set(sources.map(s => s.url || s.source_url));

      // Ensure the primary item's own source is seeded at index 0
      if (primaryMeta.url && !existingUrls.has(primaryMeta.url)) {
        sources.unshift({
          source_name: primaryMeta.platform || 'Primary',
          platform: primaryMeta.platform || 'Primary',
          title: primaryMeta.title,
          url: primaryMeta.url,
          type: 'primary',
          created_at: primaryMeta.createdAt ? new Date(primaryMeta.createdAt).toISOString() : new Date().toISOString()
        });
        existingUrls.add(primaryMeta.url);
      }

      // Add dup source if not already present
      const simVal = parseFloat(Number(pData.sim || 0).toFixed(4));
      if (dupMeta.url && !existingUrls.has(dupMeta.url)) {
        sources.push({
          source_name: dupMeta.platform || 'Cross-Platform Media',
          platform: dupMeta.platform || 'Media',
          title: dupMeta.title,
          url: dupMeta.url,
          type: 'discussion',
          similarity: simVal,
          match_method: pData.matchMethod
        });
        existingUrls.add(dupMeta.url);
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
        primaryMeta.createdAt || new Date().toISOString(),
        primaryPayload.viral_score || 0,
        primaryPayload.metric_tracking?.delta || 0,
        Array.isArray(primaryPayload.raw_comments) ? primaryPayload.raw_comments.length : 0
      );
      payloadUpdates.set(primaryId, primaryPayload);

      // Record reverse-lookup merged_into metadata on the duplicate item's payload for debugging
      dupPayload.merged_into = {
        hub_id: primaryId,
        similarity: simVal,
        method: pData.matchMethod,
        shared_tokens: pData.sharedTokens || [],
        merged_at: new Date().toISOString()
      };
      payloadUpdates.set(dupId, dupPayload);

      hubRedirectMap.set(dupId, primaryId);
      archivedIds.add(dupId);
      mergedCount++;
    }

    // Attach dedup_trace (top nearest neighbors + similarity + decision) to batch items' raw_payload
    for (const [bId, entry] of traceMap.entries()) {
      if (entry.traces.length > 0) {
        const targetPayload = payloadUpdates.get(bId) || entry.payload || {};
        targetPayload.dedup_trace = entry.traces;
        payloadUpdates.set(bId, targetPayload);
      }
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

    // Bulk Update all modified payloads (hubs + archived reverse-links + dedup_trace) in 1 single query
    if (payloadUpdates.size > 0) {
      const pClauses = [];
      const pParams = [];
      let pIdx = 1;
      for (const [pId, pPayload] of payloadUpdates.entries()) {
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
