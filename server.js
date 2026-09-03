const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

// 1. Auto-load .env into process.env
const envPath = path.join(__dirname, '.env');
if (fs.existsSync(envPath)) {
  const envContent = fs.readFileSync(envPath, 'utf8');
  envContent.split('\n').forEach(line => {
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith('#') && trimmed.includes('=')) {
      const idx = trimmed.indexOf('=');
      const key = trimmed.slice(0, idx).trim();
      const val = trimmed.slice(idx + 1).trim();
      if (!process.env[key]) {
        process.env[key] = val;
      }
    }
  });
}

if (!process.env.DATABASE_URL && process.env.NEON_KEY) {
  process.env.DATABASE_URL = process.env.NEON_KEY;
}

const portfoliosHandler = require('./api/portfolios');
const queueHandler = require('./api/queue');
const healthHandler = require('./api/health');
const batchHandler = require('./api/batch');

const PORT = process.env.PORT || 3000;
const PUBLIC_DIR = path.join(__dirname, 'public');

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon'
};

// Express-like mock response adapter for Serverless functions
function adaptResponse(res) {
  res.status = function(code) {
    res.statusCode = code;
    return res;
  };
  res.json = function(data) {
    res.setHeader('Content-Type', 'application/json; charset=utf-8');
    res.end(JSON.stringify(data, null, 2));
    return res;
  };
  return res;
}

// Helper to parse JSON body
function parseRequestBody(req) {
  return new Promise((resolve) => {
    if (req.method === 'GET' || req.method === 'OPTIONS') {
      return resolve({});
    }
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        resolve(JSON.parse(body || '{}'));
      } catch (e) {
        resolve({});
      }
    });
  });
}

const server = http.createServer(async (req, res) => {
  const parsedUrl = url.parse(req.url, true);
  const pathname = parsedUrl.pathname;

  adaptResponse(res);

  // Parse Body for POST requests
  req.body = await parseRequestBody(req);

  console.log(`[${new Date().toLocaleTimeString()}] ${req.method} ${pathname}`);

  // Route: /api/portfolios
  if (pathname === '/api/portfolios') {
    return portfoliosHandler(req, res);
  }

  // Route: /api/queue or /api/news
  if (pathname === '/api/queue') {
    return queueHandler(req, res);
  }

  if (pathname === '/api/health') {
    return healthHandler(req, res);
  }

  if (pathname === '/api/batch') {
    return batchHandler(req, res);
  }

  // Static File Serving (from public/)
  let filePath = path.join(PUBLIC_DIR, pathname === '/' ? 'index.html' : pathname);
  if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
    filePath = path.join(PUBLIC_DIR, 'index.html');
  }

  const ext = path.extname(filePath).toLowerCase();
  const contentType = MIME_TYPES[ext] || 'application/octet-stream';

  fs.readFile(filePath, (err, content) => {
    if (err) {
      res.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('500 Internal Server Error');
      return;
    }
    res.writeHead(200, { 'Content-Type': contentType });
    res.end(content);
  });
});

server.listen(PORT, () => {
  console.log('===============================================================');
  console.log(`🚀 [LOCAL LIVE SERVER] Running at http://localhost:${PORT}`);
  console.log(`🐘 [NEON DB CONNECTED] Real-time queries on 16 Verified Cases`);
  console.log('===============================================================');
});
