#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/daily_2300_local_eod.py
==============================================================================
Nightly 23:00 KST Local End-of-Day (EOD) Automation Runner
------------------------------------------------------------------------------
Strict Invariant Pipeline:
1. Check unclassified items in DB (Aiven PostgreSQL SSOT)
2. Run local AI Enrichment via Antigravity CLI Gemini Flash (Zero External API Cost)
3. Run Voyage Embedding on enriched text (MANDATORY: strictly AFTER enrichment)
4. Recompute H-V-D Tripod Spike Scores & Cross-Platform Clusters
5. Run EOD Daily Digest
==============================================================================
"""

import os
import sys
import time
import subprocess
from datetime import datetime, timezone

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
tools_dir = os.path.join(ROOT_DIR, "tools")
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

from db_config import get_db_connection

def run_step(step_name: str, cmd_list: list):
    print("\n" + "=" * 70)
    print(f"▶ [{step_name}] Starting...")
    print(f"  Command: {' '.join(cmd_list)}")
    print("=" * 70, flush=True)
    t0 = time.time()
    res = subprocess.run(cmd_list, cwd=ROOT_DIR)
    dur = time.time() - t0
    if res.returncode == 0:
        print(f"✓ [{step_name}] Completed successfully in {dur:.1f}s")
        return True
    else:
        print(f"✗ [{step_name}] Failed with exit code {res.returncode} in {dur:.1f}s")
        return False

def main():
    print("=" * 70)
    print("🌙 [AI FactCheck Hub] Nightly 23:00 KST Local Pipeline Runner")
    print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Local)")
    print("=" * 70)

    conn = get_db_connection()
    if not conn:
        print("[!] DB connection failed. Aborting.")
        return 1

    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM raw_trends_inbox WHERE is_classified = FALSE;")
    unclassified_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM raw_trends_inbox WHERE is_classified = TRUE AND embedding IS NULL;")
    unembedded_count = cur.fetchone()[0]
    conn.close()

    print(f"[*] Current DB Status:")
    print(f"  • Unclassified items : {unclassified_count:,} 건")
    print(f"  • Unembedded items   : {unembedded_count:,} 건")

    # Step 1: AI Enrichment via Antigravity CLI Gemini Flash
    if unclassified_count > 0:
        print(f"\n[*] Found {unclassified_count} unclassified items. Launching Antigravity CLI Gemini Flash enricher...")
        ok = run_step(
            "Step 1: AI Enrichment (Antigravity CLI Gemini Flash)",
            [sys.executable, "-u", os.path.join(tools_dir, "re_enrich_all_600.py"), "--mode", "local-gemini", "--batch-size", "25", "--concurrency", "3"]
        )
        if not ok:
            print("[!] AI Enrichment step had errors. Please check logs.")
    else:
        print("\n✓ No unclassified items found. All items already enriched!")

    # Step 2: Voyage Semantic Embedding (Runs strictly after enrichment)
    run_step(
        "Step 2: Voyage Semantic Embedding",
        [sys.executable, "-u", os.path.join(tools_dir, "drain_voyage_embeddings.py")]
    )

    # Step 3: H-V-D Tripod Spike Scores & EOD Top 10 Daily Hot Curation (Single-Pass SSOT)
    run_step(
        "Step 3: H-V-D Tripod Spike Scores & EOD Daily Hot 10 (Single-Pass)",
        [sys.executable, "-u", os.path.join(tools_dir, "recompute_spike_scores.py"), "--commit"]
    )

    print("\n" + "=" * 70)
    print("🎉 [Nightly Local Pipeline] All tasks completed successfully!")
    print("=" * 70)
    return 0

if __name__ == "__main__":
    sys.exit(main())
