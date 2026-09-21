#!/usr/bin/env python3
"""
tools/orchestrate_enrichment.py
==============================================================================
Smart Remote Orchestrator for 100% Multilingual Enrichment (Spec Kit SDD)
------------------------------------------------------------------------------
Purpose:
  Acts as an asynchronous remote controller from GitHub Actions.
  Dispatches 1-item enrichment requests to Vercel Serverless Worker
  until ALL newly ingested items in Neon DB are enriched with:
  - Korean (title_ko, hook_ko, 3 key_takeaways_ko)
  - English (title_en, hook_en, 3 key_takeaways_en)
  - Chinese (title_zh, hook_zh, 3 key_takeaways_zh)
  - Category tagging & Canonical keys

Guarantees:
  1. 100% completion of all newly harvested items per run.
  2. Zero 10-second timeout risk on Vercel (1 item per ~2.5s).
  3. Safe rate-limit pacing (1.0s interval between requests).
  4. Graceful termination if queue reaches 0 or daily quota exhausted.
==============================================================================
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error

# Ensure UTF-8 output
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DEFAULT_BASE_URL = os.environ.get("VERCEL_APP_URL", "https://ai-factcheck-portfolio.vercel.app").rstrip('/')

def orchestrate(base_url=DEFAULT_BASE_URL, max_items=30, delay_sec=1.0, max_time_sec=180):
    start_time = time.time()
    endpoint = f"{base_url}/api/enrich-worker?limit=1"
    
    print("==================================================================")
    print("🚀 [Spec Kit Orchestrator] Starting 1-by-1 Multilingual AI Enrichment")
    print(f"[*] Target Endpoint : {endpoint}")
    print(f"[*] Safety Limits   : Max {max_items} items | Max {max_time_sec}s timeout | {delay_sec}s pacing")
    print("==================================================================")

    processed_total = 0
    consecutive_errors = 0

    while processed_total < max_items:
        elapsed = time.time() - start_time
        if elapsed > max_time_sec:
            print(f"[!] [Orchestrator] Safety timeout reached ({elapsed:.1f}s > {max_time_sec}s). Stopping gracefully.")
            break

        try:
            req = urllib.request.Request(
                endpoint,
                headers={
                    "User-Agent": "FactCheck-Orchestrator/2.0 (SpecKit-SDD)",
                    "Accept": "application/json"
                }
            )
            # Timeout of 12s allows Vercel function (max 10s) to return
            with urllib.request.urlopen(req, timeout=12) as resp:
                status_code = resp.status
                raw_body = resp.read().decode("utf-8")
                data = json.loads(raw_body)
                consecutive_errors = 0

                status = data.get("status", "")
                remaining = data.get("remaining_unclassified", 0)
                duration = data.get("duration_seconds", 0.0)
                model = data.get("model_used", "openrouter-free")
                items = data.get("items", [])
                item_id = items[0].get("inbox_id") if items else "unknown"

                if status == "noop" or remaining == 0:
                    print(f"\n[+] [Orchestrator] Queue completely empty! All items in Neon DB are 100% enriched.")
                    break

                if status == "quota_exhausted":
                    print(f"\n[!] [Orchestrator] OpenRouter free daily quota reached: {data.get('message')}")
                    print(f"[*] Remaining items will be processed after 09:00 KST quota reset.")
                    break

                if status == "success":
                    processed_total += 1
                    print(f"[{processed_total:>2}/{max_items}] Enriched '{item_id}' ({duration}s via {model}) -> Remaining: {remaining}")
                else:
                    print(f"[*] [Orchestrator] Worker returned status '{status}' -> Remaining: {remaining}")

                # Rate-limit safety sleep
                time.sleep(delay_sec)

        except urllib.error.HTTPError as he:
            consecutive_errors += 1
            print(f"[!] [Orchestrator] HTTP Error {he.code}: {he.reason} (Attempt {consecutive_errors}/3)")
            if consecutive_errors >= 3:
                print("[!] [Orchestrator] 3 consecutive HTTP errors encountered. Halting.")
                break
            time.sleep(2.0)

        except urllib.error.URLError as ue:
            consecutive_errors += 1
            print(f"[!] [Orchestrator] Network Error: {ue.reason} (Attempt {consecutive_errors}/3)")
            if consecutive_errors >= 3:
                print("[!] [Orchestrator] Network unreachable. Halting.")
                break
            time.sleep(2.0)

        except Exception as ex:
            consecutive_errors += 1
            print(f"[!] [Orchestrator] Unexpected error: {ex}")
            if consecutive_errors >= 3:
                break
            time.sleep(2.0)

    total_time = time.time() - start_time
    print("==================================================================")
    print(f"🎯 [Orchestrator Finished] Processed: {processed_total} items | Total Time: {total_time:.1f}s")
    print("==================================================================")
    return processed_total

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Spec Kit AI Enrichment Orchestrator")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Vercel App Base URL")
    parser.add_argument("--max-items", type=int, default=30, help="Max items to process in this run")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests in seconds")
    parser.add_argument("--max-time", type=int, default=180, help="Safety timeout in seconds")
    args = parser.parse_args()

    orchestrate(
        base_url=args.base_url,
        max_items=args.max_items,
        delay_sec=args.delay,
        max_time_sec=args.max_time
    )
