/**
 * tools/drain_voyage_embeddings.js
 * ==============================================================================
 * Ultra-Fast Bulk Voyage Embedding & Semantic Deduplication Drainer
 * ------------------------------------------------------------------------------
 * Loops through all items in raw_trends_inbox where embedding IS NULL
 * in batches of 100 via api/embed-worker.js until 0 remaining.
 * ==============================================================================
 */

const path = require('path');
const handler = require('../api/embed-worker.js');

async function runDrain() {
  console.log('==================================================================');
  console.log('🚀 [Voyage Embedder Drain] Starting Full Vector Drain Loop');
  console.log('==================================================================');

  let remaining = 999999;
  let batchNum = 1;
  let totalProcessed = 0;
  let totalMerged = 0;
  const startTime = Date.now();

  while (remaining > 0) {
    const batchStart = Date.now();
    try {
      const batchPromise = new Promise((resolve, reject) => {
        const req = { query: { limit: '100' }, body: {} };
        const res = {
          setHeader: () => {},
          status: (code) => ({
            json: (data) => resolve({ code, data })
          })
        };
        handler(req, res).catch(reject);
      });

      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Batch processing timed out after 45s')), 45000);
      });

      const result = await Promise.race([batchPromise, timeoutPromise]);

      if (result.code !== 200 || !result.data.success) {
        console.error(`[!] Batch #${batchNum} failed with code ${result.code}:`, result.data);
        break;
      }

      const pCount = result.data.processed_count || 0;
      const mCount = result.data.merged_duplicates_count || 0;
      remaining = result.data.remaining_unembedded !== undefined ? result.data.remaining_unembedded : 0;
      totalProcessed += pCount;
      totalMerged += mCount;

      console.log(`[Batch #${String(batchNum).padStart(2)}] Embedded: ${String(pCount).padStart(3)} | Merged: ${String(mCount).padStart(2)} | Remaining: ${String(remaining).padStart(4)} | ${Date.now() - batchStart}ms`);

      if (pCount === 0 || remaining === 0) {
        break;
      }

      batchNum++;
      await new Promise(r => setTimeout(r, 600));
    } catch (err) {
      console.error(`[!] Exception during batch #${batchNum}:`, err.message);
      // Wait 3s before retry or stop
      await new Promise(r => setTimeout(r, 3000));
      batchNum++;
    }
  }

  const totalSec = ((Date.now() - startTime) / 1000).toFixed(1);
  console.log('==================================================================');
  console.log(`🎉 [Voyage Drain Completed] ${totalProcessed} embedded, ${totalMerged} duplicates merged in ${totalSec}s!`);
  console.log(`📊 Final Remaining Unembedded: ${remaining}`);
  console.log('==================================================================');
}

runDrain().then(() => {
  process.exit(0);
}).catch(err => {
  console.error('[Fatal]', err);
  process.exit(1);
});
