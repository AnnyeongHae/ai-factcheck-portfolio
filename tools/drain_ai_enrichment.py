#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/drain_ai_enrichment.py
=====================================================
Automated Zero-Interaction AI Enrichment Worker Drain
-----------------------------------------------------
Executes during CI/CD after multi-source trend harvesting to process
unclassified items in Neon DB using Vercel Serverless micro-batches.
Eliminates reliance on user browser refresh to trigger OpenRouter AI summarization.
"""

import os
import sys
import time
import json
import urllib.request
import urllib.error

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tools_dir = os.path.join(base_dir, "tools")
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

VERCEL_WORKER_URL = "https://ai-factcheck-portfolio.vercel.app/api/enrich-worker?limit=5"
STATS_URL = "https://ai-factcheck-portfolio.vercel.app/api/stats"
MAX_ROUNDS = 8
REQUEST_TIMEOUT = 25

def get_unclassified_count():
    """Checks unclassified count directly from Neon DB, falling back to /api/stats."""
    try:
        from db_bridge import get_db_connection
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM raw_trends_inbox WHERE is_classified = FALSE;")
            count = cur.fetchone()[0]
            conn.close()
            return int(count)
    except Exception as e:
        print(f"[*] DB direct query note: {e}")

    try:
        req = urllib.request.Request(STATS_URL, headers={"User-Agent": "FactCheck-DrainWorker/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return int(data.get("counts", {}).get("inbox_unclassified", 0))
    except Exception as e:
        print(f"[!] Stats API check failed: {e}")

    return None

def trigger_worker_batch():
    """Calls Vercel enrich-worker with limit=5."""
    req = urllib.request.Request(VERCEL_WORKER_URL, headers={
        "User-Agent": "FactCheck-DrainWorker/1.0",
        "Accept": "application/json"
    })
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as he:
        body = he.read().decode("utf-8", errors="replace")
        print(f"[!] Worker HTTP {he.code}: {body[:200]}")
        return {"status": "error", "code": he.code}
    except Exception as e:
        print(f"[!] Worker call failed: {e}")
        return {"status": "error", "message": str(e)}

def drain():
    print("[*] [Zero-Interaction AI Drain] Starting automated background AI enrichment...")
    t_start = time.time()

    initial_count = get_unclassified_count()
    if initial_count is not None:
        print(f"[*] Current unclassified queue in Neon DB: {initial_count} items.")
        if initial_count == 0:
            print("[+] All inbox items are already 100% enriched and classified! Nothing to drain.")
            return
    else:
        print("[*] Queue count unknown. Probing worker once...")

    rounds = 0
    total_processed = 0

    while rounds < MAX_ROUNDS:
        rounds += 1
        print(f"[*] [Round {rounds}/{MAX_ROUNDS}] Triggering Vercel serverless micro-worker (limit=5)...")
        r_start = time.time()
        res = trigger_worker_batch()
        dur = round(time.time() - r_start, 2)

        status = res.get("status", "unknown")
        processed = res.get("processed_count", 0)
        remaining = res.get("remaining_unclassified", None)
        total_processed += processed

        print(f"    -> Result: status={status}, processed={processed}, remaining={remaining} ({dur}s)")

        if status == "noop" or remaining == 0:
            print(f"[+] Queue fully cleared! Total processed in this run: {total_processed} items.")
            break

        if status == "quota_exhausted" or res.get("is_quota_exhausted"):
            print("[!] OpenRouter free daily quota (1,000 req) exhausted. Halting drain gracefully.")
            break

        if status == "error":
            print("[!] Worker error encountered. Pausing 3s before retry...")
            time.sleep(3)
            continue

        # Gentle pause between batches to respect free router rate limits
        time.sleep(1.5)

    elapsed = round(time.time() - t_start, 2)
    print(f"[+] AI Enrichment Drain complete in {elapsed}s (Rounds: {rounds}, Processed: {total_processed}).")

if __name__ == "__main__":
    try:
        drain()
    except Exception as e:
        print(f"[!] Drain encountered unexpected exception: {e}. Exiting cleanly.")
        sys.exit(0)
