#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI-Powered Inbox Auto-Enricher (Classification, Korean 3-line Summary & Value Scoring)
Powered by Google Gemini 3.6 Flash (100% Free Tier: 1,500 RPD)
"""

import argparse
import glob
import json
import os
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

def call_gemini_enricher(api_key: str, title: str, platform: str, desc: str) -> dict:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}"
    
    system_prompt = (
        "당신은 최고 수준의 시니어 AI 아키텍트이자 기술 팩트체커입니다. "
        "주어진 오픈소스/기술 뉴스 항목을 분석하여 바쁜 한국인 개발자를 위해 핵심을 간결하게 정리하세요.\n"
        "반드시 아래 JSON 형식으로만 응답하세요:\n"
        "{\n"
        '  "category": "핵심 기술 분야 (예: LLM 경량화/추론가속, 웹 에이전트 도구, 데이터 인프라, 비디오/멀티모달, 보안/감사 등)",\n'
        '  "korean_title": "이해하기 쉽고 직관적인 한국어 번역 제목",\n'
        '  "one_line_summary": "핵심을 꿰뚫는 1줄 요약",\n'
        '  "key_takeaways": ["핵심 포인트 1", "핵심 포인트 2", "핵심 포인트 3"],\n'
        '  "recommended_tag": "🔥 강력 추천 (필독) 또는 💡 유용한 도구 또는 📝 기술 참고",\n'
        '  "worth_investigating": "HIGH 또는 MEDIUM 또는 LOW",\n'
        '  "score": 1.0부터 5.0 사이의 추천 가치 점수\n'
        "}"
    )

    user_content = f"플랫폼: {platform}\n제목: {title}\n원문 설명: {desc}"

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": system_prompt + "\n\n" + user_content}
                ]
            }
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

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(raw_text)

def enrich_inbox_items(limit: int = 3, specific_files: list = None):
    key = get_gemini_api_key()
    if not key:
        print("[!] ERROR: GEMINI_API_KEY is not set in environment or .env file!")
        sys.exit(1)

    pending_files = []

    if specific_files:
        for sf in specific_files:
            if os.path.exists(sf):
                with open(sf, "r", encoding="utf-8") as fp:
                    pending_files.append((sf, json.load(fp)))
    else:
        inbox_files = glob.glob("inbox/*.json")
        for f in inbox_files:
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    d = json.load(fp)
                    if not d.get("ai_enrichment"):
                        pending_files.append((f, d))
                        if len(pending_files) >= limit:
                            break
            except Exception:
                continue

    print(f"[*] Processing {len(pending_files)} items with Gemini 3.6 Flash...")

    success_count = 0
    for idx, (fpath, item) in enumerate(pending_files, start=1):
        fname = os.path.basename(fpath)
        title = item.get("title", "")
        platform = item.get("source_platform", "Unknown")
        desc = item.get("description", "")

        print(f"\n[{idx}/{len(pending_files)}] Enriching: {title} ({platform})")
        try:
            res = call_gemini_enricher(key, title, platform, desc)
            item["ai_enrichment"] = res
            if res.get("korean_title"):
                item["title_ko"] = res["korean_title"]
            if res.get("one_line_summary"):
                item["description_ko"] = res["one_line_summary"]

            with open(fpath, "w", encoding="utf-8") as fp:
                json.dump(item, fp, indent=2, ensure_ascii=False)

            safe_tag = res.get('recommended_tag', '')
            safe_cat = res.get('category', '')
            print(f"  [+] Category: {safe_cat} | Tag: {safe_tag} | Score: {res.get('score')}")
            print(f"  [+] Title: {res.get('korean_title')}")
            print(f"  [+] Summary: {res.get('one_line_summary')}")
            for kp in res.get("key_takeaways", []):
                print(f"      - {kp}")
            success_count += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"  [-] Failed to enrich {fname}: {e}")

    print(f"\n[OK] Complete! {success_count}/{len(pending_files)} items enriched successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=3, help="Number of items to enrich (default: 3)")
    parser.add_argument("--files", nargs="*", help="Specific files to enrich")
    args = parser.parse_args()
    enrich_inbox_items(limit=args.limit, specific_files=args.files)
