#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enterprise Multi-Item Batch AI Inbox Auto-Enricher (v7.0)
- 3-Item Batching for 67% Quota Reduction & 13.3 RPM Rate-Limit Defense
- Automatic Classification: MODEL | AGENT | TECH | NEWS
- Source Language Detection: KO | EN | ZH
- The Hook ("사람이 읽고 싶은 1줄 훅") & 3-line Summary Extraction
- Programming Language & Root Keywords Detection
- Auto-Linking with Existing 18 Fact-Check Dossiers
"""

import argparse
import glob
import json
import os
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
    """Load existing 18 fact-check dossiers for root technology matching."""
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
    """Find the best matching verified dossier, or None."""
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

def call_gemini_batch_enricher(api_key: str, batch_items: list, retries: int = 3) -> list:
    """Sends a batch of 3 items to Gemini 3.6 Flash and returns an array of enrichments."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}"

    system_prompt = (
        "당신은 최고 수준의 시니어 AI 아키텍트이자 엔터프라이즈 기술 팩트체커입니다.\n"
        "주어진 기술/뉴스 후보 항목 배열을 분석하여, 각 항목마다 아래 스키마를 만족하는 JSON 배열로만 응답하세요.\n"
        "반드시 JSON 포맷만을 반환해야 하며, 마크다운이나 부가 설명은 일절 포함하지 마세요.\n\n"
        "[\n"
        "  {\n"
        '    "id": "입력받은 id",\n'
        '    "source_lang": "KO 또는 EN 또는 ZH (원문 언어)",\n'
        '    "type_classification": "MODEL(새 모델/가중치/아키텍처 발표) 또는 AGENT(에이전트 프레임워크/도구/하네스) 또는 TECH(신기술/최적화/엔지니어링/라이브러리) 또는 NEWS(단순 업계동향/통계/기업이슈/칼럼)",\n'
        '    "category": "세부 기술 카테고리 (예: LLM 양자화 및 추론, 웹 에이전트, 비디오 편집, 데이터베이스 등)",\n'
        '    "programming_lang": "핵심 프로그래밍 언어/런타임 (예: Python, Rust, TypeScript, C++, CUDA 등, 없으면 General)",\n'
        '    "root_keywords": ["핵심 Root 키워드 1", "핵심 Root 키워드 2", "핵심 Root 키워드 3"],\n'
        '    "korean_title": "기술 본질을 정확하고 매력적으로 전달하는 한국어 번역 제목",\n'
        '    "hook": "엔지니어가 이 기술/기사를 당장 읽고 싶게 만드는 결정적 1문장 훅 (The Hook: 파괴적 혁신, 실무적 충격, 메모리/비용 절감 포인트 강조)",\n'
        '    "key_takeaways": [\n'
        '      "핵심 포인트 1",\n'
        '      "핵심 포인트 2",\n'
        '      "핵심 포인트 3"\n'
        "    ],\n"
        '    "recommended_tag": "🔥 강력 추천 (필독) 또는 💡 유용한 도구 또는 📝 기술 참고",\n'
        '    "worth_score": 1.0부터 5.0 사이의 추천 가치 점수\n'
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

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    backoff_delays = [5, 12, 25]
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=35) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(raw_text)
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8", errors="ignore")
            print(f"[!] HTTP Error {e.code} (Attempt {attempt+1}/{retries}): {err_msg[:100]}")
            if e.code == 429:
                wait_t = backoff_delays[attempt]
                print(f"[*] 429 Rate Limit hit. Backing off for {wait_t}s...")
                time.sleep(wait_t)
            else:
                if attempt == retries - 1: raise
                time.sleep(backoff_delays[attempt])
        except Exception as e:
            print(f"[!] Network Error (Attempt {attempt+1}/{retries}): {e}")
            if attempt == retries - 1: raise
            time.sleep(backoff_delays[attempt])

    return []

