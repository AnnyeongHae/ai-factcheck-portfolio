#!/usr/bin/env python3
"""
tools/run_eod_digest.py
==============================================================================
Daily EOD (End of Day) Tech & Trend Digest Engine (23:00 KST / 14:00 UTC)
------------------------------------------------------------------------------
Purpose:
  Runs once per day at 23:00 KST via GitHub Actions.
  Analyzes 24-hour growth velocity (Δstars, Δlikes, Δupvotes) and cross-platform
  co-occurrences across all verified, 100% multilingual enriched items in Neon DB.
  
  Selects the definitive "Today's Top 10 Hot Tech Trends" (오늘 하루 핫한 것)
  and marks them with:
  - curation_tier = 'DAILY_HOT'
  - editorial_pick_date = CURRENT_DATE
==============================================================================
"""

import argparse
import datetime
import os
import sys

# Ensure UTF-8 output
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

def run_eod_digest(top_n=10):
    try:
        from tools.db_bridge import get_db_connection
    except Exception:
        try:
            from db_bridge import get_db_connection
        except Exception as e:
            print(f"[!] Cannot import db_bridge: {e}")
            return False

    conn = get_db_connection()
    if not conn:
        print("[!] [EOD Digest] Failed to establish Neon DB connection.")
        return False

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    kst_tz = datetime.timezone(datetime.timedelta(hours=9))
    now_kst = now_utc.astimezone(kst_tz)
    today_kst_str = now_kst.strftime("%Y-%m-%d")

    print("==================================================================")
    print(f"🏆 [EOD Digest Engine] Calculating 24-Hour Hot Trends for {today_kst_str}")
    print(f"[*] Execution Timestamp : {now_kst.strftime('%Y-%m-%d %H:%M:%S KST')}")
    print("==================================================================")

    try:
        cur = conn.cursor()

        # Step 1: Ensure columns exist in raw_trends_inbox
        cur.execute("""
            ALTER TABLE raw_trends_inbox ADD COLUMN IF NOT EXISTS curation_tier VARCHAR(50);
            ALTER TABLE raw_trends_inbox ADD COLUMN IF NOT EXISTS editorial_pick_date DATE;
            ALTER TABLE raw_trends_inbox ADD COLUMN IF NOT EXISTS daily_hot_rank INT;
        """)

        # Step 2: Reset yesterday's active 'DAILY_HOT' flags to 'ARCHIVED_HOT'
        cur.execute("""
            UPDATE raw_trends_inbox 
            SET curation_tier = 'ARCHIVED_HOT'
            WHERE curation_tier = 'DAILY_HOT' AND editorial_pick_date < CURRENT_DATE;
        """)

        # Step 3: Compute 24-hour delta metrics and cross-platform presence
        # Uses trend_metric_snapshots deltas where available, combined with viral scores
        ranking_query = """
            WITH recent_deltas AS (
                SELECT 
                    inbox_id,
                    MAX(metric_value) - MIN(metric_value) as delta_metric,
                    COALESCE(SUM(delta), 0) as total_delta
                FROM trend_metric_snapshots
                WHERE recorded_at >= (CURRENT_TIMESTAMP - INTERVAL '24 hours')
                GROUP BY inbox_id
            ),
            candidates AS (
                SELECT 
                    r.id,
                    r.inbox_id,
                    r.title,
                    COALESCE(r.raw_payload->'ai_enrichment'->>'korean_title', r.raw_payload->'multilingual'->'ko'->>'title', r.title) AS title_ko,
                    r.source_platform,
                    COALESCE(r.raw_payload->'ai_enrichment'->>'canonical_story_key', r.raw_payload->>'canonical_key', r.inbox_id) AS canonical_key,
                    r.viral_score,
                    r.created_at,
                    r.is_classified,
                    COALESCE(d.delta_metric, 0) * 1.5 + 
                    COALESCE(d.total_delta, 0) * 1.0 + 
                    COALESCE(r.viral_score, 0) * 0.5 AS raw_velocity
                FROM raw_trends_inbox r
                LEFT JOIN recent_deltas d ON r.inbox_id = d.inbox_id
                WHERE r.created_at >= (CURRENT_TIMESTAMP - INTERVAL '48 hours')
            ),
            scored_clusters AS (
                SELECT 
                    MIN(id) AS representative_id,
                    MAX(title_ko) AS display_title,
                    canonical_key,
                    COUNT(DISTINCT source_platform) AS platform_count,
                    array_agg(DISTINCT source_platform) AS platforms,
                    SUM(raw_velocity) * (CASE WHEN COUNT(DISTINCT source_platform) >= 2 THEN 1.5 ELSE 1.0 END) AS final_velocity_score
                FROM candidates
                WHERE canonical_key IS NOT NULL AND canonical_key != ''
                GROUP BY canonical_key
            )
            SELECT 
                representative_id,
                display_title,
                canonical_key,
                platform_count,
                platforms,
                ROUND(final_velocity_score::numeric, 1) AS score
            FROM scored_clusters
            ORDER BY score DESC
            LIMIT %s;
        """

        cur.execute(ranking_query, (top_n,))
        top_items = cur.fetchall()

        if not top_items:
            print("[*] [EOD Digest] No active candidates found in the last 48 hours.")
            cur.close()
            conn.close()
            return True

        print(f"[+] [EOD Digest] Identified Top {len(top_items)} Emerging Tech & News Trends:")
        top_ids = []
        for rank, item in enumerate(top_items, start=1):
            rep_id, title_ko, ckey, p_count, platforms, score = item
            top_ids.append(rep_id)
            cross_badge = "🔥 [CROSS-PLATFORM]" if p_count >= 2 else "  "
            print(f"  #{rank:>2} {cross_badge} [{score:>6.1f} pts] {title_ko[:50]} (Sources: {', '.join(platforms)})")

            # Update database with rank
            cur.execute("""
                UPDATE raw_trends_inbox
                SET curation_tier = 'DAILY_HOT',
                    editorial_pick_date = CURRENT_DATE,
                    daily_hot_rank = %s
                WHERE id = %s;
            """, (rank, rep_id))

        conn.commit()
        cur.close()
        conn.close()

        print("==================================================================")
        print(f"🎯 [EOD Digest Complete] Successfully marked {len(top_ids)} items as 'DAILY_HOT' in Neon DB.")
        print("==================================================================")
        return True

    except Exception as e:
        print(f"[!] [EOD Digest Error]: {e}")
        try:
            conn.rollback()
            conn.close()
        except Exception:
            pass
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run EOD 23:00 KST Daily Digest Ranking")
    parser.add_argument("--top", type=int, default=10, help="Number of daily hot trends to select")
    args = parser.parse_args()

    success = run_eod_digest(top_n=args.top)
    sys.exit(0 if success else 1)
