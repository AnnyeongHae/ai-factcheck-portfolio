/**
 * api/enrich-worker.js
 * ==============================================================================
 * Zero-Cost Vercel Serverless AI Micro-Worker (v1.0)
 * ------------------------------------------------------------------------------
 * Purpose:
 *   Offloads the heavy AI translation and enrichment task from GitHub Actions
 *   (which previously caused 8-minute runtimes) to Vercel Serverless.
 *   Processes 1~2 items per request within Vercel's 10-second serverless window
 *   using OpenRouter 100% Free AI Models ($0.00 cost guarantee).
 * 
 * Execution Modes:
 *   1. Automated Client-side SWR Trigger: Frontend triggers this asynchronously.
 *   2. Admin On-Demand Trigger: GET /api/enrich-worker?limit=2
 *   3. Scheduled Vercel Cron Trigger: Triggered periodically.
 * ==============================================================================
 */

let cachedPool = null;

function getDbPool() {
  const DATABASE_URL = process.env.DATABASE_URL || process.env.NEON_KEY || process.env.NEON_DATABASE_URL;
  if (!DATABASE_URL) return null;
  if (!cachedPool) {
    try {
      const { Pool } = require('pg');
      cachedPool = new Pool({
        connectionString: DATABASE_URL,
        ssl: { rejectUnauthorized: true },
        max: 3,
        idleTimeoutMillis: 15000,
        connectionTimeoutMillis: 5000
      });
      cachedPool.on('error', (err) => {
        console.error('[PgPool Error in enrich-worker]:', err);
        cachedPool = null;
      });
    } catch (e) {
      console.error('[Pg Driver Error]:', e);
      return null;
    }
  }
  return cachedPool;
}

const FREE_MODELS = [
  'nvidia/nemotron-3-super-120b-a12b:free',
  'liquid/lfm-2.5-2.6b:free',
  'dots-studio/dots-3-note-preview:free',
  'google/gemma-3-27b-it:free'
];

function sanitizeJsonString(str) {
  let cleaned = (str || '').trim();
  cleaned = cleaned.replace(/<think>[\s\S]*?<\/think>/gi, '').trim();
  cleaned = cleaned.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/i, '').trim();
  
  try {
    return JSON.parse(cleaned);
  } catch (e) {}

  const arrMatch = cleaned.match(/\[[\s\S]*?\]/);
  if (arrMatch) {
    try { return JSON.parse(arrMatch[0]); } catch (e) {}
  }

  const objMatch = cleaned.match(/\{[\s\S]*?\}/);
  if (objMatch) {
    try { return [JSON.parse(objMatch[0])]; } catch (e) {}
  }

  return null;
}

