#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/drain_ai_enrichment.py
==============================================================================
Autonomous AI Multi-Language Inbox Enrichment & Drain Worker (AGENTS.md Compliant)
------------------------------------------------------------------------------
Purpose:
  Batch-processes unclassified items from Aiven PostgreSQL (SSOT)
  during regular GitHub Actions schedules or manual CLI runs.
  Enriches items with Trilingual Parity (KO / EN / ZH), The Hook,
  4-Tier Category Classification, and Universal Story/Tech Canonical Keys.

Architecture & Safety Guarantees (per AGENTS.md):
  1. Centralized DB-First (Aiven PostgreSQL SSOT).
  2. Zero Client-side dependency: fully executed in CI/CD batch environment.
  3. Bounded Runtime: Default --max-items 15, --max-time 110s (protects Actions quota).
  4. Hard Circuit Breaker: Halts immediately on 3 consecutive failures.
  5. HTTP 429 Immediate Abort: stops cascade immediately if rate limited.
  6. Model Cascade Cap: Max 2 models attempted per item (Primary + 1 Fallback).
  7. Atomic DB Persistence & Telemetry logging to vercel_worker_logs.
==============================================================================
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
import requests

# Force UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
tools_dir = os.path.join(ROOT_DIR, "tools")
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

from db_config import get_db_connection, get_db_info
from openrouter_free_router import get_openrouter_api_key

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Primary & Fallback Free Models (Verified fast & high quality CJK multilingual)
PRIMARY_MODEL = "inclusionai/ling-3.0-flash-sante:free"
FALLBACK_MODEL = "inclusionai/ling-3.0-flash-vl:free"

KOREAN_REGEX = re.compile(r'[\uac00-\ud7a3]')
CHINESE_REGEX = re.compile(r'[\u4e00-\u9fff]')

VALID_TIER1_CATEGORIES = [
    'TECH_COMPUTING', 'SCIENCE_RESEARCH', 'ECONOMY_FINANCE',
    'POLITICS_POLICY', 'LAW_CRIME_JUSTICE', 'CULTURE_HUMANITIES'
]

VALID_PRIMARY_CATEGORIES = [
    'INFERENCE_OPT', 'AGENTS_DEVTOOLS', 'MULTIMODAL_AI', 'FOUNDATION_MODELS',
    'INFRA_RAG_SECURITY', 'DEEP_SCIENCE_SPACE', 'MACRO_GLOBAL_BIZ',
    'CIVIC_CRIME_INCIDENT', 'HISTORY_LIFE_CULTURE', 'INDUSTRY_TRENDS'
]

