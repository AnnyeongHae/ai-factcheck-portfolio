#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/local_vault.py
==============================================================================
Local Intelligence Vault (SQLite + NumPy Vector Store & GZIP Raw Content Vault)
------------------------------------------------------------------------------
Keeps heavy 1024-dim Voyage embeddings (~115 MB) and GZIP full-text articles
(~28 MB) strictly on the local machine (`data/local_rag_vault.db`, gitignored)
so the Cloud Aiven PostgreSQL stays ultra-light (<100 MB) for Korean summaries
and verified factchecks only.
==============================================================================
"""

import os
import json
import gzip
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_VAULT_PATH = ROOT_DIR / "data" / "local_rag_vault.db"
VOYAGE_DIM = 1024


def get_vault_path() -> Path:
    custom = os.environ.get("LOCAL_RAG_VAULT_PATH")
    p = Path(custom) if custom else DEFAULT_VAULT_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def get_vault_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else get_vault_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    init_vault_schema(conn)
    return conn


def init_vault_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS embeddings (
            inbox_id TEXT PRIMARY KEY,
            pg_id INTEGER UNIQUE,
            title TEXT,
            title_ko TEXT,
            title_en TEXT,
            hook_ko TEXT,
            hook_en TEXT,
            source_platform TEXT,
            source_url TEXT,
            category_primary TEXT,
            description TEXT,
            peak_spike_score REAL DEFAULT 0.0,
            live_spike_score REAL DEFAULT 0.0,
            is_cross_spiking INTEGER DEFAULT 0,
            viral_metric TEXT,
            created_at TEXT,
            updated_at TEXT,
            vector BLOB NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_local_emb_pg_id ON embeddings(pg_id);
        CREATE INDEX IF NOT EXISTS idx_local_emb_created ON embeddings(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_local_emb_category ON embeddings(category_primary);

        CREATE TABLE IF NOT EXISTS raw_content_vault (
            inbox_id TEXT PRIMARY KEY,
            source_url TEXT,
            source_platform TEXT,
            title TEXT,
            full_text_gzip BLOB,
            raw_char_len INTEGER,
            compressed_bytes INTEGER,
            created_at TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_local_rcv_created ON raw_content_vault(created_at DESC);
        """
    )
    conn.commit()


def pack_vector(vec: Any) -> bytes:
    """Pack a list/array or pgvector string '[0.1,0.2,...]' into float32 bytes."""
    if isinstance(vec, (bytes, bytearray, memoryview)):
        return bytes(vec)
    if isinstance(vec, str):
        arr = np.fromstring(vec.strip("[] "), sep=",", dtype=np.float32)
    else:
        arr = np.asarray(vec, dtype=np.float32)
    if arr.size != VOYAGE_DIM:
        raise ValueError(f"Expected vector dim {VOYAGE_DIM}, got {arr.size}")
    return arr.tobytes()


def unpack_vector(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)


def upsert_embedding_rows(rows: List[Tuple], db_path: Optional[Path] = None) -> int:
    if not rows:
        return 0
    conn = get_vault_connection(db_path)
    try:
        conn.executemany(
            """
            INSERT INTO embeddings (
                inbox_id, pg_id, title, title_ko, title_en, hook_ko, hook_en,
                source_platform, source_url, category_primary, description,
                peak_spike_score, live_spike_score, is_cross_spiking, viral_metric,
                created_at, updated_at, vector
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(inbox_id) DO UPDATE SET
                pg_id = COALESCE(excluded.pg_id, embeddings.pg_id),
                title = excluded.title,
                title_ko = COALESCE(NULLIF(excluded.title_ko, ''), embeddings.title_ko),
                title_en = COALESCE(NULLIF(excluded.title_en, ''), embeddings.title_en),
                hook_ko = COALESCE(NULLIF(excluded.hook_ko, ''), embeddings.hook_ko),
                hook_en = COALESCE(NULLIF(excluded.hook_en, ''), embeddings.hook_en),
                source_platform = excluded.source_platform,
                source_url = excluded.source_url,
                category_primary = excluded.category_primary,
                description = excluded.description,
                peak_spike_score = MAX(COALESCE(embeddings.peak_spike_score, 0), COALESCE(excluded.peak_spike_score, 0)),
                live_spike_score = excluded.live_spike_score,
                is_cross_spiking = MAX(COALESCE(embeddings.is_cross_spiking, 0), COALESCE(excluded.is_cross_spiking, 0)),
                viral_metric = excluded.viral_metric,
                updated_at = excluded.updated_at,
                vector = excluded.vector;
            """,
            rows,
        )
        conn.commit()
        return len(rows)
    finally:
        conn.close()


def upsert_raw_content_rows(rows: List[Tuple], db_path: Optional[Path] = None) -> int:
    if not rows:
        return 0
    conn = get_vault_connection(db_path)
    try:
        conn.executemany(
            """
            INSERT INTO raw_content_vault (
                inbox_id, source_url, source_platform, title,
                full_text_gzip, raw_char_len, compressed_bytes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(inbox_id) DO UPDATE SET
                full_text_gzip = CASE
                    WHEN excluded.raw_char_len > COALESCE(raw_content_vault.raw_char_len, 0)
                    THEN excluded.full_text_gzip
                    ELSE raw_content_vault.full_text_gzip
                END,
                raw_char_len = MAX(COALESCE(raw_content_vault.raw_char_len, 0), excluded.raw_char_len),
                compressed_bytes = CASE
                    WHEN excluded.raw_char_len > COALESCE(raw_content_vault.raw_char_len, 0)
                    THEN excluded.compressed_bytes
                    ELSE raw_content_vault.compressed_bytes
                END;
            """,
            rows,
        )
        conn.commit()
        return len(rows)
    finally:
        conn.close()


