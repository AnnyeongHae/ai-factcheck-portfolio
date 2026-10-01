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
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

def classify_source_axis(platform_str, url=""):
    p = (platform_str or "").lower()
    u = (url or "").lower()
    if any(k in p for k in ["github", "hugging", "hf", "arxiv", "pytorch", "code", "paper", "model", "deepmind", "openai", "anthropic", "research"]) or any(k in u for k in ["github.com", "huggingface.co", "arxiv.org", "deepmind.google", "openai.com", "research.google"]):
        return "CODE"
    if any(k in p for k in ["hacker news", "reddit", "geeknews", "lobsters", "hada.io", "community", "forum", "v2ex"]) or any(k in u for k in ["ycombinator.com", "reddit.com", "hada.io"]) and "the hacker news" not in p:
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

import re

GENERIC_VERSION_PATTERNS = [
    # Matches patterns like: gemini 4 argon, gpt-6.1 sol, gpt-6 astra, claude opus 5.5, deepseek-v3.2, qwen-3.5, llama-4.5, glm-5.3, m5 ultra
    re.compile(r'\b(gemini|gpt|claude|deepseek|qwen|llama|glm|gemma|mistral|grok)[\s\-_]*(?:opus|sonnet|haiku|pro|flash|ultra|mini|v|r)?[\s\-_]*(\d+(?:\.\d+)?)\s*([a-z]{3,10})?\b', re.IGNORECASE),
    re.compile(r'\b(m[456])\s+(ultra|max|pro)\b', re.IGNORECASE),
]
STOP_CODENAMES = {
    'model', 'models', 'with', 'from', 'into', 'over', 'after', 'before', 'under', 'about', 'between',
    'will', 'can', 'may', 'now', 'just', 'more', 'most', 'other', 'some', 'such', 'says', 'said',
    'report', 'reports', 'launch', 'launches', 'launched', 'release', 'releases', 'released', 'announces',
    'announced', 'unveils', 'unveiled', 'rolls', 'out', 'update', 'updates', 'for', 'and', 'the',
    'that', 'this', 'new', 'open', 'source', 'free', 'api', 'app', 'web', 'chat', 'code', 'agent', 'agents',
    'million', 'billion', 'context', 'tokens', 'users', 'bench', 'benchmark', 'benchmarks'
}

def extract_release_cluster_key(title: str, title_ko: str = "", story_key: str = "", title_en: str = "") -> str:
    """
    Detects canonical cross-platform release/event signatures across EN/KO/ZH headlines.
    Combines:
      1. Explicit multilingual aliases (e.g. 제미나이/아르곤, 클로드, 맥 스튜디오)
      2. General Regex Entity + Version + Codename Anchor extraction (automatically catches ANY future model/version launch without hardcoding)
    """
    combined = f"{title or ''} {title_en or ''} {title_ko or ''} {story_key or ''}".lower()
    if ("gemini" in combined or "제미나이" in combined) and ("argon" in combined or "아르곤" in combined):
        return "release:google-gemini-4-argon"
    if ("gpt-6.1" in combined or "gpt 6.1" in combined) and "sol" in combined:
        return "release:openai-gpt-6-1-sol"
    if "gpt-6" in combined and "astra" in combined and "6.1" not in combined:
        return "release:openai-gpt-6-astra"
    if ("claude" in combined or "클로드" in combined) and "opus" in combined and "5.5" in combined:
        return "release:anthropic-claude-opus-5-5"
    if ("mac studio" in combined or "맥 스튜디오" in combined) and "m5" in combined and "ultra" in combined:
        return "release:apple-mac-studio-m5-ultra"
    if "deepseek-v3.2" in combined or ("deepseek" in combined and "v3.2" in combined):
        return "release:deepseek-v3-2-exp"
    if ("openai" in combined or "오픈ai" in combined) and ("dots" in combined or "'dot'" in combined or " dot " in combined) and ("agent" in combined or "avatar" in combined or "에이전트" in combined or "智能体" in combined):
        return "release:openai-dots-agent"
    if "f-droid" in combined and "2.0" in combined:
        return "release:f-droid-2-0"
    if "copilot+" in combined and ("dead" in combined or "pull back" in combined):
        return "release:microsoft-copilot-plus-pc-dead"

    # General regex anchor for any future model + version (+ optional codename)
    m = GENERIC_VERSION_PATTERNS[0].search(combined)
    if m:
        family = m.group(1).lower()
        ver = m.group(2).replace('.', '-')
        codename = (m.group(3) or '').lower()
        if codename and codename not in STOP_CODENAMES:
            return f"release:auto-{family}-{ver}-{codename}"
        # Only group by family+version if version has a decimal (e.g. 5.5, 3.2, 6.1) to avoid overly broad 'gpt-4' or 'gemini-2' collisions
        if '-' in ver:
            return f"release:auto-{family}-{ver}"

    return ""

