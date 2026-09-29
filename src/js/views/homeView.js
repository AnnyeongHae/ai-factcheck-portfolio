/**
 * ==============================================================================
 * Home Dashboard View (Radar Session, Top Picks & Instant Navigation)
 * ==============================================================================
 */

import {
  currentLang,
  liveCasesData,
  trendRadarData,
  AppStore
} from '../core/store.js';
import { sortCollection } from '../utils/collectionSorter.js';
import { formatDateTimeCompact } from '../utils/dateTime.js';
import { cleanPlatformName, formatRadarPointBadge } from '../utils/metricFormatter.js';
import { getLocalizedContent } from '../components/newsCard.js';
import { openModal, openCaseModal } from '../components/modal.js';
import { switchView } from './router.js';
import { renderModels } from '../components/modelsCard.js';
import { renderNews } from './newsView.js';

export let activeRadarSession = 1;

export function switchRadarSession(sessionNum) {
  activeRadarSession = sessionNum;
  window.activeRadarSession = sessionNum;
  renderRadarSession();
}

export function navigateFromRadar(view, searchKey, inboxId) {
  window.targetSelectedInboxId = inboxId || '';
  switchView(view);
  const cleanQ = (searchKey || '').trim();
  if (view === 'models') {
    window.currentModelsPage = 1;
    window.modelsSearchQuery = cleanQ;
    const inp = document.getElementById('modelsSearchInput');
    if (inp) inp.value = cleanQ;
    renderModels();
  } else if (view === 'news') {
    window.currentNewsPage = 1;
    window.currentNewsSearch = cleanQ.toLowerCase();
    const inp = document.getElementById('newsSearchInput');
    if (inp) inp.value = cleanQ;
    renderNews();
  }
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

export function renderRadarSession() {
  const radarData = (trendRadarData && trendRadarData.sessions) ? trendRadarData : (window.trendRadarData || {});
  if (!radarData.sessions) return;
  const sessionData = radarData.sessions[String(activeRadarSession)];
  if (!sessionData) return;

  const sLabels = {
    KO: ['1회 00시', '2회 06시', '3회 12시', '4회 18시'],
    ZH: ['1期 00点', '2期 06点', '3期 12点', '4期 18点'],
    EN: ['S1 00:00', 'S2 06:00', 'S3 12:00', 'S4 18:00']
  };
  const curLang = window.currentLang || currentLang || 'KO';
  const curLabels = sLabels[curLang] || sLabels['KO'];
  for (let i = 1; i <= 4; i++) {
    const btn = document.getElementById('radarBtn' + i);
    if (btn) {
      btn.innerText = curLabels[i - 1];
      if (i === activeRadarSession) {
        btn.className = 'px-2 py-0.5 rounded border border-emerald-600 bg-emerald-600 text-white font-bold shadow-xs transition cursor-pointer';
      } else {
        btn.className = 'px-2 py-0.5 rounded border border-surface-border bg-surface-subtle text-ink-muted hover:text-ink-primary hover:bg-slate-100 transition cursor-pointer font-medium';
      }
    }
  }

  const windowLabelEl = document.getElementById('trendRadarWindowLabel');
  const pulseDotEl = document.getElementById('trendRadarPulseDot');

  if (windowLabelEl) {
    const wLabel = (curLang === 'KO' ? sessionData.window_label_ko : (curLang === 'ZH' ? sessionData.window_label_zh : sessionData.window_label_en)) || sessionData.window_label;
    windowLabelEl.innerText = wLabel;
  }
  if (pulseDotEl) {
    if (sessionData.is_current) {
      pulseDotEl.className = 'w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse';
    } else if (sessionData.is_future) {
      pulseDotEl.className = 'w-1.5 h-1.5 rounded-full bg-amber-500';
    } else {
      pulseDotEl.className = 'w-1.5 h-1.5 rounded-full bg-slate-400';
    }
  }

  const bulletsContainer = document.getElementById('trendRadarBullets');
  if (bulletsContainer) {
    bulletsContainer.innerHTML = '';
    const items = sessionData.items || [];

    if (items.length > 0) {
      items.forEach((it, idx) => {
        const cleanPlatform = cleanPlatformName(it.platform || it.source_platform || 'AI Hub');
        let platformBadgeClass = 'bg-surface-subtle text-ink-primary border-surface-border';
        const pf = (it.platform_family || '').toLowerCase();
        if (pf.includes('github')) {
          platformBadgeClass = 'bg-slate-100 text-slate-800 border-slate-300';
        } else if (pf.includes('hugging')) {
          platformBadgeClass = 'bg-purple-50 text-purple-700 border-purple-200';
        } else if (pf.includes('arxiv')) {
          platformBadgeClass = 'bg-rose-50 text-rose-700 border-rose-200';
        } else if (pf.includes('hacker')) {
          platformBadgeClass = 'bg-amber-50 text-amber-800 border-amber-200';
        } else if (pf.includes('geek')) {
          platformBadgeClass = 'bg-blue-50 text-blue-700 border-blue-200';
        }

        const itemTitle = (curLang === 'KO' ? (it.title_ko || it.title) : (curLang === 'ZH' ? (it.title_zh || it.title) : (it.title_en || it.title))) || it.title;
        const itemSummary = (curLang === 'KO' ? (it.summary_ko || it.summary) : (curLang === 'ZH' ? (it.summary_zh || it.summary) : (it.summary_en || it.summary))) || it.summary;
        const factCheckBtnText = curLang === 'KO' ? '팩트체크' : (curLang === 'ZH' ? '事实核查' : 'Fact-Check');
        const pointBadgeHtml = formatRadarPointBadge(it, curLang);

        const itemCard = document.createElement('div');
        itemCard.className = 'group p-3 rounded-xl bg-surface-subtle/50 hover:bg-white border border-surface-border hover:border-emerald-400 hover:shadow-xs transition duration-150 flex flex-col gap-2';
        itemCard.innerHTML = `
          <div class="flex items-center justify-between gap-2">
            <div class="flex items-center gap-1.5 flex-wrap">
              <span class="w-5 h-5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200/80 flex items-center justify-center font-mono font-bold text-[10px] shrink-0">0${idx + 1}</span>
              <span class="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold ${platformBadgeClass} border">${cleanPlatform}</span>
              ${pointBadgeHtml}
              ${it.is_this_session ? `<span class="px-1.5 py-0.5 rounded-md text-[9px] font-mono font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-0.5"><i data-lucide="sparkles" class="w-2.5 h-2.5 text-emerald-700"></i><span>${curLang === 'KO' ? '실시간 신규' : (curLang === 'ZH' ? '实时更新' : 'Live New')}</span></span>` : ''}
            </div>
            <div class="flex items-center gap-1.5 shrink-0">
              ${it.case_id ? `
                <button onclick="openCaseModal('${it.case_id}')" class="text-[10px] font-mono font-bold px-2 py-0.5 rounded-md bg-emerald-100 text-emerald-800 border border-emerald-300 hover:bg-emerald-200 flex items-center gap-1 transition cursor-pointer">
                  <i data-lucide="shield-check" class="w-3 h-3 text-emerald-700"></i>
                  <span>${factCheckBtnText}</span>
                </button>
              ` : ''}
            </div>
          </div>

          <a href="${it.source_url}" target="_blank" rel="noopener noreferrer" class="group/title block">
            <div class="text-xs sm:text-[13px] font-bold text-ink-primary group-hover/title:text-emerald-700 transition flex items-center justify-between gap-2 leading-snug">
              <span class="line-clamp-1">${itemTitle}</span>
              <span class="text-[11px] font-mono text-emerald-700 shrink-0 flex items-center gap-0.5 opacity-80 group-hover/title:opacity-100 bg-emerald-50 hover:bg-emerald-100 px-1.5 py-0.5 rounded border border-emerald-200 transition">
                <i data-lucide="arrow-up-right" class="w-3 h-3"></i>
              </span>
            </div>
            ${itemSummary ? `<p class="text-[11px] text-ink-muted line-clamp-1 leading-relaxed mt-1">${itemSummary}</p>` : ''}
          </a>

          <div class="pt-1.5 border-t border-surface-border/60 flex items-center justify-between text-[10px] font-mono text-ink-muted flex-wrap gap-1">
            <span class="flex items-center gap-1"><i data-lucide="calendar" class="w-3 h-3 text-slate-400"></i><span class="font-medium">${curLang === 'KO' ? '발행' : (curLang === 'ZH' ? '发布' : 'Pub')}:</span> ${formatDateTimeCompact(it.published_at || it.harvested_at)}</span>
            <span class="flex items-center gap-1"><i data-lucide="download" class="w-3 h-3 text-slate-400"></i><span class="font-medium">${curLang === 'KO' ? '수집' : (curLang === 'ZH' ? '采集' : 'Rec')}:</span> ${formatDateTimeCompact(it.harvested_at)}</span>
          </div>
        `;
        bulletsContainer.appendChild(itemCard);
      });
    } else {
      const emptyMsg = curLang === 'KO' ? '이 회차에 등록된 트렌드 데이터가 없습니다.' : (curLang === 'ZH' ? '该时段暂无趋势数据。' : 'No trend data for this session.');
      bulletsContainer.innerHTML = `<div class="py-6 text-center text-xs text-ink-muted font-mono">${emptyMsg}</div>`;
    }
  }
  if (window.lucide) window.lucide.createIcons();
}

export function renderHomeTopPicks() {
  const container = document.getElementById('homeTopPicksContainer');
  if (!container) return;
  container.innerHTML = '';

  const cases = (window.liveCasesData && window.liveCasesData.length > 0) 
    ? window.liveCasesData 
    : (liveCasesData && liveCasesData.length > 0 ? liveCasesData : (AppStore.getCases() || []));
  const sortedCases = sortCollection([...cases], 'date-audit-desc');
  const top3 = sortedCases.slice(0, 3);
  const curLang = window.currentLang || currentLang || 'KO';

  top3.forEach(c => {
    const card = document.createElement('div');
    card.className = 'p-4 rounded-xl border border-surface-border bg-surface-subtle hover:bg-white hover:border-ink-primary hover:shadow-md transition cursor-pointer flex flex-col justify-between space-y-2.5';
    card.onclick = () => openModal(c);

    const isVerifiedTrue = c.verdict === 'VERIFIED_TRUE';
    const isHalfTrue = (c.verdict || '').includes('HALF');
    const badgeColor = isVerifiedTrue ? 'bg-emerald-50 text-emerald-800 border-emerald-200' : (isHalfTrue ? 'bg-amber-50 text-amber-900 border-amber-200' : 'bg-rose-50 text-rose-800 border-rose-200');
    const badgeLabel = isVerifiedTrue ? (curLang === 'KO' ? '사실 검증됨' : (curLang === 'ZH' ? '事实已核验' : 'Verified True')) : (isHalfTrue ? (curLang === 'KO' ? '절반의 사실' : (curLang === 'ZH' ? '部分属实' : 'Half True')) : (curLang === 'KO' ? '과장/왜곡' : (curLang === 'ZH' ? '夸大/失实' : 'Gamed/Hype')));

    const { displayTitle, displayHook } = getLocalizedContent(c, curLang);
    const displayDate = c.investigation_date || (c.source_published_date ? c.source_published_date.slice(0, 10) : '2026-09-04');

    card.innerHTML = `
      <div class="space-y-2">
        <div class="flex items-center justify-between text-xs font-mono">
          <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${badgeColor}">${badgeLabel}</span>
          <span class="text-ink-muted text-[11px] font-semibold">${c.confidence_score || 95}%</span>
        </div>
        <h4 class="text-xs sm:text-sm font-bold text-ink-primary line-clamp-2 leading-snug hover:text-indigo-600 transition">${displayTitle}</h4>
        <p class="text-[11px] text-ink-secondary line-clamp-2 leading-relaxed">${displayHook}</p>
      </div>
      <div class="pt-2 border-t border-surface-border flex items-center justify-between text-[10px] font-mono text-ink-muted">
        <span>🔬 ${curLang === 'KO' ? '분석일: ' : (curLang === 'ZH' ? '分析日: ' : 'Audited: ')}${displayDate}</span>
        <span class="font-bold text-indigo-700 flex items-center gap-0.5">${curLang === 'KO' ? '상세 보고서' : (curLang === 'ZH' ? '查看报告' : 'View Dossier')} <i data-lucide="arrow-right" class="w-3 h-3"></i></span>
      </div>
    `;
    container.appendChild(card);
  });
  if (window.lucide) window.lucide.createIcons({ root: container });
}
