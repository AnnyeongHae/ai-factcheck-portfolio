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

export function changePortfolioPage(page, pushHistory = true) {
  setPortfolioPage(page);
  if (typeof window.renderCards === 'function') window.renderCards();
  document.getElementById('portfolioView')?.scrollIntoView({ behavior: 'smooth' });
  if (pushHistory && typeof history !== 'undefined') {
    const targetHash = page > 1 ? '#/factchecks?page=' + page : '#/factchecks';
    if (window.location.hash !== targetHash) {
      try { history.pushState({ view: 'portfolio', page: page }, '', targetHash); } catch(e) { window.location.hash = targetHash; }
    }
  }
}

export function changeModelsPage(page, pushHistory = true) {
  setModelsPage(page);
  if (typeof window.renderModels === 'function') window.renderModels();
  document.getElementById('modelsView')?.scrollIntoView({ behavior: 'smooth' });
  if (pushHistory && typeof history !== 'undefined') {
    const targetHash = page > 1 ? '#/models?page=' + page : '#/models';
    if (window.location.hash !== targetHash) {
      try { history.pushState({ view: 'models', page: page }, '', targetHash); } catch(e) { window.location.hash = targetHash; }
    }
  }
}

export function changeNewsPage(page, pushHistory = true) {
  setNewsPage(page);
  if (typeof window.renderNews === 'function') window.renderNews();
  document.getElementById('newsView')?.scrollIntoView({ behavior: 'smooth' });
  if (pushHistory && typeof history !== 'undefined') {
    const targetHash = page > 1 ? '#/news?page=' + page : '#/news';
    if (window.location.hash !== targetHash) {
      try { history.pushState({ view: 'news', page: page }, '', targetHash); } catch(e) { window.location.hash = targetHash; }
    }
  }
}

export function changeInboxPage(page, pushHistory = true) {
  setInboxPage(page);
  if (typeof window.renderInbox === 'function') window.renderInbox();
  document.getElementById('inboxView')?.scrollIntoView({ behavior: 'smooth' });
  if (pushHistory && typeof history !== 'undefined') {
    const targetHash = page > 1 ? '#/inbox?page=' + page : '#/inbox';
    if (window.location.hash !== targetHash) {
      try { history.pushState({ view: 'inbox', page: page }, '', targetHash); } catch(e) { window.location.hash = targetHash; }
    }
  }
}

if (typeof window !== 'undefined') {
  window.renderPagination = renderPagination;
  window.changePortfolioPage = changePortfolioPage;
  window.changeModelsPage = changeModelsPage;
  window.changeNewsPage = changeNewsPage;
  window.changeInboxPage = changeInboxPage;
}
