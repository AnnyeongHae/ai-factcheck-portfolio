#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Neon PostgreSQL pgvector Extension & Schema Migration Script
Enables vector extension and adds 512-dim embedding column to raw_trends_inbox.
"""

import os
import sys
import psycopg2


def load_env():
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip("'\"")
                    if k not in os.environ:
                        os.environ[k] = v


load_env()
DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("NEON_KEY") or os.environ.get("NEON_DATABASE_URL")

if not DATABASE_URL:
    print("[!] Error: No DATABASE_URL or NEON_KEY found in environment or .env.", file=sys.stderr)
    sys.exit(1)


def setup_pgvector():
    print(f"[*] Connecting to Neon PostgreSQL...")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()

    try:
        # 1. Enable pgvector extension
        print("[*] 1. Enabling pgvector extension...")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        print("[+] 'vector' extension is active.")

        # 2. Add embedding column to raw_trends_inbox if not exists
        print("[*] 2. Checking and creating 'embedding vector(512)' column on raw_trends_inbox...")
        cursor.execute("""
            ALTER TABLE raw_trends_inbox 
            ADD COLUMN IF NOT EXISTS embedding vector(512);
        """)
        print("[+] 'embedding vector(512)' column ensured on raw_trends_inbox.")

        # 3. Create HNSW index for ultra-fast approximate nearest neighbors search
        print("[*] 3. Ensuring HNSW cosine distance index...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_raw_trends_inbox_embedding_hnsw 
            ON raw_trends_inbox 
            USING hnsw (embedding vector_cosine_ops);
        """)
        print("[+] HNSW index 'idx_raw_trends_inbox_embedding_hnsw' ensured.")

        # Verify
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'raw_trends_inbox' AND column_name = 'embedding';
        """)
        row = cursor.fetchone()
        print(f"[+] Verification: raw_trends_inbox.embedding -> {row}")

    except Exception as e:
        print(f"[!] Migration Error: {e}", file=sys.stderr)
        raise
    finally:
        cursor.close()
        conn.close()
        print("[+] Database connection closed.")


if __name__ == "__main__":
    setup_pgvector()
