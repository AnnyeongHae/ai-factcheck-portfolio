/**
 * ==============================================================================
 * Telemetry Dashboard, Countdown & Timeline Charts Component
 * Ingestion pulse visualization, Cron schedules, and multi-runner logs (GHA / Vercel / Voyage)
 * ==============================================================================
 */

import {
  currentLang,
  timeline24hData,
  actionsTelemetryData,
  liveInboxData,
  currentView
} from '../core/store.js';
import { i18n } from '../core/i18n.js';
import { getDynamicKstDate, getDynamicKstHour } from '../utils/dateTime.js';

export const cronScheduleConfig = [
  { id: 1, hour: 0, min: 17, slotKo: '1회차 (00:17)', slotZh: '第1轮 (00:17)', slotEn: 'Session 1 (00:17)', nameKo: '심야 글로벌 릴리스', nameZh: '深夜全球发布', nameEn: 'Midnight Global Release', estSec: 545, runId: '34133531110', actualDur: '9분 05초' },
  { id: 2, hour: 6, min: 17, slotKo: '2회차 (06:17)', slotZh: '第2轮 (06:17)', slotEn: 'Session 2 (06:17)', nameKo: '모닝 브리핑', nameZh: '早间简报', nameEn: 'Morning Briefing', estSec: 362, runId: '34096402553', actualDur: '6분 02초' },
  { id: 3, hour: 12, min: 17, slotKo: '3회차 (12:17)', slotZh: '第3轮 (12:17)', slotEn: 'Session 3 (12:17)', nameKo: '정오 레이더', nameZh: '正午雷达', nameEn: 'Noon Radar', estSec: 456, runId: '34064244121', actualDur: '7분 36초' },
  { id: 4, hour: 18, min: 17, slotKo: '4회차 (18:17)', slotZh: '第4轮 (18:17)', slotEn: 'Session 4 (18:17)', nameKo: '저녁 라운드업', nameZh: '晚间汇总', nameEn: 'Evening Roundup', estSec: 694, runId: '34048453203', actualDur: '11분 34초' }
];

export function recomputeTimeline24hFromLiveInbox() {
  const nowKst = getDynamicKstDate();
  const pad = (n) => String(n).padStart(2, '0');
  const curKstDateStr = `${nowKst.getFullYear()}-${pad(nowKst.getMonth() + 1)}-${pad(nowKst.getDate())}`;
  const curHour = getDynamicKstHour();

  const slotDefs = [
    { slot: '1회차 (00시)', short_slot: '00:00', hour: 0, range: '00:00 - 05:59', name: '심야 릴리스' },
    { slot: '2회차 (06시)', short_slot: '06:00', hour: 6, range: '06:00 - 11:59', name: '모닝 브리핑' },
    { slot: '3회차 (12시)', short_slot: '12:00', hour: 12, range: '12:00 - 17:59', name: '정오 레이더' },
    { slot: '4회차 (18시)', short_slot: '18:00', hour: 18, range: '18:00 - 23:59', name: '저녁 라운드업' }
  ];

  const counts = {
    0: { inbox: 0, news: 0, model: 0, enriched: 0 },
    6: { inbox: 0, news: 0, model: 0, enriched: 0 },
    12: { inbox: 0, news: 0, model: 0, enriched: 0 },
    18: { inbox: 0, news: 0, model: 0, enriched: 0 }
  };

  const parseKst = (raw) => {
    if (!raw || typeof raw !== 'string') return null;
    if (raw.includes('T')) {
      const dt = new Date(raw);
      if (!isNaN(dt.getTime())) {
        const utcMs = dt.getTime() + (dt.getTimezoneOffset() * 60000);
        const kstDt = new Date(utcMs + (9 * 3600 * 1000));
        return {
          dateStr: `${kstDt.getFullYear()}-${pad(kstDt.getMonth() + 1)}-${pad(kstDt.getDate())}`,
          hour: kstDt.getHours()
        };
      }
    } else if (/^\d{4}-\d{2}-\d{2}/.test(raw)) {
      return { dateStr: raw.substring(0, 10), hour: 0 };
    }
    return null;
  };

  const inbList = typeof window !== 'undefined' && window.liveInboxData ? window.liveInboxData : liveInboxData;
  inbList.forEach(it => {
    const rawTime = it.harvested_at || it.harvested_date || it.created_at || '';
    const kstHarvest = parseKst(rawTime);
    if (kstHarvest && kstHarvest.dateStr === curKstDateStr) {
      const slotHour = Math.floor(kstHarvest.hour / 6) * 6;
      if (counts[slotHour]) counts[slotHour].inbox++;
    }

    const isEnriched = it.is_classified || it.ai_enrichment;
    if (isEnriched) {
      const rawEnrichTime = (it.ai_enrichment && it.ai_enrichment.enriched_at) || it.updated_at || '';
      const kstEnrich = parseKst(rawEnrichTime);
      if (kstEnrich && kstEnrich.dateStr === curKstDateStr) {
        const slotHour = Math.floor(kstEnrich.hour / 6) * 6;
        if (counts[slotHour]) {
          counts[slotHour].enriched++;
          const isModel = it.item_type === 'MODEL' || (it.source_platform && (it.source_platform.includes('Models') || it.source_platform.includes('Hub')));
          if (isModel) counts[slotHour].model++;
          else counts[slotHour].news++;
        }
      }
    }
  });

  const totalToday = Object.values(counts).reduce((acc, cur) => acc + cur.inbox + cur.enriched, 0);
  if (totalToday > 0) {
    const tData = typeof window !== 'undefined' && window.timeline24hData ? window.timeline24hData : timeline24hData;
    const newTData = slotDefs.map(s => {
      const existing = (tData || []).find(d => d.hour === s.hour);
      const inboxCnt = (existing && existing.inbox_count > counts[s.hour].inbox) ? existing.inbox_count : counts[s.hour].inbox;
      const enrichedCnt = (existing && existing.enriched_count > counts[s.hour].enriched) ? existing.enriched_count : counts[s.hour].enriched;
      return {
        slot: s.slot,
        short_slot: s.short_slot,
        hour: s.hour,
        range: s.range,
        name: s.name,
        inbox_count: inboxCnt,
        enriched_count: enrichedCnt,
        model_count: counts[s.hour].model,
        news_count: counts[s.hour].news,
        is_current: (s.hour <= curHour && curHour < s.hour + 6),
        is_future: (s.hour > curHour)
      };
    });
    if (typeof window !== 'undefined') window.timeline24hData = newTData;
  }
}

