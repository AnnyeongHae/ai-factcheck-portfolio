/**
 * ==============================================================================
 * News Card & Intelligence Feed Presentation Component
 * Renders executive cards with multi-source rollups, hooks, AI takeaways, and comments
 * ==============================================================================
 */

import { currentLang } from '../core/store.js';
import { i18n } from '../core/i18n.js';
import { formatCleanMetricVal, getPrimaryImpactPlatform } from '../utils/metricFormatter.js';
import { formatDateTimeCompact, formatModelAttribution } from '../utils/dateTime.js';
import { buildMultiSourceCluster, deduplicateClusterSources } from './popover.js';
import { openCaseModal } from './modal.js';

export function cleanDescriptionText(desc, title) {
  if (!desc || typeof desc !== 'string') return '';
  let d = desc.trim();
  d = d.replace(/^HN\s*Score:\s*\d+\s*pts\s*(\|\s*Comments:\s*\d+\s*)?(\|\s*)?/i, '');
  d = d.replace(/^Abstract:\s*/i, '');
  if (/^Trending Score:\s*\d+/i.test(d)) return '';
  if (/^Downloads:\s*\d+/i.test(d)) return '';
  if (title && d.toLowerCase() === title.toLowerCase().trim()) {
    return '';
  }
  return d.trim();
}

export function getLocalizedContent(it, lang = currentLang) {
  if (!it) return { displayTitle: '', displayHook: '', displayDesc: '', displayTakeaways: [], hasTrilingual: false };
  const ai = it.ai_enrichment;
  const multi = it.multilingual || (ai ? ai.multilingual : null);
  const story = it.portfolio_story || {};

  let displayTitle = '';
  let displayHook = '';
  let displayDesc = '';
  let displayTakeaways = [];

  if (lang === 'ZH') {
    displayTitle = multi?.zh?.title || it.title_zh || multi?.en?.title || it.title_en || it.title || '';
    displayHook = multi?.zh?.hook || it.hook_zh || story.the_hook_zh || it.curation?.personal_motivation_zh || (ai ? ai.hook : '') || it.hook || story.the_hook || it.curation?.personal_motivation || '';
    displayDesc = multi?.zh?.description || it.description_zh || displayHook || it.description || '';
    if (multi?.zh?.key_takeaways?.length > 0) displayTakeaways = multi.zh.key_takeaways;
    else if (it.key_takeaways_zh?.length > 0) displayTakeaways = it.key_takeaways_zh;
    else if (ai?.takeaways_zh?.length > 0) displayTakeaways = ai.takeaways_zh;
    else if (ai?.key_takeaways?.length > 0) displayTakeaways = ai.key_takeaways;
  } else if (lang === 'EN') {
    displayTitle = multi?.en?.title || it.title_en || it.title || '';
    displayHook = multi?.en?.hook || it.hook_en || story.the_hook_en || it.curation?.personal_motivation_en || (ai ? ai.hook : '') || it.hook || story.the_hook || it.curation?.personal_motivation || '';
    displayDesc = multi?.en?.description || it.description_en || displayHook || it.description || '';
    if (multi?.en?.key_takeaways?.length > 0) displayTakeaways = multi.en.key_takeaways;
    else if (it.key_takeaways_en?.length > 0) displayTakeaways = it.key_takeaways_en;
    else if (ai?.takeaways_en?.length > 0) displayTakeaways = ai.takeaways_en;
    else if (ai?.key_takeaways?.length > 0) displayTakeaways = ai.key_takeaways;
  } else {
    displayTitle = multi?.ko?.title || it.title_ko || it.title || '';
    displayHook = multi?.ko?.hook || it.hook_ko || story.the_hook || it.curation?.personal_motivation || (ai ? ai.hook : '') || it.hook || '';
    displayDesc = multi?.ko?.description || it.description_ko || it.description || displayHook || '';
    if (multi?.ko?.key_takeaways?.length > 0) displayTakeaways = multi.ko.key_takeaways;
    else if (it.key_takeaways?.length > 0) displayTakeaways = it.key_takeaways;
    else if (ai?.key_takeaways?.length > 0) displayTakeaways = ai.key_takeaways;
    else if (ai?.takeaways_ko?.length > 0) displayTakeaways = ai.takeaways_ko;
  }

  if (displayHook && displayTitle) {
    const cleanT = displayTitle.trim();
    const cleanH = displayHook.trim();
    if (cleanH === cleanT || cleanH === `${cleanT} 관련 핵심 기술 명세 및 글로벌 엔지니어링 생태계 영향 분석`) {
      const fallbackDesc = cleanDescriptionText(it.description || '', cleanT);
      displayHook = fallbackDesc && fallbackDesc.length > 15 && fallbackDesc !== cleanH
        ? fallbackDesc
        : (lang === 'KO' ? '핵심 기술 아키텍처 명세 및 글로벌 엔지니어링 생태계 영향 분석' : (lang === 'ZH' ? '核心技术架构突破与全球开发者生态深度解析' : 'Key architectural updates and practitioner impact analysis.'));
    } else if (cleanT.length > 8 && cleanH.startsWith(cleanT)) {
      const stripped = cleanH.slice(cleanT.length).replace(/^[\s:：\-–—·,]+/, '').trim();
      if (stripped.length > 10) displayHook = stripped;
    }
  }

  if (Array.isArray(displayTakeaways) && displayTakeaways.length > 0 && displayTitle) {
    const cleanT = displayTitle.trim();
    displayTakeaways = displayTakeaways.map(tk => {
      if (typeof tk !== 'string') return tk;
      return tk
        .replace(`'${cleanT}' 관련 `, '')
        .replace(`「${cleanT}」`, '해당 기술 ')
        .replace(`regarding ${cleanT}`, 'regarding this release');
    });
  }

  if (displayHook) {
    const cleanH = displayHook.trim();
    if (displayDesc.trim() === cleanH) {
      displayDesc = '';
    } else if (cleanH && displayDesc.includes(cleanH)) {
      displayDesc = displayDesc.replace(cleanH, '').trim();
    }
  }

  displayDesc = cleanDescriptionText(displayDesc, displayTitle);
  const hasTrilingual = Boolean((multi && multi.zh && multi.ko && multi.en) || (it.title_zh && it.title_en));

  return {
    displayTitle,
    displayHook,
    displayDesc,
    displayTakeaways,
    hasTrilingual
  };
}

