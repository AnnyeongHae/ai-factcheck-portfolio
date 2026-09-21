const { getDbPool, getDbProviderInfo } = require('./_lib/db');
const { handleOptions, setCorsHeaders } = require('./_lib/cors');

module.exports = async (req, res) => {
  if (handleOptions(req, res, 'GET, OPTIONS')) return;
  setCorsHeaders(res, 'GET, OPTIONS');

  const pool = getDbPool();
  const providerInfo = getDbProviderInfo();
  let dbStatus = pool ? "INITIALIZING" : "NOT_CONFIGURED";
  let counts = {};
  let pgVersion = null;

  if (pool) {
    try {
      const [c1, c2, c3, vRes] = await Promise.all([
        pool.query("SELECT COUNT(*) FROM verified_factchecks;"),
        pool.query("SELECT COUNT(*) FROM raw_trends_inbox;"),
        pool.query("SELECT COUNT(*) FROM raw_trends_inbox WHERE triage_status = 'QUEUED_FOR_INVESTIGATION';"),
        pool.query("SELECT version();")
      ]);
      counts["verified_factchecks"] = parseInt(c1.rows[0].count, 10);
      counts["raw_trends_inbox"] = parseInt(c2.rows[0].count, 10);
      counts["queued_for_investigation"] = parseInt(c3.rows[0].count, 10);
      pgVersion = vRes.rows[0]?.version || '';
      dbStatus = "CONNECTED_HEALTHY";
    } catch (e) {
      console.error('[Health Check DB Query Error]:', e.message);
      dbStatus = "UNHEALTHY";
    }
  }

  return res.status(200).json({
    service: "AI Tech-Lineage Fact-Check Hub (Vercel Serverless Node.js Backend)",
    version: "v21.1",
    database_status: dbStatus,
    database_provider: providerInfo.provider,
    database_host: providerInfo.host,
    database_version: pgVersion,
    neon_postgres_status: dbStatus, // Legacy alias for backward compatibility
    database_url_present: Boolean(pool),
    metrics: counts
  });
};


