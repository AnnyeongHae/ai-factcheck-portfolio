// api/_lib/auth.js - Fail-closed Authentication
function verifyAdminSecret(req, res) {
  const adminSecret = process.env.ADMIN_QUEUE_SECRET || process.env.CRON_SECRET;
  if (!adminSecret) {
    res.status(500).json({ status: 'error', message: 'Server misconfigured: Secret not set' });
    return false;
  }

  const authHeader = req.headers.authorization || '';
  const customHeader = req.headers['x-admin-key'] || '';
  const querySecret = req.query?.secret || '';
  const provided = authHeader.startsWith('Bearer ') ? authHeader.substring(7) : (customHeader || querySecret);

  if (!provided || provided !== adminSecret) {
    res.status(401).json({ status: 'error', message: 'Unauthorized: Invalid or missing secret' });
    return false;
  }

  return true;
}

module.exports = { verifyAdminSecret };
