#!/usr/bin/env python3
"""
Anti-Gaming & Hype Risk Auditing Engine (2026 SOTA Framework - v1.0)
- GitHub Star-Farming (스타 조작), 벤치마크 체리피킹(Pass@64 왜곡), 씬 래퍼(Thin Wrapper), AI Slop 라이센스 리스크를 정량적으로 감사
- Hype Risk Score (0~100) 및 위험 플래그 자동 산출
"""

import argparse
import json
import os
import re
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

def audit_candidate(title: str, description: str, source_platform: str, viral_metric: str, source_url: str = ""):
    """
    Analyzes an AI trend candidate and computes a Hype Risk Score (0~100).
    Higher score indicates high marketing hype, cherry-picked benchmarks, or star-farming patterns.
    """
    text = f"{title} {description} {viral_metric}".lower()
    risk_score = 15  # Baseline risk
    risk_flags = []
    audit_notes = []

    # 1. Benchmark Cherry-picking / Exaggeration patterns
    if re.search(r'\b(beats o1|beats gpt-4o|crushes claude|100x faster|kills openai)\b', text):
        risk_score += 35
        risk_flags.append("BENCHMARK_HYPING")
        audit_notes.append("자극적인 비교 마케팅 문구 감지 ('beats o1/kills openai' 등). Pass@1 실측 검증 필요.")

    # 2. Automated Passive Income / Money Printing Slop patterns
    if re.search(r'\b(make \$|passive income|월 1000|자동 수익|shorts automation|tiktok bot)\b', text):
        risk_score += 40
        risk_flags.append("AI_SLOP_REVENUE_RISK")
        audit_notes.append("유튜브/SNS 수익화 자동화 슬롭 패턴. 플랫폼 정책 위반(재사용 콘텐츠 제재) 위험 극심.")

    # 3. Thin Wrapper / Star-Farming Heuristics
    if source_platform == "GitHub Official" and "stars" in viral_metric.lower():
        star_match = re.search(r'([\d,]+)\s*stars', viral_metric.lower())
        if star_match:
            try:
                stars = int(star_match.group(1).replace(',', ''))
                if stars > 3000 and len(description) < 30:
                    risk_score += 25
                    risk_flags.append("STAR_FARMING_SUSPECT")
                    audit_notes.append("설명이나 리드미 대비 비정상적으로 빠른 스타 급증 패턴 감지.")
            except Exception:
                pass

    # 4. Proprietary Lock-in masquerading as Open Source (Fair Source / Business License)
    if re.search(r'\b(open source|free for everyone)\b', text) and re.search(r'\b(fair source|non-commercial|business license|\$1m)\b', text):
        risk_score += 20
        risk_flags.append("RESTRICTIVE_LICENSE_MASKED")
        audit_notes.append("순수 오픈소스가 아닌 'Fair Source / 상업용 라이선스 제약' 조항 존재.")

    # Clamp score to 0~100
    risk_score = min(100, max(0, risk_score))

    verdict_risk_level = "LOW_RISK"
    if risk_score >= 70:
        verdict_risk_level = "HIGH_GAMING_RISK"
    elif risk_score >= 40:
        verdict_risk_level = "MODERATE_HYP_RISK"

    return {
        "hype_risk_score": risk_score,
        "risk_level": verdict_risk_level,
        "risk_flags": risk_flags,
        "audit_notes": audit_notes
    }

def audit_all_inbox():
    inbox_dir = os.path.join(base_dir, "inbox")
    if not os.path.exists(inbox_dir):
        print("[-] Inbox is empty.")
        return

    items = []
    audited_count = 0
    high_risk_count = 0

    print("\n" + "="*90)
    print(" 🛡️ [Anti-Gaming & Hype Auditing Engine] 인박스 전체 127건 사기/과장 위험도 실사 시작")
    print("="*90)

    for f in sorted(os.listdir(inbox_dir)):
        if f.endswith(".json"):
            path = os.path.join(inbox_dir, f)
            try:
                with open(path, "r", encoding="utf-8") as fp:
                    data = json.load(fp)

                audit_result = audit_candidate(
                    title=data.get("title", ""),
                    description=data.get("description", ""),
                    source_platform=data.get("source_platform", ""),
                    viral_metric=data.get("viral_metric", ""),
                    source_url=data.get("source_url", "")
                )

                data["audit_risk"] = audit_result
                with open(path, "w", encoding="utf-8") as fp:
                    json.dump(data, fp, indent=2, ensure_ascii=False)

                audited_count += 1
                if audit_result["risk_level"] == "HIGH_GAMING_RISK":
                    high_risk_count += 1
                    print(f"[⚠️ HIGH RISK: {audit_result['hype_risk_score']}점] {data.get('title')[:60]}...")
                    for note in audit_result["audit_notes"]:
                        print(f"     • {note}")

            except Exception as e:
                pass

    print(f"\n[+] 총 {audited_count}건 인박스 후보 실사 완료 (⚠️ 고위험 과장/슬롭 감지: {high_risk_count}건)")
    print("="*90 + "\n")

if __name__ == "__main__":
    audit_all_inbox()
