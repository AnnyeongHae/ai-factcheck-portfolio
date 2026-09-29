/**
 * ==============================================================================
 * Technical Dossier Detail Modal Component
 * Displays verified factchecks, claims vs reality matrices, and benchmarks
 * ==============================================================================
 */

import { APP_CONFIG, ROUTES } from '../core/config.js';
import { currentLang, liveCasesData, casesData, currentView } from '../core/store.js';
import { i18n } from '../core/i18n.js';

export function openModal(c, skipHistory = false) {
  if (!c || typeof document === 'undefined') return;
  const cid = c.case_id || c.investigation_id;
  const curLang = typeof window !== 'undefined' && window.currentLang ? window.currentLang : currentLang;
  const curView = typeof window !== 'undefined' && window.currentView ? window.currentView : currentView;

  if (!skipHistory && cid && typeof history !== 'undefined') {
    const targetHash = '#/factchecks?case=' + encodeURIComponent(cid);
    if (window.location.hash !== targetHash) {
      try { history.pushState({ caseId: cid, view: curView }, '', targetHash); } catch (e) {}
    }
  }

  const modal = document.getElementById('detailModal');
  if (!modal) return;

  const story = c.portfolio_story || {};
  const handsOn = (story.hands_on_log && Object.keys(story.hands_on_log).length > 0) ? story.hands_on_log : (c.hands_on_review || {});
  const curation = c.curation || {};
  const clustering = c.clustering || {};
  const rawPost = c.raw_viral_post || {};
  const t = i18n[curLang] || i18n.KO;

  let displayTitle = c.title;
  let displayMotivation = curation.personal_motivation || story.the_hook || '';
  let displayQuote = rawPost.quote || '';

  if (curLang === 'ZH') {
    displayTitle = c.title_zh || c.title;
    displayMotivation = curation.personal_motivation_zh || displayMotivation;
    displayQuote = rawPost.quote_zh || displayQuote;
  } else if (curLang === 'EN') {
    displayTitle = c.title_en || c.title;
    displayMotivation = curation.personal_motivation_en || displayMotivation;
  }

  const safeSetTxt = (id, txt) => {
    const el = document.getElementById(id);
    if (el) el.innerText = txt || '';
  };

  safeSetTxt('modalTitle', displayTitle);
  safeSetTxt('modalModeBadge', curLang === 'KO' ? '기술 검증 리포트' : (curLang === 'ZH' ? '技术核验报告' : 'AUDITED DOSSIER'));
  const mMode = document.getElementById('modalModeBadge');
  if (mMode) mMode.className = 'text-xs px-2.5 py-0.5 rounded-md font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200';
  
  safeSetTxt('modalClusterBadge', clustering.cluster_name || c.category || 'Tech');
  safeSetTxt('modalVerdictBadge', c.verdict);
  const mVerdict = document.getElementById('modalVerdictBadge');
  if (mVerdict) {
    mVerdict.className = c.verdict === 'VERIFIED_TRUE' ? 'text-xs px-2.5 py-0.5 rounded-md font-semibold verdict-true' : 'text-xs px-2.5 py-0.5 rounded-md font-semibold verdict-half';
  }
  safeSetTxt('modalStageBadge', handsOn.status === 'ACTIVE_DEVELOPED' ? (curLang === 'KO' ? '실제 개발 적용' : (curLang === 'ZH' ? '生产级落地' : 'Production Active')) : (curLang === 'KO' ? '기술 조사 완료' : (curLang === 'ZH' ? '已审计完毕' : 'Audited')));

  safeSetTxt('modalMotivation', displayMotivation);
  safeSetTxt('modalWorkflow', curation.target_workflow || 'Universal AI Pipeline');

  // Viral Claims Dossier
  const viralBox = document.getElementById('modalViralPostBox');
  const hasQuote = displayQuote && displayQuote.trim().length > 0;

  if (hasQuote && viralBox) {
    viralBox.classList.remove('hidden');
    safeSetTxt('modalSecViralPostTitle', t.modalSecViralPostTitle);
    safeSetTxt('modalViralPlatformBadge', rawPost.platform || 'Social Post');
    safeSetTxt('modalViralAuthor', (rawPost.author ? (rawPost.author + ' : ') : '') + (rawPost.screenshot_note || 'Viral Marketing Post Evidence'));
    safeSetTxt('modalViralQuote', `"${displayQuote}"`);
    safeSetTxt('modalViralNote', rawPost.screenshot_note || '');
    safeSetTxt('modalViralLinkText', t.modalViralLinkText);
    
    const directLink = document.getElementById('modalViralDirectLink');
    if (directLink) {
      if (rawPost.post_url) {
        directLink.href = rawPost.post_url;
        directLink.classList.remove('hidden');
      } else if (rawPost.url) {
        directLink.href = rawPost.url;
        directLink.classList.remove('hidden');
      } else if (c.sources && c.sources.length > 0) {
        directLink.href = c.sources[0].url;
        directLink.classList.remove('hidden');
      } else {
        directLink.classList.add('hidden');
      }
    }
  } else if (viralBox) {
    viralBox.classList.add('hidden');
  }

  safeSetTxt('modalHook', (curLang === 'ZH' && story.the_hook_zh) ? story.the_hook_zh : (story.the_hook || ''));
  safeSetTxt('modalHype', story.marketing_hype_anatomy ? ((curLang === 'KO' ? '과장 마케팅 해부: ' : (curLang === 'ZH' ? '营销炒作解构: ' : 'Marketing Hype Anatomy: ')) + story.marketing_hype_anatomy) : '');
  
  safeSetTxt('modalHandsOnEnv', handsOn.test_environment || handsOn.environment ? ((curLang === 'KO' ? '환경: ' : (curLang === 'ZH' ? '实测环境: ' : 'Env: ')) + (handsOn.test_environment || handsOn.environment)) : '');
  safeSetTxt('modalHandsOnMetrics', handsOn.measured_results ? ((curLang === 'KO' ? '실측치: ' : (curLang === 'ZH' ? '实测指标: ' : 'Metrics: ')) + handsOn.measured_results) : (handsOn.measured_metrics ? Object.entries(handsOn.measured_metrics).map(([k, v]) => `${k}: ${v}`).join(' | ') : ''));
  safeSetTxt('modalHandsOnDetails', handsOn.details || handsOn.failure_modes || story.empirical_findings || 'Empirical benchmark verified.');

  // Claims vs Reality
  const claimsBox = document.getElementById('modalClaimsBox');
  const claimsList = document.getElementById('modalClaimsList');
  const claims = (c.claims_assessment && c.claims_assessment.length > 0) ? c.claims_assessment : (c.marketing_claims || []);
  const isAwaitingClaims = cid && (!claims || claims.length === 0);

  if (claims && claims.length > 0 && claimsBox && claimsList) {
    claimsBox.classList.remove('hidden');
    safeSetTxt('modalSecClaimsTitle', t.modalSecClaimsTitle || 'Marketing Claims vs Empirical Reality');
    claimsList.innerHTML = claims.map(cl => {
      const claimTitle = cl.claim || cl.statement || cl.claim_title || cl.claim_text || cl.marketing_hook || '';
      const claimTruth = cl.reality || cl.fact_checked_truth || cl.verification_evidence || cl.empirical_reality || cl.reality_check || '';
      const claimStatus = cl.status || cl.verdict || cl.claim_verdict || 'VERIFIED';
      const isTrue = (claimStatus === 'VERIFIED_TRUE' || claimStatus === 'TRUE');
      const isFalse = (claimStatus === 'FALSE' || claimStatus === 'FALSE_CLAIM' || claimStatus === 'GAMED_CLAIM' || claimStatus === 'MARKETING_HYPE');
      const statusClass = isTrue ? 'text-emerald-700 bg-emerald-50 border border-emerald-200' : (isFalse ? 'text-rose-700 bg-rose-50 border border-rose-200' : 'text-amber-800 bg-amber-50 border border-amber-200');
      return `
        <div class="p-3 rounded-lg bg-white border border-amber-200 text-xs space-y-1.5 shadow-sm">
          <div class="flex items-center justify-between font-mono text-[11px] gap-2 flex-wrap">
            <span class="text-ink-primary font-bold">Claim: "${claimTitle}"</span>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold ${statusClass}">${claimStatus}</span>
          </div>
          <div class="text-ink-secondary font-medium leading-relaxed">${curLang === 'KO' ? '🔬 실증 팩트 검증:' : (curLang === 'ZH' ? '🔬 实测事实核验:' : '🔬 Empirical Verification:')} ${claimTruth}</div>
        </div>
      `;
    }).join('');
  } else if (isAwaitingClaims && claimsBox && claimsList) {
    claimsBox.classList.remove('hidden');
    safeSetTxt('modalSecClaimsTitle', t.modalSecClaimsTitle || 'Marketing Claims vs Empirical Reality');
    claimsList.innerHTML = `
      <div id="modalClaimsSpinner" class="p-4 rounded-xl border border-indigo-200 bg-indigo-50/50 flex items-center justify-center gap-3 text-center shadow-xs">
        <div class="w-4 h-4 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin shrink-0"></div>
        <div class="text-left">
          <div class="text-xs font-bold text-indigo-950">${curLang === 'KO' ? `${APP_CONFIG.dbProvider}에서 원자적 검증 명제 및 실측 데이터 수신 중...` : (curLang === 'ZH' ? `正在从 ${APP_CONFIG.dbProvider} 实时接收原子级事实核验与实测数据...` : `Streaming atomic claims & empirical benchmarks from ${APP_CONFIG.dbProvider}...`)}</div>
          <div class="text-[10px] text-indigo-600">${curLang === 'KO' ? '초경량 요약본에서 심층 팩트체크 리포트를 확장 하이드레이션하고 있습니다.' : (curLang === 'ZH' ? '正在从超轻量摘要扩展深度事实核验报告。' : 'Hydrating in-depth dossier from lightweight summary snapshot.')}</div>
        </div>
      </div>
    `;
  } else if (claimsBox) {
    claimsBox.classList.add('hidden');
  }

  // Alternatives Table
  const altBody = document.getElementById('modalAlternativesBody');
  const alts = clustering.alternatives || c.alternatives || [];
  if (alts && alts.length > 0 && altBody) {
    altBody.innerHTML = alts.map(a => `
      <tr>
        <td class="p-3 font-bold text-ink-primary">${a.name || a.tool_name || ''}</td>
        <td class="p-3 font-mono text-ink-secondary text-[11px]">${a.tech_stack || a.stack || '-'}</td>
        <td class="p-3 text-emerald-700">${a.pros || '-'}</td>
        <td class="p-3 text-rose-700">${a.cons || '-'}</td>
        <td class="p-3 text-ink-secondary font-medium">${a.best_for || '-'}</td>
      </tr>
    `).join('');
  } else if (isAwaitingClaims && altBody) {
    altBody.innerHTML = `<tr><td colspan="5" class="p-4 text-center text-xs text-indigo-600"><div class="flex items-center justify-center gap-2"><div class="w-3.5 h-3.5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin shrink-0"></div>${curLang === 'KO' ? `대안 비교 데이터를 ${APP_CONFIG.dbProvider}에서 동기화 중...` : (curLang === 'ZH' ? `正在从 ${APP_CONFIG.dbProvider} 同步替代方案数据...` : `Syncing alternative comparisons from ${APP_CONFIG.dbProvider}...`)}</div></td></tr>`;
  } else if (altBody) {
    altBody.innerHTML = `<tr><td colspan="5" class="p-4 text-center text-ink-muted">${curLang === 'KO' ? '등록된 대체 기술 비교 데이터가 없습니다.' : (curLang === 'ZH' ? '暂无替代方案对比数据。' : 'No comparative alternatives registered.')}</td></tr>`;
  }

  // Sources
  const sourcesList = document.getElementById('modalSourcesList');
  const sources = c.sources || [];
  if (sourcesList) {
    sourcesList.innerHTML = sources.map(s => `
      <a href="${s.url}" target="_blank" rel="noopener noreferrer" class="p-2.5 rounded-xl bg-surface-subtle border border-surface-border hover:border-ink-primary flex items-center justify-between text-xs text-ink-secondary hover:text-ink-primary transition">
        <div class="space-y-0.5">
          <span class="text-[10px] font-mono text-ink-primary uppercase font-bold">${s.tier || 'Tier 1'} • ${s.type || 'Repository'}</span>
          <div class="font-medium truncate max-w-[240px] text-ink-primary">${s.name || s.title || 'Source Link'}</div>
        </div>
        <i data-lucide="external-link" class="w-3.5 h-3.5 text-ink-muted shrink-0"></i>
      </a>
    `).join('');
  }

  modal.classList.remove('hidden');
  document.body.style.overflow = 'hidden';
  if (window.lucide) window.lucide.createIcons();

  // On-Demand Full Case Hydration
  if (cid && !skipHistory && (!c.claims_assessment || c.claims_assessment.length === 0 || !c.portfolio_story?.marketing_hype_anatomy)) {
    const fetchUrl = APP_CONFIG.apiUrl(`/api/portfolios?case_id=${encodeURIComponent(cid)}`);
    fetch(fetchUrl)
      .then(res => res.json())
      .then(data => {
        if (data && data.success && data.case) {
          Object.assign(c, data.case);
          openModal(c, true);
        }
      })
      .catch(() => {});
  }
}

