#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/drain_voyage_embeddings.py
==============================================================================
Direct Python High-Throughput Voyage Embedder Drain (SSOT)
------------------------------------------------------------------------------
Fetches remaining items with `embedding IS NULL` in batches of 100,
generates Voyage embeddings (voyage-4-lite, 1024-dim),
and writes pgvector embeddings to PostgreSQL SSOT.
==============================================================================
"""

import os
import sys
import time
from datetime import datetime

# UTF-8 support on Windows
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
tools_dir = os.path.join(ROOT_DIR, "tools")
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

from db_config import get_db_connection
from voyage_embedder import get_embeddings

def drain_voyage(batch_size: int = 100):
    conn = get_db_connection()
    if not conn:
        print("[!] DB connection failed.")
        return False

    print("==================================================================", flush=True)
    print("🚀 [Voyage Embedder Python Drain] Starting Full Vector Drain Loop", flush=True)
    print(f"[*] Batch Size: {batch_size} | Model: voyage-4-lite (1024-dim)", flush=True)
    print("==================================================================", flush=True)

    total_embedded = 0
    start_time = time.time()
    batch_num = 1

    while True:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, 
                   COALESCE(raw_payload->>'title_en', title, '') as title_en,
                   COALESCE(raw_payload->>'hook_en', raw_payload->>'hook', '') as hook_en,
                   COALESCE(raw_payload->'ai_enrichment'->>'summary_en', raw_payload->>'description', '') as summary_en
            FROM raw_trends_inbox 
            WHERE is_classified = TRUE AND embedding IS NULL 
            ORDER BY created_at DESC 
            LIMIT %s;
        """, (batch_size,))
        rows = cur.fetchall()

        if not rows:
            print("[+] All items are 100% embedded! No unembedded rows remain in DB.")
            cur.close()
            break

        texts = []
        for r in rows:
            en = (r[1] or '').strip()
            hook = (r[2] or '').strip()
            summary = (r[3] or '').strip()
            parts = [en] if en else []
            if hook:
                parts.append(f"Hook: {hook}")
            if summary:
                parts.append(f"Summary: {summary[:300]}")
            texts.append(" | ".join(parts) or "Untitled")

        t0 = time.time()
        try:
            embs = get_embeddings(texts, model="voyage-4-lite", dimension=1024)
        except Exception as e:
            print(f"[!] Voyage API call failed on batch #{batch_num}: {e}")
            cur.close()
            break

        if not embs or len(embs) != len(rows):
            print(f"[!] Mismatch in embeddings count ({len(embs) if embs else 0} vs {len(rows)})")
            cur.close()
            break

        # Batch update into PostgreSQL
        for idx, r in enumerate(rows):
            vec_str = f"[{','.join(map(str, embs[idx]))}]"
            cur.execute("""
                UPDATE raw_trends_inbox 
                SET embedding = %s::vector, updated_at = NOW() 
                WHERE id = %s;
            """, (vec_str, r[0]))

        conn.commit()

        cur.execute("SELECT COUNT(*) FROM raw_trends_inbox WHERE embedding IS NULL;")
        remaining = cur.fetchone()[0]
        cur.close()

        total_embedded += len(rows)
        dt = time.time() - t0
        print(f"[Batch #{batch_num:>2}] Embedded: {len(rows):>3} items ({dt:.2f}s) | Remaining Unembedded: {remaining:>4}", flush=True)

        batch_num += 1
        time.sleep(0.3)

    conn.close()
    elapsed = time.time() - start_time
    print("==================================================================")
    print(f"🎉 [Voyage Python Drain Complete] Total Embedded: {total_embedded} in {elapsed:.1f}s")
    print("==================================================================")
    return True

if __name__ == "__main__":
    drain_voyage(batch_size=100)
