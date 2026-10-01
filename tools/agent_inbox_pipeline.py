#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/agent_inbox_pipeline.py
==============================================================================
Antigravity Local Agent-Assisted Inbox Enrichment Pipeline (SSOT Aiven DB)
------------------------------------------------------------------------------
Purpose:
  Enables high-throughput, zero-cost AI enrichment of unclassified inbox items
  by pairing local Aiven PostgreSQL DB access with Antigravity / LLM reasoning.
  Bypasses external serverless rate limits and timeouts.

Commands:
  python tools/agent_inbox_pipeline.py --status
  python tools/agent_inbox_pipeline.py --fetch 50 [--out data/agent_inbox_batch.json]
  python tools/agent_inbox_pipeline.py --apply data/agent_inbox_enriched.json
==============================================================================
"""

import os
import sys
import json
import argparse
import re
from datetime import datetime, timezone
from pathlib import Path

# Force UTF-8 stdout
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "tools"))

from db_config import get_db_connection, get_db_info

VALID_TIER1_CATEGORIES = [
    'TECH_COMPUTING', 'SCIENCE_RESEARCH', 'ECONOMY_FINANCE',
    'POLITICS_POLICY', 'LAW_CRIME_JUSTICE', 'CULTURE_HUMANITIES'
]

VALID_PRIMARY_CATEGORIES = [
    'INFERENCE_OPT', 'AGENTS_DEVTOOLS', 'MULTIMODAL_AI', 'FOUNDATION_MODELS',
    'INFRA_RAG_SECURITY', 'DEEP_SCIENCE_SPACE', 'MACRO_GLOBAL_BIZ',
    'CIVIC_CRIME_INCIDENT', 'HISTORY_LIFE_CULTURE', 'INDUSTRY_TRENDS'
]

def check_status():
    conn = get_db_connection()
    if not conn:
        print("[!] Error: Could not connect to database.")
        return 1
    
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM raw_trends_inbox;")
    total = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM raw_trends_inbox WHERE is_classified = TRUE;")
    classified = cur.fetchone()[0]
    
    unclassified = total - classified
    pct = (classified / total * 100) if total > 0 else 0
    
    info = get_db_info()
    print("=" * 60)
    print(f"📊 Aiven PostgreSQL Inbox Status ({info.get('provider', 'DB')})")
    print("=" * 60)
    print(f" • Total Inbox Items:      {total:,} 건")
    print(f" • Classified & Enriched:  {classified:,} 건 ({pct:.1f}%)")
    print(f" • Pending AI Enrichment:  {unclassified:,} 건")
    print("=" * 60)
    
    if unclassified > 0:
        cur.execute("""
            SELECT id, inbox_id, title, source_platform, created_at 
            FROM raw_trends_inbox 
            WHERE is_classified = FALSE 
            ORDER BY created_at DESC 
            LIMIT 5;
        """)
        rows = cur.fetchall()
        print("🔍 Next 5 Pending Items:")
        for r in rows:
            print(f"   [{r[0]}] ({r[3]}) {r[2][:70]}")
    
    conn.close()
    return 0

def fetch_batch(limit=50, out_path="data/agent_inbox_batch.json"):
    conn = get_db_connection()
    if not conn:
        print("[!] Error: Could not connect to database.")
        return 1
    
    cur = conn.cursor()
    cur.execute("""
        SELECT id, inbox_id, title, source_platform, source_url, created_at, raw_payload
        FROM raw_trends_inbox
        WHERE is_classified = FALSE
        ORDER BY created_at DESC
        LIMIT %s;
    """, (limit,))
    rows = cur.fetchall()
    
    if not rows:
        print("✨ All items in raw_trends_inbox are already classified and enriched! (0 remaining)")
        conn.close()
        return 0
    
    items = []
    for r in rows:
        r_id, r_inbox_id, r_title, r_platform, r_url, r_created_at, r_payload = r
        payload = r_payload if isinstance(r_payload, dict) else (json.loads(r_payload) if r_payload else {})
        items.append({
            "id": r_id,
            "inbox_id": r_inbox_id or str(r_id),
            "title": r_title,
            "source_platform": r_platform,
            "source_url": r_url,
            "created_at": r_created_at.isoformat() if hasattr(r_created_at, 'isoformat') else str(r_created_at),
            "existing_payload": payload
        })
    
    conn.close()
    
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Successfully fetched {len(items)} unclassified items from DB -> {out_path}")
    print(f"📌 Instructions: Process this batch with high-quality KO/EN/ZH translations and save to enriched JSON.")
    return 0

def apply_enriched_batch(in_path="data/agent_inbox_enriched.json", model_name="antigravity-local-agent"):
    in_file = Path(in_path)
    if not in_file.exists():
        print(f"[!] Error: File not found: {in_path}")
        return 1
    
    with open(in_file, "r", encoding="utf-8") as f:
        enriched_list = json.load(f)
    
    if not isinstance(enriched_list, list) or len(enriched_list) == 0:
        print("[!] Error: Input file must be a non-empty JSON array.")
        return 1
    
    conn = get_db_connection()
    if not conn:
        print("[!] Error: Could not connect to database.")
        return 1
    
    cur = conn.cursor()
    applied_count = 0
    now_iso = datetime.now(timezone.utc).isoformat()
    t0 = datetime.now()
    
    print(f"🚀 Applying {len(enriched_list)} enriched items to Aiven PostgreSQL...")
    
    for item in enriched_list:
        db_id = item.get("id")
        if not db_id:
            continue
        
        # Load existing payload from DB to avoid overwriting metadata
        cur.execute("SELECT raw_payload, inbox_id FROM raw_trends_inbox WHERE id = %s;", (db_id,))
        row = cur.fetchone()
        if not row:
            continue
        
        raw_payload = row[0] if isinstance(row[0], dict) else (json.loads(row[0]) if row[0] else {})
        r_inbox_id = row[1] or str(db_id)
        
        title_ko = (item.get("title_ko") or item.get("title") or "").strip()
        title_en = (item.get("title_en") or item.get("title") or "").strip()
        title_zh = (item.get("title_zh") or item.get("title") or "").strip()
        
        hook_ko = (item.get("hook_ko") or item.get("hook") or title_ko).strip()
        hook_en = (item.get("hook_en") or title_en).strip()
        hook_zh = (item.get("hook_zh") or title_zh).strip()
        
        takeaways_ko = item.get("key_takeaways_ko") or item.get("key_takeaways") or [hook_ko]
        takeaways_en = item.get("key_takeaways_en") or [hook_en]
        takeaways_zh = item.get("key_takeaways_zh") or [hook_zh]
        
        item_type = item.get("item_type") or "TECH"
        t1_cat = item.get("tier1_category") or "TECH_COMPUTING"
        prim_cat = item.get("category_primary") or item.get("tier2_category") or "INDUSTRY_TRENDS"
        art_type = item.get("artifact_type") or "article"
        
        canonical_story_key = item.get("canonical_story_key") or raw_payload.get("canonical_story_key")
        canonical_tech_entity = item.get("canonical_tech_entity") or raw_payload.get("canonical_tech_entity")
        
        source_lang = (item.get("source_lang") or raw_payload.get("ai_enrichment", {}).get("source_lang") or "EN").upper()
        
        # Merge into raw_payload
        raw_payload.update({
            "source_lang": source_lang,
            "title_ko": title_ko,
            "title_en": title_en,
            "title_zh": title_zh,
            "hook": hook_ko,
            "hook_ko": hook_ko,
            "hook_en": hook_en,
            "hook_zh": hook_zh,
            "description_ko": hook_ko,
            "description_en": hook_en,
            "description_zh": hook_zh,
            "key_takeaways": takeaways_ko,
            "key_takeaways_ko": takeaways_ko,
            "key_takeaways_en": takeaways_en,
            "key_takeaways_zh": takeaways_zh,
            "category_type": item_type,
            "item_type": item_type,
            "category_primary": prim_cat,
            "tier1_category": t1_cat,
            "tier2_category": prim_cat,
            "artifact_type": art_type,
            "canonical_story_key": canonical_story_key,
            "canonical_tech_entity": canonical_tech_entity,
            "multilingual": {
                "ko": {"title": title_ko, "hook": hook_ko, "key_takeaways": takeaways_ko},
                "en": {"title": title_en, "hook": hook_en, "key_takeaways": takeaways_en},
                "zh": {"title": title_zh, "hook": hook_zh, "key_takeaways": takeaways_zh}
            },
            "ai_enrichment": {
                "id": r_inbox_id,
                "source_lang": source_lang,
                "type_classification": item_type,
                "category_primary": prim_cat,
                "tier1_category": t1_cat,
                "tier2_category": prim_cat,
                "artifact_type": art_type,
                "canonical_story_key": canonical_story_key,
                "canonical_tech_entity": canonical_tech_entity,
                "korean_title": title_ko,
                "hook": hook_ko,
                "key_takeaways": takeaways_ko,
                "takeaways_ko": takeaways_ko,
                "takeaways_en": takeaways_en,
                "takeaways_zh": takeaways_zh,
                "multilingual": {
                    "ko": {"title": title_ko, "hook": hook_ko, "key_takeaways": takeaways_ko},
                    "en": {"title": title_en, "hook": hook_en, "key_takeaways": takeaways_en},
                    "zh": {"title": title_zh, "hook": hook_zh, "key_takeaways": takeaways_zh}
                },
                "enriched_by_model": model_name,
                "enriched_at": now_iso
            }
        })
        
        cur.execute("""
            UPDATE raw_trends_inbox
            SET is_classified = TRUE,
                category_primary = %s,
                item_type = %s,
                raw_payload = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s;
        """, (prim_cat, item_type, json.dumps(raw_payload, ensure_ascii=False), db_id))
        
        applied_count += 1
    
    conn.commit()
    dur = (datetime.now() - t0).total_seconds()
    
    # Check remaining count
    cur.execute("SELECT COUNT(*) FROM raw_trends_inbox WHERE is_classified = FALSE;")
    remaining_unclassified = cur.fetchone()[0]
    
    # Log to vercel_worker_logs for dashboard telemetry sync
    cur.execute("""
        INSERT INTO vercel_worker_logs (worker_name, model_used, processed_count, duration_seconds, remaining_count, status)
        VALUES ('Antigravity Local Agent Pipeline', %s, %s, %s, %s, 'SUCCESS');
    """, (model_name, applied_count, dur, remaining_unclassified))
    conn.commit()
    conn.close()
    
    print(f"\n🎉 Successfully applied {applied_count} items in {dur:.2f}s!")
    print(f"📊 Remaining Unclassified Items in DB: {remaining_unclassified:,} 건")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Antigravity Local Agent Inbox Pipeline")
    parser.add_argument("--status", action="store_true", help="Show current DB inbox classification status")
    parser.add_argument("--fetch", type=int, default=0, help="Fetch N unclassified items to JSON for agent processing")
    parser.add_argument("--out", type=str, default="data/agent_inbox_batch.json", help="Path to write fetched items")
    parser.add_argument("--apply", type=str, default="", help="Path to enriched JSON file to apply to DB")
    parser.add_argument("--model", type=str, default="antigravity-local-agent", help="Model name identifier")
    
    args = parser.parse_args()
    
    if args.status:
        sys.exit(check_status())
    elif args.fetch > 0:
        sys.exit(fetch_batch(args.fetch, args.out))
    elif args.apply:
        sys.exit(apply_enriched_batch(args.apply, args.model))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
