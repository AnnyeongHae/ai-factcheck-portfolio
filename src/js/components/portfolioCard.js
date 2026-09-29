/**
 * ==============================================================================
 * Portfolio Card & Dossier View Component
 * Renders executive scannable cards with dual dates, confidence scores, and verdicts
 * ==============================================================================
 */

import {
  currentLang,
  liveCasesData,
  currentMode,
  currentDomain,
  currentSort,
  searchQuery,
  currentPortfolioPage,
  PORTFOLIO_PAGE_SIZE,
  setPortfolioPage,
  AppStore
} from '../core/store.js';
import { i18n } from '../core/i18n.js';
import { getLocalizedContent } from './newsCard.js';
import { sortCollection } from '../utils/collectionSorter.js';
import { formatModelAttribution } from '../utils/dateTime.js';
import { renderPagination } from './pagination.js';
import { openModal } from './modal.js';

export function renderCards() {
  if (typeof document === 'undefined') return;
  const grid = document.getElementById('cardsGrid');
  if (!grid) return;
  grid.innerHTML = '';
  const lang = typeof window !== 'undefined' && window.currentLang ? window.currentLang : currentLang;
  const t = i18n[lang] || i18n.KO;
  const lCases = (window.liveCasesData && window.liveCasesData.length > 0)
    ? window.liveCasesData
    : (liveCasesData && liveCasesData.length > 0 ? liveCasesData : (AppStore.getCases() || []));

  const countUser = lCases.filter(c => (c.curation?.discovery_mode || 'USER_CURATED') === 'USER_CURATED').length;
  const countAuto = lCases.filter(c => (c.curation?.discovery_mode || 'USER_CURATED') === 'AUTO_HARVESTED').length;

  const safeSetTxt = (id, txt) => {
    const el = document.getElementById(id);
    if (el) el.innerText = txt;
  };

  safeSetTxt('badgeCountAll', lCases.length);
  safeSetTxt('badgeCountUser', countUser);
  safeSetTxt('badgeCountAuto', countAuto);
  safeSetTxt('headerVerifiedCount', '(' + lCases.length + ')');
  safeSetTxt('mHeaderVerifiedCount', '(' + lCases.length + ')');

  const curMode = typeof window !== 'undefined' && window.currentMode ? window.currentMode : currentMode;
  const curDomain = typeof window !== 'undefined' && window.currentDomain ? window.currentDomain : currentDomain;
  const curSort = typeof window !== 'undefined' && window.currentSort ? window.currentSort : currentSort;
  const curSearch = typeof window !== 'undefined' && window.searchQuery ? window.searchQuery : searchQuery;
  let curPage = typeof window !== 'undefined' && window.currentPortfolioPage ? window.currentPortfolioPage : currentPortfolioPage;

  const filtered = lCases.filter(c => {
    const mode = c.curation ? c.curation.discovery_mode : 'USER_CURATED';
    const matchesMode = curMode === 'ALL' || mode === curMode;
    
    const cat = (c.category || '').toLowerCase();
    const cluster = (c.clustering?.cluster_id || '').toLowerCase();
    const fullTxt = (c.title + ' ' + (c.clustering?.cluster_name || '') + ' ' + cat).toLowerCase();

    let matchesDomain = true;
    if (curDomain === 'frontend') {
      matchesDomain = cat.includes('design') || cat.includes('frontend') || cat.includes('media') || cluster.includes('design') || cluster.includes('media') || fullTxt.includes('taste') || fullTxt.includes('concat');
    } else if (curDomain === 'agent') {
      matchesDomain = cat.includes('agent') || cluster.includes('agent') || fullTxt.includes('openworker') || fullTxt.includes('praxist');
    } else if (curDomain === 'scraping') {
      matchesDomain = cat.includes('scraping') || cat.includes('browser') || cluster.includes('scraping') || fullTxt.includes('watercrawl') || fullTxt.includes('obscura');
    } else if (curDomain === 'doc') {
      matchesDomain = cat.includes('doc') || cat.includes('ocr') || cluster.includes('doc') || fullTxt.includes('docling') || fullTxt.includes('anydoc');
    } else if (curDomain === '3d') {
      matchesDomain = cat.includes('3d') || cat.includes('graphics') || cluster.includes('3d') || fullTxt.includes('three');
    } else if (curDomain === 'rust') {
      matchesDomain = fullTxt.includes('rust') || fullTxt.includes('omarchy') || fullTxt.includes('serverbox');
    } else if (curDomain === 'other') {
      const isStandard = cat.includes('design') || cat.includes('frontend') || cat.includes('media') || cat.includes('agent') || cat.includes('scraping') || cat.includes('doc') || cat.includes('3d') || fullTxt.includes('rust');
      matchesDomain = !isStandard;
    }

    const story = c.portfolio_story || {};
    const searchTxt = (c.title + ' ' + (c.title_zh || '') + ' ' + (c.title_en || '') + ' ' + cat + ' ' + (story.the_hook || '') + ' ' + (c.curation?.personal_motivation || '')).toLowerCase();
    const matchesSearch = searchTxt.includes(curSearch.toLowerCase());

    return matchesMode && matchesDomain && matchesSearch;
  });

  sortCollection(filtered, curSort);

  safeSetTxt('resultsCountLabel', lang === 'KO' ? `총 ${filtered.length}건 표시 (전체 ${lCases.length}건 중)` : (lang === 'ZH' ? `显示 ${filtered.length} 项 (共 ${lCases.length} 项)` : `Showing ${filtered.length} of ${lCases.length} dossiers`));

  const totalPages = Math.ceil(filtered.length / PORTFOLIO_PAGE_SIZE) || 1;
  if (curPage > totalPages) curPage = totalPages;
  if (curPage < 1) curPage = 1;
  setPortfolioPage(curPage);

  renderPagination('portfolioPagination', curPage, totalPages, 'changePortfolioPage');

  if (filtered.length === 0) {
    grid.innerHTML = `<div class="col-span-full py-16 text-center text-ink-muted font-medium">${lang === 'KO' ? '일치하는 기술 검증 보고서가 없습니다.' : (lang === 'ZH' ? '未找到符合条件的技术核查报告。' : 'No matching fact-check dossiers found.')}</div>`;
    return;
  }

  const pagedItems = filtered.slice((curPage - 1) * PORTFOLIO_PAGE_SIZE, curPage * PORTFOLIO_PAGE_SIZE);
  const fragment = document.createDocumentFragment();

  pagedItems.forEach((c, idx) => {
    const curation = c.curation || { discovery_mode: 'USER_CURATED' };
    const isUserMode = curation.discovery_mode === 'USER_CURATED';
    
    const parseDate = (d) => {
      if (!d) return '2026-09-02';
      const m = String(d).match(/([0-9][0-9][0-9][0-9])[-_]([0-9][0-9])[-_]([0-9][0-9])/);
      return m ? `${m[1]}-${m[2]}-${m[3]}` : '2026-09-02';
    };
    const srcDate = parseDate(c.source_published_date || c.investigation_date);
    const invDate = parseDate(c.investigation_date || c.source_published_date);
    const confScore = Number(c.confidence_score) || 95.0;
    const verdictStr = String(c.verdict || '');
    const isVerifiedTrue = verdictStr === 'VERIFIED_TRUE';
    const isHalfTrue = verdictStr.includes('HALF');

    const { displayTitle, displayHook } = getLocalizedContent(c, lang);
    let displayMotivation = displayHook;
    let displayTruth = displayHook || 'Empirical benchmark completed.';

    let motivationHtml = displayMotivation;
    const tagMatch = displayMotivation.match(new RegExp('^\\\\[(.*?)\\\\]\\\s*(.*)$'));
    if (tagMatch) {
      motivationHtml = `<span class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold font-mono bg-indigo-50 text-indigo-700 border border-indigo-200 mr-1.5">${tagMatch[1]}</span><span>${tagMatch[2]}</span>`;
    }

    let verdictLabel = '';
    let verdictClass = '';
    let dotClass = '';

    if (isVerifiedTrue) {
      verdictLabel = lang === 'KO' ? '사실 검증됨' : (lang === 'ZH' ? '经实测属实' : 'VERIFIED TRUE');
      verdictClass = 'verdict-true';
      dotClass = 'bg-emerald-600';
    } else if (isHalfTrue) {
      verdictLabel = lang === 'KO' ? '절반의 사실' : (lang === 'ZH' ? '部分属实' : 'HALF TRUE');
      verdictClass = 'verdict-half';
      dotClass = 'bg-amber-600';
    } else {
      verdictLabel = lang === 'KO' ? '과장/왜곡' : (lang === 'ZH' ? '夸大/失真' : 'EXAGGERATED');
      verdictClass = 'verdict-gamed';
      dotClass = 'bg-rose-600';
    }

    const card = document.createElement('div');
    card.className = 'executive-card p-4 sm:p-6 flex flex-col justify-between cursor-pointer space-y-4 group';
    card.onclick = () => openModal(c);

    card.innerHTML = `
      <div class="space-y-3.5">
        <div class="flex items-center justify-between text-xs gap-2 flex-wrap">
          <div class="flex items-center gap-1.5 sm:gap-2 flex-wrap">
            <span class="text-xs font-mono font-bold text-ink-muted">#${String((curPage - 1) * PORTFOLIO_PAGE_SIZE + idx + 1).padStart(2, '0')}</span>
            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold font-mono ${isUserMode ? 'bg-indigo-50 text-indigo-700 border border-indigo-200' : 'bg-emerald-50 text-emerald-700 border border-emerald-200'}">
              ${isUserMode ? (lang === 'KO' ? '직접 큐레이션' : (lang === 'ZH' ? '手动精选' : 'USER CURATED')) : (lang === 'KO' ? '자동 트렌드' : (lang === 'ZH' ? '自动趋势' : 'AUTO HARVEST'))}
            </span>
            <div class="flex items-center gap-1.5 text-[11px] font-mono text-ink-muted">
              <span title="${lang === 'KO' ? '수집/원출처 발행일' : (lang === 'ZH' ? '采集/原文发布日' : 'Source Date')}">📅 ${srcDate}</span>
              <span>•</span>
              <span title="${lang === 'KO' ? '심층 기술 분석일' : (lang === 'ZH' ? '深度分析日' : 'Audit Date')}" class="text-indigo-700 font-semibold">🔬 ${invDate}</span>
            </div>
          </div>

          <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold font-mono flex items-center gap-1.5 ${verdictClass}">
            <span class="w-1.5 h-1.5 rounded-full ${dotClass}"></span>
            ${verdictLabel}
          </span>
        </div>

        <div class="space-y-1">
          <span class="text-[11px] text-ink-muted font-mono font-semibold uppercase tracking-wider">${c.category || 'AI Technology'}</span>
          <h3 class="font-bold text-base text-ink-primary group-hover:text-indigo-600 transition leading-snug">
            ${displayTitle}
          </h3>
        </div>

        <div class="space-y-2 pt-1">
          <div class="p-3 rounded-xl bg-surface-subtle border border-surface-border text-xs space-y-1">
            <div class="text-[11px] font-bold text-ink-secondary flex items-center gap-1.5">
              <i data-lucide="compass" class="w-3.5 h-3.5 text-indigo-600"></i> ${t.cardMotivationLabel}
            </div>
            <p class="text-xs text-ink-secondary leading-relaxed line-clamp-2">${motivationHtml}</p>
          </div>

          <div class="p-3 rounded-xl bg-emerald-50/70 border border-emerald-200 text-xs space-y-1">
            <div class="text-[11px] font-bold text-emerald-900 flex items-center gap-1.5">
              <i data-lucide="zap" class="w-3.5 h-3.5 text-emerald-700"></i> ${t.cardVerdictLabel}
            </div>
            <p class="text-xs text-emerald-950 leading-relaxed font-medium line-clamp-2">${displayTruth}</p>
          </div>
        </div>

      </div>

      <div class="pt-3 border-t border-surface-border space-y-1.5 text-xs font-mono">
        <div class="flex items-center justify-between text-ink-muted text-[11px]">
          <span title="${lang === 'KO' ? '수집/원출처 발행일' : (lang === 'ZH' ? '采集/发布日' : 'Source Date')}">📅 ${srcDate}</span>
          <span class="text-emerald-700 font-bold flex items-center gap-1 font-sans">
            <i data-lucide="shield-check" class="w-3.5 h-3.5"></i> ${t.cardConfidenceLabel} ${confScore.toFixed(1)}%
          </span>
        </div>

        <div class="flex items-center justify-between text-indigo-700 text-[11px] font-semibold gap-2">
          <span title="${lang === 'KO' ? '심층 기술 분석일' : (lang === 'ZH' ? '深度分析日' : 'Audit Date')}" class="flex items-center gap-1.5 min-w-0 overflow-hidden">
            <span class="shrink-0">🔬 ${invDate}</span>
            <span class="text-ink-muted font-normal truncate min-w-0 align-bottom cursor-help" title="${c.curation?.audited_by_model || c.audited_by_model || 'gemini-3.8-flash-medium'}">(${formatModelAttribution(c.curation?.audited_by_model || c.audited_by_model || 'gemini-3.8-flash-medium')})</span>
          </span>
          <span class="text-ink-muted font-normal shrink-0">${(c.sources || []).length}${t.cardSourcesLabel}</span>
        </div>

        <div class="flex items-center justify-between pt-0.5 font-sans">
          <span class="text-[11px] text-ink-muted font-mono flex items-center gap-1">
            ${c.sources && c.sources.length > 0 ? `<a href="${c.sources[0].url}" target="_blank" onclick="event.stopPropagation();" class="text-indigo-600 hover:underline flex items-center gap-0.5 font-semibold">📄 ${lang === 'KO' ? '원문' : (lang === 'ZH' ? '原文' : 'Source')} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>` : ''}
          </span>
          <button class="text-ink-primary font-bold text-xs group-hover:translate-x-0.5 transition flex items-center gap-1 cursor-pointer">
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

export function setModeFilter(mode) {
  window.currentPortfolioPage = 1;
  window.currentMode = mode;
  document.querySelectorAll('.segment-btn').forEach(btn => btn.classList.remove('active'));
  if (mode === 'ALL') {
    const el = document.getElementById('modeBtnAll');
    if (el) el.classList.add('active');
  } else if (mode === 'USER_CURATED') {
    const el = document.getElementById('modeBtnUser');
    if (el) el.classList.add('active');
  } else if (mode === 'AUTO_HARVESTED') {
    const el = document.getElementById('modeBtnAuto');
    if (el) el.classList.add('active');
  }
  renderCards();
}

export function setDomainFilter(dom) {
  window.currentPortfolioPage = 1;
  window.currentDomain = dom;
  document.querySelectorAll('.tag-pill').forEach(btn => {
    if (btn.dataset.domain === dom) btn.classList.add('active');
    else btn.classList.remove('active');
  });
  renderCards();
}

export function changeSort(val) {
  window.currentPortfolioPage = 1;
  window.currentSort = val;
  renderCards();
}

export function clearSearch() {
  window.currentPortfolioPage = 1;
  const input = document.getElementById('searchInput');
  if (input) input.value = '';
  window.searchQuery = '';
  const clearBtn = document.getElementById('clearSearchBtn');
  if (clearBtn) clearBtn.classList.add('hidden');
  renderCards();
}

if (typeof window !== 'undefined') {
  window.renderCards = renderCards;
  window.setModeFilter = setModeFilter;
  window.setDomainFilter = setDomainFilter;
  window.changeSort = changeSort;
  window.clearSearch = clearSearch;
}

