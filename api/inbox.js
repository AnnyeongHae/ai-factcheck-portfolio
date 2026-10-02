const { getDbPool } = require('./_lib/db');
const { handleOptions, setCorsHeaders } = require('./_lib/cors');

const inboxApiCache = new Map();
const CACHE_TTL_MS = 30 * 1000;
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

function getStaticInboxFallback(req) {
  try {
    let d = null;
    try {
      d = require('./_lib/data.json');
    } catch (e1) {
      try {
        d = require('../public/data.json');
      } catch (e2) {
        const fs = require('fs');
        const path = require('path');
        const candidatePaths = [
          path.join(__dirname, '_lib', 'data.json'),
          path.join(process.cwd(), 'public', 'data.json'),
          path.join(process.cwd(), 'docs', 'data.json'),
          path.join(__dirname, '..', 'public', 'data.json'),
          path.join(__dirname, '..', 'docs', 'data.json')
        ];
        for (const p of candidatePaths) {
          if (fs.existsSync(p)) {
            d = JSON.parse(fs.readFileSync(p, 'utf8'));
            if (d) break;
          }
        }
      }
    }

    if (d && (d.news_items || d.inbox_items)) {
      const type = (req.query?.type || req.query?.tab || '').toUpperCase();
      let items = d.news_items || [];
      if (type === 'MODEL') items = d.model_items || [];
      else if (type === 'INBOX') items = d.inbox_items || [];
      else if (type === 'ALL') items = (d.news_items || []).concat(d.model_items || []);

      const facet = req.query?.facet;
      if (facet && facet !== 'ALL') {
        if (facet === 'CROSS_SPIKE') {
          const nowMs = Date.now();
          const sevenDaysMs = 7 * 24 * 60 * 60 * 1000;
          items = items.filter(it => {
            const itemTime = new Date(it.created_at || it.harvested_date || 0).getTime();
            if (nowMs - itemTime > sevenDaysMs) return false;
            const score = it.spike_analysis ? Number(it.spike_analysis.score || 0) : 0;
            return (it.is_cross_spiking || (Array.isArray(it.sources) && it.sources.length > 1)) && (!it.spike_analysis || score >= 0.3);
          });
        } else if (facet === 'MODEL') {
          items = items.filter(it => it.facet_type === 'MODEL' || it.is_model || (it.source_platform || '').toLowerCase().includes('model'));
        } else if (facet === 'TOOL') {
          items = items.filter(it => it.facet_type === 'TOOL' || (it.source_platform || '').toLowerCase().includes('github'));
        }
      }

      const source = req.query?.source;
      if (source && source !== 'ALL') {
        const srcLower = source.toLowerCase();
        items = items.filter(it => (it.source_platform || '').toLowerCase().includes(srcLower));
      }

      const tier1 = req.query?.tier1;
      if (tier1 && tier1 !== 'ALL') {
        items = items.filter(it => (it.tier1_category || 'TECH_COMPUTING') === tier1);
      }

      const lang = (req.query?.lang || '').toUpperCase();
      if (lang && lang !== 'ALL') {
        items = items.filter(it => {
          const itemLang = (it.ai_enrichment?.source_lang || it.source_lang || '').toUpperCase();
          if (itemLang) return itemLang === lang;
          const plat = (it.source_platform || '').toLowerCase();
          const inferred = (plat.includes('geeknews') || plat.includes('daum') || plat.includes('naver') || plat.includes('pytorchkr')) ? 'KO' : 'EN';
          return inferred === lang;
        });
      }

      const limit = Math.min(100, Math.max(1, parseInt(req.query?.limit, 10) || 15));
      const page = Math.max(1, parseInt(req.query?.page, 10) || 1);
      const offset = (page - 1) * limit;
      const pagedItems = items.slice(offset, offset + limit);

      return {
        status: 'success',
        source: 'static_snapshot_fallback',
        page: page,
        limit: limit,
        total: items.length,
        total_pages: Math.ceil(items.length / limit) || 1,
        items: pagedItems,
        news: pagedItems
      };
    }
  } catch (e) {}
  return null;
}