export function renderTelemetryCharts() {
  if (typeof document === 'undefined') return;
  const nowKst = getDynamicKstDate();
  const pad = (n) => String(n).padStart(2, '0');
  const curKstDateStr = `${nowKst.getFullYear()}-${pad(nowKst.getMonth() + 1)}-${pad(nowKst.getDate())}`;
  const titleEl = document.getElementById('timelineTitleText');
  const isPending = typeof window !== 'undefined' && !!window._timelineIsPendingToday;
  const lang = typeof window !== 'undefined' && window.currentLang ? window.currentLang : currentLang;

  if (titleEl) {
    if (isPending) {
      titleEl.innerHTML = `${i18n[lang]?.timelineTitle || '당일 24시간 수집 타임라인'} (${curKstDateStr}) <span class="ml-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-300 inline-flex items-center gap-1 font-sans"><span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>1회차 실시간 집계 대기 중</span>`;
    } else {
      titleEl.innerText = `${i18n[lang]?.timelineTitle || '당일 24시간 수집 타임라인'} (${curKstDateStr})`;
    }
  }

  const tlContainer = document.getElementById('timeline24hChartContainer');
  if (tlContainer) {
    tlContainer.innerHTML = '';
    const tData = typeof window !== 'undefined' && window.timeline24hData ? window.timeline24hData : timeline24hData;
    const maxVal = Math.max(...(tData || []).map(d => Math.max(d.inbox_count || 0, d.enriched_count !== undefined ? d.enriched_count : ((d.news_count || 0) + (d.model_count || 0)))), 10);

    const curKstHour = getDynamicKstHour();
    (tData || []).forEach(d => {
      const enrichedCount = d.enriched_count !== undefined ? d.enriched_count : ((d.news_count || 0) + (d.model_count || 0));
      const hPct = (d.inbox_count > 0) ? Math.max(10, Math.round(((d.inbox_count) / maxVal) * 100)) : 0;
      const hEnrichedPct = (enrichedCount > 0) ? Math.max(10, Math.round((enrichedCount / maxVal) * 100)) : 0;
      const isCurrent = (d.hour <= curKstHour && curKstHour < d.hour + 6);
      const isFuture = (d.hour > curKstHour);

      const col = document.createElement('div');
      col.className = 'flex flex-col items-center justify-end h-full group relative cursor-pointer';
      col.innerHTML = `
        <div class="opacity-0 group-hover:opacity-100 transition-opacity absolute -top-16 z-20 pointer-events-none bg-ink-primary text-white text-[10px] font-mono py-1.5 px-2.5 rounded-lg shadow-lg whitespace-nowrap">
          <div class="font-bold text-indigo-300">${d.range}</div>
          <div class="text-indigo-200">📥 수집: ${d.inbox_count || 0}건</div>
          <div class="text-emerald-300">✨ AI요약: ${enrichedCount}건${d.backlog_cleared ? ` <span class="text-emerald-400 text-[9px] font-normal">(+${d.backlog_cleared} 백로그)</span>` : ''}</div>
          ${isCurrent ? (isPending ? '<div class="text-emerald-400 font-bold mt-0.5">⚡ 1회차 세션 파이프라인 인입 중</div>' : '<div class="text-emerald-400 font-bold mt-0.5">● 현재 세션 인입 중</div>') : (isFuture ? '<div class="text-slate-400 mt-0.5">예정 세션</div>' : '<div class="text-slate-300 mt-0.5">수집 완료</div>')}
        </div>

        <div class="flex items-center gap-1 text-[9px] sm:text-[10px] font-mono font-bold mb-1">
          <span class="${isCurrent ? 'text-indigo-600 font-extrabold' : 'text-ink-muted'}" title="수집 건수">${d.inbox_count || 0}</span>
          <span class="text-slate-300">/</span>
          <span class="${isCurrent ? 'text-emerald-600 font-extrabold' : 'text-emerald-600/80'}" title="AI 요약 건수">${enrichedCount}</span>
        </div>

        <div class="w-full max-w-[58px] sm:max-w-[76px] flex items-end justify-center gap-1 sm:gap-1.5 h-24 ${isFuture ? 'opacity-30' : ''}">
          <div class="flex-1 ${isCurrent ? 'bg-indigo-500 ring-2 ring-indigo-400 animate-pulse' : 'bg-indigo-600'} rounded-t-sm sm:rounded-t-md transition-all duration-500 hover:bg-indigo-700" style="height: ${hPct}%; min-height: 0;" title="수집량: ${d.inbox_count || 0}건"></div>
          <div class="flex-1 ${isCurrent ? 'bg-emerald-400 ring-1 ring-emerald-300' : 'bg-emerald-500'} rounded-t-sm sm:rounded-t-md transition-all duration-500 hover:bg-emerald-600" style="height: ${hEnrichedPct}%; min-height: 0;" title="AI 요약완료: ${enrichedCount}건"></div>
        </div>

        <span class="text-[10px] sm:text-[11px] font-mono font-bold ${isCurrent ? 'text-indigo-600 font-extrabold' : 'text-ink-muted'} mt-2 group-hover:text-indigo-600 transition text-center">
          ${d.slot}
        </span>
      `;
      tlContainer.appendChild(col);
    });

    const totCollected = (tData || []).reduce((acc, cur) => acc + (cur.inbox_count || 0), 0);
    const totEnriched = (tData || []).reduce((acc, cur) => acc + (cur.enriched_count !== undefined ? cur.enriched_count : ((cur.news_count || 0) + (cur.model_count || 0))), 0);
    const ftEl = document.getElementById('timelineFooterText');
    if (ftEl) {
      if (isPending) {
        ftEl.innerHTML = `⚡ <b class="text-indigo-700">${curKstDateStr} 1회차(00:00~06:00) 파이프라인 가동 중</b> │ 📊 전일 확정 실적: <b class="text-slate-800">${totCollected}건 수집</b> / <b class="text-emerald-700">${totEnriched}건 AI 분석</b>`;
      } else {
        ftEl.innerHTML = `⚡ 당일 24H 수집: <b class="text-indigo-700">${totCollected}건</b> │ ✨ AI 요약분석 완료: <b class="text-emerald-700">${totEnriched}건</b>`;
      }
    }
  }

  if (typeof window.renderRadarSession === 'function') {
    window.renderRadarSession();
  }
}

