/**
 * ==============================================================================
 * Popover & Multi-Source Cluster Dropdown Component
 * Handles unified source grouping, responsive viewport clamping, and ESC dismiss
 * ==============================================================================
 */

import { currentLang } from '../core/store.js';
import { cleanPlatformName, getPlatformImpactWeight } from '../utils/metricFormatter.js';

export function isCommunity(s) {
  const p = (s.platform || s.source_name || '').toLowerCase();
  const u = (s.url || '#').toLowerCase();
  return p.includes('hacker news') || u.includes('ycombinator') ||
         p.includes('reddit') || u.includes('reddit.com') ||
         p.includes('geeknews') || u.includes('hada.io') ||
         p.includes('pytorch') ||
         p.includes('github') || u.includes('github.com') ||
         p.includes('space') || u.includes('/spaces/') ||
         p.includes('hugging') || u.includes('huggingface.co') ||
         p.includes('arxiv') || u.includes('arxiv.org') ||
         p.includes('youtube') || u.includes('youtube.com') ||
         p.includes('twitter') || p.includes(' x') || u.includes('x.com');
}

export function getSourceMeta(s) {
  const p = (s.platform || s.source_name || '').toLowerCase();
  const u = (s.url || '#').toLowerCase();
  const cleanName = cleanPlatformName(s.platform || s.source_name);
  const lang = typeof window !== 'undefined' && window.currentLang ? window.currentLang : currentLang;
  let icon = '📄';
  let label = cleanName || (lang === 'KO' ? '원문' : 'Source');
  let badgeCls = 'bg-surface-subtle text-ink-secondary hover:text-ink-primary border-surface-border';
  let isComm = false;

  if (p.includes('hacker news') || u.includes('ycombinator')) {
    icon = '🔥';
    label = lang === 'KO' ? 'HN 토론' : 'HN';
    badgeCls = 'bg-orange-50 text-orange-800 hover:text-orange-950 border-orange-200';
    isComm = true;
  } else if (p.includes('geeknews') || u.includes('hada.io')) {
    icon = '💬';
    label = lang === 'KO' ? '긱뉴스' : 'GeekNews';
    badgeCls = 'bg-indigo-50 text-indigo-800 hover:text-indigo-950 border-indigo-200';
    isComm = true;
  } else if (p.includes('pytorch')) {
    icon = '🇰🇷';
    label = 'PyTorchKR';
    badgeCls = 'bg-purple-50 text-purple-800 hover:text-purple-950 border-purple-200';
    isComm = true;
  } else if (p.includes('reddit')) {
    icon = '🤖';
    label = lang === 'KO' ? '레딧' : 'Reddit';
    badgeCls = 'bg-red-50 text-red-800 hover:text-red-950 border-red-200';
    isComm = true;
  } else if (p.includes('github')) {
    icon = '🐙';
    label = 'GitHub';
    badgeCls = 'bg-slate-100 text-slate-800 hover:text-slate-950 border-slate-300';
    isComm = true;
  } else if (p.includes('space') || u.includes('/spaces/')) {
    icon = '🤗';
    label = 'HF Spaces';
    badgeCls = 'bg-amber-50 text-amber-900 hover:text-amber-950 border-amber-200';
    isComm = true;
  } else if (p.includes('hugging') || u.includes('huggingface.co')) {
    icon = '🤗';
    label = 'HuggingFace';
    badgeCls = 'bg-amber-50 text-amber-900 hover:text-amber-950 border-amber-200';
    isComm = true;
  } else if (p.includes('arxiv')) {
    icon = '📑';
    label = 'ArXiv';
    badgeCls = 'bg-rose-50 text-rose-900 hover:text-rose-950 border-rose-200';
    isComm = true;
  } else if (p.includes('youtube') || u.includes('youtube.com') || u.includes('youtu.be')) {
    icon = '📺';
    label = lang === 'KO' ? '유튜브' : 'YouTube';
    badgeCls = 'bg-red-50 text-red-800 hover:text-red-950 border-red-200';
    isComm = true;
  } else if (p.includes('twitter') || p.includes(' x') || u.includes('x.com') || u.includes('twitter.com')) {
    icon = '𝕏';
    label = 'X (트위터)';
    badgeCls = 'bg-zinc-100 text-zinc-800 hover:text-zinc-950 border-zinc-300';
    isComm = true;
  } else {
    // Press / Official News
    icon = '📰';
    label = cleanName || (lang === 'KO' ? '보도' : 'Press');
    badgeCls = 'bg-emerald-50 text-emerald-800 hover:text-emerald-950 border-emerald-200';
    isComm = false;
  }

  return {
    icon,
    label,
    cleanPlatform: cleanName,
    badgeCls,
    url: s.url || '#',
    title: s.title || '',
    weight: getPlatformImpactWeight(s.platform || s.source_name),
    isCommunity: isComm
  };
}

