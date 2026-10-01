/**
 * ==============================================================================
 * Ingestion Inbox View (Candidates Pipeline, Sorting & Queue Actions)
 * ==============================================================================
 */

import {
  currentLang,
  currentInboxPage,
  currentInboxSort,
  currentInboxLang,
  currentInboxType,
  currentInboxTech,
  currentInboxSource,
  inboxSearchQuery,
  liveInboxData,
  queuedItemIds,
  PAGE_SIZE
} from '../core/store.js';
import { APP_CONFIG, API_BASE } from '../core/config.js';
import { i18n } from '../core/i18n.js';
import { sortCollection } from '../utils/collectionSorter.js';
import { detectSourceLang } from '../utils/languageDetector.js';
import { calculateStandardizedViralScore } from '../utils/metricFormatter.js';
import { formatKstMonthDay } from '../utils/dateTime.js';
import { renderPagination } from '../components/pagination.js';
import { showToast } from '../components/toast.js';
import {
  getLocalizedContent,
  renderHookCallout,
  renderAiTakeaways,
  renderRelatedDossierButton,
  renderCommentsAccordion,
  renderCardStandardFooter
} from '../components/newsCard.js';

export function setInboxSort(val) {
  window.currentInboxPage = 1;
  window.currentInboxSort = val;
  renderInbox();
}

export function toggleInboxIncludePending(checked) {
  window.inboxIncludePending = !!checked;
  window.currentInboxPage = 1;
  renderInbox();
}

export function setInboxLangFilter(lang) {
  window.currentInboxPage = 1;
  window.currentInboxLang = lang;
  document.querySelectorAll('.inbox-filter-pill').forEach(btn => {
    if (btn.dataset.langVal === lang) {
      btn.className = 'inbox-filter-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shrink-0 whitespace-nowrap';
    } else {
      btn.className = 'inbox-filter-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
    }
  });
  renderInbox();
}

export function setInboxTypeFilter(typeVal) {
  window.currentInboxPage = 1;
  window.currentInboxType = typeVal;
  document.querySelectorAll('.inbox-type-pill').forEach(btn => {
    if (btn.dataset.typeVal === typeVal) {
      btn.className = 'inbox-type-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shrink-0 whitespace-nowrap';
    } else {
      btn.className = 'inbox-type-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
    }
  });
  renderInbox();
}

export function setInboxTechFilter(tech) {
  window.currentInboxPage = 1;
  window.currentInboxTech = tech;
  document.querySelectorAll('.inbox-tech-pill').forEach(btn => {
    if (btn.dataset.techVal === tech) {
      btn.className = 'inbox-tech-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shrink-0 whitespace-nowrap';
    } else {
      btn.className = 'inbox-tech-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
    }
  });
  renderInbox();
}

export function setInboxSourceFilter(src) {
  window.currentInboxPage = 1;
  window.currentInboxSource = src;
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

export async function toggleQueueItem(inboxId, title) {
  const isCurrentlyQueued = queuedItemIds.has(inboxId);
  const action = isCurrentlyQueued ? 'unqueue' : 'queue';
  
  if (isCurrentlyQueued) {
    queuedItemIds.delete(inboxId);
  } else {
    queuedItemIds.add(inboxId);
  }
  try {
    localStorage.setItem('queued_factchecks', JSON.stringify(Array.from(queuedItemIds)));
  } catch (e) {}
  renderInbox();

  try {
    const res = await fetch(API_BASE + '/api/queue', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ inbox_id: inboxId, action: action })
    });
    if (res.ok) {
      showToast(action === 'queue' ? `[${title}] 항목이 클라우드 DB 실시간 큐에 등록되었습니다!` : `대기열에서 제외되었습니다.`);
      return;
    }
  } catch (err) {}

  showToast(isCurrentlyQueued ? `대기열에서 제외되었습니다.` : `[${title}] 항목이 대기열에 등록되었습니다.`);
}

import { ClientCache } from '../core/cache.js';

const inboxDbCache = new Map();
let inboxFetchAbortController = null;

