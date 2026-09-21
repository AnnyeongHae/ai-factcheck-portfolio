// api/_lib/config.js - Centralized Backend & Database Configuration
const { URL } = require('url');

const DATABASE_URL = process.env.DATABASE_URL || 
                     process.env.AIVEN_SERVICE_URI || 
                     process.env.NEON_KEY || 
                     process.env.NEON_DATABASE_URL || 
                     '';

function getDbProviderInfo(rawUrl = DATABASE_URL) {
  if (!rawUrl) {
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
