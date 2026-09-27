#!/usr/bin/env python3
"""
tools/recompute_spike_scores.py
2026 SOTA H-V-D Tripod Decay Engine
Recomputes spike scores across all raw_trends_inbox rows based on:
  - H: Heterogeneity Multiplier (1-Axis=1.0x, 2-Axis=2.5x, 3-Axis=5.0x)
  - V: Velocity (Sources / sqrt(Time))
  - D: Depth (Comments * 2.0 + Upvotes * 0.5)
  - Decay: 36h Half-life exponential decay
"""

import os
import sys
import math
import json
import argparse
from datetime import datetime, timezone
import psycopg2
from dotenv import load_dotenv

load_dotenv()

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

def classify_source_axis(platform_str, url=""):
    p = (platform_str or "").lower()
    u = (url or "").lower()
    if any(k in p for k in ["github", "hugging", "hf", "arxiv", "pytorch", "code", "paper", "model"]) or any(k in u for k in ["github.com", "huggingface.co", "arxiv.org"]):
        return "CODE"
    if any(k in p for k in ["hacker news", "reddit", "geeknews", "lobsters", "hada.io", "community", "forum"]) or any(k in u for k in ["ycombinator.com", "reddit.com", "hada.io"]):
        return "COMMUNITY"
    return "PRESS"

def parse_iso_or_default(val, default_dt):
    if not val:
        return default_dt
    if isinstance(val, datetime):
        return val if val.tzinfo else val.replace(tzinfo=timezone.utc)
    try:
        clean = str(val).replace('Z', '+00:00')
        dt = datetime.fromisoformat(clean)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return default_dt

def compute_hvd_score(row_data, now_utc):
    """
    row_data: dict with id, title, source_platform, source_url, viral_score, created_at, raw_payload
    """
    row_id = row_data["id"]
    title = row_data["title"]
    source_platform = row_data["source_platform"] or ""
    source_url = row_data["source_url"] or ""
    viral_score = row_data.get("viral_score") or 0
    created_at = parse_iso_or_default(row_data.get("created_at"), now_utc)
    raw_payload = row_data.get("raw_payload") or {}

    sources = raw_payload.get("sources")
    if not isinstance(sources, list) or len(sources) == 0:
        sources = [{
            "platform": source_platform,
            "url": source_url,
            "created_at": created_at.isoformat()
        }]

    # 1. Classify axes and count
    axes = set()
    press_count = 0
    community_count = 0
    code_count = 0

    earliest_dt = created_at
    for s in sources:
        if not isinstance(s, dict):
            continue
        p = s.get("platform") or s.get("source_name") or source_platform
        u = s.get("url") or source_url
        axis = classify_source_axis(p, u)
        axes.add(axis)
        if axis == "PRESS":
            press_count += 1
        elif axis == "COMMUNITY":
            community_count += 1
        elif axis == "CODE":
            code_count += 1

        # Check earliest timestamp
        s_dt = parse_iso_or_default(s.get("created_at") or s.get("original_created_at"), created_at)
        if s_dt < earliest_dt:
            earliest_dt = s_dt

    num_axes = len(axes)
    if num_axes >= 3:
        h_mult = 5.0
        tier_label = "3-Axis SUPER SPIKE"
    elif num_axes == 2:
        h_mult = 2.5
        tier_label = "2-Axis CROSS SPIKE"
    else:
        h_mult = 1.0
        tier_label = "1-Axis PRESS CLUSTER" if len(sources) > 1 else "SINGLE"

    # 2. Velocity
    delta_seconds = max(1800.0, (now_utc - earliest_dt).total_seconds())
    delta_hours = delta_seconds / 3600.0

    tracking = raw_payload.get("metric_tracking") or {}
    delta_metric = 0
    try:
        delta_metric = float(tracking.get("delta") or tracking.get("growth_delta") or 0)
    except Exception:
        delta_metric = 0

    # Velocity: Sources / (hours^0.5) with delta metric acceleration
    velocity = (len(sources) / math.sqrt(max(1.0, delta_hours))) * (1.0 + min(2.5, delta_metric / 40.0))

    # 3. Depth
    raw_comments = raw_payload.get("raw_comments") or []
    comments_count = len(raw_comments) if isinstance(raw_comments, list) else 0
    depth_inner = 10.0 + (max(0, comments_count) * 2.0) + (max(0.0, float(viral_score)) * 0.5) + (max(0.0, float(delta_metric)) * 0.5)
    depth = math.log10(max(1.0, depth_inner))

    # 4. Time Decay (Half-life = 36 hours)
    # lambda = ln(2) / 36.0
    decay = math.exp(- (math.log(2.0) / 36.0) * delta_hours)

    # Base spike score
    raw_spike = (h_mult * velocity * depth) * 10.0
    final_spike_score = round(raw_spike * decay, 1)

    # Determine if actively spiking
    # Condition: score >= 0.5 AND (len(sources) >= 2 OR num_axes >= 2)
    is_spiking = bool(final_spike_score >= 0.5 and (len(sources) >= 2 or num_axes >= 2))

    spike_analysis = {
        "score": final_spike_score,
        "raw_score": round(raw_spike, 1),
        "tier": tier_label,
        "axes_count": num_axes,
        "axes": list(axes),
        "press_count": press_count,
        "community_count": community_count,
        "code_count": code_count,
        "sources_count": len(sources),
        "velocity": round(velocity, 2),
        "depth": round(depth, 2),
        "decay_factor": round(decay, 3),
        "delta_hours": round(delta_hours, 1),
        "updated_at": now_utc.isoformat()
    }

    return final_spike_score, is_spiking, spike_analysis

