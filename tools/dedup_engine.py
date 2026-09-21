# =============================================================================
# 3-Tier Deduplication & Semantic Matching Engine (v1.0.0)
# 관리 위치: tools/dedup_engine.py
# =============================================================================
import os
import re
import json
import urllib.parse
from datetime import datetime

try:
    import yaml
except ImportError:
    yaml = None

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None


def normalize_url(url: str) -> str:
    """Tier 1: Canonical URL Normalization"""
    if not url:
        return ""
    try:
        parsed = urllib.parse.urlparse(url.strip())
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        
        # Remove tracking query params
        query_params = urllib.parse.parse_qsl(parsed.query)
        filtered_params = [
            (k, v) for k, v in query_params 
            if not k.lower().startswith("utm_") 
            and not k.lower().startswith("ref")
            and k.lower() not in ["fbclid", "gclid", "source", "s"]
        ]
        new_query = urllib.parse.urlencode(sorted(filtered_params))
        path = parsed.path.rstrip("/")
        
        return urllib.parse.urlunparse((
            "https",
            netloc,
            path,
            "",
            new_query,
            ""
        ))
    except Exception:
        return url.strip().rstrip("/")


def clean_title(title: str) -> str:
    """Tier 2: Title Normalization & Tokenization"""
    if not title:
        return ""
    # Strip common platform prefixes
    t = re.sub(r"^(Show HN:|Ask HN:|GeekNews:|Hugging Face Blog:|GitHub - |\[GitHub\]|Release v?[0-9\.]+:?)\s*", "", title, flags=re.IGNORECASE)
    # Remove emojis and punctuation
    t = re.sub(r"[^a-zA-Z0-9가-힣\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip().lower()
    return t


def extract_canonical_entity_key(title: str, source_url: str = "", article_url: str = "") -> str:
    """
    Tier 2.5: Fast Deterministic Canonical Entity Extractor (O(1), zero-cost)
    Extracts core normalized tech entity key from titles and URLs across platforms.
    Examples:
      - "HF 스페이스에 Qwen-Image 2.1 이미지 생성 모델 공개" -> "qwen-image-2.1"
      - "Qwen-Image-2.1, 소형 고효율 통합 이미지 생성 모델 출시" -> "qwen-image-2.1"
      - "Qwen-Image-2.1: 컴팩트하고 효율적이며 통합된..." -> "qwen-image-2.1"
      - "JEV 에코시스템 해부 — 답변 검증기 13종을..." -> "jev"
    """
    all_text = f"{title or ''} {source_url or ''} {article_url or ''}".lower()

    # 1. GitHub repo slug (owner/repo)
    gh_match = re.search(r'github\.com/([\w\.-]+/[\w\.-]+)', all_text)
    if gh_match:
        repo_part = gh_match.group(1).lower().rstrip('.git')
        # return just repo name or owner/repo
        return repo_part

    # 2. Known AI Model / Project name regex patterns
    known_patterns = [
        r'\b(qwen[-_ ]?image[-_ ]?2\.?1)\b',
        r'\b(jev)\b',
        r'\b(deepseek[-_ ]?[rv]\d+[\w\.-]*)\b',
        r'\b(llama[-_ ]?\d+[\w\.-]*)\b',
        r'\b(glm[-_ ]?\d+[\w\.-]*)\b',
        r'\b(flux[-_ ]?\d+[\w\.-]*)\b',
        r'\b(flash[-_ ]?attn[-_ ]?\d*)\b',
        r'\b(bespoke[-_ ]?nimble[-_ ]?\d+b?)\b',
        r'\b(confucius\d+[-_ ]?r\d+t\d+)\b',
        r'\b([a-z0-9]+-[a-z0-9]+(?:-\d+[\w\.-]*)?)\b', # general hyphenated names like "vllm-project"
    ]
    for p in known_patterns:
        m = re.search(p, all_text)
        if m:
            clean_key = re.sub(r'[-_ ]+', '-', m.group(1)).strip('-')
            if len(clean_key) >= 3:
                return clean_key

    # 3. Clean platform prefixes from title & take leading alphanumeric token
    t = title or ""
    clean = re.sub(r'^(?:github:\s*|huggingface:\s*|hf space:\s*|hacker news:\s*|arxiv:\s*|geeknews:\s*|pytorchkr:\s*|show hn:\s*)', '', t, flags=re.I).strip()
    words = re.findall(r'[a-zA-Z0-9가-힣\.-]{3,}', clean)
    if words:
        first = words[0].lower().strip(".-")
        if len(first) >= 3 and not first.isdigit() and first not in ["출시", "공개", "발표", "오픈소스", "모델"]:
            return first
    return clean_title(title)[:25].strip().replace(" ", "-")


def title_jaccard_similarity(title1: str, title2: str) -> float:
    t1_tokens = set(clean_title(title1).split())
    t2_tokens = set(clean_title(title2).split())
    if not t1_tokens or not t2_tokens:
        return 0.0
    intersection = t1_tokens.intersection(t2_tokens)
    union = t1_tokens.union(t2_tokens)
    return len(intersection) / len(union)


def check_ai_semantic_dedup(api_key: str, candidate_title: str, existing_title: str) -> dict:
    """Tier 3: AI-based Semantic Deduplication (Gemini API suspended per zero-cost policy)."""
    return {"is_duplicate": False, "reason": "gemini_suspended"}


def evaluate_deduplication(candidate: dict, existing_cases: list, existing_inbox: list, api_key: str = None) -> dict:
    """
    Full 3-Tier Deduplication Pipeline:
    1. Canonical URL Match
    2. Normalized Title Jaccard Match (>= 0.7)
    3. AI Semantic Deduplication (for ambiguous 0.35 ~ 0.70 range)
    """
    cand_url = normalize_url(candidate.get("source_url") or candidate.get("url") or "")
    cand_title = candidate.get("title", "")
    cand_title_ko = candidate.get("title_ko", "")

    # 1. Tier 1: URL Check against investigations
    for c in existing_cases:
        c_url = normalize_url(c.get("raw_viral_post", {}).get("post_url") or (c.get("sources", [{}])[0].get("url") if c.get("sources") else ""))
        if cand_url and c_url and cand_url == c_url:
            return {
                "is_duplicate": True,
                "tier": 1,
                "method": "CANONICAL_URL_MATCH",
                "matched_type": "INVESTIGATION",
                "matched_id": c.get("case_id"),
                "matched_title": c.get("title"),
                "reason": f"Canonical URL precisely matches existing investigation ({cand_url})"
            }

    # 2. Tier 1: URL Check against inbox
    for ib in existing_inbox:
        ib_url = normalize_url(ib.get("source_url") or "")
        if cand_url and ib_url and cand_url == ib_url:
            return {
                "is_duplicate": True,
                "tier": 1,
                "method": "CANONICAL_URL_MATCH",
                "matched_type": "INBOX",
                "matched_id": ib.get("inbox_id"),
                "matched_title": ib.get("title"),
                "reason": f"Canonical URL precisely matches existing inbox item ({cand_url})"
            }

    # 3. Tier 2: Title Jaccard against investigations & inbox
    for c in existing_cases:
        sim = max(
            title_jaccard_similarity(cand_title, c.get("title", "")),
            title_jaccard_similarity(cand_title_ko, c.get("title", "")) if cand_title_ko else 0.0
        )
        if sim >= 0.70:
            return {
                "is_duplicate": True,
                "tier": 2,
                "method": "TITLE_TOKEN_JACCARD",
                "similarity": sim,
                "matched_type": "INVESTIGATION",
                "matched_id": c.get("case_id"),
                "matched_title": c.get("title"),
                "reason": f"Title token overlap ({sim:.2f}) indicates duplicate topic with {c.get('case_id')}"
            }

    # 4. Tier 3: AI Semantic Check (Check candidates with high keyword overlap or same tech keyword)
    if api_key:
        for c in existing_cases:
            sim = max(
                title_jaccard_similarity(cand_title, c.get("title", "")),
                title_jaccard_similarity(cand_title_ko, c.get("title", "")) if cand_title_ko else 0.0
            )
            # Check if key tech word overlaps (e.g. "Gradio" in both)
            cand_words = set(clean_title(cand_title).split() + clean_title(cand_title_ko).split())
            case_words = set(clean_title(c.get("title", "")).split())
            common = cand_words.intersection(case_words)
            has_major_tech_overlap = any(len(w) >= 5 for w in common)

            if sim >= 0.35 or has_major_tech_overlap:
                ai_res = check_ai_semantic_dedup(api_key, cand_title, c.get("title", ""))
                if ai_res.get("is_duplicate"):
                    return {
                        "is_duplicate": True,
                        "tier": 3,
                        "method": "AI_SEMANTIC_MATCH",
                        "similarity": ai_res.get("similarity_score", 0.9),
                        "matched_type": "INVESTIGATION",
                        "matched_id": c.get("case_id"),
                        "matched_title": c.get("title"),
                        "canonical_tech_name": ai_res.get("canonical_tech_name"),
                        "reason": ai_res.get("reason", "AI determined both items represent the same core tech release")
                    }

    return {"is_duplicate": False, "reason": "Unique novel tech candidate"}
