// api/auth/google.js - Google Identity Services OAuth Verification for Admin
const https = require('https');
const { setCorsHeaders, handleOptions } = require('../_lib/cors');
const { ALLOWED_ADMIN_EMAILS, generateAdminSessionToken, verifyAdminSessionToken } = require('../_lib/auth');

const GOOGLE_CLIENT_ID = process.env.GOOGLE_CLIENT_ID || '62067487846-a43fhnnnk6teqfdi99vrkiknfato8fk0.apps.googleusercontent.com';

function fetchGoogleTokenInfo(idToken) {
  return new Promise((resolve, reject) => {
    const url = `https://oauth2.googleapis.com/tokeninfo?id_token=${encodeURIComponent(idToken)}`;
    https.get(url, (res) => {
      let data = '';
      res.on('data', chunk => { data += chunk; });
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(parsed);
          } else {
            reject(new Error(parsed.error_description || parsed.error || 'Token verification failed'));
          }
        } catch (e) {
          reject(e);
        }
      });
    }).on('error', reject);
  });
}

module.exports = async function handler(req, res) {
  if (handleOptions(req, res, 'GET, POST, OPTIONS')) return;
  setCorsHeaders(res, 'GET, POST, OPTIONS');

  // GET: Check current admin authentication status
  if (req.method === 'GET') {
    const authHeader = req.headers.authorization || '';
    const customHeader = req.headers['x-admin-key'] || '';
    const token = authHeader.startsWith('Bearer ') ? authHeader.substring(7).trim() : (customHeader || '').trim();
    const session = verifyAdminSessionToken(token);
    if (session) {
      return res.status(200).json({ authenticated: true, user: session });
    }
    return res.status(200).json({ authenticated: false });
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method Not Allowed' });
  }

  try {
    const { credential } = req.body || {};
    if (!credential) {
      return res.status(400).json({ success: false, error: 'Google 인증 정보(credential)가 전달되지 않았습니다.' });
    }

    const payload = await fetchGoogleTokenInfo(credential);

    // 1. Audience (Client ID) verification
    if (payload.aud !== GOOGLE_CLIENT_ID) {
      console.warn(`[Auth] Audience mismatch: expected ${GOOGLE_CLIENT_ID}, got ${payload.aud}`);
      return res.status(401).json({ success: false, error: 'Google Client ID가 일치하지 않습니다.' });
    }

    // 2. Email verification
    if (payload.email_verified !== 'true' && payload.email_verified !== true) {
      return res.status(401).json({ success: false, error: '이메일 인증이 완료되지 않은 Google 계정입니다.' });
    }

    // 3. Strict Admin Email Whitelist check
    const email = (payload.email || '').toLowerCase().trim();
    if (!ALLOWED_ADMIN_EMAILS.includes(email)) {
      console.warn(`[Auth] Unauthorized admin login attempt by: ${email}`);
      return res.status(403).json({
        success: false,
        error: '접근 권한이 없는 Google 계정입니다. 허가된 관리자 계정으로 로그인해 주세요.'
      });
    }

    // 4. Generate signed admin session token
    const adminToken = generateAdminSessionToken(email);

    return res.status(200).json({
      success: true,
      message: '관리자 인증이 완료되었습니다.',
      user: {
        email: payload.email,
        name: payload.name || payload.email,
        picture: payload.picture || ''
      },
      adminToken
    });
  } catch (err) {
    console.error('[Auth Error]', err.message);
    return res.status(401).json({ success: false, error: `Google 인증 검증 실패: ${err.message}` });
  }
};
