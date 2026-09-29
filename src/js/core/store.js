/**
 * ==============================================================================
 * Central Reactive Application Store (Single Source of Truth)
 * Framework-Agnostic State Management (Compatible with React useSyncExternalStore / Zustand)
 * ==============================================================================
 */

// Global hydrated collections
export let casesData = [];
export let modelsData = [];
export let newsData = [];
export let inboxData = [];
export let adminData = {};
export let graphData = { nodes: [], links: [] };
export let timeline24hData = [];
export let actionsTelemetryData = {};
export let trend6hData = {};
export let trendRadarData = {};
export let snapshotStats = {};

export let liveCasesData = casesData;
export let liveModelsData = modelsData;
export let liveInboxData = inboxData;
export let liveNewsData = newsData;
export let liveAnalysesData = [];

// Filter & Navigation states
export let currentLang = 'KO';
export let currentView = 'home';
export let currentMode = 'ALL';
export let currentDomain = 'ALL';
export let currentSort = 'date-audit-desc';
export let searchQuery = '';

export let currentInboxSource = 'ALL';
export let currentInboxLang = 'ALL';
export let currentInboxType = 'ALL';
export let currentInboxTech = 'ALL';
export let currentInboxSort = 'date-audit-desc';
export let inboxSearchQuery = '';
export let isFamilyGroupingActive = true;
export let currentGraphType = 'ALL';
export let simulationRef = null;

// News filter state
export let currentNewsTier1 = 'ALL';
export let currentNewsTier2 = 'ALL';
export let currentNewsSort = 'date-audit-desc';
export let currentNewsFacet = 'ALL';
export let currentNewsSource = 'ALL';
export let currentNewsSearch = '';
export let targetSelectedInboxId = '';

// Models filter state
export let currentModelsFamily = 'ALL';
export let currentModelsArtifact = 'ALL';
export let currentModelsModality = 'ALL';
export let currentModelsSort = 'date-audit-desc';
export let modelsSearchQuery = '';

// Global Pagination State (PORTFOLIO_PAGE_SIZE = 10 for clean decade pagination)
export const PAGE_SIZE = 15;
export const PORTFOLIO_PAGE_SIZE = 10;
export let currentPortfolioPage = 1;
export let currentModelsPage = 1;
export let currentNewsPage = 1;
export let currentInboxPage = 1;

// Queued item IDs set
export const queuedItemIds = new Set(
  typeof localStorage !== 'undefined'
    ? JSON.parse(localStorage.getItem('queued_factchecks') || '[]')
    : []
);

// Reactive listeners
const _listeners = new Set();

export function subscribe(listener) {
  _listeners.add(listener);
  return () => _listeners.delete(listener);
}

export function notifySubscribers() {
  _listeners.forEach(fn => {
    try { fn(AppStore.getState()); } catch (e) { console.error('[Store Subscriber Error]', e); }
  });
}

