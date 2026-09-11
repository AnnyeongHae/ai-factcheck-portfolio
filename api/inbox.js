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
        max: 5,
        idleTimeoutMillis: 30000,
        connectionTimeoutMillis: 5000
      });
      cachedPool.on('error', (err) => {
        console.error('[PgPool Error in inbox]:', err);
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
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.setHeader('Cache-Control', 'public, s-maxage=10, stale-while-revalidate=30');

  if (req.method === 'OPTIONS') {
    return res.status(204).end();
  }

  const pool = getDbPool();
  if (!pool) {
    return res.status(500).json({ status: 'error', message: 'Database connection not configured' });
  }

  try {
    const rawLimit = parseInt(req.query?.limit, 10);
    const limit = Number.isInteger(rawLimit) ? Math.min(100, Math.max(1, rawLimit)) : 30;

    const query = `
      SELECT id, inbox_id, source_platform, title, item_type, category_primary, is_classified, harvested_date, created_at, raw_payload
      FROM raw_trends_inbox
      ORDER BY id DESC
      LIMIT $1;
    `;
    const result = await pool.query(query, [limit]);

    const items = result.rows.map(r => {
      let p = r.raw_payload;
      if (typeof p === 'string') {
        try { p = JSON.parse(p); } catch (e) { p = {}; }
      }
      if (p && typeof p.description === 'string') {
        let d = p.description.trim();
        d = d.replace(/^HN\s*Score:\s*\d+\s*pts\s*(\|\s*Comments:\s*\d+\s*)?(\|\s*)?/i, '');
        d = d.replace(/^Abstract:\s*/i, '').trim();
        p.description = d;
      }
      return {
        id: r.id,
        inbox_id: r.inbox_id,
        source_platform: r.source_platform,
        title: r.title,
        item_type: r.item_type,
        category_primary: r.category_primary,
        is_classified: r.is_classified,
        harvested_date: r.harvested_date,
        created_at: r.created_at,
        ...p
      };
    });

    return res.status(200).json({
      status: 'success',
      count: items.length,
      items: items
    });
  } catch (err) {
    console.error('[API Inbox Error]:', err);
    return res.status(500).json({ status: 'error', message: 'Internal server error while fetching inbox items' });
  }
};

