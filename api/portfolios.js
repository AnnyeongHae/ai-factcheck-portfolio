const { getDbPool } = require('./_lib/db');
const { handleOptions, setCorsHeaders } = require('./_lib/cors');

function getStaticFallback() {
  try {
    const fs = require('fs');
    const path = require('path');
    const candidatePaths = [
      path.join(process.cwd(), 'public', 'data.json'),
      path.join(process.cwd(), 'docs', 'data.json'),
      path.join(__dirname, '..', 'public', 'data.json'),
      path.join(__dirname, '..', 'docs', 'data.json')
    ];
    for (const p of candidatePaths) {
      if (fs.existsSync(p)) {
        const d = JSON.parse(fs.readFileSync(p, 'utf8'));
        if (d && d.cases) {
          return {
            success: true,
            source: 'static_filesystem_fallback',
            portfolios: d.cases,
            technical_analyses: d.technical_analyses || []
          };
        }
      }
    }
  } catch (e) {}
  return null;
}

module.exports = async (req, res) => {
  if (handleOptions(req, res, 'GET, OPTIONS')) return;
  setCorsHeaders(res, 'GET, OPTIONS');

  // 🌟 High-Performance Edge SWR Cache Headers
  // s-maxage=600: Edge CDN caches for 10 minutes (0.05s response to 99% users)
  // stale-while-revalidate=86400: Serves stale cache instantly while revalidating in background for 24h
  res.setHeader('Cache-Control', 'public, s-maxage=600, stale-while-revalidate=86400');

  const pool = getDbPool();
  if (!pool) {
    const fallback = getStaticFallback();
    if (fallback) return res.status(200).json(fallback);
    return res.status(200).json({
      success: false,
      source: 'fallback_static',
      error: 'DATABASE_URL is not configured and static fallback unavailable.'
    });
  }

  // Query parameters for modern DB-First pagination & chunking
  const queryParams = req.query || {};
  const caseIdParam = queryParams.case_id || queryParams.id;
  const categoryParam = queryParams.category;
  const page = Math.max(1, parseInt(queryParams.page, 10) || 1);
  const limit = Math.max(0, parseInt(queryParams.limit, 10) || 0);
  const summaryOnly = queryParams.summary === 'true' || queryParams.summary === '1';

  try {
    // 1. Build Factchecks Query
    let sql = 
      "SELECT " +
        "vf.case_id, " +
        "vf.title, " +
        "vf.category, " +
        "vf.created_at, " +
        "vf.verdict, " +
        "vf.confidence_score, " +
        "vf.discovery_mode, " +
        "vf.curator_name, " +
        "vf.personal_motivation, " +
        "vf.target_workflow, " +
        "vf.cluster_id, " +
        "vf.cluster_name, " +
        "vf.hands_on_status, " +
        "vf.hands_on_pipeline, " +
        "vf.hands_on_env, " +
        "vf.hands_on_metrics, " +
        "vf.hands_on_details, " +
        "vf.the_hook, " +
        "vf.marketing_hype_anatomy, " +
        "vf.engineering_takeaways, " +
        "vf.future_applications, " +
        "vf.sources " +
      "FROM verified_factchecks vf ";

    const values = [];
    const whereClauses = [];

    if (caseIdParam) {
      values.push(caseIdParam);
      whereClauses.push(`vf.case_id = $${values.length}`);
    } else if (categoryParam) {
      values.push(categoryParam);
      whereClauses.push(`vf.category = $${values.length}`);
    }

    if (whereClauses.length > 0) {
      sql += "WHERE " + whereClauses.join(" AND ") + " ";
    }

    sql += "ORDER BY vf.created_at DESC;";

    const factcheckRows = await pool.query(sql, values);
    const totalCount = factcheckRows.rows.length;

    // Apply pagination if limit is specified
    let targetRows = factcheckRows.rows;
    if (limit > 0 && !caseIdParam) {
      const offset = (page - 1) * limit;
      targetRows = targetRows.slice(offset, offset + limit);
    }

    const caseIds = targetRows.map(r => r.case_id);

    // 2. Fetch relations in parallel with case_id filtering
    let altRows = { rows: [] };
    let commRows = { rows: [] };
    let claimsRows = { rows: [] };

    if (caseIds.length > 0) {
      const [alts, comms, claims] = await Promise.all([
        pool.query("SELECT case_id, tool_name as name, tech_stack, pros, cons, best_for FROM factcheck_alternatives WHERE case_id = ANY($1);", [caseIds]).catch(() => ({ rows: [] })),
        pool.query("SELECT case_id, platform, author_type, quote, source_url as url, signal_type FROM factcheck_community_signals WHERE case_id = ANY($1);", [caseIds]).catch(() => ({ rows: [] })),
        pool.query("SELECT case_id, claim_number as claim_id, claim_title, claim_text as statement, claim_text as claim, claim_verdict as status, claim_verdict as verdict, verification_evidence as fact_checked_truth, verification_evidence as reality FROM factcheck_atomic_claims WHERE case_id = ANY($1) ORDER BY case_id, claim_number;", [caseIds]).catch(() => ({ rows: [] }))
      ]);
      altRows = alts;
      commRows = comms;
      claimsRows = claims;
    }

    // Group relations by case_id
    const altsByCase = {};
    altRows.rows.forEach(r => {
      if (!altsByCase[r.case_id]) altsByCase[r.case_id] = [];
      altsByCase[r.case_id].push(r);
    });

    const commByCase = {};
    commRows.rows.forEach(r => {
      if (!commByCase[r.case_id]) commByCase[r.case_id] = [];
      commByCase[r.case_id].push(r);
    });

    const claimsByCase = {};
    claimsRows.rows.forEach(r => {
      if (!claimsByCase[r.case_id]) claimsByCase[r.case_id] = [];
      claimsByCase[r.case_id].push(r);
    });

    function extractValidDate(caseId, createdAtFallback) {
      if (caseId) {
        const match = String(caseId).match(/(\d{4})[-_](\d{2})[-_](\d{2})/);
        if (match) return match[1] + '-' + match[2] + '-' + match[3];
      }
      if (createdAtFallback) {
        try {
          const d = new Date(createdAtFallback);
          if (!isNaN(d.getTime())) return d.toISOString().split('T')[0];
        } catch (e) {}
      }
      return '2026-03-01';
    }

    const dossiers = targetRows.map(row => {
      const caseDate = extractValidDate(row.case_id, row.created_at);
      let parsedSources = row.sources;
      if (typeof parsedSources === 'string') {
        try { parsedSources = JSON.parse(parsedSources); } catch (e) { parsedSources = []; }
      }
      if (!Array.isArray(parsedSources)) parsedSources = [];

      const metricsStr = typeof row.hands_on_metrics === 'string' 
        ? row.hands_on_metrics 
        : (row.hands_on_metrics && Object.keys(row.hands_on_metrics).length > 0 ? Object.entries(row.hands_on_metrics).map(([k, v]) => `${k}: ${v}`).join(' | ') : '');

      const baseItem = {
        case_id: row.case_id,
        title: row.title,
        category: row.category,
        investigation_date: caseDate,
        source_published_date: caseDate,
        verdict: row.verdict,
        confidence_score: row.confidence_score,
        curation: {
          discovery_mode: row.discovery_mode || 'USER_CURATED',
          curator: row.curator_name || 'FactCheck AI Lab',
          personal_motivation: row.personal_motivation || '',
          target_workflow: row.target_workflow || ''
        },
        clustering: {
          cluster_id: row.cluster_id || 'general',
          cluster_name: row.cluster_name || 'General AI',
          alternatives: altsByCase[row.case_id] || []
        },
        portfolio_story: {
          the_hook: row.the_hook || '',
          marketing_hype_anatomy: row.marketing_hype_anatomy || '',
          engineering_takeaways: row.engineering_takeaways || '',
          future_applications: row.future_applications || '',
          hands_on_log: {
            status: row.hands_on_status || 'verified',
            pipeline_or_url: row.hands_on_pipeline || '',
            test_environment: row.hands_on_env || '',
            measured_results: metricsStr,
            details: summaryOnly ? '' : (row.hands_on_details || '')
          }
        },
        hands_on_review: {
          status: row.hands_on_status || 'verified',
          pipeline: row.hands_on_pipeline || '',
          environment: row.hands_on_env || '',
          empirical_metrics: row.hands_on_metrics || {},
          details: summaryOnly ? '' : (row.hands_on_details || '')
        },
        raw_viral_post: (commByCase[row.case_id] && commByCase[row.case_id].length > 0) ? {
          platform: commByCase[row.case_id][0].platform || 'Social Post',
          author: commByCase[row.case_id][0].author_type || '',
          quote: commByCase[row.case_id][0].quote || '',
          post_url: commByCase[row.case_id][0].url || ''
        } : null,
        sources: summaryOnly ? [] : parsedSources,
        claims_assessment: claimsByCase[row.case_id] || [],
        alternatives: altsByCase[row.case_id] || [],
        community_signals: commByCase[row.case_id] || []
      };

      return baseItem;
    });

    // If single case requested, return directly
    if (caseIdParam && dossiers.length > 0) {
      return res.status(200).json({
        success: true,
        source: 'neon_postgres_direct',
        case: dossiers[0]
      });
    }

    // Fetch technical analyses if present (only when on page 1 or full list)
    let techAnalyses = [];
    if (page === 1) {
      try {
        const tRes = await pool.query('SELECT payload FROM ecosystem_technical_analyses ORDER BY id DESC LIMIT 50;');
        techAnalyses = tRes.rows.map(r => {
          let p = r.payload;
          if (typeof p === 'string') {
            try { p = JSON.parse(p); } catch (e) { p = {}; }
          }
          return p;
        });
      } catch (tErr) {}
    }

    return res.status(200).json({
      success: true,
      source: 'neon_postgres_direct',
      total_count: totalCount,
      count: dossiers.length,
      page: limit > 0 ? page : 1,
      total_pages: limit > 0 ? Math.ceil(totalCount / limit) : 1,
      limit: limit > 0 ? limit : totalCount,
      portfolios: dossiers,
      technical_analyses: techAnalyses
    });

  } catch (err) {
    console.error('[API Portfolios Error]:', err);
    const fallback = getStaticFallback();
    if (fallback) return res.status(200).json(fallback);

    return res.status(500).json({
      success: false,
      error: 'Internal server error while fetching dossiers'
    });
  }
};