export const AppStore = {
  _itemsMap: new Map(),
  _cases: [],
  _models: [],
  _news: [],
  _inbox: [],

  init(data) {
    if (!data) return;
    this._itemsMap.clear();
    this._cases = Array.isArray(data) ? data : (data.cases || []);
    this._models = data.model_items || data.models || [];
    this._news = data.news_items || data.news || [];
    this._inbox = data.inbox_items || data.inbox || [];

    // JEV Deterministic Indexing (Preserve facet_type & is_model)
    this._models.forEach(it => { it.is_model = true; it.is_news = false; });
    this._news.forEach(it => {
      if (it.is_model === undefined) {
        const plat = (it.source_platform || '').toLowerCase();
        const fam = (it.model_family || '').toLowerCase();
        const art = (it.artifact_type || '').toLowerCase();
        const cat = (it.category_primary || '').toLowerCase();
        it.is_model = it.facet_type === 'MODEL' || (fam.length > 0 && fam !== 'standalone') || plat.includes('model') || plat.includes('space') || art.includes('weight') || cat.includes('model');
      }
      if (it.is_news === undefined) it.is_news = !it.is_model;
    });
    this._inbox.forEach(it => {
      if (it.is_model === undefined) it.is_model = !!(it.model_family || it.artifact_type || (it.category_primary === 'MODEL_RELEASE'));
      if (it.is_news === undefined) it.is_news = !it.is_model;
    });

    // Centralized index across all harvested candidates, news, and AI models
    [...this._inbox, ...this._news, ...this._models].forEach(it => {
      const id = it.inbox_id || it.id;
      if (id && !this._itemsMap.has(id)) {
        this._itemsMap.set(id, it);
      }
    });

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

    this._syncGlobals();
    notifySubscribers();
  },

  getItem(id) {
    return this._itemsMap.get(id);
  },

  updateItem(id, patch) {
    const it = this._itemsMap.get(id);
    if (it && patch) {
      Object.assign(it, patch);
      this._syncGlobals();
      notifySubscribers();
    }
  },

  getCases() { return this._cases; },
  getModels() { return this._models; },
  getNews() { return this._news; },
  getInbox() { return this._inbox; },

  appendArchive(archiveData) {
    if (!archiveData) return;
    const mergeItems = (existingList, incomingList) => {
      if (!Array.isArray(incomingList)) return;
      const existingIds = new Set(existingList.map(it => it.inbox_id || it.id));
      for (const it of incomingList) {
        const id = it.inbox_id || it.id;
        if (id && !existingIds.has(id)) {
          existingList.push(it);
          existingIds.add(id);
        }
        if (id && !this._itemsMap.has(id)) {
          this._itemsMap.set(id, it);
        }
      }
    };

    mergeItems(this._inbox, archiveData.inbox_items);
    mergeItems(this._news, archiveData.news_items);
    mergeItems(this._models, archiveData.model_items);

    liveInboxData = this._inbox;
    liveNewsData = this._news;
    liveModelsData = this._models;
    inboxData = this._inbox;
    newsData = this._news;
    modelsData = this._models;

    this._syncGlobals();
    notifySubscribers();
  },

  getState() {
    return {
      cases: this._cases,
      models: this._models,
      news: this._news,
      inbox: this._inbox,
      currentLang,
      currentView,
      currentPortfolioPage,
      currentNewsPage,
      currentModelsPage,
      currentInboxPage
    };
  },

  _syncGlobals() {
    if (typeof window === 'undefined') return;
    window.casesData = casesData;
    window.modelsData = modelsData;
    window.newsData = newsData;
    window.inboxData = inboxData;
    window.liveCasesData = liveCasesData;
    window.liveModelsData = liveModelsData;
    window.liveNewsData = liveNewsData;
    window.liveInboxData = liveInboxData;
    window.snapshotStats = snapshotStats;
    window.adminData = adminData;
    window.graphData = graphData;
    window.timeline24hData = timeline24hData;
    window.actionsTelemetryData = actionsTelemetryData;
    window.trend6hData = trend6hData;
    window.trendRadarData = trendRadarData;
  },

  setCases(cases) {
    if (!Array.isArray(cases)) return;
    this._cases = cases;
    casesData = cases;
    liveCasesData = cases;
    this._syncGlobals();
    notifySubscribers();
  },

  setGraphData(g) {
    if (!g) return;
    graphData = g;
    this._syncGlobals();
  }
};

export function setLiveCases(cases) {
  casesData = cases;
  liveCasesData = cases;
  AppStore._cases = cases;
  AppStore._syncGlobals();
}

export function setLiveGraph(g) {
  graphData = g;
  AppStore._syncGlobals();
}

