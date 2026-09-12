// api/_lib/cors.js - Standard CORS handling
function setCorsHeaders(res, methods = 'GET, POST, OPTIONS') {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', methods);
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Admin-Key');
}

function handleOptions(req, res, methods = 'GET, POST, OPTIONS') {
  setCorsHeaders(res, methods);
  if (req.method === 'OPTIONS') {
    res.status(204).end();
    return true;
  }
  return false;
}

module.exports = { setCorsHeaders, handleOptions };
