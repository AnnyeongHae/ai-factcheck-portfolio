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
  res.setHeader('Cache-Control', 'public, s-maxage=60, stale-while-revalidate=120');

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

  try {
    // 1. Fetch Verified Factchecks
    const factcheckRows = await pool.query(
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
      "FROM verified_factchecks vf " +
      "ORDER BY vf.created_at DESC;"
    );

    const caseIds = factcheckRows.rows.map(r => r.case_id);

    // 2. Fetch relations in parallel with case_id filtering
    let altRows = { rows: [] };
    let commRows = { rows: [] };
    let claimsRows = { rows: [] };

    if (caseIds.length > 0) {
      const [alts, comms, claims] = await Promise.all([
        pool.query("SELECT case_id, tool_name as name, tech_stack, pros, cons, best_for FROM factcheck_alternatives WHERE case_id = ANY($1);", [caseIds]),
        pool.query("SELECT case_id, platform, author_type, quote, source_url as url, signal_type FROM factcheck_community_signals WHERE case_id = ANY($1);", [caseIds]),
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
        if (match) {
          return match[1] + '-' + match[2] + '-' + match[3];
        }
      }
      if (createdAtFallback) {
        try {
          const d = new Date(createdAtFallback);
          if (!isNaN(d.getTime())) {
            return d.toISOString().split('T')[0];
          }
        } catch (e) {}
      }
      return '2026-03-01';
    }

    const dossiers = factcheckRows.rows.map(row => {
      const caseDate = extractValidDate(row.case_id, row.created_at);
      let parsedSources = row.sources;
      if (typeof parsedSources === 'string') {
        try { parsedSources = JSON.parse(parsedSources); } catch (e) { parsedSources = []; }
      }
      if (!Array.isArray(parsedSources)) parsedSources = [];

      return {
        case_id: row.case_id,
        title: row.title,
        category: row.category,
        investigation_date: caseDate,
        source_published_date: caseDate,
        verdict: row.verdict,
        confidence_score: row.confidence_score,
        discovery_mode: row.discovery_mode,
        curator: {
          name: row.curator_name || 'AI FactCheck Lab',
          personal_motivation: row.personal_motivation || '',
          target_workflow: row.target_workflow || ''
        },
        cluster: {
          id: row.cluster_id || 'general',
          name: row.cluster_name || 'General AI'
        },
        hands_on_review: {
          status: row.hands_on_status || 'verified',
          pipeline: row.hands_on_pipeline || '',
          environment: row.hands_on_env || '',
          empirical_metrics: row.hands_on_metrics || {},
          details: row.hands_on_details || ''
        },
        debunking_narrative: {
          the_hook: row.the_hook || '',
          marketing_hype_anatomy: row.marketing_hype_anatomy || '',
          engineering_takeaways: row.engineering_takeaways || '',
          future_applications: row.future_applications || ''
        },
        sources: parsedSources,
        atomic_claims: claimsByCase[row.case_id] || [],
        alternatives: altsByCase[row.case_id] || [],
        community_signals: commByCase[row.case_id] || []
      };
    });

    // Fetch technical analyses if present
    let techAnalyses = [];
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

    return res.status(200).json({
      success: true,
      source: 'neon_postgres_direct',
      count: dossiers.length,
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
