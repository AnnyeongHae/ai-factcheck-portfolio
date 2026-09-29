/**
 * ==============================================================================
 * Main Application Entry Point (Modular Architecture SSOT)
 * Bundles and coordinates all modules, provides backward compatibility window globals,
 * and handles fail-safe initialization.
 * ==============================================================================
 */

// Core
import { APP_CONFIG, API_BASE, ROUTES } from './core/config.js';
import {
  AppStore,
  subscribe,
  casesData,
  modelsData,
  newsData,
  inboxData,
  liveCasesData,
  liveModelsData,
  liveNewsData,
  liveInboxData,
  currentLang,
  currentView,
  currentPortfolioPage,
  currentModelsPage,
  currentNewsPage,
  currentInboxPage,
  PAGE_SIZE,
  PORTFOLIO_PAGE_SIZE,
  queuedItemIds
} from './core/store.js';
import { i18n, setLanguage } from './core/i18n.js';
import {
  bootstrapApplicationData,
  checkVoyageEmbeddingStatus,
  toggleVoyageEmbeddingWorker,
  startContinuousVoyageWorker,
  startContinuousAiWorker,
  toggleAiEnrichWorker,
  triggerAiEnrichWorker,
  updateGlobalStatsUI,
  runSystemVerificationAgent
} from './core/api.js';

// Utils
import { detectSourceLang } from './utils/languageDetector.js';
import {
  formatCleanMetricVal,
  calculateStandardizedViralScore,
  getPlatformImpactWeight,
  cleanPlatformName,
  getPrimaryImpactPlatform
} from './utils/metricFormatter.js';
import {
  parseItemTimestamp,
  formatDateTime,
  formatDateTimeCompact,
  formatKstMonthDay,
  formatModelAttribution,
  getDynamicKstHour,
  getDynamicKstDate,
  getDynamicKstSession
} from './utils/dateTime.js';
import { sortCollection } from './utils/collectionSorter.js';
import { extractStoryEntity, clusterFeedItems } from './utils/feedClustering.js';
import {
  cleanStealthUrl,
  stealthNavigate,
  initStealthLinkInterceptor
} from './utils/stealthUrl.js';

// Components
import {
  renderPagination,
  changePortfolioPage,
  changeModelsPage,
  changeNewsPage,
  changeInboxPage
} from './components/pagination.js';
import { showToast } from './components/toast.js';
import {
  buildMultiSourceCluster,
  toggleSourcePopover,
  toggleClusterPopover
} from './components/popover.js';
import {
  openModal,
  openCaseModal,
  closeModal,
  showVerificationReportModal
} from './components/modal.js';
import {
  createNewsCardElement,
  getLocalizedContent,
  toggleNewsComments,
  renderHookCallout,
  renderAiTakeaways,
  renderRelatedDossierButton,
  renderCommentsAccordion,
  renderCardStandardFooter
} from './components/newsCard.js';
import {
  renderCards,
  setModeFilter,
  setDomainFilter,
  changeSort,
  clearSearch
} from './components/portfolioCard.js';
import {
  renderModels,
  setModelsSort,
  setModelsArtifactFilter,
  setModelsModalityFilter,
  setModelsFamilyFilter,
  toggleFamilyGrouping,
  initModelsSearchListener
} from './components/modelsCard.js';
import {
  renderTelemetryCharts,
  renderPipelineTelemetryCards,
  renderRunsTable,
  updateCronCountdown,
  switchRunLogsTab
} from './components/telemetry.js';
import {
  initCitationGraph,
  filterGraphGroup
} from './components/citationGraph.js';

// Views
import {
  switchView,
  resetAllFiltersAndSearch,
  handleHashRoute,
  initRouter
} from './views/router.js';
import {
  renderHomeTopPicks,
  switchRadarSession,
  navigateFromRadar,
  renderRadarSession
} from './views/homeView.js';
import {
  renderNews,
  renderNewsGridItems,
  renderNewsSkeleton,
  preloadTopNewsFilters,
  setNewsCategoryFilter,
  setNewsTier2Filter,
  setNewsFacetFilter,
  setNewsSourceFilter,
  setNewsSort,
  handleNewsSearch,
  handleNewsSearchImmediate,
  clearNewsSearch,
  updateSearchClearBtn
} from './views/newsView.js';
import {
  renderInbox,
  setInboxSort,
  setInboxLangFilter,
  setInboxTypeFilter,
  setInboxTechFilter,
  setInboxSourceFilter,
  toggleQueueItem
} from './views/inboxView.js';