let _lastTelemetryMinute = -1;

export function renderPipelineTelemetryCards() {
  if (typeof document === 'undefined') return;
  const slotsContainer = document.getElementById('pipelineSlotsContainer');
  if (!slotsContainer) return;

  const tLang = (typeof window !== 'undefined' && window.currentLang ? window.currentLang : currentLang).toLowerCase();
  const aData = typeof window !== 'undefined' && window.actionsTelemetryData ? window.actionsTelemetryData : actionsTelemetryData;

  const usedMin = aData.monthly_used_minutes || 0.0;
  const remMin = aData.monthly_remaining_minutes || (2000.0 - usedMin);
  const usagePct = aData.monthly_usage_percent || 0.0;

  const usedEl = document.getElementById('quotaUsedMin');
  const remEl = document.getElementById('quotaRemMin');
  const progEl = document.getElementById('quotaProgressBar');
  if (usedEl) usedEl.innerText = `${usedMin}분`;
  if (remEl) remEl.innerText = `${remMin}분 (${100 - usagePct}%)`;
  if (progEl) progEl.style.width = `${Math.min(100, Math.max(2, usagePct))}%`;

  const nowKst = getDynamicKstDate();
  const curHour = nowKst.getHours();
  const curMin = nowKst.getMinutes();
  const curSec = nowKst.getSeconds();
  const curTotalSec = curHour * 3600 + curMin * 60 + curSec;
  const tData = typeof window !== 'undefined' && window.timeline24hData ? window.timeline24hData : timeline24hData;
  let cardsHtml = '';

  cronScheduleConfig.forEach((s, idx) => {
    const sTotalSec = s.hour * 3600 + s.min * 60;
    const isPast = curTotalSec >= sTotalSec + (s.estSec || 360);
    const isActive = curTotalSec >= sTotalSec && curTotalSec < sTotalSec + (s.estSec || 360);

    const sessionTitle = tLang === 'zh' ? s.slotZh : (tLang === 'en' ? s.slotEn : s.slotKo);
    const sessionSub = tLang === 'zh' ? s.nameZh : (tLang === 'en' ? s.nameEn : s.nameKo);

    const slotKeys = ['00:00', '06:00', '12:00', '18:00'];
    const slotKey = slotKeys[idx] || '00:00';
    const sLog = (aData.slot_logs && aData.slot_logs[slotKey]) ? aData.slot_logs[slotKey] : null;

    const tlMatch = (tData || []).find(d => d.hour === (idx * 6));
    const itemCount = (sLog && sLog.is_today && sLog.items_collected !== null && sLog.items_collected !== undefined)
      ? sLog.items_collected
      : (tlMatch ? (tlMatch.inbox_count || 0) : 0);

    let statusBadge = '';
    let timeInfo = '';
    let cardBorder = 'border-surface-border';
    let cardBg = 'bg-slate-50/50';

    const isRunToday = sLog && sLog.is_today;
    const isRunSuccess = isRunToday && (sLog.status === 'SUCCESS' || sLog.status === 'completed');
    const isRunActive = (sLog && sLog.status === 'in_progress') || isActive;

    if (isRunSuccess) {
      const actualDuration = sLog.actual_duration || (s.actualDur || '-');
      const errCount = (sLog && typeof sLog.error_count !== 'undefined') ? sLog.error_count : 0;

      cardBorder = 'border-emerald-200';
      cardBg = 'bg-emerald-50/30';
      statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1"><i data-lucide="check-circle" class="w-3 h-3 text-emerald-600"></i>${tLang === 'zh' ? '已完成' : (tLang === 'en' ? 'Completed' : '수집 완료')}</span>`;
      timeInfo = `<span>${tLang === 'zh' ? '实测耗时' : (tLang === 'en' ? 'Duration' : '실측 소요')}: <b class="text-ink-primary font-bold">${actualDuration}</b> · ${errCount} ${tLang === 'zh' ? '错误' : (tLang === 'en' ? 'errors' : '에러')}</span>`;
    } else if (isRunActive) {
      cardBorder = 'border-indigo-400 ring-2 ring-indigo-200';
      cardBg = 'bg-indigo-50/70';
      statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-600 text-white flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-white animate-ping"></span>${tLang === 'zh' ? '运行中' : (tLang === 'en' ? 'Running' : '수집 진행 중')}</span>`;
      timeInfo = `<span class="text-indigo-700 font-bold">${tLang === 'zh' ? '正在执行' : (tLang === 'en' ? 'Ingesting live...' : '실시간 파이프라인 가동')}</span>`;
    } else if (isPast && !isRunToday) {
      cardBorder = 'border-amber-300 ring-1 ring-amber-200';
      cardBg = 'bg-amber-50/40';
      statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300 flex items-center gap-1"><i data-lucide="clock" class="w-3 h-3 text-amber-600"></i>${tLang === 'zh' ? '队列等待中' : (tLang === 'en' ? 'Queue Waiting' : '⏳ 수집 큐 대기')}</span>`;
      timeInfo = `<span class="text-amber-700 font-medium">${tLang === 'zh' ? '已过调度时段 · GHA 队列等待中' : (tLang === 'en' ? 'Scheduled time elapsed · Waiting in GHA queue' : '예정 시각 경과 · Actions 큐 대기 중')}</span>`;
    } else {
      const slotDiffSec = sTotalSec - curTotalSec;
      const futH = Math.floor(slotDiffSec / 3600);
      const futM = Math.floor((slotDiffSec % 3600) / 60);
      statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-600 border border-slate-200 flex items-center gap-1"><i data-lucide="clock" class="w-3 h-3 text-slate-500"></i>${tLang === 'zh' ? '等待中' : (tLang === 'en' ? 'Scheduled' : '대기 중')}</span>`;
      timeInfo = `<span>${tLang === 'zh' ? '剩余' : (tLang === 'en' ? 'Remaining' : '남은 시간')}: <b class="text-indigo-600">${futH}h ${futM}m</b> · ${tLang === 'zh' ? '预计约' : (tLang === 'en' ? 'Est. ' : '예상 ')}${Math.round(s.estSec/60)}분</span>`;
    }

    cardsHtml += `
      <div class="p-3.5 rounded-xl border ${cardBorder} ${cardBg} flex flex-col justify-between space-y-2.5 transition">
        <div class="flex items-center justify-between">
          <span class="font-bold text-ink-primary text-xs">${sessionTitle}</span>
          ${statusBadge}
        </div>
        <div class="space-y-1">
          <div class="text-[11px] text-ink-secondary font-medium">${sessionSub}</div>
          <div class="text-xs font-bold text-ink-primary flex items-center justify-between">
            <span>${tLang === 'zh' ? '采集总量' : (tLang === 'en' ? 'Ingested' : '수집량')}:</span>
            <span class="text-indigo-600 font-mono">${itemCount}건</span>
          </div>
        </div>
        <div class="pt-2 border-t border-surface-border/60 text-[10px] text-ink-muted flex items-center justify-between">
          ${timeInfo}
        </div>
      </div>
    `;
  });
  slotsContainer.innerHTML = cardsHtml;
  if (typeof lucide !== 'undefined') lucide.createIcons({ root: slotsContainer });
}

