module.exports = async (req, res) => {
  // CORS Headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(204).end();
  }

  const DATABASE_URL = process.env.DATABASE_URL || process.env.NEON_KEY;

  if (!DATABASE_URL) {
    return res.status(200).json({
      success: false,
      source: "fallback_static",
      error: "DATABASE_URL or NEON_KEY is not configured."
    });
  }

  let dbClient;
  try {
    const { Pool } = require('pg');
    dbClient = new Pool({
      connectionString: DATABASE_URL,
      ssl: { rejectUnauthorized: false }
    });
  } catch (modErr) {
    return res.status(200).json({
      success: false,
      source: "fallback_static",
      error: "Postgres driver initialization warning: " + modErr.message
    });
  }

  try {
    // 1. Fetch Verified Factchecks from Neon DB Tier 2 Knowledge Core
    const factcheckRows = await dbClient.query(`
      SELECT 
        vf.case_id, 
        vf.title, 
        vf.category, 
        COALESCE(SUBSTRING(vf.case_id FROM 1 FOR 10), vf.created_at::date::text) as investigation_date,
        vf.verdict, 
        vf.confidence_score, 
        vf.discovery_mode, 
        vf.curator_name, 
        vf.personal_motivation, 
        vf.target_workflow,
        vf.cluster_id, 
        vf.cluster_name,
        vf.hands_on_status, 
        vf.hands_on_pipeline, 
        vf.hands_on_env, 
        vf.hands_on_metrics, 
        vf.hands_on_details,
        vf.the_hook, 
        vf.marketing_hype_anatomy, 
        vf.engineering_takeaways, 
        vf.future_applications, 
        vf.sources,
        vf.created_at
      FROM verified_factchecks vf
      ORDER BY vf.created_at DESC;
    `);

    // 2. Fetch Alternatives and Community Signals in parallel
    const altRows = await dbClient.query(`SELECT case_id, tool_name as name, tech_stack, pros, cons, best_for FROM factcheck_alternatives;`);
    const commRows = await dbClient.query(`SELECT case_id, platform, author_type, quote, source_url as url, signal_type FROM factcheck_community_signals;`);
    
    let claimsRows = { rows: [] };
    try {
      claimsRows = await dbClient.query(`SELECT case_id, claim_id, statement, fact_checked_truth, status FROM factcheck_atomic_claims;`);
    } catch (cErr) {}

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

    // Assemble complete Portfolios JSON
    const portfolios = factcheckRows.rows.map(r => {
      let sources = [];
      try {
        sources = typeof r.sources === 'string' ? JSON.parse(r.sources) : (r.sources || []);
      } catch (e) {
        sources = [];
      }

      return {
        case_id: r.case_id,
        title: r.title,
        category: r.category,
        investigation_date: typeof r.investigation_date === 'string' ? r.investigation_date : (r.investigation_date ? r.investigation_date.toISOString().split('T')[0] : '2026-09-01'),
        verdict: r.verdict,
        confidence_score: parseFloat(r.confidence_score) || 95.0,
        curation: {
          discovery_mode: r.discovery_mode,
          curator: r.curator_name,
          personal_motivation: r.personal_motivation,
          target_workflow: r.target_workflow
        },
        clustering: {
          cluster_id: r.cluster_id,
          cluster_name: r.cluster_name,
          alternatives: altsByCase[r.case_id] || []
        },
        sources: sources,
        community_reactions: commByCase[r.case_id] || [],
        claims_assessment: claimsByCase[r.case_id] || [],
        portfolio_story: {
          the_hook: r.the_hook,
          marketing_hype_anatomy: r.marketing_hype_anatomy,
          engineering_takeaways: r.engineering_takeaways,
          future_applications: r.future_applications,
          hands_on_log: {
            status: r.hands_on_status,
            pipeline_or_url: r.hands_on_pipeline,
            test_environment: r.hands_on_env,
            measured_results: r.hands_on_metrics,
            details: r.hands_on_details
          }
        },
        created_at: r.created_at
      };
    });

    // 3. Fetch Technical Ecosystem Analyses from Neon DB
    let analyses = [];
    try {
      const anaResult = await dbClient.query(`
        SELECT 
          analysis_key, 
          title, 
          base_standard, 
          third_party_ecosystem, 
          core_philosophy_comparison, 
          domain_lineage_matrix, 
          performance_bottlenecks, 
          engineering_tradeoffs,
          created_at
        FROM ecosystem_technical_analyses
        ORDER BY created_at DESC;
      `);
      analyses = anaResult.rows;
    } catch (anaErr) {
      console.warn("ecosystem_technical_analyses query warning:", anaErr.message);
    }

    return res.status(200).json({
      success: true,
      source: "neon_database_live",
      total_count: portfolios.length,
      portfolios: portfolios,
      technical_analyses: analyses,
      server_timestamp: new Date().toISOString()
    });

  } catch (err) {
    console.error("Neon DB query error:", err);
    return res.status(200).json({
      success: false,
      source: "fallback_static",
      error: "Neon Database Query Error: " + (err.message || String(err))
    });
  }
};
