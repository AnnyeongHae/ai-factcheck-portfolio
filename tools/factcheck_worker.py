#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/factcheck_worker.py
====================================================================
Autonomous Fact-Check Worker & Token Economics Ledger
- Scans for items in QUEUED_FOR_INVESTIGATION status
- Performs deep engineering verification using Gemini 3.6 Flash
- Measures exact prompt, candidate, and reasoning tokens
- Appends usage metadata to logs/token_usage_ledger.json
- Automatically updates inbox status and maintains token ledger
====================================================================
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT_DIR, '.env'))

LEDGER_PATH = os.path.join(ROOT_DIR, 'logs', 'token_usage_ledger.json')

def load_ledger():
    if os.path.exists(LEDGER_PATH):
        try:
            with open(LEDGER_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def record_token_usage(entry):
    ledger = load_ledger()
    ledger.append(entry)
    os.makedirs(os.path.dirname(LEDGER_PATH), exist_ok=True)
    with open(LEDGER_PATH, 'w', encoding='utf-8') as f:
        json.dump(ledger, f, ensure_ascii=False, indent=2)
    print(f"[+] Token ledger updated ({len(ledger)} total runs recorded).")

def get_queued_items():
    queued = []
    inbox_dir = os.path.join(ROOT_DIR, 'inbox')
    if os.path.exists(inbox_dir):
        for fname in os.listdir(inbox_dir):
            if not fname.endswith('.json'):
                continue
            fpath = os.path.join(inbox_dir, fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('status') == 'QUEUED_FOR_INVESTIGATION':
                        queued.append((fpath, data))
            except Exception:
                continue
    return queued

def main():
    parser = argparse.ArgumentParser(description="Autonomous Fact-Check Worker")
    parser.add_argument("--dry-run", action="store_true", help="Inspect queued items without calling API")
    parser.add_argument("--limit", type=int, default=1, help="Max items to process in one run")
    args = parser.parse_args()

    # 🚨 STRICT SAFETY POLICY: 외부 유료 API 토큰을 소모하는 자동 심층 팩트체크는 영구 금지됩니다.
    # 심층 팩트체크는 Antigravity 에이전트와의 로컬 페어 프로그래밍으로만 생성됩니다.
    print("[🛡️ SAFETY GUARD] External API-based factcheck worker is PERMANENTLY DISABLED.")
    print("                 Deep investigations must be conducted exclusively via Local Agent Pair Programming.")
    return

    for idx, (fpath, item) in enumerate(queued[:args.limit]):
        inbox_id = item.get('inbox_id', 'unknown')
        title = item.get('title', '')
        print(f"\n[{idx+1}/{min(len(queued), args.limit)}] Target: {title} ({inbox_id})")

        if args.dry_run:
            print("  [DRY-RUN] Would call Gemini 3.6 Flash to audit and promote this item.")
            continue

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("[-] GEMINI_API_KEY is not configured.")
            return

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        
        viral_metric = item.get('viral_metric', '') or item.get('metric_tracking', {}).get('latest', {}).get('display', '')
        prompt = f"""
다음 안건에 대해 시니어 엔지니어링 팩트체크 도시에를 생성하세요:
- 제목: {title}
- 플랫폼: {item.get('source_platform', '')}
- 바이럴/인게이지먼트 지표: {viral_metric}
- 설명: {item.get('description', '')}
- 출처 URL: {item.get('source_url', '')}

요구사항:
1. 완전한 유효 JSON으로만 응답할 것 (마크다운 코드블록 제외 또는 순수 JSON).
2. curation.personal_motivation 및 personal_motivation_en의 맨 앞부분에 반드시 "[{viral_metric}] "를 명시하여 발굴 의도에 좋아요/추천수 지표를 승계할 것.
3. 한국어, 영어, 중국어 3개국어 대칭 필드(title_ko, title_en, title_zh, quote, quote_zh, the_hook, the_hook_zh, the_hook_en) 포함.
4. verdict는 VERIFIED_TRUE, HALF_TRUE, GAMED_OR_EXAGGERATED 중 하나.
5. confidence_score(0~100 float) 및 구체적 하드웨어/아키텍처 실측 메트릭.
"""

        print("[*] Calling Gemini 3.6 Flash with token accounting...")
        t0 = time.time()
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2
            )
        )
        elapsed = time.time() - t0

        usage = response.usage_metadata
        prompt_tokens = usage.prompt_token_count or 0
        cand_tokens = usage.candidates_token_count or 0
        total_tokens = usage.total_token_count or (prompt_tokens + cand_tokens)

        # Gemini 3.6 Flash pricing: Input $0.15/1M, Output $0.60/1M
        cost_usd = (prompt_tokens / 1_000_000) * 0.15 + (cand_tokens / 1_000_000) * 0.60
        cost_krw = cost_usd * 1380.0

        print(f"[+] Fact-check generated in {elapsed:.2f}s")
        print(f"  - Tokens: Input {prompt_tokens:,} | Output {cand_tokens:,} | Total {total_tokens:,}")
        print(f"  - Cost: ${cost_usd:.6f} (about {cost_krw:.2f} KRW)")

        # Record to ledger
        record_token_usage({
            "timestamp": datetime.now().isoformat(),
            "inbox_id": inbox_id,
            "title": title,
            "model": "gemini-3.6-flash",
            "prompt_tokens": prompt_tokens,
            "candidate_tokens": cand_tokens,
            "total_tokens": total_tokens,
            "cost_usd": cost_usd,
            "cost_krw": cost_krw,
            "elapsed_seconds": round(elapsed, 2)
        })

        # Update inbox file status
        item['status'] = 'FACT_CHECKED'
        item['audited_at'] = datetime.now().isoformat()
        with open(fpath, 'w', encoding='utf-8') as f:
            json.dump(item, f, ensure_ascii=False, indent=2)
        print(f"[+] Updated inbox item status to FACT_CHECKED.")

if __name__ == "__main__":
    main()
