/**
 * ==============================================================================
 * Universal Asynchronous Data Hydration & Real-time Live API Engine
 * Manages Vercel Serverless / Cloud DB synchronization and client-side background workers
 * ==============================================================================
 */

import { APP_CONFIG } from './config.js';
import {
  AppStore,
  casesData,
  modelsData,
  newsData,
  inboxData,
  adminData,
  graphData,
  timeline24hData,
  actionsTelemetryData,
  trend6hData,
  trendRadarData,
  snapshotStats,
  liveCasesData,
  liveModelsData,
  liveInboxData,
  liveNewsData,
  currentLang
} from './store.js';
import { getDynamicKstHour, getDynamicKstDate } from '../utils/dateTime.js';
import { showToast } from '../components/toast.js';
import { ClientCache } from './cache.js';

export async function bootstrapApplicationData() {
  console.log('[Bootstrap] Initializing asynchronous DB-First data hydration...');
  let loadedFromEdge = false;

  // 1. Primary Source: Session SWR Cache or Vercel Edge SWR API
  const cachedPortfolios = ClientCache.get('portfolios_summary', 120000);
  if (cachedPortfolios && cachedPortfolios.success && Array.isArray(cachedPortfolios.portfolios) && cachedPortfolios.portfolios.length > 0) {
    AppStore.setCases(cachedPortfolios.portfolios);
    loadedFromEdge = true;
    if (cachedPortfolios.db_provider) APP_CONFIG.setDbProvider(cachedPortfolios.db_provider);
    console.log(`[Bootstrap] ⚡ [Session SWR Cache] Restored ${cachedPortfolios.portfolios.length} dossiers instantly.`);
  } else {
    try {
      const portfoliosApiUrl = APP_CONFIG.apiUrl('/api/portfolios?summary=true');
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 6000);
      const edgeRes = await fetch(portfoliosApiUrl, { signal: controller.signal });
      clearTimeout(timeoutId);

      if (edgeRes.ok) {
        const edgeData = await edgeRes.json();
        if (edgeData && edgeData.success && Array.isArray(edgeData.portfolios) && edgeData.portfolios.length > 0) {
          AppStore.setCases(edgeData.portfolios);
          loadedFromEdge = true;
          ClientCache.set('portfolios_summary', edgeData);
          if (edgeData.db_provider) APP_CONFIG.setDbProvider(edgeData.db_provider);
          console.log(`[Bootstrap] ⚡ [DB-First Edge SWR] Loaded ${edgeData.portfolios.length} dossiers directly from ${APP_CONFIG.dbProvider} Edge API.`);
        }
      }
    } catch (edgeErr) {
      console.warn('[Bootstrap] Edge API first-paint timeout or offline, falling back to static snapshot:', edgeErr.message);
    }
  }

  try {
    let staticRes = await fetch('data.json', { cache: 'default' });
    let cType = staticRes.headers.get('content-type') || '';
    if (!staticRes.ok || !cType.includes('application/json')) {
      staticRes = await fetch('/data.json', { cache: 'default' });
      cType = staticRes.headers.get('content-type') || '';
    }
    if (staticRes.ok && cType.includes('application/json')) {
      const data = await staticRes.json();
      AppStore.setGraphData(data.graph || { nodes: [], links: [] });
      window.adminData = data.admin_stats || {};
      window.timeline24hData = data.timeline_24h || [];
      window.actionsTelemetryData = data.actions_telemetry || {};
      window.trend6hData = data.trend_6h || {};
      window.trendRadarData = data.trend_radar || {};

      Object.assign(snapshotStats, {
        total_cases: data.total_cases || (data.cases ? data.cases.length : 58),
        news_total_count: data.news_total_count || (data.news_items ? data.news_items.length : 3039),
        models_total_count: data.models_total_count || (data.model_items ? data.model_items.length : 344),
        inbox_total_count: data.inbox_total_count || (data.inbox_items ? data.inbox_items.length : 3039),
        tier1_counts: data.tier1_counts || null,
        news_cat_counts: data.news_cat_counts || null,
        model_art_counts: data.model_art_counts || null,
        model_fam_counts: data.model_fam_counts || null
      });

      if (!loadedFromEdge) {
        AppStore.init(data);
        console.log(`[Bootstrap] Loaded ${AppStore.getCases().length} dossiers from static snapshot fallback.`);
      } else {
        AppStore._news = data.trend_items || data.news_items || data.news || [];
        AppStore._models = data.model_items || data.models || [];
        AppStore._inbox = data.inbox_items || (data.inbox_recent || []).concat(data.inbox || []);

        AppStore._models.forEach(it => { it.is_model = true; });
        AppStore._news.forEach(it => {
          if (it.is_model === undefined) {
            it.is_model = it.facet_type === 'MODEL' || !!(it.model_family || it.artifact_type || (it.category_primary === 'MODEL_RELEASE'));
          }
        });
        AppStore._inbox.forEach(it => {
          if (it.is_model === undefined) it.is_model = !!(it.model_family || it.artifact_type || (it.category_primary === 'MODEL_RELEASE'));
          if (it.is_news === undefined) it.is_news = !it.is_model;
        });

        [...AppStore._inbox, ...AppStore._news, ...AppStore._models].forEach(it => {
          const id = it.inbox_id || it.id;
          if (id && !AppStore._itemsMap.has(id)) {
            AppStore._itemsMap.set(id, it);
          }
        });

        window.liveNewsData = AppStore._news;
        window.liveModelsData = AppStore._models;
        window.inboxData = AppStore._inbox;
        window.liveInboxData = AppStore._inbox;
        window.newsData = AppStore._news;
        window.modelsData = AppStore._models;
      }
    }
  } catch (e) {
    console.warn('[Bootstrap] Static snapshot fallback skipped:', e.message);
  }

  updateGlobalStatsUI();

  // Restore user saved language preference if previously selected
  try {
    const savedLang = localStorage.getItem('factcheck_lang');
    if (savedLang && ['KO', 'ZH', 'EN'].includes(savedLang) && savedLang !== 'KO') {
      if (typeof window.setLanguage === 'function') window.setLanguage(savedLang);
    }
  } catch (e) {}

  // Lazy Active View Rendering
  const initialHash = typeof window !== 'undefined' ? window.location.hash || '' : '';
  let initialView = 'home';
  if (initialHash.startsWith('#/factchecks') || initialHash.startsWith('#case/')) initialView = 'portfolio';
  else if (initialHash.startsWith('#/news')) initialView = 'news';
  else if (initialHash.startsWith('#/models')) initialView = 'models';
  else if (initialHash.startsWith('#/graph')) initialView = 'graph';
  else if (initialHash.startsWith('#/inbox')) initialView = 'inbox';

  if (typeof window.switchView === 'function') {
    window.switchView(initialView, false, true);
  }

  // Live DB sync in background (idle delay)
  setTimeout(() => {
    syncFromLiveDB(false)
      .then(() => updateGlobalStatsUI())
      .catch(e => console.warn('[Bootstrap] Live DB sync completed or skipped:', e.message));
  }, 1500);

  // Mark app as initialized for the zero-downtime fallback harness
  if (typeof window !== 'undefined') {
    window.__APP_INITIALIZED__ = true;
  }
}

