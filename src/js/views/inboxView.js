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
import { API_BASE } from '../core/config.js';
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

export function renderInbox() {
  const grid = document.getElementById('inboxGrid');
  if (!grid) return;
  grid.innerHTML = '';

  const curLang = window.currentLang || currentLang || 'KO';
  const curPage = window.currentInboxPage || currentInboxPage || 1;
  const curSort = window.currentInboxSort || currentInboxSort || 'date-audit-desc';
  const curSrc = window.currentInboxSource || currentInboxSource || 'ALL';
  const curLangFilter = window.currentInboxLang || currentInboxLang || 'ALL';
  const curType = window.currentInboxType || currentInboxType || 'ALL';
  const curTech = window.currentInboxTech || currentInboxTech || 'ALL';
  const curSearch = window.inboxSearchQuery || inboxSearchQuery || '';

  const inboxList = window.liveInboxData || liveInboxData || [];

  const filtered = inboxList.filter(item => {
    const ai = item.ai_enrichment;

    // 1. 수집 플랫폼 매칭
    const filterSrcKey = curSrc.toLowerCase();
    const matchesSrc = curSrc === 'ALL' || ((item.source_platform || '').toLowerCase().includes(filterSrcKey));

    // 2. 원문 언어 매칭 (KO, EN, ZH, JA)
    const itemLang = detectSourceLang(item);
    const matchesLang = curLangFilter === 'ALL' || itemLang === curLangFilter;

    // 3. 4대 기술 분류 매칭
    const itemType = (ai ? ai.type_classification : null) || item.category_type || 'TECH';
    const matchesType = curType === 'ALL' ? true : (itemType === curType);

    // 4. 기술 스택 매칭
    const itemTech = (ai ? ai.programming_lang : null) || item.programming_lang || 'General';
    const matchesTech = curTech === 'ALL' || (itemTech.toLowerCase().includes(curTech.toLowerCase()));

    // 5. 검색어 매칭
    const text = (
      (item.title || '') + ' ' + 
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
    const matchesSearch = text.includes(curSearch.toLowerCase());

    return matchesSrc && matchesLang && matchesType && matchesTech && matchesSearch;
  });

  // DateTime Sorting
  sortCollection(filtered, curSort);

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE) || 1;
  let page = curPage;
  if (page > totalPages) page = totalPages;
  if (page < 1) page = 1;
  window.currentInboxPage = page;

  renderPagination('inboxPagination', page, totalPages, 'changeInboxPage');

  if (filtered.length === 0) {
    grid.innerHTML = `<div class="col-span-full py-16 text-center text-ink-muted font-medium">${curLang === 'KO' ? '수집된 인박스 후보가 없습니다.' : (curLang === 'ZH' ? '收件箱暂无候选数据。' : 'No candidates in the inbox.')}</div>`;
    return;
  }

  const pagedInbox = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const fragment = document.createDocumentFragment();
  pagedInbox.forEach(it => {
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
          <span class="px-2 py-0.5 rounded text-[11px] font-bold font-mono ${viralScore >= 70 ? 'bg-rose-50 text-rose-700 border border-rose-200' : 'bg-amber-50 text-amber-700 border border-amber-200'}">
            ${curLang === 'KO' ? `🔥 인기 ${viralScore}점` : (curLang === 'ZH' ? `🔥 热度 ${viralScore}分` : `🔥 Viral ${viralScore} pts`)}
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

    fragment.appendChild(card);
  });
  grid.appendChild(fragment);

  if (window.lucide) window.lucide.createIcons({ root: grid });
}
