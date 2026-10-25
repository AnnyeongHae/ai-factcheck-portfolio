#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/re_enrich_all_600.py
==============================================================================
Production AI Enrichment Dispatcher (SSOT)
------------------------------------------------------------------------------
CRITICAL ARCHITECTURAL POLICY:
- External paid LLM APIs (Google AI Studio REST, OpenRouter) and fallback chains
  are PERMANENTLY PROHIBITED.
- AI Enrichment is 100% strictly executed via Antigravity In-Session Subagents
  (`invoke_subagent`, Model: Flash, Parallel Wave x3, $0 cost).
- This script exports unclassified items into `data/subagent_queue/batch_XXX.json`
  and applies completed `batch_XXX_done.json` files to PostgreSQL SSOT.
==============================================================================
"""

import sys
import os
import re
import json
import time
from datetime import datetime, timezone
import subprocess

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

def run_re_enrichment(batch_size: int = 25, limit: int = None, **kwargs):
    print("=" * 65)
    print("🛡️ [AI Enrichment Dispatcher] Strict Zero-External-LLM SSOT Policy")
    print(" • External Gemini REST API : PERMANENTLY DISABLED (No 404/Quota leaks)")
    print(" • External OpenRouter API  : PERMANENTLY DISABLED (No 429/Fallback chains)")
    print(" • Canonical Enrichment Engine: Antigravity In-Session Subagents ($0)")
    print("=" * 65 + "\n")

    conn = get_db_connection()
    if not conn:
        print("[!] Error: DB Connection failed.")
        return 1

    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*)
        FROM raw_trends_inbox
        WHERE is_classified = FALSE OR raw_payload->'ai_enrichment' IS NULL;
    """)
    unclassified_count = cur.fetchone()[0]
    conn.close()

    print(f"[*] Current Database Status: {unclassified_count} unclassified items pending.")

    if unclassified_count == 0:
        print("✨ All items already have verified authentic translations & hooks (100% complete)!")
        return 0

    # Step 1: Export unclassified items into subagent queue batches
    queue_dir = os.path.join(ROOT_DIR, "data", "subagent_queue")
    os.makedirs(queue_dir, exist_ok=True)
    num_batches = (unclassified_count + batch_size - 1) // batch_size
    print(f"[*] Exporting {unclassified_count} items into {num_batches} queue batches (batch_size={batch_size})...")

    try:
        from export_subagent_waves import export_waves
        export_waves(start_batch=201, num_batches=num_batches, batch_size=batch_size)
    except Exception as e:
        print(f"[!] Warning: Wave export helper returned: {e}")

    # Step 2: Check for any existing completed batch files and apply them
    applied_count = 0
    try:
        for fname in sorted(os.listdir(queue_dir)):
            if fname.endswith("_done.json"):
                fpath = os.path.join(queue_dir, fname)
                mtime = os.path.getmtime(fpath)
                if (time.time() - mtime) < 3600:  # within last hour
                    cmd = [sys.executable, os.path.join(tools_dir, "subagent_queue_manager.py"), "--apply", fpath]
                    res = subprocess.run(cmd, capture_output=True, text=True)
                    if res.returncode == 0:
                        applied_count += 1
                        print(f"[+] Applied completed batch: {fname}")
    except Exception as e:
        print(f"[!] Error applying done batches: {e}")

    # Check updated status
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM raw_trends_inbox WHERE is_classified = FALSE OR raw_payload->'ai_enrichment' IS NULL;")
        rem_count = cur.fetchone()[0]
        conn.close()
        print(f"\n[*] Status Summary:")
        print(f"   • Remaining unclassified items: {rem_count}건")
        if rem_count > 0:
            print("   👉 Items are queued in data/subagent_queue/. Please run In-Session Subagents to complete.")
        else:
            print("   ✅ All items successfully enriched! Triggering Voyage and Spike ranking...")
            try:
                subprocess.run([sys.executable, os.path.join(tools_dir, "drain_voyage_embeddings.py")], check=False)
                subprocess.run([sys.executable, os.path.join(tools_dir, "recompute_spike_scores.py"), "--commit", "--silent"], check=False)
            except Exception as e:
                print(f"[!] Post-enrichment trigger error: {e}")

    return 0

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AI Enrichment Dispatcher (In-Session Subagent SSOT)")
    parser.add_argument("--batch-size", type=int, default=25, help="Batch size per queue chunk (default: 25)")
    parser.add_argument("--limit", type=int, default=None, help="Max candidates")
    parser.add_argument("--mode", type=str, default="in-session", help="Ignored (external APIs disabled)")
    parser.add_argument("--concurrency", type=int, default=3, help="Ignored")
    args = parser.parse_args()
    sys.exit(run_re_enrichment(batch_size=args.batch_size, limit=args.limit))
