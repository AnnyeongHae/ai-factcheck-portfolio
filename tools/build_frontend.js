/**
 * ==============================================================================
 * Frontend Modular Build & Synchronization Engine (SSOT)
 * Bundles modular src/js/main.js into src/js/app.js, public/app.js, and docs/app.js
 * Runs node:vm syntax check to guarantee 0 syntax errors before publishing.
 * ==============================================================================
 */

const fs = require('fs');
const path = require('path');
const vm = require('vm');
const esbuild = require('esbuild');

const ROOT_DIR = path.resolve(__dirname, '..');
const ENTRY_FILE = path.join(ROOT_DIR, 'src', 'js', 'main.js');

const TARGETS = [
  path.join(ROOT_DIR, 'src', 'js', 'app.js'),
  path.join(ROOT_DIR, 'public', 'app.js'),
  path.join(ROOT_DIR, 'docs', 'app.js')
];

async function buildFrontend() {
  const startTime = Date.now();
  console.log('[Build] 🚀 Starting frontend modular bundle build from:', ENTRY_FILE);

  if (!fs.existsSync(ENTRY_FILE)) {
    console.error('[Build Error] Entry file does not exist:', ENTRY_FILE);
    process.exit(1);
  }

  try {
    // 1. Bundle using esbuild (IIFE format for universal browser compatibility)
    const result = await esbuild.build({
      entryPoints: [ENTRY_FILE],
      bundle: true,
      format: 'iife',
      target: ['es2021'],
      write: false,
      sourcemap: false,
      minify: false, // Keep readable for auditability
      banner: {
        js: `/* AI Factcheck Hub - Modular Production Bundle (SSOT) | Built: ${new Date().toISOString()} */\n`
      }
    });

    if (!result.outputFiles || result.outputFiles.length === 0) {
      throw new Error('esbuild produced no output files');
    }

    const bundledCode = result.outputFiles[0].text;
    const bundleSizeKb = (Buffer.byteLength(bundledCode, 'utf8') / 1024).toFixed(1);

    // 2. Syntax Validation via node:vm
    console.log(`[Build] 🔍 Validating JavaScript syntax (${bundleSizeKb} KB)...`);
    try {
      new vm.Script(bundledCode, { filename: 'app.bundle.js' });
      console.log('[Build] ✅ Syntax validation passed! 0 syntax errors detected.');
    } catch (syntaxErr) {
      console.error('[Build FATAL] Syntax error detected in bundled code:');
      console.error(syntaxErr.stack || syntaxErr);
      process.exit(1);
    }

    // 3. Atomically write to all target locations
    for (const targetPath of TARGETS) {
      const dir = path.dirname(targetPath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      fs.writeFileSync(targetPath, bundledCode, 'utf8');
      console.log(`[Build] 📦 Wrote: ${path.relative(ROOT_DIR, targetPath)}`);
    }

    // 4. Synchronize index.html from src/ to public/ and docs/
    const srcHtmlPath = path.join(ROOT_DIR, 'src', 'index.html');
    if (fs.existsSync(srcHtmlPath)) {
      const htmlContent = fs.readFileSync(srcHtmlPath, 'utf8');
      const publicHtmlPath = path.join(ROOT_DIR, 'public', 'index.html');
      const docsHtmlPath = path.join(ROOT_DIR, 'docs', 'index.html');
      fs.writeFileSync(publicHtmlPath, htmlContent, 'utf8');
      fs.writeFileSync(docsHtmlPath, htmlContent, 'utf8');
      console.log(`[Build] 📄 Synced index.html -> public/index.html & docs/index.html`);
    }

    const elapsed = Date.now() - startTime;
    console.log(`[Build] 🌟 Modular build completed successfully in ${elapsed}ms (${bundleSizeKb} KB across 3 targets).\n`);

  } catch (err) {
    console.error('[Build Error] Failed to build frontend:', err);
    process.exit(1);
  }
}

if (require.main === module) {
  buildFrontend();
}

module.exports = { buildFrontend };