def ensure_primary_in_sources(row_data, created_at):
    """
    Self-healing fix: If raw_payload['sources'] has merged duplicate sources from embed-worker
    but omitted the primary row's own source_url, prepend the primary row at index 0.
    """
    raw_payload = row_data["raw_payload"]
    sources = raw_payload.get("sources")
    source_platform = row_data["source_platform"] or "Primary"
    source_url = row_data["source_url"] or ""
    title = row_data["title"] or ""

    if not isinstance(sources, list) or len(sources) == 0:
        return [{
            "source_name": source_platform,
            "platform": source_platform,
            "title": title,
            "url": source_url,
            "type": "primary",
            "created_at": created_at.isoformat()
        }], False

    existing_urls = {(s.get("url") or s.get("source_url") or "").strip() for s in sources if isinstance(s, dict)}
    if source_url and source_url.strip() not in existing_urls:
        healed = [{
            "source_name": source_platform,
            "platform": source_platform,
            "title": title,
            "url": source_url,
            "type": "primary",
            "created_at": created_at.isoformat()
        }] + [s for s in sources if isinstance(s, dict)]
        return healed, True

    return [s for s in sources if isinstance(s, dict)], False

def compute_hvd_score(row_data, now_utc):
    """
    row_data: dict with id, title, source_platform, source_url, viral_score, created_at, raw_payload
    """
    source_platform = row_data["source_platform"] or ""
    source_url = row_data["source_url"] or ""
    viral_score = row_data.get("viral_score") or 0
    created_at = parse_iso_or_default(row_data.get("created_at"), now_utc)
    raw_payload = row_data.get("raw_payload") or {}

    sources, was_healed = ensure_primary_in_sources(row_data, created_at)
    if was_healed or len(sources) > 1:
        raw_payload["sources"] = sources
        raw_payload["has_multi_sources"] = len(sources) > 1

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

        s_dt = parse_iso_or_default(s.get("created_at") or s.get("original_created_at") or s.get("published_at"), created_at)
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

    velocity = (len(sources) / math.sqrt(max(1.0, delta_hours))) * (1.0 + min(2.5, delta_metric / 40.0))

    # 3. Depth
    raw_comments = raw_payload.get("raw_comments") or []
    comments_count = len(raw_comments) if isinstance(raw_comments, list) else 0
    depth_inner = 10.0 + (max(0, comments_count) * 2.0) + (max(0.0, float(viral_score)) * 0.5) + (max(0.0, float(delta_metric)) * 0.5)
    depth = math.log10(max(1.0, depth_inner))

    # 4. Time Decay (Half-life = 36 hours)
    decay = math.exp(- (math.log(2.0) / 36.0) * delta_hours)

    raw_spike = (h_mult * velocity * depth) * 10.0
    final_spike_score = round(raw_spike * decay, 1)

    # Determine if actively spiking: multi-source (len >= 2) with score >= 0.3
    is_spiking = bool(final_spike_score >= 0.3 and (len(sources) >= 2 or num_axes >= 2))

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

    return final_spike_score, is_spiking, spike_analysis, was_healed

