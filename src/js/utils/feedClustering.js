/**
 * ==============================================================================
 * Feed Clustering & Entity Extraction Utility
 * Groups cross-posted stories and duplicate releases into unified cards
 * ==============================================================================
 */

export function extractStoryEntity(it) {
  if (!it) return '';
  const text = `${it.title || ''} ${it.title_ko || ''} ${it.source_url || ''} ${it.canonical_story_key || ''}`.toLowerCase();
  
  // 1. Versioned model or specific project regex
  const m = text.match(/\b(qwen[-_ ]?image[-_ ]?2\.?1|qwen[-_ ]?3\.?8[-_ ]?35b|qwen[-_ ]?2\.?5[-_ ]?coder|deepseek[-_ ]?[rv]\d+[\w.-]*|llama[-_ ]?\d+[\w.-]*|glm[-_ ]?\d+[\w.-]*|flux[-_ ]?\d+[\w.-]*|jev)\b/i);
  if (m) {
    return m[1].toLowerCase().replace(/[-_ ]+/g, '-');
  }
  
  // 2. Canonical story key if present and informative
  if (it.canonical_story_key && it.canonical_story_key.length > 5) {
    const cleaned = it.canonical_story_key.toLowerCase().replace(/-(?:github|huggingface|geeknews|hn|demo|release|repo|compact|efficient|unified|uncensored|gguf|trending).*$/, '');
    if (cleaned.length >= 4) return cleaned;
  }
  
  return '';
}

export function clusterFeedItems(rawItems) {
  if (!Array.isArray(rawItems) || rawItems.length <= 1) return rawItems || [];
  
  const entityMap = new Map();
  const clustered = [];

  for (const raw of rawItems) {
    const it = { ...raw };
    const entity = extractStoryEntity(it);

    if (entity && entity.length >= 3) {
      if (entityMap.has(entity)) {
        const primary = entityMap.get(entity);
        primary.sources = primary.sources ? [...primary.sources] : [];
        if (primary.sources.length === 0 && primary.source_platform) {
          primary.sources.push({
            source_name: primary.source_platform,
            platform: primary.source_platform,
            url: primary.source_url || primary.hn_url || primary.article_url || '',
            title: primary.title,
            type: 'original'
          });
        }

        const incomingUrl = it.source_url || it.hn_url || it.article_url || '';
        const exists = primary.sources.some(s => (s.url || '').toLowerCase() === incomingUrl.toLowerCase());
        if (!exists && incomingUrl) {
          primary.sources.push({
            source_name: it.source_platform || 'Cross-post',
            platform: it.source_platform || 'Cross-post',
            url: incomingUrl,
            title: it.title,
            type: 'cross_post'
          });
        }

        primary.cross_posts = primary.cross_posts ? [...primary.cross_posts] : [];
        primary.cross_posts.push({
          platform: it.source_platform,
          url: incomingUrl,
          title: it.title
        });

        primary.is_cross_spiking = true;

        if (Array.isArray(it.raw_comments) && it.raw_comments.length > 0) {
          primary.raw_comments = [...(primary.raw_comments || []), ...it.raw_comments];
        }
        continue;
      } else {
        entityMap.set(entity, it);
        clustered.push(it);
      }
    } else {
      clustered.push(it);
    }
  }

  return clustered;
}

if (typeof window !== 'undefined') {
  window.extractStoryEntity = extractStoryEntity;
  window.clusterFeedItems = clusterFeedItems;
}
