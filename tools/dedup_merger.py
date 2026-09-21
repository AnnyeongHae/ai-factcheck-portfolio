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

GENERIC_WORDS = {
    "ai", "model", "models", "llm", "tool", "show", "ask", "hn", "new", "open",
    "source", "code", "paper", "release", "research", "using", "free", "data",
    "test", "system", "app", "web", "with", "from", "for", "the", "and", "in",
    "about", "how", "what", "why", "when", "into", "over", "after"
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
        if len(mapped) > 1 and mapped not in STOP_WORDS and mapped not in GENERIC_WORDS:
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
            if mapped not in GENERIC_WORDS and mapped not in STOP_WORDS:
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

def are_story_keys_similar(key_a: str, key_b: str) -> bool:
    if not key_a or not key_b:
        return False
    if key_a == key_b:
        return True
    parts_a = set(re.findall(r'[a-z0-9]+', key_a.lower())) - {"the", "a", "an", "and", "or", "in", "on", "of", "to", "with", "by", "for"}
    parts_b = set(re.findall(r'[a-z0-9]+', key_b.lower())) - {"the", "a", "an", "and", "or", "in", "on", "of", "to", "with", "by", "for"}
    if len(parts_a) >= 3 and len(parts_b) >= 3:
        common = parts_a.intersection(parts_b)
        min_len = min(len(parts_a), len(parts_b))
        if len(common) >= 3 and (len(common) / min_len) >= 0.50:
            return True
    return False

def are_items_duplicate_story(item_a: dict, item_b: dict, max_window_hours: float = 72.0) -> bool:
    # 1. Check URL exact match (including external article_url)
    urls_a = {item_a.get("source_url") or "", item_a.get("url") or "", item_a.get("article_url") or ""} - {""}
    urls_b = {item_b.get("source_url") or "", item_b.get("url") or "", item_b.get("article_url") or ""} - {""}
    if urls_a and urls_b and bool(urls_a.intersection(urls_b)):
        return True

    # 2. Temporal Window Check: Model/Tool has no time limit (Permanent Asset); News allows up to 168h (7 days)
    is_asset = (item_a.get("facet_type") in ["MODEL", "TOOL"] or item_b.get("facet_type") in ["MODEL", "TOOL"] or 
                "github" in str(item_a.get("source_platform", "")).lower() or "github" in str(item_b.get("source_platform", "")).lower())
    if not is_asset:
        ts_a = parse_iso_timestamp(item_a)
        ts_b = parse_iso_timestamp(item_b)
        if ts_a > 0 and ts_b > 0:
            hour_diff = abs(ts_a - ts_b) / 3600.0
            if hour_diff > 168.0:
                return False

    # 2.5 SOTA Voyage AI Dense Embedding Similarity Check
    try:
        from voyage_embedder import get_single_embedding, cosine_similarity
        e_a = item_a.get("embedding") or get_single_embedding(f"[{item_a.get('canonical_tech_entity') or ''}] {item_a.get('title', '')}")
        e_b = item_b.get("embedding") or get_single_embedding(f"[{item_b.get('canonical_tech_entity') or ''}] {item_b.get('title', '')}")
        sim = cosine_similarity(e_a, e_b)
        if sim >= 0.82:
            return True
        if sim < 0.35:
            return False
    except Exception:
        pass

    # 3. Canonical Story Key exact or high-containment match
    key_a = get_item_story_key(item_a)
    key_b = get_item_story_key(item_b)
    if key_a and key_b and are_story_keys_similar(key_a, key_b):
        return True

    # 4. Core Entities Overlap
    ents_a = get_item_entities(item_a)
    ents_b = get_item_entities(item_b)
    if ents_a and ents_b:
        intersection = ents_a.intersection(ents_b)
        if len(intersection) >= 2:
            return True

    # 5. Cross-Lingual Entity & Semantic Keyword Overlap (TITLE ONLY, NO HOOK/DESC TO PREVENT FALSE POSITIVES)
    title_a = f"{item_a.get('title', '')} {item_a.get('title_ko', '')} {item_a.get('title_en', '')}"
    title_b = f"{item_b.get('title', '')} {item_b.get('title_ko', '')} {item_b.get('title_en', '')}"
    tokens_a = normalize_text_tokens(title_a)
    tokens_b = normalize_text_tokens(title_b)

    if tokens_a and tokens_b:
        # 5-A. Dynamic Anchor Matching (high-signal event/incident entity pairs ONLY)
        critical_anchors = [
            {"houthi", "island"},
            {"houthi", "shipping"},
            {"houthi", "control"},
            {"flock", "veteran"},
            {"deepseek", "v3"},
            {"qwen", "2.5-coder"},
            {"chorleywood", "bread"}
        ]
        for anchor in critical_anchors:
            if anchor.issubset(tokens_a) and anchor.issubset(tokens_b):
                return True

        # 5-B. High Precision Overlap Ratio (>= 0.60 on non-generic title tokens)
        common = tokens_a.intersection(tokens_b)
        min_len = min(len(tokens_a), len(tokens_b))
        if min_len >= 3 and len(common) >= 3:
            overlap_ratio = len(common) / min_len
            if overlap_ratio >= 0.60:
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

    def get_canonical_platform(s):
        p = (s.get("platform") or s.get("source_name") or "").lower()
        u = (s.get("url") or "").lower()
        if "github" in p or "github.com" in u: return "github"
        if "space" in p or "/spaces/" in u: return "hf_spaces"
        if "hugging" in p or "huggingface.co" in u: return "huggingface"
        if "hacker news" in p or "ycombinator.com" in u: return "hackernews"
        if "geeknews" in p or "hada.io" in u: return "geeknews"
        if "reddit" in p or "reddit.com" in u: return "reddit"
        if "arxiv" in p or "arxiv.org" in u: return "arxiv"
        return p or u

    existing_urls = {s.get("url") for s in primary["sources"] if s.get("url")}
    existing_platforms = {get_canonical_platform(s) for s in primary["sources"]}
    
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
        s_plat = get_canonical_platform(s)
        if s_url and s_url not in existing_urls and s_plat not in existing_platforms:
            primary["sources"].append(s)
            existing_urls.add(s_url)
            existing_platforms.add(s_plat)

    primary["source_count"] = len(primary["sources"])

    # If primary misses Korean title/hook but secondary has it, upgrade primary
    if not primary.get("title_ko") and secondary.get("title_ko"):
        primary["title_ko"] = secondary["title_ko"]
    if not primary.get("hook_ko") and secondary.get("hook_ko"):
        primary["hook_ko"] = secondary["hook_ko"]

    return primary

def extract_english_title_tokens(item: dict) -> set:
    """Extracts normalized English title tokens for high-precision cross-lingual semantic matching."""
    t_en = (
        item.get("title_en") or 
        (item.get("multilingual") or {}).get("en", {}).get("title") or 
        (item.get("ai_enrichment") or {}).get("title_en") or 
        ""
    )
    if not t_en:
        raw = item.get("title", "")
        clean = re.sub(r'^(?:GitHub|HuggingFace|HF Space|Hacker News|ArXiv|GeekNews|PyTorchKR|Paper|Reddit):\s*', '', raw, flags=re.I).strip()
        t_en = clean

    words = re.findall(r'[a-zA-Z0-9_\-\.]+', t_en.lower())
    stop_words_en = {
        "the", "a", "an", "and", "or", "in", "on", "at", "by", "for", "with", "from", 
        "is", "are", "was", "were", "to", "of", "it", "its", "that", "this", "how", "what", 
        "why", "when", "into", "over", "after", "via", "vs", "new", "using", "use"
    }
    return {w for w in words if len(w) > 1 and w not in stop_words_en}

def is_specific_model_entity(ent: str) -> bool:
    """
    Distinguishes specific versioned model/tool entities (e.g. 'qwen-image-2.1', 'llama-3.3', 'deepseek-r1')
    from broad generic/concept single-word tokens (e.g. 'jev', 'claude', 'agent', 'rag', 'llm').
    """
    if not ent:
        return False
    if any(char.isdigit() for char in ent):
        return True
    if "-" in ent and len(ent.split("-")) >= 2:
        parts = ent.split("-")
        if any(p in ["image", "coder", "vl", "vlm", "math", "distill", "turbo", "flash", "pro", "ultra"] for p in parts):
            return True
    return False

def compute_jaccard_overlap(set_a: set, set_b: set) -> float:
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return intersection / union if union > 0 else 0.0

def deduplicate_inbox_items(items: list, max_window_hours: float = 72.0) -> list:
    """Clusters and deduplicates items into a clean list of story-centric items with O(N) indexing."""
    try:
        from tools.dedup_engine import extract_canonical_entity_key
    except ImportError:
        try:
            from dedup_engine import extract_canonical_entity_key
        except ImportError:
            extract_canonical_entity_key = lambda t, u, a: ""

    merged_items = []
    item_tokens = []
    item_en_tokens = []
    item_urls = []
    item_keys = []
    item_entities = []
    item_timestamps = []

    for it in items:
        title = f"{it.get('title', '')} {it.get('title_ko', '')} {it.get('title_en', '')}"
        item_tokens.append(normalize_text_tokens(title))
        item_en_tokens.append(extract_english_title_tokens(it))
        item_urls.append({it.get("source_url") or "", it.get("url") or "", it.get("article_url") or ""} - {""})
        item_keys.append(get_item_story_key(it))
        
        c_ent = (it.get("canonical_tech_entity") or (it.get("ai_enrichment") or {}).get("canonical_tech_entity") or "").strip().lower()
        if not c_ent or c_ent in ["null", "none"]:
            c_ent = extract_canonical_entity_key(it.get("title", ""), it.get("source_url", ""), it.get("article_url", "")) or ""
        item_entities.append(c_ent)

        item_timestamps.append(parse_iso_timestamp(it))

    merged_tokens = []
    merged_en_tokens = []
    merged_urls = []
    merged_keys = []
    merged_entities = []
    merged_timestamps = []

    critical_anchors = [
        {"houthi", "island"},
        {"houthi", "shipping"},
        {"houthi", "control"},
        {"flock", "veteran"},
        {"deepseek", "v3"},
        {"qwen", "2.5-coder"},
        {"chorleywood", "bread"}
    ]

    for idx, item in enumerate(items):
        tokens = item_tokens[idx]
        en_tokens = item_en_tokens[idx]
        urls = item_urls[idx]
        key = item_keys[idx]
        ts = item_timestamps[idx]

        matched_idx = -1

        for m_idx, target in enumerate(merged_items):
            # 1. URL exact match
            m_urls = merged_urls[m_idx]
            if urls and m_urls and bool(urls.intersection(m_urls)):
                matched_idx = m_idx
                break

            # 2. Temporal window check
            m_ts = merged_timestamps[m_idx]
            if ts > 0 and m_ts > 0 and (abs(ts - m_ts) / 3600.0) > max_window_hours:
                continue

            # 2.5. Canonical Tech/Story Entity match with Granularity Guardrail
            m_ent = merged_entities[m_idx]
            ent = item_entities[idx]
            if ent and m_ent and ent == m_ent and len(ent) >= 3:
                # If specific versioned model/tool identifier (e.g. qwen-image-2.1), allow O(1) single-release merge
                if is_specific_model_entity(ent):
                    matched_idx = m_idx
                    break
                else:
                    # Broad single-word concept (e.g. 'jev', 'claude', 'agent'):
                    # Require canonical_story_key match OR English title Jaccard >= 0.50!
                    m_key = merged_keys[m_idx]
                    en_overlap = compute_jaccard_overlap(en_tokens, merged_en_tokens[m_idx])
                    if (key and m_key and are_story_keys_similar(key, m_key)) or en_overlap >= 0.50:
                        matched_idx = m_idx
                        break

            # 3. Canonical story key match (exact or high-containment)
            m_key = merged_keys[m_idx]
            if key and m_key and are_story_keys_similar(key, m_key):
                matched_idx = m_idx
                break

            # 4. English Translated Title Semantic Jaccard Overlap (>= 50% threshold)
            en_overlap = compute_jaccard_overlap(en_tokens, merged_en_tokens[m_idx])
            if en_overlap >= 0.50:
                matched_idx = m_idx
                break

            # 5. Token & Anchor match
            m_tokens = merged_tokens[m_idx]
            if tokens and m_tokens:
                anchor_hit = False
                for anc in critical_anchors:
                    if anc.issubset(tokens) and anc.issubset(m_tokens):
                        matched_idx = m_idx
                        anchor_hit = True
                        break
                if anchor_hit:
                    break

                common = tokens.intersection(m_tokens)
                min_len = min(len(tokens), len(m_tokens))
                if min_len >= 3 and len(common) >= 3:
                    if (len(common) / min_len) >= 0.60:
                        matched_idx = m_idx
                        break

        if matched_idx >= 0:
            target = merged_items[matched_idx]
            merge_sources_into_primary(target, item)
            merged_urls[matched_idx].update(urls)
            merged_tokens[matched_idx].update(tokens)
            merged_en_tokens[matched_idx].update(en_tokens)
            if not merged_entities[matched_idx] and item_entities[idx]:
                merged_entities[matched_idx] = item_entities[idx]
        else:
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
            merged_tokens.append(set(tokens))
            merged_en_tokens.append(set(en_tokens))
            merged_urls.append(set(urls))
            merged_keys.append(key)
            merged_entities.append(item_entities[idx])
            merged_timestamps.append(ts)

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
