#!/usr/bin/env python3
"""
AI Agent Orchestration & Autonomous Triage Runner (2026 SOTA Framework)
Neon Postgres DB의 raw_trends_inbox를 스캔하여 AI 에이전트의 심층 팩트체크를 트리거합니다.
"""

import argparse
import json
import os
import sys

# Ensure UTF-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from tools.db_bridge import get_db_connection

def triage_pending_trends(top_n=5):
    conn = get_db_connection()
    if not conn:
        print("[!] Cannot connect to Neon DB. Falling back to local inbox/ directory.")
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        inbox_dir = os.path.join(base_dir, "inbox")
        items = []
        for f in os.listdir(inbox_dir):
            if f.endswith(".json"):
                try:
                    with open(os.path.join(inbox_dir, f), "r", encoding="utf-8") as fp:
                        items.append(json.load(fp))
                except Exception:
                    pass
        print(f"\n[🤖 AI Agent Inbox Scan] Found {len(items)} pending candidates locally.")
        for idx, it in enumerate(items[:top_n], 1):
            print(f"[{idx}] {it.get('title')} ({it.get('source_platform')}) - Domains: {it.get('matched_user_domains')}")
        return

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT inbox_id, title, source_platform, source_url, viral_metric, matched_user_domains, description, harvested_date
                FROM raw_trends_inbox
                WHERE triage_status = 'PENDING_REVIEW'
                ORDER BY harvested_date DESC, id DESC
                LIMIT %s;
            """, (top_n,))
            rows = cur.fetchall()

        print("\n" + "="*80)
        print(f" 🤖 [AI Agent Autonomous Triage] Neon DB 최신 미검증 트렌드 TOP {len(rows)} 분석 보고")
        print("="*80)

        for idx, r in enumerate(rows, 1):
            inbox_id, title, platform, url, viral, domains, desc, hdate = r
            domains_str = ", ".join(domains) if isinstance(domains, list) else str(domains)
            print(f"\n[{idx:02d}] 📌 {title}")
            print(f"     • 플랫폼: {platform} | 수집일자: {hdate}")
            print(f"     • 원문 URL: {url}")
            print(f"     • 바이럴 지표: {viral}")
            print(f"     • 사용자 연계 도메인: {domains_str}")
            print(f"     • 요약: {desc[:100]}...")
            print(f"     👉 승인 및 팩트체크 실행: python tools/triage.py --promote {inbox_id}")
        
        print("\n" + "="*80)
        print("💡 AI 제언: 위 후보 중 관심 있는 번호의 승격 명령어를 실행하시면 심층 팩트체크가 즉시 진행됩니다.\n")

    except Exception as e:
        print(f"[!] Error querying Neon DB: {e}")
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="AI Agent Triage Runner")
    parser.add_argument("--triage-pending", action="store_true", default=True, help="Scan Neon DB for pending trends and generate briefing")
    parser.add_argument("--top", type=int, default=5, help="Number of top candidates to display")

    args = parser.parse_args()
    triage_pending_trends(args.top)

if __name__ == "__main__":
    main()
