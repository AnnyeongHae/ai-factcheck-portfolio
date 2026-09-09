let cachedPool = null;

function getDbPool() {
  const DATABASE_URL = process.env.DATABASE_URL || process.env.NEON_KEY || process.env.NEON_DATABASE_URL;
  if (!DATABASE_URL) return null;
  if (!cachedPool) {
    try {
      const { Pool } = require('pg');
      cachedPool = new Pool({
        connectionString: DATABASE_URL,
        ssl: { rejectUnauthorized: true },
        max: 3,
        idleTimeoutMillis: 30000,
        connectionTimeoutMillis: 5000
      });
      cachedPool.on('error', (err) => {
        console.error('[PgPool Error in health]:', err);
        cachedPool = null;
      });
    } catch (e) {
      console.error('[Pg Driver Error]:', e);
      return null;
    }
  }
  return cachedPool;
}

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(204).end();
  }

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
      console.error('[Health Check DB Query Error]:', e);
      dbStatus = "ERROR: " + (e.message || "Database query failed");
    }
  }

  return res.status(200).json({
    service: "AI Tech-Lineage Fact-Check Hub (Vercel Serverless Node.js Backend)",
    version: "v20.0",
    neon_postgres_status: dbStatus,
    database_url_present: Boolean(pool),
    metrics: counts
  });
};

