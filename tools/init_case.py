#!/usr/bin/env python3
"""
Fact-Check Case Initializer (2026 SOTA Framework - Portfolio Edition)
새로운 웹/SNS 최신 기술 팩트체크 및 포트폴리오 케이스 폴더를 자동 생성합니다.
"""

import argparse
import datetime
import json
import os
import shutil
import re

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '_', text)
    return text

def main():
    parser = argparse.ArgumentParser(description="2026 SOTA Fact-Check & Portfolio Case Initializer")
    parser.add_argument("--type", choices=["sns", "repo"], required=True, help="Case type: 'sns' or 'repo'")
    parser.add_argument("--name", required=True, help="Descriptive name of the case or technology")
    parser.add_argument("--title", default=None, help="Human-readable title for portfolio")
    parser.add_argument("--category", default="AI & Emerging Tech", help="Portfolio Category (e.g. 'RAG', 'GenAI Video', 'LLM')")
    parser.add_argument("--date", default=None, help="Date in YYYY-MM-DD format (default: today)")

    args = parser.parse_args()

    date_str = args.date if args.date else datetime.date.today().strftime("%Y-%m-%d")
    clean_name = slugify(args.name)

    folder_name = f"{date_str}_{args.type}_{clean_name}" if not clean_name.startswith(args.type) else f"{date_str}_{clean_name}"
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_dir = os.path.join(base_dir, "investigations", folder_name)
    template_dir = os.path.join(base_dir, "templates", f"template_{args.type}")

    if os.path.exists(target_dir):
        print(f"[!] Warning: Target directory already exists: {target_dir}")
        return

    print(f"[*] Creating new Fact-Check investigation: {folder_name}")
    shutil.copytree(template_dir, target_dir)

    title_str = args.title if args.title else args.name.replace("_", " ").title()

    # Replace placeholders in markdown files
    for root, _, files in os.walk(target_dir):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                content = content.replace("YYYY-MM-DD", date_str)
                content = content.replace("[이슈명]", title_str)
                content = content.replace("[저장소명]", title_str)

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

    # Create portfolio-ready metadata.json
    metadata = {
        "case_id": folder_name,
        "title": title_str,
        "category": args.category,
        "date_created": date_str,
        "type": args.type,
        "source_url": "",
        "source_platform": "X (Twitter) / GitHub" if args.type == "sns" else "GitHub",
        "verdict": "IN_PROGRESS",
        "confidence_score": 0.0,
        "status": "IN_PROGRESS",
        "lead_agent": "Antigravity SOTA Factchecker",
        "portfolio_story": {
            "discovery_channel": "어떤 SNS/채널에서 발견했는가?",
            "the_hook": "왜 눈길을 끌었는가? (매력 포인트)",
            "marketing_hype_anatomy": "어떤 식으로 홍보/과장했는가? (체리피킹, 비용 은폐 등)",
            "engineering_takeaways": "엔지니어로서 배운 점 & 기술적 실체",
            "future_applications": "추후 어떤 서비스/프로젝트에 활용 가능한가?",
            "hands_on_log": {
                "has_tested": False,
                "test_environment": "Local / Cloud Sandbox",
                "test_cases": "수행한 테스트 시나리오",
                "measured_results": "실측 결과 (VRAM, Latency, Throughput, Cost)",
                "real_world_use": "실제 프로젝트/서비스에 어떻게 적용했는가?"
            }
        },
        "files": os.listdir(target_dir)
    }

    with open(os.path.join(target_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"[+] Successfully initialized fact-check case at:\n    {target_dir}")
    
    # Auto rebuild dashboard
    try:
        from build_dashboard import build_dashboard
        build_dashboard()
    except Exception:
        pass

if __name__ == "__main__":
    main()
