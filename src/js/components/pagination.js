/**
 * ==============================================================================
 * Global Pagination Component (Sliding Window Decade Pagination)
 * ==============================================================================
 */

import {
  currentPortfolioPage,
  currentModelsPage,
  currentNewsPage,
  currentInboxPage,
  setPortfolioPage,
  setModelsPage,
  setNewsPage,
  setInboxPage
} from '../core/store.js';
import { getBasePath } from '../core/config.js';

export function renderPagination(containerId, currentPage, totalPages, onPageChange) {
  if (typeof document === 'undefined') return;
  const container = document.getElementById(containerId);
  if (!container) return;
  if (totalPages <= 1) {
    container.innerHTML = '';
    return;
  }

  let html = '<div class="flex items-center justify-center gap-1.5 pt-6 pb-4 text-xs font-mono select-none flex-wrap">';

  // First Page <<
  const firstDisabled = currentPage === 1;
  const hovFirst = firstDisabled ? '' : `onmouseenter="window.onPaginationHover && window.onPaginationHover('${containerId}', 1)"`;
  html += `<button onclick="${firstDisabled ? '' : onPageChange + '(1)'}" ${hovFirst} class="px-2.5 py-1.5 rounded-lg border font-bold transition shadow-xs ${firstDisabled ? 'opacity-30 cursor-not-allowed bg-surface-subtle text-ink-muted border-surface-border' : 'bg-white hover:bg-surface-subtle text-ink-primary border-surface-border cursor-pointer'}" title="처음으로">&laquo;&laquo;</button>`;

  // Prev Page <
  const prevDisabled = currentPage === 1;
  const prevTarget = Math.max(1, currentPage - 1);
  const hovPrev = prevDisabled ? '' : `onmouseenter="window.onPaginationHover && window.onPaginationHover('${containerId}', ${prevTarget})"`;
  html += `<button onclick="${prevDisabled ? '' : onPageChange + '(' + prevTarget + ')'}" ${hovPrev} class="px-2.5 py-1.5 rounded-lg border font-bold transition shadow-xs ${prevDisabled ? 'opacity-30 cursor-not-allowed bg-surface-subtle text-ink-muted border-surface-border' : 'bg-white hover:bg-surface-subtle text-ink-primary border-surface-border cursor-pointer'}" title="이전">&lsaquo;</button>`;

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
    const hovP = isCur ? '' : `onmouseenter="window.onPaginationHover && window.onPaginationHover('${containerId}', ${p})"`;
    html += `<button onclick="${onPageChange}(${p})" ${hovP} class="w-8 h-8 rounded-lg border flex items-center justify-center transition ${btnStyle}">${p}</button>`;
  }

  // Next Page >
  const nextDisabled = currentPage === totalPages;
  const nextTarget = Math.min(totalPages, currentPage + 1);
  const hovNext = nextDisabled ? '' : `onmouseenter="window.onPaginationHover && window.onPaginationHover('${containerId}', ${nextTarget})"`;
  html += `<button onclick="${nextDisabled ? '' : onPageChange + '(' + nextTarget + ')'}" ${hovNext} class="px-2.5 py-1.5 rounded-lg border font-bold transition shadow-xs ${nextDisabled ? 'opacity-30 cursor-not-allowed bg-surface-subtle text-ink-muted border-surface-border' : 'bg-white hover:bg-surface-subtle text-ink-primary border-surface-border cursor-pointer'}" title="다음">&rsaquo;</button>`;

  // Last Page >>
  const lastDisabled = currentPage === totalPages;
  const hovLast = lastDisabled ? '' : `onmouseenter="window.onPaginationHover && window.onPaginationHover('${containerId}', ${totalPages})"`;
  html += `<button onclick="${lastDisabled ? '' : onPageChange + '(' + totalPages + ')'}" ${hovLast} class="px-2.5 py-1.5 rounded-lg border font-bold transition shadow-xs ${lastDisabled ? 'opacity-30 cursor-not-allowed bg-surface-subtle text-ink-muted border-surface-border' : 'bg-white hover:bg-surface-subtle text-ink-primary border-surface-border cursor-pointer'}" title="끝으로">&raquo;&raquo;</button>`;

  html += '</div>';
  container.innerHTML = html;
}