function inferCategoriesAndArtifact(item, parsedAi) {
  const title = (item.title || '').toLowerCase();
  const desc = (item.description || '').toLowerCase();
  const platform = (item.source_platform || '').toLowerCase();
  const text = `${title} ${desc} ${platform}`;

  // 1. Primary Category
  let categoryPrimary = 'INDUSTRY_TRENDS';
  if (text.match(/gguf|vllm|sglang|ollama|awq|fp8|int4|int8|quantization|추론|양자화|서빙|가속/)) {
    categoryPrimary = 'INFERENCE_OPT';
  } else if (text.match(/vlm|diffusion|tts|stt|whisper|flux|wan|sora|kling|video|vision|audio|speech|voice|multimodal|멀티모달|음성|비디오|영상/)) {
    categoryPrimary = 'MULTIMODAL_AI';
  } else if (text.match(/agent|agents|browser.use|crawler|scraper|devtools|copilot|sdk|cli|framework|에이전트|자동화|개발도구/)) {
    categoryPrimary = 'AGENTS_DEVTOOLS';
  } else if (text.match(/rag|vectordb|vector.database|embedding|jailbreak|cve|vulnerability|security|보안|취약점|탈옥|임베딩/)) {
    categoryPrimary = 'INFRA_RAG_SECURITY';
  } else if (text.match(/aerospace|rocket|orbit|satellite|nasa|astronomy|dark matter|우주|항공우주|인공위성|천문/)) {
    categoryPrimary = 'DEEP_SCIENCE_SPACE';
  } else if (text.match(/gold|reserve|central bank|inflation|interest rate|macroeconomics|gdp|금|중앙은행|인플레이션|기준금리|거시경제/)) {
    categoryPrimary = 'MACRO_GLOBAL_BIZ';
  } else if (text.match(/babylonian|recipe|cooking|archaeology|medieval|고대 요리|바빌로니아|고고학|역사/)) {
    categoryPrimary = 'HISTORY_LIFE_CULTURE';
  } else if (text.match(/weights|safetensors|checkpoint|lora|foundation model|qwen|deepseek|llama|mistral|gemma|파운데이션|가중치/) || platform.includes('models')) {
    categoryPrimary = 'FOUNDATION_MODELS';
  }

  // 2. IPTC Tier 1
  let tier1 = 'TECH_COMPUTING';
  if (['DEEP_SCIENCE_SPACE'].includes(categoryPrimary)) tier1 = 'SCIENCE_RESEARCH';
  else if (['MACRO_GLOBAL_BIZ'].includes(categoryPrimary)) tier1 = 'ECONOMY_FINANCE';
  else if (['HISTORY_LIFE_CULTURE'].includes(categoryPrimary)) tier1 = 'CULTURE_HUMANITIES';

  // 3. Artifact Type
  let artifactType = 'ARTICLE';
  if (platform.includes('spaces') || text.includes('spaces') || text.includes('gradio')) {
    artifactType = 'WEB_SERVICE';
  } else if (text.match(/agent|harness|cli|sdk|framework|devtools/) || platform.includes('github')) {
    artifactType = 'SKILL_AGENT';
  } else if (text.match(/lora|adapter|finetune|fine-tuning/)) {
    artifactType = 'FINETUNE';
  } else if (text.match(/gguf|safetensors|fp8|weights/) || platform.includes('models')) {
    artifactType = 'WEIGHTS';
  }

  // 4. Item Type Classification
  let itemType = 'TECH';
  if (artifactType === 'WEIGHTS' || text.match(/gguf|lora|safetensors|checkpoint|weights|7b|14b|70b|32b/) || platform.includes('models')) {
    itemType = 'MODEL';
  } else if (artifactType === 'SKILL_AGENT' || text.match(/agent|crawler|scraper|devtools|copilot/)) {
    itemType = 'AGENT';
  } else if (text.match(/shooting|police|arrest|minister|court|antitrust|election|attack/)) {
    itemType = 'NEWS';
  }

  return { categoryPrimary, tier1, artifactType, itemType };
}

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Admin-Key');
  res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate');

  if (req.method === 'OPTIONS') {
    return res.status(204).end();
  }

  // Admin / Secret Authorization Check (Optional if secret is set)
  const adminSecret = process.env.ADMIN_QUEUE_SECRET || process.env.CRON_SECRET;
  if (adminSecret) {
    const authHeader = req.headers.authorization || '';
    const customHeader = req.headers['x-admin-key'] || '';
    const querySecret = req.query?.secret || '';
    const provided = authHeader.startsWith('Bearer ') ? authHeader.substring(7) : (customHeader || querySecret);
    if (provided && provided !== adminSecret) {
      return res.status(401).json({ status: 'error', message: 'Unauthorized: Invalid secret' });
    }
  }

  const pool = getDbPool();
  if (!pool) {
    return res.status(500).json({ status: 'error', message: 'Neon Database connection not configured' });
  }

  const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY;
  if (!OPENROUTER_API_KEY) {
    return res.status(500).json({ status: 'error', message: 'OPENROUTER_API_KEY not configured' });
  }

  const startTime = Date.now();

  try {
    // 1. Determine batch limit (Default 1 item to guarantee completion within ~4-6s on Vercel Hobby)
    const rawLimit = parseInt(req.query?.limit, 10);
    const limit = Number.isInteger(rawLimit) ? Math.min(3, Math.max(1, rawLimit)) : 1;

    // 2. Fetch unclassified records
    const selectQuery = `
      SELECT id, inbox_id, source_platform, source_url, title, description, item_type, harvested_date, raw_payload
      FROM raw_trends_inbox
      WHERE is_classified = FALSE
      ORDER BY id DESC
      LIMIT $1;
    `;
    const candidateResult = await pool.query(selectQuery, [limit]);
    const candidates = candidateResult.rows;

    // Total remaining count check
    const countResult = await pool.query(`SELECT COUNT(*) FROM raw_trends_inbox WHERE is_classified = FALSE;`);
    const totalRemaining = parseInt(countResult.rows[0]?.count || '0', 10);

    if (candidates.length === 0) {
      return res.status(200).json({
        status: 'noop',
        message: 'All items in Neon DB are already enriched and classified!',
        processed_count: 0,
        remaining_unclassified: 0
      });
    }

    // 3. Prepare payload for OpenRouter Free Router
    const promptItems = candidates.map(c => ({
      id: c.inbox_id,
      platform: c.source_platform || 'Unknown',
      title: (c.title || '').slice(0, 150),
      description: (c.description || '').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 300)
    }));

    const systemPrompt = `당신은 글로벌 최고 수준의 다국어 AI 기술 아키텍트입니다.
주어진 기술/뉴스 후보 목록을 분석하여 각 항목마다 한국어 번역, 매력적인 1줄 훅(엔지니어가 지금 읽고 싶게 만드는 핵심 요약), 다국어 정보를 반드시 JSON 배열 형식으로만 응답하세요.
JSON 스키마 예시:
[
  {
    "id": "item_id",
    "korean_title": "한국어 번역 제목",
    "hook_ko": "엔지니어가 당장 클릭하고 싶게 만드는 결정적 1줄 한국어 훅",
    "hook_en": "1-line compelling hook in English",
    "hook_zh": "1-line compelling hook in Chinese",
    "title_en": "Title in English",
    "title_zh": "Title in Chinese",
    "programming_lang": "Python | TypeScript | Rust | General"
  }
]`;

    let enrichedAiList = null;
    let modelUsed = null;
    let llmLatencySec = 0;

    // Call OpenRouter with fast fallback models and dynamic time budget (never exceeds 7.5s total)
    for (const modelName of FREE_MODELS) {
      const budgetMs = 7500 - (Date.now() - startTime);
      if (budgetMs < 1500) {
        console.warn(`[Worker] Time budget exhausted (${budgetMs}ms left). Breaking early.`);
        break;
      }
      const callStart = Date.now();
      try {
        const controller = new AbortController();
        const timeoutMs = Math.min(4500, budgetMs);
        const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

        const aiResponse = await fetch('https://openrouter.ai/api/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://github.com/AnnyeongHae/ai-factcheck-portfolio',
            'X-Title': 'AI FactCheck Portfolio Serverless Worker'
          },
          body: JSON.stringify({
            model: modelName,
            models: FREE_MODELS.filter(m => m !== modelName).slice(0, 3),
            messages: [
              { role: 'system', content: systemPrompt },
              { role: 'user', content: `분석할 항목 목록:\n${JSON.stringify(promptItems, null, 2)}` }
            ],
            temperature: 0.1
          }),
          signal: controller.signal
        });
        clearTimeout(timeoutId);

        llmLatencySec = ((Date.now() - callStart) / 1000).toFixed(2);

        if (!aiResponse.ok) {
          console.warn(`[Worker] ${modelName} returned HTTP ${aiResponse.status} (${llmLatencySec}s)`);
          continue;
        }

        const aiJson = await aiResponse.json();
        modelUsed = aiJson.model || modelName;
        const rawContent = aiJson.choices?.[0]?.message?.content || '';
        const parsed = sanitizeJsonString(rawContent);

        if (Array.isArray(parsed) && parsed.length > 0) {
          // Check Korean character guardrail
          const hasKorean = parsed.some(p => /[\uac00-\ud7a3]/.test((p.korean_title || '') + ' ' + (p.hook_ko || '')));
          if (hasKorean) {
            enrichedAiList = parsed;
            break;
          }
        }
      } catch (err) {
        console.warn(`[Worker] Model ${modelName} error (${((Date.now() - callStart) / 1000).toFixed(2)}s): ${err.message}`);
      }
    }

    const resMap = {};
    if (enrichedAiList) {
      for (const item of enrichedAiList) {
        if (item.id) resMap[item.id] = item;
      }
    }

    const processedItems = [];

    // 4. Update Database for each item
    for (let i = 0; i < candidates.length; i++) {
      const cand = candidates[i];
      let aiData = resMap[cand.inbox_id];
      // Positional fallback if LLM omitted or altered the item ID
      if (!aiData && enrichedAiList && enrichedAiList[i]) {
        aiData = enrichedAiList[i];
      }
      
      // If AI translation failed and no fallback requested, skip to allow retry
      if (!aiData && req.query?.allow_fallback !== 'true') {
        console.warn(`[Worker] No valid AI translation for ${cand.inbox_id}. Leaving for retry.`);
        continue;
      }

      let payload = cand.raw_payload;
      if (typeof payload === 'string') {
        try { payload = JSON.parse(payload); } catch (e) { payload = {}; }
      }
      if (!payload || typeof payload !== 'object') payload = {};

      const nowIso = new Date().toISOString();
      const cleanTitle = (cand.title || '').replace(/^(Show HN|Ask HN|GeekNews|HN):\s*/i, '').trim();

      const titleKo = aiData?.korean_title || payload.title_ko || cleanTitle;
      const titleEn = aiData?.title_en || payload.title_en || cleanTitle;
      const titleZh = aiData?.title_zh || payload.title_zh || cleanTitle;

      const hookKo = aiData?.hook_ko || payload.hook_ko || payload.hook || cleanTitle;
      const hookEn = aiData?.hook_en || payload.hook_en || cleanTitle;
      const hookZh = aiData?.hook_zh || payload.hook_zh || cleanTitle;

      const inferred = inferCategoriesAndArtifact(cand, aiData || {});

      // Build structured payload matching enterprise schema
      payload.title_ko = titleKo;
      payload.title_en = titleEn;
      payload.title_zh = titleZh;
      payload.hook = hookKo;
      payload.hook_ko = hookKo;
      payload.hook_en = hookEn;
      payload.hook_zh = hookZh;
      payload.description_ko = hookKo;
      payload.description_en = hookEn;
      payload.description_zh = hookZh;

      payload.category_type = inferred.itemType;
      payload.category_primary = inferred.categoryPrimary;
      payload.tier1_category = inferred.tier1;
      payload.tier2_category = inferred.categoryPrimary;
      payload.artifact_type = inferred.artifactType;
      payload.programming_lang = aiData?.programming_lang || payload.programming_lang || 'General';

      payload.multilingual = {
        ko: { title: titleKo, hook: hookKo },
        en: { title: titleEn, hook: hookEn },
        zh: { title: titleZh, hook: hookZh }
      };

      payload.ai_enrichment = {
        id: cand.inbox_id,
        source_lang: 'EN',
        programming_lang: payload.programming_lang,
        type_classification: inferred.itemType,
        category_primary: inferred.categoryPrimary,
        tier1_category: inferred.tier1,
        tier2_category: inferred.categoryPrimary,
        artifact_type: inferred.artifactType,
        korean_title: titleKo,
        hook: hookKo,
        multilingual: payload.multilingual,
        enriched_by_model: modelUsed || 'heuristic-rule-engine',
        enriched_at: nowIso
      };

      // Atomic Update to Neon Database
      const updateSql = `
        UPDATE raw_trends_inbox
        SET is_classified = TRUE,
            category_primary = $1,
            item_type = $2,
            raw_payload = $3,
            updated_at = CURRENT_TIMESTAMP
        WHERE inbox_id = $4;
      `;
      await pool.query(updateSql, [
        inferred.categoryPrimary,
        inferred.itemType,
        JSON.stringify(payload),
        cand.inbox_id
      ]);

      processedItems.push({
        inbox_id: cand.inbox_id,
        title_ko: titleKo,
        category_primary: inferred.categoryPrimary,
        item_type: inferred.itemType,
        enriched_by_model: modelUsed || 'heuristic-rule-engine'
      });
    }

    const totalDurationSec = ((Date.now() - startTime) / 1000).toFixed(2);
    const newRemaining = Math.max(0, totalRemaining - processedItems.length);

    return res.status(200).json({
      status: 'success',
      processed_count: processedItems.length,
      model_used: modelUsed || 'heuristic-rule-engine',
      duration_seconds: parseFloat(totalDurationSec),
      remaining_unclassified: newRemaining,
      items: processedItems
    });

  } catch (err) {
    console.error('[API enrich-worker Error]:', err);
    return res.status(500).json({
      status: 'error',
      message: 'Internal server error in enrich worker',
      error: err.message
    });
  }
};
