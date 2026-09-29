/**
 * ==============================================================================
 * News Feed View (Real-Time Ingestion, Facet Filtering & SWR Revalidation)
 * ==============================================================================
 */

import {
  currentLang,
  currentNewsPage,
  currentNewsTier1,
  currentNewsTier2,
  currentNewsFacet,
  currentNewsSource,
  currentNewsSearch,
  currentNewsSort,
  targetSelectedInboxId,
  liveNewsData,
  PAGE_SIZE,
  snapshotStats
} from '../core/store.js';
import { APP_CONFIG } from '../core/config.js';
import { i18n } from '../core/i18n.js';
import { renderPagination } from '../components/pagination.js';
import { createNewsCardElement } from '../components/newsCard.js';

let newsFetchAbortController = null;
export const newsDbCache = new Map();

export function getNewsCacheKey(page = window.currentNewsPage || currentNewsPage || 1) {
  const params = new URLSearchParams();
  params.set('limit', PAGE_SIZE);
  params.set('page', page);
  const t1 = window.currentNewsTier1 || currentNewsTier1;
  const t2 = window.currentNewsTier2 || currentNewsTier2;
  const facet = window.currentNewsFacet || currentNewsFacet;
  const src = window.currentNewsSource || currentNewsSource;
  const search = window.currentNewsSearch || currentNewsSearch;
  const sort = window.currentNewsSort || currentNewsSort;

  if (t1 && t1 !== 'ALL') params.set('tier1', t1);
  if (t2 && t2 !== 'ALL') params.set('tier2', t2);
  if (facet && facet !== 'ALL') params.set('facet', facet);
  if (src && src !== 'ALL') params.set('source', src);
  if (search) params.set('search', search);
  if (sort) params.set('sort', sort);
  return params.toString();
}

export async function fetchNewsFromDb(page = window.currentNewsPage || currentNewsPage || 1, bypassCache = false) {
  const baseUrl = APP_CONFIG.apiUrl('/api/inbox');
  const cacheKey = getNewsCacheKey(page);

  if (!bypassCache && newsDbCache.has(cacheKey)) {
    const cached = newsDbCache.get(cacheKey);
    if (cached && (Date.now() - (cached.timestamp || 0) < 30000)) {
      return cached;
    }
  }

  if (newsFetchAbortController) {
    try { newsFetchAbortController.abort(); } catch(e) {}
  }
  newsFetchAbortController = new AbortController();

  const url = `${baseUrl}?${cacheKey}`;
  const res = await fetch(url, { signal: newsFetchAbortController.signal });
  if (!res.ok) throw new Error(`HTTP error ${res.status}`);
  const data = await res.json();
  if (data && data.status === 'success') {
    const result = {
      total: data.total || 0,
      totalPages: data.total_pages || Math.ceil((data.total || 0) / PAGE_SIZE) || 1,
      items: data.items || [],
      timestamp: Date.now()
    };
    newsDbCache.set(cacheKey, result);
    return result;
  }
  throw new Error('API returned invalid payload');
}

export function renderNewsGridItems(items, grid) {
  if (!grid) return;
  grid.innerHTML = '';
  const frag = document.createDocumentFragment();
  const renderPool = Array.isArray(items) ? items : [];
  const curLang = window.currentLang || currentLang || 'KO';
  renderPool.forEach(it => frag.appendChild(createNewsCardElement(it, curLang)));
  grid.appendChild(frag);
  if (window.lucide) window.lucide.createIcons({ root: grid });
}

export function renderNewsSkeleton(grid, count = 6) {
  if (!grid) return;
  grid.innerHTML = Array.from({ length: count }).map(() => `
    <div class="executive-card p-5 animate-pulse space-y-4">
      <div class="h-4 bg-slate-200 rounded w-1/3"></div>
      <div class="h-5 bg-slate-200 rounded w-5/6"></div>
      <div class="h-12 bg-slate-100 rounded"></div>
      <div class="h-4 bg-slate-200 rounded w-1/2"></div>
    </div>
  `).join('');
}

export function preloadTopNewsFilters() {
  const topFilters = [
    { tier1: 'ALL' },
    { tier1: 'TECH_COMPUTING' },
    { tier1: 'SCIENCE_RESEARCH' },
    { tier1: 'ECONOMY_FINANCE' },
    { tier1: 'LAW_CRIME_JUSTICE' },
    { facet: 'CROSS_SPIKE' },
    { facet: 'MODEL' }
  ];
  const baseUrl = APP_CONFIG.apiUrl('/api/inbox');

  topFilters.forEach((f, idx) => {
    setTimeout(() => {
      const p = new URLSearchParams({ limit: PAGE_SIZE, page: 1, ...f });
      const key = p.toString();
      if (!newsDbCache.has(key)) {
        fetch(`${baseUrl}?${key}`).then(r => r.json()).then(data => {
          if (data && data.status === 'success') {
            newsDbCache.set(key, {
              total: data.total || 0,
              totalPages: data.total_pages || Math.ceil((data.total || 0) / PAGE_SIZE) || 1,
              items: data.items || []
            });
          }
        }).catch(() => {});
      }
    }, 150 + idx * 100);
  });
}

