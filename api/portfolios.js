module.exports = async (req, res) => {
  // CORS Headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(204).end();
  }

  const DATABASE_URL = process.env.DATABASE_URL;

  if (!DATABASE_URL) {
    return res.status(200).json({
      success: false,
      source: "fallback_static",
      error: "DATABASE_URL is not configured in Vercel Environment Variables."
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
    // 1. Fetch Verified Portfolios from Neon DB
    const portResult = await dbClient.query(`
      SELECT 
        case_id, 
        title, 
        category, 
        investigation_date, 
        verdict, 
        confidence_score, 
        curation, 
        clustering, 
        sources, 
        community_reactions, 
        claims_assessment, 
        portfolio_story,
        created_at
      FROM verified_portfolios 
      ORDER BY investigation_date DESC, created_at DESC;
    `);

    // 2. Fetch Technical Ecosystem Analyses from Neon DB
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
      total_count: portResult.rows.length,
      portfolios: portResult.rows,
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
