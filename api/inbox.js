const { getDbPool } = require('./_lib/db');
const { handleOptions, setCorsHeaders } = require('./_lib/cors');

const inboxApiCache = new Map();
const CACHE_TTL_MS = 60 * 1000;
const MAX_CACHE_SIZE = 300;

function getCachedResponse(key) {
  const entry = inboxApiCache.get(key);
  if (!entry) return null;
  if (Date.now() - entry.timestamp > CACHE_TTL_MS) {
    inboxApiCache.delete(key);
    return null;
  }
  return entry.data;
}

function setCachedResponse(key, data) {
  if (inboxApiCache.size >= MAX_CACHE_SIZE) {
    const firstKey = inboxApiCache.keys().next().value;
    if (firstKey) inboxApiCache.delete(firstKey);
  }
  inboxApiCache.set(key, { timestamp: Date.now(), data });
}

module.exports = async (req, res) => {
  if (handleOptions(req, res, 'GET, OPTIONS')) return;
  setCorsHeaders(res, 'GET, OPTIONS');

  // 🌟 High-Performance Edge SWR Cache Headers
  res.setHeader('Cache-Control', 'public, s-maxage=600, stale-while-revalidate=86400');

  const cacheKey = req.url || JSON.stringify(req.query || {});
  const cachedData = getCachedResponse(cacheKey);
  if (cachedData) {
    return res.status(200).json(cachedData);
  }

  const pool = getDbPool();
  if (!pool) {
    return res.status(500).json({ status: 'error', message: 'Database connection not configured' });
  }

  try {
    const rawLimit = parseInt(req.query?.limit, 10);
    const limit = Number.isInteger(rawLimit) ? Math.min(100, Math.max(1, rawLimit)) : 15;
    
    // Page-based or offset-based calculation
    const rawPage = parseInt(req.query?.page, 10);
    let offset = 0;
    if (Number.isInteger(rawPage) && rawPage > 1) {
      offset = (rawPage - 1) * limit;
    } else {
      const rawOffset = parseInt(req.query?.offset, 10);
      offset = Number.isInteger(rawOffset) ? Math.max(0, rawOffset) : 0;
    }
    const page = Math.floor(offset / limit) + 1;

    const conditions = [];
    const params = [];

    // 1. Basic Type & Classification filters
    const itemType = req.query?.type;
    if (itemType && itemType !== 'ALL') {
      params.push(itemType);
      conditions.push('item_type = $' + params.length);
    }

    const isClassified = req.query?.classified;
    if (isClassified === 'true' || isClassified === 'false') {
      params.push(isClassified === 'true');
      conditions.push('is_classified = $' + params.length);
    }

    // 2. 🌟 Tier 1 Category Filter
    const tier1 = req.query?.tier1;
    if (tier1 && tier1 !== 'ALL') {
      params.push(tier1);
      conditions.push("COALESCE(raw_payload->>'tier1_category', 'TECH_COMPUTING') = $" + params.length);
    }

    // 3. 🌟 Tier 2 Specialization Filter
    const tier2 = req.query?.tier2;
    if (tier2 && tier2 !== 'ALL') {
      params.push(tier2);
      conditions.push("(COALESCE(raw_payload->>'tier2_category', category_primary, 'INDUSTRY_TRENDS') = $" + params.length + ")");
    }

    // 4. 🌟 Smart Facet Filter
    const facet = req.query?.facet;
    if (facet && facet !== 'ALL') {
      if (facet === 'CROSS_SPIKE') {
        conditions.push(`(
          raw_payload->>'is_cross_spiking' = 'true' 
          OR (jsonb_typeof(raw_payload->'sources') = 'array' AND jsonb_array_length(raw_payload->'sources') > 1)
          OR (raw_payload->'metric_tracking'->>'delta' ~ '^[0-9]+$' AND (raw_payload->'metric_tracking'->>'delta')::numeric > 0)
        )`);
      } else if (facet === 'MODEL') {
        conditions.push(`(
          raw_payload->>'facet_type' = 'MODEL'
          OR raw_payload->>'is_model' = 'true'
          OR (raw_payload->>'model_family' IS NOT NULL AND raw_payload->>'model_family' != '' AND raw_payload->>'model_family' != 'standalone')
          OR source_platform ILIKE '%model%'
          OR source_platform ILIKE '%space%'
          OR category_primary ILIKE '%model%'
        )`);
      } else if (facet === 'TOOL') {
        conditions.push(`(
          raw_payload->>'facet_type' = 'TOOL'
          OR source_platform ILIKE '%github%'
          OR raw_payload->>'artifact_type' ILIKE '%agent%'
          OR raw_payload->>'artifact_type' ILIKE '%skill%'
          OR category_primary ILIKE '%devtool%'
        )`);
      } else if (facet === 'NEWS') {
        conditions.push(`(
          raw_payload->>'facet_type' = 'NEWS'
          OR (
            (raw_payload->>'facet_type' IS NULL OR raw_payload->>'facet_type' != 'MODEL')
            AND (raw_payload->>'model_family' IS NULL OR raw_payload->>'model_family' = '' OR raw_payload->>'model_family' = 'standalone')
            AND source_platform NOT ILIKE '%github%'
            AND source_platform NOT ILIKE '%space%'
          )
        )`);
      }
    }

    // 5. Source Platform Filter
    const source = req.query?.source;
    if (source && source !== 'ALL') {
      params.push(`%${source}%`);
      conditions.push('source_platform ILIKE $' + params.length);
    }

    // 6. 🌟 Multi-Field Search Filter
    const search = (req.query?.search || '').trim();
    if (search) {
      params.push(`%${search}%`);
      const pIdx = params.length;
      conditions.push(`(
        title ILIKE $${pIdx}
        OR COALESCE(raw_payload->>'title_ko', '') ILIKE $${pIdx}
        OR COALESCE(raw_payload->>'title_en', '') ILIKE $${pIdx}
        OR COALESCE(raw_payload->>'hook_ko', '') ILIKE $${pIdx}
        OR COALESCE(raw_payload->>'hook', '') ILIKE $${pIdx}
        OR COALESCE(raw_payload->'ai_enrichment'->>'summary_ko', '') ILIKE $${pIdx}
        OR COALESCE(raw_payload->>'canonical_story_key', '') ILIKE $${pIdx}
      )`);
    }

    const whereClause = conditions.length > 0 ? ('WHERE ' + conditions.join(' AND ')) : '';

    // Sorting
    let sortParam = 'created_at DESC NULLS LAST, id DESC';
    const sort = req.query?.sort;
    if (sort === 'viral-score-desc' || sort === 'score') {
      sortParam = 'viral_score DESC NULLS LAST, created_at DESC, id DESC';
    } else if (sort === 'growth-delta-desc' || sort === 'growth') {
      sortParam = `CASE WHEN raw_payload->'metric_tracking'->>'delta' ~ '^[0-9]+$' THEN (raw_payload->'metric_tracking'->>'delta')::numeric ELSE 0 END DESC, created_at DESC, id DESC`;
    } else if (sort === 'published' || sort === 'date-pub-desc') {
      sortParam = 'harvested_date DESC NULLS LAST, created_at DESC, id DESC';
    } else if (sort === 'id') {
      sortParam = 'id DESC';
    } else if (sort === 'updated') {
      sortParam = 'updated_at DESC NULLS LAST, id DESC';
    }

    // Pagination limits
    params.push(limit);
    const limitParam = '$' + params.length;
    params.push(offset);
    const offsetParam = '$' + params.length;

    // 🚀 SOTA High-Performance Single Query with Window Count (Eliminates 50% Latency)
    const query = `
      SELECT id, inbox_id, source_platform, source_url, title, item_type, category_primary, 
             viral_metric, viral_score, is_classified, harvested_date, created_at, updated_at, raw_payload,
             COUNT(*) OVER() AS full_count
      FROM raw_trends_inbox
      ${whereClause}
      ORDER BY ${sortParam}
      LIMIT ${limitParam} OFFSET ${offsetParam};
    `;
    const result = await pool.query(query, params);

    let total = 0;
    if (result.rows.length > 0) {
      total = parseInt(result.rows[0].full_count, 10) || 0;
    } else if (offset > 0) {
      // If offset was past end of results, get true count
      const countRes = await pool.query('SELECT COUNT(*) FROM raw_trends_inbox ' + whereClause + ';', params.slice(0, -2));
      total = parseInt(countRes.rows[0].count, 10) || 0;
    }

    // Clean & Lean items mapping (Preserve all card display fields, strip internal/giant blobs)
    const items = result.rows.map(r => {
      let p = r.raw_payload;
      if (typeof p === 'string') {
        try { p = JSON.parse(p); } catch (e) { p = {}; }
      }
      p = p || {};

      let desc = p.description || '';
      if (typeof desc === 'string') {
        desc = desc.replace(/^HN\s*Score:\s*\d+\s*pts\s*(\|\s*Comments:\s*\d+\s*)?(\|\s*)?/i, '');
        desc = desc.replace(/^Abstract:\s*/i, '').trim();
      }

      const multi = p.multilingual || p.ai_enrichment?.multilingual || null;
      const keyTakeaways = (p.ai_enrichment?.key_takeaways && p.ai_enrichment.key_takeaways.length > 0)
        ? p.ai_enrichment.key_takeaways
        : (multi?.ko?.key_takeaways && multi.ko.key_takeaways.length > 0)
          ? multi.ko.key_takeaways
          : (p.key_takeaways || []);

      const aiEnrichment = p.ai_enrichment ? {
        ...p.ai_enrichment,
        key_takeaways: keyTakeaways,
        takeaways_ko: multi?.ko?.key_takeaways || keyTakeaways,
        takeaways_en: multi?.en?.key_takeaways || [],
        takeaways_zh: multi?.zh?.key_takeaways || [],
        summary_ko: p.ai_enrichment.summary_ko || '',
        enriched_at: p.ai_enrichment.enriched_at || r.updated_at || r.harvested_date,
        enriched_by_model: p.ai_enrichment.enriched_by_model || 'inclusionai/ling-3.0-flash-sante:free'
      } : (keyTakeaways.length > 0 ? {
        key_takeaways: keyTakeaways,
        takeaways_ko: multi?.ko?.key_takeaways || keyTakeaways,
        takeaways_en: multi?.en?.key_takeaways || [],
        takeaways_zh: multi?.zh?.key_takeaways || [],
        summary_ko: '',
        enriched_at: r.updated_at || r.harvested_date,
        enriched_by_model: 'inclusionai/ling-3.0-flash-sante:free'
      } : null);

      return {
        id: r.id,
        inbox_id: r.inbox_id,
        source_platform: r.source_platform,
        source_url: r.source_url || p.source_url || '',
        hn_url: p.hn_url || ((r.source_url || '').includes('news.ycombinator.com') ? r.source_url : null),
        article_url: p.article_url || null,
        title: r.title,
        title_ko: p.title_ko || r.title,
        title_en: p.title_en || '',
        title_zh: p.title_zh || '',
        hook: p.hook || '',
        hook_ko: p.hook_ko || p.hook || '',
        hook_en: p.hook_en || '',
        hook_zh: p.hook_zh || '',
        description: desc,
        item_type: r.item_type,
        category_primary: r.category_primary,
        tier1_category: p.tier1_category || 'TECH_COMPUTING',
        tier2_category: p.tier2_category || r.category_primary || 'INDUSTRY_TRENDS',
        facet_type: p.facet_type || 'NEWS',
        is_model: p.is_model !== undefined ? p.is_model : (p.facet_type === 'MODEL'),
        model_family: p.model_family || '',
        artifact_type: p.artifact_type || '',
        sources: p.sources || [],
        cross_posts: p.cross_posts || [],
        is_cross_spiking: Boolean(p.is_cross_spiking),
        metric_tracking: p.metric_tracking || {},
        viral_metric: r.viral_metric || p.viral_metric || '',
        viral_score: r.viral_score !== null ? Number(r.viral_score) : (p.viral_score || 0),
        is_classified: r.is_classified,
        harvested_date: r.harvested_date,
        published_at: p.published_at || p.published_date || r.harvested_date,
        created_at: r.created_at,
        updated_at: r.updated_at,
        multilingual: multi,
        key_takeaways: keyTakeaways,
        ai_enrichment: aiEnrichment,
        raw_comments: Array.isArray(p.raw_comments) ? p.raw_comments : [],
        canonical_story_key: p.canonical_story_key || ''
      };
    });

    const totalPages = Math.ceil(total / limit) || 1;

    const responsePayload = {
      status: 'success',
      total: total,
      page: page,
      total_pages: totalPages,
      limit: limit,
      offset: offset,
      count: items.length,
      has_more: (offset + items.length) < total,
      items: items
    };

    setCachedResponse(cacheKey, responsePayload);

    return res.status(200).json(responsePayload);
  } catch (err) {
    console.error('[API Inbox Error]:', err);
    return res.status(500).json({ status: 'error', message: 'Internal server error while fetching inbox items' });
  }
};