export function setNewsCategoryFilter(t1) {
  window.currentNewsPage = 1;
  window.currentNewsTier1 = t1;

  if (t1 !== 'TECH_COMPUTING') {
    window.currentNewsTier2 = 'ALL';
  }

  const curFacet = window.currentNewsFacet || currentNewsFacet;
  if (t1 !== 'TECH_COMPUTING' && t1 !== 'ALL') {
    if (curFacet === 'MODEL' || curFacet === 'TOOL') {
      window.currentNewsFacet = 'ALL';
      document.querySelectorAll('.news-facet-pill').forEach(btn => {
        const isAll = btn.getAttribute('data-facet') === 'ALL';
        if (isAll) {
          btn.className = 'news-facet-pill active px-3.5 py-1.5 rounded-xl text-xs font-bold bg-indigo-600 text-white shadow-md ring-2 ring-indigo-300 transition shrink-0 whitespace-nowrap cursor-pointer';
        } else {
          const f = btn.getAttribute('data-facet');
          let colorCls = 'text-slate-200 bg-white/10 border-white/20 hover:bg-white/20';
          if (f === 'CROSS_SPIKE') colorCls = 'text-amber-300 bg-amber-500/10 border-amber-400/30 hover:bg-amber-500/20';
          else if (f === 'MODEL') colorCls = 'text-cyan-300 bg-cyan-500/10 border-cyan-400/30 hover:bg-cyan-500/20';
          else if (f === 'TOOL') colorCls = 'text-emerald-300 bg-emerald-500/10 border-emerald-400/30 hover:bg-emerald-500/20';
          btn.className = `news-facet-pill px-3.5 py-1.5 rounded-xl text-xs font-semibold ${colorCls} border transition shrink-0 whitespace-nowrap cursor-pointer`;
        }
      });
    }
  }

  document.querySelectorAll('.news-cat-pill').forEach(btn => {
    if (btn.getAttribute('data-cat') === t1) {
      btn.className = 'news-cat-pill active px-3 py-1.5 rounded-xl text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap cursor-pointer';
    } else {
      btn.className = 'news-cat-pill px-3 py-1.5 rounded-xl text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap cursor-pointer';
    }
  });

  const curT2 = window.currentNewsTier2 || currentNewsTier2;
  document.querySelectorAll('.news-t2-pill').forEach(btn => {
    if (btn.getAttribute('data-t2') === curT2) {
      btn.className = 'news-t2-pill active px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap cursor-pointer';
    } else {
      btn.className = 'news-t2-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap cursor-pointer';
    }
  });

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

export function setNewsTier2Filter(t2) {
  window.currentNewsPage = 1;
  window.currentNewsTier2 = t2;
  const curT1 = window.currentNewsTier1 || currentNewsTier1;

  if (t2 !== 'ALL' && curT1 !== 'ALL' && curT1 !== 'TECH_COMPUTING') {
    window.currentNewsTier1 = 'TECH_COMPUTING';
    document.querySelectorAll('.news-cat-pill').forEach(btn => {
      if (btn.getAttribute('data-cat') === 'TECH_COMPUTING') {
        btn.className = 'news-cat-pill active px-3 py-1.5 rounded-xl text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap cursor-pointer';
      } else {
        btn.className = 'news-cat-pill px-3 py-1.5 rounded-xl text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap cursor-pointer';
      }
    });
    const t2Container = document.getElementById('newsTier2Container');
    if (t2Container) t2Container.classList.remove('opacity-40', 'pointer-events-none');
  }

  document.querySelectorAll('.news-t2-pill').forEach(btn => {
    if (btn.getAttribute('data-t2') === t2) {
      btn.className = 'news-t2-pill active px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap cursor-pointer';
    } else {
      btn.className = 'news-t2-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap cursor-pointer';
    }
  });
  renderNews();
}

let newsSearchDebounceTimer = null;
export function updateSearchClearBtn(val) {
  const btn = document.getElementById('newsSearchClearBtn');
  if (btn) {
    if (val && String(val).trim().length > 0) {
      btn.classList.remove('hidden');
    } else {
      btn.classList.add('hidden');
    }
  }
}

export function clearNewsSearch() {
  const input = document.getElementById('newsSearchInput');
  if (input) {
    input.value = '';
    input.focus();
  }
  updateSearchClearBtn('');
  handleNewsSearchImmediate('');
}

export function handleNewsSearch(val) {
  updateSearchClearBtn(val);
  clearTimeout(newsSearchDebounceTimer);
  newsSearchDebounceTimer = setTimeout(() => {
    window.targetSelectedInboxId = '';
    window.currentNewsPage = 1;
    window.currentNewsSearch = (val || '').trim().toLowerCase();
    renderNews();
  }, 300);
}

export function handleNewsSearchImmediate(val) {
  updateSearchClearBtn(val);
  clearTimeout(newsSearchDebounceTimer);
  window.targetSelectedInboxId = '';
  window.currentNewsPage = 1;
  window.currentNewsSearch = (val || '').trim().toLowerCase();
  renderNews();
}

export function setNewsSort(sort) {
  window.currentNewsPage = 1;
  window.currentNewsSort = sort;
  renderNews();
}

export function setNewsFacetFilter(facet) {
  window.targetSelectedInboxId = '';
  window.currentNewsPage = 1;
  window.currentNewsFacet = facet;

  if (facet === 'CROSS_SPIKE') {
    window.currentNewsSort = 'viral-score-desc';
    const sortSel = document.getElementById('newsSortSelect');
    if (sortSel) sortSel.value = 'viral-score-desc';
  }

  const curT1 = window.currentNewsTier1 || currentNewsTier1;
  if ((facet === 'MODEL' || facet === 'TOOL') && curT1 !== 'TECH_COMPUTING' && curT1 !== 'ALL') {
    window.currentNewsTier1 = 'ALL';
    window.currentNewsTier2 = 'ALL';
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
  }

  document.querySelectorAll('.news-facet-pill').forEach(btn => {
    const isActive = btn.getAttribute('data-facet') === facet;
    if (isActive) {
      btn.className = 'news-facet-pill active px-3.5 py-1.5 rounded-xl text-xs font-bold bg-indigo-600 text-white shadow-md ring-2 ring-indigo-300 transition shrink-0 whitespace-nowrap cursor-pointer';
    } else {
      const f = btn.getAttribute('data-facet');
      let colorCls = 'text-slate-200 bg-white/10 border-white/20 hover:bg-white/20';
      if (f === 'CROSS_SPIKE') colorCls = 'text-amber-300 bg-amber-500/10 border-amber-400/30 hover:bg-amber-500/20';
      else if (f === 'MODEL') colorCls = 'text-cyan-300 bg-cyan-500/10 border-cyan-400/30 hover:bg-cyan-500/20';
      else if (f === 'TOOL') colorCls = 'text-emerald-300 bg-emerald-500/10 border-emerald-400/30 hover:bg-emerald-500/20';
      btn.className = `news-facet-pill px-3.5 py-1.5 rounded-xl text-xs font-semibold ${colorCls} border transition shrink-0 whitespace-nowrap cursor-pointer`;
    }
  });
  renderNews();
}

export function setNewsSourceFilter(src) {
  window.currentNewsPage = 1;
  window.currentNewsSource = src;
  document.querySelectorAll('.news-src-btn').forEach(btn => {
    if (btn.getAttribute('data-src') === src) {
      btn.className = 'news-src-btn active px-2.5 py-1 rounded-lg text-xs font-bold bg-ink-primary text-white transition shrink-0 whitespace-nowrap';
    } else {
      btn.className = 'news-src-btn px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:bg-white transition border border-surface-border shrink-0 whitespace-nowrap';
    }
  });
  renderNews();
}

export async function renderNews() {
  const grid = document.getElementById('newsGrid');
  if (!grid) return;
  const curLang = window.currentLang || currentLang || 'KO';
  const curPage = window.currentNewsPage || currentNewsPage || 1;
  const curT1 = window.currentNewsTier1 || currentNewsTier1 || 'ALL';
  const curT2 = window.currentNewsTier2 || currentNewsTier2 || 'ALL';
  const curFacet = window.currentNewsFacet || currentNewsFacet || 'ALL';
  const curSrc = window.currentNewsSource || currentNewsSource || 'ALL';
  const curSearch = window.currentNewsSearch || currentNewsSearch || '';
  const targetId = window.targetSelectedInboxId || targetSelectedInboxId || '';

  const cacheKey = getNewsCacheKey(curPage);
  const isDefaultFilter = (curT1 === 'ALL' && curT2 === 'ALL' && curFacet === 'ALL' && !curSearch && !targetId);

  // 1. ⚡ 0ms ZERO-LATENCY FIRST PAINT: Cached Result in Memory (Optimistic SWR)
  let renderedFromCache = false;
  let cachedFirstId = null;
  if (newsDbCache.has(cacheKey)) {
    const cached = newsDbCache.get(cacheKey);
    if (cached && Array.isArray(cached.items) && cached.items.length > 0) {
      renderNewsGridItems(cached.items, grid);
      renderPagination('newsPagination', curPage, cached.totalPages, 'changeNewsPage');
      if (window.lucide) window.lucide.createIcons({ root: grid });
      renderedFromCache = true;
      cachedFirstId = cached.items[0]?.inbox_id || cached.items[0]?.id;
      if (Date.now() - (cached.timestamp || 0) < 10000) {
        return;
      }
    }
  }

  // 2. ⚡ Optimistic Filter (0ms Instant Preview from local snapshot if no cache)
  if (!renderedFromCache) {
    const newsList = window.liveNewsData || liveNewsData || [];
    const memMatches = newsList.filter(it => {
      if (targetId && (it.inbox_id === targetId || it.id === targetId)) return true;
      if (curT1 !== 'ALL' && (it.tier1_category || 'TECH_COMPUTING') !== curT1) return false;
      if (curT2 !== 'ALL' && (it.tier2_category || it.category_primary || 'INDUSTRY_TRENDS') !== curT2) return false;
      if (curFacet === 'CROSS_SPIKE' && !it.is_cross_spiking && (!it.sources || it.sources.length <= 1)) return false;
      if (curFacet === 'MODEL' && !it.is_model && it.facet_type !== 'MODEL') return false;
      if (curSrc !== 'ALL') {
        const plat = (it.source_platform || '').toLowerCase();
        const filterKey = curSrc.toLowerCase();
        const hasInCrossPosts = Array.isArray(it.cross_posts) && it.cross_posts.some(cp => (cp.platform || '').toLowerCase().includes(filterKey));
        const hasInSources = Array.isArray(it.sources) && it.sources.some(s => (s.platform || s.source_name || '').toLowerCase().includes(filterKey));
        if (!plat.includes(filterKey) && !hasInCrossPosts && !hasInSources) return false;
      }
      if (curSearch) {
        const s = curSearch.toLowerCase();
        const matchTitle = (it.title || '').toLowerCase().includes(s) || (it.title_ko || '').toLowerCase().includes(s);
        const matchHook = (it.hook || '').toLowerCase().includes(s) || (it.hook_ko || '').toLowerCase().includes(s);
        if (!matchTitle && !matchHook) return false;
      }
      return true;
    });

    if (memMatches.length > 0) {
      const optimisticSlice = memMatches.slice(0, PAGE_SIZE);
      renderNewsGridItems(optimisticSlice, grid);
      const estPages = Math.ceil(memMatches.length / PAGE_SIZE) || 1;
      renderPagination('newsPagination', curPage, estPages, 'changeNewsPage');
      if (window.lucide) window.lucide.createIcons({ root: grid });
    } else if (grid.children.length === 0) {
      renderNewsSkeleton(grid, 6);
    }
  }

  // 3. 🐘 Background SWR Revalidation (Cloud DB via Edge SWR)
  try {
    const dbRes = await fetchNewsFromDb(curPage, renderedFromCache);
    const items = dbRes.items || [];
    const total = dbRes.total || 0;
    const totalPages = dbRes.totalPages || Math.ceil(total / PAGE_SIZE) || 1;

    const newFirstId = items[0]?.inbox_id || items[0]?.id;
    if (!renderedFromCache || newFirstId !== cachedFirstId || items.length !== (newsDbCache.get(cacheKey)?.items?.length)) {
      if (items.length === 0) {
        grid.innerHTML = `<div class="col-span-full py-16 text-center text-ink-muted font-medium">${curLang === 'KO' ? '해당 플랫폼/조건의 수집 AI 뉴스가 없습니다.' : (curLang === 'ZH' ? '暂无该条件的 AI 资讯。' : 'No AI news articles available for this criteria.')}</div>`;
      } else {
        renderNewsGridItems(items, grid);
      }

      if (window.currentNewsPage > totalPages) window.currentNewsPage = totalPages;
      if (window.currentNewsPage < 1) window.currentNewsPage = 1;
      renderPagination('newsPagination', window.currentNewsPage, totalPages, 'changeNewsPage');

      if (isDefaultFilter && total > 0) {
        if (snapshotStats) snapshotStats.news_total_count = total;
        const numEl = document.getElementById('statValNews');
        if (numEl) numEl.textContent = total.toLocaleString();
        const headEl = document.getElementById('headerNewsCount');
        if (headEl) headEl.textContent = `(${total.toLocaleString()})`;
        const allPill = document.querySelector('.news-cat-pill[data-cat="ALL"]');
        if (allPill) allPill.textContent = curLang === 'KO' ? `전체 (${total.toLocaleString()})` : (curLang === 'ZH' ? `全部 (${total.toLocaleString()})` : `All (${total.toLocaleString()})`);
      }
    }
  } catch (err) {
    if (err.name === 'AbortError') return;
    console.warn('[News DB-Native Fetch Fallback]:', err.message);
  }
}