export function updateCronCountdown() {
  if (typeof document === 'undefined') return;
  const curView = typeof window !== 'undefined' && window.currentView ? window.currentView : currentView;
  if (curView !== 'inbox') return;
  const countdownEl = document.getElementById('pipelineCountdownValue');
  if (!countdownEl) return;

  const nowKst = getDynamicKstDate();
  const curHour = nowKst.getHours();
  const curMin = nowKst.getMinutes();
  const curSec = nowKst.getSeconds();
  const curTotalSec = curHour * 3600 + curMin * 60 + curSec;

  let nextSlot = null;
  let diffSec = 0;

  for (let s of cronScheduleConfig) {
    const sTotalSec = s.hour * 3600 + s.min * 60;
    if (sTotalSec > curTotalSec) {
      nextSlot = s;
      diffSec = sTotalSec - curTotalSec;
      break;
    }
  }

  if (!nextSlot) {
    nextSlot = cronScheduleConfig[0];
    const eodSec = 24 * 3600 - curTotalSec;
    diffSec = eodSec + (nextSlot.hour * 3600 + nextSlot.min * 60);
  }

  const remH = Math.floor(diffSec / 3600);
  const remM = Math.floor((diffSec % 3600) / 60);
  const remS = diffSec % 60;
  const pad = (n) => String(n).padStart(2, '0');

  const tLang = (typeof window !== 'undefined' && window.currentLang ? window.currentLang : currentLang).toLowerCase();
  const slotName = tLang === 'zh' ? nextSlot.slotZh : (tLang === 'en' ? nextSlot.slotEn : nextSlot.slotKo);
  countdownEl.innerText = `${pad(remH)}:${pad(remM)}:${pad(remS)} (${slotName})`;

  if (_lastTelemetryMinute !== curMin) {
    _lastTelemetryMinute = curMin;
    renderPipelineTelemetryCards();
    renderRunsTable();
  }

  if (curSec === 17 && !document.hidden) {
    checkLiveActionsRuns();
  }
}