module.exports = async (req, res) => {
  if (handleOptions(req, res, 'GET, OPTIONS')) return;
  setCorsHeaders(res, 'GET, OPTIONS');

  // 🌟 High-Performance Edge SWR Cache Headers (30s Freshness for Real-time Sync)
  res.setHeader('Cache-Control', 'public, s-maxage=30, stale-while-revalidate=120');

  const cacheKey = req.url || JSON.stringify(req.query || {});
  const cachedData = getCachedResponse(cacheKey);
  if (cachedData) {
    return res.status(200).json(cachedData);
  }

  const pool = getDbPool();
  if (!pool) {
    const fallback = getStaticInboxFallback(req);
    if (fallback) {
      return res.status(200).json(fallback);
    }
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

    // 🌟 0-A. Cross-Viral Ranking Calendar Metadata Endpoint (?spike_dates_list=true)
    if (req.query?.spike_dates_list === 'true') {
      const datesQuery = `
        SELECT
          ranking_date::text AS ranking_date,
          COUNT(*)::int AS total_ranked,
          MAX(spike_score)::numeric(10,1) AS top_score,
          (ARRAY_AGG(title_snapshot ORDER BY rank_position ASC))[1] AS top_title,
          (ARRAY_AGG(spike_tier ORDER BY rank_position ASC))[1] AS top_tier
        FROM cross_viral_daily_rankings
        GROUP BY ranking_date
        ORDER BY ranking_date DESC
        LIMIT 60;
      `;
      const datesRes = await pool.query(datesQuery);
      const payload = {
        status: 'success',
        dates: datesRes.rows
      };
      setCachedResponse(cacheKey, payload);
      return res.status(200).json(payload);
    }

    const spikeDate = (req.query?.spike_date || '').trim();
    const isValidSpikeDate = /^\d{4}-\d{2}-\d{2}$/.test(spikeDate);

    const conditions = [];
    const params = [];

    // 0. Live Inbox Filter: Exclude archived duplicates by default (unless querying a historical daily ranking snapshot)
    const includeArchived = req.query?.include_archived === 'true' || isValidSpikeDate;
    if (!includeArchived) {
      conditions.push("(triage_status IS NULL OR triage_status != 'archived')");
    }

    // 1. Basic Type, Source Language & Classification filters
    const itemType = req.query?.type;
    if (itemType && itemType !== 'ALL') {
      params.push(itemType);
      conditions.push('item_type = $' + params.length);
    }

    const langFilter = (req.query?.lang || '').toUpperCase();
    if (langFilter && langFilter !== 'ALL' && ['KO', 'EN', 'ZH'].includes(langFilter)) {
      params.push(langFilter);
      const pIdx = params.length;
      conditions.push(`UPPER(COALESCE(
        NULLIF(raw_payload->'ai_enrichment'->>'source_lang', ''),
        NULLIF(raw_payload->>'source_lang', ''),
        CASE
          WHEN source_platform ILIKE '%geeknews%' OR source_platform ILIKE '%daum%' OR source_platform ILIKE '%naver%' OR source_platform ILIKE '%pytorchkr%' OR title ~ '[가-힣]' THEN 'KO'
          WHEN title ~ '[\\u4e00-\\u9fff]' THEN 'ZH'
          ELSE 'EN'
        END
      )) = $${pIdx}`);
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

    // 3. 🌟 Tier 2 Specialization Filter with Alias Expansion
    const tier2 = req.query?.tier2;
    if (tier2 && tier2 !== 'ALL') {
      const t2Map = {
        'INFERENCE_OPT': ['INFERENCE_OPT', 'INFERENCE_SERVING'],
        'AGENTS_DEVTOOLS': ['AGENTS_DEVTOOLS', 'SOFTWARE_WEB'],
        'MULTIMODAL_AI': ['MULTIMODAL_AI', 'MULTIMODAL_MEDIA'],
        'FOUNDATION_MODELS': ['FOUNDATION_MODELS', 'FOUNDATION_WEIGHTS'],
        'INFRA_RAG_SECURITY': ['INFRA_RAG_SECURITY', 'SYSTEM_CYBERSEC']
      };
      if (t2Map[tier2]) {
        const placeholders = t2Map[tier2].map(v => {
          params.push(v);
          return '$' + params.length;
        }).join(', ');
        conditions.push(`COALESCE(raw_payload->>'tier2_category', category_primary) IN (${placeholders})`);
      } else if (tier2 === 'INDUSTRY_TRENDS') {
        const allKnown = [
          'INFERENCE_OPT', 'INFERENCE_SERVING',
          'AGENTS_DEVTOOLS', 'SOFTWARE_WEB',
          'MULTIMODAL_AI', 'MULTIMODAL_MEDIA',
          'FOUNDATION_MODELS', 'FOUNDATION_WEIGHTS',
          'INFRA_RAG_SECURITY', 'SYSTEM_CYBERSEC'
        ];
        const placeholders = allKnown.map(v => {
          params.push(v);
          return '$' + params.length;
        }).join(', ');
        conditions.push(`(COALESCE(raw_payload->>'tier2_category', category_primary) NOT IN (${placeholders}) OR COALESCE(raw_payload->>'tier2_category', category_primary) IS NULL)`);
      } else {
        params.push(tier2);
        conditions.push("(COALESCE(raw_payload->>'tier2_category', category_primary, 'INDUSTRY_TRENDS') = $" + params.length + ")");
      }
    }

    // 4. 🌟 Smart Facet Filter
    const facet = req.query?.facet;
    if (facet && facet !== 'ALL') {
      if (facet === 'CROSS_SPIKE') {
        if (isValidSpikeDate) {
          params.push(spikeDate);
          conditions.push(`id IN (SELECT item_id FROM cross_viral_daily_rankings WHERE ranking_date = $${params.length}::date)`);
        } else {
          conditions.push(`(
            (raw_payload->>'is_cross_spiking' = 'true' OR (CASE WHEN jsonb_typeof(raw_payload->'sources') = 'array' THEN jsonb_array_length(raw_payload->'sources') ELSE 0 END > 1))
            AND created_at >= (NOW() - INTERVAL '7 days')
            AND (
              raw_payload->'spike_analysis' IS NULL
              OR COALESCE(live_spike_score, (raw_payload->'spike_analysis'->>'score')::numeric, 0) >= 0.3
            )
          )`);
        }
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
          OR item_type = 'NEWS'
          OR raw_payload->'ai_enrichment'->>'type_classification' = 'NEWS'
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

    // 6. 🌟 Multi-Keyword Smart Search Filter (Tokenized AND matching)
    const rawSearch = (req.query?.search || '').trim();
    if (rawSearch) {
      const searchTokens = rawSearch.split(/\s+/).filter(Boolean);
      for (const token of searchTokens) {
        params.push(`%${token}%`);
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
    }

    // 7. 🔬 Strict AI Audit Date Filtering & Pre-Analysis Pending Filter
    const sort = req.query?.sort;
    const status = req.query?.status;
    const includePending = req.query?.include_pending === 'true' || req.query?.includePending === 'true' || req.query?.show_pending === 'true';

    if (status === 'pending' || sort === 'pending') {
      conditions.push("(raw_payload->'ai_enrichment' IS NULL OR is_classified = FALSE OR raw_payload->'ai_enrichment'->>'enriched_at' IS NULL)");
    } else if (sort === 'date-audit-desc' || sort === 'date-audit-asc') {
      if (!includePending) {
        conditions.push("(is_classified = TRUE AND raw_payload ? 'ai_enrichment' AND (raw_payload->'ai_enrichment') IS NOT NULL AND (raw_payload->'ai_enrichment'->>'enriched_at') IS NOT NULL)");
      }
    }

    const whereClause = conditions.length > 0 ? ('WHERE ' + conditions.join(' AND ')) : '';

    // Sorting
    let sortParam = 'created_at DESC NULLS LAST, id DESC';
    if (status === 'pending' || sort === 'pending') {
      sortParam = 'created_at DESC NULLS LAST, id DESC';
    } else if (isValidSpikeDate && facet === 'CROSS_SPIKE') {
      params.push(spikeDate);
      const sdIdx = params.length;
      sortParam = `
        (SELECT rank_position FROM cross_viral_daily_rankings cdr WHERE cdr.item_id = raw_trends_inbox.id AND cdr.ranking_date = $${sdIdx}::date LIMIT 1) ASC NULLS LAST,
        COALESCE(peak_spike_score, live_spike_score, 0) DESC, id DESC
      `;
    } else if (sort === 'viral-score-desc' || sort === 'score' || (!sort && facet === 'CROSS_SPIKE')) {
      sortParam = `
        COALESCE(live_spike_score, NULLIF(raw_payload->'spike_analysis'->>'score', '')::numeric, viral_score, 0) DESC,
        CASE WHEN jsonb_typeof(raw_payload->'sources') = 'array' THEN jsonb_array_length(raw_payload->'sources') ELSE 0 END DESC,
        created_at DESC, id DESC
      `;
    } else if (sort === 'growth-delta-desc' || sort === 'growth') {
      sortParam = `CASE WHEN raw_payload->'metric_tracking'->>'delta' ~ '^[0-9]+$' THEN (raw_payload->'metric_tracking'->>'delta')::numeric ELSE 0 END DESC, created_at DESC, id DESC`;
    } else if (sort === 'published' || sort === 'date-pub-desc' || sort === 'date-source-desc') {
      sortParam = 'harvested_date DESC NULLS LAST, created_at DESC, id DESC';
    } else if (sort === 'date-source-asc') {
      sortParam = 'harvested_date ASC NULLS LAST, created_at ASC, id ASC';
    } else if (sort === 'id') {
      sortParam = 'id DESC';
    } else if (sort === 'date-audit-desc') {
      sortParam = "COALESCE((raw_payload->'ai_enrichment'->>'enriched_at')::timestamptz, updated_at) DESC NULLS LAST, id DESC";
    } else if (sort === 'date-audit-asc') {
      sortParam = "COALESCE((raw_payload->'ai_enrichment'->>'enriched_at')::timestamptz, updated_at) ASC NULLS LAST, id ASC";
    } else if (sort === 'updated') {
      sortParam = 'updated_at DESC NULLS LAST, id DESC';
    }

    const countParams = [...params];
    if (isValidSpikeDate && facet === 'CROSS_SPIKE') {
      // Remove the extra sort param from countQuery params
      countParams.pop();
    }

    // Pagination limits
    params.push(limit);
    const limitParam = '$' + params.length;
    params.push(offset);
    const offsetParam = '$' + params.length;

    // 🚀 SOTA High-Performance Fast Index Scan
    const dataQuery = `
      SELECT id, inbox_id, source_platform, source_url, title, item_type, category_primary, 
             viral_metric, viral_score, is_classified, harvested_date, created_at, updated_at, raw_payload,
             live_spike_score, peak_spike_score, peak_spike_date::text AS peak_spike_date, best_spike_rank
      FROM raw_trends_inbox
      ${whereClause}
      ORDER BY ${sortParam}
      LIMIT ${limitParam} OFFSET ${offsetParam};
    `;

    const countQuery = `SELECT COUNT(id) AS total_count FROM raw_trends_inbox ${whereClause};`;

    // Execute data fetch, count, and optional historical snapshot fetch in parallel
    const queries = [
      pool.query(dataQuery, params),
      pool.query(countQuery, countParams)
    ];
    if (isValidSpikeDate) {
      queries.push(
        pool.query(
          `SELECT item_id, ranking_date::text AS ranking_date, rank_position, spike_score, raw_spike_score,
                  spike_tier, axes_count, sources_count, press_count, community_count, code_count,
                  velocity, depth, canonical_release_key
           FROM cross_viral_daily_rankings
           WHERE ranking_date = $1::date`,
          [spikeDate]
        )
      );
    }

    const [result, countRes, histRes] = await Promise.all(queries);
    const histMap = new Map();
    if (histRes && Array.isArray(histRes.rows)) {
      for (const hr of histRes.rows) {
        histMap.set(Number(hr.item_id), hr);
      }
    }

    // Fetch per-item daily point trajectory (spike_history) for returned items
    const spikeHistoryMap = new Map();
    const returnedIds = result.rows.map(r => Number(r.id)).filter(id => Number.isFinite(id) && id > 0);
    if (returnedIds.length > 0) {
      try {
        const trajRes = await pool.query(
          `SELECT item_id, ranking_date::text AS date, rank_position AS rank,
                  spike_score::float8 AS score, sources_count::int AS sources_count
           FROM cross_viral_daily_rankings
           WHERE item_id = ANY($1::bigint[])
           ORDER BY ranking_date ASC`,
          [returnedIds]
        );
        for (const tr of trajRes.rows) {
          const iid = Number(tr.item_id);
          if (!spikeHistoryMap.has(iid)) spikeHistoryMap.set(iid, []);
          spikeHistoryMap.get(iid).push({
            date: tr.date,
            rank: Number(tr.rank),
            score: Number(tr.score),
            sources_count: Number(tr.sources_count)
          });
        }
      } catch (trajErr) {
        // Non-fatal fallback if table is not yet initialized
      }
    }

    const total = parseInt(countRes.rows[0]?.total_count, 10) || 0;

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

      // 🌟 Source Language SSOT: Trust AI Enrichment JSON source_lang first; fallback to original title only (exclude description to avoid RSS locale '[댓글]' pollution)
      const aiLang = (p.ai_enrichment?.source_lang || '').toUpperCase();
      let detectedLang = ['KO', 'EN', 'ZH', 'JA'].includes(aiLang) ? aiLang : '';
      if (!detectedLang) {
        const origTitle = r.title || '';
        const rPlat = (r.source_platform || '').toLowerCase();
        const rUrl = (r.source_url || '').toLowerCase();
        if (/[\uac00-\ud7a3]/.test(origTitle) || /daum|geeknews|hada\.io|chosun|donga|yonhap|naver/i.test(rPlat) || /daum\.net|hada\.io|naver\.com/i.test(rUrl)) {
          detectedLang = 'KO';
        } else if (/[\u3040-\u30ff]/.test(origTitle)) {
          detectedLang = 'JA';
        } else if (/[\u4e00-\u9fff]/.test(origTitle) || /weibo|zhihu|36kr|ithome|sspai|bilibili|wechat|qq\.com|sina|baidu|jiqizhixin|qbitai|v2ex|geekpark|oschina|infoq/i.test(rPlat) || /\.cn|\.com\.cn|weibo\.com|zhihu\.com|36kr\.com|ithome\.com|sspai\.com|bilibili\.com|v2ex\.com/i.test(rUrl)) {
          detectedLang = 'ZH';
        } else {
          detectedLang = 'EN';
        }
      }

      let aiEnrichment = null;
      if (p.ai_enrichment) {
        aiEnrichment = {
          id: p.ai_enrichment.id || r.inbox_id,
          hook: p.ai_enrichment.hook || p.hook || '',
          source_lang: detectedLang,
          artifact_type: p.ai_enrichment.artifact_type || p.artifact_type || '',
          type_classification: p.ai_enrichment.type_classification || p.category_type || 'TECH',
          key_takeaways: keyTakeaways,
          summary_ko: p.ai_enrichment.summary_ko || '',
          enriched_at: p.ai_enrichment.enriched_at || r.updated_at || r.harvested_date,
          enriched_by_model: p.ai_enrichment.enriched_by_model || 'inclusionai/ling-3.0-flash-sante:free'
        };
      } else if (keyTakeaways.length > 0) {
        aiEnrichment = {
          key_takeaways: keyTakeaways,
          summary_ko: '',
          enriched_at: r.updated_at || r.harvested_date,
          enriched_by_model: 'inclusionai/ling-3.0-flash-sante:free'
        };
      }

      // 🌟 Earliest Harvested / First Spotted SSOT
      const dateCandidates = [];
      if (r.harvested_date) dateCandidates.push(new Date(r.harvested_date).getTime());
      if (r.created_at) dateCandidates.push(new Date(r.created_at).getTime());
      if (p.initial_harvested_date || p.earliest_harvested_date) {
        dateCandidates.push(new Date(p.initial_harvested_date || p.earliest_harvested_date).getTime());
      }
      if (Array.isArray(p.sources)) {
        p.sources.forEach(s => {
          if (s.harvested_date || s.created_at || s.captured_at) {
            dateCandidates.push(new Date(s.harvested_date || s.created_at || s.captured_at).getTime());
          }
        });
      }
      if (Array.isArray(p.cross_posts)) {
        p.cross_posts.forEach(cp => {
          if (cp.captured_at || cp.harvested_date || cp.created_at) {
            dateCandidates.push(new Date(cp.captured_at || cp.harvested_date || cp.created_at).getTime());
          }
        });
      }
      const validDates = dateCandidates.filter(t => !isNaN(t) && t > 0);
      const earliestTimestamp = validDates.length > 0 ? Math.min(...validDates) : (r.created_at ? new Date(r.created_at).getTime() : Date.now());
      const earliestHarvestedAt = new Date(earliestTimestamp).toISOString();

      // 🌟 Cross-Spike Breakdown (Press vs Community)
      const allSourcesList = Array.isArray(p.sources) ? [...p.sources] : [];
      if (r.source_platform && !allSourcesList.some(s => (s.url || s.source_url) === r.source_url)) {
        allSourcesList.unshift({
          platform: r.source_platform,
          source_name: r.source_platform,
          url: r.source_url,
          title: r.title
        });
      }
      let pressCount = 0;
      let communityCount = 0;
      const pressKeywords = ['press', 'news', 'bbc', 'cbc', 'reuters', 'bloomberg', 'theverge', 'the verge', 'techcrunch', 'guardian', 'hill', 'fortune', 'ktvn', 'times', 'wsj', 'cnn', 'cbs', 'abc', 'wired', 'axios', 'npr', 'time'];
      const communityKeywords = ['hacker news', 'ycombinator', 'reddit', 'geeknews', 'hada.io', 'pytorch', 'github', 'huggingface', 'spaces', 'arxiv', 'youtube', 'twitter', 'x.com'];
      
      const seenSourceKeys = new Set();
      allSourcesList.forEach(s => {
        const plat = (s.platform || s.source_name || '').toLowerCase();
        const u = (s.url || s.source_url || '').toLowerCase();
        const key = plat + '::' + u;
        if (seenSourceKeys.has(key)) return;
        seenSourceKeys.add(key);

        const isComm = communityKeywords.some(k => plat.includes(k) || u.includes(k));
        const isPrs = pressKeywords.some(k => plat.includes(k) || u.includes(k));
        if (isComm) {
          communityCount++;
        } else if (isPrs) {
          pressCount++;
        } else {
          pressCount++;
        }
      });

      const totalSourcesCount = Math.max(seenSourceKeys.size, allSourcesList.length);
      const histSnap = histMap.get(Number(r.id));
      const isCrossSpiking = Boolean(histSnap || p.is_cross_spiking || (pressCount >= 1 && communityCount >= 1 && totalSourcesCount >= 2));

      let activeSpikeAnalysis = p.spike_analysis || null;
      if (histSnap) {
        activeSpikeAnalysis = {
          ...(p.spike_analysis || {}),
          score: Number(histSnap.spike_score),
          raw_score: Number(histSnap.raw_spike_score),
          tier: histSnap.spike_tier,
          axes_count: Number(histSnap.axes_count),
          sources_count: Number(histSnap.sources_count),
          press_count: Number(histSnap.press_count),
          community_count: Number(histSnap.community_count),
          code_count: Number(histSnap.code_count),
          velocity: Number(histSnap.velocity),
          depth: Number(histSnap.depth),
          ranking_date: histSnap.ranking_date,
          daily_rank: Number(histSnap.rank_position)
        };
      }

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
        source_lang: detectedLang,
        category_primary: r.category_primary,
        tier1_category: p.tier1_category || 'TECH_COMPUTING',
        tier2_category: p.tier2_category || r.category_primary || 'INDUSTRY_TRENDS',
        facet_type: p.facet_type || 'NEWS',
        is_model: p.is_model !== undefined ? p.is_model : (p.facet_type === 'MODEL'),
        model_family: p.model_family || '',
        artifact_type: p.artifact_type || '',
        sources: p.sources || [],
        cross_posts: p.cross_posts || [],
        is_cross_spiking: isCrossSpiking,
        spike_analysis: activeSpikeAnalysis,
        spike_history: spikeHistoryMap.get(Number(r.id)) || [],
        live_spike_score: r.live_spike_score !== null && r.live_spike_score !== undefined ? Number(r.live_spike_score) : (p.spike_analysis?.score || 0),
        peak_spike_score: r.peak_spike_score !== null && r.peak_spike_score !== undefined ? Number(r.peak_spike_score) : (p.spike_analysis?.peak_score || 0),
        peak_spike_date: r.peak_spike_date || p.spike_analysis?.peak_date || null,
        best_spike_rank: r.best_spike_rank !== null && r.best_spike_rank !== undefined ? Number(r.best_spike_rank) : (p.spike_analysis?.best_rank || null),
        daily_spike_rank: histSnap ? Number(histSnap.rank_position) : null,
        spike_ranking_date: histSnap ? histSnap.ranking_date : null,
        cross_spike_summary: {
          total_count: totalSourcesCount,
          press_count: pressCount,
          community_count: communityCount,
          is_cross_spiking: isCrossSpiking
        },
        metric_tracking: p.metric_tracking || {},
        viral_metric: r.viral_metric || p.viral_metric || '',
        viral_score: r.viral_score !== null ? Number(r.viral_score) : (p.viral_score || 0),
        is_classified: r.is_classified,
        harvested_date: r.harvested_date,
        initial_harvested_at: earliestHarvestedAt,
        earliest_harvested_at: earliestHarvestedAt,
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
      spike_date: isValidSpikeDate ? spikeDate : null,
      items: items
    };

    setCachedResponse(cacheKey, responsePayload);

    return res.status(200).json(responsePayload);
  } catch (err) {
    console.error('[API Inbox Error]:', err.message || err);
    const fallback = getStaticInboxFallback(req);
    if (fallback) {
      return res.status(200).json(fallback);
    }
    return res.status(200).json({
      status: 'success',
      source: 'empty_fallback',
      page: 1,
      limit: 15,
      total: 0,
      total_pages: 1,
      items: [],
      news: []
    });
  }
};