export function openCaseModal(caseId) {
  if (!caseId) return;
  const lCases = typeof window !== 'undefined' ? window.liveCasesData : liveCasesData;
  const cData = typeof window !== 'undefined' ? window.casesData : casesData;
  let c = (lCases || []).find(x => x.case_id === caseId || x.investigation_id === caseId) || (cData || []).find(x => x.case_id === caseId);
  if (c) {
    openModal(c);
  } else {
    const fetchUrl = APP_CONFIG.apiUrl(`/api/portfolios?case_id=${encodeURIComponent(caseId)}`);
    fetch(fetchUrl)
      .then(res => res.json())
      .then(data => {
        if (data && data.success && data.case) {
          openModal(data.case);
        }
      })
      .catch(() => {});
  }
}

export function closeModal(pushHistory = true) {
  if (typeof document === 'undefined') return;
  const modal = document.getElementById('detailModal');
  if (modal) modal.classList.add('hidden');
  document.body.style.overflow = 'auto';

  const curView = typeof window !== 'undefined' && window.currentView ? window.currentView : currentView;
  if (pushHistory && typeof history !== 'undefined') {
    const targetHash = ROUTES[curView] || '#/' + curView;
    if (window.location.hash !== targetHash) {
      try {
        history.pushState({ view: curView }, '', targetHash);
      } catch (e) {
        window.location.hash = targetHash;
      }
    }
  }
}

