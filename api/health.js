module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(204).end();
  }

  const DATABASE_URL = process.env.DATABASE_URL;
  let dbStatus = "NOT_CONFIGURED";
  let counts = {};

  if (DATABASE_URL) {
    try {
      const { Pool } = require('pg');
      const pool = new Pool({
        connectionString: DATABASE_URL,
        ssl: { rejectUnauthorized: false }
      });
      const c1 = await pool.query("SELECT COUNT(*) FROM verified_portfolios;");
      counts["verified_portfolios"] = parseInt(c1.rows[0].count, 10);
      const c2 = await pool.query("SELECT COUNT(*) FROM inbox_candidates;");
      counts["inbox_candidates"] = parseInt(c2.rows[0].count, 10);
      const c3 = await pool.query("SELECT COUNT(*) FROM inbox_candidates WHERE status = 'QUEUED_FOR_INVESTIGATION';");
      counts["queued_for_investigation"] = parseInt(c3.rows[0].count, 10);
      await pool.end();
      dbStatus = "CONNECTED_HEALTHY";
    } catch (e) {
      dbStatus = "ERROR: " + e.message;
    }
  }

  return res.status(200).json({
    service: "AI Tech-Lineage Fact-Check Hub (Vercel Serverless Node.js Backend)",
    version: "v14.0",
    neon_postgres_status: dbStatus,
    database_url_present: Boolean(DATABASE_URL),
    metrics: counts
  });
};
