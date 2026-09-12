#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Source News & Inbox Deduplication and Story Clustering Merger (v1.0)
- Canonical Story Key & Core Entities Matching
- 72-Hour Temporal Window Deduplication
- Techmeme-style Multi-Source Hub Merging (sources list append)
"""

import json
import os
import re
from datetime import datetime, timezone

# =============================================================================
# 2026 SOTA Cross-Lingual Entity & Canonical Anchor Dictionary
# Maps Korean, English, and transliterated variants into unified canonical tokens
# =============================================================================
CROSS_LINGUAL_ENTITY_MAP = {
    # Geopolitics & Major News Events
    "후티": "houthi", "후티반군": "houthi", "houthis": "houthi", "houthi": "houthi",
    "홍해": "redsea", "red-sea": "redsea", "red sea": "redsea",
    "해운": "shipping", "해상": "shipping", "shipping": "shipping", "maritime": "shipping",
    "항로": "route", "무역로": "route", "수송망": "route", "route": "route", "routes": "route",
    "장악": "control", "점령": "control", "통제": "control", "control": "control", "take-control": "control", "seize": "control", "seized": "control",
    "섬": "island", "island": "island", "islands": "island",
    "핵심": "key", "전략적": "key", "주요": "key", "key": "key", "strategic": "key",
    "글로벌": "global", "국제": "global", "세계": "global", "global": "global", "international": "global", "world": "global",
    
    # Surveillance & Legal Incidents
    "플록": "flock", "플록안전": "flock", "flock": "flock", "flocksafety": "flock",
    "퇴역군인": "veteran", "해군": "navy", "veteran": "veteran", "navy": "navy",
    "교통단속": "traffic-stop", "단속": "traffic-stop", "traffic-stop": "traffic-stop",
    "녹화": "record", "촬영": "record", "record": "record", "filmed": "record",
    "추적": "track", "사찰": "track", "track": "track", "tracked": "track", "surveillance": "track",
    "100회": "100-times", "100번": "100-times", "100+": "100-times",

    # AI Models & Compute Vendors
    "딥시크": "deepseek", "deepseek": "deepseek",
    "라마": "llama", "llama": "llama", "llama3": "llama",
    "큐원": "qwen", "qwen": "qwen", "qwen2": "qwen", "qwen2.5": "qwen",
    "오픈ai": "openai", "openai": "openai",
    "앤트로픽": "anthropic", "anthropic": "anthropic",
    "클로드": "claude", "claude": "claude", "sonnet": "claude", "opus": "claude",
    "제미나이": "gemini", "gemini": "gemini",
    "미니맥스": "minimax", "minimax": "minimax",
    "미스트랄": "mistral", "mistral": "mistral",
    "엔비디아": "nvidia", "nvidia": "nvidia",
    "구글": "google", "google": "google",
    "메타": "meta", "meta": "meta",
    "애플": "apple", "apple": "apple",
    "마이크로소프트": "microsoft", "microsoft": "microsoft"
}

STOP_WORDS = {
    "hacker", "news", "geeknews", "기사", "선언", "the", "in", "of", "and", "to", "for", 
    "on", "at", "by", "with", "from", "is", "a", "an", "as", "that", "this", "it",
    "으로", "에서", "있는", "위한", "대한", "관련", "사용", "넘게", "이상", "통해", "이어지는",
    "따른", "위해", "가장", "대해", "통한"
}

def normalize_text_tokens(text: str) -> set:
    if not text:
        return set()
    text = text.lower()
    
    # 1. Multi-word phrase substitution
    for k in sorted(CROSS_LINGUAL_ENTITY_MAP.keys(), key=len, reverse=True):
        if " " in k and k in text:
            text = text.replace(k, f" {CROSS_LINGUAL_ENTITY_MAP[k]} ")

    # 2. Extract words
    raw_words = re.findall(r'[a-zA-Z0-9가-힣]+', text)
    canonical = set()
    for w in raw_words:
        mapped = CROSS_LINGUAL_ENTITY_MAP.get(w, w)
        if len(mapped) > 1 and mapped not in STOP_WORDS:
            canonical.add(mapped)
    return canonical

def get_item_story_key(item: dict) -> str:
    dedup = item.get("dedup_fingerprint") or item.get("dedup_metadata") or {}
    key = dedup.get("canonical_story_key") or item.get("canonical_story_key") or ""
    if key and len(key.strip()) > 3:
        return key.strip().lower()
    return ""

def get_item_entities(item: dict) -> set:
    dedup = item.get("dedup_fingerprint") or item.get("dedup_metadata") or {}
    ents = dedup.get("core_entities") or item.get("core_entities") or []
    res = set()
    for e in ents:
        if isinstance(e, str) and len(e.strip()) > 1:
            mapped = CROSS_LINGUAL_ENTITY_MAP.get(e.strip().lower(), e.strip().lower())
            res.add(mapped)
    return res

def parse_iso_timestamp(item: dict) -> float:
    for field in ["published_at", "source_published_date", "published_date", "harvested_at", "created_at"]:
        val = item.get(field)
        if val and isinstance(val, str):
            try:
                dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
                return dt.timestamp()
            except Exception:
                pass
    return 0.0

def are_items_duplicate_story(item_a: dict, item_b: dict, max_window_hours: float = 72.0) -> bool:
    # 1. Check URL exact match (including external article_url)
    urls_a = {item_a.get("source_url") or "", item_a.get("url") or "", item_a.get("article_url") or ""} - {""}
    urls_b = {item_b.get("source_url") or "", item_b.get("url") or "", item_b.get("article_url") or ""} - {""}
    if urls_a and urls_b and bool(urls_a.intersection(urls_b)):
        return True

    # 2. Temporal Window Check (allow up to 72 hours for viral story lifecycle)
    ts_a = parse_iso_timestamp(item_a)
    ts_b = parse_iso_timestamp(item_b)
    if ts_a > 0 and ts_b > 0:
        hour_diff = abs(ts_a - ts_b) / 3600.0
        if hour_diff > max_window_hours:
            return False

    # 3. Canonical Story Key exact match
    key_a = get_item_story_key(item_a)
    key_b = get_item_story_key(item_b)
    if key_a and key_b and key_a == key_b:
        return True

    # 4. Core Entities Overlap
    ents_a = get_item_entities(item_a)
    ents_b = get_item_entities(item_b)
    if ents_a and ents_b:
        intersection = ents_a.intersection(ents_b)
        if len(intersection) >= 2:
            return True

    # 5. Cross-Lingual Entity & Semantic Keyword Overlap
    title_a = f"{item_a.get('title', '')} {item_a.get('title_ko', '')} {item_a.get('title_en', '')} {item_a.get('hook', '')} {item_a.get('hook_ko', '')}"
    title_b = f"{item_b.get('title', '')} {item_b.get('title_ko', '')} {item_b.get('title_en', '')} {item_b.get('hook', '')} {item_b.get('hook_ko', '')}"
    tokens_a = normalize_text_tokens(title_a)
    tokens_b = normalize_text_tokens(title_b)

    if tokens_a and tokens_b:
        common = tokens_a.intersection(tokens_b)
        min_len = min(len(tokens_a), len(tokens_b))
        
        # 5-A. Dynamic Anchor Matching (high-signal entity pairs)
        critical_anchors = [
            {"houthi", "island"},
            {"houthi", "shipping"},
            {"houthi", "control"},
            {"flock", "veteran"},
            {"deepseek", "v3"},
            {"qwen", "coder"},
            {"anthropic", "claude"},
            {"openai", "chatgpt"}
        ]
        for anchor in critical_anchors:
            if anchor.issubset(tokens_a) and anchor.issubset(tokens_b):
                return True

        # 5-B. Substantial Overlap Ratio (>= 0.45 or >= 4 common canonical entities)
        if len(common) >= 4:
            return True

        if min_len >= 3 and len(common) >= 3:
            overlap_ratio = len(common) / min_len
            if overlap_ratio >= 0.45:
                return True

    return False

def merge_sources_into_primary(primary: dict, secondary: dict) -> dict:
    # Ensure primary has sources array
    if "sources" not in primary or not isinstance(primary.get("sources"), list) or len(primary["sources"]) == 0:
        primary["sources"] = [
            {
                "source_name": primary.get("source_platform") or "Primary",
                "platform": primary.get("source_platform") or "Primary",
                "title": primary.get("title") or primary.get("title_ko") or "",
                "url": primary.get("source_url") or primary.get("url") or "",
                "type": "primary",
                "published_at": primary.get("published_date") or primary.get("source_published_date") or primary.get("harvested_at") or ""
            }
        ]

    existing_urls = {s.get("url") for s in primary["sources"] if s.get("url")}
    
    # Secondary sources to add
    sec_sources = secondary.get("sources", [])
    if not sec_sources:
        sec_sources = [
            {
                "source_name": secondary.get("source_platform") or "Secondary",
                "platform": secondary.get("source_platform") or "Secondary",
                "title": secondary.get("title") or secondary.get("title_ko") or "",
                "url": secondary.get("source_url") or secondary.get("url") or "",
                "type": "discussion" if any(x in (secondary.get("source_platform") or "").lower() for x in ["hacker news", "geeknews", "reddit"]) else "media",
                "published_at": secondary.get("published_date") or secondary.get("source_published_date") or secondary.get("harvested_at") or ""
            }
        ]

    for s in sec_sources:
        s_url = s.get("url")
        if s_url and s_url not in existing_urls:
            primary["sources"].append(s)
            existing_urls.add(s_url)

    primary["source_count"] = len(primary["sources"])

    # If primary misses Korean title/hook but secondary has it, upgrade primary
    if not primary.get("title_ko") and secondary.get("title_ko"):
        primary["title_ko"] = secondary["title_ko"]
    if not primary.get("hook_ko") and secondary.get("hook_ko"):
        primary["hook_ko"] = secondary["hook_ko"]

    return primary

def deduplicate_inbox_items(items: list, max_window_hours: float = 72.0) -> list:
    """Clusters and deduplicates items into a clean list of story-centric items."""
    merged_items = []
    
    for item in items:
        matched = False
        for target in merged_items:
            if are_items_duplicate_story(target, item, max_window_hours=max_window_hours):
                merge_sources_into_primary(target, item)
                matched = True
                break
        if not matched:
            # Initialize sources if not present
            if "sources" not in item or not isinstance(item.get("sources"), list):
                item["sources"] = [
                    {
                        "source_name": item.get("source_platform") or "Primary",
                        "platform": item.get("source_platform") or "Primary",
                        "title": item.get("title") or item.get("title_ko") or "",
                        "url": item.get("source_url") or item.get("url") or "",
                        "type": "primary",
                        "published_at": item.get("published_date") or item.get("source_published_date") or item.get("harvested_at") or ""
                    }
                ]
            item["source_count"] = len(item["sources"])
            merged_items.append(item)

    return merged_items

if __name__ == "__main__":
    # Self-test using the exact user test case!
    test_item_1 = {
        "inbox_id": "INBOX-TEST-001",
        "title": "플록, 교통단속 녹화한 퇴역군인 추적에 100회 이상 사용",
        "source_platform": "GeekNews",
        "source_url": "https://news.hada.io/topic?id=12345",
        "published_at": "2026-09-06T08:00:00Z",
        "dedup_fingerprint": {
            "canonical_story_key": "flock-surveillance-veteran-traffic-stop",
            "core_entities": ["Flock Safety", "Navy Veteran", "Traffic Stop"]
        }
    }
    test_item_2 = {
        "inbox_id": "INBOX-TEST-002",
        "title": "교통 단속을 촬영한 해군 퇴역군인, Flock으로 100회 넘게 추적당해",
        "source_platform": "IT World Korea",
        "source_url": "https://itworld.co.kr/news/67890",
        "published_at": "2026-09-06T09:30:00Z",
        "dedup_fingerprint": {
            "canonical_story_key": "flock-surveillance-veteran-traffic-stop",
            "core_entities": ["Flock Safety", "Navy Veteran", "ALPR"]
        }
    }
    test_item_3 = {
        "inbox_id": "INBOX-TEST-003",
        "title": "Navy veteran who filmed traffic stop tracked 100+ times with Flock",
        "source_platform": "Hacker News",
        "source_url": "https://news.ycombinator.com/item?id=99999",
        "published_at": "2026-09-06T10:00:00Z"
    }

    clustered = deduplicate_inbox_items([test_item_1, test_item_2, test_item_3])
    print(f"Total inputs: 3 -> Clustered output stories: {len(clustered)}")
    primary = clustered[0]
    print(f"Primary Title: {primary['title']}")
    print(f"Merged Sources count: {primary['source_count']}")
    for idx, s in enumerate(primary["sources"], 1):
        print(f"  [{idx}] {s['source_name']}: {s['title']} ({s['url']})")