export function handlePaginationHover(containerId, targetPage) {
  if (!targetPage || targetPage < 1) return;
  if (containerId === 'newsPagination' && typeof window.prefetchNewsPage === 'function') {
    window.prefetchNewsPage(targetPage);
  } else if (containerId === 'inboxPagination' && typeof window.prefetchInboxPage === 'function') {
    window.prefetchInboxPage(targetPage);
  } else if (containerId === 'modelsPagination' && typeof window.prefetchModelsPage === 'function') {
    window.prefetchModelsPage(targetPage);
  }
}

export function changePortfolioPage(page, pushHistory = true) {
  setPortfolioPage(page);
  if (typeof window.renderCards === 'function') window.renderCards();
  document.getElementById('portfolioView')?.scrollIntoView({ behavior: 'smooth' });
  if (pushHistory && typeof history !== 'undefined') {
    const base = getBasePath();
    const targetUrl = base + (page > 1 ? '/factchecks?page=' + page : '/factchecks');
    const curPath = window.location.pathname + window.location.search;
    if (curPath !== targetUrl) {
      try { history.pushState({ view: 'portfolio', page: page }, '', targetUrl); } catch(e) {}
    }
  }
}

export function changeModelsPage(page, pushHistory = true) {
  setModelsPage(page);
  if (typeof window.renderModels === 'function') window.renderModels();
  document.getElementById('modelsView')?.scrollIntoView({ behavior: 'smooth' });
  if (pushHistory && typeof history !== 'undefined') {
    const base = getBasePath();
    const targetUrl = base + (page > 1 ? '/models?page=' + page : '/models');
    const curPath = window.location.pathname + window.location.search;
    if (curPath !== targetUrl) {
      try { history.pushState({ view: 'models', page: page }, '', targetUrl); } catch(e) {}
    }
  }
}

export function changeNewsPage(page, pushHistory = true) {
  setNewsPage(page);
  if (typeof window.renderNews === 'function') window.renderNews();
  document.getElementById('newsView')?.scrollIntoView({ behavior: 'smooth' });
  if (pushHistory && typeof history !== 'undefined') {
    const curFacet = window.currentNewsFacet || 'ALL';
    const curSpkDate = window.currentSpikeDate || '';
    let qs = page > 1 ? `page=${page}` : '';
    if (curFacet && curFacet !== 'ALL') {
      qs += (qs ? '&' : '') + `facet=${encodeURIComponent(curFacet)}`;
      if (curFacet === 'CROSS_SPIKE' && curSpkDate) {
        qs += `&date=${encodeURIComponent(curSpkDate)}`;
      }
    }
    const base = getBasePath();
    const targetUrl = base + (qs ? `/news?${qs}` : '/news');
    const curPath = window.location.pathname + window.location.search;
    if (curPath !== targetUrl) {
      try { history.pushState({ view: 'news', page: page }, '', targetUrl); } catch(e) {}
    }
  }
}

export function changeInboxPage(page, pushHistory = true) {
  setInboxPage(page);
  if (typeof window.renderInbox === 'function') window.renderInbox();
  document.getElementById('inboxView')?.scrollIntoView({ behavior: 'smooth' });
  if (pushHistory && typeof history !== 'undefined') {
    const base = getBasePath();
    const targetUrl = base + (page > 1 ? '/inbox?page=' + page : '/inbox');
    const curPath = window.location.pathname + window.location.search;
    if (curPath !== targetUrl) {
      try { history.pushState({ view: 'inbox', page: page }, '', targetUrl); } catch(e) {}
    }
  }
}

if (typeof window !== 'undefined') {
  window.renderPagination = renderPagination;
  window.onPaginationHover = handlePaginationHover;
  window.handlePaginationHover = handlePaginationHover;
  window.changePortfolioPage = changePortfolioPage;
  window.changeModelsPage = changeModelsPage;
  window.changeNewsPage = changeNewsPage;
  window.changeInboxPage = changeInboxPage;
}