export function renderHookCallout(displayHook) {
  if (!displayHook) return '';
  return `
    <div class="p-2.5 rounded-xl bg-amber-50/70 border border-amber-200/80 border-l-4 border-l-amber-500 text-[11px] text-amber-950 font-medium leading-relaxed flex items-start gap-1.5 shadow-2xs">
      <span class="shrink-0 font-bold text-amber-800">🪝 Hook:</span>
      <span>${displayHook}</span>
    </div>
  `;
}

export function renderNewsSkeleton(grid, count = 6) {
  if (!grid) return;
  let cards = '';
  for (let i = 0; i < count; i++) {
    cards += `
      <div class="executive-card p-4 sm:p-5 flex flex-col justify-between space-y-4 animate-pulse">
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <div class="h-4 w-20 bg-slate-200/80 rounded-md"></div>
              <div class="h-4 w-16 bg-slate-200/60 rounded-md"></div>
            </div>
            <div class="h-4 w-14 bg-slate-200/60 rounded-md"></div>
          </div>
          <div class="h-5 w-full bg-slate-200/90 rounded-md"></div>
          <div class="h-4 w-3/4 bg-slate-200/70 rounded-md"></div>
          <div class="h-12 w-full bg-amber-100/40 rounded-xl border border-amber-200/30"></div>
          <div class="h-16 w-full bg-indigo-50/40 rounded-xl border border-indigo-100/40"></div>
        </div>
        <div class="pt-3 border-t border-surface-border space-y-2">
          <div class="flex items-center justify-between">
            <div class="h-3 w-28 bg-slate-200/60 rounded"></div>
            <div class="h-3 w-20 bg-slate-200/60 rounded"></div>
          </div>
          <div class="flex justify-end gap-2 pt-1">
            <div class="h-6 w-16 bg-slate-200/80 rounded-md"></div>
            <div class="h-6 w-20 bg-amber-100/80 rounded-md"></div>
          </div>
        </div>
      </div>
    `;
  }
  grid.innerHTML = cards;
}