function getInboxCacheKey(page) {
  const params = new URLSearchParams();
  params.set('limit', PAGE_SIZE);
  params.set('page', page);
  const curSrc = window.currentInboxSource || currentInboxSource || 'ALL';
  const curLangFilter = window.currentInboxLang || currentInboxLang || 'ALL';
  const curType = window.currentInboxType || currentInboxType || 'ALL';
  const curSearch = window.inboxSearchQuery || inboxSearchQuery || '';
  const curSort = window.currentInboxSort || currentInboxSort || 'date-audit-desc';

  if (curSrc && curSrc !== 'ALL') params.set('source', curSrc);
  if (curLangFilter && curLangFilter !== 'ALL') params.set('lang', curLangFilter);
  if (curType && curType !== 'ALL') params.set('type', curType);
  if (curSearch) params.set('search', curSearch);
  if (curSort) params.set('sort', curSort);
  if (window.inboxIncludePending) params.set('include_pending', 'true');
  return params.toString();
}

export async function fetchInboxFromDb(page = window.currentInboxPage || currentInboxPage || 1, bypassCache = false) {
  const baseUrl = APP_CONFIG.apiUrl('/api/inbox');
  const cacheKey = getInboxCacheKey(page);

  if (!bypassCache) {
    const cached = ClientCache.get(cacheKey, 60000);
    if (cached) {
      inboxDbCache.set(cacheKey, cached);
      return cached;
    }
  }

  if (inboxFetchAbortController) {
    try { inboxFetchAbortController.abort(); } catch(e) {}
  }
  inboxFetchAbortController = new AbortController();

  const url = `${baseUrl}?${cacheKey}`;
  const res = await fetch(url, { signal: inboxFetchAbortController.signal });
  if (!res.ok) throw new Error(`HTTP error ${res.status}`);
  const data = await res.json();
  if (data && data.status === 'success') {
    const result = {
      total: data.total || 0,
      totalPages: data.total_pages || Math.ceil((data.total || 0) / PAGE_SIZE) || 1,
      items: data.items || [],
      timestamp: Date.now()
    };
    inboxDbCache.set(cacheKey, result);
    ClientCache.set(cacheKey, result);
    return result;
  }
  throw new Error('API returned invalid payload');
}