def get_existing_embedded_ids(db_path: Optional[Path] = None) -> set:
    conn = get_vault_connection(db_path)
    try:
        cur = conn.execute("SELECT inbox_id FROM embeddings;")
        return {r[0] for r in cur.fetchall()}
    finally:
        conn.close()


def get_raw_content_text(inbox_id: str, db_path: Optional[Path] = None) -> Optional[str]:
    conn = get_vault_connection(db_path)
    try:
        cur = conn.execute("SELECT full_text_gzip FROM raw_content_vault WHERE inbox_id = ?;", (inbox_id,))
        row = cur.fetchone()
        if not row or not row[0]:
            return None
        return gzip.decompress(row[0]).decode("utf-8", errors="replace")
    finally:
        conn.close()


_VECTOR_CACHE: Dict[str, Any] = {"mtime": 0.0, "path": "", "rows": [], "vecs": None, "norms": None}


def _load_cached_vectors(db_path: Optional[Path] = None):
    path = Path(db_path) if db_path else get_vault_path()
    mtime = path.stat().st_mtime if path.exists() else 0.0
    if _VECTOR_CACHE["vecs"] is not None and _VECTOR_CACHE["path"] == str(path) and _VECTOR_CACHE["mtime"] == mtime:
        return _VECTOR_CACHE["rows"], _VECTOR_CACHE["vecs"], _VECTOR_CACHE["norms"]

    conn = get_vault_connection(path)
    try:
        rows = conn.execute(
            """
            SELECT pg_id, inbox_id, title, title_ko, title_en, hook_ko, hook_en,
                   source_platform, source_url, category_primary, description,
                   peak_spike_score, live_spike_score, is_cross_spiking, viral_metric,
                   created_at, vector
            FROM embeddings;
            """
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        return [], None, None

    vecs = np.vstack([np.frombuffer(r[16], dtype=np.float32) for r in rows])
    norms = np.linalg.norm(vecs, axis=1)
    norms[norms == 0] = 1.0
    meta_rows = [r[:16] for r in rows]
    _VECTOR_CACHE.update({"mtime": mtime, "path": str(path), "rows": meta_rows, "vecs": vecs, "norms": norms})
    return meta_rows, vecs, norms


def search_local_vectors(
    query_vec: List[float],
    top_k: int = 50,
    platform: Optional[str] = None,
    category: Optional[str] = None,
    min_similarity: float = 0.30,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Ultra-fast in-memory NumPy cosine similarity search over local SQLite vault.
    ~20-30ms (warm) for 30,000 x 1024-dim float32 vectors, 0 Cloud DB load.
    """
    q = np.asarray(query_vec, dtype=np.float32)
    q_norm = np.linalg.norm(q)
    if q_norm == 0:
        return []
    q = q / q_norm

    meta_rows, vecs, norms = _load_cached_vectors(db_path)
    if vecs is None or not meta_rows:
        return []

    sims = (vecs @ q) / norms
    if platform or category:
        plat_l = platform.lower() if platform else None
        mask = np.ones(len(meta_rows), dtype=bool)
        for idx, r in enumerate(meta_rows):
            if plat_l and plat_l not in (r[7] or "").lower():
                mask[idx] = False
            elif category and (r[9] or "") != category:
                mask[idx] = False
        sims = np.where(mask, sims, -1.0)

    k = min(top_k, len(meta_rows))
    if k < len(meta_rows):
        top_idx = np.argpartition(sims, -k)[-k:]
        top_idx = top_idx[np.argsort(sims[top_idx])[::-1]]
    else:
        top_idx = np.argsort(sims)[::-1]

    results = []
    for idx in top_idx:
        sim = float(sims[idx])
        if sim < min_similarity:
            continue
        r = meta_rows[idx]
        results.append(
            {
                "id": r[0] or 0,
                "inbox_id": r[1],
                "title": r[2] or "",
                "title_ko": r[3] or "",
                "title_en": r[4] or "",
                "hook_ko": r[5] or "",
                "hook_en": r[6] or "",
                "platform": r[7] or "",
                "url": r[8] or "",
                "category": r[9] or "",
                "description": r[10] or "",
                "peak_score": float(r[11] or 0.0),
                "live_score": float(r[12] or 0.0),
                "is_cross_spiking": bool(r[13]),
                "viral_metric": r[14] or "",
                "created_at": r[15],
                "similarity": sim,
            }
        )
    return results


def get_vault_stats(db_path: Optional[Path] = None) -> Dict[str, Any]:
    path = Path(db_path) if db_path else get_vault_path()
    conn = get_vault_connection(path)
    try:
        emb_cnt = conn.execute("SELECT COUNT(*) FROM embeddings;").fetchone()[0]
        rcv_cnt = conn.execute("SELECT COUNT(*) FROM raw_content_vault;").fetchone()[0]
        size_mb = round(path.stat().st_size / (1024 * 1024), 2) if path.exists() else 0.0
        return {
            "vault_path": str(path),
            "embeddings_count": emb_cnt,
            "raw_content_vault_count": rcv_cnt,
            "file_size_mb": size_mb,
        }
    finally:
        conn.close()
