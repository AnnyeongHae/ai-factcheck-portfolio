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
    if any(k in p for k in ["pytorchkr", "pytorch.kr"]) or "discuss.pytorch.kr" in u:
        return "COMMUNITY"
    if any(k in p for k in ["github", "hugging", "hf ", "arxiv", "code", "paper", "model", "deepmind", "openai", "anthropic", "research"]) or any(k in u for k in ["github.com", "huggingface.co", "arxiv.org", "deepmind.google", "openai.com", "anthropic.com", "claude.dev", "research.google"]):
        return "CODE"
    if (any(k in p for k in ["hacker news", "reddit", "geeknews", "lobsters", "hada.io", "youtube", "twitter", "community", "forum", "v2ex"]) or any(k in u for k in ["ycombinator.com", "reddit.com", "hada.io", "youtube.com", "youtu.be", "x.com"])) and "the hacker news" not in p:
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
    if ("meta" in combined or "메타" in combined) and "muse" in combined and any(k in combined for k in ["agent", "personal", "openclaw", "imessage", "exploit", "filesystem", "amazon", "에이전트"]):
        return "release:meta-muse-ai-agent"
    if "f-droid" in combined and "2.0" in combined:
        return "release:f-droid-2-0"
    if "copilot+" in combined and ("dead" in combined or "pull back" in combined):
        return "release:microsoft-copilot-plus-pc-dead"
    if ("pi 1.0" in combined or "pi durable" in combined) and "raspberry" not in combined:
        return "release:earendil-pi-1-0"
    if "kolibri" in combined and any(k in combined for k in ["sovereign", "open-weight", "open weight", "aleph-alpha", "tech report", "소버린", "오픈웨이트", "주권형", "기술 보고서"]):
        return "release:germany-sovereign-ai-kolibri"
    if any(k in combined for k in ["altman", "알트만", "오픈ai 최고경영자", "openai ceo"]) and any(k in combined for k in ["bad things", "accept some", "risks are worth", "warrant accepting", "일부 위험 감수", "나쁜 일도 받아들여야", "regulatory divide", "리스크 규제 입장", "부작용을 일으키겠지만"]):
        return "event:openai-altman-accept-ai-risks"

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

PREFIX_STRIP_RE_PY = re.compile(r'^(?:News|Hacker News|Reddit|GeekNews|GitHub|HuggingFace Model|HF Space|PyTorchKR|YouTube(?:\s*\([^)]*\))?|Press(?:\s*\([^)]*\))?|r/[a-zA-Z0-9_]+):\s*', re.IGNORECASE)
SHOW_HN_RE_PY = re.compile(r'^(?:Show HN|Ask HN|Show GN):\s*', re.IGNORECASE)
VERSION_TOKEN_RE_PY = re.compile(r'\b(?:b\d{4,6}|v?\d+\.\d+(?:\.\d+)?(?:-[a-z0-9.]+)?)\b', re.IGNORECASE)
MAJOR_ENTITIES_PY = ['openai', 'google', 'anthropic', 'meta', 'microsoft', 'apple', 'deepseek', 'qwen', 'houthi', 'flock', 'nvidia', 'tesla']
BROAD_ENTITY_TOKENS_PY = {
    'openai', 'chatgpt', 'anthropic', 'claude', 'google', 'gemini', 'meta', 'llama',
    'microsoft', 'copilot', 'apple', 'nvidia', 'deepseek', 'qwen', 'amazon', 'aws', 'tesla', 'github'
}
STOP_WORDS_PY = {
    'the', 'and', 'for', 'with', 'that', 'this', 'from', 'into', 'over', 'after', 'before',
    'under', 'about', 'between', 'through', 'during', 'without', 'within', 'along', 'following',
    'across', 'behind', 'beyond', 'plus', 'except', 'but', 'up', 'out', 'around', 'down', 'off',
    'above', 'near', 'new', 'how', 'why', 'what', 'when', 'where', 'who', 'will', 'can', 'may',
    'now', 'just', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
    'same', 'so', 'than', 'too', 'very', 'says', 'said', 'report', 'reports', 'launch', 'launches',
    'launched', 'release', 'releases', 'released', 'announces', 'announced', 'unveils', 'unveiled',
    'rolls', 'out', 'update', 'updates', 'model', 'models', 'ai', 'artificial', 'intelligence',
    'tech', 'technology', 'company', 'users', 'system', 'systems', 'data', 'first', 'next', 'open', 'source',
    'youtube', 'jocoding', 'shorts', 'reddit', 'geeknews', 'hacker', 'news', 'github', 'arxiv',
    'press', 'pytorchkr', 'huggingface', 'hugging', 'face', 'space', 'video', 'videos', 'channel',
    'show', 'ask', 'has', 'have', 'are', 'was', 'were', 'been', 'being', 'tells', 'shows',
    'difference', 'stance', 'taking', 'llm', 'llms', 'agent', 'agents', 'reasoning', 'training',
    'design', 'code', 'coding', 'paper', 'papers', 'preprint', 'world', 'features', 'personal',
    'research', 'blog', 'technical', 'changelog', 'university', 'peking', 'tsinghua',
    '2025', '2026', '2027', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
    'notable', 'weekly', 'daily', 'build', 'building', 'guide', 'using', 'based', 'via', 'part', 'large', 'language'
}

def strip_platform_prefix_py(text: str, platform: str = "") -> str:
    s = (text or '').strip()
    if platform:
        p_clean = platform.split('(')[0].strip()
        for cand in (platform.strip(), p_clean):
            if cand and s.lower().startswith(cand.lower() + ':'):
                s = s[len(cand) + 1:].strip()
    s = PREFIX_STRIP_RE_PY.sub('', s)
    s = SHOW_HN_RE_PY.sub('', s)
    return s