SYSTEM_PROMPT = """당신은 글로벌 최고 수준의 다국어 AI 기술 분석가 및 뉴스 번역 전문가입니다.
주어진 기술/뉴스 후보를 분석하여, 한국어(KO), 영어(EN), 중국어(ZH) 3개 국어 번역 제목, 1줄 훅(Hook), 'AI 3줄 핵심 요약'(언어별 3개씩: key_takeaways_ko, key_takeaways_en, key_takeaways_zh), 다국어 중복 방지를 위한 영문 표준 사건 식별키(canonical_story_key), 정규화된 기술 고유명칭(canonical_tech_entity), 핵심 영문 엔티티 목록(core_entities), 그리고 정확한 카테고리 분류를 반드시 아래 JSON 배열 형식으로만 응답하세요. 생각 과정이나 마크다운 등 기타 텍스트는 일절 출력하지 마세요.
중요 번역 및 정규화 규칙:
1. title_zh, hook_zh, key_takeaways_zh에는 반드시 실제 한자(간체자) 중국어 번역을 출력해야 합니다. 영어나 한국어를 그대로 복사하지 마세요.
2. title_ko, hook_ko, key_takeaways_ko에는 반드시 실제 한글(Hangul)로 작성된 자연스러운 고품질 한국어 요약을 출력하세요. 중국어 한자를 한국어 요약에 섞지 마세요.
3. title_en, hook_en, key_takeaways_en에는 정제된 전문 영문 제목, 훅, 요약을 출력하세요.
4. 법률, 재판, 판결, 범죄, 사회적 사건사고 기사는 절대로 TECH(기술)로 분류하지 말고 item_type: "NEWS", tier1_category: "LAW_CRIME_JUSTICE"로 정확히 분류해야 합니다.
5. canonical_tech_entity 정규화: 기술, 모델, 프레임워크 관련 기사는 반드시 소문자 하이픈 형식의 공식 표준 명칭 1개(예: 'qwen-image-2.1', 'jev', 'deepseek-r1', 'vllm', 'flash-attn-3')를 정확히 추출하세요. 일반 사회/정치/뉴스 기사라면 null을 반환하세요.
6. canonical_story_key 정규화: 모든 뉴스/기사에 대해 핵심 사건을 식별하는 고유 영어 소문자 하이픈 슬러그 3~5단어(예: 'vllm-serving-engine', 'google-antitrust-ruling', 'openai-for-profit-transition')를 반드시 정확하게 작성하세요.
[
  {
    "id": "item_id",
    "title_ko": "자연스러운 한국어 번역 제목",
    "hook_ko": "결정적 1줄 한국어 훅",
    "key_takeaways_ko": [
      "한국어로 작성된 첫 번째 핵심 요약 포인트",
      "한국어로 작성된 두 번째 핵심 요약 포인트",
      "한국어로 작성된 세 번째 핵심 요약 포인트"
    ],
    "title_en": "Refined Professional English Title",
    "hook_en": "Decisive 1-line English hook",
    "key_takeaways_en": [
      "First key takeaway in English",
      "Second key takeaway in English",
      "Third key takeaway in English"
    ],
    "title_zh": "精准吸引人的中文标题",
    "hook_zh": "直击核心亮点的中文一句话提炼",
    "key_takeaways_zh": [
      "中文第一条核心要点",
      "中文第二条核心要点",
      "中文第三条核心要点"
    ],
    "canonical_tech_entity": "소문자 하이픈 기술명칭 1개 또는 null",
    "canonical_story_key": "영문 소문자 하이픈 슬러그 (3~5단어)",
    "core_entities": ["핵심 영문 고유명칭 2~4개"],
    "tier1_category": "TECH_COMPUTING, SCIENCE_RESEARCH, ECONOMY_FINANCE, POLITICS_POLICY, LAW_CRIME_JUSTICE, CULTURE_HUMANITIES 중 택1",
    "item_type": "MODEL, AGENT, TECH, NEWS 중 택1",
    "category_primary": "INFERENCE_OPT, AGENTS_DEVTOOLS, MULTIMODAL_AI, FOUNDATION_MODELS, INFRA_RAG_SECURITY, DEEP_SCIENCE_SPACE, MACRO_GLOBAL_BIZ, CIVIC_CRIME_INCIDENT, HISTORY_LIFE_CULTURE, INDUSTRY_TRENDS 중 택1",
    "programming_lang": "Python, TypeScript, Rust, General 중 택1"
  }
]"""

