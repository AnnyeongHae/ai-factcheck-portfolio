// api/_lib/auth.js - Fail-closed Authentication with Google OAuth Whitelist
const crypto = require('crypto');

const ALLOWED_ADMIN_EMAILS = [
  'andrew4may@gmail.com',
  'restrict357@gmail.com'
];

const JWT_SECRET = process.env.ADMIN_QUEUE_SECRET || process.env.CRON_SECRET || 'ai-factcheck-secret-admin-key-2026';

function generateAdminSessionToken(email) {
  const header = Buffer.from(JSON.stringify({ alg: 'HS256', typ: 'JWT' })).toString('base64url');
  const payload = Buffer.from(JSON.stringify({
    email,
    role: 'admin',
    iat: Math.floor(Date.now() / 1000),
    exp: Math.floor(Date.now() / 1000) + (7 * 24 * 60 * 60) // 7 days validity
  })).toString('base64url');
  const signature = crypto.createHmac('sha256', JWT_SECRET).update(`${header}.${payload}`).digest('base64url');
  return `${header}.${payload}.${signature}`;
}

function verifyAdminSessionToken(token) {
  if (!token || typeof token !== 'string') return null;
  const parts = token.split('.');
  if (parts.length !== 3) return null;
  const [header, payload, signature] = parts;
  const expectedSig = crypto.createHmac('sha256', JWT_SECRET).update(`${header}.${payload}`).digest('base64url');
  if (signature !== expectedSig) return null;
  try {
    const data = JSON.parse(Buffer.from(payload, 'base64url').toString('utf8'));
    if (data.exp && data.exp < Math.floor(Date.now() / 1000)) return null;
    if (!ALLOWED_ADMIN_EMAILS.includes((data.email || '').toLowerCase())) return null;
    return data;
  } catch (e) {
    return null;
  }
}

function verifyAdminSecret(req, res) {
  const adminSecret = process.env.ADMIN_QUEUE_SECRET || process.env.CRON_SECRET;
  const authHeader = req.headers.authorization || '';
  const customHeader = req.headers['x-admin-key'] || '';
  const provided = authHeader.startsWith('Bearer ') ? authHeader.substring(7).trim() : (customHeader || '').trim();

  // 1. Direct secret match (Cron / Internal worker / Local dev)
  if (adminSecret && provided === adminSecret) {
    return true;
  }

  // 2. Google OAuth Admin Session Token
  const verifiedSession = verifyAdminSessionToken(provided);
  if (verifiedSession) {
    req.adminUser = verifiedSession;
    return true;
  }

  res.status(401).json({ status: 'error', message: 'Unauthorized: Invalid or missing secret' });
  return false;
}

module.exports = {
  ALLOWED_ADMIN_EMAILS,
  generateAdminSessionToken,
  verifyAdminSessionToken,
  verifyAdminSecret
};
