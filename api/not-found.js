// api/not-found.js - Fail-closed JSON 404/401 handler for unknown /api/* routes
const { handleOptions, setCorsHeaders } = require('./_lib/cors');

module.exports = (req, res) => {
  if (handleOptions(req, res, 'GET, POST, OPTIONS')) return;
  setCorsHeaders(res, 'GET, POST, OPTIONS');
  res.setHeader('Cache-Control', 'no-store');

  const path = String(req.url || '');
  if (/^\/api\/admin(\/|$)/i.test(path)) {
    return res.status(401).json({ status: 'error', error: 'Unauthorized' });
  }
  return res.status(404).json({ status: 'error', error: 'API endpoint not found' });
};