// ================= GLOBAL BINDINGS (100% Backward Compatibility) =================
if (typeof window !== 'undefined') {
  // Store & Config
  window.APP_CONFIG = APP_CONFIG;
  window.API_BASE = API_BASE;
  window.ROUTES = ROUTES;
  window.AppStore = AppStore;

  // Language & I18n
  window.i18n = i18n;
  window.setLanguage = setLanguage;

  // Router & Navigation
  window.switchView = switchView;
  window.resetAllFiltersAndSearch = resetAllFiltersAndSearch;
  window.handleHashRoute = handleHashRoute;

  // Home View
  window.renderHomeTopPicks = renderHomeTopPicks;
  window.switchRadarSession = switchRadarSession;
  window.navigateFromRadar = navigateFromRadar;
  window.renderRadarSession = renderRadarSession;

  // Portfolio
  window.renderCards = renderCards;
  window.setModeFilter = setModeFilter;
  window.setDomainFilter = setDomainFilter;
  window.changeSort = changeSort;
  window.clearSearch = clearSearch;

  // Models
  window.renderModels = renderModels;
  window.setModelsSort = setModelsSort;
  window.setModelsArtifactFilter = setModelsArtifactFilter;
  window.setModelsModalityFilter = setModelsModalityFilter;
  window.setModelsFamilyFilter = setModelsFamilyFilter;
  window.toggleFamilyGrouping = toggleFamilyGrouping;

  // News
  window.renderNews = renderNews;
  window.setNewsCategoryFilter = setNewsCategoryFilter;
  window.setNewsTier2Filter = setNewsTier2Filter;
  window.setNewsFacetFilter = setNewsFacetFilter;
  window.switchNewsFacet = function(facet) {
    switchView('news');
    setNewsFacetFilter(facet || 'ALL');
  };
  window.setNewsSourceFilter = setNewsSourceFilter;
  window.setNewsSort = setNewsSort;
  window.handleNewsSearch = handleNewsSearch;
  window.handleNewsSearchImmediate = handleNewsSearchImmediate;
  window.clearNewsSearch = clearNewsSearch;
  window.updateSearchClearBtn = updateSearchClearBtn;

  // Inbox
  window.renderInbox = renderInbox;
  window.setInboxSort = setInboxSort;
  window.setInboxLangFilter = setInboxLangFilter;
  window.setInboxTypeFilter = setInboxTypeFilter;
  window.setInboxTechFilter = setInboxTechFilter;
  window.setInboxSourceFilter = setInboxSourceFilter;
  window.toggleQueueItem = toggleQueueItem;

  // Pagination
  window.changePortfolioPage = changePortfolioPage;
  window.changeModelsPage = changeModelsPage;
  window.changeNewsPage = changeNewsPage;
  window.changeInboxPage = changeInboxPage;

  // Modal & Popover
  window.openModal = openModal;
  window.openCaseModal = openCaseModal;
  window.closeModal = closeModal;
  window.toggleSourcePopover = toggleSourcePopover;
  window.toggleClusterPopover = toggleClusterPopover;
  window.toggleNewsComments = toggleNewsComments;

  // Telemetry & Graph
  window.renderTelemetryCharts = renderTelemetryCharts;
  window.renderPipelineTelemetryCards = renderPipelineTelemetryCards;
  window.renderRunsTable = renderRunsTable;
  window.updateCronCountdown = updateCronCountdown;
  window.switchRunLogsTab = switchRunLogsTab;
  window.filterLogsByRunner = switchRunLogsTab;
  window.initCitationGraph = initCitationGraph;
  window.filterGraphGroup = filterGraphGroup;
  window.showToast = showToast;

  // Workers & Verification
  window.checkVoyageEmbeddingStatus = checkVoyageEmbeddingStatus;
  window.toggleVoyageEmbeddingWorker = toggleVoyageEmbeddingWorker;
  window.startContinuousVoyageWorker = startContinuousVoyageWorker;
  window.toggleAiEnrichWorker = toggleAiEnrichWorker;
  window.drainAiEnrichmentWorker = startContinuousAiWorker;
  window.startContinuousAiWorker = startContinuousAiWorker;
  window.triggerAiEnrichWorker = triggerAiEnrichWorker;
  window.updateGlobalStatsUI = updateGlobalStatsUI;
  window.runSystemVerificationAgent = runSystemVerificationAgent;
  window.showVerificationReportModal = showVerificationReportModal;

  // Stealth
  window.cleanStealthUrl = cleanStealthUrl;
  window.stealthNavigate = stealthNavigate;

  // Filter out noisy third-party browser extension message channel disconnections
  window.addEventListener('unhandledrejection', (event) => {
    if (event?.reason?.message && event.reason.message.includes('message channel closed before a response was received')) {
      event.preventDefault();
    }
  });

  // Attach search listeners
  const inboxSearchEl = document.getElementById('inboxSearchInput');
  if (inboxSearchEl) {
    inboxSearchEl.addEventListener('input', (e) => {
      window.currentInboxPage = 1;
      window.inboxSearchQuery = e.target.value;
      renderInbox();
    });
  }

  const searchEl = document.getElementById('searchInput');
  if (searchEl) {
    searchEl.addEventListener('input', (e) => {
      window.searchQuery = e.target.value;
      const clearBtn = document.getElementById('clearSearchBtn');
      if (clearBtn) clearBtn.classList.toggle('hidden', !e.target.value);
      renderCards();
    });
  }

  // Stealth interceptor
  initStealthLinkInterceptor();

  // Router init
  initRouter();

  console.log('[App] 🚀 Modular architecture components registered.');
}

// Bootstrap application on load
if (typeof document !== 'undefined') {
  const initApp = async () => {
    try {
      await bootstrapApplicationData();
    } catch (err) {
      console.warn('[App] Bootstrap warning:', err);
    }
    // Saved language preference
    const savedLang = localStorage.getItem('factcheck_lang') || 'KO';
    setLanguage(savedLang);

    // Initial cron interval
    setInterval(updateCronCountdown, 1000);
    updateCronCountdown();

    // SWR preload top news filters
    setTimeout(preloadTopNewsFilters, 1500);

    // Live stats sync
    setTimeout(updateGlobalStatsUI, 2000);

    // Initial Voyage embedding status check
    setTimeout(checkVoyageEmbeddingStatus, 800);

    // Signal modular app ready and hydrated
    window.__APP_INITIALIZED__ = true;
    console.log('[App] 🚀 Modular architecture hydrated and fully ready.');
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
  } else {
    initApp();
  }
}
