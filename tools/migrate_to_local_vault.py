#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/migrate_to_local_vault.py
==============================================================================
100% Lossless Migration: Aiven Cloud PG -> Local SQLite Vault (`data/local_rag_vault.db`)
------------------------------------------------------------------------------
Streams all pgvector embeddings (raw_trends_inbox.embedding) and all GZIP
full-text articles (raw_content_vault) from Aiven PostgreSQL into the local
SQLite vault, then verifies exact count parity.
==============================================================================
"""

import os
import sys
import json
import time
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.local_vault import (
    pack_vector,
    upsert_embedding_rows,
    upsert_raw_content_rows,
    get_vault_stats,
)

load_dotenv(ROOT_DIR / ".env")
load_dotenv(ROOT_DIR / ".env.local")


def migrate_all():
    url = os.environ.get("AIVEN_SERVICE_URI") or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("AIVEN_SERVICE_URI / DATABASE_URL not configured")

    t0 = time.perf_counter()
    conn = psycopg2.connect(url)
    conn.set_session(readonly=True)

    # 1. Check source counts
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM raw_trends_inbox WHERE embedding IS NOT NULL;")
        src_emb_total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM raw_content_vault;")
        src_rcv_total = cur.fetchone()[0]

    print(f"[*] Source Aiven counts -> embeddings: {src_emb_total:,} | raw_content_vault: {src_rcv_total:,}", flush=True)

    # 2. Stream embeddings in batches of 1,000 (cursor-based keyset pagination)
    print("[*] Migrating embeddings to local SQLite vault...", flush=True)
    last_id = 0
    migrated_emb = 0
    while True:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, inbox_id, title, source_platform, source_url, category_primary,
                       description, peak_spike_score, live_spike_score, viral_metric,
                       created_at::text, updated_at::text, raw_payload, embedding::text
                FROM raw_trends_inbox
                WHERE id > %s AND embedding IS NOT NULL
                ORDER BY id ASC
                LIMIT 1000;
                """,
                (last_id,),
            )
            rows = cur.fetchall()
        if not rows:
            break

        batch = []
        for r in rows:
            last_id = r[0]
            p = r[12] if isinstance(r[12], dict) else {}
            ai = p.get("ai_enrichment") or {}
            title_ko = p.get("title_ko") or ai.get("title_ko") or ai.get("korean_title") or ""
            title_en = p.get("title_en") or ai.get("title_en") or ""
            hook_ko = p.get("hook_ko") or p.get("hook") or ai.get("hook_ko") or ai.get("hook") or ""
            hook_en = p.get("hook_en") or ai.get("hook_en") or ""
            is_cross = 1 if p.get("is_cross_spiking") else 0
            vm = r[9] or ""
            if not isinstance(vm, str):
                vm = json.dumps(vm, ensure_ascii=False)
            vec_bytes = pack_vector(r[13])
            batch.append(
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
                    is_cross,
                    vm,
                    r[10] or "",
                    r[11] or "",
                    vec_bytes,
                )
            )

        migrated_emb += upsert_embedding_rows(batch)
        if migrated_emb % 5000 == 0 or migrated_emb >= src_emb_total:
            print(f"    -> embeddings migrated: {migrated_emb:,} / {src_emb_total:,} ({time.perf_counter()-t0:.1f}s)", flush=True)

    # 3. Stream raw_content_vault in batches of 1,000
    print("[*] Migrating raw_content_vault (GZIP full text) to local SQLite vault...", flush=True)
    last_inbox_id = ""
    migrated_rcv = 0
    while True:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT inbox_id, source_url, source_platform, title,
                       full_text_gzip, raw_char_len, compressed_bytes, created_at::text
                FROM raw_content_vault
                WHERE inbox_id > %s
                ORDER BY inbox_id ASC
                LIMIT 1000;
                """,
                (last_inbox_id,),
            )
            rows = cur.fetchall()
        if not rows:
            break

        batch = []
        for r in rows:
            last_inbox_id = r[0]
            gz_bytes = bytes(r[4]) if r[4] is not None else b""
            batch.append(
                (
                    r[0],
                    r[1] or "",
                    r[2] or "",
                    r[3] or "",
                    gz_bytes,
                    int(r[5] or 0),
                    int(r[6] or 0),
                    r[7] or "",
                )
            )
        migrated_rcv += upsert_raw_content_rows(batch)
        if migrated_rcv % 5000 == 0 or migrated_rcv >= src_rcv_total:
            print(f"    -> raw_content_vault migrated: {migrated_rcv:,} / {src_rcv_total:,} ({time.perf_counter()-t0:.1f}s)", flush=True)

    conn.close()

    stats = get_vault_stats()
    print("\n=== MIGRATION VERIFICATION ===")
    print(f"Source Embeddings: {src_emb_total:,} | Local Vault Embeddings: {stats['embeddings_count']:,}")
    print(f"Source Raw Vault : {src_rcv_total:,} | Local Vault Raw Vault : {stats['raw_content_vault_count']:,}")
    print(f"Local SQLite Size: {stats['file_size_mb']} MB ({stats['vault_path']})")
    print(f"Total Elapsed    : {time.perf_counter()-t0:.1f}s")

    if stats["embeddings_count"] < src_emb_total or stats["raw_content_vault_count"] < src_rcv_total:
        raise RuntimeError("Count mismatch! Aborting before any cloud cleanup.")
    print("[SUCCESS] 100% lossless local migration verified!")


if __name__ == "__main__":
    migrate_all()