export function showVerificationReportModal(report) {
  if (typeof document === 'undefined') return;
  let modal = document.getElementById('verificationReportModal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'verificationReportModal';
    document.body.appendChild(modal);
  }

  const { allPassed, elapsed, checks } = report;
  const statusColor = allPassed ? 'emerald' : 'amber';
  const statusTitle = allPassed ? '시스템 무결성 100% 검증 완료' : '시스템 검증 점검 필요';
  const statusBadge = allPassed ? 'READY FOR PRODUCTION' : 'NEEDS ATTENTION';

  modal.className = 'fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs transition-opacity duration-200';
  modal.innerHTML = `
    <div class="relative w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl border border-surface-border space-y-4">
      <div class="flex items-center justify-between pb-3 border-b border-surface-border">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 rounded-lg bg-${statusColor}-50 text-${statusColor}-700 border border-${statusColor}-200 flex items-center justify-center">
            <i data-lucide="${allPassed ? 'shield-check' : 'alert-triangle'}" class="w-5 h-5"></i>
          </div>
          <div>
            <h3 class="text-sm font-bold text-ink-primary font-mono">${statusTitle}</h3>
            <span class="text-[10px] font-mono text-ink-muted">진단 소요: ${elapsed}초 | 소모 비용: $0 (0 LLM Tokens)</span>
          </div>
        </div>
        <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-${statusColor}-100 text-${statusColor}-800 border border-${statusColor}-300">${statusBadge}</span>
      </div>

      <div class="space-y-2 max-h-72 overflow-y-auto">
        ${checks.map((c) => `
          <div class="p-3 rounded-xl ${c.pass ? 'bg-surface-subtle border border-surface-border' : 'bg-rose-50 border border-rose-200'} flex items-start gap-2.5">
            <span class="w-5 h-5 rounded-md ${c.pass ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'} flex items-center justify-center text-xs shrink-0 mt-0.5 font-bold">
              ${c.pass ? '✓' : '✗'}
            </span>
            <div class="flex-1 min-w-0">
              <div class="text-xs font-bold ${c.pass ? 'text-ink-primary' : 'text-rose-900'}">${c.title}</div>
              <div class="text-[11px] font-mono text-ink-muted mt-0.5 leading-snug break-all">${c.details}</div>
            </div>
          </div>
        `).join('')}
      </div>

      <div class="pt-2 border-t border-surface-border flex items-center justify-between gap-2">
        <span class="text-[10px] text-ink-muted font-mono">Autonomous QA Verifier Agent</span>
        <button onclick="document.getElementById('verificationReportModal').remove()" class="px-4 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs font-mono transition cursor-pointer">
          닫기 (Close)
        </button>
      </div>
    </div>
  `;

  if (window.lucide) window.lucide.createIcons();
}

if (typeof window !== 'undefined') {
  window.openModal = openModal;
  window.openCaseModal = openCaseModal;
  window.closeModal = closeModal;
  window.showVerificationReportModal = showVerificationReportModal;
}
