
// ================= DATA STORE & REPOSITORIES (SINGLE SOURCE OF TRUTH) =================
const AppStore = {
  _itemsMap: new Map(),
  _cases: [],
  _models: [],
  _news: [],
  _inbox: [],

  init(data) {
    if (!data) return;
    this._itemsMap.clear();
    this._cases = Array.isArray(data) ? data : (data.cases || []);
    this._models = data.model_items || [];
    this._news = data.news_items || [];
    this._inbox = data.inbox_items || [];

    // Centralized index across all harvested candidates, news, and AI models
    [...this._inbox, ...this._news, ...this._models].forEach(it => {
      const id = it.inbox_id || it.id;
      if (id && !this._itemsMap.has(id)) {
        this._itemsMap.set(id, it);
      }
    });

    // Provide reactive views to existing global arrays for backward compatibility
    casesData = this._cases;
    modelsData = this._models;
    newsData = this._news;
    inboxData = this._inbox;

    liveCasesData = this._cases;
    liveModelsData = this._models;
    liveNewsData = this._news;
    liveInboxData = this._inbox;

    if (data.actions_telemetry) {
      actionsTelemetryData = data.actions_telemetry;
    }
  },

  getItem(id) {
    return this._itemsMap.get(id);
  },

  updateItem(id, patch) {
    const it = this._itemsMap.get(id);
    if (it && patch) {
      Object.assign(it, patch);
    }
  },

  getCases() { return this._cases; },
  getModels() { return this._models; },
  getNews() { return this._news; },
  getInbox() { return this._inbox; }
};
window.AppStore = AppStore;

// ================= UNIVERSAL ASYNC DATA HYDRATION LAYER =================
async function bootstrapApplicationData() {
  console.log('[Bootstrap] Initializing asynchronous data hydration...');
  try {
    // 1. Try loading static data.json (works on both local server and GitHub Pages)
    const staticRes = await fetch('data.json', { cache: 'no-cache' });
    if (staticRes.ok) {
      const data = await staticRes.json();
      adminData = data.admin_stats || {};
      graphData = data.graph || { nodes: [], links: [] };
      timeline24hData = data.timeline_24h || [];
      actionsTelemetryData = data.actions_telemetry || {};
      trend6hData = data.trend_6h || {};
      trendRadarData = data.trend_radar || {};

      AppStore.init(data);

      console.log(`[Bootstrap] Loaded ${AppStore.getCases().length} dossiers, ${AppStore.getNews().length} news, ${AppStore.getModels().length} models from data.json.`);
    }
  } catch (e) {
    console.warn('[Bootstrap] Static data.json fetch skipped/failed, relying on live Neon APIs:', e.message);
  }

  updateGlobalStatsUI();

  // Restore user saved language preference if previously selected
  try {
    const savedLang = localStorage.getItem('factcheck_lang');
    if (savedLang && ['KO', 'ZH', 'EN'].includes(savedLang) && savedLang !== 'KO') {
      setLanguage(savedLang);
    }
  } catch (e) {}

  // Initial render with loaded data
  try { renderCards(); } catch(e) {}
  try { renderHomeTopPicks(); } catch(e) {}
  try { renderTimeline24h(); } catch(e) {}
  try { renderTrendRadar(); } catch(e) {}
  try { renderModels(); } catch(e) {}
  try { renderNews(); } catch(e) {}
  try { renderInbox(); } catch(e) {}
  try { renderTelemetryCharts(); } catch(e) {}
  try { if (window.lucide) window.lucide.createIcons(); } catch(e) {}

  // 2. Perform live DB sync in background (non-blocking, instant 0ms page load)
  setTimeout(() => {
    syncFromNeonLiveDB(false)
      .then(() => updateGlobalStatsUI())
      .catch(e => console.warn('[Bootstrap] Live DB sync completed or skipped:', e.message));
  }, 100);
}


// Asynchronously Hydrated Data Stores (Decoupled from Monolithic HTML)
let casesData = [];
let modelsData = [];
let newsData = [];
let inboxData = [];
let adminData = {};
let graphData = { nodes: [], links: [] };
let timeline24hData = [];
let actionsTelemetryData = {};
let trend6hData = {};
let trendRadarData = {};

    let liveCasesData = casesData;
    let liveModelsData = modelsData;
    let liveInboxData = inboxData;
    let liveNewsData = newsData;
    let liveAnalysesData = [];

function updateGlobalStatsUI() {
  const safeSet = (id, txt) => { const el = document.getElementById(id); if (el) el.textContent = txt; };
  const numCases = (typeof liveCasesData !== 'undefined' && liveCasesData.length) || 49;
  const numNews = (typeof liveNewsData !== 'undefined' && liveNewsData.length) || 1251;
  const numModels = (typeof liveModelsData !== 'undefined' && liveModelsData.length) || 175;
  const numInbox = (typeof liveInboxData !== 'undefined' && liveInboxData.length) || 1805;

  safeSet('statValVerified', numCases);
  safeSet('statValNews', numNews);
  safeSet('statValModels', numModels);
  safeSet('statValInbox', numInbox.toLocaleString());

  safeSet('headerVerifiedCount', `(${numCases})`);
  safeSet('headerNewsCount', `(${numNews})`);
  safeSet('headerModelsCount', `(${numModels})`);
  safeSet('headerInboxCount', `(${numInbox})`);

  // 수집 건수 vs AI 요약분석 완료 건수 분리 계산
  const inbList = typeof liveInboxData !== 'undefined' ? liveInboxData : [];
  const enrichedInbox = inbList.filter(x => x.is_classified || x.ai_enrichment).length;
  const pendingInbox = Math.max(0, numInbox - enrichedInbox);
  const enrichedPct = numInbox > 0 ? ((enrichedInbox / numInbox) * 100).toFixed(1) : '100.0';

  safeSet('statInboxEnrichedText', `● 요약 ${enrichedInbox.toLocaleString()}건 (${enrichedPct}%)`);
  safeSet('statInboxPendingText', `· 대기 ${pendingInbox.toLocaleString()}건`);

  const casesList = typeof liveCasesData !== 'undefined' ? liveCasesData : [];
  const trueCount = casesList.filter(c => c.verdict === 'VERIFIED_TRUE').length;
  const halfCount = numCases - trueCount;
  safeSet('statVerifiedTrue', `● ${trueCount} 사실`);
  safeSet('statHalfTrue', `● ${halfCount} 부분`);

  safeSet('heroAuditCount', `● ${numCases}개 기술 검증 완료`);

  // Update Category & Tier 2 pills dynamically
  if (typeof updateNewsCategoryPillCounts === 'function') {
    updateNewsCategoryPillCounts();
  }
  if (typeof updateModelCategoryPillCounts === 'function') {
    updateModelCategoryPillCounts();
  }
}
window.updateGlobalStatsUI = updateGlobalStatsUI;

function updateNewsCategoryPillCounts() {
  const items = (typeof liveNewsData !== 'undefined' && liveNewsData.length) ? liveNewsData : [];
  const total = items.length;
  const t1Counts = {
    TECH_COMPUTING: 0,
    SCIENCE_RESEARCH: 0,
    ECONOMY_FINANCE: 0,
    LAW_CRIME_JUSTICE: 0,
    POLITICS_POLICY: 0,
    CULTURE_HUMANITIES: 0
  };
  const t2Counts = {
    INFERENCE_OPT: 0,
    AGENTS_DEVTOOLS: 0,
    MULTIMODAL_AI: 0,
    FOUNDATION_MODELS: 0,
    INFRA_RAG_SECURITY: 0,
    INDUSTRY_TRENDS: 0
  };

  items.forEach(it => {
    const t1 = it.tier1_category || 'TECH_COMPUTING';
    if (t1 in t1Counts) t1Counts[t1]++;
    else t1Counts.TECH_COMPUTING++;

    const t2 = it.category_primary || it.tier2_category || 'INDUSTRY_TRENDS';
    if (t2 in t2Counts) t2Counts[t2]++;
    else t2Counts.INDUSTRY_TRENDS++;
  });

  const lang = (typeof currentLang !== 'undefined' ? currentLang : 'KO');

  const t1Labels = {
    KO: {
      ALL: `전체 (${total.toLocaleString()})`,
      TECH_COMPUTING: `💻 IT·컴퓨팅 (${t1Counts.TECH_COMPUTING.toLocaleString()})`,
      SCIENCE_RESEARCH: `🚀 과학·우주 (${t1Counts.SCIENCE_RESEARCH.toLocaleString()})`,
      ECONOMY_FINANCE: `🏦 경제·금융 (${t1Counts.ECONOMY_FINANCE.toLocaleString()})`,
      LAW_CRIME_JUSTICE: `⚖️ 사회·법률 (${t1Counts.LAW_CRIME_JUSTICE.toLocaleString()})`,
      POLITICS_POLICY: `🏛️ 정치·정책 (${t1Counts.POLITICS_POLICY.toLocaleString()})`,
      CULTURE_HUMANITIES: `🌿 문화·인문 (${t1Counts.CULTURE_HUMANITIES.toLocaleString()})`
    },
    ZH: {
      ALL: `全部 (${total.toLocaleString()})`,
      TECH_COMPUTING: `💻 IT与计算 (${t1Counts.TECH_COMPUTING.toLocaleString()})`,
      SCIENCE_RESEARCH: `🚀 科学与航天 (${t1Counts.SCIENCE_RESEARCH.toLocaleString()})`,
      ECONOMY_FINANCE: `🏦 经济与金融 (${t1Counts.ECONOMY_FINANCE.toLocaleString()})`,
      LAW_CRIME_JUSTICE: `⚖️ 社会与法治 (${t1Counts.LAW_CRIME_JUSTICE.toLocaleString()})`,
      POLITICS_POLICY: `🏛️ 政治与政策 (${t1Counts.POLITICS_POLICY.toLocaleString()})`,
      CULTURE_HUMANITIES: `🌿 文化与人文 (${t1Counts.CULTURE_HUMANITIES.toLocaleString()})`
    },
    EN: {
      ALL: `All (${total.toLocaleString()})`,
      TECH_COMPUTING: `💻 IT & Computing (${t1Counts.TECH_COMPUTING.toLocaleString()})`,
      SCIENCE_RESEARCH: `🚀 Science & Space (${t1Counts.SCIENCE_RESEARCH.toLocaleString()})`,
      ECONOMY_FINANCE: `🏦 Economy & Finance (${t1Counts.ECONOMY_FINANCE.toLocaleString()})`,
      LAW_CRIME_JUSTICE: `⚖️ Society & Law (${t1Counts.LAW_CRIME_JUSTICE.toLocaleString()})`,
      POLITICS_POLICY: `🏛️ Policy & Politics (${t1Counts.POLITICS_POLICY.toLocaleString()})`,
      CULTURE_HUMANITIES: `🌿 Culture & Arts (${t1Counts.CULTURE_HUMANITIES.toLocaleString()})`
    }
  };

  const t2Labels = {
    KO: {
      ALL: `전체 IT 분야`,
      INFERENCE_OPT: `⚡ 추론·서빙 (${t2Counts.INFERENCE_OPT.toLocaleString()})`,
      AGENTS_DEVTOOLS: `🛠️ 에이전트·도구 (${t2Counts.AGENTS_DEVTOOLS.toLocaleString()})`,
      MULTIMODAL_AI: `🎨 멀티모달 (${t2Counts.MULTIMODAL_AI.toLocaleString()})`,
      FOUNDATION_MODELS: `🤖 파운데이션 (${t2Counts.FOUNDATION_MODELS.toLocaleString()})`,
      INFRA_RAG_SECURITY: `🛡️ 인프라·보안 (${t2Counts.INFRA_RAG_SECURITY.toLocaleString()})`,
      INDUSTRY_TRENDS: `🌐 일반 SW·웹 (${t2Counts.INDUSTRY_TRENDS.toLocaleString()})`
    },
    ZH: {
      ALL: `全部 IT 领域`,
      INFERENCE_OPT: `⚡ 推理与服务 (${t2Counts.INFERENCE_OPT.toLocaleString()})`,
      AGENTS_DEVTOOLS: `🛠️ 智能体与工具 (${t2Counts.AGENTS_DEVTOOLS.toLocaleString()})`,
      MULTIMODAL_AI: `🎨 多模态 (${t2Counts.MULTIMODAL_AI.toLocaleString()})`,
      FOUNDATION_MODELS: `🤖 基础模型 (${t2Counts.FOUNDATION_MODELS.toLocaleString()})`,
      INFRA_RAG_SECURITY: `🛡️ 基础架构与安全 (${t2Counts.INFRA_RAG_SECURITY.toLocaleString()})`,
      INDUSTRY_TRENDS: `🌐 软件与行业动态 (${t2Counts.INDUSTRY_TRENDS.toLocaleString()})`
    },
    EN: {
      ALL: `All Tech Fields`,
      INFERENCE_OPT: `⚡ Inference & Serving (${t2Counts.INFERENCE_OPT.toLocaleString()})`,
      AGENTS_DEVTOOLS: `🛠️ Agents & DevTools (${t2Counts.AGENTS_DEVTOOLS.toLocaleString()})`,
      MULTIMODAL_AI: `🎨 Multimodal (${t2Counts.MULTIMODAL_AI.toLocaleString()})`,
      FOUNDATION_MODELS: `🤖 Foundation Models (${t2Counts.FOUNDATION_MODELS.toLocaleString()})`,
      INFRA_RAG_SECURITY: `🛡️ Infra & Security (${t2Counts.INFRA_RAG_SECURITY.toLocaleString()})`,
      INDUSTRY_TRENDS: `🌐 General SW & Web (${t2Counts.INDUSTRY_TRENDS.toLocaleString()})`
    }
  };

  const curDict1 = t1Labels[lang] || t1Labels.KO;
  document.querySelectorAll('.news-cat-pill').forEach(btn => {
    const cat = btn.getAttribute('data-cat');
    if (curDict1 && curDict1[cat]) {
      btn.textContent = curDict1[cat];
    }
  });

  const curDict2 = t2Labels[lang] || t2Labels.KO;
  document.querySelectorAll('.news-t2-pill').forEach(btn => {
    const t2 = btn.getAttribute('data-t2');
    if (curDict2 && curDict2[t2]) {
      btn.textContent = curDict2[t2];
    }
  });
}
window.updateNewsCategoryPillCounts = updateNewsCategoryPillCounts;

