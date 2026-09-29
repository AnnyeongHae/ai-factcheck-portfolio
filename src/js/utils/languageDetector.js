/**
 * ==============================================================================
 * Language Detector Utility (Single Source of Truth)
 * Deterministic Regex & Platform-based Source Language Detection
 * Supports: KO (Korean), ZH (Chinese), JA (Japanese), EN (English)
 * ==============================================================================
 */

export function detectSourceLang(item) {
  if (!item) return 'EN';
  const ai = item.ai_enrichment || {};
  const itPlat = (item.source_platform || '').toLowerCase();
  const itUrl = (item.source_url || '').toLowerCase();
  const rawItemText = `${item.title || ''} ${item.description || ''} ${item.title_ko || ''} ${item.content || ''}`;
  let effectiveSourceLang = (ai.source_lang || item.source_lang || '').toUpperCase();

  if (/[\uac00-\ud7a3]/.test(rawItemText) || /daum|geeknews|hada\.io|chosun|donga|yonhap|naver/i.test(itPlat) || /daum\.net|hada\.io|naver\.com/i.test(itUrl)) {
    effectiveSourceLang = 'KO';
  } else if (/[\u3040-\u30ff]/.test(rawItemText)) {
    effectiveSourceLang = 'JA';
  } else if (/[\u4e00-\u9fff]/.test(rawItemText) || /weibo|zhihu|36kr|ithome|sspai|bilibili|wechat|qq\.com|sina|baidu|jiqizhixin|qbitai|v2ex|geekpark|oschina|infoq/i.test(itPlat) || /\.cn|\.com\.cn|weibo\.com|zhihu\.com|36kr\.com|ithome\.com|sspai\.com|bilibili\.com|v2ex\.com/i.test(itUrl)) {
    effectiveSourceLang = 'ZH';
  } else if (!effectiveSourceLang || (effectiveSourceLang === 'KO' && !/[\uac00-\ud7a3]/.test(rawItemText))) {
    effectiveSourceLang = 'EN';
  }

  return effectiveSourceLang;
}

if (typeof window !== 'undefined') {
  window.detectSourceLang = detectSourceLang;
}