def run_enrichment_pipeline(limit: int = 15, batch_size: int = 3, force_all: bool = False):
    key = get_gemini_api_key()
    if not key:
        print("[!] ERROR: GEMINI_API_KEY is not set in environment or .env file!")
        sys.exit(1)

    dossiers = load_existing_dossiers()
    print(f"[*] Loaded {len(dossiers)} verified dossiers for technology linking.")

    inbox_files = sorted(glob.glob("inbox/*.json"), reverse=True)
    print(f"[*] Total files in inbox: {len(inbox_files)}")

    target_items = []
    for f in inbox_files:
        try:
            with open(f, "r", encoding="utf-8") as fp:
                d = json.load(fp)
                if force_all or not d.get("ai_enrichment"):
                    target_items.append((f, d))
                    if len(target_items) >= limit:
                        break
        except Exception:
            continue

    total_to_process = len(target_items)
    print(f"[*] Selected {total_to_process} target items to enrich (Batch size: {batch_size})...")

    if total_to_process == 0:
        print("[+] All target items already enriched. Nothing to do.")
        return

    # Process in batches of 3
    success_count = 0
    num_batches = (total_to_process + batch_size - 1) // batch_size

    for b_idx in range(num_batches):
        batch = target_items[b_idx * batch_size : (b_idx + 1) * batch_size]
        batch_raw = [item for _, item in batch]

        print(f"\n=======================================================")
        print(f"[*] Executing Batch {b_idx+1}/{num_batches} ({len(batch)} items)...")
        for _, it in batch:
            print(f"  - [{it.get('source_platform')}] {it.get('title')[:45]}...")

        try:
            results = call_gemini_batch_enricher(key, batch_raw)
            # Map results by id
            res_map = {r["id"]: r for r in results if "id" in r}

            for fpath, item in batch:
                iid = item.get("inbox_id")
                enrich_data = res_map.get(iid)
                if not enrich_data:
                    # Fallback matching by index if IDs mismatched
                    idx = [it.get("inbox_id") for _, it in batch].index(iid)
                    if idx < len(results):
                        enrich_data = results[idx]

                if enrich_data:
                    item["ai_enrichment"] = enrich_data
                    item["source_lang"] = enrich_data.get("source_lang", "EN")
                    item["programming_lang"] = enrich_data.get("programming_lang", "General")
                    item["root_keywords"] = enrich_data.get("root_keywords", [])
                    item["hook"] = enrich_data.get("hook", "")
                    
                    if enrich_data.get("korean_title"):
                        item["title_ko"] = enrich_data["korean_title"]
                    if enrich_data.get("key_takeaways"):
                        item["description_ko"] = enrich_data.get("hook") or item.get("description_ko")

                    # Classification Routing
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
                        print(f"  [🔗 LINKED DOSSIER] {related['target_tech']} -> {related['case_id']}")

                    with open(fpath, "w", encoding="utf-8") as fp:
                        json.dump(item, fp, indent=2, ensure_ascii=False)

                    print(f"  [+] [{c_type} | {item['source_lang']}] {enrich_data.get('korean_title')[:35]}")
                    print(f"      Hook: {enrich_data.get('hook')[:60]}...")
                    success_count += 1

            # Safety delay to strictly respect 15 RPM
            if b_idx < num_batches - 1:
                print(f"[*] Sleeping 4.5s for 15 RPM rate-limit margin...")
                time.sleep(4.5)

        except Exception as e:
            print(f"[!] Batch {b_idx+1} failed completely: {e}")

    print(f"\n=======================================================")
    print(f"[🎉] Enrichment Finished: {success_count}/{total_to_process} items successfully updated!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=15, help="Number of items to enrich (default: 15)")
    parser.add_argument("--batch-size", type=int, default=3, help="Batch size per API call (default: 3)")
    parser.add_argument("--all", action="store_true", help="Force re-enrich all items")
    args = parser.parse_args()
    run_enrichment_pipeline(limit=args.limit, batch_size=args.batch_size, force_all=args.all)