function updateModelCategoryPillCounts() {
  const items = (typeof liveModelsData !== 'undefined' && liveModelsData.length) ? liveModelsData : [];
  const total = items.length;
  const fCounts = {
    ALL: total,
    Qwen: 0,
    Wan: 0,
    MiniMax: 0,
    FLUX: 0,
    GLM: 0,
    DeepSeek: 0,
    Hunyuan: 0,
    Audio: 0,
    Standalone: 0
  };
  const artCounts = {
    ALL: total,
    WEIGHTS: 0,
    WEB_SERVICE: 0,
    FINETUNE: 0
  };

  items.forEach(it => {
    const fam = (it.model_family || '').toLowerCase();
    if (fam.includes('qwen')) fCounts.Qwen++;
    else if (fam.includes('wan')) fCounts.Wan++;
    else if (fam.includes('minimax')) fCounts.MiniMax++;
    else if (fam.includes('flux')) fCounts.FLUX++;
    else if (fam.includes('glm')) fCounts.GLM++;
    else if (fam.includes('deepseek')) fCounts.DeepSeek++;
    else if (fam.includes('hunyuan')) fCounts.Hunyuan++;
    else if (fam.includes('audio') || fam.includes('speech') || fam.includes('tts') || fam.includes('whisper')) fCounts.Audio++;
    else fCounts.Standalone++;

    const art = it.artifact_type || (it.source_platform?.includes('Spaces') ? 'WEB_SERVICE' : 'WEIGHTS');
    if (art in artCounts) artCounts[art]++;
    else artCounts.WEIGHTS++;
  });

  const lang = (typeof currentLang !== 'undefined' ? currentLang : 'KO');

  const famLabels = {
    KO: {
      ALL: `전체 패밀리 (${total})`,
      Qwen: `Qwen (${fCounts.Qwen})`,
      Wan: `Wan 비디오 (${fCounts.Wan})`,
      MiniMax: `MiniMax (${fCounts.MiniMax})`,
      FLUX: `FLUX 이미지 (${fCounts.FLUX})`,
      GLM: `GLM (${fCounts.GLM})`,
      DeepSeek: `DeepSeek (${fCounts.DeepSeek})`,
      Hunyuan: `Hunyuan (${fCounts.Hunyuan})`,
      Audio: `음성/TTS (${fCounts.Audio})`,
      Standalone: `독립/신규 모델 (${fCounts.Standalone})`
    },
    ZH: {
      ALL: `全部系列 (${total})`,
      Qwen: `Qwen (${fCounts.Qwen})`,
      Wan: `Wan 视频 (${fCounts.Wan})`,
      MiniMax: `MiniMax (${fCounts.MiniMax})`,
      FLUX: `FLUX 图像 (${fCounts.FLUX})`,
      GLM: `GLM (${fCounts.GLM})`,
      DeepSeek: `DeepSeek (${fCounts.DeepSeek})`,
      Hunyuan: `Hunyuan (${fCounts.Hunyuan})`,
      Audio: `语音/TTS (${fCounts.Audio})`,
      Standalone: `独立/新模型 (${fCounts.Standalone})`
    },
    EN: {
      ALL: `All Families (${total})`,
      Qwen: `Qwen (${fCounts.Qwen})`,
      Wan: `Wan Video (${fCounts.Wan})`,
      MiniMax: `MiniMax (${fCounts.MiniMax})`,
      FLUX: `FLUX Image (${fCounts.FLUX})`,
      GLM: `GLM (${fCounts.GLM})`,
      DeepSeek: `DeepSeek (${fCounts.DeepSeek})`,
      Hunyuan: `Hunyuan (${fCounts.Hunyuan})`,
      Audio: `Audio/TTS (${fCounts.Audio})`,
      Standalone: `Standalone Models (${fCounts.Standalone})`
    }
  };

  const artLabels = {
    KO: {
      ALL: `전체 (${total})`,
      WEIGHTS: `🤖 가중치·체크포인트 (${artCounts.WEIGHTS})`,
      WEB_SERVICE: `🌐 인터랙티브 데모·Spaces (${artCounts.WEB_SERVICE})`,
      FINETUNE: `🎯 특화 파인튜닝 (${artCounts.FINETUNE})`
    },
    ZH: {
      ALL: `全部 (${total})`,
      WEIGHTS: `🤖 模型权重·检查点 (${artCounts.WEIGHTS})`,
      WEB_SERVICE: `🌐 在线演示·Spaces (${artCounts.WEB_SERVICE})`,
      FINETUNE: `🎯 定制微调 (${artCounts.FINETUNE})`
    },
    EN: {
      ALL: `All (${total})`,
      WEIGHTS: `🤖 Weights & Checkpoints (${artCounts.WEIGHTS})`,
      WEB_SERVICE: `🌐 Interactive Demos / Spaces (${artCounts.WEB_SERVICE})`,
      FINETUNE: `🎯 Specialized Finetunes (${artCounts.FINETUNE})`
    }
  };

  const curFamDict = famLabels[lang] || famLabels.KO;
  document.querySelectorAll('.model-fam-pill').forEach(btn => {
    const fam = btn.getAttribute('data-fam');
    if (curFamDict && curFamDict[fam]) {
      btn.textContent = curFamDict[fam];
    }
  });

  const curArtDict = artLabels[lang] || artLabels.KO;
  document.querySelectorAll('.model-art-pill').forEach(btn => {
    const art = btn.getAttribute('data-art');
    if (curArtDict && curArtDict[art]) {
      btn.textContent = curArtDict[art];
    }
  });
}
window.updateModelCategoryPillCounts = updateModelCategoryPillCounts;

    const API_BASE = '';

    let currentLang = 'KO';
    let currentView = 'home';
    let currentMode = 'ALL';
    let currentDomain = 'ALL';
    let currentSort = 'date-audit-desc';
    let searchQuery = '';

    let currentInboxSource = 'ALL';
    let inboxSearchQuery = '';
    let isFamilyGroupingActive = true;
    let currentGraphType = 'ALL';
    let simulationRef = null;

    // 📄 Global Pagination State (15 items per page for 3x5 Grid: << < 1, 2, 3, 4, 5 > >>)
    const PAGE_SIZE = 15;
    let currentPortfolioPage = 1;
    let currentModelsPage = 1;
    let currentNewsPage = 1;
    let currentInboxPage = 1;

    function renderPagination(containerId, currentPage, totalPages, onPageChange) {
      const container = document.getElementById(containerId);
      if (!container) return;
      if (totalPages <= 1) {
        container.innerHTML = '';
        return;
      }

      let html = '<div class="flex items-center justify-center gap-1.5 pt-6 pb-4 text-xs font-mono select-none flex-wrap">';

      // First Page <<
      const firstDisabled = currentPage === 1;
      html += `<button onclick="${firstDisabled ? '' : onPageChange + '(1)'}" class="px-2.5 py-1.5 rounded-lg border font-bold transition shadow-xs ${firstDisabled ? 'opacity-30 cursor-not-allowed bg-surface-subtle text-ink-muted border-surface-border' : 'bg-white hover:bg-surface-subtle text-ink-primary border-surface-border cursor-pointer'}" title="처음으로">&laquo;&laquo;</button>`;

      // Prev Page <
      const prevDisabled = currentPage === 1;
      html += `<button onclick="${prevDisabled ? '' : onPageChange + '(' + (currentPage - 1) + ')'}" class="px-2.5 py-1.5 rounded-lg border font-bold transition shadow-xs ${prevDisabled ? 'opacity-30 cursor-not-allowed bg-surface-subtle text-ink-muted border-surface-border' : 'bg-white hover:bg-surface-subtle text-ink-primary border-surface-border cursor-pointer'}" title="이전">&lsaquo;</button>`;

      // Page numbers (Sliding window of up to 5 numbers)
      let startPage = Math.max(1, currentPage - 2);
      let endPage = Math.min(totalPages, startPage + 4);
      if (endPage - startPage < 4) {
        startPage = Math.max(1, endPage - 4);
      }

      for (let p = startPage; p <= endPage; p++) {
        const isCur = p === currentPage;
        const btnStyle = isCur
          ? 'bg-indigo-600 text-white font-extrabold border-indigo-600 shadow-sm'
          : 'bg-white hover:bg-surface-subtle text-ink-secondary hover:text-ink-primary border-surface-border font-semibold cursor-pointer';
        html += `<button onclick="${onPageChange}(${p})" class="w-8 h-8 rounded-lg border flex items-center justify-center transition ${btnStyle}">${p}</button>`;
      }

      // Next Page >
      const nextDisabled = currentPage === totalPages;
      html += `<button onclick="${nextDisabled ? '' : onPageChange + '(' + (currentPage + 1) + ')'}" class="px-2.5 py-1.5 rounded-lg border font-bold transition shadow-xs ${nextDisabled ? 'opacity-30 cursor-not-allowed bg-surface-subtle text-ink-muted border-surface-border' : 'bg-white hover:bg-surface-subtle text-ink-primary border-surface-border cursor-pointer'}" title="다음">&rsaquo;</button>`;

      // Last Page >>
      const lastDisabled = currentPage === totalPages;
      html += `<button onclick="${lastDisabled ? '' : onPageChange + '(' + totalPages + ')'}" class="px-2.5 py-1.5 rounded-lg border font-bold transition shadow-xs ${lastDisabled ? 'opacity-30 cursor-not-allowed bg-surface-subtle text-ink-muted border-surface-border' : 'bg-white hover:bg-surface-subtle text-ink-primary border-surface-border cursor-pointer'}" title="끝으로">&raquo;&raquo;</button>`;

      html += '</div>';
      container.innerHTML = html;
    }

    function changePortfolioPage(page, pushHistory = true) {
      currentPortfolioPage = page;
      renderCards();
      document.getElementById('portfolioView')?.scrollIntoView({ behavior: 'smooth' });
      if (pushHistory) {
        const targetHash = page > 1 ? '#/factchecks?page=' + page : '#/factchecks';
        if (window.location.hash !== targetHash) {
          try { history.pushState({ view: 'portfolio', page: page }, '', targetHash); } catch(e) { window.location.hash = targetHash; }
        }
      }
    }

    function changeModelsPage(page, pushHistory = true) {
      currentModelsPage = page;
      renderModels();
      document.getElementById('modelsView')?.scrollIntoView({ behavior: 'smooth' });
      if (pushHistory) {
        const targetHash = page > 1 ? '#/models?page=' + page : '#/models';
        if (window.location.hash !== targetHash) {
          try { history.pushState({ view: 'models', page: page }, '', targetHash); } catch(e) { window.location.hash = targetHash; }
        }
      }
    }

    function changeNewsPage(page, pushHistory = true) {
      currentNewsPage = page;
      renderNews();
      document.getElementById('newsView')?.scrollIntoView({ behavior: 'smooth' });
      if (pushHistory) {
        const targetHash = page > 1 ? '#/news?page=' + page : '#/news';
        if (window.location.hash !== targetHash) {
          try { history.pushState({ view: 'news', page: page }, '', targetHash); } catch(e) { window.location.hash = targetHash; }
        }
      }
    }

    function changeInboxPage(page, pushHistory = true) {
      currentInboxPage = page;
      renderInbox();
      document.getElementById('inboxView')?.scrollIntoView({ behavior: 'smooth' });
      if (pushHistory) {
        const targetHash = page > 1 ? '#/inbox?page=' + page : '#/inbox';
        if (window.location.hash !== targetHash) {
          try { history.pushState({ view: 'inbox', page: page }, '', targetHash); } catch(e) { window.location.hash = targetHash; }
        }
      }
    }
    let linkSelection = null;
    let nodeSelection = null;

    const queuedItemIds = new Set(JSON.parse(localStorage.getItem('queued_factchecks') || '[]'));

    // Complete Tri-Lingual i18n Dictionary (KO / ZH / EN)
    const i18n = {
      KO: {
        brandTitle: "FactCheck Hub",
        brandSubtitle: "AI 팩트체크 & 글로벌 테크 최신 동향",
        navHome: "대시보드",
        navPortfolio: "공식 검증",
        navModels: "AI 모델 트렌드",
        navNews: "테크 & AI 동향",
        navGraph: "인용 계보망",
        navInbox: "수집 인박스",
        adminArchiveBtn: "아카이브 (Admin)",
        statArchiveLabel: "원천 아카이브 (Admin)",
      pipelineScheduleDesc: "1일 4회(00:17, 06:17, 12:17, 18:17 KST) 전략 수집",
      pipelineWidgetTitle: "자율 크론 파이프라인 텔레메트리 & 차기 수집 카운트다운",
      pipelineNextTargetLabel: "다음 자동 수집 예정",
      pipelineFooterAudit: "23:30 KST 야간 EOD 전수 배치 감사 자동 연동",
      pipelineFooterNote: "* GitHub Actions 큐 상태에 따라 ±2~5분의 스케줄 지연이 발생할 수 있습니다.",
        heroBadge: "ZERO-HALLUCINATION ARCHITECTURE & COST AUDIT",
        heroMainTitle: "바이럴된 AI 기술의 실체 분석",
        heroMainDesc: "SNS 바이럴 마케팅의 환각을 걷어내고, 1차 공식 출처 감사와 기저 표준 vs 서드파티 실측 벤치마크를 통해 도출한 100% 실증 보고서입니다.",
        heroUpdateLabel: "최종 검증일",
        heroAuditCount: "49개 기술 검증 완료",
        promoBannerTitle: "기술 검증 포트폴리오 최신 상태 알림",
        promoCountBadge: "49건 검증 완료",
        promoBannerDesc: "바이럴 임계치를 초과하여 유입된 주요 오픈소스 및 모델 후보군 총 49건에 대한 심층 실측 벤치마크와 팩트체크가 모두 완료되었습니다.",
        promoBtnText: "수집 인박스 후보군 보기",
        timelineTitle: "당일 24시간 수집 타임라인",
        timelineSub: "1일 4회(00, 06, 12, 18시 KST) 6시간 주기 전략 수집 + 23:30 EOD 전수 감사",
        timelineBadge: "1일 4회 6h 펄스",
        timelineLegend: "세션별 수집 건수",
        timelineFooterPrefix: "⚡ 당일 총 수집량:",
        trendRadarTitle: "1일 4회 AI 트렌드 레이더",
        trendRadarSub: "글로벌 오픈소스 & AI 신규 가중치 6시간 주기 자동 감지",
        homeTopPicksTitle: "최신 심층 기술 검증 하이라이트",
        homeTopPicksViewAll: "전체 49개 검증 도시에 보러가기",
        btnAll: "전체 검증",
        btnUser: "직접 큐레이션",
        btnAuto: "자동 트렌드",
        sortLabel: "정렬:",
        sortOptions: [
          { val: "date-audit-desc", text: "🔬 분석일자 최신순 (기본)" },
          { val: "date-audit-asc", text: "🔬 분석일자 오래된순" },
          { val: "date-source-desc", text: "📅 원출처 발행 최신순" },
          { val: "date-source-asc", text: "📅 원출처 발행 오래된순" }
        ],
        searchPlaceholder: "기술명, 아키텍처, 큐레이션 동기 검색...",
        domainLabel: "도메인:",
        tagAll: "전체",
        tagFrontend: "프론트엔드",
        tagAgent: "AI 에이전트",
        tagScraping: "웹 스크래핑",
        tagDoc: "문서 파싱",
        tag3d: "3D/컴포넌트",
        tagRust: "Rust/시스템",
        tagOther: "기타/코어 인프라",
        cardMotivationLabel: "💡 발굴 의도 / 문제의식:",
        cardVerdictLabel: "⚡ 검증 팩트 / 결론:",
        cardConfidenceLabel: "신뢰도",
        cardSourcesLabel: "개 1차 출처",
        cardViewBtn: "심층 보고서 열람",
        newsHeaderBadge: "GLOBAL TECH & AI INTELLIGENCE FEED",
        newsHeaderTitle: "커뮤니티, 해커뉴스, 사설에서 수집된 테크 & AI 최신 담론",
        newsHeaderDesc: "소프트웨어·AI 저장소뿐만 아니라 신소재·우주, 거시경제, 인프라 보안 등 글로벌 기술 동향을 선별합니다.",
        newsOriginalLink: "기사 원문",
        newsCatFilterLabel: "🏷️ 기술·글로벌 분류:",
        newsCats: {
          'ALL': "전체",
          'TECH_COMPUTING': "💻 IT·컴퓨팅",
          'SCIENCE_RESEARCH': "🚀 과학·우주",
          'ECONOMY_FINANCE': "🏦 경제·금융",
          'LAW_CRIME_JUSTICE': "⚖️ 사회·법률",
          'POLITICS_POLICY': "🏛️ 정치·정책",
          'CULTURE_HUMANITIES': "🌿 문화·인문"
        },
        newsTier2FilterLabel: "↳ 💻 IT 세부 분야:",
        newsT2: {
          'ALL': "전체 IT 분야",
          'INFERENCE_OPT': "⚡ 추론·서빙",
          'AGENTS_DEVTOOLS': "🛠️ 에이전트·도구",
          'MULTIMODAL_AI': "🎨 멀티모달",
          'FOUNDATION_MODELS': "🤖 파운데이션",
          'INFRA_RAG_SECURITY': "🛡️ 인프라·보안",
          'INDUSTRY_TRENDS': "🌐 일반 SW·웹"
        },
        newsSourceLabel: "출처:",
        newsSrcAll: "전체 출처",
        newsSearchPlaceholder: "기술명, 키워드 검색...",
        newsSortLabel: "정렬:",
        newsSortOptions: [
          { val: "date-audit-desc", text: "🔬 AI 분석일 최신순 (기본)" },
          { val: "date-audit-asc", text: "🔬 AI 분석일 오래된순" },
          { val: "date-source-desc", text: "📅 수집/발표 최신순" },
          { val: "date-source-asc", text: "📅 수집/발표 오래된순" }
        ],
        modelsFamilyLabel: "🤖 모델 패밀리:",
        modelFams: {
          'ALL': "전체 패밀리",
          'Qwen': "Qwen",
          'Wan': "Wan 비디오",
          'MiniMax': "MiniMax",
          'FLUX': "FLUX 이미지",
          'GLM': "GLM",
          'DeepSeek': "DeepSeek",
          'Hunyuan': "Hunyuan",
          'Audio': "음성/TTS",
          'Standalone': "독립/신규 모델"
        },
        modelsArtifactLabel: "🧩 허브 유형:",
        modelArts: {
          'ALL': "전체",
          'WEIGHTS': "🤖 가중치·체크포인트",
          'WEB_SERVICE': "🌐 인터랙티브 데모·Spaces",
          'FINETUNE': "🎯 특화 파인튜닝"
        },
        modelsSearchPlaceholder: "모델명, 아키텍처, 포맷 검색...",
        modelsSortLabel: "정렬:",
        modelsSortOptions: [
          { val: "date-source-desc", text: "📅 발행일 최신순 (기본)" },
          { val: "date-source-asc", text: "📅 발행일 오래된순" },
          { val: "date-audit-desc", text: "🔬 분석일 최신순" },
          { val: "title-asc", text: "🔤 모델명 가나다순" }
        ],
        graphHeaderBadge: "MULTI-ENTITY CITATION NETWORK",
        graphHeaderTitle: "인물과 논문 인용 계보를 통한 기술 탄생의 뿌리 지도",
        graphHeaderSub: "기술 • 연구자 • 연구소 • 1차 논문",
        graphBtnAll: "전체 보기",
        graphBtnLang: "언어",
        graphBtnTech: "기술/엔진",
        graphBtnOrg: "연구소",
        graphBtnPerson: "인물",
        graphBtnPaper: "논문",
        criteriaTitle: "자율 크론 4대 자동 승격(Promotion) 기준 가이드",
        criteriaDesc: "수집된 수많은 오픈소스 및 논문 중 아래의 4대 바이럴/기술 임계치를 돌파한 항목은 자동으로 [자동 승격 트렌드 후보]로 격상되어 최우선 기술 검증 대기열에 등록됩니다.",
        critGithub: "최근 14일 이내 생성 & ★ > 500 Stars 돌파",
        critHn: "Top/Best 스토리 중 추천 점수 🔥 > 150 Points",
        critHf: "Trending 점수 상위권 & ❤️ > 100 Likes 모델/데모",
        critArxiv: "MoE, Reasoning, VLM 등 혁신 아키텍처 1차 논문",
        inboxHeaderBadge: "AUTONOMOUS HARVEST INBOX",
        inboxHeaderTitle: "원천 데이터 아카이브 & 관리자 파이프라인",
        inboxHeaderDesc: "크롤러가 24시간 실시간 수집한 원천 로우 데이터를 영구 보존하며, 관리자가 심층 팩트체크(공식 검증)로 승격할 후보를 검토하는 내부 저장소입니다.",
        inboxFamilyOn: "패밀리 묶음 (ON)",
        inboxFamilyOff: "패밀리 묶음 (OFF)",
        inboxSearchPlaceholder: "후보 기술 또는 모델명 검색...",
        inboxQueueBtn: "분석 큐 담기",
        inboxQueuedBtn: "대기열 등록됨",
        modalSecCurationTitle: "Discovery Motivation & Target Workflow",
        modalSecViralPostTitle: "1차 마케팅 원문 & 바이럴 클레임 발췌 (Raw Viral Claim)",
        modalSecClaimsTitle: "Marketing Claims vs Empirical Reality",
        modalSecHookTitle: "The Hook & Marketing Hype",
        modalSecHandsOnTitle: "Hands-on Measured Results",
        modalSecAltsTitle: "Comparative Alternatives Matrix",
        modalSecSourcesTitle: "Audited Primary Sources",
        modalWorkflowLabel: "🎯 연계 워크플로우:",
        modalViralLinkText: "원문 포스트 바로가기",
        thTool: "도구 / 기술명",
        thStack: "기술 스택",
        thPros: "장점",
        thCons: "단점",
        thBestFor: "적합한 환경"
      },
      ZH: {
        brandTitle: "FactCheck Hub",
        brandSubtitle: "AI 事实核查与全球科技前沿动态",
        navHome: "仪表盘",
        navPortfolio: "官方核查",
        navModels: "AI 模型趋势",
        navNews: "科技与AI动态",
        navGraph: "引用系谱图",
        navInbox: "采集收件箱",
        adminArchiveBtn: "归档 (Admin)",
        statArchiveLabel: "原始归档 (Admin)",
      pipelineScheduleDesc: "每日 4 次（00:17、06:17、12:17、18:17 KST）周期策略采集",
      pipelineWidgetTitle: "自主定时流水线遥测与下次采集倒计时",
      pipelineNextTargetLabel: "下次自动采集计划",
      pipelineFooterAudit: "23:30 KST 夜间 EOD 全量批处理审计自动联动",
      pipelineFooterNote: "* 受 GitHub Actions 队列负载影响，可能存在 ±2~5 分钟调度延迟.",
        heroBadge: "ZERO-HALLUCINATION ARCHITECTURE & COST AUDIT",
        heroMainTitle: "热门 AI 技术的工程真相与实体验证",
        heroMainDesc: "摒弃社交媒体营销炒作与幻觉，基于第一手官方源码审计以及基础标准 vs 第三方工具的实测基准，输出 100% 真实客观的工程报告。",
        heroUpdateLabel: "最新审计",
        heroAuditCount: "已完成 49 项技术审计",
        promoBannerTitle: "技术审计档案库最新状态",
        promoCountBadge: "49 项核验完毕",
        promoBannerDesc: "已对突破热度阈值自动晋升的 49 项重点开源项目与前沿模型完成全流程深度实测基准与事实核查。",
        promoBtnText: "查看采集收件箱候选",
        timelineTitle: "当日 24 小时采集时间线",
        timelineSub: "每日 4 次 (00, 06, 12, 18时 KST) 6小时周期定向采集 + 23:30 EOD 全量审计",
        timelineBadge: "每日4次 6h脉冲",
        timelineLegend: "各时段采集数",
        timelineFooterPrefix: "⚡ 当日总采集量:",
        trendRadarTitle: "每日 4 次 AI 趋势雷达",
        trendRadarSub: "全球开源与 AI 前沿权重 6 小时周期自动感应",
        homeTopPicksTitle: "最新深度技术核查精选",
        homeTopPicksViewAll: "查看全部 49 份核查档案",
        btnAll: "全部审计",
        btnUser: "人工精选",
        btnAuto: "自动趋势",
        sortLabel: "排序:",
        sortOptions: [
          { val: "date-audit-desc", text: "🔬 审核日期最新 (默认)" },
          { val: "date-audit-asc", text: "🔬 审核日期最早" },
          { val: "date-source-desc", text: "📅 原文发布最新" },
          { val: "date-source-asc", text: "📅 原文发布最早" }
        ],
        searchPlaceholder: "搜索技术名、架构或策展动机...",
        domainLabel: "领域:",
        tagAll: "全部",
        tagFrontend: "前端/UI",
        tagAgent: "AI Agent",
        tagScraping: "网页爬虫",
        tagDoc: "文档解析",
        tag3d: "3D/组件",
        tagRust: "Rust系统",
        tagOther: "核心基建",
        cardMotivationLabel: "💡 挖掘动机 / 痛点问题:",
        cardVerdictLabel: "⚡ 审计结论 / 事实核验:",
        cardConfidenceLabel: "可信度",
        cardSourcesLabel: "个一手来源",
        cardViewBtn: "查阅完整报告",
        newsHeaderBadge: "GLOBAL TECH & AI INTELLIGENCE FEED",
        newsHeaderTitle: "源自社区、HackerNews 与专栏的全球科技与 AI 讨论",
        newsHeaderDesc: "不仅追踪开源代码与模型，还精选深科技、航空航天、宏观经济与基础设施安全动态。",
        newsOriginalLink: "阅读原文",
        newsCatFilterLabel: "🏷️ 技术与全球领域:",
        newsCats: {
          'ALL': "全部",
          'TECH_COMPUTING': "💻 IT与计算",
          'SCIENCE_RESEARCH': "🚀 科学与航天",
          'ECONOMY_FINANCE': "🏦 经济与金融",
          'LAW_CRIME_JUSTICE': "⚖️ 社会与法治",
          'POLITICS_POLICY': "🏛️ 政治与政策",
          'CULTURE_HUMANITIES': "🌿 文化与人文"
        },
        newsTier2FilterLabel: "↳ 💻 IT 细分领域:",
        newsT2: {
          'ALL': "全部 IT 领域",
          'INFERENCE_OPT': "⚡ 推理与服务",
          'AGENTS_DEVTOOLS': "🛠️ 智能体与工具",
          'MULTIMODAL_AI': "🎨 多模态",
          'FOUNDATION_MODELS': "🤖 基础模型",
          'INFRA_RAG_SECURITY': "🛡️ 基础架构与安全",
          'INDUSTRY_TRENDS': "🌐 软件与行业动态"
        },
        newsSourceLabel: "来源:",
        newsSrcAll: "全部来源",
        newsSearchPlaceholder: "搜索技术名、关键词...",
        newsSortLabel: "排序:",
        newsSortOptions: [
          { val: "date-audit-desc", text: "🔬 AI 审核时间最新 (默认)" },
          { val: "date-audit-asc", text: "🔬 AI 审核时间最早" },
          { val: "date-source-desc", text: "📅 采集发布时间最新" },
          { val: "date-source-asc", text: "📅 采集发布时间最早" }
        ],
        modelsFamilyLabel: "🤖 模型系列:",
        modelFams: {
          'ALL': "全部系列",
          'Qwen': "Qwen",
          'Wan': "Wan 视频",
          'MiniMax': "MiniMax",
          'FLUX': "FLUX 图像",
          'GLM': "GLM",
          'DeepSeek': "DeepSeek",
          'Hunyuan': "Hunyuan",
          'Audio': "语音/TTS",
          'Standalone': "独立/新模型"
        },
        modelsArtifactLabel: "🧩 资源类型:",
        modelArts: {
          'ALL': "全部",
          'WEIGHTS': "🤖 模型权重·检查点",
          'WEB_SERVICE': "🌐 在线演示·Spaces",
          'FINETUNE': "🎯 定制微调"
        },
        modelsSearchPlaceholder: "搜索模型名、架构、格式...",
        modelsSortLabel: "排序:",
        modelsSortOptions: [
          { val: "date-source-desc", text: "📅 发布时间最新 (默认)" },
          { val: "date-source-asc", text: "📅 发布时间最早" },
          { val: "date-audit-desc", text: "🔬 AI 审核最新" },
          { val: "title-asc", text: "🔤 模型名 A-Z" }
        ],
        graphHeaderBadge: "MULTI-ENTITY CITATION NETWORK",
        graphHeaderTitle: "人物与论文引用系谱技术溯源全景图",
        graphHeaderSub: "技术 • 研究员 • 实验室 • 一手论文",
        graphBtnAll: "查看全部",
        graphBtnLang: "编程语言",
        graphBtnTech: "核心技术/引擎",
        graphBtnOrg: "科研机构",
        graphBtnPerson: "代表人物",
        graphBtnPaper: "经典论文",
        criteriaTitle: "全自动巡检 4 大自动晋升 (Promotion) 判定准则",
        criteriaDesc: "在海量采集的开源项目与前沿论文中，突破以下 4 项热度与技术指标的候选项目将自动晋升至优先核查队列。",
        critGithub: "14 天内新建仓库且 ★ > 500 Stars 突破",
        critHn: "Top/Best 讨论中点赞热度 🔥 > 150 Points",
        critHf: "Trending 趋势榜前列且 ❤️ > 100 Likes 模型/Demo",
        critArxiv: "涵盖 MoE、推理强化、VLM 的第一手经典架构论文",
        inboxHeaderBadge: "AUTONOMOUS HARVEST INBOX",
        inboxHeaderTitle: "原始数据归档与管理员流水线",
        inboxHeaderDesc: "全天候实时采集的原始数据永久存储库，供管理员审查并晋升至深度事实核查（官方审计）候选。",
        inboxFamilyOn: "系列聚合 (开)",
        inboxFamilyOff: "系列聚合 (关)",
        inboxSearchPlaceholder: "搜索候选技术或模型名称...",
        inboxQueueBtn: "加入待审队列",
        inboxQueuedBtn: "已在队列中",
        modalSecCurationTitle: "Discovery Motivation & Target Workflow",
        modalSecViralPostTitle: "营销宣传原文摘录与主张证据 (Raw Viral Claim)",
        modalSecClaimsTitle: "Marketing Claims vs Empirical Reality",
        modalSecHookTitle: "The Hook & Marketing Hype",
        modalSecHandsOnTitle: "Hands-on Measured Results",
        modalSecAltsTitle: "Comparative Alternatives Matrix",
        modalSecSourcesTitle: "Audited Primary Sources",
        modalWorkflowLabel: "🎯 协同工作流:",
        modalViralLinkText: "直达原文帖子",
        thTool: "工具 / 技术",
        thStack: "技术栈",
        thPros: "核心优势",
        thCons: "劣势与局限",
        thBestFor: "最适用场景"
      },
      EN: {
        brandTitle: "FactCheck Hub",
        brandSubtitle: "AI Fact-Checking & Global Tech Intelligence",
        navHome: "Dashboard",
        navPortfolio: "Fact-Checks",
        navModels: "AI Model Trends",
        navNews: "Tech & AI Trends",
        navGraph: "Citation Graph",
        navInbox: "Harvest Inbox",
        adminArchiveBtn: "Archive (Admin)",
        statArchiveLabel: "Raw Archive (Admin)",
      pipelineScheduleDesc: "4x Daily (00:17, 06:17, 12:17, 18:17 KST) Strategic Ingestion",
      pipelineWidgetTitle: "Autonomous Cron Pipeline Telemetry & Next Ingestion Countdown",
      pipelineNextTargetLabel: "Next Scheduled Ingestion",
      pipelineFooterAudit: "Auto-linked with 23:30 KST Nightly EOD Batch Audit",
      pipelineFooterNote: "* ±2~5 min schedule variance may occur based on GitHub Actions runner queue load.",
        heroBadge: "ZERO-HALLUCINATION ARCHITECTURE & COST AUDIT",
        heroMainTitle: "Empirical Analysis of Viral AI Technologies",
        heroMainDesc: "A zero-hallucination dossier derived from Tier-1 official source audits and empirical benchmarks comparing base standards with third-party tools.",
        heroUpdateLabel: "LAST AUDITED",
        heroAuditCount: "49 Audits Completed",
        promoBannerTitle: "Dossier Status Update",
        promoCountBadge: "49 Completed",
        promoBannerDesc: "All 49 high-velocity repositories and models that crossed the viral threshold have been rigorously benchmarked and fact-checked.",
        promoBtnText: "Explore Harvest Inbox",
        timelineTitle: "Today 24-Hour Collection Timeline",
        timelineSub: "4x daily (00, 06, 12, 18 KST) 6h strategic collection + 23:30 EOD audit",
        timelineBadge: "4x Daily 6h Pulse",
        timelineLegend: "Items per Session",
        timelineFooterPrefix: "⚡ Today Total Collected:",
        trendRadarTitle: "4x Daily AI Trend Radar",
        trendRadarSub: "Autonomous 6-hour radar for trending open weights & code",
        homeTopPicksTitle: "Latest Deep Technical Verification Highlights",
        homeTopPicksViewAll: "View All 49 Empirical Dossiers",
        btnAll: "All Dossiers",
        btnUser: "User Curated",
        btnAuto: "Auto Trends",
        sortLabel: "Sort:",
        sortOptions: [
          { val: "date-audit-desc", text: "🔬 Audit Date (Newest first)" },
          { val: "date-audit-asc", text: "🔬 Audit Date (Oldest first)" },
          { val: "date-source-desc", text: "📅 Source Published (Newest first)" },
          { val: "date-source-asc", text: "📅 Source Published (Oldest first)" }
        ],
        searchPlaceholder: "Search tech, architecture, or motivation...",
        domainLabel: "Domain:",
        tagAll: "All",
        tagFrontend: "Frontend",
        tagAgent: "AI Agents",
        tagScraping: "Scraping",
        tagDoc: "Docs/OCR",
        tag3d: "3D WebGL",
        tagRust: "Rust/Sys",
        tagOther: "Core Infra",
        cardMotivationLabel: "💡 Intent & Problem:",
        cardVerdictLabel: "⚡ Empirical Truth & Verdict:",
        cardConfidenceLabel: "Confidence",
        cardSourcesLabel: "Sources",
        cardViewBtn: "View Full Dossier",
        newsHeaderBadge: "GLOBAL AI INTELLIGENCE FEED",
        newsHeaderTitle: "AI Trends & Engineering Discourse from HackerNews & Communities",
        newsHeaderDesc: "Curated engineering analyses, security vulnerabilities, and architectural tutorials.",
        newsOriginalLink: "Read Source",
        newsCatFilterLabel: "🏷️ Global Domain:",
        newsCats: {
          'ALL': "All",
          'TECH_COMPUTING': "💻 IT & Computing",
          'SCIENCE_RESEARCH': "🚀 Science & Space",
          'ECONOMY_FINANCE': "🏦 Economy & Finance",
          'LAW_CRIME_JUSTICE': "⚖️ Society & Law",
          'POLITICS_POLICY': "🏛️ Policy & Politics",
          'CULTURE_HUMANITIES': "🌿 Culture & Arts"
        },
        newsTier2FilterLabel: "↳ 💻 IT Sub-tracks:",
        newsT2: {
          'ALL': "All IT Tracks",
          'INFERENCE_OPT': "⚡ Inference & Serving",
          'AGENTS_DEVTOOLS': "🛠️ Agents & DevTools",
          'MULTIMODAL_AI': "🎨 Multimodal AI",
          'FOUNDATION_MODELS': "🤖 Foundation Models",
          'INFRA_RAG_SECURITY': "🛡️ Infra & Security",
          'INDUSTRY_TRENDS': "🌐 General SW & Web"
        },
        newsSourceLabel: "Source:",
        newsSrcAll: "All Sources",
        newsSearchPlaceholder: "Search tech, keywords...",
        newsSortLabel: "Sort:",
        newsSortOptions: [
          { val: "date-audit-desc", text: "🔬 AI Audit Date (Newest first, default)" },
          { val: "date-audit-asc", text: "🔬 AI Audit Date (Oldest first)" },
          { val: "date-source-desc", text: "📅 Source Published (Newest first)" },
          { val: "date-source-asc", text: "📅 Source Published (Oldest first)" }
        ],
        modelsFamilyLabel: "🤖 Model Family:",
        modelFams: {
          'ALL': "All Families",
          'Qwen': "Qwen",
          'Wan': "Wan Video",
          'MiniMax': "MiniMax",
          'FLUX': "FLUX Image",
          'GLM': "GLM",
          'DeepSeek': "DeepSeek",
          'Hunyuan': "Hunyuan",
          'Audio': "Audio/TTS",
          'Standalone': "Standalone Models"
        },
        modelsArtifactLabel: "🧩 Hub Resource:",
        modelArts: {
          'ALL': "All",
          'WEIGHTS': "🤖 Weights & Checkpoints",
          'WEB_SERVICE': "🌐 Interactive Demos / Spaces",
          'FINETUNE': "🎯 Specialized Finetunes"
        },
        modelsSearchPlaceholder: "Search model name, architecture, format...",
        modelsSortLabel: "Sort:",
        modelsSortOptions: [
          { val: "date-source-desc", text: "📅 Source Published (Newest first)" },
          { val: "date-source-asc", text: "📅 Source Published (Oldest first)" },
          { val: "date-audit-desc", text: "🔬 Audit Date (Newest first)" },
          { val: "title-asc", text: "🔤 Model Name (A-Z)" }
        ],
        graphHeaderBadge: "MULTI-ENTITY CITATION NETWORK",
        graphHeaderTitle: "Genealogy Map of AI Innovations via Citations",
        graphHeaderSub: "Tech • Researchers • Labs • Primary Papers",
        graphBtnAll: "Show All",
        graphBtnLang: "Language",
        graphBtnTech: "Tech / Engine",
        graphBtnOrg: "Laboratories",
        graphBtnPerson: "People",
        graphBtnPaper: "Papers",
        criteriaTitle: "Autonomous Cron Promotion Criteria Guide",
        criteriaDesc: "Repositories and papers exceeding these 4 viral thresholds are auto-promoted into the priority technical verification queue.",
        critGithub: "Created in last 14 days & > 500 Stars",
        critHn: "Top/Best stories with Score 🔥 > 150 Points",
        critHf: "Top Trending with ❤️ > 100 Likes",
        critArxiv: "Foundational papers on MoE, Reasoning, VLM",
        inboxHeaderBadge: "AUTONOMOUS HARVEST INBOX",
        inboxHeaderTitle: "Raw Data Archive & Admin Pipeline",
        inboxHeaderDesc: "Permanent raw ingestion repository collected 24/7, enabling administrators to review and promote candidates into deep fact-checks.",
        inboxFamilyOn: "Family Group (ON)",
        inboxFamilyOff: "Family Group (OFF)",
        inboxSearchPlaceholder: "Search candidate tech or model...",
        inboxQueueBtn: "Queue for Audit",
        inboxQueuedBtn: "In Queue",
        modalSecCurationTitle: "Discovery Motivation & Target Workflow",
        modalSecViralPostTitle: "Raw Viral Claim Excerpt & Evidence",
        modalSecClaimsTitle: "Marketing Claims vs Empirical Reality",
        modalSecHookTitle: "The Hook & Marketing Hype",
        modalSecHandsOnTitle: "Hands-on Measured Results",
        modalSecAltsTitle: "Comparative Alternatives Matrix",
        modalSecSourcesTitle: "Audited Primary Sources",
        modalWorkflowLabel: "🎯 Target Workflow:",
        modalViralLinkText: "Go to Viral Post",
        thTool: "Tool / Repository",
        thStack: "Tech Stack",
        thPros: "Empirical Strengths",
        thCons: "Weaknesses & Bottlenecks",
        thBestFor: "Best For"
      }
    };

    // ================= URL ROUTING & BROWSER HISTORY ENGINE =================
    const ROUTES = {
      'home': '#/home',
      'portfolio': '#/factchecks',
      'news': '#/news',
      'models': '#/models',
      'graph': '#/graph',
      'inbox': '#/inbox'
    };

    // ================= GLOBAL SEARCH & FILTER RESET ENGINE =================
    function resetAllFiltersAndSearch() {
      // 1. Reset Portfolio search & filters
      currentPortfolioPage = 1;
      searchQuery = '';
      currentMode = 'ALL';
      currentDomain = 'ALL';
      currentSort = 'date-audit-desc';
      const cInput = document.getElementById('searchInput');
      if (cInput) cInput.value = '';
      const cBtn = document.getElementById('clearSearchBtn');
      if (cBtn) cBtn.classList.add('hidden');
      const sortSel = document.getElementById('sortSelect');
      if (sortSel) sortSel.value = 'date-audit-desc';
      document.querySelectorAll('.tag-pill').forEach(b => {
        if (b.dataset.domain === 'ALL') b.classList.add('active');
        else b.classList.remove('active');
      });
      document.querySelectorAll('.segment-btn').forEach(b => b.classList.remove('active'));
      const modeAll = document.getElementById('modeBtnAll');
      if (modeAll) modeAll.classList.add('active');

      // 2. Reset News search & filters
      currentNewsPage = 1;
      currentNewsSearch = '';
      currentNewsTier1 = 'ALL';
      currentNewsTier2 = 'ALL';
      currentNewsSource = 'ALL';
      currentNewsSort = 'date-audit-desc';
      const nInput = document.getElementById('newsSearchInput');
      if (nInput) nInput.value = '';
      const nSort = document.getElementById('newsSortSelect');
      if (nSort) nSort.value = 'date-audit-desc';
      document.querySelectorAll('.news-cat-pill').forEach(btn => {
        if (btn.getAttribute('data-cat') === 'ALL') {
          btn.className = 'news-cat-pill active px-3 py-1.5 rounded-xl text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap';
        } else {
          btn.className = 'news-cat-pill px-3 py-1.5 rounded-xl text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }
      });
      document.querySelectorAll('.news-t2-pill').forEach(btn => {
        if (btn.getAttribute('data-t2') === 'ALL') {
          btn.className = 'news-t2-pill active px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap';
        } else {
          btn.className = 'news-t2-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }
      });
      const t2Container = document.getElementById('newsTier2Container');
      if (t2Container) t2Container.classList.remove('opacity-40', 'pointer-events-none');
      document.querySelectorAll('.news-src-btn').forEach(btn => {
        if (btn.getAttribute('data-src') === 'ALL') {
          btn.className = 'news-src-btn active px-2.5 py-1 rounded-lg text-xs font-bold bg-ink-primary text-white transition shrink-0 whitespace-nowrap';
        } else {
          btn.className = 'news-src-btn px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:bg-white transition border border-surface-border shrink-0 whitespace-nowrap';
        }
      });

      // 3. Reset Models search & filters
      currentModelsPage = 1;
      modelsSearchQuery = '';
      currentModelsFamily = 'ALL';
      currentModelsModality = 'ALL';
      currentModelsArtifact = 'ALL';
      currentModelsSort = 'date-audit-desc';
      const mInput = document.getElementById('modelsSearchInput');
      if (mInput) mInput.value = '';
      const mSort = document.getElementById('modelsSortSelect');
      if (mSort) mSort.value = 'date-audit-desc';
      document.querySelectorAll('.model-fam-pill').forEach(btn => {
        if (btn.getAttribute('data-fam') === 'ALL') {
          btn.className = 'model-fam-pill active px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap';
        } else {
          btn.className = 'model-fam-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }
      });
      document.querySelectorAll('.model-mod-pill').forEach(btn => {
        if (btn.dataset.mod === 'ALL') {
          btn.className = 'model-mod-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shrink-0 whitespace-nowrap';
        } else {
          btn.className = 'model-mod-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }
      });
      document.querySelectorAll('.model-art-pill').forEach(btn => {
        if (btn.getAttribute('data-art') === 'ALL') {
          btn.className = 'model-art-pill active px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap';
        } else {
          btn.className = 'model-art-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }
      });

      // 4. Reset Inbox search & filters
      currentInboxPage = 1;
      inboxSearchQuery = '';
      currentInboxSource = 'ALL';
      currentInboxLang = 'ALL';
      currentInboxType = 'ALL';
      currentInboxTech = 'ALL';
      currentInboxSort = 'date-audit-desc';
      const iInput = document.getElementById('inboxSearchInput');
      if (iInput) iInput.value = '';
      const iSort = document.getElementById('inboxSortSelect');
      if (iSort) iSort.value = 'date-audit-desc';
      document.querySelectorAll('.inbox-src-pill').forEach(btn => {
        if (btn.getAttribute('data-src-val') === 'ALL') {
          btn.className = 'inbox-src-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shrink-0 whitespace-nowrap';
        } else {
          btn.className = 'inbox-src-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }
      });
      document.querySelectorAll('.inbox-filter-pill').forEach(btn => {
        if (btn.dataset.langVal === 'ALL') {
          btn.className = 'inbox-filter-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shrink-0 whitespace-nowrap';
        } else {
          btn.className = 'inbox-filter-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }
      });
    }

    // ================= VIEW SWITCHER (Clean 6 Core Tabs with History Support) =================
    function switchView(view, pushHistory = true, preserveFilters = false) {
      if (!preserveFilters) {
        resetAllFiltersAndSearch();
      }
      currentView = view;
      const validViews = ['home', 'portfolio', 'news', 'models', 'graph', 'inbox'];
      if (!validViews.includes(view)) view = 'home';

      validViews.forEach(v => {
        const el = document.getElementById(v + 'View');
        const btn = document.getElementById('tab' + v.charAt(0).toUpperCase() + v.slice(1) + 'Btn');
        const mBtn = document.getElementById('mTab' + v.charAt(0).toUpperCase() + v.slice(1) + 'Btn');
        
        if (el) el.classList.toggle('hidden', v !== view);
        
        if (btn) {
          if (v === view) {
            btn.className = 'nav-tab active flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-white bg-ink-primary transition shadow-sm';
          } else {
            btn.className = 'nav-tab flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-ink-secondary hover:text-ink-primary transition';
          }
        }

        if (mBtn) {
          if (v === view) {
            mBtn.className = 'mobile-nav-tab active shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-ink-primary transition shadow-sm';
          } else {
            mBtn.className = 'mobile-nav-tab shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium text-ink-secondary hover:text-ink-primary bg-surface-subtle border border-surface-border transition';
          }
        }
      });

      // Update Admin Archive Button State
      const adminBtn = document.getElementById('adminArchiveBtn');
      if (adminBtn) {
        if (view === 'inbox') {
          adminBtn.className = 'flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-bold text-white bg-slate-800 transition border border-slate-700 shadow-sm';
        } else {
          adminBtn.className = 'flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold text-ink-muted hover:text-ink-primary hover:bg-surface-subtle transition border border-transparent hover:border-surface-border';
        }
      }

      // Synchronize Clean URL and Push to Browser History
      if (pushHistory) {
        const targetHash = ROUTES[view] || '#/' + view;
        if (window.location.hash !== targetHash) {
          try {
            history.pushState({ view: view }, '', targetHash);
          } catch (e) {
            window.location.hash = targetHash;
          }
        }
      }

      // 🌟 Immediate Active View Re-render
      if (view === 'home') {
        renderTelemetryCharts();
      updateCronCountdown();
        renderHomeTopPicks();
      } else if (view === 'portfolio') {
        renderCards();
      } else if (view === 'models') {
        renderModels();
      } else if (view === 'news') {
        renderNews();
      } else if (view === 'inbox') {
        renderInbox();
        updateCronCountdown();
        checkLiveActionsRuns();
      } else if (view === 'graph' && !simulationRef) {
        initCitationGraph();
      }

      window.scrollTo({ top: 0, behavior: 'smooth' });
      lucide.createIcons();
    }

    // ================= RENDER HOME TOP PICKS PREVIEW (최신 분석일 기준 DESC) =================
    function renderHomeTopPicks() {
      const container = document.getElementById('homeTopPicksContainer');
      if (!container) return;
      container.innerHTML = '';
      
      // Sort cases strictly by investigation_date descending (latest first)
      const sortedCases = sortCollection([...(liveCasesData || [])], 'date-audit-desc');
      const top3 = sortedCases.slice(0, 3);

      top3.forEach(c => {
        const card = document.createElement('div');
        card.className = 'p-4 rounded-xl border border-surface-border bg-surface-subtle hover:bg-white hover:border-ink-primary hover:shadow-md transition cursor-pointer flex flex-col justify-between space-y-2.5';
        card.onclick = () => openModal(c);

        const isVerifiedTrue = c.verdict === 'VERIFIED_TRUE';
        const isHalfTrue = (c.verdict || '').includes('HALF');
        const badgeColor = isVerifiedTrue ? 'bg-emerald-50 text-emerald-800 border-emerald-200' : (isHalfTrue ? 'bg-amber-50 text-amber-900 border-amber-200' : 'bg-rose-50 text-rose-800 border-rose-200');
        const badgeLabel = isVerifiedTrue ? (currentLang === 'KO' ? '사실 검증됨' : (currentLang === 'ZH' ? '事实已核验' : 'Verified True')) : (isHalfTrue ? (currentLang === 'KO' ? '절반의 사실' : (currentLang === 'ZH' ? '部分属实' : 'Half True')) : (currentLang === 'KO' ? '과장/왜곡' : (currentLang === 'ZH' ? '夸大/失实' : 'Gamed/Hype')));

        const { displayTitle, displayHook } = getLocalizedContent(c, currentLang);
        const displayDate = c.investigation_date || (c.source_published_date ? c.source_published_date.slice(0, 10) : '2026-09-04');

        card.innerHTML = `
          <div class="space-y-2">
            <div class="flex items-center justify-between text-xs font-mono">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${badgeColor}">${badgeLabel}</span>
              <span class="text-ink-muted text-[11px] font-semibold">${c.confidence_score || 95}%</span>
            </div>
            <h4 class="text-xs sm:text-sm font-bold text-ink-primary line-clamp-2 leading-snug hover:text-indigo-600 transition">${displayTitle}</h4>
            <p class="text-[11px] text-ink-secondary line-clamp-2 leading-relaxed">${displayHook}</p>
          </div>
          <div class="pt-2 border-t border-surface-border flex items-center justify-between text-[10px] font-mono text-ink-muted">
            <span>🔬 ${currentLang === 'KO' ? '분석일: ' : (currentLang === 'ZH' ? '分析日: ' : 'Audited: ')}${displayDate}</span>
            <span class="font-bold text-indigo-700 flex items-center gap-0.5">${currentLang === 'KO' ? '상세 보고서' : (currentLang === 'ZH' ? '查看报告' : 'View Dossier')} <i data-lucide="arrow-right" class="w-3 h-3"></i></span>
          </div>
        `;
        container.appendChild(card);
      });
      if (window.lucide) window.lucide.createIcons({ root: container });
    }

    // ================= LANGUAGE TOGGLE & HIGH-FIDELITY CJK FONT SWITCHING =================
    function setLanguage(lang) {
      currentLang = lang;
      try {
        localStorage.setItem('factcheck_lang', lang);
      } catch (e) {}
      
      // Dynamic Native Font Stack Switching
      if (lang === 'ZH') {
        document.documentElement.lang = 'zh-CN';
        document.body.style.fontFamily = "'Noto Sans SC', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'SimHei', sans-serif";
      } else if (lang === 'EN') {
        document.documentElement.lang = 'en';
        document.body.style.fontFamily = "'Geist', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif";
      } else {
        document.documentElement.lang = 'ko';
        document.body.style.fontFamily = "'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif";
      }

      // Language Switcher Button Highlighting
      ['KO', 'ZH', 'EN'].forEach(l => {
        const btn = document.getElementById('lang' + l.charAt(0) + l.slice(1).toLowerCase() + 'Btn');
        if (btn) {
          btn.className = l === lang 
            ? 'px-2 py-0.5 rounded bg-ink-primary text-white font-bold transition text-[10px] sm:text-[11px] shadow-sm' 
            : 'px-2 py-0.5 rounded text-ink-secondary hover:text-ink-primary transition text-[10px] sm:text-[11px]';
        }
      });
      
      const t = i18n[lang] || i18n['KO'];
      const safeSetText = (id, txt) => {
        const el = document.getElementById(id);
        if (el && txt !== undefined) el.innerText = txt;
      };
      const safeSetHtml = (id, html) => {
        const el = document.getElementById(id);
        if (el && html !== undefined) el.innerHTML = html;
      };
      const safeSetAttr = (id, attr, val) => {
        const el = document.getElementById(id);
        if (el && val !== undefined) el.setAttribute(attr, val);
      };

      // Brand & Navigation
      safeSetText('headerBrandTitle', t.brandTitle);
      safeSetText('headerBrandSubtitle', t.brandSubtitle);
      safeSetText('navTabHome', t.navHome || '대시보드');
      safeSetText('mNavTabHome', t.navHome || '대시보드');
      safeSetText('navTabPortfolio', t.navPortfolio);
      safeSetText('mNavTabPortfolio', t.navPortfolio);
      safeSetText('navTabModels', t.navModels);
      safeSetText('mNavTabModels', t.navModels + ' (' + (typeof liveModelsData !== 'undefined' ? liveModelsData.length : 242) + ')');
      safeSetText('navTabNews', t.navNews);
      safeSetText('mNavTabNews', t.navNews + ' (' + (typeof liveNewsData !== 'undefined' ? liveNewsData.length : 1535) + ')');
      safeSetText('navTabGraph', t.navGraph);
      safeSetText('mNavTabGraph', t.navGraph);
      safeSetText('adminArchiveLabel', t.adminArchiveBtn);
      safeSetText('mNavTabInbox', (t.adminArchiveBtn || '아카이브') + ' (' + (typeof liveInboxData !== 'undefined' ? liveInboxData.length : 1777) + ')');

      // Hero Elements
      safeSetText('heroBadge', t.heroBadge);
      safeSetText('heroMainTitle', t.heroMainTitle);
      safeSetHtml('heroMainDesc', t.heroMainDesc);
      safeSetText('heroAuditCount', t.heroAuditCount);

      // Dashboard KPI Telemetry
      safeSetText('statLabelVerified', lang === 'KO' ? '공식 기술 검증' : (lang === 'ZH' ? '官方技术核查' : 'Verified Fact-Checks'));
      safeSetText('statLabelInbox', lang === 'KO' ? '수집 인박스' : (lang === 'ZH' ? '采集收件箱' : 'Harvested Inbox'));
      safeSetText('statLabelModels', lang === 'KO' ? 'AI 모델 트렌드' : (lang === 'ZH' ? 'AI 模型趋势' : 'AI Model Trends'));
      safeSetText('statLabelNews', lang === 'KO' ? 'AI 테크 동향' : (lang === 'ZH' ? 'AI 科技动态' : 'Tech Intelligence'));
      safeSetText('statLabelArchive', t.statArchiveLabel);
      safeSetText('statDescInbox', lang === 'KO' ? 'HN · GeekNews · GitHub · HF 24/7 수집' : (lang === 'ZH' ? 'HN · GeekNews · GitHub · HF 全天候采集' : 'HN · GeekNews · GitHub · HF 24/7 Ingestion'));
      const safeSetDescModels = lang === 'KO' ? 'MoE, VLM, 추론 특화 오픈 가중치' : (lang === 'ZH' ? 'MoE、VLM与推理优化开源权重' : 'MoE, VLM & Reasoning Open Weights');
      safeSetText('statDescModels', safeSetDescModels);
      const safeSetDescNews = lang === 'KO' ? 'CVE 취약점, 인프라 장애, 아키텍처 토론' : (lang === 'ZH' ? 'CVE 漏洞、基础设施故障与架构实践' : 'CVEs, Infra Outages & Architecture Posts');
      safeSetText('statDescNews', safeSetDescNews);

      const nowKstForTitle = getDynamicKstDate();
      const pad0 = (n) => String(n).padStart(2, '0');
      const curKstDateStrForTitle = `${nowKstForTitle.getFullYear()}-${pad0(nowKstForTitle.getMonth() + 1)}-${pad0(nowKstForTitle.getDate())}`;
      safeSetText('timelineTitleText', (t.timelineTitle || '당일 24시간 수집 타임라인') + ' (' + curKstDateStrForTitle + ')');
      safeSetText('timelineSub', t.timelineSub);
      safeSetText('timelineBadgeText', t.timelineBadge);
      safeSetText('timelineLegendText', t.timelineLegend);
      safeSetHtml('timelineFooterText', t.timelineFooterPrefix + ' <b class="text-indigo-700">0' + (lang === 'KO' ? '건' : (lang === 'ZH' ? '条' : ' items')) + '</b>');
      safeSetText('trendRadarTitleText', t.trendRadarTitle);
      safeSetText('trendRadarSub', t.trendRadarSub);
      safeSetHtml('trendRadarFooter', `<span class="flex items-center gap-1.5"><i data-lucide="zap" class="w-3.5 h-3.5 text-amber-500"></i> ` + (lang === 'KO' ? 'LLM 자동 트렌드 추출 (OpenRouter 0원 라우팅)' : (lang === 'ZH' ? 'LLM 自动化趋势提取 (OpenRouter 0元路由)' : 'Automated LLM Trend Extraction (OpenRouter Free Tier)')) + `</span>`);
      safeSetText('homeTopPicksTitle', t.homeTopPicksTitle);
      safeSetText('homeTopPicksViewAll', t.homeTopPicksViewAll);

      // News View Labels & Pills
      safeSetText('newsHeaderBadge', t.newsHeaderBadge);
      safeSetText('newsHeaderTitle', t.newsHeaderTitle);
      safeSetText('newsHeaderDesc', t.newsHeaderDesc);
      safeSetText('newsCatFilterLabel', t.newsCatFilterLabel);
      safeSetText('newsTier2FilterLabel', t.newsTier2FilterLabel);
      safeSetText('newsSourceLabel', t.newsSourceLabel);
      safeSetText('newsSrcBtnAll', t.newsSrcAll);
      safeSetAttr('newsSearchInput', 'placeholder', t.newsSearchPlaceholder);
      safeSetText('newsSortLabel', t.newsSortLabel);

      if (typeof updateNewsCategoryPillCounts === 'function') {
        updateNewsCategoryPillCounts();
      }

      const newsSortSel = document.getElementById('newsSortSelect');
      if (newsSortSel && t.newsSortOptions) {
        const cur = newsSortSel.value;
        newsSortSel.innerHTML = t.newsSortOptions.map(opt => `<option value="${opt.val}" ${opt.val === cur ? 'selected' : ''}>${opt.text}</option>`).join('');
      }

      // Models View Labels & Pills
      safeSetText('modelsFamilyLabel', t.modelsFamilyLabel);
      safeSetText('modelsArtifactLabel', t.modelsArtifactLabel);
      safeSetAttr('modelsSearchInput', 'placeholder', t.modelsSearchPlaceholder);
      safeSetText('modelsSortLabel', t.modelsSortLabel);

      if (typeof updateModelCategoryPillCounts === 'function') {
        updateModelCategoryPillCounts();
      } else {
        document.querySelectorAll('.model-fam-pill').forEach(pill => {
          const fam = pill.dataset.fam;
          if (t.modelFams && t.modelFams[fam]) pill.innerText = t.modelFams[fam];
        });
        document.querySelectorAll('.model-art-pill').forEach(pill => {
          const art = pill.dataset.art;
          if (t.modelArts && t.modelArts[art]) pill.innerText = t.modelArts[art];
        });
      }

      const modelsSortSel = document.getElementById('modelsSortSelect');
      if (modelsSortSel && t.modelsSortOptions) {
        const cur = modelsSortSel.value;
        modelsSortSel.innerHTML = t.modelsSortOptions.map(opt => `<option value="${opt.val}" ${opt.val === cur ? 'selected' : ''}>${opt.text}</option>`).join('');
      }

      // Graph View
      safeSetText('graphHeaderBadge', t.graphHeaderBadge);
      safeSetText('graphHeaderTitle', t.graphHeaderTitle);
      safeSetText('graphHeaderSub', t.graphHeaderSub);
      safeSetText('graphBtnAll', t.graphBtnAll);
      safeSetText('graphBtnLang', t.graphBtnLang);
      safeSetText('graphBtnTech', t.graphBtnTech);
      safeSetText('graphBtnOrg', t.graphBtnOrg);
      safeSetText('graphBtnPerson', t.graphBtnPerson);
      safeSetText('graphBtnPaper', t.graphBtnPaper);

      // Archive & Inbox View
      safeSetText('inboxHeaderBadge', t.inboxHeaderBadge);
      safeSetText('inboxHeaderTitle', t.inboxHeaderTitle);
      safeSetText('pipelineScheduleDesc', t.pipelineScheduleDesc);
      safeSetText('pipelineWidgetTitle', t.pipelineWidgetTitle);
      safeSetText('pipelineNextTargetLabel', t.pipelineNextTargetLabel);
      safeSetText('pipelineFooterAudit', t.pipelineFooterAudit);
      safeSetText('pipelineFooterNote', t.pipelineFooterNote);
      if (typeof updateCronCountdown === 'function') updateCronCountdown();
      safeSetText('inboxHeaderDesc', t.inboxHeaderDesc);
      safeSetText('inboxHeaderCount', lang === 'KO' ? ('총 ' + (typeof liveInboxData !== 'undefined' ? liveInboxData.length : '') + '건') : (lang === 'ZH' ? ('共 ' + (typeof liveInboxData !== 'undefined' ? liveInboxData.length : '') + ' 项') : ('Total: ' + (typeof liveInboxData !== 'undefined' ? liveInboxData.length : '') + ' items')));
      safeSetText('criteriaTitle', t.criteriaTitle);
      safeSetText('criteriaDesc', t.criteriaDesc);
      safeSetText('critGithub', t.critGithub);
      safeSetText('critHn', t.critHn);
      safeSetText('critHf', t.critHf);
      safeSetText('critArxiv', t.critArxiv);
      safeSetAttr('inboxSearchInput', 'placeholder', t.inboxSearchPlaceholder);

      // Portfolio Controls
      safeSetText('btnLabelAll', t.btnAll);
      safeSetText('btnLabelUser', t.btnUser);
      safeSetText('btnLabelAuto', t.btnAuto);
      safeSetText('sortLabel', t.sortLabel);
      safeSetAttr('searchInput', 'placeholder', t.searchPlaceholder);
      safeSetText('domainFilterLabel', t.domainLabel);
      safeSetText('tagAll', t.tagAll);
      safeSetText('tagFrontend', t.tagFrontend);
      safeSetText('tagAgent', t.tagAgent);
      safeSetText('tagScraping', t.tagScraping);
      safeSetText('tagDoc', t.tagDoc);
      safeSetText('tag3d', t.tag3d);
      safeSetText('tagRust', t.tagRust);
      safeSetText('tagOther', t.tagOther);

      const sortSel = document.getElementById('sortSelect');
      if (sortSel && t.sortOptions) {
        const curVal = sortSel.value;
        sortSel.innerHTML = t.sortOptions.map(opt => `<option value="${opt.val}" ${opt.val === curVal ? 'selected' : ''}>${opt.text}</option>`).join('');
      }

      // 🌟 Instant Full Re-render on Active Views
      try { renderCards(); } catch (e) {}
      try { renderHomeTopPicks(); } catch (e) {}
      try { renderRadarSession(); } catch (e) {}
      try { renderTelemetryCharts(); } catch (e) {}
      try { updateCronCountdown(); } catch (e) {}
      try { renderModels(); } catch (e) {}
      try { renderNews(); } catch (e) {}
      try { renderInbox(); } catch (e) {}
      if (window.lucide && typeof window.lucide.createIcons === 'function') {
        try { window.lucide.createIcons(); } catch (e) {}
      }
    }

    // Expose setLanguage globally for inline HTML onclick handlers
    window.setLanguage = setLanguage;

    // ================= REAL-TIME DB SYNC (VERCEL LIVE API + STATIC FALLBACK) =================
    let _isSyncing = false;
    let _syncTimeoutId = null;
    async function syncFromNeonLiveDB(force = false) {
      if (_isSyncing && !force) return;
      _isSyncing = true;
      if (_syncTimeoutId) clearTimeout(_syncTimeoutId);
      _syncTimeoutId = setTimeout(() => { _isSyncing = false; }, 8000);
      const badge = document.getElementById('dbLiveBadge');
      try {
        const tStart = performance.now();
        const apiUrl = window.location.hostname.includes('vercel.app') ? '/api/stats' : 'https://ai-factcheck-portfolio.vercel.app/api/stats';
        const res = await fetch(apiUrl, { cache: 'no-store' });
        const tLatency = Math.round(performance.now() - tStart);


        if (res.ok) {
          const data = await res.json();
          if (data.status === 'success' && data.counts) {
            const liveInbox = data.counts.inbox_deduped || data.counts.inbox_total;
            const liveModels = data.counts.models_total;
            const liveNews = data.counts.news_total;

            const hInbox = document.getElementById('headerInboxCount');
            if (hInbox && liveInbox) hInbox.textContent = `(${liveInbox})`;

            const statInbox = document.getElementById('statValInbox');
            if (statInbox && liveInbox) statInbox.textContent = liveInbox;

            const mNavInbox = document.getElementById('mNavTabInbox');
            if (mNavInbox && liveInbox) mNavInbox.textContent = `아카이브 (${liveInbox})`;

            const inbHdr = document.getElementById('inboxHeaderCount');
            if (inbHdr && liveInbox) inbHdr.textContent = `총 ${liveInbox}건`;

            if (data.counts.inbox_unclassified !== undefined) {
              const unclass = data.counts.inbox_unclassified;
              const btn = document.getElementById('btnTriggerWorker');
              const txt = document.getElementById('btnWorkerText');

              if (unclass === 0) {
                if (txt) txt.textContent = '✨ 모든 항목 AI 요약 완료됨';
                if (btn) {
                  btn.disabled = true;
                  btn.className = "px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-800 font-bold font-mono text-[11px] border border-emerald-200 transition shadow-xs flex items-center gap-1.5 cursor-default";
                }
              } else {
                if (!window._autoWorkerPaused && !window._autoWorkerRunning) {
                  startContinuousAiWorker();
                } else if (window._autoWorkerRunning && !window._autoWorkerPaused) {
                  if (txt) txt.innerHTML = `<span class="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse mr-1"></span> AI 요약 중 (잔여: ${unclass}건)`;
                }
              }
            }

            if (badge) {
              badge.innerHTML = `
                <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 shadow-xs cursor-pointer" title="Vercel Edge & Neon DB 실시간 연결됨 (총 ${data.counts.inbox_total}건, 레이턴시: ${tLatency}ms)">
                  <span class="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse"></span> Vercel Live API (${liveInbox})
                </span>
              `;
            }

            // Vercel Serverless & Edge Telemetry Real-time Hydration
            const pingVal = document.getElementById('vercelPingValue');
            const pingLat = document.getElementById('vercelLatencyText');
            if (pingVal && pingLat) {
              pingVal.innerHTML = `<span class="text-emerald-400">200 OK</span>`;
              pingLat.textContent = `(실측 레이턴시: ${tLatency}ms)`;
            }

            if (data.vercel_telemetry) {
              const vt = data.vercel_telemetry;
              const invUsed = document.getElementById('vercelInvocationsUsed');
              const invBar = document.getElementById('vercelInvocationsBar');
              const invRem = document.getElementById('vercelInvocationsRem');
              const invBadge = document.getElementById('vercelInvocationsBadge');
              if (invUsed && vt.invocations) invUsed.textContent = vt.invocations.used_estimated.toLocaleString();
              if (invBar && vt.invocations) invBar.style.width = `${vt.invocations.used_pct}%`;
              if (invRem && vt.invocations) invRem.textContent = `${vt.invocations.remaining.toLocaleString()}회 (${(100 - vt.invocations.used_pct).toFixed(1)}%)`;
              if (invBadge && vt.invocations) invBadge.textContent = `안전 (${vt.invocations.used_pct}%)`;

              const cpuUsed = document.getElementById('vercelCpuUsed');
              const cpuBar = document.getElementById('vercelCpuBar');
              if (cpuUsed && vt.active_cpu_time) cpuUsed.textContent = `${vt.active_cpu_time.used_hours}h`;
              if (cpuBar && vt.active_cpu_time) cpuBar.style.width = `${vt.active_cpu_time.used_pct}%`;

              const bwUsed = document.getElementById('vercelBandwidthUsed');
              const bwBar = document.getElementById('vercelBandwidthBar');
              if (bwUsed && vt.bandwidth_gb) bwUsed.textContent = `${vt.bandwidth_gb.used_estimated} GB`;
              if (bwBar && vt.bandwidth_gb) bwBar.style.width = `${vt.bandwidth_gb.used_pct}%`;
            }

            // 🌟 Real-time dynamic card hydration: Fetch latest DB records and update/unshift
            try {
              const isLocalOrVercel = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' || window.location.hostname.includes('vercel.app');
              const inboxApiUrl = isLocalOrVercel ? '/api/inbox?limit=50&sort=updated' : 'https://ai-factcheck-portfolio.vercel.app/api/inbox?limit=50&sort=updated';
              const inbRes = await fetch(inboxApiUrl, { cache: 'no-store' });
              if (inbRes.ok) {
                const inbData = await inbRes.json();
                if (inbData.status === 'success' && Array.isArray(inbData.items)) {
                  const mapExisting = new Map(liveInboxData.map(x => [x.inbox_id || x.id, x]));
                  let addedCount = 0;
                  let updatedCount = 0;
                  for (let i = 0; i < inbData.items.length; i++) {
                    const newItem = inbData.items[i];
                    const nid = newItem.inbox_id || newItem.id;
                    if (!nid) continue;
                    const isModel = newItem.item_type === 'MODEL' || (newItem.source_platform && (newItem.source_platform.includes('Models') || newItem.source_platform.includes('Hub') || newItem.source_platform.includes('Spaces')));
                    if (mapExisting.has(nid)) {
                      const oldItem = mapExisting.get(nid);
                      if (!oldItem.is_classified && newItem.is_classified) {
                        Object.assign(oldItem, newItem);
                        updatedCount++;
                        if (isModel) {
                          const existM = liveModelsData.find(x => (x.inbox_id || x.id) === nid);
                          if (existM) Object.assign(existM, newItem);
                          else liveModelsData.unshift(newItem);
                        } else {
                          const existN = liveNewsData.find(x => (x.inbox_id || x.id) === nid);
                          if (existN) Object.assign(existN, newItem);
                          else liveNewsData.unshift(newItem);
                        }
                      }
                    } else {
                      liveInboxData.push(newItem);
                      mapExisting.set(nid, newItem);
                      addedCount++;
                    }
                  }
                  if (addedCount > 0 || updatedCount > 0) {
                    updateGlobalStatsUI();
                    requestAnimationFrame(() => {
                      if (currentView === 'inbox') renderInbox();
                      else if (currentView === 'news') renderNews();
                      else if (currentView === 'models') renderModels();
                    });
                  }
                }
              }
            } catch (inbErr) {
              console.warn('[Live DB Sync] Inbox items hydration error:', inbErr);
            }

            if (data.timeline_24h_live && Array.isArray(data.timeline_24h_live) && data.timeline_24h_live.length > 0) {
              const curKstH = getDynamicKstHour();
              timeline24hData = data.timeline_24h_live.map(liveSlot => ({
                ...liveSlot,
                is_current: (liveSlot.hour <= curKstH && curKstH < liveSlot.hour + 6),
                is_future: (liveSlot.hour > curKstH)
              }));
              if (typeof renderTelemetryCharts === 'function') {
                renderTelemetryCharts();
              }
            }

            if (data.vercel_worker_runs && Array.isArray(data.vercel_worker_runs)) {
              window.vercelWorkerRunsData = data.vercel_worker_runs;
              if (window.currentRunsTab === 'vercel' && typeof renderRunsTable === 'function') {
                renderRunsTable();
              }
            }

            if (!window._hasInitiallySynced) {
              window._hasInitiallySynced = true;
              console.log('[Live DB Sync] Vercel Serverless API connected successfully:', `${tLatency}ms`);
            }
            return;
          }
        }
      } catch (err) {
        // Graceful fallback for static GitHub Pages or offline
      } finally {
        _isSyncing = false;
        if (_syncTimeoutId) clearTimeout(_syncTimeoutId);
      }

      if (badge) {
        badge.innerHTML = `
          <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 shadow-xs">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse"></span> Neon DB Direct (${casesData.length})
          </span>
        `;
      }
    }
 
    let _autoWorkerRunning = false;
    let _autoWorkerPaused = false;
    window._autoWorkerRunning = false;
    window._autoWorkerPaused = false;

    async function startContinuousAiWorker() {
      if (_autoWorkerRunning) return;
      _autoWorkerRunning = true;
      _autoWorkerPaused = false;
      window._autoWorkerRunning = true;
      window._autoWorkerPaused = false;

      const btn = document.getElementById('btnTriggerWorker');
      const txt = document.getElementById('btnWorkerText');

      if (btn) {
        btn.disabled = false;
        btn.className = "px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-bold font-mono text-[11px] border border-indigo-700 transition shadow-xs flex items-center gap-1.5 cursor-pointer";
      }

      console.log('[AutoWorker] Continuous client-side AI worker started.');

      let consecutiveErrors = 0;

      while (_autoWorkerRunning && !_autoWorkerPaused) {
        try {
          const isLocalOrVercel = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' || window.location.hostname.includes('vercel.app');
          const workerUrl = isLocalOrVercel ? '/api/enrich-worker?limit=1' : 'https://ai-factcheck-portfolio.vercel.app/api/enrich-worker?limit=1';
          
          if (txt && !_autoWorkerPaused) {
            txt.innerHTML = `<span class="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-ping mr-1"></span> AI 요약 분석 중...`;
          }

          const res = await fetch(workerUrl, { cache: 'no-store' });
          if (!res.ok) {
            consecutiveErrors++;
            console.warn(`[AutoWorker] Worker request returned HTTP ${res.status}. Backing off...`);
            if (txt && !_autoWorkerPaused) {
              txt.textContent = `⚡ 쿨다운 대기 중 (${consecutiveErrors}회 재시도)`;
            }
            const backoffMs = Math.min(30000, 5000 * consecutiveErrors);
            await new Promise(r => setTimeout(r, backoffMs));
            continue;
          }

          consecutiveErrors = 0;
          const resData = await res.json();

          if (resData.status === 'noop' || resData.remaining_unclassified === 0) {
            console.log('[AutoWorker] All items are classified! 100% complete.');
            _autoWorkerRunning = false;
            window._autoWorkerRunning = false;
            if (txt) txt.textContent = '✨ 모든 항목 AI 요약 완료됨 (100%)';
            if (btn) {
              btn.disabled = true;
              btn.className = "px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-800 font-bold font-mono text-[11px] border border-emerald-200 transition shadow-xs flex items-center gap-1.5 cursor-default";
            }
            await syncFromNeonLiveDB(true);
            break;
          }

          if (resData.status === 'quota_exhausted' || resData.is_quota_exhausted) {
            console.warn('[AutoWorker] OpenRouter daily free quota (1,000 requests) exhausted. Halting background worker until 09:00 KST reset.');
            _autoWorkerRunning = false;
            window._autoWorkerRunning = false;
            if (txt) {
              txt.innerHTML = `<span class="inline-block w-2 h-2 rounded-full bg-slate-400 mr-1"></span> AI 1일 쿼터 소진 (내일 09:00 KST 재개)`;
            }
            if (btn) {
              btn.disabled = true;
              btn.className = "px-3 py-1.5 rounded-lg bg-slate-100 text-slate-500 font-bold font-mono text-[11px] border border-slate-200 transition shadow-xs flex items-center gap-1.5 cursor-default";
            }
            break; // Stop loop completely - zero further requests sent!
          }

          if (resData.status === 'partial_fallback') {
            if (txt && !_autoWorkerPaused) {
              txt.innerHTML = `<span class="inline-block w-2 h-2 rounded-full bg-amber-400 mr-1"></span> AI 쿼터/모델 쿨다운 (60초 후 재시도)`;
            }
            console.warn('[AutoWorker] AI models busy or daily quota reached. Pausing for 60s...');
            await new Promise(r => setTimeout(r, 60000));
            continue;
          }

          if (resData.status === 'success') {
            const rem = resData.remaining_unclassified;
            if (txt && !_autoWorkerPaused) {
              txt.innerHTML = `<span class="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse mr-1"></span> 자동 요약 중 (잔여: ${rem}건)`;
            }

            // In-memory card hydration
            if (Array.isArray(resData.items) && resData.items.length > 0) {
              let hydratedAny = false;
              for (const enr of resData.items) {
                const targetInbox = liveInboxData.find(x => (x.inbox_id || x.id) === enr.inbox_id);
                if (targetInbox) {
                  targetInbox.title_ko = enr.title_ko;
                  targetInbox.hook = enr.hook_ko;
                  targetInbox.hook_ko = enr.hook_ko;
                  targetInbox.key_takeaways = enr.key_takeaways;
                  targetInbox.category_primary = enr.category_primary;
                  targetInbox.tier1_category = enr.tier1_category;
                  targetInbox.item_type = enr.item_type;
                  targetInbox.is_classified = true;
                  targetInbox.ai_enrichment = Object.assign(targetInbox.ai_enrichment || {}, {
                    korean_title: enr.title_ko,
                    hook: enr.hook_ko,
                    key_takeaways: enr.key_takeaways,
                    category_primary: enr.category_primary,
                    tier1_category: enr.tier1_category,
                    type_classification: enr.item_type,
                    enriched_by_model: enr.enriched_by_model,
                    enriched_at: new Date().toISOString()
                  });
                  targetInbox.multilingual = {
                    ko: { title: enr.title_ko, hook: enr.hook_ko, key_takeaways: enr.key_takeaways },
                    en: { title: targetInbox.title, hook: enr.hook_ko, key_takeaways: enr.key_takeaways },
                    zh: { title: targetInbox.title, hook: enr.hook_ko, key_takeaways: enr.key_takeaways }
                  };
                  hydratedAny = true;
                }

                const isModel = enr.item_type === 'MODEL' || enr.artifact_type === 'WEIGHTS' || (targetInbox && targetInbox.source_platform && (targetInbox.source_platform.includes('Models') || targetInbox.source_platform.includes('Hub') || targetInbox.source_platform.includes('Spaces')));

                if (isModel) {
                  const targetModel = liveModelsData.find(x => (x.inbox_id || x.id) === enr.inbox_id);
                  if (targetModel) {
                    targetModel.title_ko = enr.title_ko;
                    targetModel.hook = enr.hook_ko;
                    targetModel.hook_ko = enr.hook_ko;
                    targetModel.key_takeaways = enr.key_takeaways;
                    targetModel.category_primary = enr.category_primary;
                    targetModel.tier1_category = enr.tier1_category;
                    targetModel.item_type = 'MODEL';
                    targetModel.is_classified = true;
                    targetModel.ai_enrichment = targetInbox?.ai_enrichment;
                    targetModel.multilingual = targetInbox?.multilingual;
                    hydratedAny = true;
                  } else if (targetInbox) {
                    liveModelsData.unshift(targetInbox);
                    hydratedAny = true;
                  }
                } else {
                  const targetNews = liveNewsData.find(x => (x.inbox_id || x.id) === enr.inbox_id);
                  if (targetNews) {
                    targetNews.title_ko = enr.title_ko;
                    targetNews.hook = enr.hook_ko;
                    targetNews.hook_ko = enr.hook_ko;
                    targetNews.key_takeaways = enr.key_takeaways;
                    targetNews.category_primary = enr.category_primary;
                    targetNews.tier1_category = enr.tier1_category;
                    targetNews.item_type = enr.item_type || 'NEWS';
                    targetNews.is_classified = true;
                    targetNews.ai_enrichment = targetInbox?.ai_enrichment;
                    targetNews.multilingual = targetInbox?.multilingual;
                    hydratedAny = true;
                  } else if (targetInbox) {
                    liveNewsData.unshift(targetInbox);
                    hydratedAny = true;
                  }
                }
              }

              // Prepend to Vercel worker runs log history in real time
              const nowKst = new Date(Date.now() + 9 * 3600 * 1000).toISOString().replace('T', ' ').substring(5, 16);
              if (!Array.isArray(window.vercelWorkerRunsData)) window.vercelWorkerRunsData = [];
              window.vercelWorkerRunsData.unshift({
                id: Date.now(),
                worker_name: 'Vercel Serverless AI Enricher',
                model_used: resData.model_used || 'openrouter-free',
                processed_count: resData.processed_count || 1,
                duration_seconds: resData.duration_seconds || 1.8,
                duration_str: (resData.duration_seconds || 1.8) + '초',
                remaining_count: rem,
                status: 'SUCCESS',
                created_at_kst: nowKst
              });
              if (window.vercelWorkerRunsData.length > 25) window.vercelWorkerRunsData.pop();
              if (typeof renderRunsTable === 'function' && window.currentRunsTab === 'vercel') {
                renderRunsTable();
              }

              // Dynamically increment 24H timeline enriched count for current slot
              const curSlotHour = Math.floor(getDynamicKstHour() / 6) * 6;
              const curTlSlot = (typeof timeline24hData !== 'undefined' ? timeline24hData : []).find(d => d.hour === curSlotHour);
              if (curTlSlot) {
                curTlSlot.enriched_count = (curTlSlot.enriched_count || 0) + (resData.processed_count || 1);
                if (typeof renderTelemetryCharts === 'function') {
                  renderTelemetryCharts();
                }
              }

              // Update Vercel capacity analytics (소모량 분석) in real time
              const invEl = document.getElementById('vercelInvocationsUsed');
              const cpuEl = document.getElementById('vercelCpuUsed');
              if (invEl) {
                const curInv = parseInt(invEl.textContent.replace(/,/g, ''), 10) || 1420;
                invEl.textContent = (curInv + 1).toLocaleString();
              }
              if (cpuEl && resData.duration_seconds) {
                const curHours = parseFloat(cpuEl.textContent.replace('h', '')) || 0.01;
                const newHours = (curHours + (resData.duration_seconds / 3600)).toFixed(3);
                cpuEl.textContent = `${newHours}h`;
              }

              if (hydratedAny) {
                updateGlobalStatsUI();
                requestAnimationFrame(() => {
                  if (currentView === 'inbox') renderInbox();
                  else if (currentView === 'news') renderNews();
                  else if (currentView === 'models') renderModels();
                });
              }
            }

            if (rem === 0) {
              _autoWorkerRunning = false;
              window._autoWorkerRunning = false;
              if (txt) txt.textContent = '✨ 모든 항목 AI 요약 완료됨';
              if (btn) {
                btn.disabled = true;
                btn.className = "px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-800 font-bold font-mono text-[11px] border border-emerald-200 transition shadow-xs flex items-center gap-1.5 cursor-default";
              }
              await syncFromNeonLiveDB(true);
              break;
            }
          }
        } catch (loopErr) {
          console.warn('[AutoWorker Loop Error]:', loopErr);
          consecutiveErrors++;
          await new Promise(r => setTimeout(r, 10000));
        }

        // Gentle pause between single-item summaries (3.5 seconds)
        // Respects OpenRouter RPM limits and keeps CPU idle
        await new Promise(r => setTimeout(r, 3500));
      }

      _autoWorkerRunning = false;
      window._autoWorkerRunning = false;
    }

    function toggleAiEnrichWorker() {
      const btn = document.getElementById('btnTriggerWorker');
      const txt = document.getElementById('btnWorkerText');

      if (_autoWorkerRunning && !_autoWorkerPaused) {
        _autoWorkerPaused = true;
        window._autoWorkerPaused = true;
        if (txt) txt.textContent = '⏸️ AI 요약 일시정지됨 (클릭 시 재개)';
        if (btn) {
          btn.className = "px-3 py-1.5 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-800 font-bold font-mono text-[11px] border border-amber-300 transition shadow-xs flex items-center gap-1.5 cursor-pointer";
        }
      } else {
        _autoWorkerPaused = false;
        window._autoWorkerPaused = false;
        if (txt) txt.textContent = '⏳ AI 요약 시작 중...';
        startContinuousAiWorker();
      }
    }

    async function triggerAiEnrichWorker() {
      toggleAiEnrichWorker();
    }

    function updatePromotionBanner() {}

    // ================= FILTER & SORT HANDLERS =================
    function setModeFilter(mode) {
      currentPortfolioPage = 1;
      currentMode = mode;
      document.querySelectorAll('.segment-btn').forEach(btn => btn.classList.remove('active'));
      if (mode === 'ALL') document.getElementById('modeBtnAll').classList.add('active');
      if (mode === 'USER_CURATED') document.getElementById('modeBtnUser').classList.add('active');
      if (mode === 'AUTO_HARVESTED') document.getElementById('modeBtnAuto').classList.add('active');
      renderCards();
    }

    function setDomainFilter(dom) {
      currentPortfolioPage = 1;
      currentDomain = dom;
      document.querySelectorAll('.tag-pill').forEach(btn => {
        if (btn.dataset.domain === dom) btn.classList.add('active');
        else btn.classList.remove('active');
      });
      renderCards();
    }

    function changeSort(val) {
      currentPortfolioPage = 1;
      currentSort = val;
      renderCards();
    }

    function clearSearch() {
      currentPortfolioPage = 1;
      const input = document.getElementById('searchInput');
      input.value = '';
      searchQuery = '';
      document.getElementById('clearSearchBtn').classList.add('hidden');
      renderCards();
    }

    document.getElementById('searchInput').addEventListener('input', (e) => {
      searchQuery = e.target.value;
      document.getElementById('clearSearchBtn').classList.toggle('hidden', !searchQuery);
      renderCards();
    });

    // 🌟 Precise DateTime Helpers for Sub-Second Sorting & Multi-Platform Timestamps
    function parseItemTimestamp(item, preferField) {
      if (!item) return 0;
      let raw = '';
      if (preferField === 'audit') {
        // AI 분석일(Audit Date) must strictly reflect actual AI enrichment/audit time!
        // An un-analyzed item must NEVER fall back to created_at/harvested_date,
        // otherwise unclassified raw items jump ahead of verified AI-summarized items.
        raw = item.ai_enrichment?.enriched_at || item.enriched_at || item.audited_at || item.investigation_date;
        if (!raw) return 0;
        const ms = new Date(raw).getTime();
        return isNaN(ms) ? 0 : ms;
      } else {
        // For freshest items in inbox/news/models, prioritize the latest active timestamp
        const tHarvest = item.harvested_at ? new Date(item.harvested_at).getTime() : 0;
        const tPublish = item.published_at ? new Date(item.published_at).getTime() : 0;
        const tCreated = item.created_at ? new Date(item.created_at).getTime() : 0;
        const tSourcePub = item.source_published_date ? new Date(item.source_published_date).getTime() : 0;
        const tDate = item.harvested_date ? new Date(item.harvested_date).getTime() : 0;
        const best = Math.max(
          isNaN(tHarvest) ? 0 : tHarvest,
          isNaN(tPublish) ? 0 : tPublish,
          isNaN(tCreated) ? 0 : tCreated,
          isNaN(tSourcePub) ? 0 : tSourcePub,
          isNaN(tDate) ? 0 : tDate
        );
        return best;
      }
    }

    function formatDateTime(raw) {
      if (!raw) return '-';
      const d = new Date(raw);
      if (isNaN(d.getTime())) return String(raw).substring(0, 10);
      const y = d.getFullYear();
      const m = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      const hh = String(d.getHours()).padStart(2, '0');
      const mm = String(d.getMinutes()).padStart(2, '0');
      return `${y}-${m}-${day} ${hh}:${mm}`;
    }

    function formatDateTimeCompact(raw) {
      if (!raw) return '-';
      const s = String(raw).trim();
      if (/^\\d{4}-\\d{2}-\\d{2}$/.test(s)) {
        const parts = s.split('-');
        return `<span class="hidden sm:inline">${parts[0]}-</span>${parts[1]}-${parts[2]}`;
      }
      const d = new Date(raw);
      if (isNaN(d.getTime())) return s.substring(0, 10);
      const y = d.getFullYear();
      const m = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      const hh = String(d.getHours()).padStart(2, '0');
      const mm = String(d.getMinutes()).padStart(2, '0');
      return `<span class="hidden sm:inline">${y}-</span>${m}-${day} ${hh}:${mm}`;
    }

    function formatModelAttribution(modelStr) {
      if (!modelStr) return 'AI 검증';
      let s = String(modelStr).replace(/^models\//, '').replace(/:free$/, '');
      if (s.includes('/')) s = s.split('/').pop();
      return '🤖 ' + s;
    }

    // ================= RENDER 24H TIMELINE & 1-DAY 4-SESSIONS TREND RADAR =================
    function getDynamicKstHour() {
      try {
        return parseInt(new Intl.DateTimeFormat('en-US', { timeZone: 'Asia/Seoul', hour: 'numeric', hour12: false }).format(new Date()), 10);
      } catch (e) {
        const now = new Date();
        return (now.getUTCHours() + 9) % 24;
      }
    }

    function getDynamicKstDate() {
      const now = new Date();
      const utc = now.getTime() + (now.getTimezoneOffset() * 60000);
      return new Date(utc + (3600000 * 9));
    }

    function getDynamicKstSession() {
      const h = getDynamicKstHour();
      if (h < 6) return 1;
      if (h < 12) return 2;
      if (h < 18) return 3;
      return 4;
    }

    let targetSelectedInboxId = '';
    let activeRadarSession = getDynamicKstSession();

    function switchRadarSession(sessionNum) {
      activeRadarSession = sessionNum;
      renderRadarSession();
    }

    function navigateFromRadar(view, searchKey, inboxId) {
      targetSelectedInboxId = inboxId || '';
      switchView(view);
      const cleanQ = (searchKey || '').trim();
      if (view === 'models') {
        currentModelsPage = 1;
        modelsSearchQuery = cleanQ;
        const inp = document.getElementById('modelsSearchInput');
        if (inp) inp.value = cleanQ;
        renderModels();
      } else if (view === 'news') {
        currentNewsPage = 1;
        currentNewsSearch = cleanQ.toLowerCase();
        const inp = document.getElementById('newsSearchInput');
        if (inp) inp.value = cleanQ;
        renderNews();
      }
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function renderRadarSession() {
      if (typeof trendRadarData === 'undefined' || !trendRadarData.sessions) return;
      const sessionData = trendRadarData.sessions[String(activeRadarSession)];
      if (!sessionData) return;

      // 1. Update session tabs button active states and localized labels
      const sLabels = {
        KO: ['1회 00시', '2회 06시', '3회 12시', '4회 18시'],
        ZH: ['1期 00点', '2期 06点', '3期 12点', '4期 18点'],
        EN: ['S1 00:00', 'S2 06:00', 'S3 12:00', 'S4 18:00']
      };
      const curLabels = sLabels[currentLang] || sLabels['KO'];
      for (let i = 1; i <= 4; i++) {
        const btn = document.getElementById('radarBtn' + i);
        if (btn) {
          btn.innerText = curLabels[i - 1];
          if (i === activeRadarSession) {
            btn.className = 'px-2 py-0.5 rounded border border-emerald-600 bg-emerald-600 text-white font-bold shadow-xs transition cursor-pointer';
          } else {
            btn.className = 'px-2 py-0.5 rounded border border-surface-border bg-surface-subtle text-ink-muted hover:text-ink-primary hover:bg-slate-100 transition cursor-pointer font-medium';
          }
        }
      }

      // 2. Update header labels
      const windowLabelEl = document.getElementById('trendRadarWindowLabel');
      const pulseDotEl = document.getElementById('trendRadarPulseDot');

      if (windowLabelEl) {
        const wLabel = (currentLang === 'KO' ? sessionData.window_label_ko : (currentLang === 'ZH' ? sessionData.window_label_zh : sessionData.window_label_en)) || sessionData.window_label;
        windowLabelEl.innerText = wLabel;
      }
      if (pulseDotEl) {
        if (sessionData.is_current) {
          pulseDotEl.className = 'w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse';
        } else if (sessionData.is_future) {
          pulseDotEl.className = 'w-1.5 h-1.5 rounded-full bg-amber-500';
        } else {
          pulseDotEl.className = 'w-1.5 h-1.5 rounded-full bg-slate-400';
        }
      }

      // 3. Render session items (1 clickable element per item, fully localized)
      const bulletsContainer = document.getElementById('trendRadarBullets');
      if (bulletsContainer) {
        bulletsContainer.innerHTML = '';
        const items = sessionData.items || [];

        if (items.length > 0) {
          items.forEach((it, idx) => {
            // Distinct colored badge for each platform family
            let platformBadgeClass = 'bg-surface-subtle text-ink-primary border-surface-border';
            const pf = (it.platform_family || '').toLowerCase();
            if (pf.includes('github')) {
              platformBadgeClass = 'bg-slate-100 text-slate-800 border-slate-300';
            } else if (pf.includes('hugging')) {
              platformBadgeClass = 'bg-purple-50 text-purple-700 border-purple-200';
            } else if (pf.includes('arxiv')) {
              platformBadgeClass = 'bg-rose-50 text-rose-700 border-rose-200';
            } else if (pf.includes('hacker')) {
              platformBadgeClass = 'bg-amber-50 text-amber-800 border-amber-200';
            } else if (pf.includes('geek')) {
              platformBadgeClass = 'bg-blue-50 text-blue-700 border-blue-200';
            }

            const itemTitle = (currentLang === 'KO' ? (it.title_ko || it.title) : (currentLang === 'ZH' ? (it.title_zh || it.title) : (it.title_en || it.title))) || it.title;
            const itemSummary = (currentLang === 'KO' ? (it.summary_ko || it.summary) : (currentLang === 'ZH' ? (it.summary_zh || it.summary) : (it.summary_en || it.summary))) || it.summary;
            const factCheckBtnText = currentLang === 'KO' ? '팩트체크' : (currentLang === 'ZH' ? '事实核查' : 'Fact-Check');
            const viewSourceText = currentLang === 'KO' ? '원문 보러가기' : (currentLang === 'ZH' ? '查看原文' : 'View Source');

            const itemCard = document.createElement('div');
            itemCard.className = 'group p-2.5 rounded-xl bg-surface-subtle border border-surface-border hover:border-emerald-400 hover:bg-white transition flex flex-col gap-1.5';
            itemCard.innerHTML = `
              <!-- Header Strip: Platform Badge, Viral Badge, Session Badge, FactCheck Badge, Direct External Link -->
              <div class="flex items-start justify-between gap-2">
                <div class="flex items-center gap-1.5 flex-wrap">
                  <span class="w-5 h-5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200 flex items-center justify-center font-mono font-bold text-[10px] shrink-0">0${idx + 1}</span>
                  <span class="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold ${platformBadgeClass} border">${it.platform || 'AI Hub'}</span>
                  ${it.viral_metric ? `<span class="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-50 text-rose-700 border border-rose-200 flex items-center gap-1">🔥 ${it.viral_metric}</span>` : ''}
                  ${it.is_this_session ? `<span class="px-1.5 py-0.5 rounded text-[9px] font-mono font-extrabold bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-0.5">⚡ ${currentLang === 'KO' ? '이번 회차 수집' : (currentLang === 'ZH' ? '本场实时' : 'Current Session')}</span>` : `<span class="px-1.5 py-0.5 rounded text-[9px] font-mono font-medium bg-slate-100 text-slate-600 border border-slate-200">${it.session_tag || (currentLang === 'KO' ? '당일 수집' : 'Today')}</span>`}
                </div>
                <div class="flex items-center gap-1.5 shrink-0">
                  ${it.case_id ? `
                    <button onclick="openCaseModal('${it.case_id}')" class="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-300 hover:bg-emerald-200 flex items-center gap-1 transition cursor-pointer">
                      <i data-lucide="shield-check" class="w-3 h-3"></i>
                      ${factCheckBtnText}
                    </button>
                  ` : ''}
                </div>
              </div>

              <!-- Direct Original Source Link: Title + '원문 보러가기' Indicator -->
              <a href="${it.source_url}" target="_blank" rel="noopener noreferrer" class="group/title block">
                <div class="text-xs font-bold text-ink-primary group-hover/title:text-emerald-700 transition flex items-start justify-between gap-2 leading-snug">
                  <span class="line-clamp-1">${itemTitle}</span>
                  <span class="text-[11px] font-mono font-bold text-emerald-700 shrink-0 flex items-center gap-1 opacity-90 group-hover/title:opacity-100 mt-0.5 bg-emerald-50 hover:bg-emerald-100 px-2 py-0.5 rounded border border-emerald-300 transition">
                    <span>${viewSourceText}</span>
                    <i data-lucide="external-link" class="w-3 h-3"></i>
                  </span>
                </div>
                ${itemSummary ? `<p class="text-[11px] text-ink-muted truncate leading-relaxed mt-1">${itemSummary}</p>` : ''}
              </a>

              <!-- Date Strip: 발행일 & 수집일 -->
              <div class="pt-1.5 border-t border-surface-border/60 flex items-center justify-between text-[10px] font-mono text-ink-muted flex-wrap gap-1">
                <span class="flex items-center gap-1">📰 <span class="font-medium">${currentLang === 'KO' ? '발행' : (currentLang === 'ZH' ? '发布' : 'Pub')}:</span> ${formatDateTimeCompact(it.published_at || it.harvested_at)}</span>
                <span class="flex items-center gap-1">📥 <span class="font-medium">${currentLang === 'KO' ? '수집' : (currentLang === 'ZH' ? '采集' : 'Rec')}:</span> ${formatDateTimeCompact(it.harvested_at)}</span>
              </div>
            `;
            bulletsContainer.appendChild(itemCard);
          });
        } else {
          const emptyMsg = currentLang === 'KO' ? '이 회차에 등록된 트렌드 데이터가 없습니다.' : (currentLang === 'ZH' ? '该时段暂无趋势数据。' : 'No trend data for this session.');
          bulletsContainer.innerHTML = `<div class="py-6 text-center text-xs text-ink-muted font-mono">${emptyMsg}</div>`;
        }
      }
      if (window.lucide) window.lucide.createIcons();
    }

    function recomputeTimeline24hFromLiveInbox() {
      const nowKst = getDynamicKstDate();
      const pad = (n) => String(n).padStart(2, '0');
      const curKstDateStr = `${nowKst.getFullYear()}-${pad(nowKst.getMonth() + 1)}-${pad(nowKst.getDate())}`;
      const curHour = getDynamicKstHour();

      const slotDefs = [
        { slot: '1회차 (00시)', short_slot: '00:00', hour: 0, range: '00:00 - 05:59', name: '심야 릴리스' },
        { slot: '2회차 (06시)', short_slot: '06:00', hour: 6, range: '06:00 - 11:59', name: '모닝 브리핑' },
        { slot: '3회차 (12시)', short_slot: '12:00', hour: 12, range: '12:00 - 17:59', name: '정오 레이더' },
        { slot: '4회차 (18시)', short_slot: '18:00', hour: 18, range: '18:00 - 23:59', name: '저녁 라운드업' }
      ];

      const counts = {
        0: { inbox: 0, news: 0, model: 0, enriched: 0 },
        6: { inbox: 0, news: 0, model: 0, enriched: 0 },
        12: { inbox: 0, news: 0, model: 0, enriched: 0 },
        18: { inbox: 0, news: 0, model: 0, enriched: 0 }
      };

      const parseKst = (raw) => {
        if (!raw || typeof raw !== 'string') return null;
        if (raw.includes('T')) {
          const dt = new Date(raw);
          if (!isNaN(dt.getTime())) {
            const utcMs = dt.getTime() + (dt.getTimezoneOffset() * 60000);
            const kstDt = new Date(utcMs + (9 * 3600 * 1000));
            return {
              dateStr: `${kstDt.getFullYear()}-${pad(kstDt.getMonth() + 1)}-${pad(kstDt.getDate())}`,
              hour: kstDt.getHours()
            };
          }
        } else if (/^\d{4}-\d{2}-\d{2}/.test(raw)) {
          return { dateStr: raw.substring(0, 10), hour: 0 };
        }
        return null;
      };

      const inbList = typeof liveInboxData !== 'undefined' ? liveInboxData : [];
      inbList.forEach(it => {
        // 1. Pipeline ingestion time (when item arrived)
        const rawTime = it.harvested_at || it.harvested_date || it.created_at || '';
        const kstHarvest = parseKst(rawTime);
        if (kstHarvest && kstHarvest.dateStr === curKstDateStr) {
          const slotHour = Math.floor(kstHarvest.hour / 6) * 6;
          if (counts[slotHour]) counts[slotHour].inbox++;
        }

        // 2. Exact AI Enrichment time (when AI analysis actually happened)
        const isEnriched = it.is_classified || it.ai_enrichment;
        if (isEnriched) {
          const rawEnrichTime = (it.ai_enrichment && it.ai_enrichment.enriched_at) || it.updated_at || '';
          const kstEnrich = parseKst(rawEnrichTime);
          if (kstEnrich && kstEnrich.dateStr === curKstDateStr) {
            const slotHour = Math.floor(kstEnrich.hour / 6) * 6;
            if (counts[slotHour]) {
              counts[slotHour].enriched++;
              const isModel = it.item_type === 'MODEL' || (it.source_platform && (it.source_platform.includes('Models') || it.source_platform.includes('Hub')));
              if (isModel) counts[slotHour].model++;
              else counts[slotHour].news++;
            }
          }
        }
      });

      const totalToday = Object.values(counts).reduce((acc, cur) => acc + cur.inbox + cur.enriched, 0);
      if (totalToday > 0) {
        timeline24hData = slotDefs.map(s => {
          const existing = (typeof timeline24hData !== 'undefined' ? timeline24hData : []).find(d => d.hour === s.hour);
          const inboxCnt = (existing && existing.inbox_count > counts[s.hour].inbox) ? existing.inbox_count : counts[s.hour].inbox;
          const enrichedCnt = (existing && existing.enriched_count > counts[s.hour].enriched) ? existing.enriched_count : counts[s.hour].enriched;
          return {
            slot: s.slot,
            short_slot: s.short_slot,
            hour: s.hour,
            range: s.range,
            name: s.name,
            inbox_count: inboxCnt,
            enriched_count: enrichedCnt,
            model_count: counts[s.hour].model,
            news_count: counts[s.hour].news,
            is_current: (s.hour <= curHour && curHour < s.hour + 6),
            is_future: (s.hour > curHour)
          };
        });
      }
    }

    function renderTelemetryCharts() {
      const nowKst = getDynamicKstDate();
      const pad = (n) => String(n).padStart(2, '0');
      const curKstDateStr = `${nowKst.getFullYear()}-${pad(nowKst.getMonth() + 1)}-${pad(nowKst.getDate())}`;
      const titleEl = document.getElementById('timelineTitleText');
      if (titleEl) {
        titleEl.innerText = `${i18n[currentLang]?.timelineTitle || '당일 24시간 수집 타임라인'} (${curKstDateStr})`;
      }

      // 1. Render 24-Hour Timeline Chart (4 Strategic Quarterly Sessions: 00, 06, 12, 18시)
      const tlContainer = document.getElementById('timeline24hChartContainer');
      if (tlContainer) {
        tlContainer.innerHTML = '';
        const tData = typeof timeline24hData !== 'undefined' ? timeline24hData : [];
        const maxVal = Math.max(...tData.map(d => Math.max(d.inbox_count || 0, d.enriched_count !== undefined ? d.enriched_count : ((d.news_count || 0) + (d.model_count || 0)))), 10);

        const curKstHour = getDynamicKstHour();
        tData.forEach(d => {
          const enrichedCount = d.enriched_count !== undefined ? d.enriched_count : ((d.news_count || 0) + (d.model_count || 0));
          const hPct = (d.inbox_count > 0) ? Math.max(10, Math.round(((d.inbox_count) / maxVal) * 100)) : 0;
          const hEnrichedPct = (enrichedCount > 0) ? Math.max(10, Math.round((enrichedCount / maxVal) * 100)) : 0;
          const isCurrent = (d.hour <= curKstHour && curKstHour < d.hour + 6);
          const isFuture = (d.hour > curKstHour);

          const col = document.createElement('div');
          col.className = 'flex flex-col items-center justify-end h-full group relative cursor-pointer';
          col.innerHTML = `
            <!-- Tooltip -->
            <div class="opacity-0 group-hover:opacity-100 transition-opacity absolute -top-16 z-20 pointer-events-none bg-ink-primary text-white text-[10px] font-mono py-1.5 px-2.5 rounded-lg shadow-lg whitespace-nowrap">
              <div class="font-bold text-indigo-300">${d.range}</div>
              <div class="text-indigo-200">📥 수집: ${d.inbox_count || 0}건</div>
              <div class="text-emerald-300">✨ AI요약: ${enrichedCount}건</div>
              ${isCurrent ? '<div class="text-emerald-400 font-bold mt-0.5">● 현재 세션 인입 중</div>' : (isFuture ? '<div class="text-slate-400 mt-0.5">예정 세션</div>' : '<div class="text-slate-300 mt-0.5">수집 완료</div>')}
            </div>

            <!-- Numbers (수집 / 요약) -->
            <div class="flex items-center gap-1 text-[9px] sm:text-[10px] font-mono font-bold mb-1">
              <span class="${isCurrent ? 'text-indigo-600 font-extrabold' : 'text-ink-muted'}" title="수집 건수">${d.inbox_count || 0}</span>
              <span class="text-slate-300">/</span>
              <span class="${isCurrent ? 'text-emerald-600 font-extrabold' : 'text-emerald-600/80'}" title="AI 요약 건수">${enrichedCount}</span>
            </div>

            <!-- Dual Bars (수집 인디고 바 + AI 요약 에메랄드 바) -->
            <div class="w-full max-w-[58px] sm:max-w-[76px] flex items-end justify-center gap-1 sm:gap-1.5 h-24 ${isFuture ? 'opacity-30' : ''}">
              <!-- Ingestion Bar (수집) -->
              <div class="flex-1 ${isCurrent ? 'bg-indigo-500 ring-2 ring-indigo-400 animate-pulse' : 'bg-indigo-600'} rounded-t-sm sm:rounded-t-md transition-all duration-500 hover:bg-indigo-700" style="height: ${hPct}%; min-height: 0;" title="수집량: ${d.inbox_count || 0}건"></div>
              <!-- AI Enriched Bar (요약) -->
              <div class="flex-1 ${isCurrent ? 'bg-emerald-400 ring-1 ring-emerald-300' : 'bg-emerald-500'} rounded-t-sm sm:rounded-t-md transition-all duration-500 hover:bg-emerald-600" style="height: ${hEnrichedPct}%; min-height: 0;" title="AI 요약완료: ${enrichedCount}건"></div>
            </div>

            <!-- Label -->
            <span class="text-[10px] sm:text-[11px] font-mono font-bold ${isCurrent ? 'text-indigo-600 font-extrabold' : 'text-ink-muted'} mt-2 group-hover:text-indigo-600 transition text-center">
              ${d.slot}
            </span>
          `;
          tlContainer.appendChild(col);
        });

        // Update Timeline Footer with exact sums
        const totCollected = tData.reduce((acc, cur) => acc + (cur.inbox_count || 0), 0);
        const totEnriched = tData.reduce((acc, cur) => acc + (cur.enriched_count !== undefined ? cur.enriched_count : ((cur.news_count || 0) + (cur.model_count || 0))), 0);
        const ftEl = document.getElementById('timelineFooterText');
        if (ftEl) {
          ftEl.innerHTML = `⚡ 당일 24H 수집: <b class="text-indigo-700">${totCollected}건</b> │ ✨ AI 요약분석 완료: <b class="text-emerald-700">${totEnriched}건</b>`;
        }
      }

      // 2. Render 1-Day 4-Sessions AI Trend Radar (Active Session)
      renderRadarSession();
    }

    // ================= RENDER EXECUTIVE SCANNABLE CARDS =================
    function renderCards() {
      const grid = document.getElementById('cardsGrid');
      grid.innerHTML = '';
      const t = i18n[currentLang];

      // Update Counts
      const countUser = liveCasesData.filter(c => (c.curation?.discovery_mode || 'USER_CURATED') === 'USER_CURATED').length;
      const countAuto = liveCasesData.filter(c => (c.curation?.discovery_mode || 'USER_CURATED') === 'AUTO_HARVESTED').length;
      document.getElementById('badgeCountAll').innerText = liveCasesData.length;
      document.getElementById('badgeCountUser').innerText = countUser;
      const autoBadge = document.getElementById('badgeCountAuto');
      if (autoBadge) autoBadge.innerText = countAuto;
      document.getElementById('headerVerifiedCount').innerText = '(' + liveCasesData.length + ')';
      const mCount = document.getElementById('mHeaderVerifiedCount');
      if (mCount) mCount.innerText = '(' + liveCasesData.length + ')';

      const filtered = liveCasesData.filter(c => {
        const mode = c.curation ? c.curation.discovery_mode : 'USER_CURATED';
        const matchesMode = currentMode === 'ALL' || mode === currentMode;
        
        const cat = (c.category || '').toLowerCase();
        const cluster = (c.clustering?.cluster_id || '').toLowerCase();
        const fullTxt = (c.title + ' ' + (c.clustering?.cluster_name || '') + ' ' + cat).toLowerCase();

        let matchesDomain = true;
        if (currentDomain === 'frontend') {
          matchesDomain = cat.includes('design') || cat.includes('frontend') || cat.includes('media') || cluster.includes('design') || cluster.includes('media') || fullTxt.includes('taste') || fullTxt.includes('concat');
        } else if (currentDomain === 'agent') {
          matchesDomain = cat.includes('agent') || cluster.includes('agent') || fullTxt.includes('openworker') || fullTxt.includes('praxist');
        } else if (currentDomain === 'scraping') {
          matchesDomain = cat.includes('scraping') || cat.includes('browser') || cluster.includes('scraping') || fullTxt.includes('watercrawl') || fullTxt.includes('obscura');
        } else if (currentDomain === 'doc') {
          matchesDomain = cat.includes('doc') || cat.includes('ocr') || cluster.includes('doc') || fullTxt.includes('docling') || fullTxt.includes('anydoc');
        } else if (currentDomain === '3d') {
          matchesDomain = cat.includes('3d') || cat.includes('graphics') || cluster.includes('3d') || fullTxt.includes('three');
        } else if (currentDomain === 'rust') {
          matchesDomain = fullTxt.includes('rust') || fullTxt.includes('omarchy') || fullTxt.includes('serverbox');
        } else if (currentDomain === 'other') {
          const isStandard = cat.includes('design') || cat.includes('frontend') || cat.includes('media') || cat.includes('agent') || cat.includes('scraping') || cat.includes('doc') || cat.includes('3d') || fullTxt.includes('rust');
          matchesDomain = !isStandard;
        }

        const story = c.portfolio_story || {};
        const searchTxt = (c.title + ' ' + (c.title_zh || '') + ' ' + (c.title_en || '') + ' ' + cat + ' ' + (story.the_hook || '') + ' ' + (c.curation?.personal_motivation || '')).toLowerCase();
        const matchesSearch = searchTxt.includes(searchQuery.toLowerCase());

        return matchesMode && matchesDomain && matchesSearch;
      });

      // 🌟 Precision DateTime Sorting (Unified)
      sortCollection(filtered, currentSort);

      document.getElementById('resultsCountLabel').innerText = currentLang === 'KO' ? `총 ${filtered.length}건 표시 (전체 ${liveCasesData.length}건 중)` : (currentLang === 'ZH' ? `显示 ${filtered.length} 项 (共 ${liveCasesData.length} 项)` : `Showing ${filtered.length} of ${liveCasesData.length} dossiers`);

      const totalPages = Math.ceil(filtered.length / PAGE_SIZE) || 1;
      if (currentPortfolioPage > totalPages) currentPortfolioPage = totalPages;
      if (currentPortfolioPage < 1) currentPortfolioPage = 1;

      renderPagination('portfolioPagination', currentPortfolioPage, totalPages, 'changePortfolioPage');

      if (filtered.length === 0) {
        grid.innerHTML = `<div class="col-span-full py-16 text-center text-ink-muted font-medium">${currentLang === 'KO' ? '일치하는 기술 검증 보고서가 없습니다.' : (currentLang === 'ZH' ? '未找到符合条件的技术核查报告。' : 'No matching fact-check dossiers found.')}</div>`;
        return;
      }

      // Render Executive Scannable Cards (Paged: 20 per page)
      const pagedItems = filtered.slice((currentPortfolioPage - 1) * PAGE_SIZE, currentPortfolioPage * PAGE_SIZE);
      const fragment = document.createDocumentFragment();
      pagedItems.forEach((c, idx) => {
        const story = c.portfolio_story || {};
        const curation = c.curation || { discovery_mode: 'USER_CURATED' };
        const isUserMode = curation.discovery_mode === 'USER_CURATED';
        
        const parseDate = (d) => {
          if (!d) return '2026-09-02';
          const m = String(d).match(/([0-9][0-9][0-9][0-9])[-_]([0-9][0-9])[-_]([0-9][0-9])/);
          return m ? `${m[1]}-${m[2]}-${m[3]}` : '2026-09-02';
        };
        const srcDate = parseDate(c.source_published_date || c.investigation_date);
        const invDate = parseDate(c.investigation_date || c.source_published_date);
        const confScore = c.confidence_score || 95.0;
        const isVerifiedTrue = c.verdict === 'VERIFIED_TRUE';
        const isHalfTrue = c.verdict.includes('HALF');

        const { displayTitle, displayHook } = getLocalizedContent(c, currentLang);
        let displayMotivation = displayHook;
        let displayTruth = displayHook || 'Empirical benchmark completed.';

        // 🌟 Engagement Metric Tag Enhancement for Motivation
        let motivationHtml = displayMotivation;
        const tagMatch = displayMotivation.match(new RegExp('^\\\\[(.*?)\\\\]\\\s*(.*)$'));
        if (tagMatch) {
          motivationHtml = `<span class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold font-mono bg-indigo-50 text-indigo-700 border border-indigo-200 mr-1.5">${tagMatch[1]}</span><span>${tagMatch[2]}</span>`;
        }

        // Verdict Badge for Completed Portfolios
        let verdictLabel = '';
        let verdictClass = '';
        let dotClass = '';

        if (isVerifiedTrue) {
          verdictLabel = currentLang === 'KO' ? '사실 검증됨' : (currentLang === 'ZH' ? '经实测属实' : 'VERIFIED TRUE');
          verdictClass = 'verdict-true';
          dotClass = 'bg-emerald-600';
        } else if (isHalfTrue) {
          verdictLabel = currentLang === 'KO' ? '절반의 사실' : (currentLang === 'ZH' ? '部分属实' : 'HALF TRUE');
          verdictClass = 'verdict-half';
          dotClass = 'bg-amber-600';
        } else {
          verdictLabel = currentLang === 'KO' ? '과장/왜곡' : (currentLang === 'ZH' ? '夸大/失真' : 'EXAGGERATED');
          verdictClass = 'verdict-gamed';
          dotClass = 'bg-rose-600';
        }

        const card = document.createElement('div');
        card.className = 'executive-card p-4 sm:p-6 flex flex-col justify-between cursor-pointer space-y-4 group';
        card.onclick = () => openModal(c);

        card.innerHTML = `
          <div class="space-y-3.5">
            
            <!-- Tier 1: Header Meta (ID + Mode Badge + Dual Dates + Verdict) -->
            <div class="flex items-center justify-between text-xs gap-2 flex-wrap">
              <div class="flex items-center gap-1.5 sm:gap-2 flex-wrap">
                <span class="text-xs font-mono font-bold text-ink-muted">#${String(idx + 1).padStart(2, '0')}</span>
                <span class="px-2 py-0.5 rounded-full text-[10px] font-bold font-mono ${isUserMode ? 'bg-indigo-50 text-indigo-700 border border-indigo-200' : 'bg-emerald-50 text-emerald-700 border border-emerald-200'}">
                  ${isUserMode ? (currentLang === 'KO' ? '직접 큐레이션' : (currentLang === 'ZH' ? '手动精选' : 'USER CURATED')) : (currentLang === 'KO' ? '자동 트렌드' : (currentLang === 'ZH' ? '自动趋势' : 'AUTO HARVEST'))}
                </span>
                <div class="flex items-center gap-1.5 text-[11px] font-mono text-ink-muted">
                  <span title="${currentLang === 'KO' ? '수집/원출처 발행일' : (currentLang === 'ZH' ? '采集/原文发布日' : 'Source Date')}">📅 ${srcDate}</span>
                  <span>•</span>
                  <span title="${currentLang === 'KO' ? '심층 기술 분석일' : (currentLang === 'ZH' ? '深度分析日' : 'Audit Date')}" class="text-indigo-700 font-semibold">🔬 ${invDate}</span>
                </div>
              </div>

              <!-- Verdict Pill Badge -->
              <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold font-mono flex items-center gap-1.5 ${verdictClass}">
                <span class="w-1.5 h-1.5 rounded-full ${dotClass}"></span>
                ${verdictLabel}
              </span>
            </div>

            <!-- Tier 2: Bold Headline -->
            <div class="space-y-1">
              <span class="text-[11px] text-ink-muted font-mono font-semibold uppercase tracking-wider">${c.category || 'AI Technology'}</span>
              <h3 class="font-bold text-base text-ink-primary group-hover:text-indigo-600 transition leading-snug">
                ${displayTitle}
              </h3>
            </div>

            <!-- Tier 3: 2-Tier Structured Scannable Block (Motivation vs Truth) -->
            <div class="space-y-2 pt-1">
              <!-- Block 1: Problem / Motivation -->
              <div class="p-3 rounded-xl bg-surface-subtle border border-surface-border text-xs space-y-1">
                <div class="text-[11px] font-bold text-ink-secondary flex items-center gap-1.5">
                  <i data-lucide="compass" class="w-3.5 h-3.5 text-indigo-600"></i> ${t.cardMotivationLabel}
                </div>
                <p class="text-xs text-ink-secondary leading-relaxed line-clamp-2">${motivationHtml}</p>
              </div>

              <!-- Block 2: Key Verdict / Truth -->
              <div class="p-3 rounded-xl bg-emerald-50/70 border border-emerald-200 text-xs space-y-1">
                <div class="text-[11px] font-bold text-emerald-900 flex items-center gap-1.5">
                  <i data-lucide="zap" class="w-3.5 h-3.5 text-emerald-700"></i> ${t.cardVerdictLabel}
                </div>
                <p class="text-xs text-emerald-950 leading-relaxed font-medium line-clamp-2">${displayTruth}</p>
              </div>
            </div>

          </div>

          <!-- Tier 4: Standardized 3-Line Footer -->
          <div class="pt-3 border-t border-surface-border space-y-1.5 text-xs font-mono">
            <!-- Line 1: 수집날짜&시간 -->
            <div class="flex items-center justify-between text-ink-muted text-[11px]">
              <span title="${currentLang === 'KO' ? '수집/원출처 발행일' : (currentLang === 'ZH' ? '采集/发布日' : 'Source Date')}">📅 ${srcDate}</span>
              <span class="text-emerald-700 font-bold flex items-center gap-1 font-sans">
                <i data-lucide="shield-check" class="w-3.5 h-3.5"></i> ${t.cardConfidenceLabel} ${confScore.toFixed(1)}%
              </span>
            </div>

            <!-- Line 2: 분석날짜&시간 (분석모델) -->
            <div class="flex items-center justify-between text-indigo-700 text-[11px] font-semibold gap-2">
              <span title="${currentLang === 'KO' ? '심층 기술 분석일' : (currentLang === 'ZH' ? '深度分析日' : 'Audit Date')}" class="flex items-center gap-1.5 min-w-0 overflow-hidden">
                <span class="shrink-0">🔬 ${invDate}</span>
                <span class="text-ink-muted font-normal truncate min-w-0 align-bottom cursor-help" title="${c.curation?.audited_by_model || c.audited_by_model || 'gemini-3.8-flash-medium'}">(${formatModelAttribution(c.curation?.audited_by_model || c.audited_by_model || 'gemini-3.8-flash-medium')})</span>
              </span>
              <span class="text-ink-muted font-normal shrink-0">${(c.sources || []).length}${t.cardSourcesLabel}</span>
            </div>

            <!-- Line 3: 원문 및 상세 보기 액션 -->
            <div class="flex items-center justify-between pt-0.5 font-sans">
              <span class="text-[11px] text-ink-muted font-mono flex items-center gap-1">
                ${c.sources && c.sources.length > 0 ? `<a href="${c.sources[0].url}" target="_blank" onclick="event.stopPropagation();" class="text-indigo-600 hover:underline flex items-center gap-0.5 font-semibold">📄 ${currentLang === 'KO' ? '원문' : (currentLang === 'ZH' ? '原文' : 'Source')} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>` : ''}
              </span>
              <button class="text-ink-primary font-bold text-xs group-hover:translate-x-0.5 transition flex items-center gap-1">
                ${t.cardViewBtn} <i data-lucide="arrow-right" class="w-3.5 h-3.5 text-ink-primary"></i>
              </button>
            </div>
          </div>
        `;
        fragment.appendChild(card);
      });
      grid.appendChild(fragment);

      if (window.lucide) window.lucide.createIcons({ root: grid });
    }

    // ================= MODAL HANDLER & DEEP LINKING ROUTER =================
    function openModal(c, skipHistory = false) {
      if (!c) return;
      const cid = c.case_id || c.investigation_id;
      if (!skipHistory && cid) {
        const targetHash = '#/factchecks?case=' + encodeURIComponent(cid);
        if (window.location.hash !== targetHash) {
          try { history.pushState({ caseId: cid, view: currentView }, '', targetHash); } catch (e) {}
        }
      }

      const modal = document.getElementById('detailModal');
      const story = c.portfolio_story || {};
      const handsOn = story.hands_on_log || {};
      const curation = c.curation || {};
      const clustering = c.clustering || {};
      const rawPost = c.raw_viral_post || {};
      const t = i18n[currentLang];

      let displayTitle = c.title;
      let displayMotivation = curation.personal_motivation || story.the_hook || '';
      let displayQuote = rawPost.quote || '';

      if (currentLang === 'ZH') {
        displayTitle = c.title_zh || c.title;
        displayMotivation = curation.personal_motivation_zh || displayMotivation;
        displayQuote = rawPost.quote_zh || displayQuote;
      } else if (currentLang === 'EN') {
        displayTitle = c.title_en || c.title;
        displayMotivation = curation.personal_motivation_en || displayMotivation;
      }

      document.getElementById('modalTitle').innerText = displayTitle;
      document.getElementById('modalModeBadge').innerText = currentLang === 'KO' ? '기술 검증 리포트' : (currentLang === 'ZH' ? '技术核验报告' : 'AUDITED DOSSIER');
      document.getElementById('modalModeBadge').className = 'text-xs px-2.5 py-0.5 rounded-md font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200';
      
      document.getElementById('modalClusterBadge').innerText = clustering.cluster_name || c.category || 'Tech';
      document.getElementById('modalVerdictBadge').innerText = c.verdict;
      document.getElementById('modalVerdictBadge').className = c.verdict === 'VERIFIED_TRUE' ? 'text-xs px-2.5 py-0.5 rounded-md font-semibold verdict-true' : 'text-xs px-2.5 py-0.5 rounded-md font-semibold verdict-half';
      document.getElementById('modalStageBadge').innerText = handsOn.status === 'ACTIVE_DEVELOPED' ? (currentLang === 'KO' ? '실제 개발 적용' : (currentLang === 'ZH' ? '生产级落地' : 'Production Active')) : (currentLang === 'KO' ? '기술 조사 완료' : (currentLang === 'ZH' ? '已审计完毕' : 'Audited'));

      document.getElementById('modalMotivation').innerText = displayMotivation;
      document.getElementById('modalWorkflow').innerText = curation.target_workflow || 'Universal AI Pipeline';

      // 🌟 VIRAL CLAIMS DOSSIER (Hides cleanly when quote is missing)
      const viralBox = document.getElementById('modalViralPostBox');
      const hasQuote = displayQuote && displayQuote.trim().length > 0;

      if (hasQuote) {
        viralBox.classList.remove('hidden');
        document.getElementById('modalSecViralPostTitle').innerText = t.modalSecViralPostTitle;
        document.getElementById('modalViralPlatformBadge').innerText = rawPost.platform || 'Social Post';
        document.getElementById('modalViralAuthor').innerText = (rawPost.author ? (rawPost.author + ' : ') : '') + (rawPost.screenshot_note || 'Viral Marketing Post Evidence');
        document.getElementById('modalViralQuote').innerText = `"${displayQuote}"`;
        document.getElementById('modalViralNote').innerText = rawPost.screenshot_note || '';
        document.getElementById('modalViralLinkText').innerText = t.modalViralLinkText;
        
        const directLink = document.getElementById('modalViralDirectLink');
        if (rawPost.post_url) {
          directLink.href = rawPost.post_url;
          directLink.classList.remove('hidden');
        } else if (rawPost.url) {
          directLink.href = rawPost.url;
          directLink.classList.remove('hidden');
        } else if (c.sources && c.sources.length > 0) {
          directLink.href = c.sources[0].url;
          directLink.classList.remove('hidden');
        } else {
          directLink.classList.add('hidden');
        }
      } else {
        viralBox.classList.add('hidden');
      }

      document.getElementById('modalHook').innerText = (currentLang === 'ZH' && story.the_hook_zh) ? story.the_hook_zh : (story.the_hook || '');
      document.getElementById('modalHype').innerText = story.marketing_hype_anatomy ? ((currentLang === 'KO' ? '과장 마케팅 해부: ' : (currentLang === 'ZH' ? '营销炒作解构: ' : 'Marketing Hype Anatomy: ')) + story.marketing_hype_anatomy) : '';
      
      document.getElementById('modalHandsOnEnv').innerText = handsOn.test_environment || handsOn.environment ? ((currentLang === 'KO' ? '환경: ' : (currentLang === 'ZH' ? '实测环境: ' : 'Env: ')) + (handsOn.test_environment || handsOn.environment)) : '';
      document.getElementById('modalHandsOnMetrics').innerText = handsOn.measured_results ? ((currentLang === 'KO' ? '실측치: ' : (currentLang === 'ZH' ? '实测指标: ' : 'Metrics: ')) + handsOn.measured_results) : (handsOn.measured_metrics ? Object.entries(handsOn.measured_metrics).map(([k, v]) => `${k}: ${v}`).join(' | ') : '');
      document.getElementById('modalHandsOnDetails').innerText = handsOn.details || handsOn.failure_modes || story.empirical_findings || 'Empirical benchmark verified.';

      // Claims vs Reality
      const claimsBox = document.getElementById('modalClaimsBox');
      const claimsList = document.getElementById('modalClaimsList');
      const claims = (c.claims_assessment && c.claims_assessment.length > 0) ? c.claims_assessment : (c.marketing_claims || []);
      if (claims && claims.length > 0) {
        claimsBox.classList.remove('hidden');
        document.getElementById('modalSecClaimsTitle').innerText = t.modalSecClaimsTitle || 'Marketing Claims vs Empirical Reality';
        claimsList.innerHTML = claims.map(cl => {
          const claimTitle = cl.claim || cl.statement || cl.claim_title || cl.claim_text || cl.marketing_hook || '';
          const claimTruth = cl.reality || cl.fact_checked_truth || cl.verification_evidence || cl.empirical_reality || cl.reality_check || '';
          const claimStatus = cl.status || cl.verdict || cl.claim_verdict || 'VERIFIED';
          const isTrue = (claimStatus === 'VERIFIED_TRUE' || claimStatus === 'TRUE');
          const isFalse = (claimStatus === 'FALSE' || claimStatus === 'FALSE_CLAIM' || claimStatus === 'GAMED_CLAIM' || claimStatus === 'MARKETING_HYPE');
          const statusClass = isTrue ? 'text-emerald-700 bg-emerald-50 border border-emerald-200' : (isFalse ? 'text-rose-700 bg-rose-50 border border-rose-200' : 'text-amber-800 bg-amber-50 border border-amber-200');
          return `
            <div class="p-3 rounded-lg bg-white border border-amber-200 text-xs space-y-1.5 shadow-sm">
              <div class="flex items-center justify-between font-mono text-[11px] gap-2 flex-wrap">
                <span class="text-ink-primary font-bold">Claim: "${claimTitle}"</span>
                <span class="px-2 py-0.5 rounded text-[10px] font-bold ${statusClass}">${claimStatus}</span>
              </div>
              <div class="text-ink-secondary font-medium leading-relaxed">${currentLang === 'KO' ? '🔬 실증 팩트 검증:' : (currentLang === 'ZH' ? '🔬 实测事实核验:' : '🔬 Empirical Verification:')} ${claimTruth}</div>
            </div>
          `;
        }).join('');
      } else {
        claimsBox.classList.add('hidden');
      }

      // Alternatives Table
      const altBody = document.getElementById('modalAlternativesBody');
      const alts = clustering.alternatives || c.alternatives || [];
      if (alts && alts.length > 0) {
        altBody.innerHTML = alts.map(a => `
          <tr>
            <td class="p-3 font-bold text-ink-primary">${a.name || a.tool_name || ''}</td>
            <td class="p-3 font-mono text-ink-secondary text-[11px]">${a.tech_stack || a.stack || '-'}</td>
            <td class="p-3 text-emerald-700">${a.pros || '-'}</td>
            <td class="p-3 text-rose-700">${a.cons || '-'}</td>
            <td class="p-3 text-ink-secondary font-medium">${a.best_for || '-'}</td>
          </tr>
        `).join('');
      } else {
        altBody.innerHTML = `<tr><td colspan="5" class="p-4 text-center text-ink-muted">${currentLang === 'KO' ? '등록된 대체 기술 비교 데이터가 없습니다.' : (currentLang === 'ZH' ? '暂无替代方案对比数据。' : 'No comparative alternatives registered.')}</td></tr>`;
      }

      // Sources
      const sourcesList = document.getElementById('modalSourcesList');
      const sources = c.sources || [];
      sourcesList.innerHTML = sources.map(s => `
        <a href="${s.url}" target="_blank" rel="noopener noreferrer" class="p-2.5 rounded-xl bg-surface-subtle border border-surface-border hover:border-ink-primary flex items-center justify-between text-xs text-ink-secondary hover:text-ink-primary transition">
          <div class="space-y-0.5">
            <span class="text-[10px] font-mono text-ink-primary uppercase font-bold">${s.tier || 'Tier 1'} • ${s.type || 'Repository'}</span>
            <div class="font-medium truncate max-w-[240px] text-ink-primary">${s.name || s.title || 'Source Link'}</div>
          </div>
          <i data-lucide="external-link" class="w-3.5 h-3.5 text-ink-muted shrink-0"></i>
        </a>
      `).join('');

      modal.classList.remove('hidden');
      document.body.style.overflow = 'hidden';
      lucide.createIcons();
    }

    function openCaseModal(caseId) {
      if (!caseId) return;
      const c = (liveCasesData || []).find(x => x.case_id === caseId || x.investigation_id === caseId) || (casesData || []).find(x => x.case_id === caseId);
      if (c) {
        openModal(c);
      }
    }

    function closeModal(pushHistory = true) {
      const modal = document.getElementById('detailModal');
      if (modal) modal.classList.add('hidden');
      document.body.style.overflow = 'auto';

      if (pushHistory) {
        const targetHash = ROUTES[currentView] || '#/' + currentView;
        if (window.location.hash !== targetHash) {
          try {
            history.pushState({ view: currentView }, '', targetHash);
          } catch (e) {
            window.location.hash = targetHash;
          }
        }
      }
    }

    // ================= UNIVERSAL ROUTE & POPSTATE DISPATCHER =================
    function handleHashRoute() {
      const hash = window.location.hash || '';

      // 1. Deep Link to Modal: #/factchecks?case=... or #case/...
      if (hash.includes('case=') || hash.startsWith('#case/')) {
        let targetCaseId = '';
        if (hash.includes('case=')) {
          const m = hash.match(/case=([^&]+)/);
          if (m) targetCaseId = decodeURIComponent(m[1]);
        } else {
          targetCaseId = decodeURIComponent(hash.replace('#case/', ''));
        }

        if (targetCaseId) {
          switchView('portfolio', false, true);
          const target = (liveCasesData || []).find(c => c.case_id === targetCaseId || c.investigation_id === targetCaseId) || (casesData || []).find(c => c.case_id === targetCaseId);
          if (target) {
            openModal(target, false);
            return;
          }
        }
      }

      // If modal is open and user navigates back to tab without modal query, close modal
      closeModal(false);

      // 2. Parse Route and Query Page
      const [routePart, queryPart] = hash.split('?');
      const params = new URLSearchParams(queryPart || '');
      const pageParam = parseInt(params.get('page'), 10) || 1;

      let targetView = 'home';
      if (routePart.startsWith('#/factchecks') || routePart.startsWith('#factchecks') || routePart.startsWith('#/portfolio')) {
        targetView = 'portfolio';
      } else if (routePart.startsWith('#/news') || routePart.startsWith('#news')) {
        targetView = 'news';
      } else if (routePart.startsWith('#/models') || routePart.startsWith('#models')) {
        targetView = 'models';
      } else if (routePart.startsWith('#/graph') || routePart.startsWith('#graph')) {
        targetView = 'graph';
      } else if (routePart.startsWith('#/inbox') || routePart.startsWith('#inbox')) {
        targetView = 'inbox';
      } else {
        targetView = 'home';
      }

      if (currentView !== targetView) {
        switchView(targetView, false, false);
      } else if (targetView === 'home') {
        renderTelemetryCharts();
      updateCronCountdown();
        renderHomeTopPicks();
      }

      // 3. Apply Page State to Active View (Enables Back/Forward Through Pages)
      if (targetView === 'news') {
        if (currentNewsPage !== pageParam) {
          changeNewsPage(pageParam, false);
        }
      } else if (targetView === 'portfolio') {
        if (currentPortfolioPage !== pageParam) {
          changePortfolioPage(pageParam, false);
        }
      } else if (targetView === 'models') {
        if (currentModelsPage !== pageParam) {
          changeModelsPage(pageParam, false);
        }
      } else if (targetView === 'inbox') {
        if (currentInboxPage !== pageParam) {
          changeInboxPage(pageParam, false);
        }
      }
    }

    window.addEventListener('popstate', handleHashRoute);
    window.addEventListener('hashchange', handleHashRoute);
    window.addEventListener('load', () => {
      setTimeout(handleHashRoute, 150);
    });

    function cleanDescriptionText(desc, title) {
      if (!desc || typeof desc !== 'string') return '';
      let d = desc.trim();
      d = d.replace(/^HN\s*Score:\s*\d+\s*pts\s*(\\|\s*Comments:\s*\d+\s*)?(\\|\s*)?/i, '');
      d = d.replace(/^Abstract:\s*/i, '');
      if (title && d.toLowerCase() === title.toLowerCase().trim()) {
        return '';
      }
      return d.trim();
    }

    // ================= REUSABLE CARD & PRESENTATION COMPONENTS (DRY) =================
    function getLocalizedContent(it, lang = currentLang) {
      if (!it) return { displayTitle: '', displayHook: '', displayDesc: '', displayTakeaways: [], hasTrilingual: false };
      const ai = it.ai_enrichment;
      const multi = it.multilingual || (ai ? ai.multilingual : null);
      const story = it.portfolio_story || {};

      let displayTitle = '';
      let displayHook = '';
      let displayDesc = '';
      let displayTakeaways = [];

      if (lang === 'ZH') {
        displayTitle = multi?.zh?.title || it.title_zh || multi?.en?.title || it.title_en || it.title || '';
        displayHook = multi?.zh?.hook || it.hook_zh || story.the_hook_zh || it.curation?.personal_motivation_zh || (ai ? ai.hook : '') || it.hook || story.the_hook || it.curation?.personal_motivation || '';
        displayDesc = multi?.zh?.description || it.description_zh || displayHook || it.description || '';
        if (multi?.zh?.key_takeaways?.length > 0) displayTakeaways = multi.zh.key_takeaways;
        else if (it.key_takeaways_zh?.length > 0) displayTakeaways = it.key_takeaways_zh;
      } else if (lang === 'EN') {
        displayTitle = multi?.en?.title || it.title_en || it.title || '';
        displayHook = multi?.en?.hook || it.hook_en || story.the_hook_en || it.curation?.personal_motivation_en || (ai ? ai.hook : '') || it.hook || story.the_hook || it.curation?.personal_motivation || '';
        displayDesc = multi?.en?.description || it.description_en || displayHook || it.description || '';
        if (multi?.en?.key_takeaways?.length > 0) displayTakeaways = multi.en.key_takeaways;
        else if (it.key_takeaways_en?.length > 0) displayTakeaways = it.key_takeaways_en;
      } else {
        // Default KO
        displayTitle = multi?.ko?.title || it.title_ko || it.title || '';
        displayHook = multi?.ko?.hook || it.hook_ko || story.the_hook || it.curation?.personal_motivation || (ai ? ai.hook : '') || it.hook || '';
        displayDesc = multi?.ko?.description || it.description_ko || it.description || displayHook || '';
        if (multi?.ko?.key_takeaways?.length > 0) displayTakeaways = multi.ko.key_takeaways;
        else if (it.key_takeaways?.length > 0) displayTakeaways = it.key_takeaways;
        else if (ai?.key_takeaways?.length > 0) displayTakeaways = ai.key_takeaways;
      }

      // Deduplicate Hook: Hook must ONLY appear in the yellow callout box
      if (displayHook) {
        const cleanH = displayHook.trim();
        if (displayDesc.trim() === cleanH) {
          displayDesc = '';
        } else if (cleanH && displayDesc.includes(cleanH)) {
          displayDesc = displayDesc.replace(cleanH, '').trim();
        }
      }

      displayDesc = cleanDescriptionText(displayDesc, displayTitle);
      const hasTrilingual = Boolean((multi && multi.zh && multi.ko && multi.en) || (it.title_zh && it.title_en));

      return {
        displayTitle,
        displayHook,
        displayDesc,
        displayTakeaways,
        hasTrilingual
      };
    }

    function renderHookCallout(displayHook) {
      if (!displayHook) return '';
      return `
        <div class="p-2.5 rounded-xl bg-amber-50/70 border border-amber-200/80 text-[11px] text-amber-950 font-medium leading-relaxed flex items-start gap-1.5">
          <span class="shrink-0 font-bold text-amber-800">🪝 Hook:</span>
          <span>${displayHook}</span>
        </div>
      `;
    }

    function renderAiTakeaways(takeaways, lang = currentLang) {
      if (!Array.isArray(takeaways) || takeaways.length === 0) return '';
      return `
        <div class="mt-2 p-3 rounded-xl bg-gradient-to-br from-indigo-50/50 via-sky-50/40 to-purple-50/50 border border-indigo-100 text-[11px] space-y-1.5 font-sans">
          <div class="flex items-center gap-1 text-indigo-950 font-bold text-[10px]">
            <i data-lucide="sparkles" class="w-3 h-3 text-indigo-600"></i>
            <span>${lang === 'KO' ? 'AI 3줄 핵심 요약' : (lang === 'ZH' ? 'AI 3行核心摘要' : 'AI 3-Line Summary')}</span>
          </div>
          <ul class="space-y-1 text-ink-secondary leading-relaxed list-disc list-inside">
            ${takeaways.map(k => `<li>${k}</li>`).join('')}
          </ul>
        </div>
      `;
    }

    function renderRelatedDossierButton(rel, lang = currentLang) {
      if (!rel || !rel.case_id) return '';
      const label = lang === 'KO' ? '관련 기술 검증: ' : (lang === 'ZH' ? '关联技术核验: ' : 'Related Verification: ');
      return `
        <div class="pt-2 border-t border-surface-border">
          <button onclick="openCaseModal('${rel.case_id}')" class="w-full text-left px-2.5 py-1.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 text-[11px] text-emerald-950 font-semibold flex items-center justify-between transition">
            <span class="flex items-center gap-1.5">
              <i data-lucide="shield-check" class="w-3.5 h-3.5 text-emerald-600"></i>
              <span>${label}${rel.target_tech || ''}</span>
            </span>
            <i data-lucide="arrow-right" class="w-3 h-3 text-emerald-600"></i>
          </button>
        </div>
      `;
    }

    function renderCardStandardFooter(it, lang = currentLang, extraActionHtml = '') {
      const ai = it.ai_enrichment;
      const pubLabel = lang === 'KO' ? '발행' : (lang === 'ZH' ? '发布' : 'Published');
      const hrvLabel = lang === 'KO' ? '수집' : (lang === 'ZH' ? '采集' : 'Harvested');
      const updLabel = lang === 'KO' ? '최신 갱신일' : (lang === 'ZH' ? '最新更新' : 'Updated');
      const srcLabel = lang === 'KO' ? '원문' : (lang === 'ZH' ? '原文' : 'Source');
      const pendingLabel = lang === 'KO' ? 'AI요약 대기중' : (lang === 'ZH' ? 'AI分析排队中' : 'Pending AI Audit');

      const pubDate = formatDateTimeCompact(it.published_at || it.created_at || it.harvested_at);
      const hrvDate = formatDateTimeCompact(it.harvested_at || it.harvested_date || it.created_at);
      const hasUpdate = it.updated_at && it.updated_at !== (it.harvested_at || it.harvested_date);
      const updDate = hasUpdate ? formatDateTimeCompact(it.updated_at) : '';

      let auditHtml = `
        <div class="text-[11px] text-ink-muted flex items-center gap-1.5">
          <span>🔬 ${pendingLabel}</span>
        </div>
      `;
      if (ai?.enriched_at) {
        auditHtml = `
          <div class="text-[11px] text-indigo-700 font-semibold flex items-center gap-1.5 min-w-0 overflow-hidden">
            <span class="shrink-0">🔬 ${formatDateTimeCompact(ai.enriched_at)}</span>
            <span class="text-ink-muted font-normal truncate min-w-0 align-bottom cursor-help" title="${ai.enriched_by_model || ''}">(${formatModelAttribution(ai.enriched_by_model)})</span>
          </div>
        `;
      }

      const defaultSourceLink = it.source_url ? `
        <a href="${it.source_url}" target="_blank" rel="noopener noreferrer" class="text-indigo-600 hover:underline flex items-center gap-0.5 font-semibold">
          📄 ${srcLabel} <i data-lucide="external-link" class="w-2.5 h-2.5"></i>
        </a>
      ` : '';

      return `
        <div class="pt-3 border-t border-surface-border space-y-1.5 text-xs font-mono">
          <div class="text-[11px] text-ink-muted flex items-center justify-between gap-1 flex-wrap">
            <span>📰 ${pubLabel}: ${pubDate}</span>
          </div>
          <div class="text-[11px] text-ink-muted flex items-center justify-between gap-1 flex-wrap">
            <span>📥 ${hrvLabel}: ${hrvDate}</span>
            ${hasUpdate ? `<span class="text-[10px] text-indigo-600 font-bold" title="${updLabel}">(🔄 ${updDate})</span>` : ''}
          </div>
          ${auditHtml}
          <div class="flex items-center justify-between pt-0.5 font-sans">
            <span class="text-[11px] text-ink-muted font-mono flex items-center gap-1">
              ${defaultSourceLink}
            </span>
            ${extraActionHtml || ''}
          </div>
        </div>
      `;
    }

    function sortCollection(items, sortKey) {
      if (!Array.isArray(items)) return [];
      return items.sort((a, b) => {
        const idA = a.case_id || a.inbox_id || a.id || '';
        const idB = b.case_id || b.inbox_id || b.id || '';

        if (sortKey === 'date-source-desc') {
          const diff = parseItemTimestamp(b, 'source') - parseItemTimestamp(a, 'source');
          if (diff !== 0) return diff;
          return idB.localeCompare(idA);
        }
        if (sortKey === 'date-source-asc' || sortKey === 'date-asc') {
          const diff = parseItemTimestamp(a, 'source') - parseItemTimestamp(b, 'source');
          if (diff !== 0) return diff;
          return idA.localeCompare(idB);
        }
        if (sortKey === 'date-audit-desc' || sortKey === 'date-desc') {
          const tB = parseItemTimestamp(b, 'audit');
          const tA = parseItemTimestamp(a, 'audit');
          if (tB !== tA) return tB - tA;
          const sB = parseItemTimestamp(b, 'source');
          const sA = parseItemTimestamp(a, 'source');
          if (sB !== sA) return sB - sA;
          return idB.localeCompare(idA);
        }
        if (sortKey === 'date-audit-asc') {
          const tA = parseItemTimestamp(a, 'audit');
          const tB = parseItemTimestamp(b, 'audit');
          if (tA > 0 && tB > 0 && tA !== tB) return tA - tB;
          if (tA > 0 && tB === 0) return -1;
          if (tB > 0 && tA === 0) return 1;
          const sDiff = parseItemTimestamp(a, 'source') - parseItemTimestamp(b, 'source');
          if (sDiff !== 0) return sDiff;
          return idA.localeCompare(idB);
        }
        if (sortKey === 'title-asc') {
          return (a.title || '').localeCompare(b.title || '');
        }
        if (sortKey === 'viral-desc') {
          return (typeof calculateStandardizedViralScore === 'function') ? (calculateStandardizedViralScore(b) - calculateStandardizedViralScore(a)) : 0;
        }
        if (sortKey === 'viral-asc') {
          return (typeof calculateStandardizedViralScore === 'function') ? (calculateStandardizedViralScore(a) - calculateStandardizedViralScore(b)) : 0;
        }
        const defDiff = parseItemTimestamp(b, 'source') - parseItemTimestamp(a, 'source');
        if (defDiff !== 0) return defDiff;
        return idB.localeCompare(idA);
      });
    }

    window.getLocalizedContent = getLocalizedContent;
    window.renderHookCallout = renderHookCallout;
    window.renderAiTakeaways = renderAiTakeaways;
    window.renderRelatedDossierButton = renderRelatedDossierButton;
    window.renderCardStandardFooter = renderCardStandardFooter;
    window.sortCollection = sortCollection;

    // ================= NEWS VIEW (2계층 카테고리화 엔진) =================
    let currentNewsTier1 = 'ALL';
    let currentNewsTier2 = 'ALL';
    let currentNewsSource = 'ALL';
    let currentNewsSort = 'date-audit-desc';
    let currentNewsSearch = '';

    function setNewsCategoryFilter(t1) {
      currentNewsPage = 1;
      currentNewsTier1 = t1;
      currentNewsTier2 = 'ALL';
      document.querySelectorAll('.news-cat-pill').forEach(btn => {
        if (btn.getAttribute('data-cat') === t1) {
          btn.className = 'news-cat-pill active px-3 py-1.5 rounded-xl text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap';
        } else {
          btn.className = 'news-cat-pill px-3 py-1.5 rounded-xl text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }
      });

      // Reset Tier 2 pills
      document.querySelectorAll('.news-t2-pill').forEach(btn => {
        if (btn.getAttribute('data-t2') === 'ALL') {
          btn.className = 'news-t2-pill active px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap';
        } else {
          btn.className = 'news-t2-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }
      });

      // If a non-computing domain is selected (e.g. Science, Law), dim/hide Tier 2 row
      const t2Container = document.getElementById('newsTier2Container');
      if (t2Container) {
        if (t1 !== 'ALL' && t1 !== 'TECH_COMPUTING') {
          t2Container.classList.add('opacity-40', 'pointer-events-none');
        } else {
          t2Container.classList.remove('opacity-40', 'pointer-events-none');
        }
      }

      renderNews();
    }

    function setNewsTier2Filter(t2) {
      currentNewsPage = 1;
      currentNewsTier2 = t2;
      document.querySelectorAll('.news-t2-pill').forEach(btn => {
        if (btn.getAttribute('data-t2') === t2) {
          btn.className = 'news-t2-pill active px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap';
        } else {
          btn.className = 'news-t2-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }
      });
      renderNews();
    }

    function handleNewsSearch(val) {
      targetSelectedInboxId = '';
      currentNewsPage = 1;
      currentNewsSearch = (val || '').trim().toLowerCase();
      renderNews();
    }

    function setNewsSort(sort) {
      currentNewsPage = 1;
      currentNewsSort = sort;
      renderNews();
    }

    function setNewsSourceFilter(src) {
      currentNewsPage = 1;
      currentNewsSource = src;
      document.querySelectorAll('.news-src-btn').forEach(btn => {
        if (btn.getAttribute('data-src') === src) {
          btn.className = 'news-src-btn active px-2.5 py-1 rounded-lg text-xs font-bold bg-ink-primary text-white transition shrink-0 whitespace-nowrap';
        } else {
          btn.className = 'news-src-btn px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:bg-white transition border border-surface-border shrink-0 whitespace-nowrap';
        }
      });
      renderNews();
    }

    // 🌟 Scalable Multi-Source Cross-Platform Clustering UX Engine
    function buildMultiSourceCluster(sources, rawItemId) {
      if (!sources || sources.length === 0) return '';
      const total = sources.length;
      const safeId = 'src_' + String(rawItemId || Math.random()).replace(/[^a-zA-Z0-9_-]/g, '_');

      function getSourceMeta(s) {
        const p = (s.platform || s.source_name || '').toLowerCase();
        const u = s.url || '#';
        let icon = '📄';
        let label = s.source_name || (currentLang === 'KO' ? '원문' : 'Source');
        let badgeCls = 'bg-surface-subtle text-ink-secondary hover:text-ink-primary border-surface-border';

        if (p.includes('hacker news') || u.includes('ycombinator')) {
          icon = '🔥';
          label = currentLang === 'KO' ? 'HN 토론' : 'HN';
          badgeCls = 'bg-orange-50 text-orange-800 hover:text-orange-950 border-orange-200';
        } else if (p.includes('geeknews') || u.includes('hada.io')) {
          icon = '💬';
          label = currentLang === 'KO' ? '긱뉴스' : 'GeekNews';
          badgeCls = 'bg-indigo-50 text-indigo-800 hover:text-indigo-950 border-indigo-200';
        } else if (p.includes('reddit')) {
          icon = '🤖';
          label = currentLang === 'KO' ? '레딧' : 'Reddit';
          badgeCls = 'bg-red-50 text-red-800 hover:text-red-950 border-red-200';
        } else if (p.includes('github')) {
          icon = '🐙';
          label = 'GitHub';
          badgeCls = 'bg-slate-100 text-slate-800 hover:text-slate-950 border-slate-300';
        } else if (p.includes('hugging')) {
          icon = '🤗';
          label = 'HuggingFace';
          badgeCls = 'bg-amber-50 text-amber-900 hover:text-amber-950 border-amber-200';
        } else if (p.includes('arxiv')) {
          icon = '📑';
          label = 'ArXiv';
          badgeCls = 'bg-rose-50 text-rose-900 hover:text-rose-950 border-rose-200';
        } else if (p.includes('twitter') || p.includes(' x') || u.includes('x.com') || u.includes('twitter.com')) {
          icon = '𝕏';
          label = 'X (트위터)';
          badgeCls = 'bg-zinc-100 text-zinc-800 hover:text-zinc-950 border-zinc-300';
        }

        return { icon, label, badgeCls, url: u };
      }

      if (total <= 2) {
        let html = `<div class="flex items-center gap-1.5 flex-wrap">`;
        html += `<span class="px-2 py-0.5 rounded-md text-[10px] font-bold bg-amber-50 text-amber-900 border border-amber-200 shrink-0">🔗 ${currentLang === 'KO' ? `출처 ${total}개 묶음` : (currentLang === 'ZH' ? `聚合${total}个来源` : `${total} Sources`)}</span>`;
        sources.forEach(s => {
          const meta = getSourceMeta(s);
          html += `<a href="${meta.url}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded-md ${meta.badgeCls} border text-[11px] font-bold flex items-center gap-1 shrink-0 transition shadow-xs">${meta.icon} ${meta.label} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>`;
        });
        html += `</div>`;
        return html;
      }

      // 🌟 Scalable Multi-Source UX: Top 2 visible + '+N개 더보기' floating dropdown popover
      const primarySources = sources.slice(0, 2);
      const remainingSources = sources.slice(2);

      let html = `<div class="flex items-center gap-1.5 flex-wrap relative">`;
      html += `<span class="px-2 py-0.5 rounded-md text-[10px] font-bold bg-amber-50 text-amber-900 border border-amber-200 shrink-0">🔗 ${currentLang === 'KO' ? `출처 ${total}개 묶음` : (currentLang === 'ZH' ? `聚合${total}个来源` : `${total} Sources`)}</span>`;
      primarySources.forEach(s => {
        const meta = getSourceMeta(s);
        html += `<a href="${meta.url}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded-md ${meta.badgeCls} border text-[11px] font-bold flex items-center gap-1 shrink-0 transition shadow-xs">${meta.icon} ${meta.label} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>`;
      });

      html += `
        <div class="relative inline-block src-dropdown-container">
          <button type="button" onclick="toggleSourcePopover(event, '${safeId}')" class="px-2 py-1 rounded-md bg-amber-100 hover:bg-amber-200 text-amber-950 border border-amber-300 text-[11px] font-bold flex items-center gap-1 shrink-0 transition cursor-pointer shadow-xs" title="전체 교차 출처 보기">
            <span>+${remainingSources.length}${currentLang === 'KO' ? '개 더보기' : (currentLang === 'ZH' ? '个更多' : ' more')}</span>
            <i data-lucide="chevron-down" class="w-3 h-3"></i>
          </button>
          <div id="srcMenu_${safeId}" class="hidden absolute z-50 mb-1.5 w-64 max-w-[calc(100vw-2.5rem)] min-w-[220px] bg-white rounded-xl shadow-2xl border border-surface-border p-2.5 text-xs flex flex-col gap-1.5">
            <div class="text-[10px] font-mono font-bold text-ink-muted px-1.5 pb-1 border-b border-surface-border flex items-center justify-between">
              <span>🔗 ${currentLang === 'KO' ? `전체 교차 출처 (${total}개)` : (currentLang === 'ZH' ? `全部聚合来源 (${total}个)` : `All Sources (${total})`)}</span>
              <span class="text-indigo-600 text-[9px] font-semibold">${currentLang === 'KO' ? '원문 이동' : (currentLang === 'ZH' ? '直达原文' : 'Open')} &nearr;</span>
            </div>
            <div class="max-h-48 overflow-y-auto space-y-1 divide-y divide-surface-border/40">
              ${sources.map(s => {
                const meta = getSourceMeta(s);
                return `
                  <a href="${meta.url}" target="_blank" rel="noopener noreferrer" class="flex items-center justify-between px-2 py-1.5 rounded-lg hover:bg-surface-subtle transition group text-xs text-ink-primary pt-1">
                    <span class="flex items-center gap-1.5 truncate">
                      <span class="shrink-0">${meta.icon}</span>
                      <span class="font-bold group-hover:text-indigo-600 truncate">${meta.label}</span>
                    </span>
                    <i data-lucide="external-link" class="w-3 h-3 text-ink-muted group-hover:text-indigo-600 shrink-0 ml-2"></i>
                  </a>
                `;
              }).join('')}
            </div>
          </div>
        </div>
      `;
      html += `</div>`;
      return html;
    }

    function toggleSourcePopover(e, safeId) {
      e.stopPropagation();
      const menu = document.getElementById('srcMenu_' + safeId);
      if (!menu) return;
      const isHidden = menu.classList.contains('hidden');
      document.querySelectorAll('[id^="srcMenu_"]').forEach(el => el.classList.add('hidden'));
      if (isHidden) {
        menu.classList.remove('hidden');
        
        // 🌟 Responsive Dynamic Positioning Engine (Desktop + Mobile)
        const btn = e.currentTarget;
        const btnRect = btn.getBoundingClientRect();
        const vw = window.innerWidth;
        const vh = window.innerHeight;
        const menuWidth = Math.min(260, vw - 32);
        menu.style.width = menuWidth + 'px';
        
        // Horizontal Clamping:
        // If aligning to button left overflows screen right edge, align to button right
        if (btnRect.left + menuWidth > vw - 16) {
          menu.style.left = 'auto';
          menu.style.right = '0px';
        } else {
          menu.style.left = '0px';
          menu.style.right = 'auto';
        }
        
        // Vertical Clamping:
        // If not enough room above button (< 220px) and plenty of room below, open downwards
        if (btnRect.top < 220 && (vh - btnRect.bottom > 180)) {
          menu.style.bottom = 'auto';
          menu.style.top = 'calc(100% + 6px)';
        } else {
          menu.style.top = 'auto';
          menu.style.bottom = 'calc(100% + 6px)';
        }

        if (window.lucide) window.lucide.createIcons();
      }
    }

    document.addEventListener('click', (e) => {
      if (!e.target.closest('.src-dropdown-container')) {
        document.querySelectorAll('[id^="srcMenu_"]').forEach(el => el.classList.add('hidden'));
      }
    });

    function renderNews() {
      const grid = document.getElementById('newsGrid');
      grid.innerHTML = '';
      const t = i18n[currentLang];

      const rawNewsItems = liveNewsData || [];
      const newsItems = rawNewsItems.filter(it => {
        // 🌟 Direct Primary Key Match from Radar
        if (targetSelectedInboxId && it.inbox_id === targetSelectedInboxId) {
          return true;
        }

        // 1. Tier 1 Domain Filter
        if (currentNewsTier1 !== 'ALL') {
          const itemTier1 = it.tier1_category || 'TECH_COMPUTING';
          if (itemTier1 !== currentNewsTier1) return false;
        }

        // 2. Tier 2 Specialization Filter (Under TECH_COMPUTING)
        if (currentNewsTier2 !== 'ALL') {
          const itemTier2 = it.tier2_category || it.category_primary || 'INDUSTRY_TRENDS';
          if (itemTier2 !== currentNewsTier2) return false;
        }

        // 2. Platform Source Filter
        if (currentNewsSource !== 'ALL') {
          const src = (it.source_platform || '').toLowerCase();
          const target = currentNewsSource.toLowerCase();
          if (!src.includes(target)) return false;
        }

        // 3. Search Filter
        if (currentNewsSearch) {
          const q = currentNewsSearch.toLowerCase().trim();
          const haystack = (
            (it.inbox_id || '') + ' ' +
            (it.title || '') + ' ' +
            (it.title_ko || '') + ' ' +
            (it.title_en || '') + ' ' +
            (it.hook || '') + ' ' +
            (it.hook_ko || '') + ' ' +
            (it.description || '') + ' ' +
            (it.source_platform || '') + ' ' +
            (it.category_primary || '') + ' ' +
            (Array.isArray(it.root_keywords) ? it.root_keywords.join(' ') : (it.root_keywords || '')) + ' ' +
            (Array.isArray(it.matched_user_domains) ? it.matched_user_domains.join(' ') : '') + ' ' +
            (it.ai_enrichment?.summary_ko || '')
          ).toLowerCase();

          const tokens = q.split(/\\s+/).filter(t => t.length > 0);
          const matches = haystack.includes(q) || (tokens.length > 0 && tokens.every(t => haystack.includes(t)));
          if (!matches) return false;
        }

        return true;
      });

      // 🌟 Precision DateTime Sorting (Unified)
      sortCollection(newsItems, currentNewsSort);

      const totalPages = Math.ceil(newsItems.length / PAGE_SIZE) || 1;
      if (currentNewsPage > totalPages) currentNewsPage = totalPages;
      if (currentNewsPage < 1) currentNewsPage = 1;

      renderPagination('newsPagination', currentNewsPage, totalPages, 'changeNewsPage');

      if (newsItems.length === 0) {
        grid.innerHTML = `<div class="col-span-full py-16 text-center text-ink-muted font-medium">${currentLang === 'KO' ? '해당 플랫폼의 수집 AI 뉴스가 없습니다.' : (currentLang === 'ZH' ? '暂无该平台的 AI 资讯。' : 'No AI news articles available for this source.')}</div>`;
        return;
      }

      const pagedNews = newsItems.slice((currentNewsPage - 1) * PAGE_SIZE, currentNewsPage * PAGE_SIZE);
      const fragment = document.createDocumentFragment();
      pagedNews.forEach(it => {
        const card = document.createElement('div');
        card.className = 'executive-card p-4 sm:p-5 flex flex-col justify-between space-y-4';

        const ai = it.ai_enrichment;
        const { displayTitle, displayHook, displayDesc, displayTakeaways } = getLocalizedContent(it, currentLang);
        const showDesc = (!displayTakeaways || displayTakeaways.length === 0) && displayDesc;

        const isHn = (it.source_platform || '').includes('Hacker News') || (it.source_url || '').includes('news.ycombinator.com');
        const isGn = (it.source_platform || '').includes('GeekNews') || (it.source_url || '').includes('hada.io');
        const hnUrl = it.hn_url || ((it.source_url || '').includes('news.ycombinator.com') ? it.source_url : null);
        const gnUrl = isGn ? (it.hn_url || it.source_url) : null;
        const articleUrl = it.article_url || (it.source_url !== (hnUrl || gnUrl) ? it.source_url : null);

        let linksHtml = '';
        if (it.sources && it.sources.length > 1) {
          linksHtml = buildMultiSourceCluster(it.sources, it.inbox_id || it.id);
        } else if (isHn) {
          if (articleUrl && articleUrl !== hnUrl) {
            linksHtml += `<a href="${articleUrl}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded-md bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border text-[11px] font-medium flex items-center gap-1 shrink-0">📄 ${currentLang === 'KO' ? '기사 원문' : (currentLang === 'ZH' ? '文章原文' : 'Article')} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>`;
          }
          if (hnUrl) {
            linksHtml += `<a href="${hnUrl}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded-md bg-orange-50 text-orange-800 hover:text-orange-950 border border-orange-200 text-[11px] font-bold flex items-center gap-1 shrink-0">🔥 ${currentLang === 'KO' ? 'HN 토론' : (currentLang === 'ZH' ? 'HN 讨论' : 'HN Thread')} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>`;
          }
        } else if (isGn) {
          if (articleUrl && articleUrl !== gnUrl) {
            linksHtml += `<a href="${articleUrl}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded-md bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border text-[11px] font-medium flex items-center gap-1 shrink-0">📄 ${currentLang === 'KO' ? '기사 원문' : (currentLang === 'ZH' ? '文章原文' : 'Article')} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>`;
          }
          if (gnUrl) {
            linksHtml += `<a href="${gnUrl}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded-md bg-indigo-50 text-indigo-800 hover:text-indigo-950 border border-indigo-200 text-[11px] font-bold flex items-center gap-1 shrink-0">💬 ${currentLang === 'KO' ? '긱뉴스 토론' : (currentLang === 'ZH' ? '极客新闻' : 'GeekNews')} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>`;
          }
        } else {
          linksHtml = `<a href="${it.source_url}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded-md bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border text-[11px] font-semibold flex items-center gap-1 shrink-0">📄 ${t.newsOriginalLink} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>`;
        }

        let aiBadgeHtml = '';
        let aiSummaryHtml = '';
        const hookHtml = renderHookCallout(displayHook);
        const relatedHtml = renderRelatedDossierButton(it.related_dossier, currentLang);

        const tier1Map = {
          'SCIENCE_RESEARCH': { label: currentLang === 'KO' ? '🚀 과학·우주' : (currentLang === 'ZH' ? '🚀 科学与航天' : '🚀 Science & Research'), cls: 'bg-teal-50 text-teal-900 border-teal-200' },
          'ECONOMY_FINANCE': { label: currentLang === 'KO' ? '🏦 경제·금융' : (currentLang === 'ZH' ? '🏦 经济与金融' : '🏦 Economy & Finance'), cls: 'bg-emerald-50 text-emerald-900 border-emerald-200' },
          'LAW_CRIME_JUSTICE': { label: currentLang === 'KO' ? '⚖️ 사회·법률' : (currentLang === 'ZH' ? '⚖️ 法律与社会' : '⚖️ Law & Society'), cls: 'bg-rose-50 text-rose-900 border-rose-200' },
          'POLITICS_POLICY': { label: currentLang === 'KO' ? '🏛️ 정치·정책' : (currentLang === 'ZH' ? '🏛️ 政治与政策' : '🏛️ Politics & Policy'), cls: 'bg-amber-50 text-amber-950 border-amber-300' },
          'CULTURE_HUMANITIES': { label: currentLang === 'KO' ? '🌿 문화·인문' : (currentLang === 'ZH' ? '🌿 文化与人文' : '🌿 Culture & Arts'), cls: 'bg-purple-50 text-purple-900 border-purple-200' }
        };
        const catMap = {
          'INFERENCE_OPT': { label: currentLang === 'KO' ? '⚡ 추론·서빙 최적화' : (currentLang === 'ZH' ? '⚡ 推理服务优化' : '⚡ Inference & Opt'), cls: 'bg-amber-50 text-amber-900 border-amber-200' },
          'AGENTS_DEVTOOLS': { label: currentLang === 'KO' ? '🛠️ 에이전트·개발도구' : (currentLang === 'ZH' ? '🛠️ 智能体与工具' : '🛠️ Agents & DevTools'), cls: 'bg-blue-50 text-blue-900 border-blue-200' },
          'MULTIMODAL_AI': { label: currentLang === 'KO' ? '🎨 멀티모달·영상/음성' : (currentLang === 'ZH' ? '🎨 多模态与视听' : '🎨 Multimodal & GenAI'), cls: 'bg-purple-50 text-purple-900 border-purple-200' },
          'FOUNDATION_MODELS': { label: currentLang === 'KO' ? '🤖 파운데이션·가중치' : (currentLang === 'ZH' ? '🤖 基础模型与权重' : '🤖 Foundation Models'), cls: 'bg-emerald-50 text-emerald-900 border-emerald-200' },
          'INFRA_RAG_SECURITY': { label: currentLang === 'KO' ? '🛡️ 인프라·RAG·보안' : (currentLang === 'ZH' ? '🛡️ 基础设施与安全' : '🛡️ Infra, RAG & Safety'), cls: 'bg-rose-50 text-rose-900 border-rose-200' },
          'DEEP_SCIENCE_SPACE': { label: currentLang === 'KO' ? '🚀 우주·신소재·과학' : (currentLang === 'ZH' ? '🚀 深科技与空天科学' : '🚀 Deep Science & Space'), cls: 'bg-teal-50 text-teal-900 border-teal-200' },
          'MACRO_GLOBAL_BIZ': { label: currentLang === 'KO' ? '🏦 산업·거시경제' : (currentLang === 'ZH' ? '🏦 产业与宏观经济' : '🏦 Macro & Global Biz'), cls: 'bg-amber-50 text-amber-950 border-amber-300' },
          'INDUSTRY_TRENDS': { label: currentLang === 'KO' ? '🌐 일반 테크·SW' : (currentLang === 'ZH' ? '🌐 通用科技与软件' : '🌐 General Tech & SW'), cls: 'bg-slate-100 text-slate-800 border-slate-200' }
        };
        const catInfo = (it.tier1_category && tier1Map[it.tier1_category]) ? tier1Map[it.tier1_category] : (catMap[it.category_primary] || catMap['INDUSTRY_TRENDS']);

        if (ai) {
          const tagBg = ai.worth_investigating === 'HIGH' ? 'bg-orange-50 text-orange-950 border-orange-200' : 'bg-indigo-50 text-indigo-950 border-indigo-200';
          const typeLabels = {
            'MODEL': currentLang === 'KO' ? '🤖 모델 발표' : (currentLang === 'ZH' ? '🤖 模型发布' : '🤖 Model'),
            'AGENT': currentLang === 'KO' ? '🦾 에이전트' : (currentLang === 'ZH' ? '🦾 智能体' : '🦾 Agent'),
            'TECH': currentLang === 'KO' ? '⚡ 신기술/최적화' : (currentLang === 'ZH' ? '⚡ 新技术/架构' : '⚡ Tech/Arch'),
            'NEWS': currentLang === 'KO' ? '📰 업계 동향' : (currentLang === 'ZH' ? '📰 行业资讯' : '📰 News')
          };
          const typeBadge = typeLabels[ai.type_classification] || (currentLang === 'KO' ? '💡 기술' : '💡 Tech');

          aiBadgeHtml = `
            <div class="flex items-center gap-1.5 flex-wrap my-1">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${tagBg}">
                ${ai.recommended_tag || '💡 추천'} ★${ai.score || ai.worth_score || '4.0'}
              </span>
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-900 border border-indigo-200">
                ${typeBadge}
              </span>
              ${ai.programming_lang && ai.programming_lang !== 'General' ? `<span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-50 text-amber-900 border border-amber-200">💻 ${ai.programming_lang}</span>` : ''}
              ${ai.source_lang ? `<span class="px-1.5 py-0.2 rounded text-[9px] font-mono font-semibold bg-surface-subtle text-ink-muted border border-surface-border">${ai.source_lang}</span>` : ''}
            </div>
          `;

          aiSummaryHtml = renderAiTakeaways(displayTakeaways, currentLang);
        }

        const footerHtml = renderCardStandardFooter(it, currentLang, linksHtml);

        card.innerHTML = `
          <div class="space-y-2.5">
            <div class="flex items-center justify-between text-xs font-mono">
              <div class="flex items-center gap-1.5 flex-wrap">
                <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${catInfo.cls}">
                  ${catInfo.label}
                </span>
                <span class="px-2 py-0.5 rounded bg-surface-subtle text-ink-primary font-bold border border-surface-border text-[10px]">
                  ${it.source_platform || 'Tech News'}
                </span>
              </div>
              <span class="text-ink-muted text-[11px] font-mono">${it.viral_metric || ''}</span>
            </div>

            ${aiBadgeHtml}

            <h3 class="font-bold text-sm text-ink-primary hover:text-indigo-600 transition leading-snug break-words">
              ${displayTitle}
            </h3>

            ${hookHtml}

            ${showDesc ? `<p class="text-xs text-ink-secondary leading-relaxed line-clamp-3">${displayDesc}</p>` : ''}

            ${aiSummaryHtml}
            ${relatedHtml}
          </div>

          ${footerHtml}
        `;
        fragment.appendChild(card);
      });
      grid.appendChild(fragment);

      if (window.lucide) window.lucide.createIcons({ root: grid });
    }

    // ================= AI MODELS REGISTRY VIEW =================
    let currentModelsFamily = 'ALL';
    let currentModelsModality = 'ALL';
    let currentModelsArtifact = 'ALL';
    let currentModelsSort = 'date-audit-desc';
    let modelsSearchQuery = '';

    function setModelsSort(sort) {
      currentModelsPage = 1;
      currentModelsSort = sort;
      renderModels();
    }

    function setModelsArtifactFilter(art) {
      currentModelsPage = 1;
      currentModelsArtifact = art;
      document.querySelectorAll('.model-art-pill').forEach(btn => {
        if (btn.getAttribute('data-art') === art) {
          btn.className = 'model-art-pill active px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap';
        } else {
          btn.className = 'model-art-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }
      });
      renderModels();
    }

    function setModelsModalityFilter(mod) {
      currentModelsPage = 1;
      currentModelsModality = mod;
      document.querySelectorAll('.model-mod-pill').forEach(btn => {
        if (btn.dataset.mod === mod) {
          btn.className = 'model-mod-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shrink-0 whitespace-nowrap';
        } else {
          btn.className = 'model-mod-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }
      });
      renderModels();
    }

    function setModelsFamilyFilter(fam) {
      currentModelsPage = 1;
      currentModelsFamily = fam;
      document.querySelectorAll('.model-fam-pill').forEach(btn => {
        if (btn.getAttribute('data-fam') === fam) {
          btn.className = 'model-fam-pill active px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap';
        } else {
          btn.className = 'model-fam-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }
      });
      renderModels();
    }

    document.getElementById('modelsSearchInput')?.addEventListener('input', (e) => {
      targetSelectedInboxId = '';
      currentModelsPage = 1;
      modelsSearchQuery = e.target.value;
      renderModels();
    });

    function renderModels() {
      const grid = document.getElementById('modelsGrid');
      if (!grid) return;
      grid.innerHTML = '';

      const filtered = liveModelsData.filter(item => {
        // 🚨 STRICT POLICY: 번역/요약/정리가 100% 완료된 아이템만 분류 노출 (미번역 아이템은 절대 분류 금지)
        const hasAi = !!(item.ai_enrichment && (item.multilingual || (item.ai_enrichment && item.ai_enrichment.multilingual)));
        if (!hasAi) return false;

        // 🌟 Direct Primary Key Match from Radar
        if (targetSelectedInboxId && item.inbox_id === targetSelectedInboxId) {
          return true;
        }

        let matchesMod = true;
        if (currentModelsModality !== 'ALL') {
          const itemMod = (item.task_modality || '').toLowerCase();
          matchesMod = itemMod === currentModelsModality.toLowerCase();
        }

        const fam = (item.model_family || '').toLowerCase();
        let matchesFam = true;
        if (currentModelsFamily === 'ALL') {
          matchesFam = true;
        } else if (currentModelsFamily === 'Standalone') {
          matchesFam = fam.includes('standalone') || fam.includes('독립') || !fam;
        } else if (currentModelsFamily === 'Audio / Speech') {
          matchesFam = fam.includes('audio') || fam.includes('speech') || fam.includes('tts') || fam.includes('whisper');
        } else {
          matchesFam = fam.includes(currentModelsFamily.toLowerCase());
        }

        let matchesArt = true;
        if (currentModelsArtifact !== 'ALL') {
          const itemArt = item.artifact_type || 'WEIGHTS';
          matchesArt = itemArt === currentModelsArtifact;
        }

        if (!modelsSearchQuery) {
          return matchesMod && matchesFam && matchesArt;
        }

        const q = modelsSearchQuery.toLowerCase().trim();
        const searchable = (
          (item.inbox_id || '') + ' ' +
          (item.title || '') + ' ' +
          (item.title_ko || '') + ' ' +
          (item.title_en || '') + ' ' +
          (item.title_zh || '') + ' ' +
          (item.description || '') + ' ' +
          fam + ' ' +
          (item.task_modality || '') + ' ' +
          (item.artifact_type || '') + ' ' +
          (item.parameter_size || '') + ' ' +
          (item.ai_enrichment?.summary_ko || '') + ' ' +
          (item.ai_enrichment?.hook_ko || '')
        ).toLowerCase();

        const tokens = q.split(/\\s+/).filter(t => t.length > 0);
        const matchesSearch = searchable.includes(q) || (tokens.length > 0 && tokens.every(t => searchable.includes(t)));
        return matchesMod && matchesFam && matchesArt && matchesSearch;
      });

      // 🌟 Precision DateTime Sorting (Unified)
      sortCollection(filtered, currentModelsSort);

      const countEl = document.getElementById('modelsFilteredCount');
      if (countEl) countEl.innerText = currentLang === 'KO' ? `${filtered.length}개 모델 표출` : (currentLang === 'ZH' ? `显示 ${filtered.length} 个模型` : `Showing ${filtered.length} models`);

      const totalPages = Math.ceil(filtered.length / PAGE_SIZE) || 1;
      if (currentModelsPage > totalPages) currentModelsPage = totalPages;
      if (currentModelsPage < 1) currentModelsPage = 1;

      renderPagination('modelsPagination', currentModelsPage, totalPages, 'changeModelsPage');

      if (filtered.length === 0) {
        grid.innerHTML = `<div class="col-span-full py-16 text-center text-ink-muted font-medium">${currentLang === 'KO' ? '일치하는 AI 모델이 없습니다.' : (currentLang === 'ZH' ? '暂无匹配的 AI 模型。' : 'No matching AI models.')}</div>`;
        return;
      }

      const pagedModels = filtered.slice((currentModelsPage - 1) * PAGE_SIZE, currentModelsPage * PAGE_SIZE);
      const fragment = document.createDocumentFragment();
      pagedModels.forEach(it => {
        const { displayTitle, displayHook, displayDesc } = getLocalizedContent(it, currentLang);

        const card = document.createElement('div');
        card.className = 'bg-white rounded-2xl p-4 sm:p-5 border border-surface-border hover:border-indigo-400 hover:shadow-md transition flex flex-col justify-between space-y-4';

        const artType = it.artifact_type || (it.source_platform?.includes('Spaces') ? 'WEB_SERVICE' : 'WEIGHTS');
        const artBadgeMap = {
          'WEIGHTS': {
            label: currentLang === 'KO' ? '🤖 모델 가중치' : (currentLang === 'ZH' ? '🤖 模型权重' : '🤖 Model Weights'),
            cls: 'bg-indigo-50 text-indigo-800 border-indigo-200',
            btn: currentLang === 'KO' ? '📥 허브 다운로드' : (currentLang === 'ZH' ? '📥 Hub 下载' : '📥 Hub Download')
          },
          'WEB_SERVICE': {
            label: currentLang === 'KO' ? '🌐 Spaces 데모' : (currentLang === 'ZH' ? '🌐 Spaces 演示' : '🌐 Spaces Demo'),
            cls: 'bg-emerald-50 text-emerald-800 border-emerald-200',
            btn: currentLang === 'KO' ? '🚀 데모 / Spaces 체험' : (currentLang === 'ZH' ? '🚀 在线 Demo 体验' : '🚀 Try Live Spaces Demo')
          },
          'FINETUNE': {
            label: currentLang === 'KO' ? '🎯 특화 파인튜닝' : (currentLang === 'ZH' ? '🎯 微调定制模型' : '🎯 Finetuned Model'),
            cls: 'bg-amber-50 text-amber-800 border-amber-200',
            btn: currentLang === 'KO' ? '🎯 파인튜닝 모델 보기' : (currentLang === 'ZH' ? '🎯 查看微调模型' : '🎯 View Finetuned Model')
          }
        };
        const artMeta = artBadgeMap[artType] || artBadgeMap['WEIGHTS'];
        const artBadge = `<span class="px-2 py-0.5 rounded-md font-bold border text-[10px] font-mono ${artMeta.cls}">${artMeta.label}</span>`;

        const famBadge = it.model_family ? `
          <span class="px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 font-bold border border-indigo-200 text-[11px] font-mono">
            🤖 ${it.model_family}
          </span>
        ` : '';

        let modBadge = '';
        if (it.task_modality) {
          const m = it.task_modality.toLowerCase();
          let icon = '🎯';
          let label = it.task_modality;
          if (m.includes('video')) { icon = '🎬'; label = 'Video'; }
          else if (m.includes('image-text') || m.includes('vision') || m.includes('vlm')) { icon = '👁️'; label = 'VLM'; }
          else if (m.includes('image')) { icon = '🎨'; label = 'Image'; }
          else if (m.includes('speech') || m.includes('audio')) { icon = '🎙️'; label = 'Audio/TTS'; }
          else if (m.includes('text')) { icon = '📝'; label = 'Text'; }
          modBadge = `<span class="px-2 py-0.5 rounded-md bg-purple-50 text-purple-700 font-bold border border-purple-200 text-[10px] font-mono">${icon} ${label}</span>`;
        }

        let paramBadge = '';
        if (it.parameter_size) {
          paramBadge = `<span class="px-1.5 py-0.5 rounded-md bg-amber-50 text-amber-800 font-bold border border-amber-200 text-[10px] font-mono shrink-0">⚡ ${it.parameter_size}</span>`;
        }

        let formatBadges = '';
        if (Array.isArray(it.detected_formats) && it.detected_formats.length > 0) {
          formatBadges = it.detected_formats.slice(0, 3).map(fmt => 
            `<span class="px-1.5 py-0.2 rounded bg-surface-subtle text-ink-muted text-[9px] font-mono border border-surface-border uppercase">${fmt}</span>`
          ).join(' ');
        }

        const hookHtml = renderHookCallout(displayHook);
        const relatedHtml = renderRelatedDossierButton(it.related_dossier, currentLang);

        const actionBtn = `
          <a href="${it.source_url}" target="_blank" rel="noopener noreferrer" class="px-2.5 py-1 rounded-lg bg-surface-subtle hover:bg-ink-primary hover:text-white text-ink-primary font-bold transition text-xs flex items-center gap-1 shrink-0">
            <span>${artMeta.btn}</span> <i data-lucide="external-link" class="w-3 h-3"></i>
          </a>
        `;
        const footerHtml = renderCardStandardFooter(it, currentLang, actionBtn);

        card.innerHTML = `
          <div class="space-y-3">
            <div class="flex items-center justify-between text-xs font-mono">
              <div class="flex items-center gap-1.5 flex-wrap">
                ${artBadge}
                ${famBadge}
                ${modBadge}
                ${paramBadge}
              </div>
              <span class="text-ink-muted text-[11px] shrink-0">${it.source_platform || 'Hugging Face'}</span>
            </div>

            <h3 class="font-bold text-sm text-ink-primary hover:text-indigo-600 transition leading-snug">
              ${displayTitle}
            </h3>

            ${hookHtml}

            ${displayDesc ? `<p class="text-xs text-ink-secondary leading-relaxed line-clamp-3">${displayDesc}</p>` : ''}

            ${formatBadges ? `<div class="flex items-center gap-1 flex-wrap pt-1">${formatBadges}</div>` : ''}

            ${relatedHtml}
          </div>

          ${footerHtml}
        `;

        fragment.appendChild(card);
      });
      grid.appendChild(fragment);

      if (window.lucide) window.lucide.createIcons({ root: grid });
    }

    // ================= STANDARDIZED CROSS-PLATFORM VIRAL NORMALIZER =================
    function calculateStandardizedViralScore(item) {
      const src = item.source_platform || '';
      const metric = item.viral_metric || item.description || '';
      let rawNum = 0;

      const nums = (metric.replace(/,/g, '').match(/\d+/) || []);
      if (nums.length > 0) rawNum = parseInt(nums[0], 10);

      let normScore = 25; // Base fallback score

      if (src.includes('GitHub')) {
        // GitHub: 5000 stars = 100 pts, 500 stars = ~73 pts
        normScore = rawNum > 0 ? (Math.log10(rawNum + 1) / Math.log10(5000)) * 100 : 25;
      } else if (src.includes('Hacker News')) {
        // Hacker News: 800 pts = 100 pts, 150 pts = ~75 pts
        normScore = rawNum > 0 ? (Math.log10(rawNum + 1) / Math.log10(800)) * 100 : 30;
      } else if (src.includes('Hugging Face')) {
        // Hugging Face: 300 likes = 100 pts, 50 likes = ~68 pts
        normScore = rawNum > 0 ? (Math.log10(rawNum + 1) / Math.log10(300)) * 100 : 30;
      } else if (src.includes('GeekNews')) {
        // GeekNews: 100 pts = 100 pts, 20 pts = ~66 pts
        normScore = rawNum > 0 ? (Math.log10(rawNum + 1) / Math.log10(100)) * 100 : 35;
      } else if (src.includes('ArXiv')) {
        normScore = 55; // Peer-reviewed academic baseline
      }

      normScore = Math.max(5, Math.min(100, Math.round(normScore)));

      // Blend AI enrichment rating if available (70% viral, 30% AI rating)
      const aiScore = item.ai_enrichment ? item.ai_enrichment.score : null;
      if (aiScore && aiScore > 0) {
        normScore = Math.round((normScore * 0.7) + ((aiScore * 20) * 0.3));
      }

      return normScore;
    }

    let currentInboxSort = 'date-audit-desc';

    function setInboxSort(val) {
      currentInboxPage = 1;
      currentInboxSort = val;
      renderInbox();
    }

    let currentInboxLang = 'ALL';
    let currentInboxType = 'ALL';
    let currentInboxTech = 'ALL';

    function setInboxLangFilter(lang) {
      currentInboxPage = 1;
      currentInboxLang = lang;
      document.querySelectorAll('.inbox-filter-pill').forEach(btn => {
        if (btn.dataset.langVal === lang) {
          btn.className = 'inbox-filter-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shrink-0 whitespace-nowrap';
        } else {
          btn.className = 'inbox-filter-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }
      });
      renderInbox();
    }

    function setInboxTypeFilter(typeVal) {
      currentInboxPage = 1;
      currentInboxType = typeVal;
      document.querySelectorAll('.inbox-type-pill').forEach(btn => {
        if (btn.dataset.typeVal === typeVal) {
          btn.className = 'inbox-type-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shrink-0 whitespace-nowrap';
        } else {
          btn.className = 'inbox-type-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }
      });
      renderInbox();
    }

    function setInboxTechFilter(tech) {
      currentInboxPage = 1;
      currentInboxTech = tech;
      document.querySelectorAll('.inbox-tech-pill').forEach(btn => {
        if (btn.dataset.techVal === tech) {
          btn.className = 'inbox-tech-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shrink-0 whitespace-nowrap';
        } else {
          btn.className = 'inbox-tech-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }
      });
      renderInbox();
    }

    function setInboxSourceFilter(src) {
      currentInboxPage = 1;
      currentInboxSource = src;
      const sel = document.getElementById('inboxSourceSelect');
      if (sel && sel.value !== src) sel.value = src;

      document.querySelectorAll('.inbox-src-pill').forEach(btn => {
        if (btn.dataset.srcVal === src) {
          btn.className = 'inbox-src-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shrink-0 whitespace-nowrap';
        } else {
          btn.className = 'inbox-src-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }
      });
      renderInbox();
    }

    document.getElementById('inboxSearchInput').addEventListener('input', (e) => {
      currentInboxPage = 1;
      inboxSearchQuery = e.target.value;
      renderInbox();
    });

    // ================= GITHUB ACTIONS CRON PIPELINE TELEMETRY =================
    const cronScheduleConfig = [
      { id: 1, hour: 0, min: 17, slotKo: '1회차 (00:17)', slotZh: '第1轮 (00:17)', slotEn: 'Session 1 (00:17)', nameKo: '심야 글로벌 릴리스', nameZh: '深夜全球发布', nameEn: 'Midnight Global Release', estSec: 545, runId: '34133531110', actualDur: '9분 05초' },
      { id: 2, hour: 6, min: 17, slotKo: '2회차 (06:17)', slotZh: '第2轮 (06:17)', slotEn: 'Session 2 (06:17)', nameKo: '모닝 브리핑', nameZh: '早间简报', nameEn: 'Morning Briefing', estSec: 362, runId: '34096402553', actualDur: '6분 02초' },
      { id: 3, hour: 12, min: 17, slotKo: '3회차 (12:17)', slotZh: '第3轮 (12:17)', slotEn: 'Session 3 (12:17)', nameKo: '정오 레이더', nameZh: '正午雷达', nameEn: 'Noon Radar', estSec: 456, runId: '34064244121', actualDur: '7분 36초' },
      { id: 4, hour: 18, min: 17, slotKo: '4회차 (18:17)', slotZh: '第4轮 (18:17)', slotEn: 'Session 4 (18:17)', nameKo: '저녁 라운드업', nameZh: '晚间汇总', nameEn: 'Evening Roundup', estSec: 694, runId: '34048453203', actualDur: '11분 34초' }
    ];

    function updateCronCountdown() {
      if (currentView !== 'inbox') return;
      const countdownEl = document.getElementById('pipelineCountdownValue');
      const slotsContainer = document.getElementById('pipelineSlotsContainer');
      const tbody = document.getElementById('pipelineRecentRunsTbody');
      if (!countdownEl || !slotsContainer) return;

      if (Math.floor(Date.now() / 1000) % 30 === 0) {
        checkLiveActionsRuns();
      }

      const tLang = currentLang || 'ko';
      const aData = typeof actionsTelemetryData !== 'undefined' ? actionsTelemetryData : {};

      // 1. Quota Progress & Analytics
      const usedMin = aData.monthly_used_minutes || 82.8;
      const remMin = aData.monthly_remaining_minutes || 1917.2;
      const usagePct = aData.monthly_usage_percent || 4.1;

      const usedEl = document.getElementById('quotaUsedMin');
      const remEl = document.getElementById('quotaRemMin');
      const progEl = document.getElementById('quotaProgressBar');
      if (usedEl) usedEl.innerText = `${usedMin}분`;
      if (remEl) remEl.innerText = `${remMin}분 (${100 - usagePct}%)`;
      if (progEl) progEl.style.width = `${Math.min(100, Math.max(2, usagePct))}%`;

      // 2. Next Run Countdown
      const nowKst = getDynamicKstDate();
      const curHour = nowKst.getHours();
      const curMin = nowKst.getMinutes();
      const curSec = nowKst.getSeconds();
      const curTotalSec = curHour * 3600 + curMin * 60 + curSec;

      let nextSlot = null;
      let diffSec = 0;

      for (let s of cronScheduleConfig) {
        const sTotalSec = s.hour * 3600 + s.min * 60;
        if (sTotalSec > curTotalSec) {
          nextSlot = s;
          diffSec = sTotalSec - curTotalSec;
          break;
        }
      }

      if (!nextSlot) {
        nextSlot = cronScheduleConfig[0];
        const eodSec = 24 * 3600 - curTotalSec;
        diffSec = eodSec + (nextSlot.hour * 3600 + nextSlot.min * 60);
      }

      const remH = Math.floor(diffSec / 3600);
      const remM = Math.floor((diffSec % 3600) / 60);
      const remS = diffSec % 60;
      const pad = (n) => String(n).padStart(2, '0');

      const slotName = tLang === 'zh' ? nextSlot.slotZh : (tLang === 'en' ? nextSlot.slotEn : nextSlot.slotKo);
      countdownEl.innerText = `${pad(remH)}:${pad(remM)}:${pad(remS)} (${slotName})`;

      // 3. Render 4 Quarterly Session Telemetry Cards
      const tData = typeof timeline24hData !== 'undefined' ? timeline24hData : [];
      let cardsHtml = '';

      cronScheduleConfig.forEach((s, idx) => {
        const sTotalSec = s.hour * 3600 + s.min * 60;
        const isPast = curTotalSec >= sTotalSec + (s.estSec || 360);
        const isActive = curTotalSec >= sTotalSec && curTotalSec < sTotalSec + (s.estSec || 360);
        const isPending = curTotalSec < sTotalSec;

        const sessionTitle = tLang === 'zh' ? s.slotZh : (tLang === 'en' ? s.slotEn : s.slotKo);
        const sessionSub = tLang === 'zh' ? s.nameZh : (tLang === 'en' ? s.nameEn : s.nameKo);

        const slotKeys = ['00:00', '06:00', '12:00', '18:00'];
        const slotKey = slotKeys[idx] || '00:00';
        const sLog = (aData.slot_logs && aData.slot_logs[slotKey]) ? aData.slot_logs[slotKey] : null;

        const tlMatch = tData.find(d => d.hour === (idx * 6));
        const itemCount = (sLog && sLog.is_today && sLog.items_collected !== null && sLog.items_collected !== undefined)
          ? sLog.items_collected
          : (tlMatch ? (tlMatch.inbox_count || 0) : 0);

        let statusBadge = '';
        let timeInfo = '';
        let cardBorder = 'border-surface-border';
        let cardBg = 'bg-slate-50/50';

        const isRunToday = sLog && sLog.is_today;
        const isRunSuccess = isRunToday && (sLog.status === 'SUCCESS' || sLog.status === 'completed');
        const isRunActive = (sLog && sLog.status === 'in_progress') || isActive;

        if (isRunSuccess) {
          const actualDuration = sLog.actual_duration || (s.actualDur || '-');
          const errCount = (sLog && typeof sLog.error_count !== 'undefined') ? sLog.error_count : 0;

          cardBorder = 'border-emerald-200';
          cardBg = 'bg-emerald-50/30';
          statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1"><i data-lucide="check-circle" class="w-3 h-3 text-emerald-600"></i>${tLang === 'zh' ? '已完成' : (tLang === 'en' ? 'Completed' : '수집 완료')}</span>`;
          timeInfo = `<span>${tLang === 'zh' ? '实测耗时' : (tLang === 'en' ? 'Duration' : '실측 소요')}: <b class="text-ink-primary font-bold">${actualDuration}</b> · ${errCount} ${tLang === 'zh' ? '错误' : (tLang === 'en' ? 'errors' : '에러')}</span>`;
        } else if (isRunActive) {
          cardBorder = 'border-indigo-400 ring-2 ring-indigo-200';
          cardBg = 'bg-indigo-50/70';
          statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-600 text-white flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-white animate-ping"></span>${tLang === 'zh' ? '运行中' : (tLang === 'en' ? 'Running' : '수집 진행 중')}</span>`;
          timeInfo = `<span class="text-indigo-700 font-bold">${tLang === 'zh' ? '正在执行' : (tLang === 'en' ? 'Ingesting live...' : '실시간 파이프라인 가동')}</span>`;
        } else if (isPast && !isRunToday) {
          cardBorder = 'border-amber-300 ring-1 ring-amber-200';
          cardBg = 'bg-amber-50/40';
          statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300 flex items-center gap-1"><i data-lucide="clock" class="w-3 h-3 text-amber-600"></i>${tLang === 'zh' ? '队列等待中' : (tLang === 'en' ? 'Queue Waiting' : '⏳ 수집 큐 대기')}</span>`;
          timeInfo = `<span class="text-amber-700 font-medium">${tLang === 'zh' ? '已过调度时段 · GHA 队列等待中' : (tLang === 'en' ? 'Scheduled time elapsed · Waiting in GHA queue' : '예정 시각 경과 · Actions 큐 대기 중')}</span>`;
        } else {
          const slotDiffSec = sTotalSec - curTotalSec;
          const futH = Math.floor(slotDiffSec / 3600);
          const futM = Math.floor((slotDiffSec % 3600) / 60);
          statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-600 border border-slate-200 flex items-center gap-1"><i data-lucide="clock" class="w-3 h-3 text-slate-500"></i>${tLang === 'zh' ? '等待中' : (tLang === 'en' ? 'Scheduled' : '대기 중')}</span>`;
          timeInfo = `<span>${tLang === 'zh' ? '剩余' : (tLang === 'en' ? 'Remaining' : '남은 시간')}: <b class="text-indigo-600">${futH}h ${futM}m</b> · ${tLang === 'zh' ? '预计约' : (tLang === 'en' ? 'Est. ' : '예상 ')}${Math.round(s.estSec/60)}분</span>`;
        }

        cardsHtml += `
          <div class="p-3.5 rounded-xl border ${cardBorder} ${cardBg} flex flex-col justify-between space-y-2.5 transition">
            <div class="flex items-center justify-between">
              <span class="font-bold text-ink-primary text-xs">${sessionTitle}</span>
              ${statusBadge}
            </div>
            <div class="space-y-1">
              <div class="text-[11px] text-ink-secondary font-medium">${sessionSub}</div>
              <div class="text-xs font-bold text-ink-primary flex items-center justify-between">
                <span>${tLang === 'zh' ? '采集总量' : (tLang === 'en' ? 'Ingested' : '수집량')}:</span>
                <span class="text-indigo-600 font-mono">${itemCount}건</span>
              </div>
            </div>
            <div class="pt-2 border-t border-surface-border/60 text-[10px] text-ink-muted flex items-center justify-between">
              ${timeInfo}
            </div>
          </div>
        `;
      });
      slotsContainer.innerHTML = cardsHtml;

      // 4. Render Recent Run Logs Table
      renderRunsTable();

      if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    let currentRunsTab = 'gha';
    window.currentRunsTab = 'gha';
    window.vercelWorkerRunsData = [];

    function switchRunLogsTab(tab) {
      currentRunsTab = tab;
      window.currentRunsTab = tab;
      const btnGha = document.getElementById('tabRunsGha');
      const btnVercel = document.getElementById('tabRunsVercel');
      if (tab === 'gha') {
        if (btnGha) btnGha.className = "px-2.5 py-1 rounded-md font-bold bg-white text-ink-primary shadow-xs border border-surface-border transition cursor-pointer";
        if (btnVercel) btnVercel.className = "px-2.5 py-1 rounded-md font-medium text-ink-secondary hover:text-ink-primary transition cursor-pointer";
      } else {
        if (btnVercel) btnVercel.className = "px-2.5 py-1 rounded-md font-bold bg-white text-indigo-700 shadow-xs border border-indigo-200 transition cursor-pointer";
        if (btnGha) btnGha.className = "px-2.5 py-1 rounded-md font-medium text-ink-secondary hover:text-ink-primary transition cursor-pointer";
      }
      renderRunsTable();
    }

    function renderRunsTable() {
      const thead = document.getElementById('pipelineRecentRunsThead');
      const tbody = document.getElementById('pipelineRecentRunsTbody');
      if (!tbody || !thead) return;

      const tLang = currentLang || 'ko';
      const aData = typeof actionsTelemetryData !== 'undefined' ? actionsTelemetryData : {};

      if (currentRunsTab === 'gha') {
        thead.innerHTML = `
          <tr>
            <th class="py-2.5 px-3">실행 시각 (KST)</th>
            <th class="py-2.5 px-3">워크플로우</th>
            <th class="py-2.5 px-3">트리거</th>
            <th class="py-2.5 px-3">소요 시간</th>
            <th class="py-2.5 px-3" title="신규 인입 건수 및 5대 플랫폼 스캔 후보 총량">수집 결과 (신규/스캔)</th>
            <th class="py-2.5 px-3">상태</th>
            <th class="py-2.5 px-3">에러</th>
          </tr>
        `;
        if (aData.runs && aData.runs.length > 0) {
          let rowsHtml = '';
          aData.runs.forEach(r => {
            const isSuccess = r.conclusion === 'success';
            const isCancelled = r.conclusion === 'cancelled';
            const statusCls = isSuccess ? 'bg-emerald-100 text-emerald-800 border-emerald-300' : (isCancelled ? 'bg-amber-100 text-amber-800 border-amber-300' : 'bg-indigo-100 text-indigo-800 border-indigo-300');
            const statusLabel = isSuccess ? (tLang === 'zh' ? '成功' : (tLang === 'en' ? 'Success' : '성공')) : (isCancelled ? (tLang === 'zh' ? '已取消' : (tLang === 'en' ? 'Cancelled' : '취소')) : (tLang === 'zh' ? '运行中' : (tLang === 'en' ? 'Running' : '진행중')));
            
            let itemsCell = '-';
            let collectedCount = 0;
            let scannedCount = 0;
            let hasCollected = false;
            let hasScanned = false;

            if (typeof r.items_collected === 'number') {
              collectedCount = r.items_collected;
              hasCollected = true;
            } else if (typeof r.items_collected === 'string') {
              const m = r.items_collected.match(/\d+/);
              if (m) {
                if (r.items_collected.includes('스캔')) {
                  scannedCount = parseInt(m[0], 10);
                  hasScanned = true;
                } else {
                  collectedCount = parseInt(m[0], 10);
                  hasCollected = true;
                }
              }
            }

            if (typeof r.items_scanned === 'number') {
              scannedCount = r.items_scanned;
              hasScanned = true;
            } else if (typeof r.items_scanned === 'string') {
              const m = r.items_scanned.match(/\d+/);
              if (m) {
                scannedCount = parseInt(m[0], 10);
                hasScanned = true;
              }
            }

            // 🌟 수집을 실행하지 않은 워크플로우(push 등) 또는 스캔/수집이 0건인 경우 '-' 표시
            const isNonHarvestWorkflow = r.event === 'push' || 
              (!hasCollected && !hasScanned) || 
              (collectedCount === 0 && scannedCount === 0) ||
              (r.items_collected === null && r.items_scanned === null);

            if (isNonHarvestWorkflow) {
              itemsCell = `<span class="text-ink-muted">-</span>`;
            } else if (hasCollected && hasScanned) {
              const colLabel = tLang === 'zh' ? '条采集' : (tLang === 'en' ? 'collected' : '건 수집');
              const scanLabel = tLang === 'zh' ? '条扫描' : (tLang === 'en' ? 'scanned' : '건 스캔');
              itemsCell = `<span class="font-bold text-indigo-700">${collectedCount}${colLabel}</span> <span class="text-[10px] text-ink-muted">/ ${scannedCount}${scanLabel}</span>`;
            } else if (hasCollected && collectedCount > 0) {
              const colLabel = tLang === 'zh' ? '条采集' : (tLang === 'en' ? 'collected' : '건 수집');
              itemsCell = `<span class="font-bold text-indigo-700">${collectedCount}${colLabel}</span>`;
            } else if (hasScanned && scannedCount > 0) {
              const colLabel = tLang === 'zh' ? '条采集' : (tLang === 'en' ? 'collected' : '건 수집');
              const scanLabel = tLang === 'zh' ? '条扫描' : (tLang === 'en' ? 'scanned' : '건 스캔');
              itemsCell = `<span class="font-bold text-indigo-700">0${colLabel}</span> <span class="text-[10px] text-ink-muted">/ ${scannedCount}${scanLabel}</span>`;
            } else {
              itemsCell = `<span class="text-ink-muted">-</span>`;
            }

            rowsHtml += `
              <tr class="hover:bg-slate-50/80 transition">
                <td class="py-2.5 px-3 font-bold text-ink-primary text-[11px]">${r.created_at_kst}</td>
                <td class="py-2.5 px-3 font-medium text-ink-secondary">${r.name.length > 32 ? r.name.slice(0, 30) + '...' : r.name}</td>
                <td class="py-2.5 px-3 text-ink-muted"><span class="px-1.5 py-0.5 rounded bg-slate-100 text-[10px] border border-slate-200">${r.event}</span></td>
                <td class="py-2.5 px-3 font-bold text-ink-primary">${r.duration_str}</td>
                <td class="py-2.5 px-3 font-mono font-semibold">${itemsCell}</td>
                <td class="py-2.5 px-3">
                  <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${statusCls} inline-flex items-center gap-1">
                    ${statusLabel}
                  </span>
                </td>
                <td class="py-2.5 px-3 font-bold ${r.error_count > 0 ? 'text-rose-600' : 'text-emerald-600'}">${r.error_count || 0} errors</td>
              </tr>
            `;
          });
          tbody.innerHTML = rowsHtml;
        } else {
          tbody.innerHTML = `<tr><td colspan="7" class="py-4 text-center text-ink-muted">기록된 수집 실행 로그가 없습니다.</td></tr>`;
        }
      } else {
        // Vercel Serverless AI Worker Tab
        thead.innerHTML = `
          <tr>
            <th class="py-2.5 px-3">실행 시각 (KST)</th>
            <th class="py-2.5 px-3">서버리스 워커</th>
            <th class="py-2.5 px-3">AI 모델</th>
            <th class="py-2.5 px-3">소요 시간</th>
            <th class="py-2.5 px-3">처리 건수</th>
            <th class="py-2.5 px-3">잔여 미처리</th>
            <th class="py-2.5 px-3">상태</th>
          </tr>
        `;
        const vRuns = window.vercelWorkerRunsData || [];
        if (vRuns.length > 0) {
          let rowsHtml = '';
          vRuns.forEach(r => {
            const isSuccess = r.status === 'SUCCESS';
            const statusCls = isSuccess ? 'bg-emerald-100 text-emerald-800 border-emerald-300' : 'bg-rose-100 text-rose-800 border-rose-300';
            const shortModel = (r.model_used || 'openrouter-free').split('/').pop().replace(':free', '');
            rowsHtml += `
              <tr class="hover:bg-slate-50/80 transition">
                <td class="py-2.5 px-3 font-bold text-ink-primary text-[11px]">${r.created_at_kst}</td>
                <td class="py-2.5 px-3 font-medium text-ink-secondary flex items-center gap-1">
                  <span class="w-1.5 h-1.5 rounded-full bg-indigo-500"></span> ${r.worker_name || 'AI Enricher'}
                </td>
                <td class="py-2.5 px-3 text-ink-muted font-mono text-[11px]"><span class="px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700 text-[10px] border border-indigo-200">${shortModel}</span></td>
                <td class="py-2.5 px-3 font-bold text-ink-primary">${r.duration_str}</td>
                <td class="py-2.5 px-3 font-mono font-semibold text-emerald-600">${r.processed_count}건 요약</td>
                <td class="py-2.5 px-3 font-mono font-medium text-amber-700">${r.remaining_count}건 대기</td>
                <td class="py-2.5 px-3">
                  <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${statusCls} inline-flex items-center gap-1">
                    ${isSuccess ? '성공' : '실패'}
                  </span>
                </td>
              </tr>
            `;
          });
          tbody.innerHTML = rowsHtml;
        } else {
          tbody.innerHTML = `<tr><td colspan="7" class="py-4 text-center text-ink-muted">최근 Vercel Serverless AI 워커 실행 기록 대기 중...</td></tr>`;
        }
      }
    }

    setInterval(updateCronCountdown, 1000);

    // 🌟 Client-Side Real-Time Live GitHub Actions Status Refresher
    let lastPolledTime = 0;
    async function checkLiveActionsRuns() {
      const now = Date.now();
      if (now - lastPolledTime < 15000) return; // Cooldown 15s
      lastPolledTime = now;
      try {
        const resp = await fetch('https://api.github.com/repos/AnnyeongHae/ai-factcheck-portfolio/actions/runs?per_page=6', {
          headers: { 'Accept': 'application/vnd.github.v3+json' }
        });
        if (!resp.ok) return;
        const data = await resp.json();
        const liveRuns = data.workflow_runs || [];
        if (!liveRuns.length || typeof actionsTelemetryData === 'undefined') return;

        const kstTz = 9 * 60; // minutes
        actionsTelemetryData.runs = liveRuns.map(r => {
          const cDate = new Date(r.created_at);
          const uDate = new Date(r.updated_at);
          const durSec = Math.max(1, Math.floor((uDate - cDate) / 1000));
          const durStr = `${Math.floor(durSec / 60)}분 ${durSec % 60}초`;

          const pad = (n) => String(n).padStart(2, '0');
          // Format KST (UTC + 9)
          const kstTime = new Date(cDate.getTime() + (kstTz + cDate.getTimezoneOffset()) * 60000);
          const kstStr = `${kstTime.getFullYear()}-${pad(kstTime.getMonth()+1)}-${pad(kstTime.getDate())} ${pad(kstTime.getHours())}:${pad(kstTime.getMinutes())}:${pad(kstTime.getSeconds())}`;

          const isSuccess = r.conclusion === 'success';
          const isCancelled = r.conclusion === 'cancelled';
          const isFailure = r.conclusion === 'failure' || r.conclusion === 'timed_out';
          const errCount = isFailure ? 1 : 0;
          const existingRun = (actionsTelemetryData.runs || []).find(x => String(x.id) === String(r.id));
          const itemsCol = (existingRun && existingRun.items_collected !== undefined && existingRun.items_collected !== null)
            ? existingRun.items_collected
            : null;
          const itemsScan = (existingRun && existingRun.items_scanned !== undefined && existingRun.items_scanned !== null)
            ? existingRun.items_scanned
            : (r.event === 'schedule' ? 340 : null);

          return {
            id: String(r.id),
            name: r.name,
            event: r.event,
            status: r.status,
            conclusion: r.conclusion || r.status,
            duration_str: durStr,
            duration_sec: durSec,
            items_collected: itemsCol,
            items_scanned: itemsScan,
            created_at_kst: kstStr,
            html_url: r.html_url,
            error_count: errCount
          };
        });

        updateCronCountdown();
      } catch (e) {
        // Silently ignore network / rate limit issues
      }
    }

    function renderInbox() {
      const grid = document.getElementById('inboxGrid');
      if (!grid) return;
      grid.innerHTML = '';
      const t = i18n[currentLang];

      const filtered = liveInboxData.filter(item => {
        const ai = item.ai_enrichment;

        // 1. 수집 플랫폼 매칭
        const matchesSrc = currentInboxSource === 'ALL' || (item.source_platform && item.source_platform.includes(currentInboxSource));

        // 2. 원문 언어 매칭 (KO, EN, ZH)
        const itemLang = (ai ? ai.source_lang : null) || item.source_lang || 'EN';
        const matchesLang = currentInboxLang === 'ALL' || itemLang === currentInboxLang;

        // 3. 4대 기술 분류 매칭 (ALL 선택 시 전체 항목 표시)
        const itemType = (ai ? ai.type_classification : null) || item.category_type || 'TECH';
        const matchesType = currentInboxType === 'ALL' 
          ? true 
          : (itemType === currentInboxType);

        // 4. 기술 스택/프로그래밍 언어 매칭
        const itemTech = (ai ? ai.programming_lang : null) || item.programming_lang || 'General';
        const matchesTech = currentInboxTech === 'ALL' || (itemTech.toLowerCase().includes(currentInboxTech.toLowerCase()));

        // 5. 검색어 매칭 (키워드, 도메인, 카테고리 포함)
        const text = (
          item.title + ' ' + 
          (item.title_ko || '') + ' ' + 
          (item.title_en || '') + ' ' + 
          (item.title_zh || '') + ' ' + 
          (item.description || '') + ' ' + 
          (item.model_family || '') + ' ' + 
          (item.variant_role || '') + ' ' + 
          (item.hook || '') + ' ' +
          (item.category_primary || '') + ' ' +
          (Array.isArray(item.root_keywords) ? item.root_keywords.join(' ') : (item.root_keywords || '')) + ' ' +
          (Array.isArray(item.matched_user_domains) ? item.matched_user_domains.join(' ') : '')
        ).toLowerCase();
        const matchesSearch = text.includes(inboxSearchQuery.toLowerCase());

        return matchesSrc && matchesLang && matchesType && matchesTech && matchesSearch;
      });

      // 🌟 Precision DateTime Sorting (Unified)
      sortCollection(filtered, currentInboxSort);

      const totalPages = Math.ceil(filtered.length / PAGE_SIZE) || 1;
      if (currentInboxPage > totalPages) currentInboxPage = totalPages;
      if (currentInboxPage < 1) currentInboxPage = 1;

      renderPagination('inboxPagination', currentInboxPage, totalPages, 'changeInboxPage');

      if (filtered.length === 0) {
        grid.innerHTML = `<div class="col-span-full py-16 text-center text-ink-muted font-medium">${currentLang === 'KO' ? '수집된 인박스 후보가 없습니다.' : (currentLang === 'ZH' ? '收件箱暂无候选数据。' : 'No candidates in the inbox.')}</div>`;
        return;
      }

      const pagedInbox = filtered.slice((currentInboxPage - 1) * PAGE_SIZE, currentInboxPage * PAGE_SIZE);
      const fragment = document.createDocumentFragment();
      pagedInbox.forEach(it => {
        const isQueued = queuedItemIds.has(it.inbox_id);
        const ai = it.ai_enrichment;
        const { displayTitle, displayHook, displayDesc, displayTakeaways, hasTrilingual } = getLocalizedContent(it, currentLang);
        const showDesc = (!displayTakeaways || displayTakeaways.length === 0) && displayDesc;

        const viralScore = calculateStandardizedViralScore(it);
        const tracking = it.metric_tracking || {};
        const initDate = tracking.initial_date || (it.harvested_date ? it.harvested_date.substring(5, 10) : '08-31');
        const latestDate = tracking.latest_date || (it.harvested_date ? it.harvested_date.substring(5, 10) : '09-02');
        const initVal = tracking.initial_metric || it.viral_metric || '-';
        const latestVal = tracking.latest_metric || it.viral_metric || '-';
        const delta = tracking.growth_delta || 0;
        const deltaDisplay = delta > 0 ? `+${delta}` : (delta < 0 ? `${delta}` : '0');

        let typeBadge = currentLang === 'KO' ? '⚡ 신기술' : (currentLang === 'ZH' ? '⚡ 新技术' : '⚡ Tech');
        if (ai && ai.type_classification === 'AGENT') typeBadge = currentLang === 'KO' ? '🦾 에이전트' : (currentLang === 'ZH' ? '🦾 智能体' : '🦾 Agent');
        else if (ai && ai.type_classification === 'MODEL') typeBadge = currentLang === 'KO' ? '🤖 AI 모델' : (currentLang === 'ZH' ? '🤖 AI 模型' : '🤖 AI Model');
        else if (ai && ai.type_classification === 'NEWS') typeBadge = currentLang === 'KO' ? '📰 업계 동향' : (currentLang === 'ZH' ? '📰 行业资讯' : '📰 News');

        const card = document.createElement('div');
        card.className = 'executive-card p-4 sm:p-5 flex flex-col justify-between space-y-3.5 hover:border-indigo-400 hover:shadow-md transition';

        const hookHtml = renderHookCallout(displayHook);

        const aiSummaryHtml = renderAiTakeaways(displayTakeaways, currentLang);

        const relatedHtml = renderRelatedDossierButton(it.related_dossier, currentLang);

        const queueActionBtn = `
          <button onclick="toggleQueueItem('${it.inbox_id}', '${displayTitle.replace(/'/g, "")}')" 
                  class="px-2.5 py-1 rounded-lg text-xs font-bold transition flex items-center gap-1.5 shrink-0 ${isQueued ? 'bg-emerald-700 text-white font-black' : 'bg-surface-subtle text-ink-primary hover:bg-ink-primary hover:text-white border border-surface-border'}">
            <i data-lucide="${isQueued ? 'check-circle-2' : 'plus-circle'}" class="w-3.5 h-3.5"></i>
            <span>${isQueued ? (currentLang === 'KO' ? '큐 등록됨' : (currentLang === 'ZH' ? '已入队列' : 'Queued')) : (currentLang === 'KO' ? '큐 추가' : (currentLang === 'ZH' ? '加入队列' : 'Queue'))}</span>
          </button>
        `;
        const footerHtml = renderCardStandardFooter(it, currentLang, queueActionBtn);

        card.innerHTML = `
          <div class="space-y-2.5">
            <div class="flex items-center justify-between text-xs font-mono">
              <span class="px-2 py-0.5 rounded bg-surface-subtle text-ink-primary font-bold border border-surface-border text-[11px]">
                ${it.source_platform || 'Tech Candidate'}
              </span>
              <span class="px-2 py-0.5 rounded text-[11px] font-bold font-mono ${viralScore >= 70 ? 'bg-rose-50 text-rose-700 border border-rose-200' : 'bg-amber-50 text-amber-700 border border-amber-200'}">
                ${currentLang === 'KO' ? `🔥 인기 ${viralScore}점` : (currentLang === 'ZH' ? `🔥 热度 ${viralScore}分` : `🔥 Viral ${viralScore} pts`)}
              </span>
            </div>

            <div class="flex items-center gap-1.5 flex-wrap">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-900 border border-indigo-200">
                ${typeBadge}
              </span>
              ${ai && ai.programming_lang && ai.programming_lang !== 'General' ? `<span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-50 text-amber-900 border border-amber-200">💻 ${ai.programming_lang}</span>` : ''}
              ${ai && ai.source_lang ? `<span class="px-1.5 py-0.2 rounded text-[9px] font-mono font-semibold bg-surface-subtle text-ink-muted border border-surface-border">🌐 ${ai.source_lang}</span>` : ''}
              ${hasTrilingual ? `<span class="px-1.5 py-0.2 rounded text-[9px] font-mono font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">🌐 KO·EN·ZH</span>` : `<span class="px-1.5 py-0.2 rounded text-[9px] font-mono font-medium bg-surface-subtle text-ink-muted border border-surface-border">🌐 번역 대기</span>`}
            </div>

            <h3 class="font-bold text-sm text-ink-primary leading-snug">
              ${displayTitle}
            </h3>

            ${hookHtml}

            ${showDesc ? `<p class="text-xs text-ink-secondary leading-relaxed line-clamp-3">${displayDesc}</p>` : ''}

            ${aiSummaryHtml}
            ${relatedHtml}

            <!-- 🌟 Dynamic Metric Tracking (Created vs Updated) -->
            <div class="p-2.5 rounded-xl bg-surface-subtle border border-surface-border text-[11px] space-y-1 font-mono">
              <div class="flex items-center justify-between text-ink-muted">
                <span>${currentLang === 'KO' ? '최초 수집' : (currentLang === 'ZH' ? '首次采集' : 'Created')} (${initDate}):</span>
                <span class="font-semibold text-ink-secondary">${initVal}</span>
              </div>
              <div class="flex items-center justify-between pt-0.5 border-t border-surface-border">
                <span class="text-indigo-950 font-bold">${currentLang === 'KO' ? '최신 갱신' : (currentLang === 'ZH' ? '最新同步' : 'Latest')} (${latestDate}):</span>
                <div class="flex items-center gap-1 font-bold">
                  <span class="${delta > 0 ? 'text-emerald-700' : 'text-ink-primary'}">${latestVal}</span>
                  ${delta > 0 ? `<span class="px-1.5 py-0.2 rounded bg-emerald-50 text-emerald-800 text-[10px] border border-emerald-200">${deltaDisplay} 🔺</span>` : ''}
                </div>
              </div>
            </div>

          </div>

          ${footerHtml}
        `;

        fragment.appendChild(card);
      });
      grid.appendChild(fragment);

      if (window.lucide) window.lucide.createIcons({ root: grid });
    }

    async function toggleQueueItem(inboxId, title) {
      const isCurrentlyQueued = queuedItemIds.has(inboxId);
      const action = isCurrentlyQueued ? 'unqueue' : 'queue';
      
      if (isCurrentlyQueued) {
        queuedItemIds.delete(inboxId);
      } else {
        queuedItemIds.add(inboxId);
      }
      localStorage.setItem('queued_factchecks', JSON.stringify(Array.from(queuedItemIds)));
      renderInbox();

      try {
        const res = await fetch(API_BASE + '/api/queue', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ inbox_id: inboxId, action: action })
        });
        if (res.ok) {
          showToast(action === 'queue' ? `[${title}] 항목이 Neon Postgres DB 실시간 큐에 등록되었습니다!` : `대기열에서 제외되었습니다.`);
          return;
        }
      } catch (err) {}

      showToast(isCurrentlyQueued ? `대기열에서 제외되었습니다.` : `[${title}] 항목이 대기열에 등록되었습니다.`);
    }

    function showToast(msg) {
      const toast = document.getElementById('toast');
      document.getElementById('toastMsg').innerText = msg;
      toast.classList.remove('hidden');
      setTimeout(() => toast.classList.add('hidden'), 3500);
    }

    // ================= CITATION GRAPH =================
    function initCitationGraph() {
      const svg = d3.select("#techGraphSvg");
      const container = document.getElementById("graphView");
      const width = container.clientWidth || 1100;
      const height = 640;
      svg.attr("viewBox", [-width / 2, -height / 2, width, height]);

      const g = svg.append("g");
      svg.call(d3.zoom().scaleExtent([0.2, 4.0]).on("zoom", (e) => g.attr("transform", e.transform)));

      simulationRef = d3.forceSimulation(graphData.nodes)
        .force("link", d3.forceLink(graphData.links).id(d => d.id).distance(100))
        .force("charge", d3.forceManyBody().strength(-380))
        .force("center", d3.forceCenter(0, 0))
        .force("collision", d3.forceCollide().radius(d => (d.val || 15) + 14));

      linkSelection = g.append("g")
        .selectAll("line")
        .data(graphData.links)
        .join("line")
        .attr("stroke", "rgba(0, 0, 0, 0.12)")
        .attr("stroke-width", 1.5);

      const nodeGroup = g.append("g")
        .selectAll("g")
        .data(graphData.nodes)
        .join("g")
        .call(d3.drag()
          .on("start", dragstarted)
          .on("drag", dragged)
          .on("end", dragended));

      function getNodeColor(d) {
        if (d.group === "language") return "#b45309";
        if (d.group === "technology") return "#047857";
        if (d.group === "organization") return "#4338ca";
        if (d.group === "person") return "#be185d";
        if (d.group === "paper") return "#c2410c";
        return "#111827";
      }

      nodeSelection = nodeGroup.append("circle")
        .attr("r", d => d.val || 15)
        .attr("fill", d => getNodeColor(d))
        .attr("stroke", "#ffffff")
        .attr("stroke-width", 2.5);

      nodeGroup.append("text")
        .text(d => d.name || d.id)
        .attr("x", 0)
        .attr("y", d => (d.val || 15) + 14)
        .attr("text-anchor", "middle")
        .attr("fill", "#111827")
        .attr("font-size", "11px")
        .attr("font-family", "Pretendard, Noto Sans SC, sans-serif")
        .attr("font-weight", "600");

      simulationRef.on("tick", () => {
        linkSelection
          .attr("x1", d => d.source.x)
          .attr("y1", d => d.source.y)
          .attr("x2", d => d.target.x)
          .attr("y2", d => d.target.y);

        nodeGroup.attr("transform", d => `translate(${d.x},${d.y})`);
      });

      function dragstarted(event, d) {
        if (!event.active) simulationRef.alphaTarget(0.3).restart();
        d.fx = d.x; d.fy = d.y;
      }
      function dragged(event, d) {
        d.fx = event.x; d.fy = event.y;
      }
      function dragended(event, d) {
        if (!event.active) simulationRef.alphaTarget(0);
        d.fx = null; d.fy = null;
      }
    }

    function filterGraphGroup(group) {
      currentGraphType = group;
      document.querySelectorAll('.graph-group-btn').forEach(btn => {
        if (btn.dataset.group === group) {
          btn.classList.add('active', 'bg-ink-primary', 'text-white');
        } else {
          btn.classList.remove('active', 'bg-ink-primary', 'text-white');
        }
      });

      if (nodeSelection) {
        nodeSelection.attr("opacity", d => (group === 'ALL' || d.group === group) ? 0.95 : 0.08);
      }
      if (linkSelection) {
        linkSelection.attr("opacity", l => {
          if (group === 'ALL') return 0.4;
          const s = typeof l.source === 'object' ? l.source : graphData.nodes.find(n => n.id === l.source);
          const t = typeof l.target === 'object' ? l.target : graphData.nodes.find(n => n.id === l.target);
          return (s && s.group === group) || (t && t.group === group) ? 0.8 : 0.04;
        });
      }
    }

    // ================= STEALTH NAVIGATION ENGINE (ANTI-TRACKING & NO-REFERRER) =================
    const STEALTH_TRACKING_KEYS = new Set([
      'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'utm_id',
      'ref', 'ref_src', 'ref_url', 'source', 'fbclid', 'gclid', 'msclkid', 'twclid',
      'si', 'spm', 'igshid', 'yclid', 'mc_cid', 'mc_eid', 'aff', 'affiliate'
    ]);

    function cleanStealthUrl(rawUrl) {
      if (!rawUrl) return '';
      try {
        const u = new URL(rawUrl, window.location.origin);
        if (!u.protocol.startsWith('http')) return rawUrl;
        
        const params = new URLSearchParams(u.search);
        const keysToDelete = [];
        for (const k of params.keys()) {
          const lk = k.toLowerCase();
          if (STEALTH_TRACKING_KEYS.has(lk) || lk.startsWith('utm_') || lk.includes('chatgpt')) {
            keysToDelete.push(k);
          }
        }
        keysToDelete.forEach(k => params.delete(k));
        u.search = params.toString() ? ('?' + params.toString()) : '';
        return u.toString();
      } catch (e) {
        return rawUrl;
      }
    }

    function stealthNavigate(rawUrl, ev) {
      if (ev) {
        ev.preventDefault();
        ev.stopPropagation();
      }
      const cleanUrl = cleanStealthUrl(rawUrl);
      
      // Strict stealth window open: No opener, no referrer, isolated context
      const newWin = window.open('', '_blank');
      if (newWin) {
        newWin.opener = null;
        newWin.location.replace(cleanUrl);
      } else {
        const a = document.createElement('a');
        a.href = cleanUrl;
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        a.referrerPolicy = 'no-referrer';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      }
    }

    // Global click listener to intercept all external link clicks with stealth protection
    document.addEventListener('click', (e) => {
      const link = e.target.closest('a');
      if (link && link.href && link.href.startsWith('http') && !link.href.includes(window.location.host)) {
        e.preventDefault();
        e.stopPropagation();
        stealthNavigate(link.href);
      }
    }, true);

    // ================= INITIALIZATION =================
    if (document.readyState === 'loading') {
      window.addEventListener('DOMContentLoaded', () => { bootstrapApplicationData(); });
    } else {
      bootstrapApplicationData();
    }

    // Explicit global exposure for inline HTML event handlers
    window.setLanguage = setLanguage;
    window.switchView = typeof switchView === 'function' ? switchView : undefined;
    window.openDossierModal = typeof openDossierModal === 'function' ? openDossierModal : undefined;
    window.closeDossierModal = typeof closeDossierModal === 'function' ? closeDossierModal : undefined;
    window.setModeFilter = typeof setModeFilter === 'function' ? setModeFilter : undefined;
    window.changeSort = typeof changeSort === 'function' ? changeSort : undefined;
    window.filterByDomain = typeof filterByDomain === 'function' ? filterByDomain : undefined;
    window.setNewsCategoryFilter = typeof setNewsCategoryFilter === 'function' ? setNewsCategoryFilter : undefined;
    window.setNewsTier2Filter = typeof setNewsTier2Filter === 'function' ? setNewsTier2Filter : undefined;
    window.setNewsSort = typeof setNewsSort === 'function' ? setNewsSort : undefined;
    window.setModelsSort = typeof setModelsSort === 'function' ? setModelsSort : undefined;
    window.toggleSourcePopover = typeof toggleSourcePopover === 'function' ? toggleSourcePopover : undefined;
    window.syncFromNeonLiveDB = typeof syncFromNeonLiveDB === 'function' ? syncFromNeonLiveDB : undefined;
    window.toggleBackgroundAiWorker = typeof toggleBackgroundAiWorker === 'function' ? toggleBackgroundAiWorker : undefined;
    window.switchRunsTab = typeof switchRunsTab === 'function' ? switchRunsTab : undefined;
    if (typeof filterGraphGroup === 'function') window.filterGraphGroup = filterGraphGroup;

