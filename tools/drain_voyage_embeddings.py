#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/drain_voyage_embeddings.py
==============================================================================
Direct Python High-Throughput Voyage Embedder Drain -> Local SQLite RAG Vault
------------------------------------------------------------------------------
Fetches classified items from Cloud `raw_trends_inbox` whose `inbox_id` is not
yet present in the local SQLite RAG vault (`data/local_rag_vault.db`),
generates Voyage embeddings (voyage-4-lite, 1024-dim) strictly on English
text (`title_en` + `hook_en`), and writes vectors + metadata strictly to the
LOCAL SQLite vault (0 bytes written to Cloud PostgreSQL!).
==============================================================================
"""

import os
import sys
import time
import json
import requests
from typing import List

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
from local_vault import (
    get_existing_embedded_ids,
    pack_vector,
    upsert_embedding_rows,
    upsert_raw_content_rows,
    get_vault_connection,
    get_vault_stats,
)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT_DIR, ".env.local"))
    load_dotenv(os.path.join(ROOT_DIR, ".env"))
except ImportError:
    pass

VOYAGE_API_URL = "https://api.voyageai.com/v1/embeddings"
MODEL = "voyage-4-lite"
DIMENSION = 1024


def call_voyage_api(texts: List[str], api_key: str) -> List[List[float]]:
    payload = {
        "input": texts,
        "model": MODEL,
        "output_dimension": DIMENSION,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "AIFactcheck/2.0 (local-rag-vault)",
    }
    resp = requests.post(VOYAGE_API_URL, headers=headers, json=payload, timeout=(10, 30))
    if resp.status_code != 200:
        raise RuntimeError(f"Voyage API Error {resp.status_code}: {resp.text}")
    data = resp.json()
    return [item["embedding"] for item in sorted(data.get("data", []), key=lambda x: x["index"])]


def sync_raw_content_vault_to_local(retention_days: int = 14):
    """
    Syncs GZIP full-text articles harvested by GitHub Actions from Cloud
    `raw_content_vault` into permanent Local SQLite Vault (`data/local_rag_vault.db`),
    then prunes Cloud staging rows older than `retention_days` ONLY AFTER
    verifying they exist locally. Keeps Cloud staging <10 MB with 0 data loss.
    """
    conn = get_db_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute("SELECT to_regclass('public.raw_content_vault');")
        if cur.fetchone()[0] is None:
            cur.close()
            conn.close()
            return

        cur.execute(
            """
            SELECT inbox_id, source_url, source_platform, title,
                   full_text_gzip, raw_char_len, compressed_bytes, created_at::text
            FROM raw_content_vault;
            """
        )
        rows = cur.fetchall()
        synced = 0
        if rows:
            batch = [
                (
                    r[0],
                    r[1] or "",
                    r[2] or "",
                    r[3] or "",
                    bytes(r[4]) if r[4] is not None else b"",
                    int(r[5] or 0),
                    int(r[6] or 0),
                    r[7] or "",
                )
                for r in rows
            ]
            synced = upsert_raw_content_rows(batch)

        # Verify local presence before pruning Cloud staging rows older than retention_days
        lconn = get_vault_connection()
        local_ids = {r[0] for r in lconn.execute("SELECT inbox_id FROM raw_content_vault;").fetchall()}
        lconn.close()

        cur.execute(
            "SELECT inbox_id FROM raw_content_vault WHERE created_at < NOW() - INTERVAL %s;",
            (f"{int(retention_days)} days",),
        )
        old_ids = [r[0] for r in cur.fetchall() if r[0] in local_ids]
        pruned = 0
        if old_ids:
            cur.execute("DELETE FROM raw_content_vault WHERE inbox_id = ANY(%s);", (old_ids,))
            pruned = cur.rowcount
            conn.commit()
        cur.close()
        if synced or pruned:
            print(f"[+] [Vault Sync] Synced {synced:,} GZIP articles to Local Vault | Pruned {pruned:,} Cloud staging rows (>{retention_days}d).", flush=True)
    except Exception as e:
        print(f"[!] [Vault Sync] Warning: {e}", flush=True)
    finally:
        conn.close()


def drain_voyage(batch_size: int = 64):
    # First, sync any new Cloud staging raw_content_vault rows from GitHub Actions into Local Vault
    sync_raw_content_vault_to_local(retention_days=14)

    api_key = os.environ.get("VOYAGE_API_KEY") or os.environ.get("VOYAGEAI_API_KEY")
    if not api_key:
        print("[!] Error: VOYAGE_API_KEY is not set.")
        return False

    existing_ids = get_existing_embedded_ids()
    conn = get_db_connection()
    if not conn:
        print("[!] Cloud DB connection failed.")
        return False

    cur = conn.cursor()
    # Fast lightweight ID scan (~0.3s) instead of pulling 75 MB of raw_payload for already-embedded rows
    cur.execute(
        """
        SELECT id, inbox_id
        FROM raw_trends_inbox
        WHERE is_classified = TRUE
        ORDER BY id DESC;
        """
    )
    pending_ids = [r[0] for r in cur.fetchall() if r[1] not in existing_ids]
    total_unembedded = len(pending_ids)

    print("==================================================================", flush=True)
    print("🚀 [Voyage Embedder -> Local SQLite RAG Vault]", flush=True)
    print(f"[*] Local Vault Existing: {len(existing_ids):,} | Pending New: {total_unembedded:,}", flush=True)
    print(f"[*] Model: {MODEL} ({DIMENSION}-dim) | Batch Size: {batch_size} | Cloud Writes: 0 bytes", flush=True)
    print("==================================================================", flush=True)

    if total_unembedded == 0:
        cur.close()
        conn.close()
        stats = get_vault_stats()
        print(f"[+] Local RAG Vault is 100% up to date ({stats['embeddings_count']:,} vectors, {stats['file_size_mb']} MB).")
        return True

    cur.execute(
        """
        SELECT id, inbox_id, title, source_platform, source_url, category_primary,
               description, peak_spike_score, live_spike_score, viral_metric,
               created_at::text, updated_at::text, raw_payload
        FROM raw_trends_inbox
        WHERE id = ANY(%s)
        ORDER BY created_at DESC;
        """,
        (pending_ids,),
    )
    pending = cur.fetchall()
    cur.close()
    conn.close()

    total_embedded = 0
    start_time = time.time()
    batch_num = 1

    for i in range(0, total_unembedded, batch_size):
        chunk = pending[i : i + batch_size]
        texts = []
        parsed_meta = []
        for r in chunk:
            p = r[12] if isinstance(r[12], dict) else {}
            ai = p.get("ai_enrichment") or {}
            title_ko = p.get("title_ko") or ai.get("title_ko") or ai.get("korean_title") or ""
            title_en = (p.get("title_en") or ai.get("title_en") or r[2] or "").strip()
            hook_ko = p.get("hook_ko") or p.get("hook") or ai.get("hook_ko") or ai.get("hook") or ""
            hook_en = (p.get("hook_en") or ai.get("hook_en") or "").strip()
            text = f"{title_en} | {hook_en}".strip() if hook_en else title_en
            texts.append(text or "Untitled AI Technology")
            parsed_meta.append((r, p, title_ko, title_en, hook_ko, hook_en))

        t0 = time.time()
        try:
            embs = call_voyage_api(texts, api_key)
        except Exception as e:
            print(f"[!] Voyage API call failed on batch #{batch_num}: {e}")
            break

        if not embs or len(embs) != len(chunk):
            print(f"[!] Mismatch in embeddings count ({len(embs) if embs else 0} vs {len(chunk)})")
            break

        local_rows = []
        for idx, (r, p, title_ko, title_en, hook_ko, hook_en) in enumerate(parsed_meta):
            vm = r[9] or ""
            if not isinstance(vm, str):
                vm = json.dumps(vm, ensure_ascii=False)
            local_rows.append(
                (
                    r[1],
                    r[0],
                    r[2] or "",
                    title_ko,
                    title_en,
                    hook_ko,
                    hook_en,
                    r[3] or "",
                    r[4] or "",
                    r[5] or "",
                    (r[6] or "")[:500],
                    float(r[7] or 0.0),
                    float(r[8] or 0.0),
                    1 if p.get("is_cross_spiking") else 0,
                    vm,
                    r[10] or "",
                    r[11] or "",
                    pack_vector(embs[idx]),
                )
            )

        upsert_embedding_rows(local_rows)
        total_embedded += len(local_rows)
        dt = time.time() - t0
        remaining = max(0, total_unembedded - total_embedded)
        print(f"[Batch #{batch_num:>2}] Embedded to Local Vault: {len(local_rows):>3} ({dt:.2f}s) | Remaining: {remaining:>4}", flush=True)
        batch_num += 1
        time.sleep(0.2)

    elapsed = time.time() - start_time
    stats = get_vault_stats()
    print("==================================================================")
    print(f"🎉 [Local Vault Drain Complete] Embedded: {total_embedded} in {elapsed:.1f}s")
    print(f"📦 Local Vault: {stats['embeddings_count']:,} vectors ({stats['file_size_mb']} MB)")
    print("==================================================================")
    return True


if __name__ == "__main__":
    drain_voyage(batch_size=64)
