module.exports = async (req, res) => {
  // CORS Headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(204).end();
  }

  const DATABASE_URL = process.env.DATABASE_URL || process.env.NEON_KEY;

  if (!DATABASE_URL) {
    return res.status(200).json({
      success: false,
      error: "DATABASE_URL is not configured in Environment Variables."
    });
  }

  let dbClient;
  try {
    const { Pool } = require('pg');
    dbClient = new Pool({
      connectionString: DATABASE_URL,
      ssl: { rejectUnauthorized: false }
    });
  } catch (modErr) {
    return res.status(200).json({
      success: false,
      error: "Postgres driver initialization warning: " + modErr.message
    });
  }

  try {
    if (req.method === 'GET') {
      const urlObj = new URL(req.url, 'http://localhost:3000');
      const fetchAll = urlObj.searchParams.get('all') === 'true';
      const fetchNews = urlObj.searchParams.get('type') === 'NEWS';

      if (fetchNews) {
        const newsResult = await dbClient.query(`
          SELECT 
            inbox_id, 
            title, 
            COALESCE(raw_payload->>'title_ko', title) as title_ko,
            COALESCE(raw_payload->>'title_en', title) as title_en,
            COALESCE(raw_payload->>'title_zh', title) as title_zh,
            description, 
            COALESCE(raw_payload->>'description_ko', description) as description_ko,
            COALESCE(raw_payload->>'description_en', description) as description_en,
            COALESCE(raw_payload->>'description_zh', description) as description_zh,
            source_platform, 
            source_url, 
            viral_metric, 
            harvested_date, 
            COALESCE(raw_payload->'ai_enrichment', null) as ai_enrichment,
            COALESCE(raw_payload->'multilingual', null) as multilingual,
            COALESCE(raw_payload->>'source_lang', 'EN') as source_lang,
            COALESCE(raw_payload->>'programming_lang', 'General') as programming_lang,
            COALESCE(raw_payload->>'hook', null) as hook,
            COALESCE(raw_payload->'related_dossier', null) as related_dossier,
            'NEWS' as category_type
          FROM raw_trends_inbox
          WHERE item_type = 'news' OR source_platform IN ('Hacker News', 'Reddit', 'AI News Feed')
          ORDER BY harvested_date DESC, created_at DESC;
        `);
        return res.status(200).json({
          success: true,
          source: "neon_database_live",
          total_count: newsResult.rows.length,
          news: newsResult.rows
        });
      }

      if (fetchAll) {
        const allResult = await dbClient.query(`
          SELECT 
            inbox_id, 
            title, 
            COALESCE(raw_payload->>'title_ko', title) as title_ko,
            COALESCE(raw_payload->>'title_en', title) as title_en,
            COALESCE(raw_payload->>'title_zh', title) as title_zh,
            description, 
            COALESCE(raw_payload->>'description_ko', description) as description_ko,
            COALESCE(raw_payload->>'description_en', description) as description_en,
            COALESCE(raw_payload->>'description_zh', description) as description_zh,
            source_platform, 
            source_url, 
            COALESCE(raw_payload->>'creator', 'Community') as creator,
            COALESCE(raw_payload->>'model_family', 'Standalone / General') as model_family,
            COALESCE(raw_payload->>'variant_role', 'Standard') as variant_role,
            COALESCE(raw_payload->'detected_formats', '[]'::jsonb) as detected_formats,
            COALESCE(raw_payload->'audit_risk', '{"hype_risk_score": 15, "risk_level": "LOW_RISK"}'::jsonb) as audit_risk,
            COALESCE(raw_payload->'ai_enrichment', null) as ai_enrichment,
            COALESCE(raw_payload->'multilingual', null) as multilingual,
            COALESCE(raw_payload->'metric_tracking', null) as metric_tracking,
            COALESCE(raw_payload->>'source_lang', 'EN') as source_lang,
            COALESCE(raw_payload->>'programming_lang', 'General') as programming_lang,
            COALESCE(raw_payload->>'hook', null) as hook,
            COALESCE(raw_payload->>'hook_ko', null) as hook_ko,
            COALESCE(raw_payload->>'hook_en', null) as hook_en,
            COALESCE(raw_payload->>'hook_zh', null) as hook_zh,
            COALESCE(raw_payload->'related_dossier', null) as related_dossier,
            triage_status as status, 
            harvested_date, 
            COALESCE(raw_payload->>'category_type', item_type) as category_type
          FROM raw_trends_inbox
          ORDER BY harvested_date DESC, created_at DESC;
        `);
        return res.status(200).json({
          success: true,
          source: "neon_database_live",
          total_count: allResult.rows.length,
          items: allResult.rows
        });
      }

      const result = await dbClient.query(`
        SELECT 
          inbox_id, 
          title, 
          COALESCE(raw_payload->>'title_ko', title) as title_ko,
          source_platform, 
          COALESCE(raw_payload->>'model_family', 'General') as model_family,
          COALESCE(raw_payload->>'variant_role', 'Standard') as variant_role,
          triage_status as status, 
          harvested_date 
        FROM raw_trends_inbox 
        WHERE triage_status = 'QUEUED_FOR_INVESTIGATION' 
        ORDER BY harvested_date DESC, created_at DESC;
      `);

      return res.status(200).json({
        success: true,
        source: "neon_database_live",
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
        const check = await dbClient.query('SELECT triage_status FROM raw_trends_inbox WHERE inbox_id = $1;', [inbox_ids[0]]);
        if (check.rows.length > 0 && check.rows[0].triage_status === 'QUEUED_FOR_INVESTIGATION') {
          updatedStatus = "PENDING_REVIEW";
        } else {
          updatedStatus = "QUEUED_FOR_INVESTIGATION";
        }
      }

      for (const targetId of inbox_ids) {
        await dbClient.query(`
          UPDATE raw_trends_inbox 
          SET triage_status = $1, updated_at = CURRENT_TIMESTAMP 
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
    console.error("Neon DB queue error:", err);
    return res.status(200).json({
      success: false,
      error: "Neon Database Error: " + (err.message || String(err))
    });
  }
};
