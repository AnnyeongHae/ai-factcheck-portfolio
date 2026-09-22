const { getDbPool, getDbProviderInfo } = require('./_lib/db');
const { handleOptions, setCorsHeaders } = require('./_lib/cors');

module.exports = async (req, res) => {
  if (handleOptions(req, res, 'GET, OPTIONS')) return;
  setCorsHeaders(res, 'GET, OPTIONS');

  const pool = getDbPool();
  const providerInfo = getDbProviderInfo();
  let dbStatus = pool ? "INITIALIZING" : (providerInfo.status === "FROZEN_BLOCKED" ? "NEON_FROZEN_AIVEN_REQUIRED" : "NOT_CONFIGURED");
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

  const responsePayload = {
    service: "AI Tech-Lineage Fact-Check Hub (Vercel Serverless Node.js Backend)",
    version: "v21.2",
    database_status: dbStatus,
    database_provider: providerInfo.provider,
    database_host: providerInfo.host,
    database_version: pgVersion,
    neon_postgres_status: providerInfo.provider === 'Aiven PostgreSQL' ? 'DECOMMISSIONED_IN_FAVOR_OF_AIVEN' : (providerInfo.status === 'FROZEN_BLOCKED' ? 'BLOCKED_FROZEN' : dbStatus),
    database_url_present: Boolean(pool),
    metrics: counts
  };

  if (providerInfo.instruction) {
    responsePayload.instruction = providerInfo.instruction;
  }

  return res.status(200).json(responsePayload);
};


