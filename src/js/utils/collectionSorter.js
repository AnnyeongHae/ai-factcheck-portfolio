/**
 * ==============================================================================
 * Collection Sorter Engine (Sub-Second Precision & Deterministic Tie-Breaker)
 * ==============================================================================
 */

import { parseItemTimestamp } from './dateTime.js';
import { calculateStandardizedViralScore } from './metricFormatter.js';

export function sortCollection(items, sortKey) {
  if (!Array.isArray(items)) return [];
  return items.sort((a, b) => {
    const idA = a.case_id || a.inbox_id || a.id || '';
    const idB = b.case_id || b.inbox_id || b.id || '';

    if (sortKey === 'date-source-desc') {
      const diff = parseItemTimestamp(b, 'source') - parseItemTimestamp(a, 'source');
      if (diff !== 0) return diff;
      return idB.localeCompare(idA);
    }
    if (sortKey === 'date-source-asc' || sortKey === 'date-asc') {
      const diff = parseItemTimestamp(a, 'source') - parseItemTimestamp(b, 'source');
      if (diff !== 0) return diff;
      return idA.localeCompare(idB);
    }
    if (sortKey === 'date-audit-desc' || sortKey === 'date-desc') {
      const tB = parseItemTimestamp(b, 'audit');
      const tA = parseItemTimestamp(a, 'audit');
      if (tB !== tA) return tB - tA;
      const sB = parseItemTimestamp(b, 'source');
      const sA = parseItemTimestamp(a, 'source');
      if (sB !== sA) return sB - sA;
      return idB.localeCompare(idA);
    }
    if (sortKey === 'date-audit-asc') {
      const tA = parseItemTimestamp(a, 'audit');
      const tB = parseItemTimestamp(b, 'audit');
      if (tA > 0 && tB > 0 && tA !== tB) return tA - tB;
      if (tA > 0 && tB === 0) return -1;
      if (tB > 0 && tA === 0) return 1;
      const sDiff = parseItemTimestamp(a, 'source') - parseItemTimestamp(b, 'source');
      if (sDiff !== 0) return sDiff;
      return idA.localeCompare(idB);
    }
    if (sortKey === 'title-asc') {
      return (a.title || '').localeCompare(b.title || '');
    }
    if (sortKey === 'viral-desc') {
      return calculateStandardizedViralScore(b) - calculateStandardizedViralScore(a);
    }
    if (sortKey === 'viral-asc') {
      return calculateStandardizedViralScore(a) - calculateStandardizedViralScore(b);
    }
    const defDiff = parseItemTimestamp(b, 'source') - parseItemTimestamp(a, 'source');
    if (defDiff !== 0) return defDiff;
    return idB.localeCompare(idA);
  });
}

if (typeof window !== 'undefined') {
  window.sortCollection = sortCollection;
}