export function switchRunLogsTab(tab) {
  if (typeof window !== 'undefined') window.currentRunsTab = tab;
  const btnGha = document.getElementById('tabRunsGha');
  const btnVercel = document.getElementById('tabRunsVercel');
  const btnVoyage = document.getElementById('tabRunsVoyage');

  const inactiveCls = "px-2.5 py-1 rounded-md font-medium text-ink-secondary hover:text-ink-primary transition cursor-pointer";
  if (btnGha) btnGha.className = inactiveCls;
  if (btnVercel) btnVercel.className = inactiveCls;
  if (btnVoyage) btnVoyage.className = inactiveCls;

  if (tab === 'gha') {
    if (btnGha) btnGha.className = "px-2.5 py-1 rounded-md font-bold bg-white text-ink-primary shadow-xs border border-surface-border transition cursor-pointer";
  } else if (tab === 'vercel') {
    if (btnVercel) btnVercel.className = "px-2.5 py-1 rounded-md font-bold bg-white text-indigo-700 shadow-xs border border-indigo-200 transition cursor-pointer";
  } else if (tab === 'voyage') {
    if (btnVoyage) btnVoyage.className = "px-2.5 py-1 rounded-md font-bold bg-white text-emerald-800 shadow-xs border border-emerald-300 transition cursor-pointer";
  }
  renderRunsTable();
}

