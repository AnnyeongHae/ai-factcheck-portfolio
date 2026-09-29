/**
 * ==============================================================================
 * Models Card Component & AI Models Directory
 * Handles multi-modality filtering, family groups, parameter sizes, and spaces demos
 * ==============================================================================
 */

import {
  currentLang,
  liveModelsData,
  currentModelsFamily,
  currentModelsArtifact,
  currentModelsModality,
  currentModelsSort,
  modelsSearchQuery,
  currentModelsPage,
  PAGE_SIZE,
  targetSelectedInboxId,
  setModelsPage,
  setModelsFamily,
  setModelsArtifact,
  setModelsModality,
  setModelsSortVal,
  setModelsSearchQuery,
  setTargetSelectedInboxId
} from '../core/store.js';
import { getLocalizedContent, renderHookCallout, renderRelatedDossierButton, renderCardStandardFooter } from './newsCard.js';
import { clusterFeedItems } from '../utils/feedClustering.js';
import { sortCollection } from '../utils/collectionSorter.js';
import { renderPagination } from './pagination.js';

export function setModelsSort(sort) {
  setModelsPage(1);
  setModelsSortVal(sort);
  renderModels();
}

export function setModelsArtifactFilter(art) {
  setModelsPage(1);
  setModelsArtifact(art);
  if (typeof document !== 'undefined') {
    document.querySelectorAll('.model-art-pill').forEach(btn => {
      if (btn.getAttribute('data-art') === art) {
        btn.className = 'model-art-pill active px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap';
      } else {
        btn.className = 'model-art-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
      }
    });
  }
  renderModels();
}

export function setModelsModalityFilter(mod) {
  setModelsPage(1);
  setModelsModality(mod);
  if (typeof document !== 'undefined') {
    document.querySelectorAll('.model-mod-pill').forEach(btn => {
      if (btn.dataset.mod === mod) {
        btn.className = 'model-mod-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shrink-0 whitespace-nowrap';
      } else {
        btn.className = 'model-mod-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
      }
    });
  }
  renderModels();
}

export function setModelsFamilyFilter(fam) {
  setModelsPage(1);
  setModelsFamily(fam);
  if (typeof document !== 'undefined') {
    document.querySelectorAll('.model-fam-pill').forEach(btn => {
      if (btn.getAttribute('data-fam') === fam) {
        btn.className = 'model-fam-pill active px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap';
      } else {
        btn.className = 'model-fam-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
      }
    });
  }
  renderModels();
}

