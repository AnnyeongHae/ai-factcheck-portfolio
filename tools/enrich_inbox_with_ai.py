#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enterprise Trilingual AI Inbox Auto-Enricher (v8.0)
- Trilingual Parity: Full KO (한국어) / EN (English) / ZH (中文) Extraction for Every Item
- 3-Item Batching with Smart Multi-Model Fallback (gemini-flash-latest -> gemini-flash-lite-latest -> gemma-4-31b-it)
- The Hook ("사람이 읽고 싶은 1줄 훅") in 3 Languages
- 4-Tier Classification: MODEL | AGENT | TECH | NEWS
- Automatic 18-Dossier Knowledge Graph Linking
"""

import argparse
import glob
import json
import os
import random
import re
import sys
import time
import urllib.request
import urllib.error

# Force UTF-8 on Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

MODEL_POOL = [
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemma-4-31b-it",
    "gemma-4-26b-a4b-it",
    "gemini-3.6-flash"
]

def get_gemini_api_key():
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key and os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("GEMINI_API_KEY="):
                    key = line.strip().split("=", 1)[1].strip("\"'")
                    break
    return key

def load_existing_dossiers():
    inv_dir = "investigations"
    dossiers = []
    if not os.path.exists(inv_dir):
        return dossiers

    for item in sorted(os.listdir(inv_dir)):
        mpath = os.path.join(inv_dir, item, "metadata.json")
        if os.path.exists(mpath):
            try:
                with open(mpath, "r", encoding="utf-8") as fp:
                    m = json.load(fp)
                    if "title" in m and m.get("title") != "[이슈명]":
                        dossiers.append({
                            "case_id": m.get("case_id"),
                            "title": m.get("title"),
                            "target_tech": m.get("target_technology", {}).get("name", ""),
                            "tags": [t.lower() for t in m.get("tags", [])],
                            "stack": [s.lower() for s in m.get("technology_stack", [])]
                        })
            except Exception:
                continue
    return dossiers

def match_dossier(dossiers, title, category, programming_lang, root_keywords):
    query_text = (title + " " + category + " " + programming_lang + " " + " ".join(root_keywords)).lower()
    best_match = None
    best_score = 0

    for d in dossiers:
        score = 0
        target = d["target_tech"].lower()
        if target and target in query_text:
            score += 5

        for tag in d["tags"]:
            if len(tag) > 2 and tag in query_text:
                score += 2

        for st in d["stack"]:
            if len(st) > 2 and st in query_text:
                score += 1

        if score > best_score and score >= 4:
            best_score = score
            best_match = {
                "case_id": d["case_id"],
                "title": d["title"],
                "target_tech": d["target_tech"]
            }
    return best_match

def call_gemini_trilingual_batch(api_key: str, batch_items: list) -> list:
    """Calls Gemini with 3-item batch and requests complete KO/EN/ZH trilingual parity."""
    system_prompt = (
        "당신은 글로벌 최고 수준의 다국어 AI 기술 아키텍트입니다.\n"
        "주어진 기술/뉴스 후보 목록을 분석하여, 각 항목마다 한국어(KO), 영어(EN), 중국어(ZH) 3개 국어로 완벽하게 번역 및 요약하여 아래 JSON 배열로만 응답하세요.\n"
        "반드시 JSON 배열만 출력해야 하며 마크다운이나 기타 텍스트는 일절 금지합니다.\n\n"
        "[\n"
        "  {\n"
        '    "id": "입력받은 id",\n'
        '    "source_lang": "KO 또는 EN 또는 ZH (원문의 원래 언어)",\n'
        '    "type_classification": "MODEL (새 모델/가중치 발표) 또는 AGENT (에이전트 도구/하네스) 또는 TECH (신기술/아키텍처/최적화) 또는 NEWS (단순 업계동향/통계/칼럼)",\n'
        '    "category": "세부 기술 카테고리 (예: LLM 추론 최적화, 웹 에이전트, 영상 제작 등)",\n'
        '    "programming_lang": "주요 프로그래밍 언어 (예: Rust, Python, TypeScript, CUDA, C++ 등, 없으면 General)",\n'
        '    "root_keywords": ["상위 키워드 1", "상위 키워드 2", "상위 키워드 3"],\n'
        '    "recommended_tag": "🔥 강력 추천 (필독) 또는 💡 유용한 도구 또는 📝 기술 참고",\n'
        '    "worth_score": 1.0~5.0 사이 점수,\n'
        '    "multilingual": {\n'
        '      "ko": {\n'
        '        "title": "직관적인 한국어 번역 제목",\n'
        '        "hook": "엔지니어가 이 글을 지금 당장 읽어야 하는 1줄 결정적 훅 (한국어)",\n'
        '        "key_takeaways": ["핵심 포인트 1", "핵심 포인트 2", "핵심 포인트 3"]\n'
        '      },\n'
        '      "en": {\n'
        '        "title": "Refined and attractive English Title",\n'
        '        "hook": "Compelling 1-line hook for engineers (English)",\n'
        '        "key_takeaways": ["Key Point 1", "Key Point 2", "Key Point 3"]\n'
        '      },\n'
        '      "zh": {\n'
        '        "title": "精准精炼且具吸引力的中文标题",\n'
        '        "hook": "直击工程师痛点的1句话亮点与阅读理由 (中文)",\n'
        '        "key_takeaways": ["核心要点 1", "核心要点 2", "核心要点 3"]\n'
        '      }\n'
        '    }\n'
        "  }\n"
        "]"
    )

    clean_batch = []
    for item in batch_items:
        clean_desc = re.sub(r'<[^>]+>', ' ', item.get("description", "")).strip()[:350]
        clean_batch.append({
            "id": item["inbox_id"],
            "platform": item.get("source_platform", "Unknown"),
            "title": item.get("title", ""),
            "description": clean_desc
        })

    user_content = json.dumps(clean_batch, ensure_ascii=False, indent=2)

    payload = {
        "contents": [
            {"parts": [{"text": system_prompt + "\n\n분석할 항목 목록:\n" + user_content}]}
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.2
        }
    }

    # Model Fallback Loop
    for model_name in MODEL_POOL:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=35) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                print(f"  [+] Responded by model '{model_name}' successfully.")
                return json.loads(raw_text)
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8", errors="ignore")
            if e.code == 429:
                print(f"  [-] Model '{model_name}' quota exhausted (429). Trying fallback model...")
                time.sleep(1)
                continue
            elif e.code == 404:
                continue
            else:
                print(f"  [-] HTTP Error {e.code} on '{model_name}': {err_msg[:80]}")
                time.sleep(2)
                continue
        except Exception as e:
            print(f"  [-] Network Error on '{model_name}': {e}")
            time.sleep(2)
            continue

    print("[!] All fallback models in pool exhausted!")
    return []

def run_enrichment(limit: int = 12, batch_size: int = 3, random_pick: bool = True):
    key = get_gemini_api_key()
    if not key:
        print("[!] ERROR: GEMINI_API_KEY is not set!")
        sys.exit(1)

    dossiers = load_existing_dossiers()
    print(f"[*] Loaded {len(dossiers)} verified dossiers.")

    inbox_files = glob.glob("inbox/*.json")
    print(f"[*] Total files in inbox: {len(inbox_files)}")

    # Load candidates
    candidates = []
    for f in inbox_files:
        try:
            with open(f, "r", encoding="utf-8") as fp:
                d = json.load(fp)
                # Pick items that don't have full trilingual yet
                has_tri = d.get("ai_enrichment", {}).get("multilingual", {}).get("zh")
                if not has_tri:
                    candidates.append((f, d))
        except Exception:
            continue

    print(f"[*] Candidates pending trilingual enrichment: {len(candidates)}")

    if random_pick and len(candidates) > limit:
        # Pick 12 random items as requested by user
        selected = random.sample(candidates, limit)
        print(f"[*] Randomly selected {limit} items for 4-batch test run.")
    else:
        selected = candidates[:limit]

    total_to_process = len(selected)
    num_batches = (total_to_process + batch_size - 1) // batch_size
    success_count = 0

    for b_idx in range(num_batches):
        batch = selected[b_idx * batch_size : (b_idx + 1) * batch_size]
        batch_raw = [item for _, item in batch]

        print(f"\n=======================================================")
        print(f"[*] Batch {b_idx+1}/{num_batches} ({len(batch)} items):")
        for _, it in batch:
            print(f"  - [{it.get('source_platform')}] {it.get('title')[:45]}...")

        results = call_gemini_trilingual_batch(key, batch_raw)
        res_map = {r["id"]: r for r in results if "id" in r}

        for fpath, item in batch:
            iid = item.get("inbox_id")
            enrich_data = res_map.get(iid)
            if not enrich_data:
                idx = [it.get("inbox_id") for _, it in batch].index(iid)
                if idx < len(results):
                    enrich_data = results[idx]

            if enrich_data:
                multi = enrich_data.get("multilingual", {})
                ko_data = multi.get("ko", {})
                en_data = multi.get("en", {})
                zh_data = multi.get("zh", {})

                item["ai_enrichment"] = enrich_data
                item["source_lang"] = enrich_data.get("source_lang", "EN")
                item["programming_lang"] = enrich_data.get("programming_lang", "General")
                item["root_keywords"] = enrich_data.get("root_keywords", [])
                
                # Trilingual titles
                item["title_ko"] = ko_data.get("title") or enrich_data.get("korean_title") or item.get("title_ko")
                item["title_en"] = en_data.get("title") or item.get("title_en") or item.get("title")
                item["title_zh"] = zh_data.get("title") or item.get("title_zh")

                # Trilingual hooks
                item["hook"] = ko_data.get("hook") or enrich_data.get("hook")
                item["hook_ko"] = ko_data.get("hook")
                item["hook_en"] = en_data.get("hook")
                item["hook_zh"] = zh_data.get("hook")

                # Trilingual descriptions
                item["description_ko"] = item["hook_ko"] or item.get("description_ko")
                item["description_en"] = item["hook_en"] or item.get("description_en") or item.get("description")
                item["description_zh"] = item["hook_zh"] or item.get("description_zh")

                # Routing
                c_type = enrich_data.get("type_classification", "TECH")
                item["category_type"] = "NEWS" if c_type == "NEWS" else c_type

                # Match with existing 18 dossiers
                related = match_dossier(
                    dossiers,
                    item.get("title", ""),
                    enrich_data.get("category", ""),
                    enrich_data.get("programming_lang", ""),
                    enrich_data.get("root_keywords", [])
                )
                if related:
                    item["related_dossier"] = related
                    print(f"  [🔗 LINKED] {related['target_tech']} -> {related['case_id']}")

                with open(fpath, "w", encoding="utf-8") as fp:
                    json.dump(item, fp, indent=2, ensure_ascii=False)

                print(f"  [+] [{c_type} | {item['source_lang']}] {item['title_ko'][:30]}")
                print(f"      KO: {item['hook_ko'][:45]}...")
                print(f"      EN: {item['hook_en'][:45]}...")
                print(f"      ZH: {item['hook_zh'][:45]}...")
                success_count += 1

        if b_idx < num_batches - 1:
            print("[*] Sleeping 4.5s for RPM quota safety margin...")
            time.sleep(4.5)

    print(f"\n=======================================================")
    print(f"[🎉] Complete! {success_count}/{total_to_process} items trilingually enriched!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=12, help="Number of items (default: 12)")
    parser.add_argument("--batch-size", type=int, default=3, help="Batch size (default: 3)")
    parser.add_argument("--random", action="store_true", default=True, help="Pick randomly")
    args = parser.parse_args()
    run_enrichment(limit=args.limit, batch_size=args.batch_size, random_pick=args.random)
