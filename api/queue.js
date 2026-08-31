const { Pool } = require('pg');

const DATABASE_URL = process.env.DATABASE_URL;

let pool;
function getPool() {
  if (!pool && DATABASE_URL) {
    pool = new Pool({
      connectionString: DATABASE_URL,
      ssl: { rejectUnauthorized: false }
    });
  }
  return pool;
}

module.exports = async (req, res) => {
  // CORS Headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(204).end();
  }

  if (!DATABASE_URL) {
    return res.status(200).json({
      success: false,
      error: "DATABASE_URL environment variable is not configured in Vercel Settings -> Environment Variables.",
      hint: "Add DATABASE_URL in Vercel Dashboard to connect to Neon Postgres."
    });
  }

  const clientPool = getPool();

  try {
    if (req.method === 'GET') {
      const result = await clientPool.query(`
        SELECT inbox_id, title, title_ko, source_platform, model_family, variant_role, status, harvested_date 
        FROM inbox_candidates 
        WHERE status = 'QUEUED_FOR_INVESTIGATION' 
        ORDER BY harvested_date DESC, created_at DESC;
      `);

      return res.status(200).json({
        success: true,
        queued_count: result.rows.length,
        queued_items: result.rows
      });
    }

    if (req.method === 'POST') {
      const body = req.body || {};
      const action = body.action || 'toggle';
      const inbox_id = body.inbox_id;
      const inbox_ids = body.inbox_ids || (inbox_id ? [inbox_id] : []);

      if (inbox_ids.length === 0) {
        return res.status(400).json({ success: false, error: "No inbox_id provided" });
      }

      let updatedStatus = "QUEUED_FOR_INVESTIGATION";
      if (action === 'unqueue') {
        updatedStatus = "PENDING_REVIEW";
      } else if (action === 'toggle' && inbox_ids.length === 1) {
        const check = await clientPool.query('SELECT status FROM inbox_candidates WHERE inbox_id = $1;', [inbox_ids[0]]);
        if (check.rows.length > 0 && check.rows[0].status === 'QUEUED_FOR_INVESTIGATION') {
          updatedStatus = "PENDING_REVIEW";
        } else {
          updatedStatus = "QUEUED_FOR_INVESTIGATION";
        }
      }

      for (const targetId of inbox_ids) {
        await clientPool.query(`
          UPDATE inbox_candidates 
          SET status = $1, updated_at = CURRENT_TIMESTAMP 
          WHERE inbox_id = $2;
        `, [updatedStatus, targetId]);
      }

      return res.status(200).json({
        success: true,
        action,
        target_status: updatedStatus,
        affected_ids: inbox_ids,
        message: `Successfully updated ${inbox_ids.length} item(s) to '${updatedStatus}' in Neon DB.`
      });
    }

    return res.status(405).json({ error: "Method not allowed" });

  } catch (err) {
    console.error("Database error:", err);
    return res.status(500).json({
      success: false,
      error: err.message || "Database query failed"
    });
  }
};
