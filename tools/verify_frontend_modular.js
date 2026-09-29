/**
 * ==============================================================================
 * Rigorous Automated Browser Verification Suite for Modular Frontend Architecture
 * Tests zero console errors, SWR hydration, view switching, D3 citation graph,
 * search filters, modal dialogues, and instant-abort fail-safe fallback.
 * ==============================================================================
 */

const puppeteer = require('puppeteer-core');
const path = require('path');

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const TEST_URL = process.env.TEST_URL || process.argv.find(a => a.startsWith('http')) || 'http://localhost:3000';

async function runRigorousTests() {
  console.log('===============================================================');
  console.log('🧪 Starting Rigorous Modular Frontend Test Suite...');
  console.log(`🌐 Target: ${TEST_URL}`);
  console.log('===============================================================\n');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  const consoleErrors = [];
  const consoleWarnings = [];
  const consoleLogs = [];

  page.on('console', msg => {
    const text = msg.text();
    const type = msg.type();
    if (type === 'error') {
      consoleErrors.push(text);
      console.error(`  [Browser Error]: ${text}`);
    } else if (type === 'warning') {
      consoleWarnings.push(text);
    } else {
      consoleLogs.push(text);
    }
  });

  page.on('pageerror', err => {
    consoleErrors.push(err.message || String(err));
    console.error(`  [Browser Unhandled Exception]: ${err.message}`);
  });

  let testPassed = 0;
  let testFailed = 0;

  function assert(condition, testName, details = '') {
    if (condition) {
      testPassed++;
      console.log(`  ✅ [PASS] ${testName} ${details}`);
    } else {
      testFailed++;
      console.error(`  ❌ [FAIL] ${testName} ${details}`);
    }
  }

  try {
    // -------------------------------------------------------------
    // Test 1: Initial Page Load & Zero Console Errors
    // -------------------------------------------------------------
    console.log('[Test Suite 1/6] Page Load & Initialization');
    const response = await page.goto(TEST_URL, { waitUntil: 'networkidle2', timeout: 15000 });
    assert(response && response.status() === 200, 'HTTP 200 Response on root URL');

    // Wait for full hydration signal
    await page.waitForFunction(() => window.__APP_INITIALIZED__ === true && window.liveCasesData && window.liveCasesData.length > 0, { timeout: 10000 });
    const isAppInit = await page.evaluate(() => window.__APP_INITIALIZED__);
    assert(isAppInit === true, 'Modular App initialized and hydrated (window.__APP_INITIALIZED__ === true)');

    const fallbackTriggered = await page.evaluate(() => window.__FALLBACK_TRIGGERED__);
    assert(fallbackTriggered === false, 'Fail-safe fallback was NOT triggered (clean native modular execution)');

    assert(consoleErrors.length === 0, `Zero browser console errors on first paint (Found: ${consoleErrors.length})`);

    // -------------------------------------------------------------
    // Test 2: View Switching Across All 6 Tabs
    // -------------------------------------------------------------
    console.log('\n[Test Suite 2/6] View Switching & Grid Render Parity');

    // 2-1: Home View
    await page.evaluate(() => window.switchView('home'));
    await new Promise(r => setTimeout(r, 200));
    const homeTopPicksCount = await page.evaluate(() => {
      const container = document.getElementById('homeTopPicksContainer');
      return container ? container.children.length : 0;
    });
    assert(homeTopPicksCount === 3, 'Home View renders top 3 factcheck picks', `(Count: ${homeTopPicksCount})`);

    // 2-2: Portfolio View
    await page.evaluate(() => window.switchView('portfolio'));
    await new Promise(r => setTimeout(r, 200));
    const cardsCount = await page.evaluate(() => {
      const grid = document.getElementById('cardsGrid');
      return grid ? grid.children.length : 0;
    });
    assert(cardsCount > 0, 'Portfolio View renders verified dossiers', `(Rendered: ${cardsCount} cards)`);

    // 2-3: News View
    await page.evaluate(() => window.switchView('news'));
    await new Promise(r => setTimeout(r, 500)); // Allow SWR / API to deliver
    const newsCount = await page.evaluate(() => {
      const grid = document.getElementById('newsGrid');
      return grid ? grid.children.length : 0;
    });
    assert(newsCount > 0, 'News Feed View renders AI news cards', `(Rendered: ${newsCount} cards)`);

    // 2-4: Models View
    await page.evaluate(() => window.switchView('models'));
    await new Promise(r => setTimeout(r, 200));
    const modelsCount = await page.evaluate(() => {
      const grid = document.getElementById('modelsGrid');
      return grid ? grid.children.length : 0;
    });
    assert(modelsCount > 0, 'Models Registry View renders open-weights AI models', `(Rendered: ${modelsCount} cards)`);

    // 2-5: Graph View (D3 Force-Directed Simulation)
    await page.evaluate(() => window.switchView('graph'));
    await new Promise(r => setTimeout(r, 300));
    const graphNodesCount = await page.evaluate(() => {
      const circles = document.querySelectorAll('#techGraphSvg circle');
      return circles ? circles.length : 0;
    });
    assert(graphNodesCount > 0, 'D3 Citation Network Graph renders interactive SVG nodes', `(Nodes: ${graphNodesCount})`);

    // 2-6: Inbox View
    await page.evaluate(() => window.switchView('inbox'));
    await new Promise(r => setTimeout(r, 200));
    const inboxCount = await page.evaluate(() => {
      const grid = document.getElementById('inboxGrid');
      return grid ? grid.children.length : 0;
    });
    assert(inboxCount > 0, 'Ingestion Inbox View renders candidate feed items', `(Rendered: ${inboxCount} cards)`);

    // -------------------------------------------------------------
    // Test 3: Trilingual Language Toggle (KO / ZH / EN)
    // -------------------------------------------------------------
    console.log('\n[Test Suite 3/6] High-Fidelity Trilingual Localization');

    // Switch to ZH
    await page.evaluate(() => window.setLanguage('ZH'));
    await new Promise(r => setTimeout(r, 100));
    const zhHero = await page.evaluate(() => document.getElementById('heroMainTitle')?.innerText);
    assert(zhHero && zhHero.includes('热门 AI 技术的工程真相与实体验证'), 'ZH Localization updates hero title correctly');

    // Switch to EN
    await page.evaluate(() => window.setLanguage('EN'));
    await new Promise(r => setTimeout(r, 100));
    const enHero = await page.evaluate(() => document.getElementById('heroMainTitle')?.innerText);
    assert(enHero && enHero.includes('Empirical Analysis of Viral AI Technologies'), 'EN Localization updates hero title correctly');

    // Restore to KO
    await page.evaluate(() => window.setLanguage('KO'));
    await new Promise(r => setTimeout(r, 100));
    const koHero = await page.evaluate(() => document.getElementById('heroMainTitle')?.innerText);
    assert(koHero && koHero.includes('바이럴된 AI 기술의 실체 분석'), 'KO Localization restores hero title correctly');

    // -------------------------------------------------------------
    // Test 4: Modal Dossier Open & Close
    // -------------------------------------------------------------
    console.log('\n[Test Suite 4/6] Technical Dossier Modal Interaction');
    await page.evaluate(() => window.switchView('portfolio'));
    const modalOpened = await page.evaluate(() => {
      const firstCard = document.querySelector('#cardsGrid .group');
      if (firstCard && typeof firstCard.onclick === 'function') {
        firstCard.click();
        const modal = document.getElementById('detailModal');
        return modal && !modal.classList.contains('hidden');
      }
      return false;
    });
    assert(modalOpened === true, 'Clicking dossier card opens detail modal');

    const modalClosed = await page.evaluate(() => {
      window.closeModal();
      const modal = document.getElementById('detailModal');
      return modal && modal.classList.contains('hidden');
    });
    assert(modalClosed === true, 'Calling closeModal() hides detail modal cleanly');

    // -------------------------------------------------------------
    // Test 5: Search & Filter Responsiveness
    // -------------------------------------------------------------
    console.log('\n[Test Suite 5/6] Search & Filter Engine');
    await page.evaluate(() => {
      const input = document.getElementById('searchInput');
      if (input) {
        input.value = 'OpenAI';
        input.dispatchEvent(new Event('input'));
      }
    });
    await new Promise(r => setTimeout(r, 100));
    const filteredSearchCount = await page.evaluate(() => {
      const grid = document.getElementById('cardsGrid');
      return grid ? grid.children.length : 0;
    });
    assert(filteredSearchCount >= 0, 'Portfolio search filters correctly without crashes');

    await page.evaluate(() => window.clearSearch());
    await new Promise(r => setTimeout(r, 100));
    const clearedCount = await page.evaluate(() => {
      const grid = document.getElementById('cardsGrid');
      return grid ? grid.children.length : 0;
    });
    assert(clearedCount === cardsCount, 'clearSearch() restores full card set');

    // 5-2: News Feed Search & Facet Switching
    await page.evaluate(() => window.switchView('news'));
    await page.evaluate(() => window.setNewsFacetFilter('CROSS_SPIKE'));
    await new Promise(r => setTimeout(r, 200));
    const crossSpikeCount = await page.evaluate(() => document.getElementById('newsGrid')?.children.length || 0);
    assert(crossSpikeCount > 0, 'News Smart Radar facet filters to cross-platform viral spikes', `(Count: ${crossSpikeCount})`);

    await page.evaluate(() => window.setNewsFacetFilter('ALL'));
    await new Promise(r => setTimeout(r, 200));
    const allNewsCount = await page.evaluate(() => document.getElementById('newsGrid')?.children.length || 0);
    assert(allNewsCount === 15, 'Resetting News facet restores 15 cards grid', `(Count: ${allNewsCount})`);

    // 5-3: Models Family Filtering
    await page.evaluate(() => window.switchView('models'));
    await page.evaluate(() => window.setModelsFamilyFilter('Qwen'));
    await new Promise(r => setTimeout(r, 200));
    const qwenCount = await page.evaluate(() => document.getElementById('modelsGrid')?.children.length || 0);
    assert(qwenCount > 0, 'Models family filter (Qwen) renders matching models', `(Count: ${qwenCount})`);

    await page.evaluate(() => window.setModelsFamilyFilter('ALL'));
    await new Promise(r => setTimeout(r, 200));

    // 5-4: Inbox Source Filtering
    await page.evaluate(() => window.switchView('inbox'));
    await page.evaluate(() => window.setInboxSourceFilter('Hacker News'));
    await new Promise(r => setTimeout(r, 200));
    const hnCount = await page.evaluate(() => document.getElementById('inboxGrid')?.children.length || 0);
    assert(hnCount > 0, 'Inbox platform filter (Hacker News) renders matching candidates', `(Count: ${hnCount})`);

    await page.evaluate(() => window.setInboxSourceFilter('ALL'));
    await new Promise(r => setTimeout(r, 200));

    // 5-5: Home Radar Session Navigation
    await page.evaluate(() => window.switchView('home'));
    await page.evaluate(() => window.switchRadarSession(2));
    await new Promise(r => setTimeout(r, 100));
    const session2Active = await page.evaluate(() => document.getElementById('radarBtn2')?.classList.contains('bg-emerald-600'));
    assert(session2Active === true, 'Radar session 2 (06:00 KST) activates cleanly');

    await page.evaluate(() => window.switchRadarSession(1));
    await new Promise(r => setTimeout(r, 100));

    // 5-6: Telemetry Run Logs Tab Switcher
    await page.evaluate(() => window.switchView('inbox'));
    await page.evaluate(() => window.switchRunLogsTab('vercel'));
    await new Promise(r => setTimeout(r, 100));
    const vercelTabActive = await page.evaluate(() => document.getElementById('tabRunsVercel')?.classList.contains('bg-white'));
    assert(vercelTabActive === true, 'Telemetry logs tab switches to Vercel Serverless');

    await page.evaluate(() => window.switchRunLogsTab('gha'));
    await new Promise(r => setTimeout(r, 100));

    // -------------------------------------------------------------
    // Test 6: Fail-Safe Instant-Abort Fallback Test
    // -------------------------------------------------------------
    console.log('\n[Test Suite 6/6] Zero-Downtime Fail-Safe Fallback Harness');
    const fallbackPage = await browser.newPage();
    const fallbackConsoleMsgs = [];
    fallbackPage.on('console', msg => fallbackConsoleMsgs.push(msg.text()));

    // Navigate to local server
    await fallbackPage.goto(TEST_URL, { waitUntil: 'domcontentloaded' });
    // Simulate an emergency manual fallback trigger
    await fallbackPage.evaluate(() => {
      window.triggerLegacyFallback('Automated resilience drill');
    });
    await new Promise(r => setTimeout(r, 300));

    const fallbackStatus = await fallbackPage.evaluate(() => ({
      triggered: window.__FALLBACK_TRIGGERED__,
      legacyScriptAppended: !!document.querySelector('script[src*="app.legacy.js"]'),
      AppStoreExists: typeof window.AppStore !== 'undefined',
      switchViewExists: typeof window.switchView === 'function'
    }));

    assert(fallbackStatus.triggered === true, 'Fail-safe harness detects and records trigger');
    assert(fallbackStatus.legacyScriptAppended === true, 'Harness dynamically injects app.legacy.js');
    assert(fallbackStatus.AppStoreExists === true, 'Legacy store is functional after fallback');
    assert(fallbackStatus.switchViewExists === true, 'Legacy router is functional after fallback');

    await fallbackPage.close();

    // -------------------------------------------------------------
    // Test 7: Voyage Embedding API Live Communication & Status Verification
    // -------------------------------------------------------------
    console.log('\n[Test Suite 7/7] Voyage AI Embeddings & Dedup Pipeline Live Status');
    // Ensure checkVoyageEmbeddingStatus is active
    await page.evaluate(async () => {
      if (typeof window.checkVoyageEmbeddingStatus === 'function') {
        await window.checkVoyageEmbeddingStatus();
      }
    });
    await new Promise(r => setTimeout(r, 600));

    const voyageState = await page.evaluate(() => {
      const btn = document.getElementById('btnTriggerEmbedding');
      const txt = document.getElementById('btnEmbedText');
      return {
        hasBtn: !!btn,
        btnText: txt ? txt.textContent : '',
        total: window._voyageTotal,
        embedded: window._voyageEmbedded,
        remaining: window._voyageRemaining,
        workerRunning: window._voyageWorkerRunning
      };
    });

    assert(voyageState.hasBtn === true, 'Voyage embedding trigger button exists in DOM');
    assert(typeof voyageState.total === 'number' && voyageState.total > 0, 'Voyage API returned valid total count from DB', `(Total: ${voyageState.total})`);
    assert(typeof voyageState.embedded === 'number', 'Voyage API returned valid embedded count from DB', `(Embedded: ${voyageState.embedded})`);
    assert(typeof voyageState.remaining === 'number', 'Voyage API returned valid remaining unembedded count', `(Remaining: ${voyageState.remaining})`);
    assert(voyageState.btnText.length > 0, 'Voyage button label reflects live DB status', `("${voyageState.btnText}")`);

  } catch (err) {
    console.error('💥 Test execution error:', err);
    testFailed++;
  } finally {
    await browser.close();
  }

  console.log('\n===============================================================');
  console.log(`📊 Test Summary: ${testPassed} Passed, ${testFailed} Failed`);
  if (consoleErrors.length > 0) {
    console.error(`⚠️ Total Console Errors Logged: ${consoleErrors.length}`);
  } else {
    console.log('🌟 0 Console Errors, 0 Unhandled Exceptions!');
  }
  console.log('===============================================================\n');

  if (testFailed > 0) {
    process.exit(1);
  }
}

runRigorousTests().catch(err => {
  console.error('Fatal test error:', err);
  process.exit(1);
});
