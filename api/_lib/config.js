// api/_lib/config.js - Centralized Backend & Database Configuration (SSOT: Aiven PostgreSQL)
const { URL } = require('url');

const isNeon = (url) => typeof url === 'string' && url.includes('neon.tech');

function resolveDatabaseUrl() {
  // 1. Explicit Aiven priority (SSOT)
  if (process.env.AIVEN_SERVICE_URI) {
    return process.env.AIVEN_SERVICE_URI;
  }

  // 2. DATABASE_URL
  const dbUrl = process.env.DATABASE_URL || '';
  if (dbUrl) {
    if (!isNeon(dbUrl)) {
      return dbUrl;
    }
    // If DATABASE_URL points to Neon, freeze it by default to protect quota
    if (process.env.ALLOW_FROZEN_NEON === 'true') {
      console.warn('[DB Config] ⚠️ Using frozen Neon DB (ALLOW_FROZEN_NEON=true).');
      return dbUrl;
    }
    console.warn('[DB Config] ⛔ Neon PostgreSQL is FROZEN (100% bandwidth quota exhausted). Active queries blocked to prevent suspension.');
    return '';
  }

  // 3. Fallbacks
  if (process.env.ALLOW_FROZEN_NEON === 'true') {
    return process.env.NEON_KEY || process.env.NEON_DATABASE_URL || '';
  }

  return '';
}

const DATABASE_URL = resolveDatabaseUrl();

function getDbProviderInfo(rawUrl = DATABASE_URL) {
  if (!rawUrl) {
    const envUrl = process.env.DATABASE_URL || process.env.NEON_KEY || '';
    if (isNeon(envUrl)) {
      return {
        provider: 'Neon PostgreSQL (Frozen / Blocked)',
        host: 'ep-old-violet-az13jhvl-pooler.c-3.ap-southeast-1.aws.neon.tech',
        port: '5432',
        database: 'neondb',
        user: 'neondb_owner',
        status: 'FROZEN_BLOCKED',
        instruction: 'Neon quota is exhausted (100%). Configure AIVEN_SERVICE_URI or update DATABASE_URL in Vercel settings.'
      };
    }

    return {
      provider: 'Not Configured',
      host: null,
      port: null,
      database: null,
      user: null
    };
  }

  try {
    const parsed = new URL(rawUrl);
    const host = parsed.hostname || '';
    let provider = 'PostgreSQL';

    if (host.includes('aivencloud.com')) {
      provider = 'Aiven PostgreSQL';
    } else if (host.includes('neon.tech')) {
      provider = 'Neon PostgreSQL';
    } else if (host.includes('supabase.co')) {
      provider = 'Supabase PostgreSQL';
    } else if (host === 'localhost' || host === '127.0.0.1') {
      provider = 'Local PostgreSQL';
    }

    return {
      provider,
      host,
      port: parsed.port || '5432',
      database: parsed.pathname ? parsed.pathname.replace(/^\//, '') : '',
      user: parsed.username || ''
    };
  } catch (err) {
    return {
      provider: 'Custom PostgreSQL',
      host: 'Unknown',
      port: null,
      database: null,
      user: null
    };
  }
}

const POOL_CONFIG = {
  max: 5,
  idleTimeoutMillis: 15000,
  connectionTimeoutMillis: 5000,
  ssl: { rejectUnauthorized: false }
};

module.exports = {
  DATABASE_URL,
  getDbProviderInfo,
  POOL_CONFIG
};
