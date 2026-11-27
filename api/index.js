module.exports = (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  const rawPath = String(req.url || '/api').split('?')[0].replace(/\/+$/, '') || '/api';

  if (rawPath === '/api' || rawPath === '/api/index') {
    return res.status(200).json({
      status: 'ONLINE',
      service: 'AI Tech-Lineage Fact-Check Intelligence Hub (Vercel Serverless)',
      version: 'v21.2',
      endpoints: ['/api/stats', '/api/health', '/api/inbox', '/api/portfolios', '/api/queue']
    });
  }

  res.setHeader('Cache-Control', 'no-store');
  if (/^\/api\/admin(\/|$)/i.test(rawPath)) {
    return res.status(401).json({ status: 'error', error: 'Unauthorized' });
  }
  return res.status(404).json({ status: 'error', error: 'API endpoint not found' });
};
