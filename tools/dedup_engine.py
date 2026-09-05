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


def title_jaccard_similarity(title1: str, title2: str) -> float:
    t1_tokens = set(clean_title(title1).split())
    t2_tokens = set(clean_title(title2).split())
    if not t1_tokens or not t2_tokens:
        return 0.0
    intersection = t1_tokens.intersection(t2_tokens)
    union = t1_tokens.union(t2_tokens)
    return len(intersection) / len(union)


def check_ai_semantic_dedup(api_key: str, candidate_title: str, existing_title: str) -> dict:
    """Tier 3: AI-based Semantic Deduplication using dedup_prompt.yaml"""
    if not genai or not api_key:
        return {"is_duplicate": False, "reason": "genai or api_key missing"}

    sys_instruction = "기술 중복 판정 AI 아키텍트"
    schema_text = ""
    try:
        from prompt_manager import get_prompt
        p = get_prompt("dedup")
        if p:
            sys_instruction = p.persona_and_role or sys_instruction
            schema_text = p.output_json_schema
    except Exception:
        pass

    user_prompt = f"""
후보 A (신규 수집): "{candidate_title}"
후보 B (기존 등재): "{existing_title}"

두 항목이 동일한 기술/라이브러리/모델의 동일 발표이거나 번역/해설본인지 판별하여 JSON으로 응답하세요:
{schema_text}
"""

    try:
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(
            model="gemini-flash-lite-latest",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=sys_instruction,
                temperature=0.0,
                response_mime_type="application/json"
            )
        )
        data = json.loads(resp.text)
        return data
    except Exception as e:
        return {"is_duplicate": False, "reason": str(e)}


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
