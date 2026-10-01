/**
 * ==============================================================================
 * Universal Application Router & View Switcher (Hash Routing + Browser History)
 * ==============================================================================
 */

import {
  currentView,
  casesData,
  liveCasesData,
  currentPortfolioPage,
  currentNewsPage,
  currentModelsPage,
  currentInboxPage
} from '../core/store.js';
import { ROUTES } from '../core/config.js';
import { renderCards } from '../components/portfolioCard.js';
import { renderModels } from '../components/modelsCard.js';
import {
  renderTelemetryCharts,
  renderPipelineTelemetryCards,
  renderRunsTable,
  updateCronCountdown
} from '../components/telemetry.js';
import { initCitationGraph } from '../components/citationGraph.js';
import { openModal, closeModal } from '../components/modal.js';
import {
  changePortfolioPage,
  changeModelsPage,
  changeNewsPage,
  changeInboxPage
} from '../components/pagination.js';
import { renderHomeTopPicks } from './homeView.js';
import { renderNews } from './newsView.js';
import { renderInbox } from './inboxView.js';

export function resetAllFiltersAndSearch() {
  // 1. Reset Portfolio search & filters
  window.currentPortfolioPage = 1;
  window.searchQuery = '';
  window.currentMode = 'ALL';
  window.currentDomain = 'ALL';
  window.currentSort = 'date-audit-desc';
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
  window.currentNewsPage = 1;
  window.currentNewsSearch = '';
  window.currentNewsTier1 = 'ALL';
  window.currentNewsTier2 = 'ALL';
  window.currentNewsSource = 'ALL';
  window.currentNewsSort = 'date-audit-desc';
  const nInput = document.getElementById('newsSearchInput');
  if (nInput) nInput.value = '';
  const nSort = document.getElementById('newsSortSelect');
  if (nSort) nSort.value = 'date-audit-desc';
  document.querySelectorAll('.news-cat-pill').forEach(btn => {
    if (btn.getAttribute('data-cat') === 'ALL') {
      btn.className = 'news-cat-pill active px-3 py-1.5 rounded-xl text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap cursor-pointer';
    } else {
      btn.className = 'news-cat-pill px-3 py-1.5 rounded-xl text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap cursor-pointer';
    }
  });
  document.querySelectorAll('.news-t2-pill').forEach(btn => {
    if (btn.getAttribute('data-t2') === 'ALL') {
      btn.className = 'news-t2-pill active px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap cursor-pointer';
    } else {
      btn.className = 'news-t2-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap cursor-pointer';
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
  window.currentModelsPage = 1;
  window.modelsSearchQuery = '';
  window.currentModelsFamily = 'ALL';
  window.currentModelsModality = 'ALL';
  window.currentModelsArtifact = 'ALL';
  window.currentModelsSort = 'date-audit-desc';
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
  window.currentInboxPage = 1;
  window.inboxSearchQuery = '';
  window.currentInboxSource = 'ALL';
  window.currentInboxLang = 'ALL';
  window.currentInboxType = 'ALL';
  window.currentInboxTech = 'ALL';
  window.currentInboxSort = 'date-audit-desc';
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

export function switchView(view, pushHistory = true, preserveFilters = false) {
  if (!preserveFilters) {
    resetAllFiltersAndSearch();
  }
  const validViews = ['home', 'portfolio', 'news', 'models', 'graph', 'inbox'];
  const targetView = validViews.includes(view) ? view : 'home';
  window.currentView = targetView;

  validViews.forEach(v => {
    const el = document.getElementById(v + 'View');
    const btn = document.getElementById('tab' + v.charAt(0).toUpperCase() + v.slice(1) + 'Btn');
    const mBtn = document.getElementById('mTab' + v.charAt(0).toUpperCase() + v.slice(1) + 'Btn');
    
    if (el) el.classList.toggle('hidden', v !== targetView);
    
    if (btn) {
      if (v === targetView) {
        btn.className = 'nav-tab active flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-white bg-ink-primary transition shadow-sm';
      } else {
        btn.className = 'nav-tab flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-ink-secondary hover:text-ink-primary transition';
      }
    }

    if (mBtn) {
      if (v === targetView) {
        mBtn.className = 'mobile-nav-tab active shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-ink-primary transition shadow-sm';
      } else {
        mBtn.className = 'mobile-nav-tab shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium text-ink-secondary hover:text-ink-primary bg-surface-subtle border border-surface-border transition';
      }
    }
  });

  const adminBtn = document.getElementById('adminArchiveBtn');
  if (adminBtn) {
    if (targetView === 'inbox') {
      adminBtn.className = 'flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-bold text-white bg-slate-800 transition border border-slate-700 shadow-sm';
    } else {
      adminBtn.className = 'flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold text-ink-muted hover:text-ink-primary hover:bg-surface-subtle transition border border-transparent hover:border-surface-border';
    }
  }

  if (pushHistory) {
    const targetHash = ROUTES[targetView] || '#/' + targetView;
    if (window.location.hash !== targetHash) {
      try {
        history.pushState({ view: targetView }, '', targetHash);
      } catch (e) {
        window.location.hash = targetHash;
      }
    }
  }

  // Immediate Active View Re-render
  if (targetView === 'home') {
    renderTelemetryCharts();
    updateCronCountdown();
    renderHomeTopPicks();
  } else if (targetView === 'portfolio') {
    renderCards();
  } else if (targetView === 'models') {
    renderModels();
  } else if (targetView === 'news') {
    renderNews();
  } else if (targetView === 'inbox') {
    renderInbox();
    renderPipelineTelemetryCards();
    renderRunsTable();
    updateCronCountdown();
  } else if (targetView === 'graph') {
    initCitationGraph();
  }

  if (pushHistory && window.scrollY > 60) {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
  if (window.lucide && typeof window.lucide.createIcons === 'function') {
    requestAnimationFrame(() => {
      const viewEl = document.getElementById(targetView + 'View');
      if (viewEl) window.lucide.createIcons({ root: viewEl });
      else window.lucide.createIcons();
    });
  }
}

export function handleHashRoute() {
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
      const pool = window.liveCasesData || liveCasesData || casesData || [];
      const target = pool.find(c => c.case_id === targetCaseId || c.investigation_id === targetCaseId);
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

  const curView = window.currentView || currentView || 'home';
  if (curView !== targetView) {
    switchView(targetView, false, false);
  } else if (targetView === 'home') {
    renderTelemetryCharts();
    updateCronCountdown();
    renderHomeTopPicks();
  }

  // 3. Apply Page State to Active View
  if (targetView === 'news') {
    const curP = window.currentNewsPage || currentNewsPage || 1;
    if (curP !== pageParam) changeNewsPage(pageParam, false);
  } else if (targetView === 'portfolio') {
    const curP = window.currentPortfolioPage || currentPortfolioPage || 1;
    if (curP !== pageParam) changePortfolioPage(pageParam, false);
  } else if (targetView === 'models') {
    const curP = window.currentModelsPage || currentModelsPage || 1;
    if (curP !== pageParam) changeModelsPage(pageParam, false);
  } else if (targetView === 'inbox') {
    const curP = window.currentInboxPage || currentInboxPage || 1;
    if (curP !== pageParam) changeInboxPage(pageParam, false);
  }
}

export function initRouter() {
  window.addEventListener('popstate', handleHashRoute);
  window.addEventListener('hashchange', handleHashRoute);
  window.addEventListener('load', () => {
    const hash = window.location.hash || '';
    if (!window.__APP_INITIALIZED__ || hash.includes('case=') || hash.startsWith('#case/') || hash.includes('page=')) {
      setTimeout(handleHashRoute, 150);
    }
  });
}
