const https = require('https');
const { getDbPool } = require('./_lib/db');
const { handleOptions, setCorsHeaders } = require('./_lib/cors');

function triggerGithubRecoveryHook() {
  return new Promise((resolve) => {
    const ghToken = process.env.GH_TOKEN || process.env.GITHUB_TOKEN;
    if (!ghToken) {
      return resolve({ triggered: false, reason: "GH_TOKEN not configured in Vercel environment" });
    }

    const repoOwner = process.env.GITHUB_REPO_OWNER || "AnnyeongHae";
    const repoName = process.env.GITHUB_REPO_NAME || "ai-factcheck-portfolio";
    const workflowFileName = "deploy_pages.yml";

    const payload = JSON.stringify({ ref: "main" });
    const options = {
      hostname: 'api.github.com',
      port: 443,
      path: `/repos/${repoOwner}/${repoName}/actions/workflows/${workflowFileName}/dispatches`,
      method: 'POST',
      headers: {
        'User-Agent': 'Vercel-Watchdog-Hook/1.0',
        'Authorization': `Bearer ${ghToken}`,
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload)
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode === 204 || res.statusCode === 200 || res.statusCode === 201) {
          resolve({ triggered: true, status: res.statusCode, message: "Successfully triggered GitHub Actions recovery workflow." });
        } else {
          resolve({ triggered: false, status: res.statusCode, message: `GitHub API returned HTTP ${res.statusCode}: ${data}` });
        }
      });
    });

    req.on('error', (err) => {
      resolve({ triggered: false, reason: err.message });
    });

    req.write(payload);
    req.end();
  });
}

module.exports = async (req, res) => {
  if (handleOptions(req, res, 'GET, OPTIONS')) return;
  setCorsHeaders(res, 'GET, OPTIONS');
  res.setHeader('Cache-Control', 'no-store, max-age=0');

  // Authentication: require CRON_SECRET or ADMIN_QUEUE_SECRET to prevent unauthorized GitHub Actions triggers
  const cronSecret = process.env.CRON_SECRET || process.env.ADMIN_QUEUE_SECRET;
  if (cronSecret) {
    const authHeader = req.headers.authorization || '';
    const querySecret = req.query?.secret || '';
    const provided = authHeader.startsWith('Bearer ') ? authHeader.substring(7) : querySecret;
    if (!provided || provided !== cronSecret) {
      return res.status(401).json({ status: 'ERROR', message: 'Unauthorized: Invalid or missing secret' });
    }
  }

  const pool = getDbPool();
  if (!pool) {
    return res.status(500).json({
      status: "ERROR",
      message: "Database connection not available",
      watchdog_timestamp: new Date().toISOString()
    });
  }

  try {
    // 1. Check latest harvest time from raw_trends_inbox
    const harvestTimeRes = await pool.query(`
      SELECT 
        MAX(created_at) AS latest_created_at,
        MAX(harvested_date) AS latest_harvest_date,
        COUNT(*) AS total_items
      FROM raw_trends_inbox;
    `);
    const hRow = harvestTimeRes.rows[0] || {};
    const latestCreatedAt = hRow.latest_created_at ? new Date(hRow.latest_created_at) : null;
    const totalItems = parseInt(hRow.total_items || 0, 10);

    // 2. Check latest harvest_runs entry if available
    let latestHarvestRun = null;
    try {
      const runRes = await pool.query(`
        SELECT run_id, started_at, finished_at, total_fetched, new_saved, status
        FROM harvest_runs
        ORDER BY started_at DESC
        LIMIT 1;
      `);
      if (runRes.rows.length > 0) {
        latestHarvestRun = runRes.rows[0];
      }
    } catch (e) {
      // Table might be initializing
    }

    // 3. Check latest GitHub Actions run status
    let latestActionsRun = null;
    try {
      const actionsRes = await pool.query(`
        SELECT run_id, workflow_name, status, conclusion, started_at, duration_seconds
        FROM github_actions_run_logs
        ORDER BY started_at DESC
        LIMIT 1;
      `);
      if (actionsRes.rows.length > 0) {
        latestActionsRun = actionsRes.rows[0];
      }
    } catch (e) {
      // Telemetry table optional
    }

    // 4. Calculate harvest freshness
    const now = new Date();
    const runTime = latestHarvestRun?.started_at ? new Date(latestHarvestRun.started_at) : null;
    let referenceTime = latestCreatedAt;
    if (runTime && (!referenceTime || runTime > referenceTime)) {
      referenceTime = runTime;
    }
    const hoursSinceHarvest = referenceTime ? ((now.getTime() - referenceTime.getTime()) / (1000 * 60 * 60)) : 999;

    let systemStatus = "HEALTHY";
    let alertDetails = [];

    // Threshold: 8.0 hours (6-hour cron cycle + 2-hour grace margin)
    if (hoursSinceHarvest > 8.0) {
      systemStatus = "ALERT_STALE";
      alertDetails.push(`No fresh harvest recorded for ${hoursSinceHarvest.toFixed(1)} hours (expected every 6h).`);
    }

    if (latestActionsRun && latestActionsRun.conclusion === 'failure') {
      systemStatus = systemStatus === "ALERT_STALE" ? "ALERT_CRITICAL" : "ALERT_ACTION_FAILED";
      alertDetails.push(`Most recent GitHub Actions run #${latestActionsRun.run_id} failed.`);
    }

    // 5. If Alert, trigger self-healing recovery hook if configured
    let healingResult = { triggered: false, reason: "System healthy; no recovery needed." };
    if (systemStatus.startsWith("ALERT")) {
      healingResult = await triggerGithubRecoveryHook();
    }

    return res.status(200).json({
      status: systemStatus,
      watchdog_timestamp: now.toISOString(),
      hours_since_last_harvest: parseFloat(hoursSinceHarvest.toFixed(2)),
      alert_details: alertDetails,
      metrics: {
        total_inbox_items: totalItems,
        latest_harvest_time: referenceTime ? referenceTime.toISOString() : null,
        latest_harvest_run: latestHarvestRun,
        latest_actions_run: latestActionsRun
      },
      self_healing: healingResult
    });

  } catch (err) {
    console.error('[Watchdog Error]:', err);
    return res.status(500).json({
      status: "ERROR",
      message: "Internal server error during watchdog check",
      watchdog_timestamp: new Date().toISOString()
    });
  }
};