export function renderAiTakeaways(takeaways, lang = currentLang) {
  if (!Array.isArray(takeaways) || takeaways.length === 0) return '';
  return `
    <div class="mt-2 p-3 rounded-xl bg-gradient-to-br from-indigo-50/50 via-sky-50/40 to-purple-50/50 border border-indigo-100 text-[11px] space-y-1.5 font-sans">
      <div class="flex items-center gap-1 text-indigo-950 font-bold text-[10px]">
        <i data-lucide="sparkles" class="w-3 h-3 text-indigo-600"></i>
        <span>${lang === 'KO' ? 'AI 3줄 핵심 요약' : (lang === 'ZH' ? 'AI 3行核心摘要' : 'AI 3-Line Summary')}</span>
      </div>
      <ul class="space-y-1 text-ink-secondary leading-relaxed list-disc list-inside">
        ${takeaways.map(k => `<li>${k}</li>`).join('')}
      </ul>
    </div>
  `;
}

export function renderRelatedDossierButton(rel, lang = currentLang) {
  if (!rel || !rel.case_id) return '';
  const label = lang === 'KO' ? '관련 기술 검증: ' : (lang === 'ZH' ? '关联技术核验: ' : 'Related Verification: ');
  return `
    <div class="pt-2 border-t border-surface-border">
      <button onclick="openCaseModal('${rel.case_id}')" class="w-full text-left px-2.5 py-1.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 text-[11px] text-emerald-950 font-semibold flex items-center justify-between transition cursor-pointer">
        <span class="flex items-center gap-1.5">
          <i data-lucide="shield-check" class="w-3.5 h-3.5 text-emerald-600"></i>
          <span>${label}${rel.target_tech || ''}</span>
        </span>
        <i data-lucide="arrow-right" class="w-3 h-3 text-emerald-600"></i>
      </button>
    </div>
  `;
}

export function renderCommentsAccordion(rawComments, lang = currentLang, threadUrl = null) {
  if (!Array.isArray(rawComments) || rawComments.length === 0) return '';
  const sorted = rawComments.slice().sort((a, b) => (b.points || 0) - (a.points || 0));
  const top3 = sorted.slice(0, 3);
  const topCount = rawComments.length;
  const sanitizeTxt = str => String(str || '').replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));
  
  const commentsListHtml = top3.map(cm => `
    <div class="pt-2 border-t border-indigo-100/70 text-[11px] leading-relaxed">
      <div class="flex items-center justify-between mb-1">
        <span class="font-bold font-mono text-indigo-700">@${sanitizeTxt(cm.author || 'User')}</span>
        ${cm.points ? `<span class="text-[9px] px-1.5 py-0.5 rounded bg-amber-50 text-amber-800 font-mono font-bold border border-amber-200">▲${cm.points}</span>` : ''}
      </div>
      <p class="text-ink-primary whitespace-pre-line line-clamp-3">${sanitizeTxt(cm.text || '')}</p>
    </div>
  `).join('');

  const moreCount = topCount - top3.length;
  const moreHtml = moreCount > 0 ? `
    <div class="pt-1.5 text-center">
      ${threadUrl ? `<a href="${threadUrl}" target="_blank" rel="noopener noreferrer" class="text-[10px] text-indigo-600 hover:underline font-semibold">외 ${moreCount}개 댓글 더보기 (원문 스레드 ↗)</a>` : `<span class="text-[10px] text-ink-muted">외 ${moreCount}개 댓글 생략됨</span>`}
    </div>
  ` : '';

  return `
    <details class="group rounded-xl border border-indigo-100 bg-indigo-50/25 p-2.5 transition text-xs mt-2">
      <summary class="cursor-pointer font-bold text-[11px] text-indigo-950 flex items-center justify-between select-none list-none">
        <span class="flex items-center gap-1.5">
          <i data-lucide="message-square" class="w-3.5 h-3.5 text-indigo-600"></i>
          <span>${lang === 'KO' ? `💬 커뮤니티 반응 (${topCount}개 댓글)` : (lang === 'ZH' ? `💬 社区讨论 (${topCount}条评论)` : `💬 Community Discussions (${topCount} comments)`)}</span>
        </span>
        <span class="text-[10px] font-mono text-indigo-600 group-open:rotate-180 transition-transform">▼</span>
      </summary>
      <div class="mt-2 space-y-2">
        ${commentsListHtml}
        ${moreHtml}
      </div>
    </details>
  `;
}

export function toggleNewsComments() {}