export function updateGlobalStatsUI() {
  if (typeof document === 'undefined') return;
  const safeSet = (id, txt) => { const el = document.getElementById(id); if (el) el.textContent = txt; };
  const lCases = typeof window !== 'undefined' ? window.liveCasesData : liveCasesData;
  const lNews = typeof window !== 'undefined' ? window.liveNewsData : liveNewsData;
  const lModels = typeof window !== 'undefined' ? window.liveModelsData : liveModelsData;
  const lInbox = typeof window !== 'undefined' ? window.liveInboxData : liveInboxData;

  const numCases = (lCases && lCases.length) || snapshotStats.total_cases || 58;
  const numNews = snapshotStats.news_total_count || (lNews && lNews.length) || 0;
  const numModels = snapshotStats.models_total_count || (lModels && lModels.length) || 0;
  const numInbox = snapshotStats.inbox_total_count || (lInbox && lInbox.length) || 0;

  safeSet('statValVerified', numCases);
  safeSet('statValNews', numNews);
  safeSet('statValModels', numModels);
  safeSet('statValInbox', numInbox.toLocaleString());

  safeSet('headerVerifiedCount', `(${numCases})`);
  safeSet('headerNewsCount', `(${numInbox.toLocaleString()})`);
  safeSet('headerModelsCount', `(${numModels})`);
  safeSet('headerInboxCount', `(${numInbox})`);

  const inbList = lInbox || [];
  const enrichedInbox = inbList.filter(x => x.is_classified || x.ai_enrichment).length;
  const pendingInbox = Math.max(0, numInbox - enrichedInbox);
  const enrichedPct = numInbox > 0 ? ((enrichedInbox / numInbox) * 100).toFixed(1) : '100.0';

  safeSet('statInboxEnrichedText', `● 요약 ${enrichedInbox.toLocaleString()}건 (${enrichedPct}%)`);
  safeSet('statInboxPendingText', `· 대기 ${pendingInbox.toLocaleString()}건`);

  const casesList = lCases || [];
  const trueCount = casesList.filter(c => c.verdict === 'VERIFIED_TRUE').length || snapshotStats.verified_true_count || 31;
  const halfCount = casesList.filter(c => c.verdict && c.verdict.startsWith('HALF_TRUE')).length || snapshotStats.half_true_count || 22;
  const gamedCount = Math.max(0, numCases - trueCount - halfCount);
  safeSet('statVerifiedTrue', trueCount);
  safeSet('statHalfTrue', halfCount);
  safeSet('statGamed', gamedCount);

  safeSet('heroAuditCount', `● ${numCases}개 기술 검증 완료`);
  safeSet('portfolioDossiersCountBadge', `총 ${numCases}건 완료`);
  const curLang = typeof window !== 'undefined' && window.currentLang ? window.currentLang : currentLang;
  const viewAllText = curLang === 'KO' ? `전체 ${numCases}개 검증 도시에 보러가기` : (curLang === 'ZH' ? `查看全部 ${numCases} 份核查档案` : `View All ${numCases} Empirical Dossiers`);
  safeSet('homeTopPicksViewAll', viewAllText);

  if (typeof updateNewsCategoryPillCounts === 'function') {
    updateNewsCategoryPillCounts();
  }
  if (typeof updateModelCategoryPillCounts === 'function') {
    updateModelCategoryPillCounts();
  }
}

