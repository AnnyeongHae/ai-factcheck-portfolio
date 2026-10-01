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
  const explicitLang = (ai.source_lang || item.source_lang || '').toUpperCase();
  if (['KO', 'EN', 'ZH', 'JA'].includes(explicitLang)) {
    return explicitLang;
  }

  const itPlat = (item.source_platform || '').toLowerCase();
  const itUrl = (item.source_url || '').toLowerCase();
  const origTitle = `${item.title || ''}`;

  if (/[\uac00-\ud7a3]/.test(origTitle) || /daum|geeknews|hada\.io|chosun|donga|yonhap|naver/i.test(itPlat) || /daum\.net|hada\.io|naver\.com/i.test(itUrl)) {
    return 'KO';
  } else if (/[\u3040-\u30ff]/.test(origTitle)) {
    return 'JA';
  } else if (/[\u4e00-\u9fff]/.test(origTitle) || /weibo|zhihu|36kr|ithome|sspai|bilibili|wechat|qq\.com|sina|baidu|jiqizhixin|qbitai|v2ex|geekpark|oschina|infoq/i.test(itPlat) || /\.cn|\.com\.cn|weibo\.com|zhihu\.com|36kr\.com|ithome\.com|sspai\.com|bilibili\.com|v2ex\.com/i.test(itUrl)) {
    return 'ZH';
  }
  return 'EN';
}

if (typeof window !== 'undefined') {
  window.detectSourceLang = detectSourceLang;
}
