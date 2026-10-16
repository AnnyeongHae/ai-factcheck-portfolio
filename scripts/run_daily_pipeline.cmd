@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ==============================================================================
echo [FactCheck Hub] Daily 23:00 KST Local Enrichment ^& Trend Analysis Pipeline
echo Timestamp: %DATE% %TIME%
echo ==============================================================================

set "PROJECT_DIR=D:\2026.06.21_Antigravity\2026-08-31_WEB_Factcheck"
cd /d "%PROJECT_DIR%"

echo.
echo [Step 1/4] Running Voyage Vector Embeddings Drain...
python -u tools\drain_voyage_embeddings.py
if %ERRORLEVEL% neq 0 (
    echo [!] Warning: Voyage embedding worker encountered an issue, proceeding to next step.
)

echo.
echo [Step 2/4] Running AI Summarization ^& Multilingual Translation...
:: AGENTS.md Mode 3 (Local OpenRouter Free, Batch 3) or local pipeline
python -u tools\re_enrich_all_600.py --mode local-openrouter --batch-size 3 --max-items 60 --max-time 300
if %ERRORLEVEL% neq 0 (
    echo [!] AI Enrichment completed with return code %ERRORLEVEL%.
)

echo.
echo [Step 3/4] Running 23:00 KST End-of-Day (EOD) Digest Engine...
python -u tools\run_eod_digest.py --top 10
if %ERRORLEVEL% neq 0 (
    echo [!] EOD Digest warning, proceeding to final spike recompute.
)

echo.
echo [Step 4/4] Recomputing H-V-D Tripod Spike Scores ^& Updating Daily Rankings...
python -u tools\recompute_spike_scores.py --commit
if %ERRORLEVEL% neq 0 (
    echo [!] Spike recompute warning.
)

echo.
echo ==============================================================================
echo [FactCheck Hub] Pipeline finished successfully at %DATE% %TIME%
echo ==============================================================================
exit /b 0
