#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enterprise Trilingual AI Inbox Auto-Enricher (v8.0)
- Trilingual Parity: Full KO (한국어) / EN (English) / ZH (中文) Extraction for Every Item
- 3-Item Batching with Smart Multi-Model Fallback (gemini-flash-latest -> gemini-flash-lite-latest -> gemma-4-31b-it)
- The Hook ("사람이 읽고 싶은 1줄 훅") in 3 Languages
- 4-Tier Classification: MODEL | AGENT | TECH | NEWS
- Automatic 18-Dossier Knowledge Graph Linking
"""

import argparse
import glob
import json
import os
import random
import re
import sys
import time
from datetime import datetime
import urllib.request
import urllib.error
import yaml

# Force UTF-8 on Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

tools_dir = os.path.dirname(os.path.abspath(__file__))
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

import openrouter_free_router

MODEL_POOL = [
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
    "gemma-4-31b-it",
    "gemma-4-26b-a4b-it",
    "gemini-3.6-flash"
]

def get_gemini_api_key():
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key and os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("GEMINI_API_KEY="):
                    key = line.strip().split("=", 1)[1].strip("\"'")
                    break
    return key

def load_existing_dossiers():
    inv_dir = "investigations"
    dossiers = []
    if not os.path.exists(inv_dir):
        return dossiers

    for item in sorted(os.listdir(inv_dir)):
        mpath = os.path.join(inv_dir, item, "metadata.json")
        if os.path.exists(mpath):
            try:
                with open(mpath, "r", encoding="utf-8") as fp:
                    m = json.load(fp)
                    if "title" in m and m.get("title") != "[이슈명]":
                        dossiers.append({
                            "case_id": m.get("case_id"),
                            "title": m.get("title"),
                            "target_tech": m.get("target_technology", {}).get("name", ""),
                            "tags": [t.lower() for t in m.get("tags", [])],
                            "stack": [s.lower() for s in m.get("technology_stack", [])]
                        })
            except Exception:
                continue
    return dossiers

def match_dossier(dossiers, title, category, programming_lang, root_keywords):
    query_text = (title + " " + category + " " + programming_lang + " " + " ".join(root_keywords)).lower()
    best_match = None
    best_score = 0

    for d in dossiers:
        score = 0
        target = d["target_tech"].lower()
        if target and target in query_text:
            score += 5

        for tag in d["tags"]:
            if len(tag) > 2 and tag in query_text:
                score += 2

        for st in d["stack"]:
            if len(st) > 2 and st in query_text:
                score += 1

        if score > best_score and score >= 4:
            best_score = score
            best_match = {
                "case_id": d["case_id"],
                "title": d["title"],
                "target_tech": d["target_tech"]
            }
    return best_match

def load_prompt_config():
    """Loads external centralized prompt from configs/prompts/inbox_enrichment_prompt.yaml."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    yaml_path = os.path.join(base_dir, "configs", "prompts", "inbox_enrichment_prompt.yaml")
    
    if os.path.exists(yaml_path):
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
                persona = cfg.get("persona_and_role", "").strip()
                schema = cfg.get("output_json_schema", "").strip()
                temp = cfg.get("model_parameters", {}).get("temperature", 0.2)
                sys_prompt = f"{persona}\n\n{schema}"
                return sys_prompt, temp
        except Exception as e:
            print(f"[!] Warning: Failed to load YAML prompt: {e}")
            
    # Fallback
    default_prompt = (
        "당신은 글로벌 최고 수준의 다국어 AI 기술 아키텍트입니다.\n"
        "주어진 기술/뉴스 후보 목록을 분석하여 한국어(KO), 영어(EN), 중국어(ZH) 3개 국어로 번역 및 요약하여 JSON 배열로 응답하세요."
    )
    return default_prompt, 0.2