export function renderModels() {
  if (typeof document === 'undefined') return;
  const grid = document.getElementById('modelsGrid');
  if (!grid) return;
  grid.innerHTML = '';
  const lang = typeof window !== 'undefined' && window.currentLang ? window.currentLang : currentLang;
  const lModels = typeof window !== 'undefined' && window.liveModelsData ? window.liveModelsData : liveModelsData;

  const curMod = typeof window !== 'undefined' && window.currentModelsModality ? window.currentModelsModality : currentModelsModality;
  const curFam = typeof window !== 'undefined' && window.currentModelsFamily ? window.currentModelsFamily : currentModelsFamily;
  const curArt = typeof window !== 'undefined' && window.currentModelsArtifact ? window.currentModelsArtifact : currentModelsArtifact;
  const curSort = typeof window !== 'undefined' && window.currentModelsSort ? window.currentModelsSort : currentModelsSort;
  const curSearch = typeof window !== 'undefined' && window.modelsSearchQuery ? window.modelsSearchQuery : modelsSearchQuery;
  const targetId = typeof window !== 'undefined' && window.targetSelectedInboxId ? window.targetSelectedInboxId : targetSelectedInboxId;
  let curPage = typeof window !== 'undefined' && window.currentModelsPage ? window.currentModelsPage : currentModelsPage;

  const filtered = lModels.filter(item => {
    const hasAi = !!(item.ai_enrichment && (item.multilingual || (item.ai_enrichment && item.ai_enrichment.multilingual)));
    if (!hasAi) return false;

    if (targetId && item.inbox_id === targetId) {
      return true;
    }

    let matchesMod = true;
    if (curMod !== 'ALL') {
      const itemMod = (item.task_modality || '').toLowerCase();
      matchesMod = itemMod === curMod.toLowerCase();
    }

    const fam = (item.model_family || '').toLowerCase();
    let matchesFam = true;
    if (curFam === 'ALL') {
      matchesFam = true;
    } else if (curFam === 'Standalone') {
      matchesFam = fam.includes('standalone') || fam.includes('독립') || !fam;
    } else if (curFam === 'Audio / Speech') {
      matchesFam = fam.includes('audio') || fam.includes('speech') || fam.includes('tts') || fam.includes('whisper');
    } else {
      matchesFam = fam.includes(curFam.toLowerCase());
    }

    let matchesArt = true;
    if (curArt !== 'ALL') {
      const itemArt = item.artifact_type || 'WEIGHTS';
      matchesArt = itemArt === curArt;
    }

    if (!curSearch) {
      return matchesMod && matchesFam && matchesArt;
    }

    const q = curSearch.toLowerCase().trim();
    const searchable = (
      (item.inbox_id || '') + ' ' +
      (item.title || '') + ' ' +
      (item.title_ko || '') + ' ' +
      (item.title_en || '') + ' ' +
      (item.title_zh || '') + ' ' +
      (item.description || '') + ' ' +
      fam + ' ' +
      (item.task_modality || '') + ' ' +
      (item.artifact_type || '') + ' ' +
      (item.parameter_size || '') + ' ' +
      (item.ai_enrichment?.summary_ko || '') + ' ' +
      (item.ai_enrichment?.hook_ko || '')
    ).toLowerCase();

    const tokens = q.split(/\s+/).filter(t => t.length > 0);
    const matchesSearch = searchable.includes(q) || (tokens.length > 0 && tokens.every(t => searchable.includes(t)));
    return matchesMod && matchesFam && matchesArt && matchesSearch;
  });

  sortCollection(filtered, curSort);
  const clusteredModels = clusterFeedItems(filtered);

  const countEl = document.getElementById('modelsFilteredCount');
  if (countEl) countEl.innerText = lang === 'KO' ? `${clusteredModels.length}개 모델 표출` : (lang === 'ZH' ? `显示 ${clusteredModels.length} 个模型` : `Showing ${clusteredModels.length} models`);

  const totalPages = Math.ceil(clusteredModels.length / PAGE_SIZE) || 1;
  if (curPage > totalPages) curPage = totalPages;
  if (curPage < 1) curPage = 1;
  setModelsPage(curPage);

  renderPagination('modelsPagination', curPage, totalPages, 'changeModelsPage');

  if (clusteredModels.length === 0) {
    grid.innerHTML = `<div class="col-span-full py-16 text-center text-ink-muted font-medium">${lang === 'KO' ? '일치하는 AI 모델이 없습니다.' : (lang === 'ZH' ? '暂无匹配的 AI 模型。' : 'No matching AI models.')}</div>`;
    return;
  }

  const pagedModels = clusteredModels.slice((curPage - 1) * PAGE_SIZE, curPage * PAGE_SIZE);
  const fragment = document.createDocumentFragment();

  pagedModels.forEach(it => {
    const { displayTitle, displayHook, displayDesc } = getLocalizedContent(it, lang);

    const card = document.createElement('div');
    card.className = 'bg-white rounded-2xl p-4 sm:p-5 border border-surface-border hover:border-indigo-400 hover:shadow-md transition flex flex-col justify-between space-y-4';

    const artType = it.artifact_type || (it.source_platform?.includes('Spaces') ? 'WEB_SERVICE' : 'WEIGHTS');
    const artBadgeMap = {
      'WEIGHTS': {
        label: lang === 'KO' ? '🤖 모델 가중치' : (lang === 'ZH' ? '🤖 模型权重' : '🤖 Model Weights'),
        cls: 'bg-indigo-50 text-indigo-800 border-indigo-200',
        btn: lang === 'KO' ? '📥 허브 다운로드' : (lang === 'ZH' ? '📥 Hub 下载' : '📥 Hub Download')
      },
      'WEB_SERVICE': {
        label: lang === 'KO' ? '🌐 Spaces 데모' : (lang === 'ZH' ? '🌐 Spaces 演示' : '🌐 Spaces Demo'),
        cls: 'bg-emerald-50 text-emerald-800 border-emerald-200',
        btn: lang === 'KO' ? '🚀 데모 / Spaces 체험' : (lang === 'ZH' ? '🚀 在线 Demo 体验' : '🚀 Try Live Spaces Demo')
      },
      'FINETUNE': {
        label: lang === 'KO' ? '🎯 특화 파인튜닝' : (lang === 'ZH' ? '🎯 微调定制模型' : '🎯 Finetuned Model'),
        cls: 'bg-amber-50 text-amber-800 border-amber-200',
        btn: lang === 'KO' ? '🎯 파인튜닝 모델 보기' : (lang === 'ZH' ? '🎯 查看微调模型' : '🎯 View Finetuned Model')
      }
    };
    const artMeta = artBadgeMap[artType] || artBadgeMap['WEIGHTS'];
    const artBadge = `<span class="px-2 py-0.5 rounded-md font-bold border text-[10px] font-mono ${artMeta.cls}">${artMeta.label}</span>`;

    const famBadge = it.model_family ? `
      <span class="px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 font-bold border border-indigo-200 text-[11px] font-mono">
        🤖 ${it.model_family}
      </span>
    ` : '';

    let modBadge = '';
    if (it.task_modality) {
      const m = it.task_modality.toLowerCase();
      let icon = '🎯';
      let label = it.task_modality;
      if (m.includes('video')) { icon = '🎬'; label = 'Video'; }
      else if (m.includes('image-text') || m.includes('vision') || m.includes('vlm')) { icon = '👁️'; label = 'VLM'; }
      else if (m.includes('image')) { icon = '🎨'; label = 'Image'; }
      else if (m.includes('speech') || m.includes('audio')) { icon = '🎙️'; label = 'Audio/TTS'; }
      else if (m.includes('text')) { icon = '📝'; label = 'Text'; }
      modBadge = `<span class="px-2 py-0.5 rounded-md bg-purple-50 text-purple-700 font-bold border border-purple-200 text-[10px] font-mono">${icon} ${label}</span>`;
    }

    let paramBadge = '';
    if (it.parameter_size) {
      paramBadge = `<span class="px-1.5 py-0.5 rounded-md bg-amber-50 text-amber-800 font-bold border border-amber-200 text-[10px] font-mono shrink-0">⚡ ${it.parameter_size}</span>`;
    }

    let formatBadges = '';
    if (Array.isArray(it.detected_formats) && it.detected_formats.length > 0) {
      formatBadges = it.detected_formats.slice(0, 3).map(fmt => 
        `<span class="px-1.5 py-0.2 rounded bg-surface-subtle text-ink-muted text-[9px] font-mono border border-surface-border uppercase">${fmt}</span>`
      ).join(' ');
    }

    const hookHtml = renderHookCallout(displayHook);
    const relatedHtml = renderRelatedDossierButton(it.related_dossier, lang);

    const actionBtn = `
      <a href="${it.source_url}" target="_blank" rel="noopener noreferrer" class="px-2.5 py-1 rounded-lg bg-surface-subtle hover:bg-ink-primary hover:text-white text-ink-primary font-bold transition text-xs flex items-center gap-1 shrink-0">
        <span>${artMeta.btn}</span> <i data-lucide="external-link" class="w-3 h-3"></i>
      </a>
    `;
    const footerHtml = renderCardStandardFooter(it, lang, actionBtn);

    card.innerHTML = `
      <div class="space-y-3">
        <div class="flex items-center justify-between text-xs font-mono">
          <div class="flex items-center gap-1.5 flex-wrap">
            ${artBadge}
            ${famBadge}
            ${modBadge}
            ${paramBadge}
          </div>
          <span class="text-ink-muted text-[11px] shrink-0">${it.source_platform || 'Hugging Face'}</span>
        </div>

        <h3 class="font-bold text-sm text-ink-primary hover:text-indigo-600 transition leading-snug">
          ${displayTitle}
        </h3>

        ${hookHtml}

        ${displayDesc ? `<p class="text-xs text-ink-secondary leading-relaxed line-clamp-3">${displayDesc}</p>` : ''}

        ${formatBadges ? `<div class="flex items-center gap-1 flex-wrap pt-1">${formatBadges}</div>` : ''}

        ${relatedHtml}
      </div>

      ${footerHtml}
    `;

    fragment.appendChild(card);
  });
  grid.appendChild(fragment);

  if (window.lucide) window.lucide.createIcons({ root: grid });
}

export function toggleFamilyGrouping() {}

export function initModelsSearchListener() {
  if (typeof document === 'undefined') return;
  document.getElementById('modelsSearchInput')?.addEventListener('input', (e) => {
    setTargetSelectedInboxId('');
    setModelsPage(1);
    setModelsSearchQuery(e.target.value);
    renderModels();
  });
}

if (typeof window !== 'undefined') {
  window.renderModels = renderModels;
  window.setModelsSort = setModelsSort;
  window.setModelsArtifactFilter = setModelsArtifactFilter;
  window.setModelsModalityFilter = setModelsModalityFilter;
  window.setModelsFamilyFilter = setModelsFamilyFilter;
  initModelsSearchListener();
}
