/**
 * ==============================================================================
 * DateTime & KST Utility (Single Source of Truth)
 * Sub-Second Sorting, KST Normalization, and Compact Display Helpers
 * ==============================================================================
 */

export function parseItemTimestamp(item, preferField) {
  if (!item) return 0;
  let raw = '';
  if (preferField === 'audit') {
    // AI 분석일(Audit Date) must strictly reflect actual AI enrichment/audit time!
    raw = item.ai_enrichment?.enriched_at || item.enriched_at || item.audited_at || item.investigation_date;
    if (!raw) return 0;
    const ms = new Date(raw).getTime();
    return isNaN(ms) ? 0 : ms;
  } else {
    // For freshest items in inbox/news/models, prioritize the latest active timestamp
    const tHarvest = item.harvested_at ? new Date(item.harvested_at).getTime() : 0;
    const tPublish = item.published_at ? new Date(item.published_at).getTime() : 0;
    const tCreated = item.created_at ? new Date(item.created_at).getTime() : 0;
    const tSourcePub = item.source_published_date ? new Date(item.source_published_date).getTime() : 0;
    const tDate = item.harvested_date ? new Date(item.harvested_date).getTime() : 0;
    const best = Math.max(
      isNaN(tHarvest) ? 0 : tHarvest,
      isNaN(tPublish) ? 0 : tPublish,
      isNaN(tCreated) ? 0 : tCreated,
      isNaN(tSourcePub) ? 0 : tSourcePub,
      isNaN(tDate) ? 0 : tDate
    );
    return best;
  }
}

export function formatDateTime(raw) {
  if (!raw) return '-';
  const d = new Date(raw);
  if (isNaN(d.getTime())) return String(raw).substring(0, 10);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const hh = String(d.getHours()).padStart(2, '0');
  const mm = String(d.getMinutes()).padStart(2, '0');
  return `${y}-${m}-${day} ${hh}:${mm}`;
}

export function formatDateTimeCompact(raw) {
  if (!raw) return '-';
  const s = String(raw).trim();
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) {
    const parts = s.split('-');
    return `<span class="hidden sm:inline">${parts[0]}-</span>${parts[1]}-${parts[2]}`;
  }
  const d = new Date(raw);
  if (isNaN(d.getTime())) return s.substring(0, 10);
  try {
    const parts = new Intl.DateTimeFormat('en-CA', {
      timeZone: 'Asia/Seoul',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    }).formatToParts(d);
    const getP = (type) => parts.find(p => p.type === type)?.value || '';
    const y = getP('year');
    const m = getP('month');
    const day = getP('day');
    const hh = getP('hour');
    const mm = getP('minute');
    return `<span class="hidden sm:inline">${y}-</span>${m}-${day} ${hh}:${mm}`;
  } catch (e) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hh = String(d.getHours()).padStart(2, '0');
    const mm = String(d.getMinutes()).padStart(2, '0');
    return `<span class="hidden sm:inline">${y}-</span>${m}-${day} ${hh}:${mm}`;
  }
}

export function formatKstMonthDay(raw) {
  if (!raw) return '-';
  try {
    const d = new Date(raw);
    if (isNaN(d.getTime())) return String(raw).substring(5, 10);
    return new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Seoul', month: '2-digit', day: '2-digit' }).format(d);
  } catch (e) {
    return String(raw).substring(5, 10);
  }
}

export function getDynamicKstHour() {
  try {
    return parseInt(new Intl.DateTimeFormat('en-US', { timeZone: 'Asia/Seoul', hour: 'numeric', hour12: false }).format(new Date()), 10);
  } catch (e) {
    const now = new Date();
    return (now.getUTCHours() + 9) % 24;
  }
}

export function getDynamicKstDate() {
  const now = new Date();
  const utc = now.getTime() + (now.getTimezoneOffset() * 60000);
  return new Date(utc + (3600000 * 9));
}

export function getDynamicKstSession() {
  const h = getDynamicKstHour();
  if (h < 6) return 1;
  if (h < 12) return 2;
  if (h < 18) return 3;
  return 4;
}

export function formatModelAttribution(modelStr) {
  if (!modelStr) return 'AI 검증';
  let s = String(modelStr).replace(/^models\//, '').replace(/:free$/, '');
  if (s.includes('/')) s = s.split('/').pop();
  return '🤖 ' + s;
}

if (typeof window !== 'undefined') {
  window.parseItemTimestamp = parseItemTimestamp;
  window.formatDateTime = formatDateTime;
  window.formatDateTimeCompact = formatDateTimeCompact;
  window.formatKstMonthDay = formatKstMonthDay;
  window.formatModelAttribution = formatModelAttribution;
  window.getDynamicKstHour = getDynamicKstHour;
  window.getDynamicKstDate = getDynamicKstDate;
  window.getDynamicKstSession = getDynamicKstSession;
}

