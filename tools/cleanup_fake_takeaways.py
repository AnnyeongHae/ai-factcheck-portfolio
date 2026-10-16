#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/cleanup_fake_takeaways.py
==============================================================================
Purges boilerplate fake 3-line takeaways from raw_payload across all rows
in raw_trends_inbox (Aiven PostgreSQL SSOT).
==============================================================================
"""

import os
import sys
import json
import time

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

def clean_payload_takeaways(payload: dict) -> tuple[dict, bool]:
    if not isinstance(payload, dict):
        return payload, False

    modified = False
    keys_to_remove = [
        "key_takeaways", "key_takeaways_ko", "key_takeaways_en", "key_takeaways_zh",
        "takeaways_ko", "takeaways_en", "takeaways_zh"
    ]
    for k in keys_to_remove:
        if k in payload:
            del payload[k]
            modified = True

    # Clean inside ai_enrichment
    ai = payload.get("ai_enrichment")
    if isinstance(ai, dict):
        for k in keys_to_remove:
            if k in ai:
                del ai[k]
                modified = True
        ai_multi = ai.get("multilingual")
        if isinstance(ai_multi, dict):
            for lang in ["ko", "en", "zh"]:
                if isinstance(ai_multi.get(lang), dict) and "key_takeaways" in ai_multi[lang]:
                    del ai_multi[lang]["key_takeaways"]
                    modified = True

    # Clean inside multilingual
    multi = payload.get("multilingual")
    if isinstance(multi, dict):
        for lang in ["ko", "en", "zh"]:
            if isinstance(multi.get(lang), dict) and "key_takeaways" in multi[lang]:
                del multi[lang]["key_takeaways"]
                modified = True

    return payload, modified

def main():
    print("=" * 65)
    print("🧹 [Data Purge] Cleaning fake 3-line takeaways from PostgreSQL SSOT")
    print("=" * 65)

    conn = get_db_connection()
    if not conn:
        print("[!] DB connection failed.")
        return 1

    cur = conn.cursor()
    cur.execute("SELECT id, raw_payload FROM raw_trends_inbox WHERE raw_payload::text LIKE '%key_takeaways%';")
    rows = cur.fetchall()
    print(f"[*] Found {len(rows):,} rows containing 'key_takeaways' in raw_payload.")

    batch_size = 500
    updated_count = 0
    t0 = time.time()

    for i in range(0, len(rows), batch_size):
        chunk = rows[i:i + batch_size]
        updates = []
        for r_id, r_payload in chunk:
            p = r_payload if isinstance(r_payload, dict) else (json.loads(r_payload) if r_payload else {})
            cleaned, modified = clean_payload_takeaways(p)
            if modified:
                updates.append((json.dumps(cleaned, ensure_ascii=False), r_id))

        if updates:
            import psycopg2.extras
            psycopg2.extras.execute_batch(
                cur,
                "UPDATE raw_trends_inbox SET raw_payload = %s::jsonb WHERE id = %s;",
                updates,
                page_size=500
            )
            conn.commit()
            updated_count += len(updates)
            print(f"  ✓ Purged {updated_count:,}/{len(rows):,} rows ({time.time() - t0:.1f}s)...")

    cur.close()
    conn.close()

    print("=" * 65)
    print(f"🎉 [Purge Complete] Successfully cleaned {updated_count:,} rows in {time.time() - t0:.1f}s!")
    print("=" * 65)
    return 0

if __name__ == "__main__":
    sys.exit(main())