// State mutation helpers
export function setGlobalLang(lang) { currentLang = lang; if (typeof window !== 'undefined') window.currentLang = lang; }
export function setGlobalView(view) { currentView = view; if (typeof window !== 'undefined') window.currentView = view; }
export function setGlobalMode(m) { currentMode = m; if (typeof window !== 'undefined') window.currentMode = m; }
export function setGlobalDomain(d) { currentDomain = d; if (typeof window !== 'undefined') window.currentDomain = d; }
export function setGlobalSort(s) { currentSort = s; if (typeof window !== 'undefined') window.currentSort = s; }
export function setGlobalSearch(q) { searchQuery = q; if (typeof window !== 'undefined') window.searchQuery = q; }

export function setPortfolioPage(p) { currentPortfolioPage = p; if (typeof window !== 'undefined') window.currentPortfolioPage = p; }
export function setModelsPage(p) { currentModelsPage = p; if (typeof window !== 'undefined') window.currentModelsPage = p; }
export function setNewsPage(p) { currentNewsPage = p; if (typeof window !== 'undefined') window.currentNewsPage = p; }
export function setInboxPage(p) { currentInboxPage = p; if (typeof window !== 'undefined') window.currentInboxPage = p; }

export function setNewsTier1(v) { currentNewsTier1 = v; if (typeof window !== 'undefined') window.currentNewsTier1 = v; }
export function setNewsTier2(v) { currentNewsTier2 = v; if (typeof window !== 'undefined') window.currentNewsTier2 = v; }
export function setNewsSortVal(v) { currentNewsSort = v; if (typeof window !== 'undefined') window.currentNewsSort = v; }
export function setNewsFacet(v) { currentNewsFacet = v; if (typeof window !== 'undefined') window.currentNewsFacet = v; }
export function setNewsSource(v) { currentNewsSource = v; if (typeof window !== 'undefined') window.currentNewsSource = v; }
export function setNewsSearchVal(v) { currentNewsSearch = v; if (typeof window !== 'undefined') window.currentNewsSearch = v; }
export function setTargetSelectedInboxId(v) { targetSelectedInboxId = v; if (typeof window !== 'undefined') window.targetSelectedInboxId = v; }

export function setModelsFamily(v) { currentModelsFamily = v; if (typeof window !== 'undefined') window.currentModelsFamily = v; }
export function setModelsArtifact(v) { currentModelsArtifact = v; if (typeof window !== 'undefined') window.currentModelsArtifact = v; }
export function setModelsModality(v) { currentModelsModality = v; if (typeof window !== 'undefined') window.currentModelsModality = v; }
export function setModelsSortVal(v) { currentModelsSort = v; if (typeof window !== 'undefined') window.currentModelsSort = v; }
export function setModelsSearchQuery(v) { modelsSearchQuery = v; if (typeof window !== 'undefined') window.modelsSearchQuery = v; }

export function setInboxSource(v) { currentInboxSource = v; if (typeof window !== 'undefined') window.currentInboxSource = v; }
export function setInboxLang(v) { currentInboxLang = v; if (typeof window !== 'undefined') window.currentInboxLang = v; }
export function setInboxType(v) { currentInboxType = v; if (typeof window !== 'undefined') window.currentInboxType = v; }
export function setInboxTech(v) { currentInboxTech = v; if (typeof window !== 'undefined') window.currentInboxTech = v; }
export function setInboxSortVal(v) { currentInboxSort = v; if (typeof window !== 'undefined') window.currentInboxSort = v; }
export function setInboxSearchQuery(v) { inboxSearchQuery = v; if (typeof window !== 'undefined') window.inboxSearchQuery = v; }

export function setSimulationRef(ref) { simulationRef = ref; if (typeof window !== 'undefined') window.simulationRef = ref; }

if (typeof window !== 'undefined') {
  window.AppStore = AppStore;
  window.subscribeStore = subscribe;
  window.PAGE_SIZE = PAGE_SIZE;
  window.PORTFOLIO_PAGE_SIZE = PORTFOLIO_PAGE_SIZE;
  window.queuedItemIds = queuedItemIds;
  AppStore._syncGlobals();
}
