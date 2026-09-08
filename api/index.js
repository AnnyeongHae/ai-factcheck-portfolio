module.exports = (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.status(200).json({
    status: 'ONLINE',
    service: 'AI Tech-Lineage Fact-Check Intelligence Hub (Vercel Serverless)',
    version: 'v20.0',
    endpoints: ['/api/stats', '/api/health', '/api/queue']
  });
};