export function renderRunsTable() {
  if (typeof document === 'undefined') return;
  const thead = document.getElementById('pipelineRecentRunsThead');
  const tbody = document.getElementById('pipelineRecentRunsTbody');
  if (!tbody || !thead) return;

  const tLang = (typeof window !== 'undefined' && window.currentLang ? window.currentLang : currentLang).toLowerCase();
  const aData = typeof window !== 'undefined' && window.actionsTelemetryData ? window.actionsTelemetryData : actionsTelemetryData;
  const curTab = typeof window !== 'undefined' && window.currentRunsTab ? window.currentRunsTab : 'gha';

  if (curTab === 'gha') {
    thead.innerHTML = `
      <tr>
        <th class="py-2.5 px-3">실행 시각 (KST)</th>
        <th class="py-2.5 px-3">워크플로우</th>
        <th class="py-2.5 px-3">트리거</th>
        <th class="py-2.5 px-3">소요 시간</th>
        <th class="py-2.5 px-3" title="신규 인입 건수 및 5대 플랫폼 스캔 후보 총량">수집 결과 (신규/스캔)</th>
        <th class="py-2.5 px-3">상태</th>
        <th class="py-2.5 px-3">에러</th>
      </tr>
    `;
    if (aData.runs && aData.runs.length > 0) {
      let rowsHtml = '';
      aData.runs.forEach(r => {
        const isSuccess = r.conclusion === 'success';
        const isCancelled = r.conclusion === 'cancelled';
        const statusCls = isSuccess ? 'bg-emerald-100 text-emerald-800 border-emerald-300' : (isCancelled ? 'bg-amber-100 text-amber-800 border-amber-300' : 'bg-indigo-100 text-indigo-800 border-indigo-300');
        const statusLabel = isSuccess ? (tLang === 'zh' ? '成功' : (tLang === 'en' ? 'Success' : '성공')) : (isCancelled ? (tLang === 'zh' ? '已取消' : (tLang === 'en' ? 'Cancelled' : '취소')) : (tLang === 'zh' ? '运行中' : (tLang === 'en' ? 'Running' : '진행중')));
        
        let itemsCell = '-';
        let collectedCount = 0;
        let scannedCount = 0;
        let hasCollected = false;
        let hasScanned = false;

        if (typeof r.items_collected === 'number') {
          collectedCount = r.items_collected;
          hasCollected = true;
        } else if (typeof r.items_collected === 'string') {
          const m = r.items_collected.match(/\d+/);
          if (m) {
            if (r.items_collected.includes('스캔')) {
              scannedCount = parseInt(m[0], 10);
              hasScanned = true;
            } else {
              collectedCount = parseInt(m[0], 10);
              hasCollected = true;
            }
          }
        }

        if (typeof r.items_scanned === 'number') {
          scannedCount = r.items_scanned;
          hasScanned = true;
        } else if (typeof r.items_scanned === 'string') {
          const m = r.items_scanned.match(/\d+/);
          if (m) {
            scannedCount = parseInt(m[0], 10);
            hasScanned = true;
          }
        }

        const isNonHarvestWorkflow = r.event === 'push' || 
          (!hasCollected && !hasScanned) || 
          (collectedCount === 0 && scannedCount === 0) ||
          (r.items_collected === null && r.items_scanned === null);

        if (isNonHarvestWorkflow) {
          if (r.event === 'schedule' && (r.status === 'in_progress' || r.status === 'queued')) {
            itemsCell = `<span class="text-amber-600 animate-pulse font-medium">수집 진행 중...</span>`;
          } else {
            itemsCell = `<span class="text-ink-muted">-</span>`;
          }
        } else if (hasCollected && hasScanned) {
          const colLabel = tLang === 'zh' ? '条采集' : (tLang === 'en' ? 'collected' : '건 수집');
          const scanLabel = tLang === 'zh' ? '条扫描' : (tLang === 'en' ? 'scanned' : '건 스캔');
          itemsCell = `<span class="font-bold text-indigo-700">${collectedCount}${colLabel}</span> <span class="text-[10px] text-ink-muted">/ ${scannedCount}${scanLabel}</span>`;
        } else if (hasCollected && collectedCount > 0) {
          const colLabel = tLang === 'zh' ? '条采集' : (tLang === 'en' ? 'collected' : '건 수집');
          itemsCell = `<span class="font-bold text-indigo-700">${collectedCount}${colLabel}</span>`;
        } else if (hasScanned && scannedCount > 0) {
          const colLabel = tLang === 'zh' ? '条采集' : (tLang === 'en' ? 'collected' : '건 수집');
          const scanLabel = tLang === 'zh' ? '条扫描' : (tLang === 'en' ? 'scanned' : '건 스캔');
          itemsCell = `<span class="font-bold text-indigo-700">0${colLabel}</span> <span class="text-[10px] text-ink-muted">/ ${scannedCount}${scanLabel}</span>`;
        } else {
          itemsCell = `<span class="text-ink-muted">-</span>`;
        }

        rowsHtml += `
          <tr class="hover:bg-slate-50/80 transition">
            <td class="py-2.5 px-3 font-bold text-ink-primary text-[11px]">${r.created_at_kst}</td>
            <td class="py-2.5 px-3 font-medium text-ink-secondary">${r.name.length > 32 ? r.name.slice(0, 30) + '...' : r.name}</td>
            <td class="py-2.5 px-3 text-ink-muted"><span class="px-1.5 py-0.5 rounded bg-slate-100 text-[10px] border border-slate-200">${r.event}</span></td>
            <td class="py-2.5 px-3 font-bold text-ink-primary">${r.duration_str}</td>
            <td class="py-2.5 px-3 font-mono font-semibold">${itemsCell}</td>
            <td class="py-2.5 px-3">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${statusCls} inline-flex items-center gap-1">
                ${statusLabel}
              </span>
            </td>
            <td class="py-2.5 px-3 font-bold ${r.error_count > 0 ? 'text-rose-600' : 'text-emerald-600'}">${r.error_count || 0} errors</td>
          </tr>
        `;
      });
      tbody.innerHTML = rowsHtml;
    } else {
      tbody.innerHTML = `<tr><td colspan="7" class="py-4 text-center text-ink-muted">기록된 수집 실행 로그가 없습니다.</td></tr>`;
    }
  } else if (curTab === 'vercel') {
    thead.innerHTML = `
      <tr>
        <th class="py-2.5 px-3">실행 시각 (KST)</th>
        <th class="py-2.5 px-3">서버리스 워커</th>
        <th class="py-2.5 px-3">AI 모델</th>
        <th class="py-2.5 px-3">소요 시간</th>
        <th class="py-2.5 px-3">처리 건수</th>
        <th class="py-2.5 px-3">잔여 미처리</th>
        <th class="py-2.5 px-3">상태</th>
      </tr>
    `;
    const vRuns = window.vercelWorkerRunsData || [];
    if (vRuns.length > 0) {
      let rowsHtml = '';
      vRuns.forEach(r => {
        const isSuccess = r.status === 'SUCCESS';
        const statusCls = isSuccess ? 'bg-emerald-100 text-emerald-800 border-emerald-300' : 'bg-rose-100 text-rose-800 border-rose-300';
        const shortModel = (r.model_used || 'openrouter-free').split('/').pop().replace(':free', '');
        rowsHtml += `
          <tr class="hover:bg-slate-50/80 transition">
            <td class="py-2.5 px-3 font-bold text-ink-primary text-[11px]">${r.created_at_kst}</td>
            <td class="py-2.5 px-3 font-medium text-ink-secondary flex items-center gap-1">
              <span class="w-1.5 h-1.5 rounded-full bg-indigo-500"></span> ${r.worker_name || 'AI Enricher'}
            </td>
            <td class="py-2.5 px-3 text-ink-muted font-mono text-[11px]"><span class="px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700 text-[10px] border border-indigo-200">${shortModel}</span></td>
            <td class="py-2.5 px-3 font-bold text-ink-primary">${r.duration_str}</td>
            <td class="py-2.5 px-3 font-mono font-semibold text-emerald-600">${r.processed_count}건 요약</td>
            <td class="py-2.5 px-3 font-mono font-medium text-amber-700">${r.remaining_count}건 대기</td>
            <td class="py-2.5 px-3">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${statusCls} inline-flex items-center gap-1">
                ${isSuccess ? '성공' : '실패'}
              </span>
            </td>
          </tr>
        `;
      });
      tbody.innerHTML = rowsHtml;
    } else {
      tbody.innerHTML = `<tr><td colspan="7" class="py-4 text-center text-ink-muted">최근 Vercel Serverless AI 워커 실행 기록 대기 중...</td></tr>`;
    }
  } else if (curTab === 'voyage') {
    thead.innerHTML = `
      <tr>
        <th class="py-2.5 px-3">실행 시각 (KST)</th>
        <th class="py-2.5 px-3">임베딩 엔진</th>
        <th class="py-2.5 px-3">소요 시간</th>
        <th class="py-2.5 px-3">처리 건수</th>
        <th class="py-2.5 px-3">병합 건수</th>
        <th class="py-2.5 px-3">소요 토큰</th>
        <th class="py-2.5 px-3">잔여 미임베딩</th>
        <th class="py-2.5 px-3">상태</th>
      </tr>
    `;
    const voyRuns = window.voyageWorkerRunsData || [];
    if (voyRuns.length > 0) {
      let rowsHtml = '';
      voyRuns.slice(0, 6).forEach(r => {
        const isSuccess = r.status === 'SUCCESS';
        const statusCls = isSuccess ? 'bg-emerald-100 text-emerald-800 border-emerald-300' : 'bg-rose-100 text-rose-800 border-rose-300';
        const mergedBadge = (r.merged_count && r.merged_count > 0)
          ? `<span class="px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 text-[10px] font-bold border border-purple-200">${r.merged_count}건 병합</span>`
          : `<span class="text-ink-muted text-xs">-</span>`;
        const tokensStr = typeof r.tokens_used === 'number' ? r.tokens_used.toLocaleString() + ' tok' : '-';
        const remainingStr = typeof r.remaining_count === 'number' ? r.remaining_count.toLocaleString() + '건 대기' : '-';

        rowsHtml += `
          <tr class="hover:bg-slate-50/80 transition">
            <td class="py-2.5 px-3 font-bold text-ink-primary text-[11px]">${r.created_at_kst}</td>
            <td class="py-2.5 px-3 font-medium text-emerald-800 flex items-center gap-1 font-mono text-[11px]">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span> ${r.engine || 'voyage-4-lite'}
            </td>
            <td class="py-2.5 px-3 font-bold text-ink-primary">${r.duration_str}</td>
            <td class="py-2.5 px-3 font-mono font-semibold text-emerald-700">${r.processed_count}건 임베딩</td>
            <td class="py-2.5 px-3 font-mono">${mergedBadge}</td>
            <td class="py-2.5 px-3 font-mono text-[11px] text-ink-secondary">${tokensStr}</td>
            <td class="py-2.5 px-3 font-mono font-medium text-amber-700">${remainingStr}</td>
            <td class="py-2.5 px-3">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${statusCls} inline-flex items-center gap-1">
                ${isSuccess ? '성공' : '실패'}
              </span>
            </td>
          </tr>
        `;
      });
      tbody.innerHTML = rowsHtml;
    } else {
      tbody.innerHTML = `<tr><td colspan="8" class="py-4 text-center text-ink-muted">최근 Voyage AI 임베딩 실행 기록 대기 중... ('⚡ Voyage 임베딩' 버튼을 클릭하면 실시간 배치 작업이 시작됩니다)</td></tr>`;
    }
  }
  if (typeof lucide !== 'undefined') lucide.createIcons({ root: tbody });
}

