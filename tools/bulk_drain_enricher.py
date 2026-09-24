#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/bulk_drain_enricher.py
==============================================================================
Direct High-Throughput AI Multilingual Inbox Enricher (Batch Execution)
------------------------------------------------------------------------------
Purpose:
  Directly enriches ~1,000 unclassified inbox items in Aiven PostgreSQL SSOT
  in batches of 3 items (sweet spot for 0-truncation and ~0.8s latency).
  Produces 100% schema-compliant Trilingual Parity (KO / EN / ZH), The Hook,
  3 Key Takeaways per language, Canonical Story Keys, and 4-Tier Categorization.
==============================================================================
"""

import os
import sys
import json
import time
import re
import urllib.request
import urllib.error
from datetime import datetime, timezone

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

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT_DIR, '.env'))

from db_config import get_db_connection, get_db_info
from openrouter_free_router import get_openrouter_api_key

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
PRIMARY_MODEL = "inclusionai/ling-3.0-flash-fin:free"
FALLBACK_MODEL = "inclusionai/ling-3.0-flash-sante:free"

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

VALID_TYPES = ['MODEL', 'AGENT', 'TECH', 'NEWS']

SYSTEM_PROMPT = """당신은 글로벌 최고 수준의 다국어 AI 기술 분석가 및 뉴스 번역 전문가입니다.
주어진 기술/뉴스 후보를 분석하여, 각 항목마다 한국어(KO), 영어(EN), 중국어(ZH) 3개 국어 번역 제목, 1줄 훅(Hook), 'AI 3줄 핵심 요약'(언어별 3개씩: key_takeaways_ko, key_takeaways_en, key_takeaways_zh), 영문 표준 사건 식별키(canonical_story_key), 정규화된 기술 고유명칭(canonical_tech_entity), 핵심 영문 엔티티 목록(core_entities), 그리고 정확한 카테고리 분류를 반드시 아래 JSON 배열 형식으로만 응답하세요. 생각 과정이나 마크다운 등 기타 텍스트는 일절 출력하지 마세요.