export function buildMultiSourceCluster(rawSources, rawItemId) {
  if (!rawSources || rawSources.length === 0) return '';
  const lang = typeof window !== 'undefined' && window.currentLang ? window.currentLang : currentLang;

  const seenUrls = new Set();
  const sources = [];
  for (const s of rawSources) {
    const u = (s.url || '#').toLowerCase().replace(/[?#].*$/, '');
    const meta = getSourceMeta(s);
    const dedupeKey = `${meta.cleanPlatform.toLowerCase()}::${u}`;
    if (u !== '#' && seenUrls.has(dedupeKey)) continue;
    seenUrls.add(dedupeKey);
    sources.push({ ...s, meta });
  }

  if (sources.length === 0) return '';

  const pressSources = sources.filter(s => !s.meta.isCommunity);
  const communitySources = sources.filter(s => s.meta.isCommunity);

  pressSources.sort((a, b) => b.meta.weight - a.meta.weight);
  communitySources.sort((a, b) => b.meta.weight - a.meta.weight);

  const total = sources.length;
  const safeId = 'src_' + String(rawItemId || Math.random()).replace(/[^a-zA-Z0-9_-]/g, '_');

  if (total === 1) {
    const m = sources[0].meta;
    return `<a href="${m.url}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded-md ${m.badgeCls} border text-[11px] font-bold flex items-center gap-1 shrink-0 transition shadow-xs">${m.icon} ${m.label} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>`;
  }

  const directButtons = [];
  if (pressSources.length > 0 && communitySources.length > 0) {
    directButtons.push(pressSources[0]);
    directButtons.push(communitySources[0]);
  } else if (pressSources.length > 0) {
    directButtons.push(...pressSources.slice(0, 2));
  } else {
    directButtons.push(...communitySources.slice(0, 2));
  }

  let html = `<div class="flex items-center gap-1.5 flex-wrap justify-end relative">`;

  directButtons.forEach(s => {
    const m = s.meta;
    html += `<a href="${m.url}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded-md ${m.badgeCls} border text-[11px] font-bold flex items-center gap-1 shrink-0 transition shadow-xs" title="${m.cleanPlatform} 바로가기">${m.icon} ${m.label} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>`;
  });

  if (total > directButtons.length) {
    const remainingCount = total - directButtons.length;
    html += `
      <div class="relative inline-block src-dropdown-container">
        <button type="button" onclick="toggleSourcePopover(event, '${safeId}')" class="px-2 py-1 rounded-md bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-300 text-[11px] font-extrabold flex items-center gap-1 shrink-0 transition cursor-pointer shadow-xs" title="전체 ${total}개 교차 출처 모아보기">
          <span>🔗 +${remainingCount}${lang === 'KO' ? '개 출처' : (lang === 'ZH' ? '个来源' : ' more')}</span>
          <i data-lucide="chevron-down" class="w-3 h-3 text-amber-800"></i>
        </button>
        <div id="srcMenu_${safeId}" class="hidden absolute z-50 mb-1.5 w-72 max-w-[calc(100vw-2.5rem)] min-w-[240px] bg-white rounded-xl shadow-2xl border border-surface-border p-2.5 text-xs flex flex-col gap-2">
          <div class="text-[10px] font-mono font-bold text-ink-muted px-1 pb-1.5 border-b border-surface-border flex items-center justify-between">
            <span>🔗 ${lang === 'KO' ? `전체 교차 출처 (${total}개)` : (lang === 'ZH' ? `全部聚合来源 (${total}个)` : `All Sources (${total})`)}</span>
            <span class="text-indigo-600 text-[10px] font-bold">언론 ${pressSources.length} · 커뮤니티 ${communitySources.length}</span>
          </div>
          <div class="max-h-56 overflow-y-auto space-y-2 pr-0.5 divide-y divide-surface-border/30">
            ${pressSources.length > 0 ? `
              <div class="pt-1">
                <div class="text-[10px] font-bold text-emerald-800 uppercase tracking-wider mb-1 flex items-center gap-1 px-1">
                  <span>📰 공식 언론 보도 (${pressSources.length})</span>
                </div>
                <div class="space-y-0.5">
                  ${pressSources.map(s => `
                    <a href="${s.meta.url}" target="_blank" rel="noopener noreferrer" class="flex items-center justify-between px-2 py-1 rounded-lg hover:bg-emerald-50/60 transition group text-xs text-ink-primary">
                      <span class="font-bold text-emerald-950 shrink-0 text-[11px]">[${s.meta.cleanPlatform}]</span>
                      <span class="truncate text-[10px] text-ink-muted text-right flex-1 mx-1.5 group-hover:text-emerald-700">${s.title || s.meta.cleanPlatform}</span>
                      <i data-lucide="external-link" class="w-2.5 h-2.5 text-ink-muted group-hover:text-emerald-700 shrink-0"></i>
                    </a>
                  `).join('')}
                </div>
              </div>
            ` : ''}

            ${communitySources.length > 0 ? `
              <div class="pt-1">
                <div class="text-[10px] font-bold text-orange-800 uppercase tracking-wider mb-1 flex items-center gap-1 px-1">
                  <span>💬 커뮤니티 & 개발자 반응 (${communitySources.length})</span>
                </div>
                <div class="space-y-0.5">
                  ${communitySources.map(s => `
                    <a href="${s.meta.url}" target="_blank" rel="noopener noreferrer" class="flex items-center justify-between px-2 py-1 rounded-lg hover:bg-orange-50/60 transition group text-xs text-ink-primary">
                      <span class="flex items-center gap-1 shrink-0 font-bold text-orange-950 text-[11px]">
                        <span>${s.meta.icon}</span>
                        <span>${s.meta.label}</span>
                      </span>
                      <span class="truncate text-[10px] text-ink-muted text-right flex-1 mx-1.5 group-hover:text-orange-700">${s.title || s.meta.label}</span>
                      <i data-lucide="external-link" class="w-2.5 h-2.5 text-ink-muted group-hover:text-orange-700 shrink-0"></i>
                    </a>
                  `).join('')}
                </div>
              </div>
            ` : ''}
          </div>
        </div>
      </div>
    `;
  }

  html += `</div>`;
  return html;
}

export function toggleSourcePopover(e, safeId) {
  if (e) e.stopPropagation();
  const menu = document.getElementById('srcMenu_' + safeId);
  if (!menu) return;
  const isHidden = menu.classList.contains('hidden');
  document.querySelectorAll('[id^="srcMenu_"]').forEach(el => el.classList.add('hidden'));
  if (isHidden) {
    menu.classList.remove('hidden');
    
    // Responsive Dynamic Positioning
    const btn = e.currentTarget;
    const btnRect = btn.getBoundingClientRect();
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const menuWidth = Math.min(260, vw - 32);
    menu.style.width = menuWidth + 'px';
    
    if (btnRect.left + menuWidth > vw - 16) {
      menu.style.left = 'auto';
      menu.style.right = '0px';
    } else {
      menu.style.left = '0px';
      menu.style.right = 'auto';
    }
    
    if (btnRect.top < 220 && (vh - btnRect.bottom > 180)) {
      menu.style.bottom = 'auto';
      menu.style.top = 'calc(100% + 6px)';
    } else {
      menu.style.top = 'auto';
      menu.style.bottom = 'calc(100% + 6px)';
    }

    if (window.lucide) window.lucide.createIcons();
  }
}

export function toggleClusterPopover(e, safeId) {
  if (e) e.stopPropagation();
  const menu = document.getElementById('clusterMenu_' + safeId);
  if (!menu) return;
  const isHidden = menu.classList.contains('hidden');
  document.querySelectorAll('[id^="clusterMenu_"]').forEach(el => el.classList.add('hidden'));
  document.querySelectorAll('[id^="srcMenu_"]').forEach(el => el.classList.add('hidden'));
  if (isHidden) {
    menu.classList.remove('hidden');
    if (window.lucide) window.lucide.createIcons();
  }
}

export function initPopoverDismissListeners() {
  if (typeof document === 'undefined') return;
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.src-dropdown-container')) {
      document.querySelectorAll('[id^="srcMenu_"]').forEach(el => el.classList.add('hidden'));
    }
    if (!e.target.closest('[id^="clusterMenu_"]') && !e.target.closest('button[onclick*="toggleClusterPopover"]')) {
      document.querySelectorAll('[id^="clusterMenu_"]').forEach(el => el.classList.add('hidden'));
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('[id^="srcMenu_"]').forEach(el => el.classList.add('hidden'));
      document.querySelectorAll('[id^="clusterMenu_"]').forEach(el => el.classList.add('hidden'));
    }
  });
}

if (typeof window !== 'undefined') {
  window.buildMultiSourceCluster = buildMultiSourceCluster;
  window.toggleSourcePopover = toggleSourcePopover;
  window.toggleClusterPopover = toggleClusterPopover;
  initPopoverDismissListeners();
}
