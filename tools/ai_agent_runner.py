#!/usr/bin/env python3
"""
AI Agent Autonomous Triage & Deep Fact-Check Runner (2026 SOTA Framework - v2.0)
- Neon DB에서 사용자가 웹/대시보드에서 '분석 요청(REQUESTED_ANALYSIS)'한 항목을 1순위로 감지
- 미검증 최신 트렌드(PENDING_REVIEW) 브리핑
- 사용자 요청 시 WaterCrawl급 심층 팩트체크 리포트 합성
"""

import argparse
import json
import os
import sys

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from tools.db_bridge import get_db_connection

def scan_requested_analysis():
    """Scan for user-requested analysis items from Neon DB or local inbox."""
    conn = get_db_connection()
    requested = []
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT inbox_id, title, source_platform, source_url, viral_metric, matched_user_domains, description, harvested_date
                    FROM raw_trends_inbox
                    WHERE triage_status = 'REQUESTED_ANALYSIS'
                    ORDER BY id DESC;
                """)
                rows = cur.fetchall()
                for r in rows:
                    requested.append({
                        "inbox_id": r[0], "title": r[1], "source_platform": r[2], "source_url": r[3],
                        "viral_metric": r[4], "matched_user_domains": r[5], "description": r[6], "harvested_date": r[7]
                    })
        except Exception as e:
            print(f"[!] Neon DB scan note: {e}")
        finally:
            conn.close()

    # Local fallback
    inbox_dir = os.path.join(base_dir, "inbox")
    if not requested and os.path.exists(inbox_dir):
        for f in os.listdir(inbox_dir):
            if f.endswith(".json"):
                try:
                    with open(os.path.join(inbox_dir, f), "r", encoding="utf-8") as fp:
                        it = json.load(fp)
                        if it.get("status") == "REQUESTED_ANALYSIS":
                            requested.append(it)
                except Exception:
                    pass

    return requested

def show_triage_dashboard(top_n=5):
    requested = scan_requested_analysis()
    
    print("\n" + "="*85)
    print(" 🤖 [Antigravity AI Fact-Check Command Center] Neon DB 실시간 큐 모니터")
    print("="*85)

    if requested:
        print(f"\n🔥 [사용자 직접 분석 요청 대기열 (REQUESTED_ANALYSIS)] -> 총 {len(requested)}건 발견!")
        print("-" * 85)
        for idx, r in enumerate(requested, 1):
            print(f"[{idx:02d}] ⚡ {r.get('title')}")
            print(f"     • 출처: {r.get('source_platform')} | URL: {r.get('source_url')}")
            print(f"     • 바이럴 지표: {r.get('viral_metric')}")
            print(f"     👉 지금 바로 심층 팩트체크 실행: python tools/triage.py --promote {r.get('inbox_id')}")
    else:
        print("\n[*] 현재 사용자가 웹에서 직접 의뢰한 '분석 대기열'은 비어 있습니다.")

    # Show Pending Trends
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT inbox_id, title, source_platform, source_url, viral_metric, matched_user_domains, description, harvested_date
                    FROM raw_trends_inbox
                    WHERE triage_status = 'PENDING_REVIEW'
                    ORDER BY harvested_date DESC, id DESC
                    LIMIT %s;
                """, (top_n,))
                pending = cur.fetchall()
            
            print("\n" + "-" * 85)
            print(f" 📥 [자동 수집된 미검증 트렌드 후보 (PENDING_REVIEW)] 상위 {len(pending)}건")
            print("-" * 85)
            for idx, p in enumerate(pending, 1):
                print(f"[{idx:02d}] 📌 {p[1]}")
                print(f"     • 플랫폼: {p[2]} | {p[4]}")
                print(f"     • URL: {p[3]}")
                print(f"     👉 분석 큐 등록: python tools/triage.py --request-analysis {p[0]}")
        finally:
            conn.close()

    print("\n" + "="*85 + "\n")

def main():
    parser = argparse.ArgumentParser(description="AI Agent Command Center")
    parser.add_argument("--top", type=int, default=5, help="Number of pending candidates to show")
    args = parser.parse_args()
    show_triage_dashboard(args.top)

if __name__ == "__main__":
    main()