def sanitize_json(text: str):
    """Robustly strips reasoning tags, markdown fences, and parses JSON array/object."""
    if not text:
        return None
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*```$', '', cleaned).strip()

    try:
        data = json.loads(cleaned)
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            return data
        if isinstance(data, dict):
            return [data]
    except Exception:
        pass

    arr_match = re.search(r'\[\s*\{[\s\S]*\}\s*\]', cleaned)
    if arr_match:
        try:
            data = json.loads(arr_match.group(0))
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                return data
        except Exception:
            pass

    obj_match = re.search(r'\{[\s\S]*\}', cleaned)
    if obj_match:
        try:
            data = json.loads(obj_match.group(0))
            if isinstance(data, dict):
                return [data]
        except Exception:
            pass

    return None

def infer_category(item: dict, parsed: dict):
    t1 = parsed.get("tier1_category")
    if t1 not in VALID_TIER1_CATEGORIES:
        t1 = "TECH_COMPUTING"

    p_cat = parsed.get("category_primary")
    if p_cat not in VALID_PRIMARY_CATEGORIES:
        p_cat = "INDUSTRY_TRENDS"

    i_type = parsed.get("item_type")
    if i_type not in ["MODEL", "AGENT", "TECH", "NEWS"]:
        i_type = "NEWS"

    art = parsed.get("artifact_type") or ("WEIGHTS" if i_type == "MODEL" else "ARTICLE")
    return t1, p_cat, i_type, art

def call_llm_single(api_key: str, item: dict, model: str, timeout_sec: int = 22):
    payload = [{
        "id": item["inbox_id"],
        "platform": item.get("source_platform") or "Unknown",
        "title": (item.get("title") or "")[:150],
        "description": re.sub(r'<[^>]+>', ' ', item.get("description") or "").strip()[:300]
    }]

    # Include community feedback if available in payload
    top_comments = item.get("top_comments")
    if top_comments:
        payload[0]["community_feedback"] = top_comments

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/AnnyeongHae/ai-factcheck-portfolio",
        "X-Title": "AI FactCheck Batch Drain Worker"
    }

    req_body = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"분석할 항목 목록:\n{json.dumps(payload, ensure_ascii=False)}"}
        ],
        "temperature": 0.1,
        "max_tokens": 4200
    }

    t0 = time.time()
    resp = requests.post(OPENROUTER_URL, headers=headers, json=req_body, timeout=(5.0, timeout_sec))
    dur = time.time() - t0

    if resp.status_code == 429:
        return None, dur, 429, "Rate Limited (HTTP 429)"

    if resp.status_code != 200:
        return None, dur, resp.status_code, resp.text[:120]

    data = resp.json()
    msg = data.get("choices", [{}])[0].get("message", {})
    raw_content = msg.get("content") or msg.get("reasoning") or ""
    parsed = sanitize_json(raw_content)

    if not parsed or not isinstance(parsed, list) or len(parsed) == 0:
        return None, dur, 200, "Invalid JSON structure"

    p0 = parsed[0]
    if not isinstance(p0, dict):
        return None, dur, 200, "Item in JSON array is not an object"

    title_ko = p0.get("title_ko") or ""
    title_zh = p0.get("title_zh") or ""

    if not KOREAN_REGEX.search(title_ko):
        return None, dur, 200, "Missing Hangul in title_ko"
    if not CHINESE_REGEX.search(title_zh):
        return None, dur, 200, "Missing Hanzi in title_zh"

    actual_model = data.get("model") or model
    return p0, dur, 200, actual_model

def drain_enrichment(max_items: int = 15, max_time_sec: int = 110, delay_sec: float = 1.5, dry_run: bool = False):
    start_time = time.time()
    api_key = get_openrouter_api_key()
    if not api_key:
        print("[!] Error: OPENROUTER_API_KEY is missing from environment and .env.")
        return 0

    db_info = get_db_info()
    print("==================================================================")
    print("🚀 [AI Drain Worker] Starting High-Precision Multilingual AI Enrichment")
    print(f"[*] Target DB     : {db_info.get('provider')} ({db_info.get('host')})")
    print(f"[*] Primary Model : {PRIMARY_MODEL}")
    print(f"[*] Fallback Model: {FALLBACK_MODEL}")
    print(f"[*] Safety Budget : Max {max_items} items | Max {max_time_sec}s timeout | {delay_sec}s pacing")
    print("==================================================================")

    conn = get_db_connection()
    if not conn:
        print("[!] Error: Unable to connect to PostgreSQL database.")
        return 0

    try:
        cur = conn.cursor()
        # Grab top priority unclassified items (high viral score, recent date first)
        cur.execute("""
            SELECT id, inbox_id, source_platform, source_url, title, description, item_type, viral_score, harvested_date, raw_payload
            FROM raw_trends_inbox
            WHERE is_classified = FALSE
            ORDER BY viral_score DESC NULLS LAST, harvested_date DESC, id DESC
            LIMIT %s;
        """, (max_items,))
        rows = cur.fetchall()

        cur.execute("SELECT COUNT(*) FROM raw_trends_inbox WHERE is_classified = FALSE;")
        unclassified_count = cur.fetchone()[0]

        print(f"[*] Found {len(rows)} candidates to enrich (Total unclassified in DB: {unclassified_count})")
        if not rows:
            print("[+] All items in database are already 100% enriched!")
            return 0

        processed_count = 0
        consecutive_failures = 0
        total_llm_time = 0.0

        for idx, row in enumerate(rows, 1):
            elapsed = time.time() - start_time
            if elapsed >= max_time_sec:
                print(f"[!] Time budget reached ({elapsed:.1f}s >= {max_time_sec}s). Gracefully stopping.")
                break

            r_id, r_inbox_id, r_plat, r_url, r_title, r_desc, r_type, r_score, r_hdate, r_raw = row
            raw_payload = r_raw if isinstance(r_raw, dict) else {}
            if isinstance(r_raw, str):
                try:
                    loaded = json.loads(r_raw)
                    if isinstance(loaded, dict):
                        raw_payload = loaded
                except Exception:
                    raw_payload = {}

            # Extract top comments for community context if available
            top_comments = ""
            raw_comments = raw_payload.get("raw_comments") if isinstance(raw_payload, dict) else []
            if isinstance(raw_comments, list) and len(raw_comments) > 0:
                dict_comments = [c for c in raw_comments if isinstance(c, dict)]
                if dict_comments:
                    sorted_c = sorted(dict_comments, key=lambda x: x.get("points") or 0, reverse=True)
                    top_comments = " / ".join([f"[@{c.get('author', 'User')}]: {(c.get('text') or '').replace(chr(10), ' ')[:120]}" for c in sorted_c[:3]])
                else:
                    str_comments = [str(c).replace(chr(10), ' ')[:120] for c in raw_comments if c]
                    top_comments = " / ".join(str_comments[:3])

            item_data = {
                "inbox_id": r_inbox_id,
                "source_platform": r_plat,
                "title": r_title,
                "description": r_desc,
                "top_comments": top_comments
            }

            # Cascade: Try Primary -> If failed, try Fallback (Max 2 attempts per AGENTS.md)
            parsed_res = None
            used_model = None
            call_dur = 0.0

            for model_cand in [PRIMARY_MODEL, FALLBACK_MODEL]:
                p_res, dur, status_code, err_or_model = call_llm_single(api_key, item_data, model_cand, timeout_sec=18)
                call_dur += dur
                if status_code == 429:
                    print(f"[!] [Rate Limit] HTTP 429 received from OpenRouter on '{model_cand}'. Halting cascade immediately.")
                    consecutive_failures = 99
                    break

                if p_res:
                    parsed_res = p_res
                    used_model = err_or_model
                    break
                else:
                    print(f"    ⚠️ Model '{model_cand}' failed ({dur:.1f}s): {err_or_model}")

            if consecutive_failures >= 99:
                # HTTP 429 - abort immediately
                break

            if not parsed_res:
                consecutive_failures += 1
                print(f"[{idx:>2}/{len(rows)}] ❌ Failed to enrich '{r_inbox_id}' ({call_dur:.1f}s). Failure count: {consecutive_failures}/3")
                # Rotate item's updated_at so it doesn't block the top of the queue next time
                cur.execute("UPDATE raw_trends_inbox SET updated_at = CURRENT_TIMESTAMP WHERE id = %s;", (r_id,))
                conn.commit()

                if consecutive_failures >= 3:
                    print("[!] [Circuit Breaker Tripped] 3 consecutive LLM failures. Halting worker to protect quota.")
                    break
                time.sleep(delay_sec)
                continue

            # Success: reset circuit breaker
            consecutive_failures = 0
            total_llm_time += call_dur

            t1_cat, prim_cat, item_type, art_type = infer_category(item_data, parsed_res)

            title_ko = (parsed_res.get("title_ko") or r_title).strip()
            title_en = (parsed_res.get("title_en") or r_title).strip()
            title_zh = (parsed_res.get("title_zh") or r_title).strip()

            hook_ko = (parsed_res.get("hook_ko") or title_ko).strip()
            hook_en = (parsed_res.get("hook_en") or title_en).strip()
            hook_zh = (parsed_res.get("hook_zh") or title_zh).strip()

            takeaways_ko = parsed_res.get("key_takeaways_ko") or [hook_ko]
            takeaways_en = parsed_res.get("key_takeaways_en") or [hook_en]
            takeaways_zh = parsed_res.get("key_takeaways_zh") or [hook_zh]

            raw_canonical_key = (parsed_res.get("canonical_story_key") or "").lower().strip()
            canonical_story_key = re.sub(r'[^a-z0-9-]+', '-', raw_canonical_key).strip('-')[:100]

            canonical_tech = (parsed_res.get("canonical_tech_entity") or "").lower().strip()
            canonical_tech_entity = re.sub(r'[^a-z0-9-]+', '-', canonical_tech).strip('-')[:50]
            if canonical_tech_entity in ('none', 'null', ''):
                canonical_tech_entity = None

            from datetime import timezone
            now_iso = datetime.now(timezone.utc).isoformat()

            # Structure full raw_payload
            raw_payload.update({
                "title_ko": title_ko,
                "title_en": title_en,
                "title_zh": title_zh,
                "hook": hook_ko,
                "hook_ko": hook_ko,
                "hook_en": hook_en,
                "hook_zh": hook_zh,
                "description_ko": hook_ko,
                "description_en": hook_en,
                "description_zh": hook_zh,
                "key_takeaways": takeaways_ko,
                "key_takeaways_ko": takeaways_ko,
                "key_takeaways_en": takeaways_en,
                "key_takeaways_zh": takeaways_zh,
                "category_type": item_type,
                "item_type": item_type,
                "category_primary": prim_cat,
                "tier1_category": t1_cat,
                "tier2_category": prim_cat,
                "artifact_type": art_type,
                "programming_lang": parsed_res.get("programming_lang") or raw_payload.get("programming_lang") or "General",
                "canonical_story_key": canonical_story_key or raw_payload.get("canonical_story_key"),
                "canonical_tech_entity": canonical_tech_entity or raw_payload.get("canonical_tech_entity"),
                "multilingual": {
                    "ko": {"title": title_ko, "hook": hook_ko, "key_takeaways": takeaways_ko},
                    "en": {"title": title_en, "hook": hook_en, "key_takeaways": takeaways_en},
                    "zh": {"title": title_zh, "hook": hook_zh, "key_takeaways": takeaways_zh}
                },
                "ai_enrichment": {
                    "id": r_inbox_id,
                    "source_lang": "EN",
                    "type_classification": item_type,
                    "category_primary": prim_cat,
                    "tier1_category": t1_cat,
                    "tier2_category": prim_cat,
                    "artifact_type": art_type,
                    "canonical_story_key": canonical_story_key or None,
                    "canonical_tech_entity": canonical_tech_entity or None,
                    "korean_title": title_ko,
                    "hook": hook_ko,
                    "key_takeaways": takeaways_ko,
                    "takeaways_ko": takeaways_ko,
                    "takeaways_en": takeaways_en,
                    "takeaways_zh": takeaways_zh,
                    "multilingual": {
                        "ko": {"title": title_ko, "hook": hook_ko, "key_takeaways": takeaways_ko},
                        "en": {"title": title_en, "hook": hook_en, "key_takeaways": takeaways_en},
                        "zh": {"title": title_zh, "hook": hook_zh, "key_takeaways": takeaways_zh}
                    },
                    "enriched_by_model": used_model,
                    "enriched_at": now_iso
                }
            })

            if not dry_run:
                cur.execute("""
                    UPDATE raw_trends_inbox
                    SET is_classified = TRUE,
                        category_primary = %s,
                        item_type = %s,
                        raw_payload = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s;
                """, (prim_cat, item_type, json.dumps(raw_payload, ensure_ascii=False), r_id))
                conn.commit()

            processed_count += 1
            print(f"[{idx:>2}/{len(rows)}] ✅ Enriched '{r_inbox_id}' ({call_dur:.1f}s via {used_model})")
            print(f"        KO: {title_ko[:60]}")
            print(f"        Hook: {hook_ko[:70]}")

            time.sleep(delay_sec)

        # Log worker run to vercel_worker_logs
        if processed_count > 0 and not dry_run:
            try:
                cur.execute("SELECT COUNT(*) FROM raw_trends_inbox WHERE is_classified = FALSE;")
                remaining_after = cur.fetchone()[0]
                cur.execute("""
                    INSERT INTO vercel_worker_logs (worker_name, model_used, processed_count, duration_seconds, remaining_count, status)
                    VALUES ('GitHub Actions Batch AI Drain', %s, %s, %s, %s, 'SUCCESS');
                """, (PRIMARY_MODEL, processed_count, round(total_llm_time, 2), remaining_after))
                conn.commit()
                print(f"[+] [Telemetry] Recorded worker run: {processed_count} items enriched (Remaining: {remaining_after})")
            except Exception as e:
                print(f"[!] Warning: Failed to record worker log: {e}")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"[!] Drain worker exception: {e}")
        try:
            conn.rollback()
            conn.close()
        except Exception:
            pass

    total_time = time.time() - start_time
    print("==================================================================")
    print(f"🎯 [Drain Complete] Successfully enriched {processed_count} items in {total_time:.1f}s")
    print("==================================================================")
    return processed_count

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Autonomous AI Multi-Language Inbox Enrichment & Drain Worker")
    parser.add_argument("--max-items", type=int, default=15, help="Max items to process in this run")
    parser.add_argument("--max-time", type=int, default=110, help="Max execution time in seconds")
    parser.add_argument("--delay", type=float, default=1.5, help="Pacing interval between requests in seconds")
    parser.add_argument("--dry-run", action="store_true", help="Run without writing to database")
    args = parser.parse_args()

    drain_enrichment(
        max_items=args.max_items,
        max_time_sec=args.max_time,
        delay_sec=args.delay,
        dry_run=args.dry_run
    )
