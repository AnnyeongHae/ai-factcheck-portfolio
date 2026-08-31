#!/usr/bin/env python3
"""
Tech Lineage & Root Ancestry RAG Engine (2026 SOTA Framework - v2.0)
- 4세대 진화사 (Gen 0 ~ Gen 3)
- 근본 뿌리 기술 (Root Ancestry: BeautifulSoup, Scrapy, Readability.js 등)
- 왜 SOTA가 나와도 레거시 구기술을 계속 쓰는가? (Why Legacy Persists) 트레이드오프 분석
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

def query_tech_lineage(query: str):
    reg_path = os.path.join(base_dir, "configs", "tech_lineage_registry.json")
    if not os.path.exists(reg_path):
        print("[-] Tech lineage registry not found.")
        return None

    with open(reg_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    query_lower = query.lower().strip()
    matched_cluster = None

    for cluster in data.get("clusters", []):
        c_name = cluster.get("cluster_name", "").lower()
        c_id = cluster.get("cluster_id", "").lower()
        kws = cluster.get("keywords", [])
        kw_match = any(query_lower in kw.lower() or kw.lower() in query_lower for kw in kws)

        tool_match = False
        for t in cluster.get("tools", []):
            if query_lower in t.get("name", "").lower() or query_lower in t.get("tool_key", "").lower() or query_lower in t.get("tech_stack", "").lower() or query_lower in t.get("sota_summary", "").lower():
                tool_match = True
                break
        
        if query_lower in c_name or query_lower in c_id or kw_match or tool_match:
            matched_cluster = cluster
            break

    if not matched_cluster:
        print(f"[-] No direct lineage cluster found for '{query}'.")
        return None

    print("\n" + "="*90)
    print(f" 🌲 [기술 심층 계보 & Root Ancestry] 클러스터: {matched_cluster.get('cluster_name')}")
    print(f" 👑 패러다임 원조(Pioneer): {matched_cluster.get('pioneer_tool').upper()}")
    print("="*90)

    tools = matched_cluster.get("tools", [])
    print(f"\n총 {len(tools)}개 기술의 4세대 진화 및 트레이드오프 분석:")
    
    for t in tools:
        is_pioneer = "👑 [원조/Originator]" if t.get("is_original_pioneer") else "⚡ [SOTA 파생]"
        gen = t.get("lineage_generation", "Gen X")
        roots = t.get("root_ancestry", {})

        print(f"\n" + "-"*90)
        print(f"📌 {t.get('name')} ({t.get('tech_stack')}) | {gen} | {is_pioneer}")
        print(f"   • 최초 등장일: {t.get('first_created_at')} | 최근 업데이트: {t.get('last_updated_at')}")
        print(f"   • SOTA 영역: {t.get('sota_dimension')} - {t.get('sota_summary')}")
        
        if roots:
            print(f"   🏛️ [근본 뿌리 기술 (Root Ancestry)]:")
            if roots.get("core_parser_root"): print(f"      - 코어 파서 뿌리: {roots.get('core_parser_root')}")
            if roots.get("automation_root"):  print(f"      - 브라우저 자동화 뿌리: {roots.get('automation_root')}")
            if roots.get("markdown_root"):    print(f"      - 마크다운 직렬화 뿌리: {roots.get('markdown_root')}")
            if roots.get("direct_predecessor"): print(f"      - 직전 선조 기술: {roots.get('direct_predecessor')}")

        print(f"   🟢 주요 강점 (Pros): {t.get('pros')}")
        print(f"   🔴 치명적 한계 (Cons): {t.get('cons')}")
        print(f"   💡 [SOTA가 있어도 이 레거시를 고집하는 이유 (Why Legacy Persists)]:")
        print(f"      👉 {t.get('why_legacy_still_used')}")

    print("\n" + "="*90 + "\n")
    return matched_cluster

def main():
    parser = argparse.ArgumentParser(description="Query Local Tech Lineage & Root Ancestry")
    parser.add_argument("query", type=str, help="Technology name or domain keyword (e.g. 'crawler', 'praxist', 'scraping')")
    args = parser.parse_args()
    query_tech_lineage(args.query)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        query_tech_lineage("crawler")