def normalize_for_tokens_py(text: str, platform: str = "") -> str:
    s = strip_platform_prefix_py(text, platform).lower()
    s = re.sub(r'\bsam altman\b|\baltman\b|\bopenai ceo\b|\bceo of openai\b', ' openai altman ', s)
    s = re.sub(r'\bdario amodei\b|\bamodei\b|\banthropic ceo\b', ' anthropic amodei ', s)
    s = re.sub(r'\bsundar pichai\b|\bdemis hassabis\b', ' google ', s)
    s = re.sub(r'\bopen[\s\-]+weights?\b', ' openweight ', s)
    s = re.sub(r'\bbad things\b|\bharms?\b|\brisks?\b', ' risks ', s)
    s = re.sub(r'\bworth\b|\bbenefits?\b', ' benefits ', s)
    return s

def extract_specific_tokens_py(text: str, platform: str = "") -> list:
    norm = normalize_for_tokens_py(text, platform)
    plat_tokens = set(re.sub(r'[^a-z0-9]+', ' ', (platform or '').lower()).split())
    cleaned = re.sub(r'[^a-z0-9.\-+]+', ' ', norm)
    seen = []
    for tok in cleaned.split():
        if len(tok) >= 3 and tok not in STOP_WORDS_PY and tok not in plat_tokens and tok not in seen:
            seen.append(tok)
    return seen

def has_version_conflict_py(text_a: str, text_b: str) -> bool:
    va = {m.lower().lstrip('v') for m in VERSION_TOKEN_RE_PY.findall(text_a or '')}
    vb = {m.lower().lstrip('v') for m in VERSION_TOKEN_RE_PY.findall(text_b or '')}
    if va and vb and not (va & vb):
        return True
    return False