def main():
    parser = argparse.ArgumentParser(description="Recompute H-V-D spike scores and cluster multi-source releases across DB")
    parser.add_argument("--commit", action="store_true", help="Commit changes to database")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of rows (0 for all)")
    args = parser.parse_args()

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("[!] Error: DATABASE_URL not set.")
        sys.exit(1)

    print("[*] Connecting to PostgreSQL SSOT...")
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM raw_trends_inbox;")
    total_count = cur.fetchone()[0]
    print(f"[*] Total rows in raw_trends_inbox: {total_count}")

    query = """
        SELECT id, title, source_platform, source_url, viral_score, created_at, raw_payload, triage_status, curation_tier
        FROM raw_trends_inbox
        WHERE (triage_status IS NULL OR triage_status != 'archived')
        ORDER BY id DESC
    """
    if args.limit > 0:
        query += f" LIMIT {args.limit}"

    cur.execute(query)
    rows = cur.fetchall()

    now_utc = datetime.now(timezone.utc)
    row_dicts = []
    for r in rows:
        p = r[6] if isinstance(r[6], dict) else json.loads(r[6] or "{}")
        row_dicts.append({
            "id": r[0],
            "title": r[1],
            "source_platform": r[2],
            "source_url": r[3],
            "viral_score": r[4],
            "created_at": r[5],
            "raw_payload": p,
            "triage_status": r[7],
            "curation_tier": r[8]
        })

    # Step 1: Cluster recent (<= 7 days) cross-platform named releases into unified hub stories
    clusters = {}
    for rd in row_dicts:
        dt = parse_iso_or_default(rd["created_at"], now_utc)
        if (now_utc - dt).total_seconds() > 7 * 86400:
            continue
        p = rd["raw_payload"]
        t_ko = p.get("title_ko") or (p.get("ai_enrichment") or {}).get("korean_title") or ""
        t_en = p.get("title_en") or ((p.get("multilingual") or {}).get("en") or {}).get("title") or ""
        s_key = p.get("canonical_story_key") or (p.get("ai_enrichment") or {}).get("canonical_story_key") or ""
        rel_key = extract_release_cluster_key(rd["title"], t_ko, s_key, t_en)
        if rel_key:
            clusters.setdefault(rel_key, []).append(rd)

    archived_dup_ids = []
    clustered_hub_ids = set()
    for rel_key, group in clusters.items():
        if len(group) < 2:
            continue
        # Prefer DAILY_HOT or Official Blog / Press with rich sources as primary hub
        group.sort(key=lambda x: (
            1 if x.get("curation_tier") == "DAILY_HOT" else 0,
            len(x["raw_payload"].get("sources") or []),
            1 if any(k in (x["source_platform"] or "").lower() for k in ["deepmind", "openai", "techcrunch", "geeknews", "hacker news"]) else 0,
            x["id"]
        ), reverse=True)
        hub = group[0]
        hub_dt = parse_iso_or_default(hub["created_at"], now_utc)
        hub_sources, _ = ensure_primary_in_sources(hub, hub_dt)
        existing_urls = {(s.get("url") or s.get("source_url") or "").strip() for s in hub_sources if isinstance(s, dict)}

        for sec in group[1:]:
            sec_dt = parse_iso_or_default(sec["created_at"], now_utc)
            sec_sources, _ = ensure_primary_in_sources(sec, sec_dt)
            for s in sec_sources:
                s_url = (s.get("url") or s.get("source_url") or "").strip()
                if s_url and s_url not in existing_urls:
                    hub_sources.append(s)
                    existing_urls.add(s_url)
            archived_dup_ids.append(sec["id"])

        hub["raw_payload"]["sources"] = hub_sources
        hub["raw_payload"]["has_multi_sources"] = True
        hub["raw_payload"]["is_cross_spiking"] = True
        clustered_hub_ids.add(hub["id"])
        print(f"[+] Clustered '{rel_key}' -> Hub ID {hub['id']} ({hub['title'][:50]}) with {len(hub_sources)} total cross-platform sources (Archived {len(group)-1} duplicates)")

    # Step 2: Recompute H-V-D scores across all active rows
    scored_items = []
    spike_count = 0
    super_spike_count = 0
    cross_spike_count = 0
    healed_count = 0
    updates = []

    archived_set = set(archived_dup_ids)
    for row_data in row_dicts:
        if row_data["id"] in archived_set:
            continue
        score, is_spiking, analysis, was_healed = compute_hvd_score(row_data, now_utc)
        if was_healed:
            healed_count += 1

        new_payload = dict(row_data["raw_payload"])
        new_payload["spike_analysis"] = analysis
        new_payload["is_cross_spiking"] = is_spiking

        old_spk = row_data["raw_payload"].get("is_cross_spiking")
        old_an = row_data["raw_payload"].get("spike_analysis")
        if was_healed or row_data["id"] in clustered_hub_ids or analysis["sources_count"] > 1 or is_spiking or old_spk or old_an or row_data["raw_payload"].get("metric_tracking"):
            updates.append((json.dumps(new_payload, ensure_ascii=False), row_data["id"]))

        if is_spiking:
            spike_count += 1
            if analysis["axes_count"] >= 3:
                super_spike_count += 1
            elif analysis["axes_count"] == 2:
                cross_spike_count += 1
            scored_items.append((score, analysis, row_data["title"], row_data["id"]))

    scored_items.sort(key=lambda x: x[0], reverse=True)

    print("\n" + "="*80)
    print(f"📊 [H-V-D TRIPOD SCORING RESULTS] Total Active Analyzed: {len(row_dicts) - len(archived_set)}")
    print(f"   - Self-Healed Missing Primary Sources : {healed_count} rows")
    print(f"   - Active Spiking Stories              : {spike_count}")
    print(f"   - 🔥 3-Axis Super Spikes              : {super_spike_count}")
    print(f"   - ⚡ 2-Axis Cross Spikes              : {cross_spike_count}")
    print("="*80)
    print("🏆 Top 15 Highest Spiking Stories Right Now:")
    for rank, (score, an, title, rid) in enumerate(scored_items[:15], 1):
        print(f"  #{rank:>2} [{score:>6.1f} pts] {an['tier']:<20} (Sources: {an['sources_count']}|P:{an['press_count']}|C:{an['community_count']}|K:{an['code_count']})")
        print(f"       ID {rid}: {title[:75]}")

    if args.commit:
        from psycopg2.extras import execute_batch
        if archived_dup_ids:
            cur.execute("""
                UPDATE raw_trends_inbox
                SET triage_status = 'archived',
                    curation_tier = 'duplicate',
                    updated_at = NOW()
                WHERE id = ANY(%s);
            """, (archived_dup_ids,))
            print(f"[*] Archived {len(archived_dup_ids)} cross-platform duplicate rows into their primary hubs.")
        print(f"[*] Committing updates for {len(updates)} rows to database via execute_batch...")
        update_sql = """
            UPDATE raw_trends_inbox
            SET raw_payload = %s::jsonb,
                updated_at = NOW()
            WHERE id = %s;
        """
        execute_batch(cur, update_sql, updates, page_size=200)
        conn.commit()
        print("[+] DB Update 100% Complete & Committed!")
    else:
        print("\n[!] Dry run mode. Run with --commit to apply changes to database.")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
