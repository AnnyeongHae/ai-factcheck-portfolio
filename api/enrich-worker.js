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

const { getDbPool } = require('./_lib/db');
const { handleOptions, setCorsHeaders } = require('./_lib/cors');

const FREE_MODELS = [
  'inclusionai/ling-3.0-flash-sante:free',  // Verified: resilient, fast, high quality CJK multilingual
  'inclusionai/ling-3.0-flash-vl:free',     // Reliable fallback
  'qwen/qwen3.8-27b:free',                  // High-quality Qwen free multilingual model
  'z-ai/glm-5.2:free',                      // Fast GLM free multilingual model
  'google/gemma-4-26b-a4b-it:free',         // Gemma 4 free model
  'inclusionai/ling-3.0-flash-fin:free',    // Fast fallback
  'openrouter/free'                         // OpenRouter dynamic load-balanced free router
];

function sanitizeJsonString(str) {
  let cleaned = (str || '').trim();
  cleaned = cleaned.replace(/<think>[\s\S]*?<\/think>/gi, '').trim();
  cleaned = cleaned.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/i, '').trim();
  
  // Strip non-JSON conversational preamble
  const firstBracket = cleaned.indexOf('[');
  const firstBrace = cleaned.indexOf('{');
  let startIdx = -1;
  if (firstBracket !== -1 && firstBrace !== -1) startIdx = Math.min(firstBracket, firstBrace);
  else if (firstBracket !== -1) startIdx = firstBracket;
  else if (firstBrace !== -1) startIdx = firstBrace;

  if (startIdx > 0) {
    cleaned = cleaned.slice(startIdx).trim();
  }

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

  // Attempt recovery of truncated JSON if unclosed
  try {
    let repaired = cleaned;
    const quoteCount = (repaired.match(/(?<!\\)"/g) || []).length;
    if (quoteCount % 2 !== 0) repaired += '"';
    
    const openBraces = (repaired.match(/\{/g) || []).length;
    const closeBraces = (repaired.match(/\}/g) || []).length;
    for (let i = 0; i < openBraces - closeBraces; i++) repaired += '}';
    
    const openBrackets = (repaired.match(/\[/g) || []).length;
    const closeBrackets = (repaired.match(/\]/g) || []).length;
    for (let i = 0; i < openBrackets - closeBrackets; i++) repaired += ']';
    
    const res = JSON.parse(repaired);
    if (Array.isArray(res)) return res;
    if (res && typeof res === 'object') return [res];
  } catch (e) {}

  return null;
}

function inferCategoriesAndArtifact(item, parsedAi) {
  const validTier1 = ['TECH_COMPUTING', 'SCIENCE_RESEARCH', 'ECONOMY_FINANCE', 'POLITICS_POLICY', 'LAW_CRIME_JUSTICE', 'CULTURE_HUMANITIES'];
  const validPrimary = [
    'INFERENCE_OPT', 'AGENTS_DEVTOOLS', 'MULTIMODAL_AI', 'FOUNDATION_MODELS',
    'INFRA_RAG_SECURITY', 'DEEP_SCIENCE_SPACE', 'MACRO_GLOBAL_BIZ',
    'CIVIC_CRIME_INCIDENT', 'HISTORY_LIFE_CULTURE', 'INDUSTRY_TRENDS'
  ];
  const validTypes = ['MODEL', 'AGENT', 'TECH', 'NEWS'];

  const title = (item.title || '').toLowerCase();
  const desc = (item.description || '').toLowerCase();
  const platform = (item.source_platform || '').toLowerCase();
  const text = `${title} ${desc} ${platform}`;

  // 1. AI Classifications (Highest Priority)
  let tier1 = (parsedAi?.tier1_category && validTier1.includes(parsedAi.tier1_category)) ? parsedAi.tier1_category : null;
  let categoryPrimary = (parsedAi?.category_primary && validPrimary.includes(parsedAi.category_primary)) ? parsedAi.category_primary : null;
  let itemType = (parsedAi?.item_type && validTypes.includes(parsedAi.item_type)) ? parsedAi.item_type : null;

  // 2. Keyword Fallback for Primary Category
  if (!categoryPrimary) {
    if (text.match(/convicted|conviction|verdict|guilty|sentence|sentenced|judge|court|legal|trial|crime|criminal|police|arrest|jail|prison|neglect|custody|lawsuit|attorney|prosecutor|판결|유죄|법원|징역|형사|방임|기소|선고/)) {
      categoryPrimary = 'CIVIC_CRIME_INCIDENT';
    } else if (text.match(/gguf|vllm|sglang|ollama|awq|fp8|int4|int8|quantization|추론|양자화|서빙|가속/)) {
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
    } else {
      categoryPrimary = 'INDUSTRY_TRENDS';
    }
  }

  // 3. IPTC Tier 1 Mapping
  if (!tier1) {
    if (['CIVIC_CRIME_INCIDENT'].includes(categoryPrimary) || text.match(/convicted|verdict|guilty|sentence|judge|court|legal|crime|police|arrest|lawsuit|prosecutor|판결|유죄|법원|형사|방임/)) {
      tier1 = 'LAW_CRIME_JUSTICE';
    } else if (['DEEP_SCIENCE_SPACE'].includes(categoryPrimary)) {
      tier1 = 'SCIENCE_RESEARCH';
    } else if (['MACRO_GLOBAL_BIZ'].includes(categoryPrimary)) {
      tier1 = 'ECONOMY_FINANCE';
    } else if (['HISTORY_LIFE_CULTURE'].includes(categoryPrimary)) {
      tier1 = 'CULTURE_HUMANITIES';
    } else {
      tier1 = 'TECH_COMPUTING';
    }
  }

  // 4. Artifact Type
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

  // 5. Item Type Classification
  if (!itemType) {
    if (tier1 === 'LAW_CRIME_JUSTICE' || tier1 === 'POLITICS_POLICY' || categoryPrimary === 'CIVIC_CRIME_INCIDENT' || text.match(/convicted|verdict|guilty|sentence|judge|court|legal|trial|crime|criminal|police|arrest|jail|prison|shooting|attack|minister|election|antitrust|lawsuit|prosecutor|판결|유죄|법원|형사|기소/)) {
      itemType = 'NEWS';
    } else if (artifactType === 'WEIGHTS' || text.match(/gguf|lora|safetensors|checkpoint|weights|7b|14b|70b|32b/) || platform.includes('models')) {
      itemType = 'MODEL';
    } else if (artifactType === 'SKILL_AGENT' || text.match(/agent|crawler|scraper|devtools|copilot/)) {
      itemType = 'AGENT';
    } else {
      itemType = 'TECH';
    }
  }

  return { categoryPrimary, tier1, artifactType, itemType };
}

module.exports = async (req, res) => {
  if (handleOptions(req, res, 'GET, POST, OPTIONS')) return;
  setCorsHeaders(res, 'GET, POST, OPTIONS');
  res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate');

  // Authorization policy:
  // - Public / Frontend / Cron / GHA triggers are allowed for micro-batch (limit <= 5).
  // - High-volume batches (limit > 5) require ADMIN_QUEUE_SECRET or CRON_SECRET.
  const adminSecret = process.env.ADMIN_QUEUE_SECRET || process.env.CRON_SECRET;
  const authHeader = req.headers.authorization || '';
  const customHeader = req.headers['x-admin-key'] || '';
  const querySecret = req.query?.secret || '';
  const provided = authHeader.startsWith('Bearer ') ? authHeader.substring(7) : (customHeader || querySecret);
  const isAdmin = Boolean(adminSecret && provided === adminSecret);

  const requestedLimit = parseInt(req.query?.limit, 10) || 1;
  const limit = isAdmin ? Math.min(Math.max(requestedLimit, 1), 5) : 1;

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
    // 2. Fetch unclassified records (FOR UPDATE SKIP LOCKED prevents concurrent workers from grabbing same row)
    const selectQuery = `
      SELECT id, inbox_id, source_platform, source_url, title, description, item_type, harvested_date, raw_payload
      FROM raw_trends_inbox
      WHERE is_classified = FALSE
      ORDER BY updated_at ASC NULLS FIRST, id DESC
      LIMIT $1
      FOR UPDATE SKIP LOCKED;
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
    const promptItems = candidates.map(c => {
      let topCommentsSnippet = '';
      try {
        const payload = typeof c.raw_payload === 'string' ? JSON.parse(c.raw_payload) : (c.raw_payload || {});
        const rawComments = Array.isArray(payload.raw_comments) ? payload.raw_comments : [];
        if (rawComments.length > 0) {
          // Sort comments by points descending to capture highest-signal community feedback
          const sorted = rawComments.slice().sort((a, b) => (b.points || 0) - (a.points || 0));
          const top3 = sorted.slice(0, 3).map(cm => `[@${cm.author || 'User'}]: ${(cm.text || '').replace(/\s+/g, ' ').slice(0, 140)}`);
          topCommentsSnippet = top3.join(' / ');
        }
      } catch (e) {}

      const itemObj = {
        id: c.inbox_id,
        platform: c.source_platform || 'Unknown',
        title: (c.title || '').slice(0, 150),
        description: (c.description || '').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 300)
      };
      if (topCommentsSnippet) {
        itemObj.community_feedback = topCommentsSnippet;
      }
      return itemObj;
    });

    const systemPrompt = `당신은 글로벌 최고 수준의 다국어 AI 기술 분석가 및 뉴스 번역 전문가입니다.
주어진 기술/뉴스 후보 목록을 분석하여, 각 항목마다 한국어(KO), 영어(EN), 중국어(ZH) 3개 국어 번역 제목, 1줄 훅(Hook), 'AI 3줄 핵심 요약'(언어별 3개씩: key_takeaways_ko, key_takeaways_en, key_takeaways_zh), 다국어 중복 방지를 위한 영문 표준 사건 식별키(canonical_story_key), 정규화된 기술 고유명칭(canonical_tech_entity), 핵심 영문 엔티티 목록(core_entities), 그리고 정확한 카테고리 분류를 반드시 아래 JSON 배열 형식으로만 응답하세요. 생각 과정이나 마크다운 등 기타 텍스트는 일절 출력하지 마세요.
중요 번역 및 정규화 규칙:
1. title_zh, hook_zh, key_takeaways_zh에는 반드시 실제 한자(간체자) 중국어 번역을 출력해야 합니다. 영어나 한국어를 그대로 복사하지 마세요.
2. title_ko, hook_ko, key_takeaways_ko에는 반드시 실제 한글(Hangul)로 작성된 자연스러운 고품질 한국어 요약을 출력하세요. 중국어 한자를 한국어 요약에 섞지 마세요.
3. title_en, hook_en, key_takeaways_en에는 정제된 전문 영문 제목, 훅, 요약을 출력하세요.
4. 법률, 재판, 판결, 범죄, 사회적 사건사고 기사는 절대로 TECH(기술)로 분류하지 말고 item_type: "NEWS", tier1_category: "LAW_CRIME_JUSTICE"로 정확히 분류해야 합니다.
5. canonical_tech_entity 정규화: 기술, 모델, 프레임워크 관련 기사는 반드시 소문자 하이픈 형식의 공식 표준 명칭 1개(예: 'qwen-image-2.1', 'jev', 'deepseek-r1', 'llama-3.2', 'vllm', 'flash-attn-3')를 정확히 추출하세요. 만약 일반 사회/정치/뉴스 기사라면 null을 반환하세요.
6. canonical_story_key 정규화 (뉴스·사건사고 중복 묶음용 필수): 기술뿐만 아니라 모든 일반 뉴스, 정책, 비즈니스, 사건 기사에 대해 동일한 토픽/사건을 다루는 기사들이 하나로 묶일 수 있도록 핵심 사건을 식별하는 고유 영어 소문자 하이픈 슬러그 3~5단어(예: 'google-antitrust-ruling', 'openai-for-profit-transition', 'flock-surveillance-traffic-stop', 'nvidia-blackwell-delay')를 반드시 정확하게 작성하세요.
7. 커뮤니티 피드백(community_feedback)이 포함된 경우, 대중의 핵심 반론이나 검증된 사실관계를 반영하여 단순 홍보가 아닌 균형 잡힌 팩트체크 Hook을 작성하세요.
[
  {
    "id": "item_id",
    "title_ko": "자연스러운 한국어 번역 제목",
    "hook_ko": "결정적 1줄 한국어 훅",
    "key_takeaways_ko": [
      "한국어로 작성된 첫 번째 핵심 요약 포인트",
      "한국어로 작성된 두 번째 핵심 요약 포인트",
      "한국어로 작성된 세 번째 핵심 요약 포인트"
    ],
    "title_en": "Refined Professional English Title",
    "hook_en": "Decisive 1-line English hook",
    "key_takeaways_en": [
      "First key takeaway in English",
      "Second key takeaway in English",
      "Third key takeaway in English"
    ],
    "title_zh": "精准吸引人的中文标题",
    "hook_zh": "直击核心亮点的中文一句话提炼",
    "key_takeaways_zh": [
      "中文第一条核心要点",
      "中文第二条核心要点",
      "中文第三条核心要点"
    ],
    "canonical_tech_entity": "소문자 하이픈 형식의 핵심 기술/모델 정규화 식별자 1개 (예: qwen-image-2.1, jev, deepseek-r1, vllm, 또는 일반 뉴스는 null)",
    "canonical_story_key": "영문 소문자 하이픈 슬러그 (기사/사건의 핵심 사건을 식별하는 고유 영어 키워드 3~5단어, 예: houthi-seize-red-sea-island, flock-veteran-surveillance-tracking, deepseek-v3-release)",
    "core_entities": ["핵심 기관/고유명사/사건의 표준 영문 명칭 2~4개, 예: Houthi, Red Sea, Zuqar Island"],
    "tier1_category": "TECH_COMPUTING, SCIENCE_RESEARCH, ECONOMY_FINANCE, POLITICS_POLICY, LAW_CRIME_JUSTICE, CULTURE_HUMANITIES 중 택1",
    "item_type": "MODEL, AGENT, TECH, NEWS 중 택1 (사회/법률/사건/일반뉴스는 반드시 NEWS)",
    "category_primary": "INFERENCE_OPT, AGENTS_DEVTOOLS, MULTIMODAL_AI, FOUNDATION_MODELS, INFRA_RAG_SECURITY, DEEP_SCIENCE_SPACE, MACRO_GLOBAL_BIZ, CIVIC_CRIME_INCIDENT, HISTORY_LIFE_CULTURE, INDUSTRY_TRENDS 중 택1",
    "programming_lang": "Python, TypeScript, Rust, General 중 택1"
  }
]`;

    let enrichedAiList = null;
    let modelUsed = null;
    let llmLatencySec = 0;

    let isQuotaExhausted = false;

    const isVercel = Boolean(process.env.VERCEL);
    const maxTotalBudget = isVercel ? 9200 : 30000;
    const defaultPerModelTimeout = isVercel ? 4500 : 15000;

    // Call OpenRouter with fast fallback models and dynamic time budget (within Vercel serverless 10s limit)
    for (const modelName of FREE_MODELS) {
      const budgetMs = maxTotalBudget - (Date.now() - startTime);
      if (budgetMs < 1800) {
        console.warn(`[Worker] Time budget exhausted (${budgetMs}ms left). Breaking early.`);
        break;
      }
      const callStart = Date.now();
      let timeoutId = null;
      try {
        const controller = new AbortController();
        const timeoutMs = Math.min(defaultPerModelTimeout, budgetMs);
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
            max_tokens: 2500,
            reasoning: { max_tokens: 0 }
          }),
          signal: controller.signal
        });

        if (!aiResponse.ok) {
          console.warn(`[Worker] ${modelName} returned HTTP ${aiResponse.status} (${((Date.now() - callStart) / 1000).toFixed(2)}s)`);
          if (aiResponse.status === 429) {
            try {
              const errBody = await aiResponse.text();
              if (errBody.includes('daily') || errBody.includes('quota') || errBody.includes('exceeded')) {
                isQuotaExhausted = true;
              }
            } catch (e) {}
          }
          continue;
        }

        const aiJson = await aiResponse.json();
        if (timeoutId) { clearTimeout(timeoutId); timeoutId = null; }

        llmLatencySec = ((Date.now() - callStart) / 1000).toFixed(2);
        const msgObj = aiJson.choices?.[0]?.message;
        const rawContent = (msgObj?.content && msgObj.content.trim()) ? msgObj.content : (msgObj?.reasoning || '');
        const parsed = sanitizeJsonString(rawContent);

        if (Array.isArray(parsed) && parsed.length > 0) {
          // Check Korean and Chinese character guardrails
          const hasKorean = parsed.some(p => /[\uac00-\ud7a3]/.test(p.title_ko || p.korean_title || ''));
          const hasChinese = parsed.some(p => /[\u4e00-\u9fff]/.test(p.title_zh || ''));
          const hasBrokenBytes = parsed.some(p => /[\ufffd]/.test((p.title_ko || p.korean_title || '') + ' ' + (p.hook_ko || '')));
          const hasHanziOnly = parsed.some(p => /[\u4e00-\u9fff]/.test(p.title_ko || p.korean_title || '') && !/[\uac00-\ud7a3]/.test(p.title_ko || p.korean_title || ''));
          
          // Check if Korean takeaways leaked Hanzi without Hangul
          const hasHanziOnlyTakeaways = parsed.some(p => {
            const koTake = p.key_takeaways_ko || p.key_takeaways;
            if (Array.isArray(koTake) && koTake.length > 0) {
              const first = String(koTake[0]);
              return /[\u4e00-\u9fff]/.test(first) && !/[\uac00-\ud7a3]/.test(first);
            }
            return false;
          });

          if (hasKorean && hasChinese && !hasBrokenBytes && !hasHanziOnly && !hasHanziOnlyTakeaways) {
            enrichedAiList = parsed;
            modelUsed = aiJson.model || modelName;
            break;
          } else {
            console.warn(`[Worker] Model ${modelName} rejected: hasKorean=${hasKorean}, hasChinese=${hasChinese}, hasBrokenBytes=${hasBrokenBytes}, hasHanziOnly=${hasHanziOnly}, hasHanziOnlyTakeaways=${hasHanziOnlyTakeaways}`);
          }
        }
      } catch (err) {
        console.warn(`[Worker] Model ${modelName} error (${((Date.now() - callStart) / 1000).toFixed(2)}s): ${err.message}`);
      } finally {
        if (timeoutId) clearTimeout(timeoutId);
      }
    }

    // CRITICAL: If all models failed, touch candidates' updated_at so they move to the back of the queue!
    // This completely eliminates Head-of-Line blocking (deadlock on 1 bad item).
    if (!enrichedAiList || enrichedAiList.length === 0) {
      console.warn(`[Worker] All LLM models failed or timed out. Rotating ${candidates.length} item(s) to back of queue.`);
      const candIds = candidates.map(c => c.id);
      await pool.query('UPDATE raw_trends_inbox SET updated_at = CURRENT_TIMESTAMP WHERE id = ANY($1::int[]);', [candIds]);
      return res.status(200).json({
        status: isQuotaExhausted ? 'quota_exhausted' : 'partial_fallback',
        is_quota_exhausted: isQuotaExhausted,
        reset_kst: '09:00 KST',
        message: isQuotaExhausted 
          ? 'OpenRouter free daily quota (1,000/day) reached. Pausing worker until 09:00 KST reset.'
          : 'Free LLM models temporarily busy or timed out. Shifted items back in queue to allow others to process.',
        processed_count: 0,
        remaining_unclassified: totalRemaining
      });
    }

    const resMap = {};
    if (enrichedAiList) {
      for (const item of enrichedAiList) {
        if (item.id) resMap[item.id] = item;
      }
    }

    const processedItems = [];

    const koreanRegex = /[\uac00-\ud7a3]/;
    const chineseRegex = /[\u4e00-\u9fff]/;

    // 4. Update Database for each item
    for (let i = 0; i < candidates.length; i++) {
      const cand = candidates[i];
      let aiData = resMap[cand.inbox_id];
      // Positional fallback if LLM omitted or altered the item ID
      if (!aiData && enrichedAiList && enrichedAiList[i]) {
        aiData = enrichedAiList[i];
      }
      
      const titleKoCandidate = (aiData?.title_ko || aiData?.korean_title || '').trim();
      const hookKoCandidate = (aiData?.hook_ko || '').trim();
      const titleEnCandidate = (aiData?.title_en || '').trim();
      const hookEnCandidate = (aiData?.hook_en || '').trim();
      const titleZhCandidate = (aiData?.title_zh || '').trim();
      const hookZhCandidate = (aiData?.hook_zh || '').trim();

      // Extract multilingual takeaways
      const rawTakeawaysKo = Array.isArray(aiData?.key_takeaways_ko) 
        ? aiData.key_takeaways_ko 
        : (Array.isArray(aiData?.key_takeaways) ? aiData.key_takeaways : []);
      
      let takeawaysKo = rawTakeawaysKo
        .map(t => String(t).replace(/^[-*•\d.]\s*/, '').trim())
        .filter(Boolean)
        .slice(0, 3);

      // Chinese takeaway extraction
      const rawTakeawaysZh = Array.isArray(aiData?.key_takeaways_zh) ? aiData.key_takeaways_zh : [];
      let takeawaysZh = rawTakeawaysZh
        .map(t => String(t).replace(/^[-*•\d.]\s*/, '').trim())
        .filter(Boolean)
        .slice(0, 3);

      // If takeawaysKo contains pure Hanzi without Hangul, it is Chinese leaking into Korean!
      if (takeawaysKo.length > 0 && chineseRegex.test(takeawaysKo[0]) && !koreanRegex.test(takeawaysKo[0])) {
        if (takeawaysZh.length === 0) {
          takeawaysZh = takeawaysKo;
        }
        takeawaysKo = []; // Invalidate Korean so it won't leak
      }

      // English takeaway extraction
      const rawTakeawaysEn = Array.isArray(aiData?.key_takeaways_en) ? aiData.key_takeaways_en : [];
      let takeawaysEn = rawTakeawaysEn
        .map(t => String(t).replace(/^[-*•\d.]\s*/, '').trim())
        .filter(Boolean)
        .slice(0, 3);

      const hasKoreanTitle = koreanRegex.test(titleKoCandidate);
      const hasKoreanHook = koreanRegex.test(hookKoCandidate);
      const hasHanziOnlyTitle = chineseRegex.test(titleKoCandidate) && !koreanRegex.test(titleKoCandidate);
      const isValidKorean = hasKoreanTitle && hasKoreanHook && !hasHanziOnlyTitle;

      // Chinese validation: MUST contain actual Chinese Hanzi characters!
      const hasChineseTitle = chineseRegex.test(titleZhCandidate);
      const isValidChinese = hasChineseTitle;

      // CRITICAL GUARDRAIL: Never mark as classified if valid Korean or Chinese translation is missing!
      // Touch updated_at so unclassified item rotates to back of queue instead of blocking indefinitely.
      if (!aiData || !isValidKorean || !isValidChinese) {
        console.warn(`[Worker] Skipping ${cand.inbox_id}: Missing/invalid trilingual output (ko: ${isValidKorean}, zh: ${isValidChinese}). Rotating item.`);
        await pool.query('UPDATE raw_trends_inbox SET updated_at = CURRENT_TIMESTAMP WHERE id = $1;', [cand.id]);
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
      const titleEn = titleEnCandidate || aiData?.title_en || payload.title_en || cleanTitle;
      const titleZh = titleZhCandidate;

      const hookKo = hookKoCandidate;
      const hookEn = hookEnCandidate || aiData?.hook_en || payload.hook_en || cleanTitle;
      const hookZh = hookZhCandidate || titleZhCandidate;

      // Ensure key_takeaways has 3 valid points (with fallback to hook/title if LLM returned fewer)
      const finalTakeaways = takeawaysKo.length > 0 
        ? takeawaysKo 
        : (Array.isArray(payload.multilingual?.ko?.key_takeaways) && payload.multilingual.ko.key_takeaways.length > 0 && koreanRegex.test(payload.multilingual.ko.key_takeaways[0] || '')
            ? payload.multilingual.ko.key_takeaways 
            : [hookKo || titleKo]);

      const finalTakeawaysEn = takeawaysEn.length > 0
        ? takeawaysEn
        : (Array.isArray(payload.multilingual?.en?.key_takeaways) && payload.multilingual.en.key_takeaways.length > 0 && !koreanRegex.test(payload.multilingual.en.key_takeaways[0] || '')
            ? payload.multilingual.en.key_takeaways
            : [hookEn || titleEn]);

      const finalTakeawaysZh = takeawaysZh.length > 0
        ? takeawaysZh
        : (Array.isArray(payload.multilingual?.zh?.key_takeaways) && payload.multilingual.zh.key_takeaways.length > 0 && chineseRegex.test(payload.multilingual.zh.key_takeaways[0] || '')
            ? payload.multilingual.zh.key_takeaways
            : [hookZh || titleZh]);

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

      // 🌟 Universal Cross-Lingual Deduplication Fingerprint
      const canonicalKey = (aiData?.canonical_story_key || '')
        .toLowerCase()
        .trim()
        .replace(/[^a-z0-9-]/g, '-')
        .replace(/-+/g, '-')
        .replace(/^-|-$/g, '')
        .slice(0, 100);

      const coreEntities = Array.isArray(aiData?.core_entities)
        ? aiData.core_entities.map(e => String(e).trim()).filter(e => e.length > 1).slice(0, 5)
        : [];

      const canonicalTechEntity = (aiData?.canonical_tech_entity || '')
        .toLowerCase()
        .trim()
        .replace(/[^a-z0-9-]/g, '-')
        .replace(/-+/g, '-')
        .replace(/^-|-$/g, '')
        .slice(0, 50);

      if (canonicalTechEntity && canonicalTechEntity !== 'null' && canonicalTechEntity !== 'none' && canonicalTechEntity.length >= 2) {
        payload.canonical_tech_entity = canonicalTechEntity;
      }

      if (canonicalKey) {
        payload.canonical_story_key = canonicalKey;
        payload.dedup_fingerprint = {
          canonical_story_key: canonicalKey,
          canonical_tech_entity: payload.canonical_tech_entity || null,
          core_entities: coreEntities
        };
      }

      payload.multilingual = {
        ko: { title: titleKo, hook: hookKo, key_takeaways: finalTakeaways },
        en: { title: titleEn, hook: hookEn, key_takeaways: finalTakeawaysEn },
        zh: { title: titleZh, hook: hookZh, key_takeaways: finalTakeawaysZh }
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
        canonical_story_key: canonicalKey || null,
        core_entities: coreEntities,
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
        title_en: titleEn,
        title_zh: titleZh,
        hook_ko: hookKo,
        hook_en: hookEn,
        hook_zh: hookZh,
        key_takeaways: finalTakeaways,
        key_takeaways_ko: finalTakeaways,
        key_takeaways_en: finalTakeawaysEn,
        key_takeaways_zh: finalTakeawaysZh,
        multilingual: payload.multilingual,
        tier1_category: inferred.tier1,
        category_primary: inferred.categoryPrimary,
        item_type: inferred.itemType,
        enriched_by_model: modelUsed || 'openrouter-free'
      });
    }

    const totalDurationSec = ((Date.now() - startTime) / 1000).toFixed(2);
    const newRemaining = Math.max(0, totalRemaining - processedItems.length);

    // Record execution log in vercel_worker_logs & update telemetry
    if (processedItems.length > 0) {
      try {
        await pool.query(`
          INSERT INTO vercel_worker_logs (worker_name, model_used, processed_count, duration_seconds, remaining_count, status, inbox_ids)
          VALUES ('Vercel Serverless AI Enricher', $1, $2, $3, $4, 'SUCCESS', $5);
        `, [
          modelUsed || 'openrouter-free',
          processedItems.length,
          parseFloat(totalDurationSec),
          newRemaining,
          JSON.stringify(processedItems.map(p => p.inbox_id))
        ]);

        await pool.query(`
          UPDATE vercel_serverless_telemetry
          SET invocations = CASE 
                WHEN date_trunc('month', last_invoked_at) < date_trunc('month', CURRENT_TIMESTAMP) THEN 1
                ELSE invocations + 1
              END,
              active_cpu_seconds = CASE 
                WHEN date_trunc('month', last_invoked_at) < date_trunc('month', CURRENT_TIMESTAMP) THEN 0.025
                ELSE active_cpu_seconds + 0.025
              END,
              bandwidth_bytes = CASE 
                WHEN date_trunc('month', last_invoked_at) < date_trunc('month', CURRENT_TIMESTAMP) THEN 5000
                ELSE bandwidth_bytes + 5000
              END,
              last_invoked_at = CURRENT_TIMESTAMP
          WHERE id = 1;
        `);
      } catch (logErr) {
        console.warn('[Worker Log Record Error]:', logErr.message);
      }
    }

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