def ensure_primary_in_sources(row_data, created_at):
    """
    Self-healing fix:
    1. If raw_payload['sources'] has merged duplicate sources from embed-worker
       but omitted the primary row's own source_url, prepend the primary row at index 0.
    2. Prune false same-channel YouTube self-merges (e.g. multiple different videos from 'YouTube (조코딩 JoCoding)').
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

    was_healed = False
    norm_primary_plat = source_platform.strip().lower()
    norm_primary_url = source_url.strip()

    cleaned_sources = []
    for s in sources:
        if not isinstance(s, dict):
            continue
        s_plat = (s.get("platform") or s.get("source_name") or "").strip().lower()
        s_url = (s.get("url") or s.get("source_url") or "").strip()
        # Drop false same-channel YouTube self-merges where URL differs from primary URL
        if "youtube" in norm_primary_plat and s_plat == norm_primary_plat and s_url != norm_primary_url:
            was_healed = True
            continue
        cleaned_sources.append(s)

    existing_urls = {(s.get("url") or s.get("source_url") or "").strip() for s in cleaned_sources}
    if norm_primary_url and norm_primary_url not in existing_urls:
        cleaned_sources = [{
            "source_name": source_platform,
            "platform": source_platform,
            "title": title,
            "url": source_url,
            "type": "primary",
            "created_at": created_at.isoformat()
        }] + cleaned_sources
        was_healed = True

    return cleaned_sources, was_healed

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
    if was_healed or len(sources) >= 1:
        raw_payload["sources"] = sources
        raw_payload["has_multi_sources"] = len(sources) > 1

    # 1. Classify axes and count
    axes = set()
    distinct_platforms = set()
    press_count = 0
    community_count = 0
    code_count = 0

    earliest_dt = created_at
    for s in sources:
        if not isinstance(s, dict):
            continue
        p = s.get("platform") or s.get("source_name") or source_platform
        u = s.get("url") or source_url
        distinct_platforms.add((p or "").strip().lower())
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

    # Determine if actively spiking: must have >= 2 sources AND (>= 2 distinct platforms or >= 2 axes)
    is_spiking = bool(final_spike_score >= 0.3 and len(sources) >= 2 and (len(distinct_platforms) >= 2 or num_axes >= 2))

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

from datetime import datetime, timezone, timedelta

KST_TZ = timezone(timedelta(hours=9))

def ensure_ranking_schema(cur):
    """Ensures cross_viral_daily_rankings table and raw_trends_inbox peak/live columns exist in PostgreSQL SSOT."""
    cur.execute("""
        ALTER TABLE raw_trends_inbox
            ADD COLUMN IF NOT EXISTS live_spike_score NUMERIC(10, 1) DEFAULT 0.0,
            ADD COLUMN IF NOT EXISTS peak_spike_score NUMERIC(10, 1) DEFAULT 0.0,
            ADD COLUMN IF NOT EXISTS peak_spike_date DATE,
            ADD COLUMN IF NOT EXISTS best_spike_rank INT;

        CREATE INDEX IF NOT EXISTS idx_inbox_live_spike_score ON raw_trends_inbox (live_spike_score DESC);
        CREATE INDEX IF NOT EXISTS idx_inbox_peak_spike_score ON raw_trends_inbox (peak_spike_score DESC);

        CREATE TABLE IF NOT EXISTS cross_viral_daily_rankings (
            id BIGSERIAL PRIMARY KEY,
            ranking_date DATE NOT NULL,
            rank_position INT NOT NULL,
            inbox_id VARCHAR(255) NOT NULL REFERENCES raw_trends_inbox(inbox_id) ON DELETE CASCADE,
            item_id BIGINT NOT NULL,
            spike_score NUMERIC(10, 1) NOT NULL,
            raw_spike_score NUMERIC(10, 1) NOT NULL,
            spike_tier VARCHAR(50) NOT NULL,
            axes_count INT NOT NULL DEFAULT 1,
            sources_count INT NOT NULL DEFAULT 1,
            press_count INT NOT NULL DEFAULT 0,
            community_count INT NOT NULL DEFAULT 0,
            code_count INT NOT NULL DEFAULT 0,
            velocity NUMERIC(10, 2) NOT NULL DEFAULT 0.0,
            depth NUMERIC(10, 2) NOT NULL DEFAULT 0.0,
            canonical_release_key VARCHAR(150),
            title_snapshot TEXT NOT NULL,
            sources_snapshot JSONB DEFAULT '[]'::jsonb,
            recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (ranking_date, inbox_id)
        );

        CREATE INDEX IF NOT EXISTS idx_cv_daily_rankings_date_rank
            ON cross_viral_daily_rankings (ranking_date DESC, rank_position ASC);
        CREATE INDEX IF NOT EXISTS idx_cv_daily_rankings_item_id
            ON cross_viral_daily_rankings (item_id);
    """)

def upsert_daily_ranking_snapshot(cur, ranking_date_str, top_scored_items, peak_tracker):
    """
    Upserts the top cross-viral items for a given ranking_date_str (YYYY-MM-DD in KST)
    into cross_viral_daily_rankings in a single network round-trip, preserving the highest score
    achieved on that day and re-ranking positions 1..N cleanly.
    """
    if not top_scored_items:
        return 0

    from psycopg2.extras import execute_values
    snap_values = []
    for rank_pos, entry in enumerate(top_scored_items, 1):
        score, an, rd, rel_key = entry
        rid = rd["id"]
        inbox_id = rd["inbox_id"]
        title_snap = rd["raw_payload"].get("title_ko") or rd["title"] or ""
        sources_snap = json.dumps(rd["raw_payload"].get("sources") or [], ensure_ascii=False)

        snap_values.append((
            ranking_date_str, rank_pos, inbox_id, rid,
            score, an["raw_score"], an["tier"],
            an["axes_count"], an["sources_count"], an["press_count"], an["community_count"], an["code_count"],
            an["velocity"], an["depth"], rel_key or None, title_snap, sources_snap
        ))

        # Track historical peak score & best rank per item_id
        prev = peak_tracker.get(rid)
        if not prev:
            peak_tracker[rid] = {
                "peak_score": score,
                "peak_date": ranking_date_str,
                "best_rank": rank_pos
            }
        else:
            if score > prev["peak_score"]:
                prev["peak_score"] = score
                prev["peak_date"] = ranking_date_str
            if rank_pos < prev["best_rank"]:
                prev["best_rank"] = rank_pos

    upsert_sql = """
        INSERT INTO cross_viral_daily_rankings (
            ranking_date, rank_position, inbox_id, item_id,
            spike_score, raw_spike_score, spike_tier,
            axes_count, sources_count, press_count, community_count, code_count,
            velocity, depth, canonical_release_key, title_snapshot, sources_snapshot, recorded_at
        ) VALUES %s
        ON CONFLICT (ranking_date, inbox_id) DO UPDATE SET
            spike_score = GREATEST(cross_viral_daily_rankings.spike_score, EXCLUDED.spike_score),
            raw_spike_score = GREATEST(cross_viral_daily_rankings.raw_spike_score, EXCLUDED.raw_spike_score),
            spike_tier = CASE WHEN EXCLUDED.spike_score >= cross_viral_daily_rankings.spike_score THEN EXCLUDED.spike_tier ELSE cross_viral_daily_rankings.spike_tier END,
            axes_count = GREATEST(cross_viral_daily_rankings.axes_count, EXCLUDED.axes_count),
            sources_count = GREATEST(cross_viral_daily_rankings.sources_count, EXCLUDED.sources_count),
            press_count = GREATEST(cross_viral_daily_rankings.press_count, EXCLUDED.press_count),
            community_count = GREATEST(cross_viral_daily_rankings.community_count, EXCLUDED.community_count),
            code_count = GREATEST(cross_viral_daily_rankings.code_count, EXCLUDED.code_count),
            velocity = GREATEST(cross_viral_daily_rankings.velocity, EXCLUDED.velocity),
            depth = GREATEST(cross_viral_daily_rankings.depth, EXCLUDED.depth),
            canonical_release_key = COALESCE(EXCLUDED.canonical_release_key, cross_viral_daily_rankings.canonical_release_key),
            title_snapshot = EXCLUDED.title_snapshot,
            sources_snapshot = EXCLUDED.sources_snapshot,
            recorded_at = NOW();
    """
    template = "(%s::date, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, NOW())"
    execute_values(cur, upsert_sql, snap_values, template=template, page_size=100)

    # Re-normalize rank_position (1..N) ordered by spike_score DESC for that date
    cur.execute("""
        WITH ranked AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY spike_score DESC, sources_count DESC, item_id DESC) AS new_rank
            FROM cross_viral_daily_rankings
            WHERE ranking_date = %s::date
        )
        UPDATE cross_viral_daily_rankings c
        SET rank_position = r.new_rank
        FROM ranked r
        WHERE c.id = r.id;
    """, (ranking_date_str,))
    return len(top_scored_items)

def main():
    parser = argparse.ArgumentParser(description="Recompute H-V-D spike scores, cluster releases, and persist daily cross-viral rankings")
    parser.add_argument("--commit", action="store_true", help="Commit changes to database")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of rows (0 for all)")
    parser.add_argument("--window-days", type=int, default=14, help="Active scan window in days (0 for full table scan)")
    parser.add_argument("--all", action="store_true", help="Force full table scan across all historical rows")
    parser.add_argument("--backfill-days", type=int, default=0, help="Backfill historical daily rankings for the past N days (e.g. 30)")
    parser.add_argument("--top-daily", type=int, default=30, help="Max top spiking items to store per day in cross_viral_daily_rankings")
    parser.add_argument("--silent", action="store_true", help="Minimal clean output without verbose Top 15 listings")
    args = parser.parse_args()

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("[!] Error: DATABASE_URL not set.")
        sys.exit(1)

    t0 = datetime.now(timezone.utc)
    print("[*] Connecting to PostgreSQL SSOT...")
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    if args.commit:
        ensure_ranking_schema(cur)
        conn.commit()

    effective_window_days = 0 if args.all else max(args.window_days, (args.backfill_days + 7) if args.backfill_days > 0 else args.window_days)

    where_clauses = ["(triage_status IS NULL OR triage_status != 'archived')"]
    query_params = []
    if effective_window_days > 0:
        where_clauses.append("(created_at >= NOW() - (%s || ' days')::interval OR (raw_payload->>'is_cross_spiking') = 'true')")
        query_params.append(str(effective_window_days))

    query = f"""
        SELECT id, inbox_id, title, source_platform, source_url, viral_score, created_at, raw_payload, triage_status, curation_tier,
               COALESCE(peak_spike_score, 0.0), peak_spike_date, best_spike_rank, COALESCE(live_spike_score, 0.0)
        FROM raw_trends_inbox
        WHERE {' AND '.join(where_clauses)}
        ORDER BY id DESC
    """
    if args.limit > 0:
        query += f" LIMIT {int(args.limit)}"

    cur.execute(query, query_params)
    rows = cur.fetchall()
    print(f"[*] Loaded {len(rows)} active candidate rows (window={effective_window_days if effective_window_days > 0 else 'ALL'} days) in {(datetime.now(timezone.utc) - t0).total_seconds():.2f}s")

    now_utc = datetime.now(timezone.utc)
    row_dicts = []
    for r in rows:
        p = r[7] if isinstance(r[7], dict) else json.loads(r[7] or "{}")
        row_dicts.append({
            "id": r[0],
            "inbox_id": r[1] or str(r[0]),
            "title": r[2],
            "source_platform": r[3],
            "source_url": r[4],
            "viral_score": r[5],
            "created_at": r[6],
            "raw_payload": p,
            "triage_status": r[8],
            "curation_tier": r[9],
            "db_peak_score": float(r[10] or 0.0),
            "db_peak_date": r[11].isoformat() if r[11] else None,
            "db_best_rank": int(r[12]) if r[12] is not None else None,
            "db_live_score": float(r[13] or 0.0)
        })

    # Step 1: Cluster cross-platform named releases into unified hub stories
    cluster_window_days = max(7, args.backfill_days or 7)
    clusters = {}
    row_by_id = {rd["id"]: rd for rd in row_dicts}
    for rd in row_dicts:
        p = rd["raw_payload"]
        t_ko = p.get("title_ko") or (p.get("ai_enrichment") or {}).get("korean_title") or ""
        t_en = p.get("title_en") or ((p.get("multilingual") or {}).get("en") or {}).get("title") or ""
        s_key = p.get("canonical_story_key") or (p.get("ai_enrichment") or {}).get("canonical_story_key") or ""
        rel_key = extract_release_cluster_key(rd["title"], t_ko, s_key, t_en)
        rd["release_key"] = rel_key
        rd["title_en_best"] = t_en or rd["title"] or ""
        rd["tokens"] = extract_specific_tokens_py(rd["title_en_best"], rd.get("source_platform") or "")
        if rel_key:
            dt = parse_iso_or_default(rd["created_at"], now_utc)
            if (now_utc - dt).total_seconds() <= cluster_window_days * 86400:
                clusters.setdefault(rel_key, []).append(rd)

    archived_dup_ids = []
    archived_dup_payloads = []
    clustered_hub_ids = set()

    # Pre-fetch pairwise cosine similarities for all Step 1 cluster members in a single query
    cluster_member_ids = [rd["id"] for grp in clusters.values() if len(grp) >= 2 for rd in grp]
    cluster_sim_map = {}
    if cluster_member_ids:
        cur.execute("""
            SELECT a.id, b.id, (1 - (a.embedding <=> b.embedding)) as sim
            FROM raw_trends_inbox a
            JOIN raw_trends_inbox b ON a.id != b.id
            WHERE a.id = ANY(%s) AND b.id = ANY(%s)
              AND a.embedding IS NOT NULL AND b.embedding IS NOT NULL;
        """, (cluster_member_ids, cluster_member_ids))
        for aid, bid, sim_v in cur.fetchall():
            if sim_v is not None:
                cluster_sim_map[(int(aid), int(bid))] = round(float(sim_v), 4)

    for rel_key, group in clusters.items():
        if len(group) < 2:
            continue
        distinct_group_plats = {(x.get("source_platform") or "").strip().lower() for x in group}
        if len(distinct_group_plats) < 2 and any("youtube" in p for p in distinct_group_plats):
            continue
        group.sort(key=lambda x: (
            1 if x.get("curation_tier") == "DAILY_HOT" else 0,
            len(x["raw_payload"].get("sources") or []),
            0 if "[pdf]" in (x.get("title") or "").lower() else 1,
            1 if any(k in (x["source_platform"] or "").lower() for k in ["deepmind", "openai", "techcrunch", "geeknews", "hacker news"]) else 0,
            x["id"]
        ), reverse=True)
        hub = group[0]
        hub_plat = (hub.get("source_platform") or "").strip().lower()
        hub_dt = parse_iso_or_default(hub["created_at"], now_utc)
        hub_sources, _ = ensure_primary_in_sources(hub, hub_dt)
        existing_urls = {(s.get("url") or s.get("source_url") or "").strip() for s in hub_sources if isinstance(s, dict)}
        hub_toks = hub.get("tokens") or []

        merged_any = False
        for sec in group[1:]:
            sec_plat = (sec.get("source_platform") or "").strip().lower()
            if "youtube" in hub_plat and sec_plat == hub_plat:
                continue
            sec_dt = parse_iso_or_default(sec["created_at"], now_utc)
            sec_sources, _ = ensure_primary_in_sources(sec, sec_dt)
            pair_sim = cluster_sim_map.get((hub["id"], sec["id"]))
            sec_tok_set = set(sec.get("tokens") or [])
            shared_cluster_toks = [t for t in hub_toks if t in sec_tok_set]
            for s in sec_sources:
                s_url = (s.get("url") or s.get("source_url") or "").strip()
                if s_url and s_url not in existing_urls:
                    s_copy = dict(s)
                    s_copy["type"] = "discussion"
                    if s_copy.get("similarity") is None and pair_sim is not None:
                        s_copy["similarity"] = pair_sim
                    s_copy.setdefault("match_method", f"RELEASE_CLUSTER ({rel_key})")
                    hub_sources.append(s_copy)
                    existing_urls.add(s_url)
            sec["raw_payload"]["merged_into"] = {
                "hub_id": hub["id"],
                "similarity": pair_sim,
                "shared_tokens": shared_cluster_toks,
                "method": f"RELEASE_CLUSTER ({rel_key})",
                "merged_at": now_utc.isoformat()
            }
            archived_dup_ids.append(sec["id"])
            archived_dup_payloads.append((sec["id"], json.dumps(sec["raw_payload"], ensure_ascii=False)))
            merged_any = True

        if merged_any:
            hub["raw_payload"]["sources"] = hub_sources
            hub["raw_payload"]["has_multi_sources"] = len(hub_sources) > 1
            hub["raw_payload"]["is_cross_spiking"] = len(hub_sources) > 1
            clustered_hub_ids.add(hub["id"])
            print(f"[+] Clustered '{rel_key}' -> Hub ID {hub['id']} ({hub['title'][:50]}) with {len(hub_sources)} total cross-platform sources")

    # Step 1.5: Retrospective HNSW Vector + Token-Overlap Deduplication & Trace Recording (7-Day Active Window)
    archived_set = set(archived_dup_ids)
    recent_active_ids = [
        rd["id"] for rd in row_dicts
        if rd["id"] not in archived_set and (now_utc - parse_iso_or_default(rd["created_at"], now_utc)).total_seconds() <= 7 * 86400
    ]
    if recent_active_ids:
        cur.execute("""
            SELECT a.id as a_id, b.id as b_id, (1 - (a.embedding <=> b.embedding)) as sim
            FROM UNNEST(%s::bigint[]) AS aid
            JOIN raw_trends_inbox a ON a.id = aid
            CROSS JOIN LATERAL (
                SELECT id, embedding
                FROM raw_trends_inbox
                WHERE id != a.id
                  AND created_at >= NOW() - INTERVAL '14 days'
                  AND (triage_status IS NULL OR triage_status != 'archived')
                  AND embedding IS NOT NULL
                ORDER BY a.embedding <=> embedding
                LIMIT 5
            ) b
            WHERE a.embedding IS NOT NULL
              AND (a.embedding <=> b.embedding) <= 0.35
            ORDER BY sim DESC;
        """, (recent_active_ids,))
        vec_pairs = cur.fetchall()

        trace_map = {}
        def add_trace(aid, bid, sim_val, shared_toks, decision_str):
            rd_b = row_by_id.get(bid)
            if not rd_b:
                return
            lst = trace_map.setdefault(aid, [])
            if len(lst) >= 3 or any(x.get("peer_id") == bid for x in lst):
                return
            lst.append({
                "peer_id": bid,
                "peer_title": (rd_b.get("title") or "")[:100],
                "similarity": round(float(sim_val), 4),
                "shared_tokens": shared_toks,
                "decision": decision_str
            })

        hub_redirect = {}
        def resolve_hub(item_id):
            c = item_id
            vis = set()
            while c in hub_redirect and c not in vis:
                vis.add(c)
                c = hub_redirect[c]
            return c

        seen_pairs = set()
        for a_id, b_id, sim_val in vec_pairs:
            a_id, b_id = int(a_id), int(b_id)
            sim_f = float(sim_val or 0.0)
            rd_a = row_by_id.get(a_id)
            rd_b = row_by_id.get(b_id)
            if not rd_a or not rd_b:
                continue
            if a_id in archived_set and a_id not in hub_redirect:
                continue
            if b_id in archived_set and b_id not in hub_redirect:
                continue

            tok_a = rd_a.get("tokens") or []
            tok_b_set = set(rd_b.get("tokens") or [])
            shared_toks = [t for t in tok_a if t in tok_b_set]
            specific_shared = [t for t in shared_toks if t not in BROAD_ENTITY_TOKENS_PY]

            if sim_f < 0.78:
                add_trace(a_id, b_id, sim_f, shared_toks, "BELOW_THRESHOLD")
                continue

            # Do not merge two different canonical release hubs
            rel_a = rd_a.get("release_key") or ""
            rel_b = rd_b.get("release_key") or ""
            if rel_a and rel_b and rel_a != rel_b:
                add_trace(a_id, b_id, sim_f, shared_toks, "REJECTED_RELEASE_CONFLICT")
                continue
            if (a_id in clustered_hub_ids or b_id in clustered_hub_ids) and len(specific_shared) < 2:
                add_trace(a_id, b_id, sim_f, shared_toks, "REJECTED_CANONICAL_HUB_LOCK")
                continue

            # Version / Build Number Conflict Veto (e.g. b11397 vs b11411, 0.162.0-alpha.14 vs alpha.12)
            if has_version_conflict_py(rd_a.get("title_en_best", ""), rd_b.get("title_en_best", "")):
                add_trace(a_id, b_id, sim_f, shared_toks, "REJECTED_VERSION_CONFLICT")
                continue

            norm_p_a = (rd_a.get("source_platform") or "").strip().lower()
            norm_p_b = (rd_b.get("source_platform") or "").strip().lower()
            url_a = (rd_a.get("source_url") or "").strip()
            url_b = (rd_b.get("source_url") or "").strip()
            if norm_p_a and norm_p_a == norm_p_b and "youtube" in norm_p_a and url_a != url_b:
                add_trace(a_id, b_id, sim_f, shared_toks, "REJECTED_SAME_YOUTUBE_CHANNEL")
                continue

            low_a = normalize_for_tokens_py(rd_a.get("title_en_best", ""), rd_a.get("source_platform") or "")
            low_b = normalize_for_tokens_py(rd_b.get("title_en_best", ""), rd_b.get("source_platform") or "")
            ents_a = [e for e in MAJOR_ENTITIES_PY if e in low_a]
            ents_b = [e for e in MAJOR_ENTITIES_PY if e in low_b]
            if ents_a and ents_b and not any(e in ents_b for e in ents_a):
                add_trace(a_id, b_id, sim_f, shared_toks, "REJECTED_ENTITY_VETO")
                continue

            # Same-platform items (e.g. two HuggingFace models or two GitHub repos) must share at least 2 specific tokens even at high vector similarity
            if norm_p_a == norm_p_b and len(specific_shared) < 2:
                add_trace(a_id, b_id, sim_f, shared_toks, "REJECTED_SAME_PLATFORM_LOW_SPECIFIC_TOKENS")
                continue

            if sim_f >= 0.88 and len(shared_toks) >= 1:
                method = "VECTOR_HIGH (>=0.88)"
            elif sim_f >= 0.78 and len(shared_toks) >= 2 and len(specific_shared) >= 2:
                method = f"TOKEN_OVERLAP ({','.join(shared_toks[:4])})"
            else:
                add_trace(a_id, b_id, sim_f, shared_toks, "REJECTED_AMBIGUOUS_LOW_OVERLAP")
                continue

            add_trace(a_id, b_id, sim_f, shared_toks, method)
            add_trace(b_id, a_id, sim_f, shared_toks, method)

            pkey = (min(a_id, b_id), max(a_id, b_id))
            if pkey in seen_pairs:
                continue
            seen_pairs.add(pkey)

            res_a = resolve_hub(a_id)
            res_b = resolve_hub(b_id)
            if res_a == res_b:
                continue

            rd_res_a = row_by_id.get(res_a)
            rd_res_b = row_by_id.get(res_b)
            if not rd_res_a or not rd_res_b:
                continue

            # Prefer the row with more existing sources, or older ID
            len_a = len(rd_res_a["raw_payload"].get("sources") or [])
            len_b = len(rd_res_b["raw_payload"].get("sources") or [])
            if len_b > len_a or (len_b == len_a and res_b < res_a):
                hub_rd, sec_rd = rd_res_b, rd_res_a
            else:
                hub_rd, sec_rd = rd_res_a, rd_res_b

            hub_dt = parse_iso_or_default(hub_rd["created_at"], now_utc)
            sec_dt = parse_iso_or_default(sec_rd["created_at"], now_utc)
            hub_sources, _ = ensure_primary_in_sources(hub_rd, hub_dt)
            sec_sources, _ = ensure_primary_in_sources(sec_rd, sec_dt)
            existing_urls = {(s.get("url") or s.get("source_url") or "").strip() for s in hub_sources if isinstance(s, dict)}

            for s in sec_sources:
                s_url = (s.get("url") or s.get("source_url") or "").strip()
                if s_url and s_url not in existing_urls:
                    s_copy = dict(s)
                    s_copy["type"] = "discussion"
                    s_copy["similarity"] = round(sim_f, 4)
                    s_copy["match_method"] = method
                    hub_sources.append(s_copy)
                    existing_urls.add(s_url)

            hub_rd["raw_payload"]["sources"] = hub_sources
            hub_rd["raw_payload"]["has_multi_sources"] = len(hub_sources) > 1
            hub_rd["raw_payload"]["is_cross_spiking"] = len(hub_sources) > 1
            clustered_hub_ids.add(hub_rd["id"])

            sec_rd["raw_payload"]["merged_into"] = {
                "hub_id": hub_rd["id"],
                "similarity": round(sim_f, 4),
                "method": method,
                "shared_tokens": shared_toks,
                "merged_at": now_utc.isoformat()
            }
            hub_redirect[sec_rd["id"]] = hub_rd["id"]
            archived_set.add(sec_rd["id"])
            archived_dup_ids.append(sec_rd["id"])
            archived_dup_payloads.append((sec_rd["id"], json.dumps(sec_rd["raw_payload"], ensure_ascii=False)))
            print(f"[+] Vector+Token Merged ({sim_f:.4f} | {method}) ID {sec_rd['id']} -> Hub ID {hub_rd['id']} ({hub_rd['title'][:50]})")

        for aid, traces in trace_map.items():
            rd_t = row_by_id.get(aid)
            if rd_t and rd_t["raw_payload"].get("dedup_trace") != traces:
                rd_t["raw_payload"]["dedup_trace"] = traces
                rd_t["trace_updated"] = True

    active_rows = [rd for rd in row_dicts if rd["id"] not in archived_set]

    # Track peak score & best rank across historical backfill + today
    peak_tracker = {}
    for rd in active_rows:
        if rd["db_peak_score"] > 0:
            peak_tracker[rd["id"]] = {
                "peak_score": rd["db_peak_score"],
                "peak_date": rd["db_peak_date"],
                "best_rank": rd["db_best_rank"] or 999
            }

    def get_earliest_dt(rd, default_dt):
        base_dt = parse_iso_or_default(rd.get("created_at"), default_dt)
        sources = (rd.get("raw_payload") or {}).get("sources") or []
        earliest = base_dt
        for s in sources:
            if isinstance(s, dict):
                s_dt = parse_iso_or_default(s.get("created_at") or s.get("original_created_at") or s.get("published_at"), base_dt)
                if s_dt < earliest:
                    earliest = s_dt
        return earliest

    # Step 2 (Optional): Backfill Historical Daily Rankings (--backfill-days N)
    if args.commit and args.backfill_days > 0:
        today_kst_date = now_utc.astimezone(KST_TZ).date()
        print(f"\n[*] Running Historical Time-Machine Backfill for the past {args.backfill_days} days...")
        total_snapshots_saved = 0
        for day_offset in range(args.backfill_days, 0, -1):
            target_date = today_kst_date - timedelta(days=day_offset)
            target_date_str = target_date.isoformat()
            # Simulate 23:59:59 KST on target_date
            sim_kst_dt = datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59, tzinfo=KST_TZ)
            sim_utc_dt = sim_kst_dt.astimezone(timezone.utc)

            day_candidates = []
            for rd in active_rows:
                item_dt = get_earliest_dt(rd, now_utc)
                age_sec = (sim_utc_dt - item_dt).total_seconds()
                # Must have been first spotted on or before sim_utc_dt, and within the 7-day active window of that date
                if age_sec < 0 or age_sec > 7 * 86400:
                    continue
                sim_score, sim_spiking, sim_an, _ = compute_hvd_score(rd, sim_utc_dt)
                if sim_spiking and sim_score >= 0.5:
                    day_candidates.append((sim_score, sim_an, rd, rd.get("release_key")))

            day_candidates.sort(key=lambda x: (x[0], x[1]["sources_count"], x[2]["id"]), reverse=True)
            top_day = day_candidates[:args.top_daily]
            if top_day:
                cur.execute("DELETE FROM cross_viral_daily_rankings WHERE ranking_date = %s::date;", (target_date_str,))
                saved = upsert_daily_ranking_snapshot(cur, target_date_str, top_day, peak_tracker)
                total_snapshots_saved += saved
                top1_score, top1_an, top1_rd, _ = top_day[0]
                print(f"   📅 [{target_date_str}] Saved {saved:2d} rankings | #1: [{top1_score:5.1f} pts] {top1_rd['title'][:58]}")
        conn.commit()
        print(f"[+] Historical Backfill Complete: {total_snapshots_saved} daily ranking records persisted.")

    # Step 3: Recompute LIVE H-V-D scores across all active rows right now
    scored_items = []
    today_ranking_candidates = []
    spike_count = 0
    super_spike_count = 0
    cross_spike_count = 0
    healed_count = 0

    today_kst_str = now_utc.astimezone(KST_TZ).date().isoformat()

    for row_data in active_rows:
        score, is_spiking, analysis, was_healed = compute_hvd_score(row_data, now_utc)
        if was_healed:
            healed_count += 1

        row_data["live_score"] = score
        row_data["live_spiking"] = is_spiking
        row_data["live_analysis"] = analysis
        row_data["was_healed"] = was_healed

        if is_spiking:
            spike_count += 1
            if analysis["axes_count"] >= 3:
                super_spike_count += 1
            elif analysis["axes_count"] == 2:
                cross_spike_count += 1
            scored_items.append((score, analysis, row_data["title"], row_data["id"]))

            item_dt = parse_iso_or_default(row_data["created_at"], now_utc)
            if (now_utc - item_dt).total_seconds() <= 7 * 86400:
                today_ranking_candidates.append((score, analysis, row_data, row_data.get("release_key")))

    scored_items.sort(key=lambda x: x[0], reverse=True)
    today_ranking_candidates.sort(key=lambda x: (x[0], x[1]["sources_count"], x[2]["id"]), reverse=True)

    # Upsert today's top rankings into cross_viral_daily_rankings and update peak_tracker
    if args.commit and today_ranking_candidates:
        upsert_daily_ranking_snapshot(cur, today_kst_str, today_ranking_candidates[:args.top_daily], peak_tracker)

    # Prepare raw_trends_inbox updates using strict Dirty-Check (only write rows whose multi-source state or score actually changed)
    updates = []
    for row_data in active_rows:
        rid = row_data["id"]
        score = row_data["live_score"]
        is_spiking = row_data["live_spiking"]
        analysis = row_data["live_analysis"]
        was_healed = row_data["was_healed"]

        trace_updated = bool(row_data.get("trace_updated"))
        old_spk = bool(row_data["raw_payload"].get("is_cross_spiking"))
        is_multi = bool(analysis["sources_count"] >= 2 or analysis["axes_count"] >= 2 or is_spiking or old_spk)

        # Single-source non-spiking items that were not healed and not clustered and have no trace update do not need DB writes
        if not is_multi and not was_healed and rid not in clustered_hub_ids and not trace_updated:
            continue

        pk = peak_tracker.get(rid)
        peak_score = max(score, pk["peak_score"] if pk else 0.0)
        peak_date = (pk["peak_date"] if (pk and pk["peak_score"] >= score and pk["peak_date"]) else (today_kst_str if score > 0 else None))
        best_rank = pk["best_rank"] if (pk and pk["best_rank"] < 999) else None

        if peak_score > 0:
            analysis["peak_score"] = round(peak_score, 1)
            analysis["peak_date"] = peak_date
        if best_rank is not None:
            analysis["best_rank"] = best_rank

        old_an = row_data["raw_payload"].get("spike_analysis") or {}
        score_changed = abs(float(old_an.get("score", -1.0)) - score) >= 0.1 or abs(row_data["db_live_score"] - score) >= 0.1
        spk_changed = (old_spk != is_spiking)
        src_changed = (int(old_an.get("sources_count", -1)) != int(analysis["sources_count"]))
        peak_changed = (abs(row_data["db_peak_score"] - peak_score) >= 0.1) or (row_data["db_best_rank"] != best_rank)

        if was_healed or rid in clustered_hub_ids or score_changed or spk_changed or src_changed or peak_changed or trace_updated:
            new_payload = dict(row_data["raw_payload"])
            new_payload["spike_analysis"] = analysis
            new_payload["is_cross_spiking"] = is_spiking
            updates.append((
                rid,
                json.dumps(new_payload, ensure_ascii=False),
                score,
                peak_score,
                peak_date,
                best_rank
            ))

    if not args.silent:
        print("\n" + "="*80)
        print(f"📊 [H-V-D TRIPOD SCORING RESULTS] Total Active Analyzed: {len(active_rows)}")
        print(f"   - Self-Healed Missing Primary Sources : {healed_count} rows")
        print(f"   - Active Spiking Stories              : {spike_count}")
        print(f"   - 🔥 3-Axis Super Spikes              : {super_spike_count}")
        print(f"   - ⚡ 2-Axis Cross Spikes              : {cross_spike_count}")
        print(f"   - 📅 Today's ({today_kst_str}) Persisted Top Rankings : {min(len(today_ranking_candidates), args.top_daily)}")
        print(f"   - ⚡ Dirty-Checked Rows Needing Write : {len(updates)} rows (Skipped {len(active_rows) - len(updates)} unchanged rows)")
        print("="*80)
        print("🏆 Top 15 Highest Spiking Stories Right Now:")
        for rank, (score, an, title, rid) in enumerate(scored_items[:15], 1):
            pk_info = f" | Peak #{an.get('best_rank', rank)} ({an.get('peak_score', score)}p)" if an.get("best_rank") else ""
            print(f"  #{rank:>2} [{score:>6.1f} pts] {an['tier']:<20} (Sources: {an['sources_count']}|P:{an['press_count']}|C:{an['community_count']}|K:{an['code_count']}){pk_info}")
            print(f"       ID {rid}: {title[:75]}")
    else:
        print(f"[H-V-D Spike] Analyzed {len(active_rows)} stories -> {len(updates)} updates, {min(len(today_ranking_candidates), args.top_daily)} rankings.")

    if args.commit:
        from psycopg2.extras import execute_values
        t_write = datetime.now(timezone.utc)
        if archived_dup_payloads:
            dup_sql = """
                UPDATE raw_trends_inbox AS t
                SET triage_status = 'archived',
                    curation_tier = 'duplicate',
                    raw_payload = v.payload::jsonb,
                    updated_at = NOW()
                FROM (VALUES %s) AS v(id, payload)
                WHERE t.id = v.id::bigint;
            """
            execute_values(cur, dup_sql, archived_dup_payloads, page_size=500)
            print(f"[*] Archived {len(archived_dup_payloads)} cross-platform duplicate rows (with merged_into trace) into their primary hubs.")
        if updates:
            print(f"[*] Committing updates for {len(updates)} dirty-checked rows via single-RTT execute_values...")
            bulk_sql = """
                UPDATE raw_trends_inbox AS t
                SET raw_payload = v.payload::jsonb,
                    live_spike_score = v.live_score::numeric,
                    peak_spike_score = GREATEST(COALESCE(t.peak_spike_score, 0.0), v.peak_score::numeric),
                    peak_spike_date = COALESCE(v.peak_date::date, t.peak_spike_date),
                    best_spike_rank = CASE
                        WHEN v.best_rank IS NULL THEN t.best_spike_rank
                        WHEN t.best_spike_rank IS NULL THEN v.best_rank::integer
                        ELSE LEAST(t.best_spike_rank, v.best_rank::integer)
                    END,
                    updated_at = NOW()
                FROM (VALUES %s) AS v(id, payload, live_score, peak_score, peak_date, best_rank)
                WHERE t.id = v.id::bigint;
            """
            execute_values(cur, bulk_sql, updates, page_size=500)
        conn.commit()
        print(f"[+] DB Update & Daily Ranking Snapshot Persistence 100% Complete in {(datetime.now(timezone.utc) - t_write).total_seconds():.2f}s! (Total elapsed: {(datetime.now(timezone.utc) - t0).total_seconds():.2f}s)")
    else:
        print("\n[!] Dry run mode. Run with --commit to apply changes to database.")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()

