#!/usr/bin/env python3
"""
Tech Lineage & SOTA RAG Engine (2026 SOTA Framework - v1.0)
내부 기술 계보 레지스트리(tech_lineage_registry.json)에서 신규 기술과 연관된 원조(Pioneer) 및 SOTA 대체재를 0.1초 만에 인출합니다.
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

    # Search in clusters and tools
    for cluster in data.get("clusters", []):
        c_name = cluster.get("cluster_name", "").lower()
        c_id = cluster.get("cluster_id", "").lower()
        
        # Check keywords
        kws = cluster.get("keywords", [])
        kw_match = any(query_lower in kw.lower() or kw.lower() in query_lower for kw in kws)

        # Check tool matches
        tool_match = False
        for t in cluster.get("tools", []):
            if query_lower in t.get("name", "").lower() or query_lower in t.get("tool_key", "").lower() or query_lower in t.get("tech_stack", "").lower() or query_lower in t.get("sota_summary", "").lower():
                tool_match = True
                break
        
        if query_lower in c_name or query_lower in c_id or kw_match or tool_match:
            matched_cluster = cluster
            break

    if not matched_cluster:
        print(f"[-] No direct lineage cluster found for '{query}'. (Trigger broad web exploration)")
        return None

    print("\n" + "="*85)
    print(f" 🧬 [Tech Lineage & SOTA RAG] 매칭된 기술 클러스터: {matched_cluster.get('cluster_name')}")
    print(f" 👑 원조(Pioneer): {matched_cluster.get('pioneer_tool').upper()}")
    print("="*85)

    tools = matched_cluster.get("tools", [])
    print(f"\n총 {len(tools)}개의 누적된 기술 계보 분석:")
    for t in tools:
        is_pioneer = "👑 [원조/Originator]" if t.get("is_original_pioneer") else "⚡ [SOTA 파생]"
        print(f"\n• {t.get('name')} ({t.get('tech_stack')}) - {is_pioneer}")
        print(f"   - 최초 등장일: {t.get('first_created_at')} | 최근 업데이트: {t.get('last_updated_at')}")
        print(f"   - SOTA 영역: {t.get('sota_dimension')} ({t.get('sota_summary')})")
        print(f"   - 주요 강점: {t.get('pros')}")
        print(f"   - 주요 단점: {t.get('cons')}")

    print("\n" + "="*85 + "\n")
    return matched_cluster

def main():
    parser = argparse.ArgumentParser(description="Query Local Tech Lineage Registry")
    parser.add_argument("query", type=str, help="Technology name or domain keyword (e.g. 'crawler', 'praxist', 'video')")
    args = parser.parse_args()
    query_tech_lineage(args.query)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        query_tech_lineage("crawler")