def main():
    parser = argparse.ArgumentParser(description="Recompute H-V-D spike scores across DB")
    parser.add_argument("--commit", action="store_true", help="Commit changes to database")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of rows (0 for all)")
    args = parser.parse_args()

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("[!] Error: DATABASE_URL not set.")
        sys.exit(1)

    print(f"[*] Connecting to PostgreSQL SSOT...")
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM raw_trends_inbox;")
    total_count = cur.fetchone()[0]
    print(f"[*] Total rows in raw_trends_inbox: {total_count}")

    query = """
        SELECT id, title, source_platform, source_url, viral_score, created_at, raw_payload
        FROM raw_trends_inbox
        ORDER BY id DESC
    """
    if args.limit > 0:
        query += f" LIMIT {args.limit}"

    cur.execute(query)
    rows = cur.fetchall()

    now_utc = datetime.now(timezone.utc)
    scored_items = []
    spike_count = 0
    super_spike_count = 0
    cross_spike_count = 0

    updates = []
    for r in rows:
        row_data = {
            "id": r[0],
            "title": r[1],
            "source_platform": r[2],
            "source_url": r[3],
            "viral_score": r[4],
            "created_at": r[5],
            "raw_payload": r[6] if isinstance(r[6], dict) else json.loads(r[6] or "{}")
        }
        score, is_spiking, analysis = compute_hvd_score(row_data, now_utc)
        
        # Merge analysis into raw_payload
        new_payload = dict(row_data["raw_payload"])
        new_payload["spike_analysis"] = analysis
        new_payload["is_cross_spiking"] = is_spiking

        # Only queue update if relevant to spike/sources/metric tracking
        old_spk = row_data["raw_payload"].get("is_cross_spiking")
        old_an = row_data["raw_payload"].get("spike_analysis")
        if analysis["sources_count"] > 1 or is_spiking or old_spk or old_an or row_data["raw_payload"].get("metric_tracking"):
            updates.append((is_spiking, json.dumps(new_payload), row_data["id"]))

        if is_spiking:
            spike_count += 1
            if analysis["axes_count"] >= 3:
                super_spike_count += 1
            elif analysis["axes_count"] == 2:
                cross_spike_count += 1
            scored_items.append((score, analysis, row_data["title"], row_data["id"]))

    scored_items.sort(key=lambda x: x[0], reverse=True)

    print("\n" + "="*80)
    print(f"📊 [H-V-D TRIPOD SCORING RESULTS] Total Analyzed: {len(rows)}")
    print(f"   - Active Spiking Stories: {spike_count} (vs 914 legacy noise)")
    print(f"   - 🔥 3-Axis Super Spikes: {super_spike_count}")
    print(f"   - ⚡ 2-Axis Cross Spikes: {cross_spike_count}")
    print("="*80)
    print("🏆 Top 15 Highest Spiking Stories Right Now:")
    for rank, (score, an, title, rid) in enumerate(scored_items[:15], 1):
        print(f"  #{rank:>2} [{score:>6.1f} pts] {an['tier']:<20} (Sources: {an['sources_count']}|P:{an['press_count']}|C:{an['community_count']}|K:{an['code_count']})")
        print(f"       ID {rid}: {title[:75]}")

    if args.commit:
        from psycopg2.extras import execute_batch
        print(f"\n[*] Committing updates for {len(updates)} rows to database via execute_batch...")
        update_sql = """
            UPDATE raw_trends_inbox
            SET raw_payload = %s::jsonb
            WHERE id = %s;
        """
        batch_params = [(b[1], b[2]) for b in updates]
        execute_batch(cur, update_sql, batch_params, page_size=200)
        conn.commit()
        print("[+] DB Update 100% Complete & Committed!")
    else:
        print("\n[!] Dry run mode. Run with --commit to apply changes to database.")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
