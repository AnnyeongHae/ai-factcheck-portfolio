/**
 * ==============================================================================
 * Stealth Navigation Engine (Anti-Tracking & No-Referrer)
 * Strips UTM / Analytics query parameters and isolates target browsing context
 * ==============================================================================
 */

export const STEALTH_TRACKING_KEYS = new Set([
  'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'utm_id',
  'ref', 'ref_src', 'ref_url', 'source', 'fbclid', 'gclid', 'msclkid', 'twclid',
  'si', 'spm', 'igshid', 'yclid', 'mc_cid', 'mc_eid', 'aff', 'affiliate'
]);

export function cleanStealthUrl(rawUrl) {
  if (!rawUrl) return '';
  try {
    const origin = typeof window !== 'undefined' ? window.location.origin : 'https://ai-factcheck-portfolio.vercel.app';
    const u = new URL(rawUrl, origin);
    if (!u.protocol.startsWith('http')) return rawUrl;
    
    const params = new URLSearchParams(u.search);
    const keysToDelete = [];
    for (const k of params.keys()) {
      const lk = k.toLowerCase();
      if (STEALTH_TRACKING_KEYS.has(lk) || lk.startsWith('utm_') || lk.includes('chatgpt')) {
        keysToDelete.push(k);
      }
    }
    keysToDelete.forEach(k => params.delete(k));
    u.search = params.toString() ? ('?' + params.toString()) : '';
    return u.toString();
  } catch (e) {
    return rawUrl;
  }
}

export function stealthNavigate(rawUrl, ev) {
  if (ev) {
    ev.preventDefault();
    ev.stopPropagation();
  }
  const cleanUrl = cleanStealthUrl(rawUrl);
  if (typeof window === 'undefined') return;

  // Strict stealth window open: No opener, no referrer, isolated context
  const newWin = window.open('', '_blank');
  if (newWin) {
    newWin.opener = null;
    newWin.location.replace(cleanUrl);
  } else {
    const a = document.createElement('a');
    a.href = cleanUrl;
    a.target = '_blank';
    a.rel = 'noopener noreferrer';
    a.referrerPolicy = 'no-referrer';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }
}

export function initStealthLinkInterceptor() {
  if (typeof document === 'undefined') return;
  document.addEventListener('click', (e) => {
    const link = e.target.closest('a');
    if (link && link.href && link.href.startsWith('http') && !link.href.includes(window.location.host)) {
      e.preventDefault();
      e.stopPropagation();
      stealthNavigate(link.href);
    }
  }, true);
}

if (typeof window !== 'undefined') {
  window.cleanStealthUrl = cleanStealthUrl;
  window.stealthNavigate = stealthNavigate;
  window.STEALTH_TRACKING_KEYS = STEALTH_TRACKING_KEYS;
}