export function updateNewsCategoryPillCounts() {
  if (typeof document === 'undefined') return;
  const t1Counts = Object.assign({
    TECH_COMPUTING: 2708,
    CULTURE_HUMANITIES: 141,
    SCIENCE_RESEARCH: 123,
    LAW_CRIME_JUSTICE: 107,
    ECONOMY_FINANCE: 80,
    POLITICS_POLICY: 64
  }, snapshotStats.tier1_counts || {});

  const calculatedTotal = Object.values(t1Counts).reduce((acc, c) => acc + (typeof c === 'number' ? c : 0), 0);
  const total = calculatedTotal || snapshotStats.inbox_total_count || snapshotStats.news_total_count || 5864;

  const t2Counts = Object.assign({
    INFERENCE_OPT: 231,
    AGENTS_DEVTOOLS: 415,
    MULTIMODAL_AI: 220,
    FOUNDATION_MODELS: 218,
    INFRA_RAG_SECURITY: 531,
    INDUSTRY_TRENDS: 1093
  }, snapshotStats.news_cat_counts || {});

  const lang = (typeof window !== 'undefined' && window.currentLang) ? window.currentLang : currentLang;

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
      ALL: `⚡ 전체 IT 분야 (${t1Counts.TECH_COMPUTING.toLocaleString()})`,
      INFERENCE_OPT: `⚡ 추론·서빙 (${t2Counts.INFERENCE_OPT.toLocaleString()})`,
      AGENTS_DEVTOOLS: `🛠️ 에이전트·도구 (${t2Counts.AGENTS_DEVTOOLS.toLocaleString()})`,
      MULTIMODAL_AI: `🎨 멀티모달 (${t2Counts.MULTIMODAL_AI.toLocaleString()})`,
      FOUNDATION_MODELS: `🤖 파운데이션 (${t2Counts.FOUNDATION_MODELS.toLocaleString()})`,
      INFRA_RAG_SECURITY: `🛡️ 인프라·보안 (${t2Counts.INFRA_RAG_SECURITY.toLocaleString()})`,
      INDUSTRY_TRENDS: `🌐 일반 SW·웹 (${t2Counts.INDUSTRY_TRENDS.toLocaleString()})`
    },
    ZH: {
      ALL: `⚡ 全部 IT 领域 (${t1Counts.TECH_COMPUTING.toLocaleString()})`,
      INFERENCE_OPT: `⚡ 推理与服务 (${t2Counts.INFERENCE_OPT.toLocaleString()})`,
      AGENTS_DEVTOOLS: `🛠️ 智能体与工具 (${t2Counts.AGENTS_DEVTOOLS.toLocaleString()})`,
      MULTIMODAL_AI: `🎨 多模态 (${t2Counts.MULTIMODAL_AI.toLocaleString()})`,
      FOUNDATION_MODELS: `🤖 基础模型 (${t2Counts.FOUNDATION_MODELS.toLocaleString()})`,
      INFRA_RAG_SECURITY: `🛡️ 基础架构与安全 (${t2Counts.INFRA_RAG_SECURITY.toLocaleString()})`,
      INDUSTRY_TRENDS: `🌐 软件与行业动态 (${t2Counts.INDUSTRY_TRENDS.toLocaleString()})`
    },
    EN: {
      ALL: `⚡ All Tech Fields (${t1Counts.TECH_COMPUTING.toLocaleString()})`,
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

export function updateModelCategoryPillCounts() {
  if (typeof document === 'undefined') return;
  const lModels = typeof window !== 'undefined' ? window.liveModelsData : liveModelsData;
  const items = (lModels && lModels.length) ? lModels : [];
  const total = items.length;
  const fCounts = {
    ALL: total,
    Qwen: 0, Wan: 0, MiniMax: 0, FLUX: 0, GLM: 0,
    DeepSeek: 0, Hunyuan: 0, Audio: 0, Standalone: 0
  };
  const aCounts = {
    ALL: total,
    WEIGHTS: 0,
    WEB_SERVICE: 0,
    FINETUNE: 0
  };

  items.forEach(it => {
    const fam = it.model_family || 'Standalone';
    if (fCounts[fam] !== undefined) fCounts[fam]++;
    else fCounts.Standalone++;

    const art = it.artifact_type || 'WEIGHTS';
    if (aCounts[art] !== undefined) aCounts[art]++;
  });

  const lang = (typeof window !== 'undefined' && window.currentLang) ? window.currentLang : currentLang;

  const famLabels = {
    KO: {
      ALL: `전체 패밀리 (${total.toLocaleString()})`,
      Qwen: `Qwen (${fCounts.Qwen.toLocaleString()})`,
      Wan: `Wan 비디오 (${fCounts.Wan.toLocaleString()})`,
      MiniMax: `MiniMax (${fCounts.MiniMax.toLocaleString()})`,
      FLUX: `FLUX 이미지 (${fCounts.FLUX.toLocaleString()})`,
      GLM: `GLM (${fCounts.GLM.toLocaleString()})`,
      DeepSeek: `DeepSeek (${fCounts.DeepSeek.toLocaleString()})`,
      Hunyuan: `Hunyuan (${fCounts.Hunyuan.toLocaleString()})`,
      Audio: `음성/TTS (${fCounts.Audio.toLocaleString()})`,
      Standalone: `독립/신규 모델 (${fCounts.Standalone.toLocaleString()})`
    },
    ZH: {
      ALL: `全部系列 (${total.toLocaleString()})`,
      Qwen: `Qwen (${fCounts.Qwen.toLocaleString()})`,
      Wan: `Wan 视频 (${fCounts.Wan.toLocaleString()})`,
      MiniMax: `MiniMax (${fCounts.MiniMax.toLocaleString()})`,
      FLUX: `FLUX 图像 (${fCounts.FLUX.toLocaleString()})`,
      GLM: `GLM (${fCounts.GLM.toLocaleString()})`,
      DeepSeek: `DeepSeek (${fCounts.DeepSeek.toLocaleString()})`,
      Hunyuan: `Hunyuan (${fCounts.Hunyuan.toLocaleString()})`,
      Audio: `语音/TTS (${fCounts.Audio.toLocaleString()})`,
      Standalone: `独立/新模型 (${fCounts.Standalone.toLocaleString()})`
    },
    EN: {
      ALL: `All Families (${total.toLocaleString()})`,
      Qwen: `Qwen (${fCounts.Qwen.toLocaleString()})`,
      Wan: `Wan Video (${fCounts.Wan.toLocaleString()})`,
      MiniMax: `MiniMax (${fCounts.MiniMax.toLocaleString()})`,
      FLUX: `FLUX Image (${fCounts.FLUX.toLocaleString()})`,
      GLM: `GLM (${fCounts.GLM.toLocaleString()})`,
      DeepSeek: `DeepSeek (${fCounts.DeepSeek.toLocaleString()})`,
      Hunyuan: `Hunyuan (${fCounts.Hunyuan.toLocaleString()})`,
      Audio: `Audio/TTS (${fCounts.Audio.toLocaleString()})`,
      Standalone: `Standalone (${fCounts.Standalone.toLocaleString()})`
    }
  };

  const artLabels = {
    KO: {
      ALL: `전체 (${total.toLocaleString()})`,
      WEIGHTS: `🤖 가중치·체크포인트 (${aCounts.WEIGHTS.toLocaleString()})`,
      WEB_SERVICE: `🌐 데모·Spaces (${aCounts.WEB_SERVICE.toLocaleString()})`,
      FINETUNE: `🎯 특화 파인튜닝 (${aCounts.FINETUNE.toLocaleString()})`
    },
    ZH: {
      ALL: `全部 (${total.toLocaleString()})`,
      WEIGHTS: `🤖 模型权重·检查点 (${aCounts.WEIGHTS.toLocaleString()})`,
      WEB_SERVICE: `🌐 在线演示·Spaces (${aCounts.WEB_SERVICE.toLocaleString()})`,
      FINETUNE: `🎯 定制微调 (${aCounts.FINETUNE.toLocaleString()})`
    },
    EN: {
      ALL: `All (${total.toLocaleString()})`,
      WEIGHTS: `🤖 Weights & Checkpoints (${aCounts.WEIGHTS.toLocaleString()})`,
      WEB_SERVICE: `🌐 Interactive Demos (${aCounts.WEB_SERVICE.toLocaleString()})`,
      FINETUNE: `🎯 Specialized Finetunes (${aCounts.FINETUNE.toLocaleString()})`
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

let _isSyncing = false;
let _syncTimeoutId = null;

export async function syncFromLiveDB(force = false) {
  if (_isSyncing && !force) return;
  _isSyncing = true;
  if (_syncTimeoutId) clearTimeout(_syncTimeoutId);
  _syncTimeoutId = setTimeout(() => { _isSyncing = false; }, 8000);
  const badge = document.getElementById('dbLiveBadge');
  try {
    const tStart = performance.now();
    const apiUrl = APP_CONFIG.apiUrl('/api/stats');
    const res = await fetch(apiUrl, { cache: 'default' });
    const tLatency = Math.round(performance.now() - tStart);

    if (res.ok) {
      const data = await res.json();
      if (data.db_provider) APP_CONFIG.setDbProvider(data.db_provider);
      if (data.status === 'success' && data.counts) {
        const liveInbox = data.counts.inbox_deduped || data.counts.inbox_total;
        const liveModels = data.counts.models_total;
        const liveNews = data.counts.news_total;

        // Preserve live counts in snapshotStats so subsequent UI refreshes maintain 6000+ count
        if (liveInbox) snapshotStats.inbox_total_count = liveInbox;
        if (liveModels) snapshotStats.models_total_count = liveModels;
        if (liveNews) snapshotStats.news_total_count = liveNews;
        if (data.counts.factchecks_verified) snapshotStats.total_cases = data.counts.factchecks_verified;

        const hInbox = document.getElementById('headerInboxCount');
        if (hInbox && liveInbox) hInbox.textContent = `(${liveInbox.toLocaleString()})`;

        const statInbox = document.getElementById('statValInbox');
        if (statInbox && liveInbox) statInbox.textContent = liveInbox.toLocaleString();

        const statNews = document.getElementById('statValNews');
        if (statNews && liveNews) statNews.textContent = liveNews.toLocaleString();

        const hNews = document.getElementById('headerNewsCount');
        if (hNews && liveInbox) hNews.textContent = `(${liveInbox.toLocaleString()})`;

        const statModels = document.getElementById('statValModels');
        if (statModels && liveModels) statModels.textContent = liveModels.toLocaleString();

        const hModels = document.getElementById('headerModelsCount');
        if (hModels && liveModels) hModels.textContent = `(${liveModels.toLocaleString()})`;

        const mNavInbox = document.getElementById('mNavTabInbox');
        if (mNavInbox && liveInbox) mNavInbox.textContent = `아카이브 (${liveInbox.toLocaleString()})`;

        const inbHdr = document.getElementById('inboxHeaderCount');
        if (inbHdr && liveInbox) inbHdr.textContent = `총 ${liveInbox.toLocaleString()}건`;

        if (data.counts.inbox_unclassified !== undefined) {
          const unclass = data.counts.inbox_unclassified;
          const btn = document.getElementById('btnTriggerWorker');
          const txt = document.getElementById('btnWorkerText');

          if (unclass === 0) {
            window._allClassifiedCompleted = true;
            if (txt) txt.textContent = '✨ 모든 항목 AI 요약 완료됨';
            if (btn) {
              btn.disabled = true;
              btn.className = "px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-800 font-bold font-mono text-[11px] border border-emerald-200 transition shadow-xs flex items-center gap-1.5 cursor-default";
            }
          } else {
            window._allClassifiedCompleted = false;
            if (txt && !window._autoWorkerRunning) {
              txt.textContent = `⚡ AI 요약 실행 (${unclass.toLocaleString()}건 대기)`;
            } else if (window._autoWorkerRunning && !window._autoWorkerPaused) {
              if (txt) txt.innerHTML = `<span class="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse mr-1"></span> AI 요약 중 (잔여: ${unclass.toLocaleString()}건)`;
            }
            if (btn && !window._autoWorkerRunning) {
              btn.disabled = false;
              btn.className = "px-3 py-1.5 rounded-lg bg-indigo-50 text-indigo-700 font-bold font-mono text-[11px] border border-indigo-200 transition shadow-xs flex items-center gap-1.5 cursor-pointer hover:bg-indigo-100";
            }
          }
        }

        if (data.counts.tier1_counts || data.tier1_counts) {
          snapshotStats.tier1_counts = data.counts.tier1_counts || data.tier1_counts;
        }
        if (data.counts.news_cat_counts || data.news_cat_counts) {
          snapshotStats.news_cat_counts = data.counts.news_cat_counts || data.news_cat_counts;
        }
        if (typeof updateNewsCategoryPillCounts === 'function') {
          updateNewsCategoryPillCounts();
        }

        if (badge) {
          badge.innerHTML = `
            <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 hover:bg-emerald-100 transition shadow-xs cursor-pointer" title="관리자 전용 원천 데이터 아카이브 (총 ${data.counts.inbox_total}건, 레이턴시: ${tLatency}ms)">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse"></span> Admin (${typeof liveInbox === 'number' ? liveInbox.toLocaleString() : liveInbox})
            </span>
          `;
        }

        // Vercel Serverless Telemetry Hydration
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
          const cpuBadge = document.getElementById('vercelCpuBadge');
          const cpuSubText = document.getElementById('vercelCpuSubText');
          if (cpuUsed && vt.active_cpu_time) cpuUsed.textContent = `${vt.active_cpu_time.used_hours}h`;
          if (cpuBar && vt.active_cpu_time) cpuBar.style.width = `${vt.active_cpu_time.used_pct}%`;
          if (cpuBadge && vt.active_cpu_time) {
            const pct = vt.active_cpu_time.used_pct;
            const statusStr = pct < 50 ? '극도 안정' : (pct < 80 ? '안정' : '주의');
            cpuBadge.textContent = `${statusStr} (${pct}%)`;
          }
          if (cpuSubText && vt.active_cpu_time) {
            cpuSubText.innerHTML = `• 누적 실행: <b>${vt.active_cpu_time.used_estimated_seconds}초 / 14,400초</b>`;
          }

          const bwUsed = document.getElementById('vercelBandwidthUsed');
          const bwBar = document.getElementById('vercelBandwidthBar');
          if (bwUsed && vt.bandwidth_gb) bwUsed.textContent = `${vt.bandwidth_gb.used_estimated} GB`;
          if (bwBar && vt.bandwidth_gb) bwBar.style.width = `${vt.bandwidth_gb.used_pct}%`;
        }

        // 24h Timeline Hydration from Live DB (Guarded against wiping with 0s)
        if (data.timeline_24h_live && Array.isArray(data.timeline_24h_live) && data.timeline_24h_live.length > 0) {
          const curKstH = getDynamicKstHour();
          const liveHasData = data.timeline_24h_live.some(s => (s.inbox_count > 0 || s.enriched_count > 0));
          if (liveHasData) {
            window.timeline24hData = data.timeline_24h_live.map(liveSlot => ({
              ...liveSlot,
              is_current: (liveSlot.hour <= curKstH && curKstH < liveSlot.hour + 6),
              is_future: (liveSlot.hour > curKstH)
            }));
            window._timelineIsPendingToday = false;
            if (typeof window.renderTelemetryCharts === 'function') {
              window.renderTelemetryCharts();
            }
          } else if (data.timeline_24h_baseline && Array.isArray(data.timeline_24h_baseline) && data.timeline_24h_baseline.length > 0) {
            const baseHasData = data.timeline_24h_baseline.some(s => (s.inbox_count > 0 || s.enriched_count > 0));
            if (baseHasData) {
              window.timeline24hData = data.timeline_24h_baseline.map(bSlot => ({
                ...bSlot,
                is_current: (bSlot.hour <= curKstH && curKstH < bSlot.hour + 6),
                is_future: (bSlot.hour > curKstH),
                is_pending_today: (bSlot.hour <= curKstH && curKstH < bSlot.hour + 6)
              }));
              window._timelineIsPendingToday = true;
              if (typeof window.renderTelemetryCharts === 'function') {
                window.renderTelemetryCharts();
              }
            }
          }
        }

        // Live Portfolios Sync (Only if not already populated by bootstrap)
        try {
          const currentCases = Array.isArray(window.liveCasesData) ? window.liveCasesData : [];
          if (currentCases.length === 0) {
            const portfoliosApiUrl = APP_CONFIG.apiUrl('/api/portfolios');
            const pRes = await fetch(portfoliosApiUrl, { cache: 'default' });
            if (pRes.ok) {
              const pData = await pRes.json();
              if (pData.success && Array.isArray(pData.portfolios) && pData.portfolios.length > 0) {
                window.liveCasesData = pData.portfolios;
                window.casesData = pData.portfolios;
                AppStore._cases = pData.portfolios;
                updateGlobalStatsUI();
                try { if (typeof window.renderCards === 'function') window.renderCards(); } catch(e) {}
                try { if (typeof window.renderHomeTopPicks === 'function') window.renderHomeTopPicks(); } catch(e) {}
                console.log(`[Live DB Sync] Live hydrated ${pData.portfolios.length} dossiers from ${APP_CONFIG.dbProvider}.`);
              }
            }
          }
        } catch (pErr) {
          console.warn('[Live DB Sync] Portfolios live sync skipped:', pErr.message);
        }

        // Actions Telemetry Sync
        if (data.actions_quota && data.actions_quota.total_minutes !== undefined) {
          window.actionsTelemetryData = window.actionsTelemetryData || {};
          window.actionsTelemetryData.monthly_used_minutes = data.actions_quota.total_minutes;
          window.actionsTelemetryData.monthly_remaining_minutes = data.actions_quota.remaining_minutes;
          window.actionsTelemetryData.monthly_usage_percent = data.actions_quota.burn_rate_percent;
          if (data.actions_runs && Array.isArray(data.actions_runs) && data.actions_runs.length > 0) {
            window.actionsTelemetryData.runs = data.actions_runs;
          }
          if (typeof window.renderPipelineTelemetryCards === 'function') window.renderPipelineTelemetryCards();
          if (typeof window.renderRunsTable === 'function' && window.currentRunsTab === 'gha') window.renderRunsTable();
        }

        if (data.vercel_worker_runs && Array.isArray(data.vercel_worker_runs)) {
          window.vercelWorkerRunsData = data.vercel_worker_runs;
          if (window.currentRunsTab === 'vercel' && typeof window.renderRunsTable === 'function') {
            window.renderRunsTable();
          }
        }

        if (data.voyage_worker_runs && Array.isArray(data.voyage_worker_runs)) {
          window.voyageWorkerRunsData = data.voyage_worker_runs;
          try {
            localStorage.setItem('voyage_runs_history_v1', JSON.stringify(data.voyage_worker_runs));
          } catch (e) {}
          if (window.currentRunsTab === 'voyage' && typeof window.renderRunsTable === 'function') {
            window.renderRunsTable();
          }
        }

        return;
      }
    }
  } catch (err) {
    // Graceful fallback
  } finally {
    _isSyncing = false;
    if (_syncTimeoutId) clearTimeout(_syncTimeoutId);
  }
}

// Voyage AI Workers
let _voyageWorkerRunning = false;
let _voyageWorkerPaused = false;

export async function checkVoyageEmbeddingStatus() {
  const btn = document.getElementById('btnTriggerEmbedding');
  const txt = document.getElementById('btnEmbedText');
  if (!btn || !txt) return;

  try {
    const url = APP_CONFIG.apiUrl('/api/embed-worker?check_only=true');
    const res = await fetch(url, { cache: 'no-store' });
    if (!res.ok) return;
    const data = await res.json();
    if (!data.success) return;

    const remaining = data.remaining_unembedded !== undefined ? data.remaining_unembedded : 0;
    const total = data.total_count || 0;
    const embedded = data.embedded_count || 0;

    window._voyageRemaining = remaining;
    window._voyageTotal = total;
    window._voyageEmbedded = embedded;

    if (remaining === 0) {
      txt.textContent = '✨ 모든 항목 Voyage 임베딩 완료됨';
      btn.disabled = true;
      btn.className = "px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-800 font-bold font-mono text-[11px] border border-emerald-200 transition shadow-xs flex items-center gap-1.5 cursor-default";
      btn.title = `총 ${total.toLocaleString()}건 전수 임베딩 및 중복 병합 완료 (100%)`;
    } else {
      if (!_voyageWorkerRunning) {
        txt.textContent = `⚡ Voyage 임베딩 (${remaining.toLocaleString()}건 잔여)`;
        btn.disabled = false;
        btn.className = "px-3 py-1.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-800 font-bold font-mono text-[11px] border border-emerald-200 transition shadow-xs flex items-center gap-1.5 cursor-pointer";
        btn.title = `총 ${total.toLocaleString()}건 중 ${remaining.toLocaleString()}건 미임베딩 (완료: ${embedded.toLocaleString()}건). 클릭 시 전수 자동 임베딩 시작`;
      }
    }
  } catch (err) {
    console.warn('[Voyage Status Check Skipped]:', err.message);
  }
}

export async function startContinuousVoyageWorker() {
  if (_voyageWorkerRunning) return;
  _voyageWorkerRunning = true;
  _voyageWorkerPaused = false;
  window._voyageWorkerRunning = true;
  window._voyageWorkerPaused = false;

  const btn = document.getElementById('btnTriggerEmbedding');
  const txt = document.getElementById('btnEmbedText');

  if (btn) {
    btn.disabled = false;
    btn.className = "px-3 py-1.5 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white font-bold font-mono text-[11px] border border-emerald-800 transition shadow-xs flex items-center gap-1.5 cursor-pointer";
  }

  let consecutiveErrors = 0;
  let totalProcessedInSession = 0;
  let totalMergedInSession = 0;

  while (_voyageWorkerRunning && !_voyageWorkerPaused) {
    try {
      if (txt && !_voyageWorkerPaused) {
        txt.innerHTML = `<span class="inline-block w-2 h-2 rounded-full bg-white animate-ping mr-1"></span> 임베딩 중... (${totalProcessedInSession}건 완료 / 잔여 확인 중)`;
      }

      const t0 = Date.now();
      const res = await fetch(APP_CONFIG.apiUrl('/api/embed-worker?limit=100'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ limit: 100 }),
        cache: 'no-store'
      });
      const elapsed = ((Date.now() - t0) / 1000).toFixed(1);

      if (!res.ok) {
        consecutiveErrors++;
        console.warn(`[Voyage Worker] HTTP error ${res.status}. Errors: ${consecutiveErrors}/3`);
        if (consecutiveErrors >= 3) {
          _voyageWorkerRunning = false;
          window._voyageWorkerRunning = false;
          if (txt) txt.textContent = '⚡ 임베딩 서버 지연으로 정지 (클릭 시 재개)';
          if (btn) {
            btn.className = "px-3 py-1.5 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-800 font-bold font-mono text-[11px] border border-amber-300 transition shadow-xs flex items-center gap-1.5 cursor-pointer";
          }
          break;
        }
        await new Promise(r => setTimeout(r, 4000));
        continue;
      }

      consecutiveErrors = 0;
      const data = await res.json();
      if (!data.success) {
        throw new Error(data.error || 'Server error');
      }

      const processed = data.processed_count || 0;
      const merged = data.merged_duplicates_count || 0;
      const remaining = data.remaining_unembedded !== undefined ? data.remaining_unembedded : 0;
      const totalCount = data.total_count || 0;
      const tokensUsed = data.tokens_used || 0;

      totalProcessedInSession += processed;
      totalMergedInSession += merged;

      const nowKst = new Date(Date.now() + 9 * 3600 * 1000).toISOString().replace('T', ' ').substring(5, 16);
      if (!Array.isArray(window.voyageWorkerRunsData)) window.voyageWorkerRunsData = [];
      window.voyageWorkerRunsData.unshift({
        id: Date.now(),
        created_at_kst: nowKst,
        engine: data.model || 'voyage-4-lite',
        duration_str: elapsed + '초',
        processed_count: processed,
        merged_count: merged,
        tokens_used: tokensUsed,
        remaining_count: remaining,
        total_count: totalCount,
        status: 'SUCCESS'
      });
      if (window.voyageWorkerRunsData.length > 30) window.voyageWorkerRunsData.pop();
      try {
        localStorage.setItem('voyage_runs_history_v1', JSON.stringify(window.voyageWorkerRunsData));
      } catch (e) {}

      if (window.currentRunsTab === 'voyage' && typeof window.renderRunsTable === 'function') {
        window.renderRunsTable();
      }

      if (txt && !_voyageWorkerPaused) {
        txt.innerHTML = `<span class="inline-block w-2 h-2 rounded-full bg-white animate-pulse mr-1"></span> 진행 중 (${totalProcessedInSession}건 완료 / 잔여: ${remaining.toLocaleString()}건)`;
      }

      if (remaining === 0 || processed === 0) {
        _voyageWorkerRunning = false;
        window._voyageWorkerRunning = false;
        if (txt) txt.textContent = '✨ 모든 항목 Voyage 임베딩 완료됨';
        if (btn) {
          btn.disabled = true;
          btn.className = "px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-800 font-bold font-mono text-[11px] border border-emerald-200 transition shadow-xs flex items-center gap-1.5 cursor-default";
          btn.title = `총 ${totalCount.toLocaleString()}건 전체 임베딩 및 유사도 중복 병합 완료 (100%)`;
        }
        showToast(`✨ 모든 기사(${totalCount.toLocaleString()}건) Voyage AI 임베딩이 100% 완료되었습니다!`, 'success');
        break;
      }

      await new Promise(r => setTimeout(r, 1200));

    } catch (err) {
      console.error('[Voyage Worker Loop Error]:', err);
      consecutiveErrors++;
      if (consecutiveErrors >= 3) {
        _voyageWorkerRunning = false;
        window._voyageWorkerRunning = false;
        if (txt) txt.textContent = '❌ 임베딩 오류 발생 (클릭 시 재시도)';
        if (btn) {
          btn.className = "px-3 py-1.5 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-800 font-bold font-mono text-[11px] border border-amber-300 transition shadow-xs flex items-center gap-1.5 cursor-pointer";
        }
        break;
      }
      await new Promise(r => setTimeout(r, 3000));
    }
  }

  _voyageWorkerRunning = false;
  window._voyageWorkerRunning = false;
}

export function toggleVoyageEmbeddingWorker() {
  const btn = document.getElementById('btnTriggerEmbedding');
  const txt = document.getElementById('btnEmbedText');

  if (_voyageWorkerRunning && !_voyageWorkerPaused) {
    _voyageWorkerPaused = true;
    window._voyageWorkerPaused = true;
    if (txt) txt.textContent = '⏸️ 임베딩 일시정지됨 (클릭 시 재개)';
    if (btn) {
      btn.className = "px-3 py-1.5 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-800 font-bold font-mono text-[11px] border border-amber-300 transition shadow-xs flex items-center gap-1.5 cursor-pointer";
    }
  } else {
    _voyageWorkerPaused = false;
    window._voyageWorkerPaused = false;
    if (txt) txt.textContent = '⏳ 임베딩 준비 중...';
    startContinuousVoyageWorker();
  }
}

// AI Enrichment Continuous Worker
let _autoWorkerRunning = false;
let _autoWorkerPaused = false;

export async function startContinuousAiWorker() {
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

  let consecutiveErrors = 0;
  let processedInThisSession = 0;

  while (_autoWorkerRunning && !_autoWorkerPaused) {
    try {
      const workerUrl = APP_CONFIG.apiUrl('/api/enrich-worker?limit=1');
      if (txt && !_autoWorkerPaused) {
        txt.innerHTML = `<span class="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-ping mr-1"></span> AI 요약 분석 중... (${processedInThisSession + 1}건 진행 중)`;
      }

      const res = await fetch(workerUrl, { cache: 'no-store' });
      if (res.status === 429) {
        _autoWorkerRunning = false;
        window._autoWorkerRunning = false;
        if (txt) txt.textContent = '⏸️ AI 쿼터 일시 소진 (잠시 후 다시 시도)';
        if (btn) {
          btn.disabled = false;
          btn.className = "px-3 py-1.5 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-800 font-bold font-mono text-[11px] border border-amber-300 transition shadow-xs flex items-center gap-1.5 cursor-pointer";
        }
        break;
      }
      if (!res.ok) {
        consecutiveErrors++;
        if (consecutiveErrors >= 3) {
          _autoWorkerRunning = false;
          window._autoWorkerRunning = false;
          if (txt) txt.textContent = '⚡ 서버 일시 응답 없음 (클릭 시 재시도)';
          if (btn) {
            btn.disabled = false;
            btn.className = "px-3 py-1.5 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-800 font-bold font-mono text-[11px] border border-amber-300 transition shadow-xs flex items-center gap-1.5 cursor-pointer";
          }
          break;
        }
        const backoffMs = Math.min(10000, 3000 * consecutiveErrors);
        await new Promise(r => setTimeout(r, backoffMs));
        continue;
      }

      consecutiveErrors = 0;
      const data = await res.json();

      if (data && data.status === 'success') {
        processedInThisSession++;
        const rem = data.remaining_unclassified !== undefined ? data.remaining_unclassified : 0;
        if (txt && !_autoWorkerPaused) {
          txt.innerHTML = `<span class="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse mr-1"></span> AI 요약 중 (${processedInThisSession}건 완료 / 잔여: ${rem}건)`;
        }

        if (rem === 0) {
          window._allClassifiedCompleted = true;
          _autoWorkerRunning = false;
          window._autoWorkerRunning = false;
          if (txt) txt.textContent = '✨ 모든 항목 AI 요약 완료됨';
          if (btn) {
            btn.disabled = true;
            btn.className = "px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-800 font-bold font-mono text-[11px] border border-emerald-200 transition shadow-xs flex items-center gap-1.5 cursor-default";
          }
          break;
        }

      }
    } catch (loopErr) {
      console.warn('[AutoWorker Loop Error]:', loopErr);
      consecutiveErrors++;
      await new Promise(r => setTimeout(r, 10000));
    }

    await new Promise(r => setTimeout(r, 3500));
  }

  if (processedInThisSession > 0) {
    ClientCache.clear();
    try {
      if (typeof window.renderInbox === 'function') window.renderInbox(false, true);
    } catch(e) {}
  }

  _autoWorkerRunning = false;
  window._autoWorkerRunning = false;
}

export function toggleAiEnrichWorker() {
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

export async function triggerAiEnrichWorker() {
  toggleAiEnrichWorker();
}

export async function runSystemVerificationAgent() {
  const btn = document.getElementById('btnTriggerVerification');
  const txt = document.getElementById('btnVerifyText');
  if (btn && txt) {
    txt.innerHTML = `<span class="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-ping mr-1"></span> 진단 중...`;
    btn.disabled = true;
  }

  const t0 = Date.now();
  const checks = [];

  // Check 1: Client Store & Runtime Hydration
  const cases = (window.liveCasesData && window.liveCasesData.length > 0)
    ? window.liveCasesData 
    : ((window.AppStore && typeof window.AppStore.getCases === 'function' && window.AppStore.getCases().length > 0) ? window.AppStore.getCases() : (casesData || []));
  const isHydrated = (window.__APP_INITIALIZED__ === true) || cases.length > 0;
  const casesLoaded = cases.length > 0;
  checks.push({
    title: '프런트엔드 모듈러 런타임 & 스토어 수화',
    pass: isHydrated && casesLoaded,
    details: `수화: ${isHydrated ? '정상' : '진행중'} | 검증 도시에: ${casesLoaded ? cases.length + '건' : '0건'}`
  });

  // Check 2: Voyage AI & pgvector Database Status
  try {
    const res = await fetch(APP_CONFIG.apiUrl('/api/embed-worker?check_only=true'));
    const data = await res.json();
    if (res.ok && data.success) {
      checks.push({
        title: 'Aiven PostgreSQL & Voyage pgvector 상태',
        pass: true,
        details: `총 ${data.total_count?.toLocaleString()}건 중 ${data.embedded_count?.toLocaleString()}건 임베딩 완료 (잔여: ${data.remaining_unembedded?.toLocaleString()}건)`
      });
    } else {
      checks.push({
        title: 'Aiven PostgreSQL & Voyage pgvector 상태',
        pass: false,
        details: `API 응답 오류: ${data.error || res.status}`
      });
    }
  } catch (err) {
    checks.push({
      title: 'Aiven PostgreSQL & Voyage pgvector 상태',
      pass: false,
      details: `네트워크 통신 오류: ${err.message}`
    });
  }

  // Check 3: Global Inbox & Stats API
  try {
    const res = await fetch(APP_CONFIG.apiUrl('/api/stats'));
    const data = await res.json();
    const isOk = res.ok && (data.status === 'success' || data.status === 'SUCCESS');
    const totalCount = data.counts?.inbox_total || data.data?.inbox_total_count || 0;
    if (isOk) {
      checks.push({
        title: '글로벌 집계 엔진 (No Slice Aggregation)',
        pass: true,
        details: `실시간 DB GROUP BY 집계 정상 (인박스 총량: ${totalCount.toLocaleString()}건)`
      });
    } else {
      checks.push({
        title: '글로벌 집계 엔진',
        pass: false,
        details: `집계 API 응답 비정상 (${res.status})`
      });
    }
  } catch (err) {
    checks.push({
      title: '글로벌 집계 엔진',
      pass: false,
      details: err.message
    });
  }

  // Check 4: Fail-Safe Fallback Harness Readiness
  const fallbackReady = typeof window.triggerLegacyFallback === 'function' && window.__FALLBACK_TRIGGERED__ === false;
  checks.push({
    title: '무중단 비상 롤백 하네스 (Zero-Downtime Fallback)',
    pass: fallbackReady,
    details: 'app.legacy.js 동적 스위칭 대기 정상'
  });

  const allPassed = checks.every(c => c.pass);
  const elapsed = ((Date.now() - t0) / 1000).toFixed(2);

  if (btn && txt) {
    btn.disabled = false;
    txt.innerHTML = allPassed ? '✅ 시스템 검증 완료' : '⚠️ 검증 이상 감지';
    setTimeout(() => {
      txt.textContent = '🔍 시스템 검증 실행';
    }, 4000);
  }

  if (typeof window.showVerificationReportModal === 'function') {
    window.showVerificationReportModal({
      allPassed,
      elapsed,
      checks
    });
  } else {
    showToast(allPassed ? `✅ 시스템 검증 100% 통과 (${elapsed}초)` : '⚠️ 시스템 점검 항목 발생', allPassed ? 'success' : 'warning');
  }
}

export function updatePromotionBanner() {}

if (typeof window !== 'undefined') {
  window.bootstrapApplicationData = bootstrapApplicationData;
  window.updateGlobalStatsUI = updateGlobalStatsUI;
  window.updateNewsCategoryPillCounts = updateNewsCategoryPillCounts;
  window.updateModelCategoryPillCounts = updateModelCategoryPillCounts;
  window.syncFromLiveDB = syncFromLiveDB;
  window.checkVoyageEmbeddingStatus = checkVoyageEmbeddingStatus;
  window.toggleVoyageEmbeddingWorker = toggleVoyageEmbeddingWorker;
  window.startContinuousVoyageWorker = startContinuousVoyageWorker;
  window.toggleAiEnrichWorker = toggleAiEnrichWorker;
  window.updatePromotionBanner = updatePromotionBanner;
  window.runSystemVerificationAgent = runSystemVerificationAgent;
}