let lastPolledTime = 0;
export async function checkLiveActionsRuns() {
  const now = Date.now();
  if (now - lastPolledTime < 45000 || (typeof document !== 'undefined' && document.hidden)) return;
  lastPolledTime = now;
  const ctrl = new AbortController();
  const tid = setTimeout(() => ctrl.abort(), 2500);
  try {
    const resp = await fetch('https://api.github.com/repos/AnnyeongHae/ai-factcheck-portfolio/actions/runs?per_page=6', {
      headers: { 'Accept': 'application/vnd.github.v3+json' },
      signal: ctrl.signal
    });
    clearTimeout(tid);
    if (!resp.ok) return;
    const data = await resp.json();
    const liveRuns = data.workflow_runs || [];
    if (!liveRuns.length) return;

    const kstTz = 9 * 60;
    const pad = (n) => String(n).padStart(2, '0');
    const runs = liveRuns.map(r => {
      const cDate = new Date(r.created_at);
      const uDate = new Date(r.updated_at);
      const durSec = Math.max(1, Math.floor((uDate - cDate) / 1000));
      const durStr = `${Math.floor(durSec / 60)}분 ${durSec % 60}초`;
      const kstTime = new Date(cDate.getTime() + (kstTz + cDate.getTimezoneOffset()) * 60000);
      const kstStr = `${kstTime.getFullYear()}-${pad(kstTime.getMonth()+1)}-${pad(kstTime.getDate())} ${pad(kstTime.getHours())}:${pad(kstTime.getMinutes())}:${pad(kstTime.getSeconds())}`;

      const isSuccess = r.conclusion === 'success';
      const isCancelled = r.conclusion === 'cancelled';
      const isFailure = r.conclusion === 'failure' || r.conclusion === 'timed_out';
      const errCount = isFailure ? 1 : 0;
      const existingRuns = (typeof window !== 'undefined' && window.actionsTelemetryData?.runs) || actionsTelemetryData.runs || [];
      const existingRun = existingRuns.find(x => String(x.id) === String(r.id));

      return {
        id: String(r.id),
        name: r.name,
        event: r.event,
        status: r.status,
        conclusion: r.conclusion || r.status,
        duration_str: durStr,
        duration_sec: durSec,
        items_collected: existingRun?.items_collected || null,
        items_scanned: existingRun?.items_scanned || null,
        created_at_kst: kstStr,
        html_url: r.html_url,
        error_count: errCount
      };
    });

    if (typeof window !== 'undefined') {
      window.actionsTelemetryData = window.actionsTelemetryData || {};
      window.actionsTelemetryData.runs = runs;
    }
    actionsTelemetryData.runs = runs;

    renderRunsTable();
    renderPipelineTelemetryCards();
  } catch (e) {}
}

if (typeof window !== 'undefined') {
  window.cronScheduleConfig = cronScheduleConfig;
  window.recomputeTimeline24hFromLiveInbox = recomputeTimeline24hFromLiveInbox;
  window.renderTelemetryCharts = renderTelemetryCharts;
  window.renderPipelineTelemetryCards = renderPipelineTelemetryCards;
  window.updateCronCountdown = updateCronCountdown;
  window.switchRunLogsTab = switchRunLogsTab;
  window.switchRunsTab = switchRunLogsTab;
  window.renderRunsTable = renderRunsTable;
  window.checkLiveActionsRuns = checkLiveActionsRuns;
  setInterval(updateCronCountdown, 1000);
}
