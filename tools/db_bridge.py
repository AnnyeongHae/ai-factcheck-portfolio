#!/usr/bin/env python3
"""
Neon Serverless Postgres Enterprise Cloud Bridge (2026 SOTA Framework - v6.5)
지속 가능성(Sustainability) 기반의 2계층 데이터베이스 연동 도구
- Tier 1: Ingestion & Raw Staging (raw_trends_inbox)
- Tier 2: Verified Fact-Check Knowledge & Alternatives (verified_factchecks, claims, alternatives, signals, unit_economics)
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
import time

# Ensure UTF-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def load_env_db_url():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(base_dir, ".env")
    
    # 1. Check existing environment
    db_url = os.environ.get("DATABASE_URL") or os.environ.get("NEON_KEY") or os.environ.get("NEON_DATABASE_URL")
    if db_url:
        return db_url

    # 2. Parse .env file manually
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("NEON_KEY=") or line.startswith("DATABASE_URL="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val:
                            return val
        except Exception:
            pass
    return None

def get_db_connection():
    db_url = load_env_db_url()
    if not db_url:
        print("[!] Note: 'NEON_KEY' or 'DATABASE_URL' not found in .env or environment.")
        return None

    try:
        import psycopg2
        conn = psycopg2.connect(db_url)
        return conn
    except ImportError:
        print("[!] Warning: 'psycopg2' module not installed. Installing psycopg2-binary...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "psycopg2-binary"], check=True)
        import psycopg2
        return psycopg2.connect(db_url)
    except Exception as e:
        print(f"[!] Error: Failed to connect to Neon Postgres: {e}")
        return None

def compute_fingerprint(url: str, title: str = "") -> str:
    norm = url.lower().strip()
    norm = re.sub(r'https?://(www\.)?', '', norm)
    norm = norm.rstrip('/')
    return hashlib.sha256(norm.encode('utf-8')).hexdigest()

def init_schema(clean=True):
    conn = get_db_connection()
    if not conn: return
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    schema_path = os.path.join(base_dir, "configs", "schema_neon.sql")
    if os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as f:
            sql = f.read()
        try:
            with conn.cursor() as cur:
                if clean:
                    cur.execute("""
                        DROP TABLE IF EXISTS factcheck_audit_logs CASCADE;
                        DROP TABLE IF EXISTS factcheck_unit_economics CASCADE;
                        DROP TABLE IF EXISTS factcheck_community_signals CASCADE;
                        DROP TABLE IF EXISTS factcheck_alternatives CASCADE;
                        DROP TABLE IF EXISTS factcheck_atomic_claims CASCADE;
                        DROP TABLE IF EXISTS verified_factchecks CASCADE;
                        DROP TABLE IF EXISTS trend_cross_posts CASCADE;
                        DROP TABLE IF EXISTS raw_trends_inbox CASCADE;
                        DROP TABLE IF EXISTS harvest_source_metrics CASCADE;
                        DROP TABLE IF EXISTS harvest_runs CASCADE;
                    """)
                cur.execute(sql)
            conn.commit()
            print("[+] Successfully initialized Sustainable Neon Postgres tables, indexes, and triggers!")
        except Exception as e:
            print(f"[!] Schema initialization failed: {e}")
        finally:
            conn.close()

def push_inbox_to_neon(full_sync=False):
    conn = get_db_connection()
    if not conn: return

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    inbox_dir = os.path.join(base_dir, "inbox")
    
    count = 0
    now_ts = time.time()
    twenty_four_hours = 86400

    with conn.cursor() as cur:
        for f in sorted(os.listdir(inbox_dir)):
            if f.endswith(".json"):
                path = os.path.join(inbox_dir, f)
                # Incremental Optimization: sync only if modified within 24 hours unless full_sync
                if not full_sync:
                    mtime = os.path.getmtime(path)
                    if (now_ts - mtime) > twenty_four_hours:
                        continue

                try:
                    with open(path, "r", encoding="utf-8") as fp:
                        it = json.load(fp)
                    
                    inbox_id = it.get("inbox_id", f.replace(".json", ""))
                    source_url = it.get("source_url", "")
                    fp_hash = compute_fingerprint(source_url, it.get("title", ""))
                    
                    sql = """
                    INSERT INTO raw_trends_inbox (
                        inbox_id, source_fingerprint, source_platform, source_url, title, item_type,
                        description, viral_metric, matched_user_domains, raw_payload, triage_status, harvested_date
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (source_fingerprint) DO UPDATE SET
                        viral_metric = EXCLUDED.viral_metric,
                        description = EXCLUDED.description,
                        updated_at = NOW();
                    """
                    cur.execute(sql, (
                        inbox_id,
                        fp_hash,
                        it.get("source_platform", "Web"),
                        source_url,
                        it.get("title", ""),
                        it.get("type", "repo"),
                        it.get("description", ""),
                        it.get("viral_metric", ""),
                        json.dumps(it.get("matched_user_domains", [])),
                        json.dumps(it),
                        it.get("status", "PENDING_REVIEW"),
                        it.get("harvested_date", datetime.date.today().isoformat())
                    ))
                    count += 1
                except Exception as e:
                    conn.rollback()
                    print(f"[!] Error inserting {f}: {e}")
    conn.commit()
    conn.close()
    print(f"[+] Successfully pushed {count} inbox candidates to Neon Postgres DB (Tier 1 Staging)!")

def push_factchecks_to_neon():
    conn = get_db_connection()
    if not conn: return

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    inv_dir = os.path.join(base_dir, "investigations")
    
    count = 0
    with conn.cursor() as cur:
        for d in sorted(os.listdir(inv_dir)):
            meta_path = os.path.join(inv_dir, d, "metadata.json")
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as fp:
                        m = json.load(fp)
                    
                    case_id = m.get("case_id", d)
                    story = m.get("portfolio_story", {})
                    hands_on = story.get("hands_on_log", {})
                    curation = m.get("curation", {})
                    clustering = m.get("clustering", {})

                    # 1. Main Entity
                    sql_main = """
                    INSERT INTO verified_factchecks (
                        case_id, title, category, discovery_mode, curator_name, personal_motivation, target_workflow,
                        cluster_id, cluster_name, verdict, confidence_score,
                        hands_on_status, hands_on_pipeline, hands_on_env, hands_on_metrics, hands_on_details,
                        the_hook, marketing_hype_anatomy, engineering_takeaways, future_applications, sources, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, NOW()
                    )
                    ON CONFLICT (case_id) DO UPDATE SET
                        title = EXCLUDED.title,
                        verdict = EXCLUDED.verdict,
                        confidence_score = EXCLUDED.confidence_score,
                        hands_on_status = EXCLUDED.hands_on_status,
                        sources = EXCLUDED.sources,
                        updated_at = NOW();
                    """
                    cur.execute(sql_main, (
                        case_id,
                        m.get("title", ""),
                        m.get("category", "General"),
                        curation.get("discovery_mode", "USER_CURATED"),
                        curation.get("curator", "Anyong Cheong"),
                        curation.get("personal_motivation", ""),
                        curation.get("target_workflow", ""),
                        clustering.get("cluster_id", "general"),
                        clustering.get("cluster_name", "General Tech"),
                        m.get("verdict", "UNVERIFIED"),
                        m.get("confidence_score", 95.0),
                        hands_on.get("status", "PENDING_RESEARCH"),
                        hands_on.get("pipeline_or_url", ""),
                        hands_on.get("test_environment", ""),
                        hands_on.get("measured_results", ""),
                        hands_on.get("details", ""),
                        story.get("the_hook", ""),
                        story.get("marketing_hype_anatomy", ""),
                        story.get("engineering_takeaways", ""),
                        story.get("future_applications", ""),
                        json.dumps(m.get("sources", []))
                    ))

                    # 2. Alternatives
                    cur.execute("DELETE FROM factcheck_alternatives WHERE case_id = %s;", (case_id,))
                    for alt in clustering.get("alternatives", []):
                        cur.execute("""
                            INSERT INTO factcheck_alternatives (case_id, tool_name, tech_stack, pros, cons, best_for)
                            VALUES (%s, %s, %s, %s, %s, %s);
                        """, (case_id, alt.get("name", ""), alt.get("tech_stack", ""), alt.get("pros", ""), alt.get("cons", ""), alt.get("best_for", "")))

                    # 3. Community Signals
                    cur.execute("DELETE FROM factcheck_community_signals WHERE case_id = %s;", (case_id,))
                    for cr in m.get("community_reactions", []):
                        cur.execute("""
                            INSERT INTO factcheck_community_signals (case_id, platform, author_type, quote, source_url, signal_type)
                            VALUES (%s, %s, %s, %s, %s, %s);
                        """, (case_id, cr.get("platform", "Community"), cr.get("author_type", "Practitioner"), cr.get("quote", ""), cr.get("url", ""), "REVIEW"))

                    count += 1
                except Exception as e:
                    print(f"[!] Error inserting investigation {d}: {e}")
    conn.commit()
    conn.close()
    print(f"[+] Successfully synced {count} verified fact-check portfolios to Neon Postgres DB (Tier 2 Knowledge Core)!")

def main():
    parser = argparse.ArgumentParser(description="Neon Postgres Enterprise Synchronizer")
    parser.add_argument("--init", action="store_true", help="Initialize Sustainable Neon DB schema, indexes, and triggers")
    parser.add_argument("--sync-inbox", action="store_true", help="Push local inbox candidates to Neon DB (Tier 1)")
    parser.add_argument("--sync-factchecks", action="store_true", help="Push verified portfolios to Neon DB (Tier 2)")
    parser.add_argument("--sync-all", action="store_true", help="Initialize schema and sync everything to Neon DB")

    args = parser.parse_args()

    if args.init:
        init_schema()
    elif args.sync_inbox:
        push_inbox_to_neon()
    elif args.sync_factchecks:
        push_factchecks_to_neon()
    elif args.sync_all:
        init_schema()
        push_inbox_to_neon()
        push_factchecks_to_neon()
    else:
        print("Usage: python tools/db_bridge.py [--init | --sync-inbox | --sync-factchecks | --sync-all]")

if __name__ == "__main__":
    main()
