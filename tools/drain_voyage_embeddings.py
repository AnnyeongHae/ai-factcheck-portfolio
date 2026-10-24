#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/drain_voyage_embeddings.py
==============================================================================
Direct Python High-Throughput Voyage Embedder Drain (SSOT)
------------------------------------------------------------------------------
Fetches items where `is_classified = TRUE AND embedding IS NULL`,
generates Voyage embeddings (voyage-4-lite, 1024-dim) strictly on English
text (`title_en` + `hook_en`), and writes pgvector embeddings to PostgreSQL.
==============================================================================
"""

import os
import sys
import time
import json
import requests
from typing import List

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
from psycopg2.extras import execute_batch

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT_DIR, '.env.local'))
    load_dotenv(os.path.join(ROOT_DIR, '.env'))
except ImportError:
    pass

VOYAGE_API_URL = "https://api.voyageai.com/v1/embeddings"
MODEL = "voyage-4-lite"
DIMENSION = 1024

def call_voyage_api(texts: List[str], api_key: str) -> List[List[float]]:
    """Direct Voyage API call via requests with connection reuse."""
    payload = {
        "input": texts,
        "model": MODEL,
        "output_dimension": DIMENSION
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "AIFactcheck/1.0 (voyage-drain-requests)"
    }
    resp = requests.post(VOYAGE_API_URL, headers=headers, json=payload, timeout=(10, 30))
    if resp.status_code != 200:
        raise RuntimeError(f"Voyage API Error {resp.status_code}: {resp.text}")
    data = resp.json()
    embeddings = [item["embedding"] for item in sorted(data.get("data", []), key=lambda x: x["index"])]
    return embeddings

def drain_voyage(batch_size: int = 64):
    api_key = os.environ.get("VOYAGE_API_KEY") or os.environ.get("VOYAGEAI_API_KEY")
    if not api_key:
        print("[!] Error: VOYAGE_API_KEY is not set.")
        return False

    conn = get_db_connection()
    if not conn:
        print("[!] DB connection failed.")
        return False

    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) 
        FROM raw_trends_inbox 
        WHERE is_classified = TRUE AND embedding IS NULL;
    """)
    total_unembedded = cur.fetchone()[0]
    cur.close()

    print("==================================================================", flush=True)
    print("🚀 [Voyage Embedder Python Drain] Direct High-Throughput Pipeline", flush=True)
    print(f"[*] Total Unembedded Items: {total_unembedded} | Model: {MODEL} ({DIMENSION}-dim)", flush=True)
    print(f"[*] Batch Size: {batch_size} (Strictly English texts + execute_batch)", flush=True)
    print("==================================================================", flush=True)

    if total_unembedded == 0:
        print("[+] All classified items already have embeddings! Nothing to drain.")
        conn.close()
        return True

    total_embedded = 0
    start_time = time.time()
    batch_num = 1

    while True:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, 
                   COALESCE(raw_payload->>'title_en', title, '') as title_en,
                   COALESCE(raw_payload->>'hook_en', raw_payload->>'hook', '') as hook_en
            FROM raw_trends_inbox 
            WHERE is_classified = TRUE AND embedding IS NULL 
            ORDER BY created_at DESC 
            LIMIT %s;
        """, (batch_size,))
        rows = cur.fetchall()
        cur.close()

        if not rows:
            print("[+] All items are 100% embedded! No unembedded rows remain in DB.")
            break

        texts = []
        for r in rows:
            en = (r[1] or '').strip()
            hook = (r[2] or '').strip()
            # Strictly English title + hook
            text = f"{en} | {hook}".strip() if hook else en
            texts.append(text or "Untitled AI Technology")

        t0 = time.time()
        try:
            embs = call_voyage_api(texts, api_key)
        except Exception as e:
            print(f"[!] Voyage API call failed on batch #{batch_num}: {e}")
            break

        if not embs or len(embs) != len(rows):
            print(f"[!] Mismatch in embeddings count ({len(embs) if embs else 0} vs {len(rows)})")
            break

        # High-performance batch update into PostgreSQL SSOT
        cur = conn.cursor()
        update_params = [
            (f"[{','.join(map(str, embs[idx]))}]", r[0])
            for idx, r in enumerate(rows)
        ]
        execute_batch(cur, """
            UPDATE raw_trends_inbox 
            SET embedding = %s::vector, updated_at = NOW() 
            WHERE id = %s;
        """, update_params, page_size=100)
        conn.commit()
        cur.close()

        total_embedded += len(rows)
        dt = time.time() - t0
        remaining = max(0, total_unembedded - total_embedded)
        print(f"[Batch #{batch_num:>2}] Embedded: {len(rows):>3} items ({dt:.2f}s) | Remaining: {remaining:>4}", flush=True)

        batch_num += 1
        time.sleep(0.2)

    conn.close()
    elapsed = time.time() - start_time
    print("==================================================================")
    print(f"🎉 [Voyage Python Drain Complete] Total Embedded: {total_embedded} in {elapsed:.1f}s")
    print("==================================================================")
    return True

if __name__ == "__main__":
    drain_voyage(batch_size=64)