export function renderCardStandardFooter(it, lang = currentLang, extraActionHtml = '') {
  const ai = it.ai_enrichment;
  const pubLabel = lang === 'KO' ? '발행' : (lang === 'ZH' ? '发布' : 'Published');
  const hrvLabel = lang === 'KO' ? '최초 포착' : (lang === 'ZH' ? '最初捕获' : 'First Spotted');
  const updLabel = lang === 'KO' ? '최신 갱신' : (lang === 'ZH' ? '最新更新' : 'Updated');
  const srcLabel = lang === 'KO' ? '원문' : (lang === 'ZH' ? '原文' : 'Source');
  const pendingLabel = lang === 'KO' ? 'AI요약 대기중' : (lang === 'ZH' ? 'AI分析排队中' : 'Pending AI Audit');

  const pubDate = formatDateTimeCompact(it.published_at || it.created_at || it.harvested_at);
  const earliestHrv = it.earliest_harvested_at || it.initial_harvested_at || it.harvested_at || it.harvested_date || it.created_at;
  const hrvDate = formatDateTimeCompact(earliestHrv);
  const hasUpdate = it.updated_at && formatDateTimeCompact(it.updated_at) !== hrvDate;
  const updDate = hasUpdate ? formatDateTimeCompact(it.updated_at) : '';

  let auditHtml = `
    <div class="text-[11px] text-ink-muted flex items-center gap-1.5">
      <span>🔬 ${pendingLabel}</span>
    </div>
  `;
  if (ai?.enriched_at) {
    auditHtml = `
      <div class="text-[11px] text-indigo-700 font-semibold flex items-center gap-1.5 min-w-0 overflow-hidden">
        <span class="shrink-0">🔬 ${formatDateTimeCompact(ai.enriched_at)}</span>
        <span class="text-ink-muted font-normal truncate min-w-0 align-bottom cursor-help" title="${ai.enriched_by_model || ''}">(${formatModelAttribution(ai.enriched_by_model)})</span>
      </div>
    `;
  }

  const defaultSourceLink = it.source_url ? `
    <a href="${it.source_url}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded-md bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border text-[11px] font-semibold flex items-center gap-1 shrink-0">
      📄 ${srcLabel} <i data-lucide="external-link" class="w-2.5 h-2.5"></i>
    </a>
  ` : '';

  return `
    <div class="pt-3 border-t border-surface-border space-y-1.5 text-xs font-mono">
      <div class="text-[11px] text-ink-muted flex items-center justify-between gap-1 flex-wrap">
        <span>📰 ${pubLabel}: ${pubDate}</span>
      </div>
      <div class="text-[11px] text-ink-muted flex items-center justify-between gap-1 flex-wrap">
        <span>📥 ${hrvLabel}: ${hrvDate}</span>
        ${hasUpdate ? `<span class="text-[10px] text-indigo-600 font-bold" title="${updLabel}">(🔄 ${updDate})</span>` : ''}
      </div>
      ${auditHtml}
      <div class="flex items-center justify-end gap-2 pt-1 font-sans flex-wrap">
        ${extraActionHtml || defaultSourceLink}
      </div>
    </div>
  `;
}

