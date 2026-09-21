// api/_lib/db.js - Singleton PostgreSQL Connection Pool
const { Pool } = require('pg');
const { DATABASE_URL, POOL_CONFIG, getDbProviderInfo } = require('./config');

let cachedPool = null;

function getDbPool() {
  if (!DATABASE_URL) {
    return null;
  }

  if (!cachedPool) {
    try {
      let poolOptions = { ...POOL_CONFIG };
      try {
        const { parse } = require('pg-connection-string');
        const parsedConfig = parse(DATABASE_URL);
        poolOptions = {
          ...parsedConfig,
          ...POOL_CONFIG,
          ssl: { rejectUnauthorized: false }
        };
      } catch (pErr) {
        poolOptions.connectionString = DATABASE_URL;
      }

      cachedPool = new Pool(poolOptions);

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

module.exports = { getDbPool, getDbProviderInfo, DATABASE_URL };

