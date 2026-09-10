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
  'nvidia/nemotron-3.5-lightning:free',
  'nex-agi/nex-n2.5-pro:free'
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
    // 1. Determine batch limit (Default 5 items as requested by user)
    const rawLimit = parseInt(req.query?.limit, 10);
    const limit = Number.isInteger(rawLimit) ? Math.min(10, Math.max(1, rawLimit)) : 5;

    // 2. Fetch unclassified records
    const selectQuery = `
      SELECT id, inbox_id, source_platform, source_url, title, description, item_type, harvested_date, raw_payload
      FROM raw_trends_inbox
      WHERE is_classified = FALSE
      ORDER BY updated_at ASC NULLS FIRST, id DESC
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

    const systemPrompt = `당신은 최고 수준의 AI 기술 아키텍트입니다.
주어진 기술/뉴스 후보 목록을 분석하여, 각 항목마다 한국어 번역 제목, 엔지니어가 주목할 1줄 결정적 훅(Hook), 그리고 'AI 3줄 핵심 요약'(key_takeaways: 핵심 포인트 3개)을 반드시 아래 JSON 배열 형식으로만 응답하세요. 생각 과정이나 마크다운 등 기타 텍스트는 일절 출력하지 마세요.
[
  {
    "id": "item_id",
    "korean_title": "자연스러운 한국어 번역 제목",
    "hook_ko": "결정적 1줄 한국어 훅",
    "key_takeaways": [
      "첫 번째 핵심 요약 포인트",
      "두 번째 핵심 요약 포인트",
      "세 번째 핵심 요약 포인트"
    ],
    "programming_lang": "Python, TypeScript, Rust, General 중 택1"
  }
]`;

    let enrichedAiList = null;
    let modelUsed = null;
    let llmLatencySec = 0;

    // Call OpenRouter with fast fallback models and dynamic time budget (within 45s serverless limit)
    for (const modelName of FREE_MODELS) {
      const budgetMs = 45000 - (Date.now() - startTime);
      if (budgetMs < 3000) {
        console.warn(`[Worker] Time budget exhausted (${budgetMs}ms left). Breaking early.`);
        break;
      }
      const callStart = Date.now();
      let timeoutId = null;
      try {
        const controller = new AbortController();
        const timeoutMs = Math.min(8000, budgetMs);
        timeoutId = setTimeout(() => controller.abort(), timeoutMs);


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
            messages: [
              { role: 'system', content: systemPrompt },
              { role: 'user', content: `분석할 항목 목록:\n${JSON.stringify(promptItems, null, 2)}` }
            ],
            temperature: 0.1,
            max_tokens: 1600,
            reasoning: { max_tokens: 0 }
          }),
          signal: controller.signal
        });


        if (!aiResponse.ok) {
          console.warn(`[Worker] ${modelName} returned HTTP ${aiResponse.status} (${((Date.now() - callStart) / 1000).toFixed(2)}s)`);
          continue;
        }

        const aiJson = await aiResponse.json();
        if (timeoutId) { clearTimeout(timeoutId); timeoutId = null; }

        llmLatencySec = ((Date.now() - callStart) / 1000).toFixed(2);
        const rawContent = aiJson.choices?.[0]?.message?.content || '';
        const parsed = sanitizeJsonString(rawContent);

        if (Array.isArray(parsed) && parsed.length > 0) {
          // Check Korean character guardrail & reject broken unicode replacement characters (\ufffd)
          const hasKorean = parsed.some(p => /[\uac00-\ud7a3]/.test((p.korean_title || '') + ' ' + (p.hook_ko || '')));
          const hasBrokenBytes = parsed.some(p => /[\ufffd]/.test((p.korean_title || '') + ' ' + (p.hook_ko || '')));
          if (hasKorean && !hasBrokenBytes) {
            enrichedAiList = parsed;
            modelUsed = aiJson.model || modelName;
            break;
          } else {
            console.warn(`[Worker] Model ${modelName} rejected: hasKorean=${hasKorean}, hasBrokenBytes=${hasBrokenBytes}`);
          }
        }
      } catch (err) {
        console.warn(`[Worker] Model ${modelName} error (${((Date.now() - callStart) / 1000).toFixed(2)}s): ${err.message}`);
      } finally {
        if (timeoutId) clearTimeout(timeoutId);
      }
    }

    const resMap = {};
    if (enrichedAiList) {
      for (const item of enrichedAiList) {
        if (item.id) resMap[item.id] = item;
      }
    }

    const processedItems = [];

    const koreanRegex = /[\uac00-\ud7a3]/;

    // 4. Update Database for each item
    for (let i = 0; i < candidates.length; i++) {
      const cand = candidates[i];
      let aiData = resMap[cand.inbox_id];
      // Positional fallback if LLM omitted or altered the item ID
      if (!aiData && enrichedAiList && enrichedAiList[i]) {
        aiData = enrichedAiList[i];
      }
      
      const titleKoCandidate = (aiData?.korean_title || '').trim();
      const hookKoCandidate = (aiData?.hook_ko || '').trim();
      const rawTakeaways = Array.isArray(aiData?.key_takeaways) ? aiData.key_takeaways : [];
      const takeawaysKo = rawTakeaways
        .map(t => String(t).replace(/^[-*•\d.]\s*/, '').trim())
        .filter(Boolean)
        .slice(0, 3);

      const hasKorean = koreanRegex.test(titleKoCandidate) || 
                        koreanRegex.test(hookKoCandidate) || 
                        takeawaysKo.some(t => koreanRegex.test(t));

      // CRITICAL GUARDRAIL: Never mark as classified if valid Korean translation is missing!
      // Unenriched items must stay is_classified = FALSE so they can be processed on subsequent runs.
      if (!aiData || !hasKorean) {
        console.warn(`[Worker] Skipping ${cand.inbox_id}: Missing AI translation or no Korean characters. Retaining is_classified=FALSE.`);
        continue;
      }

      let payload = cand.raw_payload;
      if (typeof payload === 'string') {
        try { payload = JSON.parse(payload); } catch (e) { payload = {}; }
      }
      if (!payload || typeof payload !== 'object') payload = {};

      const nowIso = new Date().toISOString();
      const cleanTitle = (cand.title || '').replace(/^(Show HN|Ask HN|GeekNews|HN):\s*/i, '').trim();

      const titleKo = titleKoCandidate;
      const titleEn = aiData?.title_en || payload.title_en || cleanTitle;
      const titleZh = aiData?.title_zh || payload.title_zh || cleanTitle;

      const hookKo = hookKoCandidate;
      const hookEn = aiData?.hook_en || payload.hook_en || cleanTitle;
      const hookZh = aiData?.hook_zh || payload.hook_zh || cleanTitle;

      // Ensure key_takeaways has 3 valid points (with fallback to hook/title if LLM returned fewer)
      const finalTakeaways = takeawaysKo.length > 0 
        ? takeawaysKo 
        : (Array.isArray(payload.multilingual?.ko?.key_takeaways) && payload.multilingual.ko.key_takeaways.length > 0 
            ? payload.multilingual.ko.key_takeaways 
            : [hookKo || titleKo]);

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
        ko: { title: titleKo, hook: hookKo, key_takeaways: finalTakeaways },
        en: { title: titleEn, hook: hookEn, key_takeaways: finalTakeaways },
        zh: { title: titleZh, hook: hookZh, key_takeaways: finalTakeaways }
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
        key_takeaways: finalTakeaways,
        multilingual: payload.multilingual,
        enriched_by_model: modelUsed || 'openrouter-free',
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
        enriched_by_model: modelUsed || 'openrouter-free'
      });
    }

    const totalDurationSec = ((Date.now() - startTime) / 1000).toFixed(2);
    const newRemaining = Math.max(0, totalRemaining - processedItems.length);

    return res.status(200).json({
      status: 'success',
      processed_count: processedItems.length,
      model_used: modelUsed || 'openrouter-free',
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
