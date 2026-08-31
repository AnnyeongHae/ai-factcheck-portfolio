#!/usr/bin/env python3
"""
Triage & Human-in-the-Loop Promotion Gate (2026 SOTA Framework)
inbox/에 보관된 트렌드 후보를 검토하고, 사용자가 승인(Promote)하기 전까지는 공식 포트폴리오로 승격하지 않습니다.

Usage:
    python tools/triage.py --list
    python tools/triage.py --promote 2026-08-31_repo_huggingface_trending_model
    python tools/triage.py --reject 2026-08-31_sns_spam_post
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

def list_inbox():
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

    print(f"\n=======================================================")
    print(f" 📥 승인 대기 중인 트렌드 후보 목록 (Total: {len(items)}건)")
    print(f" (사용자 검토 후 승인해야만 본격 포트폴리오로 승격됩니다)")
    print(f"=======================================================")
    for idx, it in enumerate(items, 1):
        print(f"\n[{idx}] Case ID: {it.get('inbox_id')}")
        print(f"    - 제목: {it.get('title')}")
        print(f"    - 출처: {it.get('source_platform')} ({it.get('source_url')})")
        print(f"    - 바이럴 지표: {it.get('viral_metric')}")
        print(f"    - 매칭된 사용자 도메인: {', '.join(it.get('matched_user_domains', []))}")
        print(f"    - 승인 명령어: python tools/triage.py --promote {it.get('inbox_id')}")
        print(f"    - 반려 명령어: python tools/triage.py --reject {it.get('inbox_id')}")
    print(f"=======================================================\n")

def promote_case(case_id):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    inbox_file = os.path.join(base_dir, "inbox", f"{case_id}.json" if not case_id.endswith(".json") else case_id)
    
    if not os.path.exists(inbox_file):
        print(f"[!] Error: Case ID '{case_id}' not found in inbox/")
        return

    with open(inbox_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"[*] Promoting case to official portfolio: {data.get('title')}")
    
    # Run init_case.py
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

    # Rebuild dashboard
    build_script = os.path.join(base_dir, "tools", "build_dashboard.py")
    subprocess.run([sys.executable, build_script])

    print(f"[+] Case '{case_id}' successfully promoted to investigations/ and updated on dashboard!")

def reject_case(case_id):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    inbox_file = os.path.join(base_dir, "inbox", f"{case_id}.json" if not case_id.endswith(".json") else case_id)
    
    if not os.path.exists(inbox_file):
        print(f"[!] Error: Case ID '{case_id}' not found in inbox/")
        return

    rej_dir = os.path.join(base_dir, "inbox", "_rejected")
    os.makedirs(rej_dir, exist_ok=True)
    shutil.move(inbox_file, os.path.join(rej_dir, os.path.basename(inbox_file)))
    print(f"[+] Case '{case_id}' rejected and moved to inbox/_rejected/. It will not be harvested again.")

def main():
    parser = argparse.ArgumentParser(description="Triage & Promotion Gate")
    parser.add_argument("--list", action="store_true", help="List all pending candidates in inbox/")
    parser.add_argument("--promote", help="Promote candidate to official investigations/ portfolio")
    parser.add_argument("--reject", help="Reject candidate and move to archive")

    args = parser.parse_args()

    if args.list:
        list_inbox()
    elif args.promote:
        promote_case(args.promote)
    elif args.reject:
        reject_case(args.reject)
    else:
        list_inbox()

if __name__ == "__main__":
    main()
