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
import { buildMultiSourceCluster } from './popover.js';
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
    const clusterSources = [];
    const seenClusterUrls = new Set();
    if (it.source_url) {
      seenClusterUrls.add(it.source_url.toLowerCase());
      clusterSources.push({
        platform: it.source_platform || 'Press',
        url: it.source_url,
        title: it.title || ''
      });
    }
    for (const s of allSources) {
      const u = (s.url || '').toLowerCase();
      if (u && !seenClusterUrls.has(u)) {
        seenClusterUrls.add(u);
        clusterSources.push(s);
      }
    }
    for (const cp of (it.cross_posts || [])) {
      const u = (cp.url || cp.source_url || '').toLowerCase();
      if (u && !seenClusterUrls.has(u)) {
        seenClusterUrls.add(u);
        clusterSources.push(cp);
      }
    }

    const clusterCount = Math.max(clusterSources.length, allSources.length, 2);

    const spk = it.spike_analysis || it.raw_payload?.spike_analysis || null;
    let pCount = spk?.press_count || it.cross_spike_summary?.press_count || 0;
    let cCount = spk?.community_count || it.cross_spike_summary?.community_count || 0;
    let kCount = spk?.code_count || 0;
    const spkScore = spk ? Number(spk.score || 0) : 0;

    if (!pCount && !cCount && !kCount) {
      clusterSources.forEach(s => {
        const p = (s.platform || s.source_name || '').toLowerCase();
        const u = (s.url || '').toLowerCase();
        const isCode = p.includes('github') || p.includes('hugging') || p.includes('arxiv') || u.includes('github.com') || u.includes('huggingface.co');
        const isComm = p.includes('hacker news') || p.includes('reddit') || p.includes('geeknews') || u.includes('ycombinator') || u.includes('reddit.com') || u.includes('hada.io');
        if (isCode) kCount++;
        else if (isComm) cCount++;
        else pCount++;
      });
    }
    if (pCount === 0 && cCount === 0 && kCount === 0) pCount = 1;

    const totalAxes = (pCount > 0 ? 1 : 0) + (cCount > 0 ? 1 : 0) + (kCount > 0 ? 1 : 0);
    const isSuperSpike = totalAxes >= 3 || spkScore >= 50;
    const isCrossSpike = totalAxes >= 2 || spkScore >= 15;
    const isSpike = Boolean(it.is_cross_spiking || isCrossSpike);

    let badgeBg = 'bg-gradient-to-r from-amber-500/10 via-orange-500/10 to-amber-500/10 border-amber-500/30 text-amber-950';
    let flameColor = 'text-amber-600';
    let tierBadgeText = '';

    if (isSuperSpike) {
      badgeBg = 'bg-gradient-to-r from-rose-500/15 via-amber-500/15 to-orange-500/15 border-rose-500/40 text-rose-950 shadow-xs';
      flameColor = 'text-rose-600';
      tierBadgeText = currentLang === 'KO' ? '🔥 3-Axis 슈퍼 바이럴' : (currentLang === 'ZH' ? '🔥 3-Axis 超级爆发' : '🔥 3-Axis Super Spike');
    } else if (isCrossSpike) {
      badgeBg = 'bg-gradient-to-r from-amber-500/15 via-orange-500/12 to-amber-500/10 border-amber-500/35 text-amber-950';
      flameColor = 'text-amber-600';
      tierBadgeText = currentLang === 'KO' ? '⚡ 2-Axis 크로스 바이럴' : (currentLang === 'ZH' ? '⚡ 2-Axis 跨界联合' : '⚡ 2-Axis Cross Spike');
    } else {
      tierBadgeText = currentLang === 'KO' ? `${clusterCount}개 매체 교차 보도` : (currentLang === 'ZH' ? `${clusterCount}个媒体报道` : `Covered by ${clusterCount} Outlets`);
    }

    crossRollupHtml = `
      <div class="flex items-center justify-between px-2.5 py-1.5 rounded-xl ${badgeBg} border text-xs shadow-2xs">
        <div class="flex items-center gap-1.5 min-w-0">
          <i data-lucide="flame" class="w-3.5 h-3.5 ${flameColor} shrink-0 ${isSpike ? 'animate-pulse' : ''}"></i>
          <span class="font-extrabold text-[11px] truncate">${tierBadgeText}</span>
          ${spkScore > 0 ? `<span class="px-2 py-0.5 rounded-lg bg-amber-500 text-white font-mono font-black text-[11px] shadow-xs border border-amber-400 flex items-center gap-1 shrink-0"><i data-lucide="zap" class="w-3 h-3 text-amber-200 fill-amber-200"></i><span>${spkScore} pts</span></span>` : ''}
        </div>
        <div class="flex items-center gap-1 shrink-0 font-mono text-[10px] font-bold">
          ${pCount > 0 ? `<span class="px-1.5 py-0.2 rounded bg-white/90 text-emerald-800 border border-emerald-300 shadow-2xs">📰 언론 ${pCount}</span>` : ''}
          ${cCount > 0 ? `<span class="px-1.5 py-0.2 rounded bg-white/90 text-orange-800 border border-orange-300 shadow-2xs">💬 커뮤니티 ${cCount}</span>` : ''}
          ${kCount > 0 ? `<span class="px-1.5 py-0.2 rounded bg-white/90 text-indigo-800 border border-indigo-300 shadow-2xs">💻 코드 ${kCount}</span>` : ''}
        </div>
      </div>
    `;
  }

  const footerHtml = renderCardStandardFooter(it, currentLang, linksHtml);

  const tracking = it.metric_tracking || {};
  const delta = (tracking.delta !== undefined) ? tracking.delta : (tracking.growth_delta || 0);
  const latestVal = tracking.latest?.display || tracking.latest_metric || it.viral_metric || '';
  const initVal = tracking.initial?.display || tracking.initial_metric || '';
  const isSpike = Boolean(tracking.is_spiking || delta > 0 || it.is_cross_spiking);

  const cleanInit = formatCleanMetricVal(initVal, currentLang);
  const cleanLatest = formatCleanMetricVal(latestVal, currentLang);

  let metricBadgeHtml = '';
  if (cleanLatest) {
    if (delta > 0 && cleanInit && cleanInit !== cleanLatest) {
      const numInit = cleanInit.replace(/[^0-9.]/g, '');
      const displayFlow = numInit ? `${numInit} ➔ ${cleanLatest}` : `${cleanLatest}`;
      metricBadgeHtml = `
        <span class="px-2.5 py-0.5 rounded-lg text-[11px] font-black font-mono bg-emerald-50 text-emerald-950 border border-emerald-300 shadow-2xs flex items-center gap-1 shrink-0 ml-auto whitespace-nowrap" title="최초 수집: ${cleanInit} ➔ 최신 갱신: ${cleanLatest}">
          <i data-lucide="trending-up" class="w-3.5 h-3.5 text-emerald-600"></i>
          <span>${displayFlow}</span>
          <span class="text-emerald-700 font-black bg-emerald-200/80 px-1 py-0.2 rounded text-[10px]">(+${delta.toLocaleString()})</span>
        </span>
      `;
    } else if (delta > 0) {
      metricBadgeHtml = `
        <span class="px-2.5 py-0.5 rounded-lg text-[11px] font-black font-mono bg-emerald-50 text-emerald-950 border border-emerald-300 shadow-2xs flex items-center gap-1 shrink-0 ml-auto whitespace-nowrap">
          <i data-lucide="trending-up" class="w-3.5 h-3.5 text-emerald-600"></i>
          <span>${cleanLatest}</span>
          <span class="text-emerald-700 font-black bg-emerald-200/80 px-1 py-0.2 rounded text-[10px]">(+${delta.toLocaleString()})</span>
        </span>
      `;
    } else {
      const isPointMetric = cleanLatest.includes('pts') || cleanLatest.includes('★') || cleanLatest.includes('likes') || cleanLatest.includes('점');
      const pointColor = isPointMetric 
        ? 'text-rose-900 font-black bg-rose-100/90 border border-rose-300 shadow-2xs' 
        : (isSpike ? 'text-rose-700 font-bold bg-rose-50 border border-rose-200' : 'text-ink-muted bg-surface-subtle border border-surface-border');
      metricBadgeHtml = `
        <span class="px-2.5 py-0.5 rounded-lg text-[11px] font-mono ${pointColor} shrink-0 ml-auto whitespace-nowrap flex items-center gap-1 font-bold">
          ${isPointMetric ? '<i data-lucide="flame" class="w-3.5 h-3.5 text-rose-600 fill-rose-500"></i>' : ''}
          <span>${cleanLatest}</span>
        </span>
      `;
    }
  }

  const primaryPlat = getPrimaryImpactPlatform(it, allSources);
  const isMultiSource = allSources.length > 1;

  card.innerHTML = `
    <div class="space-y-2.5">
      <div class="flex items-center justify-between text-xs font-mono gap-1.5 min-w-0">
        <div class="flex items-center gap-1.5 min-w-0 overflow-hidden">
          <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${catInfo.cls} shrink-0 truncate max-w-[130px]" title="${catInfo.label}">
            ${catInfo.label}
          </span>
          <span class="px-2 py-0.5 rounded bg-surface-subtle text-ink-primary font-bold border border-surface-border text-[10px] flex items-center gap-1 shrink-0 truncate max-w-[110px]" title="${primaryPlat}">
            <span class="truncate">${primaryPlat}</span>
            ${isMultiSource ? `<span class="px-1.5 py-0.2 rounded text-[9px] font-mono bg-amber-500 text-white font-black shadow-2xs shrink-0">+${allSources.length - 1}</span>` : ''}
          </span>
        </div>
        <div class="shrink-0 flex items-center justify-end ml-auto">
          ${metricBadgeHtml}
        </div>
      </div>

      ${crossRollupHtml}
      ${aiBadgeHtml}

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