export function createInboxCardElement(it, curLang) {
  const isQueued = queuedItemIds.has(it.inbox_id);
  const ai = it.ai_enrichment;
  const effectiveSourceLang = detectSourceLang(it);
  const { displayTitle, displayHook, displayDesc, displayTakeaways, hasTrilingual } = getLocalizedContent(it, curLang);
  const showDesc = (!displayTakeaways || displayTakeaways.length === 0) && displayDesc;

  const viralScore = calculateStandardizedViralScore(it);
  const tracking = it.metric_tracking || {};
  const initDate = formatKstMonthDay(tracking.initial?.recorded_at || tracking.initial_date || it.created_at || it.harvested_date);
  const latestDate = formatKstMonthDay(tracking.latest?.updated_at || tracking.latest_date || it.updated_at || it.harvested_date);
  const initVal = tracking.initial?.display || tracking.initial_metric || it.viral_metric || '-';
  const latestVal = tracking.latest?.display || tracking.latest_metric || it.viral_metric || '-';
  const delta = (tracking.delta !== undefined) ? tracking.delta : (tracking.growth_delta || 0);

  let typeBadge = curLang === 'KO' ? '⚡ 신기술' : (curLang === 'ZH' ? '⚡ 新技术' : '⚡ Tech');
  if (ai && ai.type_classification === 'AGENT') typeBadge = curLang === 'KO' ? '🦾 에이전트' : (curLang === 'ZH' ? '🦾 智能体' : '🦾 Agent');
  else if (ai && ai.type_classification === 'MODEL') typeBadge = curLang === 'KO' ? '🤖 AI 모델' : (curLang === 'ZH' ? '🤖 AI 模型' : '🤖 AI Model');
  else if (ai && ai.type_classification === 'NEWS') typeBadge = curLang === 'KO' ? '📰 업계 동향' : (curLang === 'ZH' ? '📰 行业资讯' : '📰 News');

  const card = document.createElement('div');
  card.className = 'executive-card p-4 sm:p-5 flex flex-col justify-between space-y-3.5 hover:border-indigo-400 hover:shadow-md transition';

  const hookHtml = renderHookCallout(displayHook);
  const aiSummaryHtml = renderAiTakeaways(displayTakeaways, curLang);
  const relatedHtml = renderRelatedDossierButton(it.related_dossier, curLang);

  const rawComments = Array.isArray(it.raw_comments) 
    ? it.raw_comments 
    : (Array.isArray(it.raw_payload?.raw_comments) ? it.raw_payload.raw_comments : []);
  
  const commentsHtml = renderCommentsAccordion(rawComments, curLang, it.source_url);

  const queueActionBtn = `
    <button onclick="toggleQueueItem('${it.inbox_id}', '${displayTitle.replace(/'/g, "")}')" 
            class="px-2.5 py-1 rounded-lg text-xs font-bold transition flex items-center gap-1.5 shrink-0 ${isQueued ? 'bg-emerald-700 text-white font-black' : 'bg-surface-subtle text-ink-primary hover:bg-ink-primary hover:text-white border border-surface-border'}">
      <i data-lucide="${isQueued ? 'check-circle-2' : 'plus-circle'}" class="w-3.5 h-3.5"></i>
      <span>${isQueued ? (curLang === 'KO' ? '큐 등록됨' : (curLang === 'ZH' ? '已入队列' : 'Queued')) : (curLang === 'KO' ? '큐 추가' : (curLang === 'ZH' ? '加入队列' : 'Queue'))}</span>
    </button>
  `;
  const footerHtml = renderCardStandardFooter(it, curLang, queueActionBtn);

  card.innerHTML = `
    <div class="space-y-2.5">
      <div class="flex items-center justify-between text-xs font-mono">
        <span class="px-2 py-0.5 rounded bg-surface-subtle text-ink-primary font-bold border border-surface-border text-[11px]">
          ${it.source_platform || 'Tech Candidate'}
        </span>
        <span class="px-2.5 py-0.5 rounded-lg text-[11px] font-black font-mono shadow-2xs flex items-center gap-1 ${viralScore >= 70 ? 'bg-rose-100/90 text-rose-800 border border-rose-300' : 'bg-amber-100/90 text-amber-900 border border-amber-300'}">
          <i data-lucide="flame" class="w-3 h-3 ${viralScore >= 70 ? 'text-rose-600 fill-rose-500' : 'text-amber-600 fill-amber-500'}"></i>
          <span>${curLang === 'KO' ? `인기 ${viralScore}점` : (curLang === 'ZH' ? `热度 ${viralScore}分` : `Viral ${viralScore} pts`)}</span>
        </span>
      </div>

      <div class="flex items-center gap-1.5 flex-wrap">
        <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-900 border border-indigo-200">
          ${typeBadge}
        </span>
        ${ai && ai.programming_lang && ai.programming_lang !== 'General' ? `<span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-50 text-amber-900 border border-amber-200">💻 ${ai.programming_lang}</span>` : ''}
        ${effectiveSourceLang ? `<span class="px-1.5 py-0.2 rounded text-[9px] font-mono font-semibold bg-surface-subtle text-ink-muted border border-surface-border">🌐 ${effectiveSourceLang}</span>` : ''}
        ${hasTrilingual ? `<span class="px-1.5 py-0.2 rounded text-[9px] font-mono font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">🌐 KO·EN·ZH</span>` : `<span class="px-1.5 py-0.2 rounded text-[9px] font-mono font-medium bg-surface-subtle text-ink-muted border border-surface-border">🌐 번역 대기</span>`}
      </div>

      <h3 class="font-bold text-sm text-ink-primary leading-snug">
        ${displayTitle}
      </h3>

      ${hookHtml}

      ${showDesc ? `<p class="text-xs text-ink-secondary leading-relaxed line-clamp-3">${displayDesc}</p>` : ''}

      ${aiSummaryHtml}
      ${relatedHtml}
      ${commentsHtml}

      <div class="p-2.5 rounded-xl bg-surface-subtle border border-surface-border text-[11px] space-y-1 font-mono">
        <div class="flex items-center justify-between text-ink-muted">
          <span>${curLang === 'KO' ? '최초 수집' : (curLang === 'ZH' ? '首次采集' : 'Created')} (${initDate}):</span>
          <span class="font-semibold text-ink-secondary">${initVal}</span>
        </div>
        <div class="flex items-center justify-between pt-0.5 border-t border-surface-border">
          <span class="${delta > 0 ? 'text-indigo-950 font-bold' : 'text-ink-muted'}">${curLang === 'KO' ? '최신 갱신' : (curLang === 'ZH' ? '最新同步' : 'Latest')} (${latestDate}):</span>
          <span class="${delta > 0 ? 'text-emerald-700 font-bold' : 'text-ink-primary font-semibold'}">${latestVal}</span>
        </div>
      </div>

    </div>

    ${footerHtml}
  `;

  return card;
}

export function renderInboxGridItems(items, grid, curLang) {
  if (!grid) return;
  grid.innerHTML = '';
  const fragment = document.createDocumentFragment();
  const renderPool = Array.isArray(items) ? items : [];
  renderPool.forEach(it => fragment.appendChild(createInboxCardElement(it, curLang)));
  grid.appendChild(fragment);
  if (window.lucide) window.lucide.createIcons({ root: grid });
}

export async function renderInbox() {
  const grid = document.getElementById('inboxGrid');
  if (!grid) return;

  const curLang = window.currentLang || currentLang || 'KO';
  const curPage = window.currentInboxPage || currentInboxPage || 1;
  const curSort = window.currentInboxSort || currentInboxSort || 'date-audit-desc';
  const curSrc = window.currentInboxSource || currentInboxSource || 'ALL';
  const curLangFilter = window.currentInboxLang || currentInboxLang || 'ALL';
  const curType = window.currentInboxType || currentInboxType || 'ALL';
  const curTech = window.currentInboxTech || currentInboxTech || 'ALL';
  const curSearch = window.inboxSearchQuery || inboxSearchQuery || '';

  const cacheKey = getInboxCacheKey(curPage);

  // 1. ⚡ 0ms SWR Cache Hit (Memory Map or SessionStorage)
  let renderedFromCache = false;
  let cachedFirstId = null;
  let cached = inboxDbCache.get(cacheKey);
  if (!cached) {
    cached = ClientCache.get(cacheKey, 60000);
    if (cached) inboxDbCache.set(cacheKey, cached);
  }
  if (cached && Array.isArray(cached.items) && cached.items.length > 0) {
    renderInboxGridItems(cached.items, grid, curLang);
    renderPagination('inboxPagination', curPage, cached.totalPages, 'changeInboxPage');
    renderedFromCache = true;
    cachedFirstId = cached.items[0]?.inbox_id || cached.items[0]?.id;
    if (Date.now() - (cached.timestamp || 0) < 10000) {
      return;
    }
  }

  // 2. Optimistic Preview from local snapshot ONLY when a full page is available
  let fallbackPaged = [];
  let fallbackTotalPages = 1;
  if (!renderedFromCache) {
    const inboxList = window.liveInboxData || liveInboxData || [];
    const filtered = inboxList.filter(item => {
      const ai = item.ai_enrichment;
      const filterSrcKey = curSrc.toLowerCase();
      const matchesSrc = curSrc === 'ALL' || ((item.source_platform || '').toLowerCase().includes(filterSrcKey));
      const itemLang = detectSourceLang(item);
      const matchesLang = curLangFilter === 'ALL' || itemLang === curLangFilter;
      const itemType = (ai ? ai.type_classification : null) || item.category_type || 'TECH';
      const matchesType = curType === 'ALL' ? true : (itemType === curType);
      const itemTech = (ai ? ai.programming_lang : null) || item.programming_lang || 'General';
      const matchesTech = curTech === 'ALL' || (itemTech.toLowerCase().includes(curTech.toLowerCase()));
      const includePending = !!window.inboxIncludePending;
      if (curSort === 'pending' && (item.ai_enrichment && item.ai_enrichment.enriched_at && item.is_classified)) return false;
      if (!includePending && (curSort === 'date-audit-desc' || curSort === 'date-audit-asc')) {
        if (!item.is_classified || !item.ai_enrichment || !item.ai_enrichment.enriched_at) return false;
      }
      const text = ((item.title || '') + ' ' + (item.title_ko || '') + ' ' + (item.description || '')).toLowerCase();
      const matchesSearch = !curSearch || text.includes(curSearch.toLowerCase());
      return matchesSrc && matchesLang && matchesType && matchesTech && matchesSearch;
    });

    if (filtered.length > 0) {
      sortCollection(filtered, curSort);
      fallbackTotalPages = Math.ceil(filtered.length / PAGE_SIZE) || 1;
      fallbackPaged = filtered.slice((curPage - 1) * PAGE_SIZE, curPage * PAGE_SIZE);
    }

    if (fallbackPaged.length >= PAGE_SIZE) {
      renderInboxGridItems(fallbackPaged, grid, curLang);
      renderPagination('inboxPagination', curPage, fallbackTotalPages, 'changeInboxPage');
    } else {
      // Clean skeleton loading state instead of flashing 1~3 stale cards
      grid.innerHTML = Array.from({ length: 6 }).map(() => `
        <div class="executive-card p-5 animate-pulse space-y-4">
          <div class="h-4 bg-slate-200 rounded w-1/3"></div>
          <div class="h-5 bg-slate-200 rounded w-5/6"></div>
          <div class="h-12 bg-slate-100 rounded"></div>
          <div class="h-4 bg-slate-200 rounded w-1/2"></div>
        </div>
      `).join('');
    }
  }

  // 3. Dynamic SWR Fetch from DB (/api/inbox)
  try {
    const dbResult = await fetchInboxFromDb(curPage, renderedFromCache);
    if (dbResult && Array.isArray(dbResult.items)) {
      const newFirstId = dbResult.items[0]?.inbox_id || dbResult.items[0]?.id;
      if (!renderedFromCache || newFirstId !== cachedFirstId || dbResult.items.length !== (inboxDbCache.get(cacheKey)?.items?.length)) {
        if (dbResult.items.length === 0) {
          grid.innerHTML = `<div class="col-span-full py-16 text-center text-ink-muted font-medium">${curLang === 'KO' ? '수집된 인박스 후보가 없습니다.' : (curLang === 'ZH' ? '收件箱暂无候选数据。' : 'No candidates in the inbox.')}</div>`;
          renderPagination('inboxPagination', 1, 1, 'changeInboxPage');
        } else {
          renderInboxGridItems(dbResult.items, grid, curLang);
          renderPagination('inboxPagination', curPage, dbResult.totalPages, 'changeInboxPage');
        }
      }
    }
  } catch (err) {
    if (err.name === 'AbortError') return;
    console.warn('[Inbox SWR] DB fetch skipped:', err.message);
    if (!renderedFromCache && fallbackPaged.length > 0 && grid.querySelector('.animate-pulse')) {
      renderInboxGridItems(fallbackPaged, grid, curLang);
      renderPagination('inboxPagination', curPage, fallbackTotalPages, 'changeInboxPage');
    } else if (!grid.children.length || grid.querySelector('.animate-pulse')) {
      grid.innerHTML = `<div class="col-span-full py-16 text-center text-ink-muted font-medium">${curLang === 'KO' ? '수집된 인박스 후보가 없습니다.' : (curLang === 'ZH' ? '收件箱暂无候选数据。' : 'No candidates in the inbox.')}</div>`;
    }
  }
}