export function createNewsCardElement(it, currentLang) {
  const card = document.createElement('div');
  card.className = 'executive-card p-4 sm:p-5 flex flex-col justify-between space-y-4';
  const t = i18n[currentLang] || i18n.KO;

  const ai = it.ai_enrichment;
  const { displayTitle, displayHook, displayDesc, displayTakeaways } = getLocalizedContent(it, currentLang);
  const showDesc = (!displayTakeaways || displayTakeaways.length === 0) && displayDesc;

  const isHn = (it.source_platform || '').includes('Hacker News') || (it.source_url || '').includes('news.ycombinator.com');
  const isGn = (it.source_platform || '').includes('GeekNews') || (it.source_url || '').includes('hada.io');
  const hnUrl = it.hn_url || ((it.source_url || '').includes('news.ycombinator.com') ? it.source_url : null);
  const gnUrl = isGn ? (it.hn_url || it.source_url) : null;
  const articleUrl = it.article_url || (it.source_url !== (hnUrl || gnUrl) ? it.source_url : null);

  const allSources = [...(it.sources || [])];
  if (it.cross_posts && it.cross_posts.length > 0) {
    it.cross_posts.forEach(cp => {
      const cpUrl = cp.url || cp.source_url || cp.article_url;
      if (cpUrl && !allSources.some(s => (s.url || '').toLowerCase() === cpUrl.toLowerCase())) {
        allSources.push({
          source_name: cp.platform || 'Cross-post',
          platform: cp.platform || 'Cross-post',
          url: cpUrl,
          title: cp.title || '',
          type: 'cross_post'
        });
      }
    });
  }

  let linksHtml = '';
  if (allSources.length > 1) {
    linksHtml = buildMultiSourceCluster(allSources, it.inbox_id || it.id);
  } else if (isHn) {
    linksHtml = `<div class="flex items-center gap-1.5 flex-wrap justify-end">`;
    if (articleUrl && articleUrl !== hnUrl) {
      linksHtml += `<a href="${articleUrl}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded-md bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border text-[11px] font-semibold flex items-center gap-1 shrink-0">📄 ${currentLang === 'KO' ? '기사 원문' : (currentLang === 'ZH' ? '文章原文' : 'Article')} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>`;
    }
    if (hnUrl) {
      linksHtml += `<a href="${hnUrl}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded-md bg-orange-50 text-orange-800 hover:text-orange-950 border border-orange-200 text-[11px] font-bold flex items-center gap-1 shrink-0">🔥 ${currentLang === 'KO' ? 'HN 토론' : (currentLang === 'ZH' ? 'HN 讨论' : 'HN Thread')} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>`;
    }
    linksHtml += `</div>`;
  } else if (isGn) {
    linksHtml = `<div class="flex items-center gap-1.5 flex-wrap justify-end">`;
    if (articleUrl && articleUrl !== gnUrl) {
      linksHtml += `<a href="${articleUrl}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded-md bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border text-[11px] font-semibold flex items-center gap-1 shrink-0">📄 ${currentLang === 'KO' ? '기사 원문' : (currentLang === 'ZH' ? '文章原文' : 'Article')} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>`;
    }
    if (gnUrl) {
      linksHtml += `<a href="${gnUrl}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded-md bg-indigo-50 text-indigo-800 hover:text-indigo-950 border border-indigo-200 text-[11px] font-bold flex items-center gap-1 shrink-0">💬 ${currentLang === 'KO' ? '긱뉴스 토론' : (currentLang === 'ZH' ? '极客新闻' : 'GeekNews')} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>`;
    }
    linksHtml += `</div>`;
  } else {
    linksHtml = `<div class="flex items-center gap-1.5 justify-end"><a href="${it.source_url}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded-md bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border text-[11px] font-semibold flex items-center gap-1 shrink-0">📄 ${t.newsOriginalLink} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a></div>`;
  }

  let aiBadgeHtml = '';
  let aiSummaryHtml = '';
  const hookHtml = renderHookCallout(displayHook);
  const relatedHtml = renderRelatedDossierButton(it.related_dossier, currentLang);
  const commentsHtml = renderCommentsAccordion(it.raw_comments, currentLang, hnUrl || it.source_url);

  const tier1Map = {
    'SCIENCE_RESEARCH': { label: currentLang === 'KO' ? '🚀 과학·우주' : (currentLang === 'ZH' ? '🚀 科学与航天' : '🚀 Science & Research'), cls: 'bg-teal-50 text-teal-900 border-teal-200' },
    'ECONOMY_FINANCE': { label: currentLang === 'KO' ? '🏦 경제·금융' : (currentLang === 'ZH' ? '🏦 经济与金融' : '🏦 Economy & Finance'), cls: 'bg-emerald-50 text-emerald-900 border-emerald-200' },
    'LAW_CRIME_JUSTICE': { label: currentLang === 'KO' ? '⚖️ 사회·법률' : (currentLang === 'ZH' ? '⚖️ 法律与社会' : '⚖️ Law & Society'), cls: 'bg-rose-50 text-rose-900 border-rose-200' },
    'POLITICS_POLICY': { label: currentLang === 'KO' ? '🏛️ 정치·정책' : (currentLang === 'ZH' ? '🏛️ 政治与政策' : '🏛️ Politics & Policy'), cls: 'bg-amber-50 text-amber-950 border-amber-300' },
    'CULTURE_HUMANITIES': { label: currentLang === 'KO' ? '🌿 문화·인문' : (currentLang === 'ZH' ? '🌿 文化与人文' : '🌿 Culture & Arts'), cls: 'bg-purple-50 text-purple-900 border-purple-200' }
  };
  const catMap = {
    'INFERENCE_OPT': { label: currentLang === 'KO' ? '⚡ 추론·서빙 최적화' : (currentLang === 'ZH' ? '⚡ 推理服务优化' : '⚡ Inference & Opt'), cls: 'bg-amber-50 text-amber-900 border-amber-200' },
    'AGENTS_DEVTOOLS': { label: currentLang === 'KO' ? '🛠️ 에이전트·개발도구' : (currentLang === 'ZH' ? '🛠️ 智能体与工具' : '🛠️ Agents & DevTools'), cls: 'bg-blue-50 text-blue-900 border-blue-200' },
    'MULTIMODAL_AI': { label: currentLang === 'KO' ? '🎨 멀티모달·영상/음성' : (currentLang === 'ZH' ? '🎨 多模态与视听' : '🎨 Multimodal & GenAI'), cls: 'bg-purple-50 text-purple-900 border-purple-200' },
    'FOUNDATION_MODELS': { label: currentLang === 'KO' ? '🤖 파운데이션·가중치' : (currentLang === 'ZH' ? '🤖 基础模型与权重' : '🤖 Foundation Models'), cls: 'bg-emerald-50 text-emerald-900 border-emerald-200' },
    'INFRA_RAG_SECURITY': { label: currentLang === 'KO' ? '🛡️ 인프라·RAG·보안' : (currentLang === 'ZH' ? '🛡️ 基础设施与安全' : '🛡️ Infra, RAG & Safety'), cls: 'bg-rose-50 text-rose-900 border-rose-200' },
    'DEEP_SCIENCE_SPACE': { label: currentLang === 'KO' ? '🚀 우주·신소재·과학' : (currentLang === 'ZH' ? '🚀 深科技与空天科学' : '🚀 Deep Science & Space'), cls: 'bg-teal-50 text-teal-900 border-teal-200' },
    'MACRO_GLOBAL_BIZ': { label: currentLang === 'KO' ? '🏦 산업·거시경제' : (currentLang === 'ZH' ? '🏦 产业与宏观经济' : '🏦 Macro & Global Biz'), cls: 'bg-amber-50 text-amber-950 border-amber-300' },
    'INDUSTRY_TRENDS': { label: currentLang === 'KO' ? '🌐 일반 테크·SW' : (currentLang === 'ZH' ? '🌐 通用科技与软件' : '🌐 General Tech & SW'), cls: 'bg-slate-100 text-slate-800 border-slate-200' }
  };
  const catInfo = (it.tier1_category && tier1Map[it.tier1_category]) ? tier1Map[it.tier1_category] : (catMap[it.category_primary] || catMap['INDUSTRY_TRENDS']);

  if (ai) {
    const tagBg = ai.worth_investigating === 'HIGH' ? 'bg-orange-50 text-orange-950 border-orange-200' : 'bg-indigo-50 text-indigo-950 border-indigo-200';
    const typeLabels = {
      'MODEL': currentLang === 'KO' ? '🤖 모델 발표' : (currentLang === 'ZH' ? '🤖 模型发布' : '🤖 Model'),
      'AGENT': currentLang === 'KO' ? '🦾 에이전트' : (currentLang === 'ZH' ? '🦾 智能体' : '🦾 Agent'),
      'TECH': currentLang === 'KO' ? '⚡ 신기술/최적화' : (currentLang === 'ZH' ? '⚡ 新技术/架构' : '⚡ Tech/Arch'),
      'NEWS': currentLang === 'KO' ? '📰 업계 동향' : (currentLang === 'ZH' ? '📰 行业资讯' : '📰 News')
    };
    const typeBadge = typeLabels[ai.type_classification] || (currentLang === 'KO' ? '💡 기술' : '💡 Tech');

    const hasRealRec = Boolean(ai.score || ai.worth_score || ai.recommended_tag);
    const recBadgeHtml = hasRealRec ? `
      <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${tagBg}">
        ${ai.recommended_tag || '💡 추천'} ★${ai.score || ai.worth_score}
      </span>
    ` : '';

    const effectiveSourceLang = (ai.source_lang || it.source_lang || '').toUpperCase();

    aiBadgeHtml = `
      <div class="flex items-center gap-1.5 flex-wrap my-1">
        ${recBadgeHtml}
        <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-900 border border-indigo-200">
          ${typeBadge}
        </span>
        ${ai.programming_lang && ai.programming_lang !== 'General' ? `<span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-50 text-amber-900 border border-amber-200">💻 ${ai.programming_lang}</span>` : ''}
        ${effectiveSourceLang ? `<span class="px-1.5 py-0.2 rounded text-[9px] font-mono font-semibold bg-surface-subtle text-ink-muted border border-surface-border">${effectiveSourceLang}</span>` : ''}
      </div>
    `;

    aiSummaryHtml = renderAiTakeaways(displayTakeaways, currentLang);
  }

  let crossRollupHtml = '';
  if ((it.cross_posts && it.cross_posts.length > 0) || allSources.length > 1) {
    const rawClusterPool = [];
    if (it.source_url) {
      rawClusterPool.push({
        platform: it.source_platform || 'Press',
        url: it.source_url,
        title: it.title || ''
      });
    }
    rawClusterPool.push(...allSources);
    for (const cp of (it.cross_posts || [])) {
      rawClusterPool.push({
        platform: cp.platform || cp.source_name || 'Cross-post',
        url: cp.url || cp.source_url || '',
        title: cp.title || ''
      });
    }

    const dedupedCluster = deduplicateClusterSources(rawClusterPool);
    const spk = it.spike_analysis || it.raw_payload?.spike_analysis || null;
    const spkScore = spk ? Number(spk.score || 0) : 0;

    let pCount = dedupedCluster.filter(s => s.meta.axis === 'PRESS').length;
    let cCount = dedupedCluster.filter(s => s.meta.axis === 'COMMUNITY').length;
    let kCount = dedupedCluster.filter(s => s.meta.axis === 'CODE').length;
    if (pCount === 0 && cCount === 0 && kCount === 0) pCount = 1;

    const totalAxes = (pCount > 0 ? 1 : 0) + (cCount > 0 ? 1 : 0) + (kCount > 0 ? 1 : 0);
    const isSuperSpike = totalAxes >= 3 || spkScore >= 50;
    const isCrossSpike = totalAxes >= 2 || spkScore >= 15;
    const isSpike = Boolean(it.is_cross_spiking || isCrossSpike);

    let badgeBg = 'bg-gradient-to-r from-amber-500/10 via-orange-500/10 to-amber-500/10 border-amber-500/30 text-amber-950';
    let flameColor = 'text-amber-600';

    if (isSuperSpike) {
      badgeBg = 'bg-gradient-to-r from-rose-500/15 via-amber-500/15 to-orange-500/15 border-rose-500/40 text-rose-950 shadow-xs';
      flameColor = 'text-rose-600';
    } else if (isCrossSpike) {
      badgeBg = 'bg-gradient-to-r from-amber-500/15 via-orange-500/12 to-amber-500/10 border-amber-500/35 text-amber-950';
      flameColor = 'text-amber-600';
    }

    // Pure Text-Free Linear Sparkline Graph (SVG) for Daily Point Decay Trajectory
    let decayLineSvgHtml = '';
    const rawHist = Array.isArray(it.spike_history) ? it.spike_history : [];
    const ptsList = rawHist.map(h => Number(h.score || 0)).filter(v => Number.isFinite(v) && v > 0);
    if (ptsList.length === 1 && spkScore > 0 && Math.abs(ptsList[0] - spkScore) >= 0.1) {
      ptsList.push(spkScore);
    } else if (ptsList.length === 0 && Number(it.peak_spike_score || 0) > spkScore && spkScore > 0) {
      ptsList.push(Number(it.peak_spike_score), spkScore);
    }
    if (ptsList.length >= 2) {
      const w = 54;
      const h = 18;
      const pad = 2.5;
      const maxV = Math.max(...ptsList, 1);
      const minV = 0;
      const coords = ptsList.map((val, idx) => {
        const x = pad + (idx / (ptsList.length - 1)) * (w - pad * 2);
        const y = (h - pad) - ((val - minV) / (maxV - minV || 1)) * (h - pad * 2);
        return [Number(x.toFixed(1)), Number(y.toFixed(1))];
      });
      const polyPoints = coords.map(c => `${c[0]},${c[1]}`).join(' ');
      const areaPoints = `${coords[0][0]},${h - 1} ${polyPoints} ${coords[coords.length - 1][0]},${h - 1}`;
      const lastPt = coords[coords.length - 1];
      const firstPt = coords[0];
      const strokeHex = isSuperSpike ? '#e11d48' : '#d97706';
      const fillHex = isSuperSpike ? 'rgba(225,29,72,0.16)' : 'rgba(217,119,6,0.16)';
      const tipText = rawHist.length >= 2
        ? rawHist.map(item => `${item.date.slice(5)}: ${item.score}p`).join(' → ')
        : ptsList.map(v => `${v}p`).join(' → ');

      decayLineSvgHtml = `
        <span class="inline-flex items-center px-1.5 py-0.5 rounded-lg bg-white/90 border border-amber-300/80 shadow-2xs shrink-0" title="${tipText}">
          <svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" class="overflow-visible">
            <polygon points="${areaPoints}" fill="${fillHex}" />
            <polyline points="${polyPoints}" fill="none" stroke="${strokeHex}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
            <circle cx="${firstPt[0]}" cy="${firstPt[1]}" r="1.8" fill="${strokeHex}" />
            <circle cx="${lastPt[0]}" cy="${lastPt[1]}" r="2.2" fill="${strokeHex}" />
          </svg>
        </span>
      `;
    }

    crossRollupHtml = `
      <div class="flex flex-wrap items-center justify-between px-2.5 py-1.5 rounded-xl ${badgeBg} border text-xs shadow-2xs gap-x-2 gap-y-1.5">
        <div class="flex flex-wrap items-center gap-1.5 min-w-0">
          <i data-lucide="flame" class="w-3.5 h-3.5 ${flameColor} shrink-0 ${isSpike ? 'animate-pulse' : ''}"></i>
          ${spkScore > 0 ? `<span class="px-2 py-0.5 rounded-lg bg-amber-500 text-white font-mono font-black text-[11px] shadow-xs border border-amber-400 flex items-center gap-1 shrink-0 whitespace-nowrap"><i data-lucide="zap" class="w-3 h-3 text-amber-200 fill-amber-200"></i><span>${spkScore} pts</span></span>` : ''}
          ${decayLineSvgHtml}
        </div>
        <div class="flex flex-wrap items-center gap-1 shrink-0 font-mono text-[10px] font-bold ml-auto">
          ${pCount > 0 ? `<span class="px-1.5 py-0.5 rounded bg-white/90 text-emerald-800 border border-emerald-300 shadow-2xs whitespace-nowrap">📰 언론 ${pCount}</span>` : ''}
          ${cCount > 0 ? `<span class="px-1.5 py-0.5 rounded bg-white/90 text-orange-800 border border-orange-300 shadow-2xs whitespace-nowrap">💬 커뮤니티 ${cCount}</span>` : ''}
          ${kCount > 0 ? `<span class="px-1.5 py-0.5 rounded bg-white/90 text-indigo-800 border border-indigo-300 shadow-2xs whitespace-nowrap">💻 코드 ${kCount}</span>` : ''}
        </div>
      </div>
    `;
  }

  const footerHtml = renderCardStandardFooter(it, currentLang, linksHtml);

  card.innerHTML = `
    <div class="space-y-2.5">
      ${crossRollupHtml}

      <h3 class="font-bold text-[14px] sm:text-[15px] text-ink-primary hover:text-indigo-600 transition leading-snug break-words line-clamp-2" title="${(displayTitle || '').replace(/"/g, '&quot;')}">
        ${displayTitle}
      </h3>

      ${hookHtml}

      ${showDesc ? `<p class="text-xs text-ink-secondary leading-relaxed line-clamp-3">${displayDesc}</p>` : ''}

      ${aiSummaryHtml}
      ${relatedHtml}
      ${commentsHtml}
    </div>

    ${footerHtml}
  `;
  return card;
}

if (typeof window !== 'undefined') {
  window.cleanDescriptionText = cleanDescriptionText;
  window.getLocalizedContent = getLocalizedContent;
  window.renderHookCallout = renderHookCallout;
  window.renderNewsSkeleton = renderNewsSkeleton;
  window.renderAiTakeaways = renderAiTakeaways;
  window.renderRelatedDossierButton = renderRelatedDossierButton;
  window.renderCommentsAccordion = renderCommentsAccordion;
  window.renderCardStandardFooter = renderCardStandardFooter;
  window.createNewsCardElement = createNewsCardElement;
}
