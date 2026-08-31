#!/usr/bin/env python3
"""
Triage & Promotion Gate (2026 SOTA Framework - v4.0)
inbox/에 보관된 대량의 트렌드 후보를 검토/일괄 승격/반려하고, logs/ 수집 시스템 상태를 실시간 모니터링합니다.

Usage:
    python tools/triage.py --list
    python tools/triage.py --promote <case_id>
    python tools/triage.py --promote-top 3
    python tools/triage.py --status
    python tools/triage.py --reject <case_id>
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

# Ensure UTF-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def list_inbox(limit=20):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    inbox_dir = os.path.join(base_dir, "inbox")
    
    if not os.path.exists(inbox_dir):
        print("[-] Inbox is empty.")
        return

    items = []
    for f in sorted(os.listdir(inbox_dir)):
        if f.endswith(".json"):
            path = os.path.join(inbox_dir, f)
            try:
                with open(path, "r", encoding="utf-8") as fp:
                    items.append(json.load(fp))
            except Exception:
                pass

    if not items:
        print("\n[*] Inbox is clean! No pending items waiting for review.")
        return

    print(f"\n==========================================================================================")
    print(f" 📥 승인 대기 중인 트렌드 후보 목록 (Total: {len(items)}건 중 상위 {min(limit, len(items))}건 표시)")
    print(f" (사용자가 승인해야만 포트폴리오로 승격됩니다)")
    print(f"==========================================================================================")
    for idx, it in enumerate(items[:limit], 1):
        print(f"\n[{idx:02d}] Case ID: {it.get('inbox_id')}")
        print(f"     - 제목: {it.get('title')}")
        print(f"     - 출처: {it.get('source_platform')} ({it.get('source_url')})")
        print(f"     - 바이럴 지표: {it.get('viral_metric')}")
        print(f"     - 맞춤 도메인: {', '.join(it.get('matched_user_domains', []))}")
        print(f"     👉 승인: python tools/triage.py --promote {it.get('inbox_id')}")
    print(f"==========================================================================================")
    print(f"💡 팁: 상위 3건을 한 번에 승격하려면 -> python tools/triage.py --promote-top 3\n")

def show_status():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    history_file = os.path.join(base_dir, "logs", "harvest_history.json")
    
    if not os.path.exists(history_file):
        print("[-] No harvest history found. Run 'python tools/harvest_trends.py' first.")
        return

    with open(history_file, "r", encoding="utf-8") as f:
        history = json.load(f)

    if not history:
        print("[-] History log is empty.")
        return

    latest = history[0]
    print(f"\n=======================================================")
    print(f" 🩺 시스템 수집 상태 및 헬스체크 모니터 ({latest.get('date')})")
    print(f"=======================================================")
    print(f"- 최근 수집 시각: {latest.get('timestamp')}")
    print(f"- 수집된 신규 후보: {latest.get('summary', {}).get('new_saved', 0)}건")
    print(f"- 중복 스킵 건수:   {latest.get('summary', {}).get('duplicates_skipped', 0)}건")
    print(f"- 에러/경고 발생:   {latest.get('summary', {}).get('errors', 0)}건")
    print(f"-------------------------------------------------------")
    print(f" [소스별 세부 헬스 상태]")
    for src, info in latest.get("sources", {}).items():
        st = info.get("status", "UNKNOWN")
        dur = info.get("duration_sec", 0)
        if st == "SUCCESS":
            cnt = info.get("items_found", 0)
            print(f"  • {src.upper():<14}: 🟢 [SUCCESS] {cnt:>2} items ({dur}s)")
        else:
            err = info.get("error", "Unknown error")
            print(f"  • {src.upper():<14}: 🟡 [BLOCKED/ERR] {err} ({dur}s)")
    print(f"=======================================================\n")

def promote_case(case_id, rebuild_after=True):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    inbox_file = os.path.join(base_dir, "inbox", f"{case_id}.json" if not case_id.endswith(".json") else case_id)
    
    if not os.path.exists(inbox_file):
        print(f"[!] Error: Case ID '{case_id}' not found in inbox/")
        return False

    with open(inbox_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"[*] Promoting case to official portfolio: {data.get('title')}")
    
    case_type = data.get("type", "repo")
    title = data.get("title", "")
    category = data.get("matched_user_domains", ["AI & Tech"])[0]
    
    init_script = os.path.join(base_dir, "tools", "init_case.py")
    cmd = [
        sys.executable, init_script,
        "--type", case_type,
        "--name", data.get("inbox_id"),
        "--title", title,
        "--category", category
    ]
    subprocess.run(cmd)

    # Move inbox file to archive
    arch_dir = os.path.join(base_dir, "inbox", "_promoted")
    os.makedirs(arch_dir, exist_ok=True)
    shutil.move(inbox_file, os.path.join(arch_dir, os.path.basename(inbox_file)))

    if rebuild_after:
        build_script = os.path.join(base_dir, "tools", "build_dashboard.py")
        subprocess.run([sys.executable, build_script])

    print(f"[+] Case '{case_id}' successfully promoted to investigations/!")
    return True

def promote_top_n(n):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    inbox_dir = os.path.join(base_dir, "inbox")
    
    items = []
    for f in sorted(os.listdir(inbox_dir)):
        if f.endswith(".json"):
            path = os.path.join(inbox_dir, f)
            try:
                with open(path, "r", encoding="utf-8") as fp:
                    items.append(json.load(fp))
            except Exception:
                pass

    if not items:
        print("[-] No items to promote.")
        return

    count = min(n, len(items))
    print(f"[*] Promoting top {count} items from inbox to official portfolio...")
    for it in items[:count]:
        promote_case(it.get("inbox_id"), rebuild_after=False)

    # Rebuild once
    build_script = os.path.join(base_dir, "tools", "build_dashboard.py")
    subprocess.run([sys.executable, build_script])
    print(f"[+] Batch promotion complete! {count} cases added to dashboard & docs/.")

def reject_case(case_id):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    inbox_file = os.path.join(base_dir, "inbox", f"{case_id}.json" if not case_id.endswith(".json") else case_id)
    
    if not os.path.exists(inbox_file):
        print(f"[!] Error: Case ID '{case_id}' not found in inbox/")
        return

    rej_dir = os.path.join(base_dir, "inbox", "_rejected")
    os.makedirs(rej_dir, exist_ok=True)
    shutil.move(inbox_file, os.path.join(rej_dir, os.path.basename(inbox_file)))
    print(f"[+] Case '{case_id}' rejected and moved to inbox/_rejected/ (Deduplication permanent block).")

def main():
    parser = argparse.ArgumentParser(description="Triage & Promotion Gate")
    parser.add_argument("--list", action="store_true", help="List all pending candidates in inbox/")
    parser.add_argument("--status", action="store_true", help="Show system harvest health check & logs")
    parser.add_argument("--promote", help="Promote candidate to official investigations/ portfolio")
    parser.add_argument("--promote-top", type=int, help="Batch promote top N candidates from inbox")
    parser.add_argument("--reject", help="Reject candidate and move to archive")

    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.promote_top:
        promote_top_n(args.promote_top)
    elif args.promote:
        promote_case(args.promote)
    elif args.reject:
        reject_case(args.reject)
    else:
        list_inbox()

if __name__ == "__main__":
    main()
