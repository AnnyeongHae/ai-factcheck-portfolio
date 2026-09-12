const { getDbPool } = require('./_lib/db');
const { handleOptions, setCorsHeaders } = require('./_lib/cors');

module.exports = async (req, res) => {
  if (handleOptions(req, res, 'GET, OPTIONS')) return;
  setCorsHeaders(res, 'GET, OPTIONS');

  const pool = getDbPool();
  let dbStatus = pool ? "INITIALIZING" : "NOT_CONFIGURED";
  let counts = {};

  if (pool) {
    try {
      const c1 = await pool.query("SELECT COUNT(*) FROM verified_factchecks;");
      counts["verified_factchecks"] = parseInt(c1.rows[0].count, 10);
      const c2 = await pool.query("SELECT COUNT(*) FROM raw_trends_inbox;");
      counts["raw_trends_inbox"] = parseInt(c2.rows[0].count, 10);
      const c3 = await pool.query("SELECT COUNT(*) FROM raw_trends_inbox WHERE triage_status = 'QUEUED_FOR_INVESTIGATION';");
      counts["queued_for_investigation"] = parseInt(c3.rows[0].count, 10);
      dbStatus = "CONNECTED_HEALTHY";
    } catch (e) {
      console.error('[Health Check DB Query Error]:', e.message);
      dbStatus = "UNHEALTHY";
    }
  }

  return res.status(200).json({
    service: "AI Tech-Lineage Fact-Check Hub (Vercel Serverless Node.js Backend)",
    version: "v21.0",
    neon_postgres_status: dbStatus,
    database_url_present: Boolean(pool),
    metrics: counts
  });
};