def call_gemini_trilingual_batch(api_key: str, batch_items: list) -> tuple:
    """Calls Gemini with batched items using centralized YAML prompt configuration."""
    system_prompt, temperature = load_prompt_config()

    clean_batch = []
    for item in batch_items:
        clean_desc = re.sub(r'<[^>]+>', ' ', item.get("description", "")).strip()[:350]
        clean_batch.append({
            "id": item["inbox_id"],
            "platform": item.get("source_platform", "Unknown"),
            "title": item.get("title", ""),
            "description": clean_desc
        })

    user_content = json.dumps(clean_batch, ensure_ascii=False, indent=2)

    payload = {
        "contents": [
            {"parts": [{"text": system_prompt + "\n\n분석할 항목 목록:\n" + user_content}]}
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": temperature
        }
    }

    # Model Fallback Loop
    for model_name in MODEL_POOL:
        is_gemma = "gemma" in model_name.lower()

        # 🌟 User Insight: Gemma models perform best with 1-by-1 single item calls to ensure 100% schema accuracy
        if is_gemma and len(clean_batch) > 1:
            print(f"  [*] Gemma model '{model_name}' detected: auto-splitting batch into single items for 100% precision...")
            gemma_results = []
            try:
                for s_item in clean_batch:
                    s_payload = {
                        "contents": [{"parts": [{"text": system_prompt + "\n\n분석할 단일 항목:\n" + json.dumps([s_item], ensure_ascii=False)}]}],
                        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2}
                    }
                    s_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                    s_req = urllib.request.Request(s_url, data=json.dumps(s_payload).encode("utf-8"), headers={"Content-Type": "application/json"})
                    with urllib.request.urlopen(s_req, timeout=30) as resp:
                        d = json.loads(resp.read().decode("utf-8"))
                        txt = d["candidates"][0]["content"]["parts"][0]["text"]
                        parsed_single = json.loads(txt)
                        if isinstance(parsed_single, list):
                            gemma_results.extend(parsed_single)
                        else:
                            gemma_results.append(parsed_single)
                    time.sleep(1)
                print(f"  [+] Responded by model '{model_name}' (1-by-1 single mode) successfully.")
                return gemma_results, model_name
            except Exception as e:
                print(f"  [-] Gemma single call failed: {e}. Falling back...")
                continue

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        # Smart Retry Loop with Exponential Backoff for 429 RPM Quotas
        for attempt in range(1, 4):
            try:
                with urllib.request.urlopen(req, timeout=40) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                    print(f"  [+] Responded by model '{model_name}' successfully.")
                    return json.loads(raw_text), model_name
            except urllib.error.HTTPError as e:
                err_msg = e.read().decode("utf-8", errors="ignore")
                if e.code == 429:
                    wait_sec = 6.0 * (2 ** (attempt - 1)) + random.uniform(1.0, 2.5)
                    print(f"  [-] Model '{model_name}' RPM limit hit (429, attempt {attempt}/3). Backing off {wait_sec:.1f}s for quota recovery...")
                    time.sleep(wait_sec)
                    continue
                elif e.code == 404:
                    break
                else:
                    print(f"  [-] HTTP Error {e.code} on '{model_name}': {err_msg[:80]}")
                    time.sleep(2)
                    break
            except Exception as e:
                print(f"  [-] Network Error on '{model_name}': {e}")
                time.sleep(2)
                break

    print("[!] All fallback models in pool exhausted for this batch!")
    return [], None

