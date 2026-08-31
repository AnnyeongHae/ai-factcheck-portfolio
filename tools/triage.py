#!/usr/bin/env python3
"""
Triage & Promotion Gate (2026 SOTA Framework - v5.0)
- inbox/ 대량 트렌드 후보를 검토/일괄 승격/반려
- Neon Postgres DB 동기화 (--sync-queue)
- 모델 패밀리 일괄 팩트체크 승격 (--promote-family)
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

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def list_inbox(limit=20):
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
    print(f"==========================================================================================")
    for idx, it in enumerate(items[:limit], 1):
        print(f"\n[{idx:02d}] Case ID: {it.get('inbox_id')}")
        print(f"     - 제목: {it.get('title_ko') or it.get('title')}")
        print(f"     - 패밀리: {it.get('model_family', '독립 모델')}")
        print(f"     - 역할: {it.get('variant_role', 'Standard')}")
        print(f"     - 출처: {it.get('source_platform')} ({it.get('source_url')})")
        print(f"     👉 승인: python tools/triage.py --promote {it.get('inbox_id')}")
    print(f"==========================================================================================")
    print(f"💡 팁: 패밀리 일괄 승격 -> python tools/triage.py --promote-family 'Qwen-3.8-27B'\n")

def show_status():
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
    print(f"=======================================================\n")

def sync_queued_items(queue_ids=None):
    """
    웹 UI에서 '분석 큐에 담기'로 선택된 항목들을 로컬 JSON 및 Neon DB에 QUEUED 상태로 동기화
    """
    inbox_dir = os.path.join(base_dir, "inbox")
    updated_count = 0

    print("\n" + "="*80)
    print(" ⚡ [Neon DB Queue Bridge] 웹 UI 큐 등록 항목을 Neon DB에 실시간 반영합니다")
    print("="*80)

    for f in sorted(os.listdir(inbox_dir)):
        if f.endswith(".json"):
            path = os.path.join(inbox_dir, f)
            try:
                with open(path, "r", encoding="utf-8") as fp:
                    item = json.load(fp)

                inbox_id = item.get("inbox_id")
                if not queue_ids or inbox_id in queue_ids:
                    item["status"] = "QUEUED_FOR_INVESTIGATION"
                    with open(path, "w", encoding="utf-8") as fp:
                        json.dump(item, fp, indent=2, ensure_ascii=False)
                    updated_count += 1
            except Exception:
                pass

    # Neon DB Sync
    db_bridge = os.path.join(base_dir, "tools", "db_bridge.py")
    subprocess.run([sys.executable, db_bridge, "--sync-inbox"])
    
    print(f"[+] 총 {updated_count}건의 분석 대기열(Queue) 상태가 Neon Postgres DB에 완벽히 동기화되었습니다!")
    print("="*80 + "\n")

def promote_family(family_keyword):
    """
    패밀리에 속한 파생본들을 하나로 묶어 대표 1건을 승격
    """
    inbox_dir = os.path.join(base_dir, "inbox")
    matched_items = []

    for f in sorted(os.listdir(inbox_dir)):
        if f.endswith(".json"):
            path = os.path.join(inbox_dir, f)
            try:
                with open(path, "r", encoding="utf-8") as fp:
                    item = json.load(fp)
                fam = item.get("model_family", "")
                title = item.get("title", "")
                if family_keyword.lower() in fam.lower() or family_keyword.lower() in title.lower():
                    matched_items.append(item)
            except Exception:
                pass

    if not matched_items:
        print(f"[!] Warning: No items found matching family keyword '{family_keyword}'.")
        return

    print(f"\n[+] Found {len(matched_items)} variant models in family matching '{family_keyword}'!")
    # Select primary (prefer base/instruct or first item)
    primary = matched_items[0]
    for it in matched_items:
        if "base" in it.get("title", "").lower() or "official" in it.get("title", "").lower():
            primary = it
            break

    print(f"[*] Elevating Representative Primary Model: {primary.get('title')}")
    promote_case(primary.get("inbox_id"), rebuild_after=False)

    # Archive other variants into _promoted
    arch_dir = os.path.join(base_dir, "inbox", "_promoted")
    os.makedirs(arch_dir, exist_ok=True)
    for it in matched_items:
        if it.get("inbox_id") != primary.get("inbox_id"):
            src_file = os.path.join(inbox_dir, f"{it.get('inbox_id')}.json")
            if os.path.exists(src_file):
                shutil.move(src_file, os.path.join(arch_dir, os.path.basename(src_file)))

    # Rebuild
    build_script = os.path.join(base_dir, "tools", "build_dashboard.py")
    subprocess.run([sys.executable, build_script])
    print(f"[+] Entire Model Family '{family_keyword}' successfully promoted into 1 unified portfolio case!")

def promote_case(case_id, rebuild_after=True):
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

def main():
    parser = argparse.ArgumentParser(description="Triage & Promotion Gate v5.0")
    parser.add_argument("--list", action="store_true", help="List all pending candidates in inbox/")
    parser.add_argument("--status", action="store_true", help="Show system harvest health check & logs")
    parser.add_argument("--promote", help="Promote candidate to official investigations/ portfolio")
    parser.add_argument("--promote-family", help="Batch promote entire model family into 1 portfolio")
    parser.add_argument("--sync-queue", nargs="*", help="Sync queued candidates to Neon DB")
    parser.add_argument("--sync-queue-all", action="store_true", help="Sync all candidates to Neon DB")

    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.promote_family:
        promote_family(args.promote_family)
    elif args.promote:
        promote_case(args.promote)
    elif args.sync_queue is not None or args.sync_queue_all:
        sync_queued_items(args.sync_queue)
    else:
        list_inbox()

if __name__ == "__main__":
    main()
