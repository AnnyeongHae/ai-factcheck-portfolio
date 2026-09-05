#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/daily_eod_enrichment.py
====================================================================
Daily 23:30 KST End-of-Day Full Batch Enrichment and Audit Engine
- Harvests all pending Gemini Batch API jobs
- Scans inbox for 100% of un-enriched / un-translated items (Zero Left Behind)
- Submits remaining items to Gemini Batch API (models/gemini-3.6-flash)
- Waits and harvests ready batches
- Rebuilds portfolio dashboard, syncs with Neon Postgres Cloud DB
- Records daily completion ledger in logs/daily_eod_report.json
====================================================================
"""

import os
import sys
import json
import glob
import time
from datetime import datetime, timezone, timedelta

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT_DIR, '.env'))
except ImportError:
    pass

sys.path.insert(0, os.path.join(ROOT_DIR, 'tools'))
import batch_manager
from build_dashboard import build_dashboard

KST = timezone(timedelta(hours=9))

def run_daily_eod():
    now_kst = datetime.now(KST)
    print(f"\n{'='*70}")
    print(f"🌙 [Daily 23:30 KST End-of-Day Enrichment Engine]")
    print(f"   Execution Time: {now_kst.strftime('%Y-%m-%d %H:%M:%S KST')}")
    print(f"{'='*70}\n")

    # 1. Harvest already completed batches
    print("[*] Step 1: Harvesting existing Gemini Batch jobs...")
    try:
        harvested_count = batch_manager.harvest_completed_batches()
        print(f"[+] Harvested {harvested_count} items from completed batches.")
    except Exception as e:
        print(f"[-] Harvest warning: {e}")
        harvested_count = 0

    # 2. Scan inbox for ANY un-enriched items (Zero Left Behind Policy)
    print("\n[*] Step 2: Scanning inbox for un-translated / un-enriched items...")
    inbox_files = sorted(glob.glob(os.path.join(ROOT_DIR, 'inbox', '*.json')))
    unenriched_items = []
    enriched_items = []

    for fpath in inbox_files:
        if '_promoted' in fpath or '_rejected' in fpath:
            continue
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                item = json.load(f)
            if item.get('ai_enrichment') and item.get('multilingual'):
                enriched_items.append(item)
            else:
                unenriched_items.append(item)
        except Exception:
            continue

    total_count = len(inbox_files)
    print(f"  - Total Inbox Items: {total_count}")
    print(f"  - Enriched (Translated/Classified): {len(enriched_items)}")
    print(f"  - Un-enriched (Pending Translation): {len(unenriched_items)}")

    submitted_batches = []
    # 3. Enrich ALL remaining un-enriched items in 1-by-1 Real-time Stream Mode
    if unenriched_items:
        print(f"\n[*] Step 3: Enriching ALL {len(unenriched_items)} un-enriched items in 1-by-1 Zero-Cost Stream Mode...")
        try:
            import enrich_inbox_with_ai
            enrich_inbox_with_ai.run_enrichment(limit=0, batch_size=1, provider="openrouter", cooldown=1.0)
            print("[+] OpenRouter Free Router 1-by-1 stream enrichment completed successfully.")
        except Exception as e:
            print(f"[-] OpenRouter enrichment encountered error: {e}")
    else:
        print("\n[+] Step 3: 100% of inbox items are already enriched! No enrichment needed.")

    # 4. Rebuild Portfolio Dashboard & Public Edge
    print("\n[*] Step 5: Compiling Dashboard & Edge Cache...")
    try:
        build_dashboard()
        print("[+] Dashboard rebuild completed.")
    except Exception as e:
        print(f"[-] Dashboard rebuild error: {e}")

    # 6. Save Daily EOD Audit Report
    report_path = os.path.join(ROOT_DIR, 'logs', 'daily_eod_report.json')
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    report = {
        'eod_date': now_kst.strftime('%Y-%m-%d'),
        'timestamp_kst': now_kst.isoformat(),
        'total_inbox': total_count,
        'enriched_count': len(enriched_items),
        'pending_count': len(unenriched_items),
        'submitted_batches': submitted_batches,
        'completion_rate_pct': round((len(enriched_items) / total_count * 100), 1) if total_count > 0 else 100.0
    }
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n[+] Daily 23:30 EOD Audit Report saved to {report_path}")
    print(f"    Completion Rate: {report['completion_rate_pct']}%")
    print(f"{'='*70}\n")

if __name__ == '__main__':
    run_daily_eod()