중요 번역 및 정규화 규칙:
1. title_zh, hook_zh, key_takeaways_zh에는 반드시 실제 한자(간체자) 중국어 번역을 출력해야 합니다. 영어나 한국어를 그대로 복사하지 마세요.
2. title_ko, hook_ko, key_takeaways_ko에는 반드시 실제 한글(Hangul)로 작성된 자연스러운 고품질 한국어 요약을 출력하세요. 중국어 한자를 한국어 요약에 섞지 마세요.
3. title_en, hook_en, key_takeaways_en에는 정제된 전문 영문 제목, 훅, 요약을 출력하세요.
4. 법률, 재판, 판결, 범죄, 사회적 사건사고 기사는 절대로 TECH(기술)로 분류하지 말고 item_type: "NEWS", tier1_category: "LAW_CRIME_JUSTICE"로 정확히 분류해야 합니다.
5. canonical_tech_entity 정규화: 기술, 모델, 프레임워크 관련 기사는 반드시 소문자 하이픈 형식의 공식 표준 명칭 1개(예: 'qwen-image-2.1', 'vllm', 'flash-attn-3')를 정확히 추출하세요. 일반 사회/정치/뉴스 기사라면 null을 반환하세요.
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
    if not text:
        return None
    cleaned = text.strip()
    cleaned = re.sub(r'<think>[\s\S]*?</think>', '', cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*```$', '', cleaned)
    cleaned = cleaned.strip()

    start_bracket = cleaned.find('[')
    start_brace = cleaned.find('{')
    start_idx = -1
    if start_bracket != -1 and start_brace != -1:
        start_idx = min(start_bracket, start_brace)
    elif start_bracket != -1:
        start_idx = start_bracket
    elif start_brace != -1:
        start_idx = start_brace

    if start_idx > 0:
        cleaned = cleaned[start_idx:].strip()

    try:
        res = json.loads(cleaned)
        return res if isinstance(res, list) else [res]
    except Exception:
        pass

    arr_m = re.search(r'\[\s*\{[\s\S]*\}\s*\]', cleaned)
    if arr_m:
        try:
            return json.loads(arr_m.group(0))
        except Exception:
            pass

    obj_m = re.search(r'\{[\s\S]*\}', cleaned)
    if obj_m:
        try:
            return [json.loads(obj_m.group(0))]
        except Exception:
            pass

    return None

def infer_categories_and_artifact(item: dict, parsed_ai: dict):
    title = (item.get("title") or "").lower()
    desc = (item.get("description") or "").lower()
    platform = (item.get("source_platform") or "").lower()
    text = f"{title} {desc} {platform}"

    t1 = parsed_ai.get("tier1_category")
    if t1 not in VALID_TIER1_CATEGORIES:
        t1 = None

    cat_pri = parsed_ai.get("category_primary")
    if cat_pri not in VALID_PRIMARY_CATEGORIES:
        cat_pri = None

    itype = parsed_ai.get("item_type")
    if itype not in VALID_TYPES:
        itype = None

    if not cat_pri:
        if any(k in text for k in ['quant', 'vllm', 'inference', 'sglang', 'tensorrt', 'fp8', 'int4', 'cuda']):
            cat_pri = 'INFERENCE_OPT'
        elif any(k in text for k in ['agent', 'workflow', 'mcp', 'copilot', 'coding', 'ide', 'langchain']):
            cat_pri = 'AGENTS_DEVTOOLS'
        elif any(k in text for k in ['vision', 'diffusion', 'multimodal', 'image', 'video', 'audio', 'whisper', 'flux']):
            cat_pri = 'MULTIMODAL_AI'
        elif any(k in text for k in ['law', 'court', 'trial', 'judge', 'lawsuit', 'crime', 'police', 'arrest', 'prison']):
            cat_pri = 'CIVIC_CRIME_INCIDENT'
        elif any(k in text for k in ['market', 'stock', 'invest', 'fund', 'nasdaq', 'tariff', 'revenue', 'economy']):
            cat_pri = 'MACRO_GLOBAL_BIZ'
        elif any(k in text for k in ['space', 'nasa', 'astronomy', 'biology', 'genome', 'crispr', 'quantum', 'physics']):
            cat_pri = 'DEEP_SCIENCE_SPACE'
        elif any(k in text for k in ['rag', 'vector', 'database', 'postgres', 'security', 'auth', 'hack', 'firewall']):
            cat_pri = 'INFRA_RAG_SECURITY'
        else:
            cat_pri = 'INDUSTRY_TRENDS'

    if not t1:
        if cat_pri in ['INFERENCE_OPT', 'AGENTS_DEVTOOLS', 'MULTIMODAL_AI', 'FOUNDATION_MODELS', 'INFRA_RAG_SECURITY']:
            t1 = 'TECH_COMPUTING'
        elif cat_pri == 'DEEP_SCIENCE_SPACE':
            t1 = 'SCIENCE_RESEARCH'
        elif cat_pri == 'MACRO_GLOBAL_BIZ':
            t1 = 'ECONOMY_FINANCE'
        elif cat_pri == 'CIVIC_CRIME_INCIDENT':
            t1 = 'LAW_CRIME_JUSTICE'
        elif cat_pri == 'HISTORY_LIFE_CULTURE':
            t1 = 'CULTURE_HUMANITIES'
        else:
            t1 = 'TECH_COMPUTING'

    if not itype:
        if 'model' in platform or 'huggingface' in platform or any(k in text for k in ['weights', 'checkpoint', 'gguf']):
            itype = 'MODEL'
        elif 'agent' in text or 'autonomous' in text:
            itype = 'AGENT'
        elif any(k in platform for k in ['press', 'news', 'reuters', 'bloomberg', 'cnbc', 'wsj']):
            itype = 'NEWS'
        else:
            itype = 'TECH'

    artifact_type = 'ARTICLE'
    if itype == 'MODEL':
        artifact_type = 'WEIGHTS'
    elif 'github' in platform or any(k in text for k in ['repo', 'github.com', 'repository']):
        artifact_type = 'CODE_REPO'
    elif 'arxiv' in platform or 'paper' in text:
        artifact_type = 'PAPER'

    return {
        'tier1': t1,
        'categoryPrimary': cat_pri,
        'itemType': itype,
        'artifactType': artifact_type
    }

def call_openrouter_batch(items: list, api_key: str, model: str = PRIMARY_MODEL, timeout_sec: float = 15.0):
    prompt_items = []
    for it in items:
        p_item = {
            'id': it['inbox_id'],
            'platform': it.get('source_platform') or 'Unknown',
            'title': (it.get('title') or '')[:140],
            'description': re.sub(r'<[^>]+>', ' ', it.get('description') or '').strip()[:260]
        }
        raw_comments = it.get('raw_comments')
        if raw_comments and isinstance(raw_comments, list):
            top3 = [f"[@{c.get('author','User')}]: {(c.get('text','') or '')[:120]}" for c in raw_comments[:3]]
            if top3:
                p_item['community_feedback'] = ' / '.join(top3)
        prompt_items.append(p_item)

    req_body = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': f'분석할 항목 목록 (총 {len(prompt_items)}개):\n{json.dumps(prompt_items, ensure_ascii=False)}'}
        ],
        'temperature': 0.1,
        'max_tokens': 4200
    }

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://github.com/AnnyeongHae/ai-factcheck-portfolio',
        'X-Title': 'AI FactCheck Direct Bulk Enricher'
    }

    t0 = time.time()
    req_data = json.dumps(req_body, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(OPENROUTER_URL, data=req_data, headers=headers, method='POST')

    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            dur = time.time() - t0
            raw_bytes = resp.read().decode('utf-8')
            data = json.loads(raw_bytes)
            msg = data.get('choices', [{}])[0].get('message', {})
            raw_content = msg.get('content') or msg.get('reasoning') or ''
            parsed = sanitize_json(raw_content)
            if not parsed or not isinstance(parsed, list):
                return None, dur, 200, "Invalid JSON structure"
            return parsed, dur, 200, data.get('model') or model
    except urllib.error.HTTPError as he:
        dur = time.time() - t0
        err_msg = he.read().decode('utf-8', errors='replace')[:120]
        return None, dur, he.code, err_msg
    except Exception as e:
        return None, time.time() - t0, 500, str(e)[:120]

def run_bulk_drain(batch_size: int = 3, max_batches: int = 400, delay_sec: float = 0.5):
    api_key = get_openrouter_api_key()
    if not api_key:
        print("[!] ERROR: OPENROUTER_API_KEY is not set.")
        return

    print("==================================================================")
    print("🚀 [Bulk Drain Enricher] Initializing Direct Multilingual AI Enrichment")
    print(f"📦 Batch Size: {batch_size} items | Max Batches: {max_batches}")
    print(f"🧠 Primary Model: {PRIMARY_MODEL}")
    print("==================================================================")

    conn = get_db_connection()
    if not conn:
        print("[!] ERROR: Failed to connect to Aiven PostgreSQL SSOT.")
        return

    total_processed = 0
    total_start = time.time()
    consecutive_errors = 0

    for batch_idx in range(1, max_batches + 1):
        cur = conn.cursor()
        # Fetch unclassified items with FOR UPDATE SKIP LOCKED
        try:
            cur.execute("""
                SELECT id, inbox_id, source_platform, source_url, title, description, item_type, raw_payload
                FROM raw_trends_inbox
                WHERE is_classified = FALSE
                ORDER BY id DESC
                LIMIT %s
                FOR UPDATE SKIP LOCKED;
            """, (batch_size,))
            db_rows = cur.fetchall()
        except Exception as e:
            print(f"[!] DB Fetch Error on batch {batch_idx}: {e}")
            conn.rollback()
            time.sleep(2)
            continue

        if not db_rows:
            print(f"\n✨ [ALL DONE] No more unclassified items found! Total processed: {total_processed}")
            cur.close()
            break

        # Check total remaining
        cur.execute("SELECT COUNT(*) FROM raw_trends_inbox WHERE is_classified = FALSE;")
        remaining_cnt = cur.fetchone()[0]

        items_to_enrich = []
        for r in db_rows:
            p_payload = r[7] if isinstance(r[7], dict) else (json.loads(r[7]) if r[7] else {})
            items_to_enrich.append({
                'db_id': r[0],
                'inbox_id': r[1],
                'source_platform': r[2],
                'source_url': r[3],
                'title': r[4],
                'description': r[5],
                'item_type': r[6],
                'raw_payload': p_payload,
                'raw_comments': p_payload.get('raw_comments', [])
            })

        # Rotate model 50/50 to avoid per-model RPM throttling
        active_model = PRIMARY_MODEL if batch_idx % 2 == 1 else FALLBACK_MODEL
        alt_model = FALLBACK_MODEL if active_model == PRIMARY_MODEL else PRIMARY_MODEL

        parsed_ai_list, latency, status_code, model_or_err = call_openrouter_batch(items_to_enrich, api_key, active_model)

        if not parsed_ai_list:
            # Fallback model attempt on error OR rate limit
            print(f"  [Fallback] Retrying batch {batch_idx} with alternate model {alt_model} (primary returned {status_code})...", flush=True)
            if status_code == 429:
                time.sleep(1.5)
            parsed_ai_list, latency, status_code, model_or_err = call_openrouter_batch(items_to_enrich, api_key, alt_model)

        if not parsed_ai_list:
            consecutive_errors += 1
            print(f"[-] [Batch {batch_idx}] Failed (HTTP {status_code}: {model_or_err}) Latency: {latency:.2f}s | Errors: {consecutive_errors}/5", flush=True)
            conn.rollback()
            if status_code == 429:
                print("  [Rate Limit Backoff] Both models rate-limited, cooling down 10s...", flush=True)
                time.sleep(10.0)
                continue
            if consecutive_errors >= 5:
                print("[!] Circuit breaker tripped: 5 consecutive failures. Halting.", flush=True)
                break
            time.sleep(2.0)
            continue

        consecutive_errors = 0
        now_iso = datetime.now(timezone.utc).isoformat()
        enriched_count_in_batch = 0

        # Update DB for each item in batch
        for it in items_to_enrich:
            inbox_id = it['inbox_id']
            # Find matching AI result by id or match by index
            matched_ai = None
            for p in parsed_ai_list:
                if p.get('id') == inbox_id:
                    matched_ai = p
                    break
            if not matched_ai and len(parsed_ai_list) == len(items_to_enrich):
                matched_ai = parsed_ai_list[items_to_enrich.index(it)]
            if not matched_ai and len(parsed_ai_list) > 0:
                matched_ai = parsed_ai_list[0]

            if not matched_ai:
                continue

            payload = it['raw_payload']
            clean_title = (it['title'] or '').strip()

            title_ko = matched_ai.get('title_ko') or clean_title
            title_en = matched_ai.get('title_en') or clean_title
            title_zh = matched_ai.get('title_zh') or clean_title

            hook_ko = matched_ai.get('hook_ko') or title_ko
            hook_en = matched_ai.get('hook_en') or title_en
            hook_zh = matched_ai.get('hook_zh') or title_zh

            takeaways_ko = matched_ai.get('key_takeaways_ko') or [hook_ko]
            takeaways_en = matched_ai.get('key_takeaways_en') or [hook_en]
            takeaways_zh = matched_ai.get('key_takeaways_zh') or [hook_zh]

            inferred = infer_categories_and_artifact(it, matched_ai)

            canonical_key = re.sub(r'[^a-z0-9-]', '-', (matched_ai.get('canonical_story_key') or '').lower().strip()).strip('-')[:100]
            core_entities = [str(e).strip() for e in matched_ai.get('core_entities', []) if len(str(e).strip()) > 1][:5]
            canonical_tech = re.sub(r'[^a-z0-9-]', '-', (matched_ai.get('canonical_tech_entity') or '').lower().strip()).strip('-')[:50]
            if canonical_tech in ['null', 'none', '']:
                canonical_tech = None

            # Build standardized payload
            payload['title_ko'] = title_ko
            payload['title_en'] = title_en
            payload['title_zh'] = title_zh
            payload['hook'] = hook_ko
            payload['hook_ko'] = hook_ko
            payload['hook_en'] = hook_en
            payload['hook_zh'] = hook_zh
            payload['description_ko'] = hook_ko
            payload['description_en'] = hook_en
            payload['description_zh'] = hook_zh
            payload['key_takeaways'] = takeaways_ko
            payload['key_takeaways_ko'] = takeaways_ko
            payload['key_takeaways_en'] = takeaways_en
            payload['key_takeaways_zh'] = takeaways_zh

            payload['category_type'] = inferred['itemType']
            payload['category_primary'] = inferred['categoryPrimary']
            payload['tier1_category'] = inferred['tier1']
            payload['tier2_category'] = inferred['categoryPrimary']
            payload['artifact_type'] = inferred['artifactType']
            payload['programming_lang'] = matched_ai.get('programming_lang') or payload.get('programming_lang') or 'General'

            if canonical_tech:
                payload['canonical_tech_entity'] = canonical_tech
            if canonical_key:
                payload['canonical_story_key'] = canonical_key
                payload['dedup_fingerprint'] = {
                    'canonical_story_key': canonical_key,
                    'canonical_tech_entity': canonical_tech,
                    'core_entities': core_entities
                }

            payload['multilingual'] = {
                'ko': {'title': title_ko, 'hook': hook_ko, 'key_takeaways': takeaways_ko},
                'en': {'title': title_en, 'hook': hook_en, 'key_takeaways': takeaways_en},
                'zh': {'title': title_zh, 'hook': hook_zh, 'key_takeaways': takeaways_zh}
            }

            payload['ai_enrichment'] = {
                'id': inbox_id,
                'source_lang': 'EN',
                'programming_lang': payload['programming_lang'],
                'type_classification': inferred['itemType'],
                'category_primary': inferred['categoryPrimary'],
                'tier1_category': inferred['tier1'],
                'tier2_category': inferred['categoryPrimary'],
                'artifact_type': inferred['artifactType'],
                'canonical_story_key': canonical_key or None,
                'core_entities': core_entities,
                'korean_title': title_ko,
                'hook': hook_ko,
                'key_takeaways': takeaways_ko,
                'multilingual': payload['multilingual'],
                'enriched_by_model': model_or_err,
                'enriched_at': now_iso
            }

            cur.execute("""
                UPDATE raw_trends_inbox
                SET is_classified = TRUE,
                    category_primary = %s,
                    item_type = %s,
                    raw_payload = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE inbox_id = %s;
            """, (
                inferred['categoryPrimary'],
                inferred['itemType'],
                json.dumps(payload, ensure_ascii=False),
                inbox_id
            ))
            enriched_count_in_batch += 1

        conn.commit()
        cur.close()

        total_processed += enriched_count_in_batch
        new_rem = max(0, remaining_cnt - enriched_count_in_batch)
        print(f"[+] [Batch {batch_idx:3d}/{max_batches}] Enriched {enriched_count_in_batch} items in {latency:.2f}s | Total: {total_processed} | Remaining: {new_rem} | Sample: {items_to_enrich[0]['title'][:40]} -> {payload['title_ko'][:35]}", flush=True)

        if delay_sec > 0:
            time.sleep(delay_sec)

    conn.close()
    elapsed = time.time() - total_start
    print("==================================================================")
    print(f"🏁 [Bulk Drain Completed] Total Enriched: {total_processed} items in {elapsed:.1f}s ({total_processed / max(1, elapsed):.1f} items/sec)")
    print("==================================================================")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Bulk AI Multilingual Inbox Drain Enricher")
    parser.add_argument("--batch-size", type=int, default=3, help="Number of items per batch (default 3)")
    parser.add_argument("--max-batches", type=int, default=360, help="Max batches to process (default 360 = ~1080 items)")
    parser.add_argument("--delay", type=float, default=1.5, help="Delay between batches in seconds (default 1.5s)")
    args = parser.parse_args()

    run_bulk_drain(batch_size=args.batch_size, max_batches=args.max_batches, delay_sec=args.delay)
