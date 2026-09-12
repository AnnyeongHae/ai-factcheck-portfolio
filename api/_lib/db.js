// api/_lib/db.js - Singleton PostgreSQL Connection Pool
const { Pool } = require('pg');

let cachedPool = null;

function getDbPool() {
  const DATABASE_URL = process.env.DATABASE_URL || process.env.NEON_KEY || process.env.NEON_DATABASE_URL;
  if (!DATABASE_URL) {
    return null;
  }

  if (!cachedPool) {
    try {
      cachedPool = new Pool({
        connectionString: DATABASE_URL,
        ssl: { rejectUnauthorized: true },
        max: 5,
        idleTimeoutMillis: 15000,
        connectionTimeoutMillis: 5000
      });

      cachedPool.on('error', (err) => {
        console.error('[PgPool Shared Error]:', err.message);
        cachedPool = null;
      });
    } catch (e) {
      console.error('[Pg Driver Error in _lib/db]:', e.message);
      return null;
    }
  }

  return cachedPool;
}

module.exports = { getDbPool };
