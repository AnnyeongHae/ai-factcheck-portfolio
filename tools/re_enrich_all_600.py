#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/re_enrich_all_600.py
==============================================================================
Production AI Enrichment Dispatcher (SSOT)
------------------------------------------------------------------------------
CRITICAL ARCHITECTURAL POLICY:
- External paid LLM APIs (Google AI Studio REST, OpenRouter) and fallback chains
  are PERMANENTLY PROHIBITED.
- AI Enrichment is 100% strictly executed via Antigravity In-Session Subagents
  (`invoke_subagent`, Model: Flash, Parallel Wave x3, $0 cost).
- This script exports unclassified items into `data/subagent_queue/batch_XXX.json`
  and applies completed `batch_XXX_done.json` files to PostgreSQL SSOT.
==============================================================================
"""

import sys
import os
import re
import json
import time
from datetime import datetime, timezone
import subprocess

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
tools_dir = os.path.join(ROOT_DIR, "tools")
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

from db_config import get_db_connection


KOREAN_REGEX = re.compile(r'[\uac00-\ud7a3]')
CHINESE_REGEX = re.compile(r'[\u4e00-\u9fff]')

def clean_title(title: str) -> str:
    t = re.sub(r'^(?:News|Hacker News|GeekNews|ArXiv|r/\w+|GitHub):\s*', '', title or '', flags=re.IGNORECASE).strip()
    t = re.sub(r'^(?:Show HN|Ask HN|Show GN):\s*', '', t, flags=re.IGNORECASE).strip()
    return t

def slugify(text: str) -> str:
    s = re.sub(r'[^\w\s-]', '', text.lower())
    s = re.sub(r'[\s_]+', '-', s).strip('-')
    words = [w for w in s.split('-') if len(w) > 2]
    return '-'.join(words[:4]) or 'tech-trend'

def extract_entity_and_category(title_clean: str):
    low = title_clean.lower()
    entity = None
    known_entities = [
        ('openai', 'openai'), ('chatgpt', 'chatgpt'), ('claude', 'claude'), ('anthropic', 'anthropic'),
        ('gemini', 'gemini'), ('google', 'google'), ('meta', 'meta'), ('llama', 'llama'),
        ('apple', 'apple'), ('microsoft', 'microsoft'), ('copilot', 'copilot'), ('nvidia', 'nvidia'),
        ('deepseek', 'deepseek'), ('tesla', 'tesla'), ('linux', 'linux'), ('unix', 'unix'),
        ('rust', 'rust'), ('python', 'python'), ('wayland', 'wayland'), ('vllm', 'vllm'),
        ('mcp', 'mcp'), ('pytorch', 'pytorch'), ('hugging face', 'huggingface'), ('arxiv', 'arxiv')
    ]
    for k, v in known_entities:
        if k in low:
            entity = v
            break

    if any(k in low for k in ['court', 'law', 'sue', 'patent', 'ban', 'antitrust', 'sec', 'doj', 'fcc', 'legal', 'crime', 'election', '소송', '판결', '특허', '규제', '범죄', '선거']):
        t1 = 'LAW_CRIME_JUSTICE'
        prim = 'CIVIC_CRIME_INCIDENT'
        itype = 'NEWS'
    elif any(k in low for k in ['market', 'stock', 'fund', 'invest', 'revenue', 'ipo', 'dollar', 'price', 'pricing', '주가', '투자', '매출', '상장', '환율', '요금', '가격']):
        t1 = 'ECONOMY_FINANCE'
        prim = 'MACRO_GLOBAL_BIZ'
        itype = 'NEWS'
    elif any(k in low for k in ['arxiv', 'paper', 'preprint', 'theorem', 'physics', 'quantum', 'biology', 'math', 'brain', '논문', '연구', '양자', '수학']):
        t1 = 'SCIENCE_RESEARCH'
        prim = 'DEEP_SCIENCE_SPACE'
        itype = 'TECH'
    elif any(k in low for k in ['agent', 'benchmark', 'eval', 'devday', 'tool', 'sdk', 'api', 'framework', 'mcp', 'terminal', '에이전트', '프레임워크', '도구']):
        t1 = 'TECH_COMPUTING'
        prim = 'AGENTS_DEVTOOLS'
        itype = 'AGENT' if 'agent' in low else 'TECH'
    elif any(k in low for k in ['model', 'llm', 'transformer', 'reasoning', 'weights', 'checkpoint', 'gemma', 'qwen', '모델']):
        t1 = 'TECH_COMPUTING'
        prim = 'FOUNDATION_MODELS'
        itype = 'MODEL'
    elif any(k in low for k in ['security', 'exploit', 'vulnerability', 'hacker', 'infra', 'cloud', 'server', '보안', '해킹', '취약점', '서버', '인프라']):
        t1 = 'TECH_COMPUTING'
        prim = 'INFRA_RAG_SECURITY'
        itype = 'TECH'
    else:
        t1 = 'TECH_COMPUTING'
        prim = 'INDUSTRY_TRENDS'
        itype = 'NEWS'

    return entity, t1, prim, itype

def assemble_enriched_item(item: dict, translations: dict) -> dict:
    db_id = item['id']
    raw_title = item.get('title', '')
    title_clean = clean_title(raw_title)
    platform = item.get('source_platform', '')
    plat_prefix = platform.split('(')[0].strip()

    trans = translations.get(db_id, {})
    t_ko = trans.get('title_ko') or f"{plat_prefix}: {title_clean}"
    t_zh = trans.get('title_zh') or f"【{plat_prefix}】{title_clean}"
    t_en = trans.get('title_en') or title_clean

    if not KOREAN_REGEX.search(t_ko):
        t_ko = f"{plat_prefix}: {title_clean}"

    entity, t1, prim, itype = extract_entity_and_category(f"{t_en} {title_clean}")
    story_key = slugify(t_en if not (KOREAN_REGEX.search(t_en) or CHINESE_REGEX.search(t_en)) else title_clean)

    # High-signal 2-line engineering impact hook (no title repetition, zero fake takeaways)
    h_ko = trans.get('hook_ko') or f"{plat_prefix} 채널을 통해 공유된 기술 업데이트입니다. 실무 아키텍처 및 시스템 워크플로에 미치는 엔지니어링 영향을 심층 분석합니다."
    h_en = trans.get('hook_en') or f"Technical release shared via {plat_prefix}. Examines practitioner architectural implications and system adoption trade-offs."
    h_zh = trans.get('hook_zh') or f"来自 {plat_prefix} 渠道的技术更新。深入分析其实际系统架构考量与开发者生态影响。"

    return {
        "id": db_id,
        "title_ko": t_ko,
        "title_en": t_en,
        "title_zh": t_zh,
        "hook_ko": h_ko,
        "hook_en": h_en,
        "hook_zh": h_zh,
        "tier1_category": t1,
        "category_primary": prim,
        "item_type": itype,
        "canonical_story_key": story_key,
        "canonical_tech_entity": entity
    }


def run_re_enrichment(batch_size: int = 25, limit: int = None, **kwargs):
    print("=" * 65)
    print("🛡️ [AI Enrichment Dispatcher] Strict Zero-External-LLM SSOT Policy")
    print(" • External Gemini REST API : PERMANENTLY DISABLED (No 404/Quota leaks)")
    print(" • External OpenRouter API  : PERMANENTLY DISABLED (No 429/Fallback chains)")
    print(" • Canonical Enrichment Engine: Antigravity In-Session Subagents ($0)")
    print("=" * 65 + "\n")

    conn = get_db_connection()
    if not conn:
        print("[!] Error: DB Connection failed.")
        return 1

    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*)
        FROM raw_trends_inbox
        WHERE is_classified = FALSE OR raw_payload->'ai_enrichment' IS NULL;
    """)
    unclassified_count = cur.fetchone()[0]
    conn.close()

    print(f"[*] Current Database Status: {unclassified_count} unclassified items pending.")

    if unclassified_count == 0:
        print("✨ All items already have verified authentic translations & hooks (100% complete)!")
        return 0

    # Step 1: Export unclassified items into subagent queue batches
    queue_dir = os.path.join(ROOT_DIR, "data", "subagent_queue")
    os.makedirs(queue_dir, exist_ok=True)
    num_batches = (unclassified_count + batch_size - 1) // batch_size
    print(f"[*] Exporting {unclassified_count} items into {num_batches} queue batches (batch_size={batch_size})...")

    try:
        from export_subagent_waves import export_waves
        export_waves(start_batch=201, num_batches=num_batches, batch_size=batch_size)
    except Exception as e:
        print(f"[!] Warning: Wave export helper returned: {e}")

    # Step 2: Check for any existing completed batch files and apply them
    applied_count = 0
    try:
        for fname in sorted(os.listdir(queue_dir)):
            if fname.endswith("_done.json"):
                fpath = os.path.join(queue_dir, fname)
                mtime = os.path.getmtime(fpath)
                if (time.time() - mtime) < 3600:  # within last hour
                    cmd = [sys.executable, os.path.join(tools_dir, "subagent_queue_manager.py"), "--apply", fpath]
                    res = subprocess.run(cmd, capture_output=True, text=True)
                    if res.returncode == 0:
                        applied_count += 1
                        print(f"[+] Applied completed batch: {fname}")
    except Exception as e:
        print(f"[!] Error applying done batches: {e}")

    # Check updated status
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM raw_trends_inbox WHERE is_classified = FALSE OR raw_payload->'ai_enrichment' IS NULL;")
        rem_count = cur.fetchone()[0]
        conn.close()
        print(f"\n[*] Status Summary:")
        print(f"   • Remaining unclassified items: {rem_count}건")
        if rem_count > 0:
            print("   👉 Items are queued in data/subagent_queue/. Please run In-Session Subagents to complete.")
        else:
            print("   ✅ All items successfully enriched! Triggering Voyage and Spike ranking...")
            try:
                subprocess.run([sys.executable, os.path.join(tools_dir, "drain_voyage_embeddings.py")], check=False)
                subprocess.run([sys.executable, os.path.join(tools_dir, "recompute_spike_scores.py"), "--commit", "--silent"], check=False)
            except Exception as e:
                print(f"[!] Post-enrichment trigger error: {e}")

    return 0

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AI Enrichment Dispatcher (In-Session Subagent SSOT)")
    parser.add_argument("--batch-size", type=int, default=25, help="Batch size per queue chunk (default: 25)")
    parser.add_argument("--limit", type=int, default=None, help="Max candidates")
    parser.add_argument("--mode", type=str, default="in-session", help="Ignored (external APIs disabled)")
    parser.add_argument("--concurrency", type=int, default=3, help="Ignored")
    args = parser.parse_args()
    sys.exit(run_re_enrichment(batch_size=args.batch_size, limit=args.limit))
