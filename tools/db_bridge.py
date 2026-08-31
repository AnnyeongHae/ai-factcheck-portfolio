#!/usr/bin/env python3
"""
Neon Postgres Cloud Bridge & Two-Tier Hybrid Synchronizer (2026 SOTA Framework)
- Tier 1: GitHub Actions / Harvester -> Neon DB (raw_trends_inbox)
- Tier 2: AI Agent (Deep Analysis) -> Neon DB (verified_factchecks) & Local Git / Pages
"""

import argparse
import datetime
import json
import os
import sys

# Ensure UTF-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def get_db_connection():
    db_url = os.environ.get("DATABASE_URL") or os.environ.get("NEON_DATABASE_URL")
    if not db_url:
        print("[!] Note: 'DATABASE_URL' environment variable not found.")
        print("    To connect to Neon Postgres, set: export DATABASE_URL='postgresql://user:password@ep-xyz.neon.tech/neondb?sslmode=require'")
        return None

    try:
        import psycopg2
        conn = psycopg2.connect(db_url)
        return conn
    except ImportError:
        print("[!] Warning: 'psycopg2' module not installed. Install via: pip install psycopg2-binary")
        return None
    except Exception as e:
        print(f"[!] Error: Failed to connect to Neon Postgres: {e}")
        return None

def init_schema():
    conn = get_db_connection()
    if not conn: return
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    schema_path = os.path.join(base_dir, "configs", "schema_neon.sql")
    if os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as f:
            sql = f.read()
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
            print("[+] Successfully initialized Neon Postgres tables and indexes!")
        except Exception as e:
            print(f"[!] Schema initialization failed: {e}")
        finally:
            conn.close()

def push_inbox_to_neon():
    conn = get_db_connection()
    if not conn: return

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    inbox_dir = os.path.join(base_dir, "inbox")
    
    count = 0
    with conn.cursor() as cur:
        for f in os.listdir(inbox_dir):
            if f.endswith(".json"):
                path = os.path.join(inbox_dir, f)
                try:
                    with open(path, "r", encoding="utf-8") as fp:
                        it = json.load(fp)
                    
                    sql = """
                    INSERT INTO raw_trends_inbox (inbox_id, harvested_date, source_platform, source_url, title, item_type, description, viral_metric, matched_user_domains, raw_payload, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (inbox_id) DO UPDATE SET
                        viral_metric = EXCLUDED.viral_metric,
                        description = EXCLUDED.description;
                    """
                    cur.execute(sql, (
                        it.get("inbox_id"),
                        it.get("harvested_date", datetime.date.today().isoformat()),
                        it.get("source_platform", "Web"),
                        it.get("source_url", ""),
                        it.get("title", ""),
                        it.get("type", "repo"),
                        it.get("description", ""),
                        it.get("viral_metric", ""),
                        json.dumps(it.get("matched_user_domains", [])),
                        json.dumps(it),
                        it.get("status", "PENDING_REVIEW")
                    ))
                    count += 1
                except Exception as e:
                    print(f"[!] Error inserting {f}: {e}")
    conn.commit()
    conn.close()
    print(f"[+] Successfully pushed {count} inbox candidates to Neon Postgres DB!")

def push_factchecks_to_neon():
    conn = get_db_connection()
    if not conn: return

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    inv_dir = os.path.join(base_dir, "investigations")
    
    count = 0
    with conn.cursor() as cur:
        for d in os.listdir(inv_dir):
            meta_path = os.path.join(inv_dir, d, "metadata.json")
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as fp:
                        m = json.load(fp)
                    
                    story = m.get("portfolio_story", {})
                    hands_on = story.get("hands_on_log", {})
                    curation = m.get("curation", {})
                    clustering = m.get("clustering", {})

                    sql = """
                    INSERT INTO verified_factchecks (
                        case_id, title, category, discovery_mode, curator, personal_motivation, target_workflow,
                        cluster_id, cluster_name, alternatives_matrix,
                        verdict, confidence_score, sources, community_reactions,
                        hands_on_status, hands_on_pipeline, hands_on_env, hands_on_metrics, hands_on_details,
                        the_hook, marketing_hype_anatomy, engineering_takeaways, future_applications, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, NOW()
                    )
                    ON CONFLICT (case_id) DO UPDATE SET
                        title = EXCLUDED.title,
                        verdict = EXCLUDED.verdict,
                        confidence_score = EXCLUDED.confidence_score,
                        alternatives_matrix = EXCLUDED.alternatives_matrix,
                        community_reactions = EXCLUDED.community_reactions,
                        hands_on_status = EXCLUDED.hands_on_status,
                        updated_at = NOW();
                    """
                    cur.execute(sql, (
                        m.get("case_id", d),
                        m.get("title", ""),
                        m.get("category", "General"),
                        curation.get("discovery_mode", "USER_CURATED"),
                        curation.get("curator", "Anyong Cheong"),
                        curation.get("personal_motivation", ""),
                        curation.get("target_workflow", ""),
                        clustering.get("cluster_id", ""),
                        clustering.get("cluster_name", ""),
                        json.dumps(clustering.get("alternatives", [])),
                        m.get("verdict", "UNVERIFIED"),
                        m.get("confidence_score", 95.0),
                        json.dumps(m.get("sources", [])),
                        json.dumps(m.get("community_reactions", [])),
                        hands_on.get("status", "PENDING_RESEARCH"),
                        hands_on.get("pipeline_or_url", ""),
                        hands_on.get("test_environment", ""),
                        hands_on.get("measured_results", ""),
                        hands_on.get("details", ""),
                        story.get("the_hook", ""),
                        story.get("marketing_hype_anatomy", ""),
                        story.get("engineering_takeaways", ""),
                        story.get("future_applications", "")
                    ))
                    count += 1
                except Exception as e:
                    print(f"[!] Error inserting investigation {d}: {e}")
    conn.commit()
    conn.close()
    print(f"[+] Successfully synced {count} verified fact-check portfolios to Neon Postgres DB!")

def main():
    parser = argparse.ArgumentParser(description="Neon Postgres Two-Tier Synchronizer")
    parser.add_argument("--init", action="store_true", help="Initialize Neon DB schema and tables")
    parser.add_argument("--sync-inbox", action="store_true", help="Push local inbox candidates to Neon DB")
    parser.add_argument("--sync-factchecks", action="store_true", help="Push verified portfolios to Neon DB")
    parser.add_argument("--sync-all", action="store_true", help="Sync everything to Neon DB")

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