def run_enrichment(limit: int = 0, batch_size: int = 1, random_pick: bool = False, only_new: bool = False, cooldown: float = 1.0, provider: str = "auto"):
    openrouter_key = openrouter_free_router.get_openrouter_api_key()
    gemini_key = get_gemini_api_key()

    if provider == "auto":
        active_provider = "openrouter" if openrouter_key else ("gemini" if gemini_key else None)
    elif provider == "openrouter":
        active_provider = "openrouter"
    elif provider == "gemini":
        active_provider = "gemini"
    else:
        active_provider = None

    if not active_provider:
        print("[!] ERROR: No AI API key found! Please set OPENROUTER_API_KEY (for $0.00 free routing) or GEMINI_API_KEY.")
        sys.exit(1)

    print(f"[*] Active AI Engine: {active_provider.upper()} ({'100% Free Zero-Cost Router ($0.00)' if active_provider == 'openrouter' else 'Paid API Tier'})")

    dossiers = load_existing_dossiers()
    print(f"[*] Loaded {len(dossiers)} verified dossiers.")

    candidates = []
    last_manifest = os.path.join("logs", "last_harvest_new_items.json")
    
    # STEP 1: Check brand-new items manifest first for O(1) lightning incremental processing
    if os.path.exists(last_manifest):
        try:
            with open(last_manifest, "r", encoding="utf-8") as fp:
                m_data = json.load(fp)
                for fpath in m_data.get("files", []):
                    if os.path.exists(fpath):
                        with open(fpath, "r", encoding="utf-8") as ifp:
                            d = json.load(ifp)
                            if not d.get("ai_enrichment", {}).get("multilingual", {}).get("zh"):
                                candidates.append((fpath, d))
            if candidates:
                print(f"[*] [O(1) INCREMENTAL] Picked {len(candidates)} brand-new harvested items from manifest!")
        except Exception as e:
            print(f"[!] Note on manifest reading: {e}")

    # STEP 2: Fallback to scanning inbox if not strictly restricted to only_new
    if not candidates and not only_new:
        inbox_files = sorted(glob.glob("inbox/*.json"), key=lambda x: os.path.basename(x), reverse=True)
        print(f"[*] Fallback: Scanning {len(inbox_files)} total files in inbox (Newest First)...")
        for f in inbox_files:
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    d = json.load(fp)
                    has_tri = d.get("ai_enrichment", {}).get("multilingual", {}).get("zh")
                    if not has_tri:
                        candidates.append((f, d))
            except Exception:
                continue

    # Ensure candidates are ordered by newest harvested/created date
    candidates.sort(key=lambda pair: (pair[1].get("harvested_date", ""), pair[1].get("created_at", ""), pair[0]), reverse=True)

    print(f"[*] Total candidates pending AI enrichment: {len(candidates)}")
    if not candidates:
        print("[+] All items are already enriched or no new items found. Skipping AI step cleanly!")
        return

    # If limit <= 0, process ALL pending items sequentially without leaving any behind
    if limit <= 0 or limit >= len(candidates):
        selected = candidates
        print(f"[*] [FULL SEQUENTIAL MODE] Processing all {len(selected)} pending items cleanly without omission.")
    elif random_pick:
        selected = random.sample(candidates, limit)
        print(f"[*] Randomly selected {limit} items.")
    else:
        selected = candidates[:limit]
        print(f"[*] Sequential batch: Processing {len(selected)} of {len(candidates)} items.")

    total_to_process = len(selected)
    num_batches = (total_to_process + batch_size - 1) // batch_size
    success_count = 0
    session_start_time = datetime.now().astimezone()

    audit_session = {
        "session_id": f"session_{session_start_time.strftime('%Y%m%d_%H%M%S')}",
        "timestamp": session_start_time.isoformat(),
        "provider": active_provider,
        "estimated_cost": "$0.00" if active_provider == "openrouter" else "API Tier",
        "total_candidates": len(candidates),
        "requested_limit": limit,
        "processed_count": total_to_process,
        "success_count": 0,
        "models_used_summary": {},
        "batches": []
    }

    for b_idx in range(num_batches):
        batch = selected[b_idx * batch_size : (b_idx + 1) * batch_size]
        batch_raw = [item for _, item in batch]

        print(f"\n=======================================================")
        print(f"[*] Batch {b_idx+1}/{num_batches} ({len(batch)} items) via [{active_provider.upper()}]:")
        for _, it in batch:
            print(f"  - [{it.get('source_platform')}] {it.get('title')[:45]}...")

        b_start_time = time.time()
        results = []
        model_used = None

        if active_provider == "openrouter":
            system_prompt, _ = load_prompt_config()
            try:
                results, model_used, b_latency = openrouter_free_router.call_openrouter_free_batch(system_prompt, batch_raw)
            except Exception as e:
                print(f"  [-] OpenRouter Free Router batch failed: {e}")
                if gemini_key:
                    print("  [*] Attempting fallback to Gemini API...")
                    results, model_used = call_gemini_trilingual_batch(gemini_key, batch_raw)
                    b_latency = round(time.time() - b_start_time, 2)
                else:
                    results, model_used, b_latency = [], None, round(time.time() - b_start_time, 2)
        else:
            results, model_used = call_gemini_trilingual_batch(gemini_key, batch_raw)
            b_latency = round(time.time() - b_start_time, 2)

        res_map = {r["id"]: r for r in results if isinstance(r, dict) and "id" in r}

        batch_log = {
            "batch_index": b_idx + 1,
            "items_count": len(batch),
            "model_used": model_used or "FAILED",
            "latency_seconds": b_latency,
            "items_processed": []
        }

        if model_used:
            audit_session["models_used_summary"][model_used] = audit_session["models_used_summary"].get(model_used, 0) + len(results)

        for fpath, item in batch:
            iid = item.get("inbox_id")
            enrich_data = res_map.get(iid)
            if not enrich_data:
                idx = [it.get("inbox_id") for _, it in batch].index(iid)
                if idx < len(results):
                    enrich_data = results[idx]

            if enrich_data:
                enrich_time = datetime.now().astimezone().isoformat()
                enrich_data["enriched_by_model"] = model_used
                enrich_data["enriched_at"] = enrich_time

                multi = enrich_data.get("multilingual", {})
                ko_data = multi.get("ko", {})
                en_data = multi.get("en", {})
                zh_data = multi.get("zh", {})

                item["ai_enrichment"] = enrich_data
                item["multilingual"] = multi
                item["source_lang"] = enrich_data.get("source_lang", "EN")
                item["programming_lang"] = enrich_data.get("programming_lang", "General")
                item["root_keywords"] = enrich_data.get("root_keywords", [])
                
                # Trilingual titles
                item["title_ko"] = ko_data.get("title") or enrich_data.get("korean_title") or item.get("title_ko")
                item["title_en"] = en_data.get("title") or item.get("title_en") or item.get("title")
                item["title_zh"] = zh_data.get("title") or item.get("title_zh")

                # Trilingual hooks
                item["hook"] = ko_data.get("hook") or enrich_data.get("hook")
                item["hook_ko"] = ko_data.get("hook")
                item["hook_en"] = en_data.get("hook")
                item["hook_zh"] = zh_data.get("hook")

                # Trilingual descriptions
                item["description_ko"] = item["hook_ko"] or item.get("description_ko")
                item["description_en"] = item["hook_en"] or item.get("description_en") or item.get("description")
                item["description_zh"] = item["hook_zh"] or item.get("description_zh")

                # Routing & Automatic Model Family Tagging
                c_type = enrich_data.get("type_classification", "TECH")

                # Guardrail: Force MODEL classification if source is HF Models or title indicates model release
                is_explicit_model = (
                    item.get("source_platform") == "Hugging Face Models" or
                    "model:" in item.get("title", "").lower() or
                    "-gguf" in item.get("title", "").lower() or
                    "gguf" in item.get("title", "").lower() or
                    "lora" in item.get("title", "").lower()
                )
                if is_explicit_model and c_type != "NEWS":
                    c_type = "MODEL"

                if c_type == "MODEL":
                    fam = enrich_data.get("model_family")
                    if not fam or fam.lower() in ["none", "null", "", "standalone"]:
                        t_lower = (item.get("title", "") + " " + (item.get("title_en", "") or "")).lower()
                        if "qwen" in t_lower: fam = "Qwen-3.8 Family"
                        elif "deepseek" in t_lower: fam = "DeepSeek Family"
                        elif "minimax" in t_lower: fam = "MiniMax / Video"
                        elif "llama" in t_lower: fam = "Llama Family"
                        elif "gemma" in t_lower: fam = "Gemma Family"
                        elif "mistral" in t_lower: fam = "Mistral Family"
                        elif "flux" in t_lower: fam = "FLUX Family"
                        elif "audio" in t_lower or "tts" in t_lower or "voice" in t_lower: fam = "Audio / TTS"
                        else: fam = "Standalone / Novel"
                    item["model_family"] = fam
                    item["category_type"] = "MODEL"
                elif c_type == "NEWS":
                    item["category_type"] = "NEWS"
                else:
                    item["category_type"] = c_type

                # Match with existing 18 dossiers
                related = match_dossier(
                    dossiers,
                    item.get("title", ""),
                    enrich_data.get("category", ""),
                    enrich_data.get("programming_lang", ""),
                    enrich_data.get("root_keywords", [])
                )
                if related:
                    item["related_dossier"] = related
                    print(f"  [🔗 LINKED] {related['target_tech']} -> {related['case_id']}")

                with open(fpath, "w", encoding="utf-8") as fp:
                    json.dump(item, fp, indent=2, ensure_ascii=False)

                print(f"  [+] [{c_type} | {item['source_lang']}] {item['title_ko'][:30]}")
                print(f"      Model: {model_used} | Time: {enrich_time[11:19]}")
                print(f"      KO: {item['hook_ko'][:45]}...")
                print(f"      EN: {item['hook_en'][:45]}...")
                print(f"      ZH: {item['hook_zh'][:45]}...")
                success_count += 1

                batch_log["items_processed"].append({
                    "inbox_id": iid,
                    "title": item.get("title"),
                    "title_ko": item.get("title_ko"),
                    "classification": c_type,
                    "model_family": item.get("model_family"),
                    "enriched_at": enrich_time
                })

        audit_session["batches"].append(batch_log)

        if b_idx < num_batches - 1:
            print(f"[*] Batch {b_idx + 1}/{num_batches} complete. Sleeping {cooldown:.1f}s for RPM safety...")
            time.sleep(cooldown)

    audit_session["success_count"] = success_count

    # Persist session to logs/ai_enrichment_history.json
    os.makedirs("logs", exist_ok=True)
    history_file = "logs/ai_enrichment_history.json"
    history = []
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as fp:
                history = json.load(fp)
                if not isinstance(history, list):
                    history = []
        except Exception:
            history = []

    history.append(audit_session)
    history = history[-100:]  # Retain latest 100 audit sessions

    with open(history_file, "w", encoding="utf-8") as fp:
        json.dump(history, fp, indent=2, ensure_ascii=False)

    print(f"\n=======================================================")
    print(f"[📊 AI ENRICHMENT AUDIT REPORT]")
    print(f"  - Session ID     : {audit_session['session_id']}")
    print(f"  - Timestamp      : {audit_session['timestamp']}")
    print(f"  - Success Rate   : {success_count}/{total_to_process} items ({(success_count/max(1, total_to_process))*100:.1f}%)")
    print(f"  - Models Active  : {json.dumps(audit_session['models_used_summary'], ensure_ascii=False)}")
    print(f"  - Audit Trail    : Saved to '{history_file}'")
    print(f"=======================================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trilingual AI Auto-Enricher with Smart Zero-Cost OpenRouter Free Routing & Gemini Fallback")
    parser.add_argument("--limit", type=int, default=0, help="Number of items to enrich (default: 0 = ALL pending unenriched items)")
    parser.add_argument("--all", action="store_true", default=False, help="Process ALL pending unenriched items without limit")
    parser.add_argument("--batch-size", type=int, default=1, help="Item batch size (default: 1 = Single-item real-time streaming mode for 100% precision & speed)")
    parser.add_argument("--cooldown", type=float, default=1.0, help="Cooldown seconds between items (default: 1.0s)")
    parser.add_argument("--random", action="store_true", default=False, help="Pick randomly from inbox")
    parser.add_argument("--only-new", action="store_true", default=False, help="Process ONLY newly harvested items from manifest")
    parser.add_argument("--provider", choices=["auto", "openrouter", "gemini"], default="auto", help="AI Provider: openrouter (100% Free Router, $0.00) or gemini")
    
    # 🌟 Google Gemini Batch API Options (50% Cost Cut & Zero RPM Throttling)
    parser.add_argument("--submit-batch", action="store_true", default=False, help="Submit un-enriched items to Gemini Batch API")
    parser.add_argument("--harvest-batch", action="store_true", default=False, help="Harvest completed Batch API responses & update inbox")
    parser.add_argument("--status-batch", action="store_true", default=False, help="Print status of all Gemini Batch API jobs")
    args = parser.parse_args()

    if args.status_batch or args.harvest_batch or args.submit_batch:
        import sys
        import os
        tools_dir = os.path.dirname(os.path.abspath(__file__))
        if tools_dir not in sys.path:
            sys.path.insert(0, tools_dir)
        import batch_manager
        if args.status_batch:
            reg = batch_manager.load_batch_registry()
            print(f"[*] Total Batch Jobs in registry: {len(reg)}")
            for b in reg:
                print(f" - [{b.get('status')}] UUID: {b.get('batch_uuid')} | Job: {b.get('gemini_job_name')} | Items: {b.get('item_count')}")
            sys.exit(0)
        
        if args.harvest_batch:
            cnt = batch_manager.harvest_completed_batches()
            print(f"[+] Done. Harvested {cnt} items from completed batches.")
            sys.exit(0)

        if args.submit_batch:
            # Gather un-enriched items
            inbox_files = sorted(glob.glob("inbox/*.json"))
            unenriched = []
            for fp in inbox_files:
                if "_promoted" in fp or "_rejected" in fp:
                    continue
                try:
                    with open(fp, "r", encoding="utf-8") as f:
                        it = json.load(f)
                    if not it.get("ai_enrichment") or not it.get("multilingual"):
                        unenriched.append(it)
                except Exception:
                    continue
            
            target_limit = args.limit if args.limit > 0 else len(unenriched)
            targets = unenriched[:target_limit]
            print(f"[*] Found {len(unenriched)} un-enriched items. Submitting {len(targets)} to Gemini Batch API...")
            if not targets:
                print("[+] No un-enriched items to submit.")
                sys.exit(0)
            
            uuid_res = batch_manager.submit_inbox_batch(targets)
            if uuid_res:
                print(f"[+] Successfully launched Batch Job with UUID: {uuid_res}")
            sys.exit(0)

    effective_limit = 0 if args.all else args.limit
    run_enrichment(limit=effective_limit, batch_size=args.batch_size, random_pick=args.random, only_new=args.only_new, cooldown=args.cooldown, provider=args.provider)
