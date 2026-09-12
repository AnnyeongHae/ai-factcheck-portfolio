const { getDbPool } = require('./_lib/db');
const { handleOptions, setCorsHeaders } = require('./_lib/cors');

module.exports = async (req, res) => {
  if (handleOptions(req, res, 'GET, OPTIONS')) return;
  setCorsHeaders(res, 'GET, OPTIONS');
  res.setHeader('Cache-Control', 'public, s-maxage=10, stale-while-revalidate=30');

  const pool = getDbPool();
  if (!pool) {
    return res.status(500).json({ status: 'error', message: 'Database connection not configured' });
  }

  try {
    const rawLimit = parseInt(req.query?.limit, 10);
    const limit = Number.isInteger(rawLimit) ? Math.min(100, Math.max(1, rawLimit)) : 30;
    const rawOffset = parseInt(req.query?.offset, 10);
    const offset = Number.isInteger(rawOffset) ? Math.max(0, rawOffset) : 0;

    const itemType = req.query?.type;
    const isClassified = req.query?.classified;

    const conditions = [];
    const params = [];

    if (itemType) {
      params.push(itemType);
      conditions.push('item_type = $' + params.length);
    }

    if (isClassified === 'true' || isClassified === 'false') {
      params.push(isClassified === 'true');
      conditions.push('is_classified = $' + params.length);
    }

    const whereClause = conditions.length > 0 ? ('WHERE ' + conditions.join(' AND ')) : '';

    // Total count for pagination
    const countQuery = 'SELECT COUNT(*) FROM raw_trends_inbox ' + whereClause + ';';
    const countRes = await pool.query(countQuery, params);
    const total = parseInt(countRes.rows[0].count, 10);

    // Items query with pagination
    params.push(limit);
    const limitParam = '$' + params.length;
    params.push(offset);
    const offsetParam = '$' + params.length;

    const sortParam = req.query?.sort === 'id' ? 'id DESC' : 'updated_at DESC NULLS LAST, id DESC';

    const query = 'SELECT id, inbox_id, source_platform, title, item_type, category_primary, is_classified, harvested_date, created_at, updated_at, raw_payload ' +
      'FROM raw_trends_inbox ' +
      whereClause + ' ' +
      'ORDER BY ' + sortParam + ' ' +
      'LIMIT ' + limitParam + ' OFFSET ' + offsetParam + ';';
    const result = await pool.query(query, params);

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
        updated_at: r.updated_at,
        ...p
      };
    });

    return res.status(200).json({
      status: 'success',
      count: items.length,
      items: items,
      pagination: {
        total: total,
        limit: limit,
        offset: offset,
        has_more: (offset + items.length) < total
      }
    });
  } catch (err) {
    console.error('[API Inbox Error]:', err);
    return res.status(500).json({ status: 'error', message: 'Internal server error while fetching inbox items' });
  }
};
