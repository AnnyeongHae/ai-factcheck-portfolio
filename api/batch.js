const fs = require('fs');
const path = require('path');

let cachedPool = null;

function getDbPool() {
  const DATABASE_URL = process.env.DATABASE_URL || process.env.NEON_KEY;
  if (!DATABASE_URL) return null;
  if (!cachedPool) {
    try {
      const { Pool } = require('pg');
      cachedPool = new Pool({
        connectionString: DATABASE_URL,
        ssl: { rejectUnauthorized: false },
        max: 5,
        idleTimeoutMillis: 30000,
        connectionTimeoutMillis: 5000
      });
    } catch (e) {
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

  // 1. Try fetching from Neon DB
  const pool = getDbPool();
  if (pool) {
    try {
      const result = await pool.query(`
        SELECT batch_uuid, gemini_job_name, item_count, status, token_usage, submitted_at, completed_at
        FROM ai_batch_jobs
        ORDER BY submitted_at DESC
        LIMIT 20;
      `);
      return res.status(200).json({
        success: true,
        source: "neon_database_live",
        total_batches: result.rows.length,
        batches: result.rows
      });
    } catch (dbe) {
      console.warn("DB batch query fallback:", dbe.message);
    }
  }

  // 2. Fallback to local logs/batch_jobs.json
  try {
    const logPath = path.join(process.cwd(), 'logs', 'batch_jobs.json');
    if (fs.existsSync(logPath)) {
      const logData = JSON.parse(fs.readFileSync(logPath, 'utf8'));
      return res.status(200).json({
        success: true,
        source: "local_log_fallback",
        total_batches: logData.length,
        batches: logData
      });
    }
  } catch (e) {}

  return res.status(200).json({
    success: true,
    source: "empty_registry",
    total_batches: 0,
    batches: []
  });
};
