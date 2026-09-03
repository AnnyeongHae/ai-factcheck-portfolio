#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/batch_manager.py
====================================================================
Google Gemini Batch API Manager with Token Accounting & DB Sync
- Submits InlinedRequest batches for un-enriched inbox items
- Tracks batch jobs with unique batch_uuid & Gemini Job ID
- Polls and harvests completed batch results (3-lang translation & metadata)
- Applies 50% Batch API cost discount and logs to token_usage_ledger.json
- Synchronizes batch status to Neon DB (ai_batch_jobs)
====================================================================
"""

import os
import sys
import json
import time
import uuid
from datetime import datetime
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT_DIR, '.env'))

BATCH_LOG_PATH = os.path.join(ROOT_DIR, 'logs', 'batch_jobs.json')
LEDGER_PATH = os.path.join(ROOT_DIR, 'logs', 'token_usage_ledger.json')

def get_db_connection():
    database_url = os.getenv("DATABASE_URL") or os.getenv("NEON_KEY")
    if not database_url:
        return None
    try:
        import psycopg2
        return psycopg2.connect(database_url)
    except Exception as e:
        print(f"[DB Warning]: Could not connect to Neon DB: {e}")
        return None

def load_batch_registry():
    if os.path.exists(BATCH_LOG_PATH):
        try:
            with open(BATCH_LOG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_batch_registry(registry):
    os.makedirs(os.path.dirname(BATCH_LOG_PATH), exist_ok=True)
    with open(BATCH_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)

def record_token_ledger(entry):
    ledger = []
    if os.path.exists(LEDGER_PATH):
        try:
            with open(LEDGER_PATH, 'r', encoding='utf-8') as f:
                ledger = json.load(f)
        except Exception:
            pass
    ledger.append(entry)
    os.makedirs(os.path.dirname(LEDGER_PATH), exist_ok=True)
    with open(LEDGER_PATH, 'w', encoding='utf-8') as f:
        json.dump(ledger, f, ensure_ascii=False, indent=2)

def submit_inbox_batch(items, model="models/gemini-3.6-flash"):
    """
    Submits a list of un-enriched inbox items to Gemini Batch API.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[-] GEMINI_API_KEY is not configured.")
        return None

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    
    batch_uuid = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    inlined_requests = []
    item_map = []

    for item in items:
        inbox_id = item.get("inbox_id")
        title = item.get("title", "")
        desc = item.get("description", "")
        platform = item.get("source_platform", "")
        url = item.get("source_url", "")

        prompt = f"""
Analyze the following technical trend item and provide a strict JSON enrichment response:
- ID: {inbox_id}
- Platform: {platform}
- Title: {title}
- Description: {desc}
- Source URL: {url}

Output Format (strict JSON, no markdown formatting):
{{
  "id": "{inbox_id}",
  "source_lang": "KO/EN/ZH/AUTO",
  "type_classification": "TECH",
  "model_family": "Architecture/Category",
  "category": "High level domain",
  "programming_lang": "Python/Rust/C++/General",
  "root_keywords": ["keyword1", "keyword2", "keyword3"],
  "recommended_tag": "🔥 강력 추천 (필독) 또는 📝 기술 참고",
  "worth_score": 4.5,
  "multilingual": {{
    "ko": {{
      "title": "한국어 번역 제목",
      "hook": "핵심 흥미 요소 및 기술적 가치 한 줄 요약",
      "key_takeaways": ["핵심 포인트 1", "핵심 포인트 2", "핵심 포인트 3"]
    }},
    "en": {{
      "title": "English translated title",
      "hook": "One line core engineering hook and technical takeaway",
      "key_takeaways": ["Key takeaway 1", "Key takeaway 2", "Key takeaway 3"]
    }},
    "zh": {{
      "title": "中文翻译标题",
      "hook": "核心工程价值与亮点一句话总结",
      "key_takeaways": ["核心要点 1", "核心要点 2", "核心要点 3"]
    }}
  }}
}}
"""
        req = types.InlinedRequest(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2
            )
        )
        inlined_requests.append(req)
        item_map.append({
            "inbox_id": inbox_id,
            "title": title
        })

    print(f"[*] Submitting Batch Job ({len(inlined_requests)} items) to {model}...")
    try:
        job = client.batches.create(
            model=model,
            src=inlined_requests
        )
        job_name = job.name
        state_str = str(job.state.name if hasattr(job.state, 'name') else job.state)
        print(f"[+] Batch Job successfully submitted!")
        print(f"  - Batch UUID:       {batch_uuid}")
        print(f"  - Gemini Job Name:  {job_name}")
        print(f"  - Initial State:    {state_str}")
        print(f"  - Total Items:      {len(items)}")

        # Save to local registry
        registry = load_batch_registry()
        entry = {
            "batch_uuid": batch_uuid,
            "gemini_job_name": job_name,
            "model": model,
            "item_count": len(items),
            "status": state_str,
            "submitted_at": datetime.now().isoformat(),
            "completed_at": None,
            "items": item_map
        }
        registry.append(entry)
        save_batch_registry(registry)

        # Sync to Neon DB
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO ai_batch_jobs (batch_uuid, gemini_job_name, item_count, inbox_ids, status, submitted_at)
                    VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (batch_uuid) DO NOTHING;
                """, (batch_uuid, job_name, len(items), json.dumps([x['inbox_id'] for x in item_map]), state_str))
                conn.commit()
                cur.close()
                conn.close()
                print("[+] Synced batch submission to Neon DB.")
            except Exception as dbe:
                print(f"[DB Sync Warning]: {dbe}")

        return batch_uuid

    except Exception as e:
        print(f"[-] Failed to submit batch: {e}")
        return None

def harvest_completed_batches():
    """
    Checks all pending batch jobs, harvests completed responses,
    updates inbox files and Neon DB, and logs 50% discounted token usage.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return 0

    from google import genai

    client = genai.Client(api_key=api_key)
    registry = load_batch_registry()
    updated_count = 0

    for job_record in registry:
        if job_record.get("status") in ["JOB_STATE_SUCCEEDED", "COMPLETED", "HARVESTED"]:
            continue

        job_name = job_record["gemini_job_name"]
        batch_uuid = job_record["batch_uuid"]
        print(f"[*] Checking status for Batch {batch_uuid} ({job_name})...")

        try:
            job = client.batches.get(name=job_name)
            current_state = job.state.name if hasattr(job.state, 'name') else str(job.state)
            job_record["status"] = current_state
            print(f"  - Current state: {current_state}")

            if current_state == "JOB_STATE_SUCCEEDED":
                print(f"[+] Batch {batch_uuid} finished! Harvesting responses...")
                
                # Check responses
                dest = job.dest
                responses = []
                if dest and hasattr(dest, 'inlined_responses') and dest.inlined_responses:
                    for inlined_resp in dest.inlined_responses:
                        if hasattr(inlined_resp, 'response'):
                            responses.append(inlined_resp.response)
                        else:
                            responses.append(inlined_resp)

                # Process responses and update inbox
                inbox_dir = os.path.join(ROOT_DIR, "inbox")
                total_prompt_tokens = 0
                total_candidate_tokens = 0

                for idx, resp in enumerate(responses):
                    if idx >= len(job_record["items"]):
                        break
                    target_meta = job_record["items"][idx]
                    inbox_id = target_meta["inbox_id"]

                    # Extract text content
                    text_content = ""
                    if hasattr(resp, "text") and resp.text:
                        text_content = resp.text
                    elif hasattr(resp, "candidates") and resp.candidates:
                        c = resp.candidates[0]
                        if hasattr(c, "content") and c.content and hasattr(c.content, "parts"):
                            text_content = "".join([p.text for p in c.content.parts if hasattr(p, "text")])

                    # Extract usage metadata
                    if hasattr(resp, "usage_metadata") and resp.usage_metadata:
                        u = resp.usage_metadata
                        total_prompt_tokens += getattr(u, "prompt_token_count", 0) or 0
                        total_candidate_tokens += getattr(u, "candidates_token_count", 0) or 0

                    if not text_content:
                        continue

                    try:
                        clean_text = text_content.strip()
                        if clean_text.startswith("```json"):
                            clean_text = clean_text[7:]
                        if clean_text.startswith("```"):
                            clean_text = clean_text[3:]
                        if clean_text.endswith("```"):
                            clean_text = clean_text[:-3]
                        parsed_ai = json.loads(clean_text.strip())

                        # Update inbox JSON file
                        inbox_file = os.path.join(inbox_dir, f"{inbox_id}.json")
                        if os.path.exists(inbox_file):
                            with open(inbox_file, "r", encoding="utf-8") as f:
                                item_data = json.load(f)

                            item_data["ai_enrichment"] = parsed_ai
                            item_data["multilingual"] = parsed_ai.get("multilingual", {})
                            item_data["source_lang"] = parsed_ai.get("source_lang", "EN")
                            item_data["programming_lang"] = parsed_ai.get("programming_lang", "General")
                            item_data["root_keywords"] = parsed_ai.get("root_keywords", [])
                            
                            ml = parsed_ai.get("multilingual", {})
                            if "ko" in ml and "title" in ml["ko"]:
                                item_data["title_ko"] = ml["ko"]["title"]
                                item_data["hook_ko"] = ml["ko"].get("hook", "")
                            if "en" in ml and "title" in ml["en"]:
                                item_data["title_en"] = ml["en"]["title"]
                                item_data["hook_en"] = ml["en"].get("hook", "")
                            if "zh" in ml and "title" in ml["zh"]:
                                item_data["title_zh"] = ml["zh"]["title"]
                                item_data["hook_zh"] = ml["zh"].get("hook", "")

                            item_data["enriched_by"] = "gemini-3.6-flash-batch-api"
                            item_data["enriched_at"] = datetime.now().isoformat()

                            with open(inbox_file, "w", encoding="utf-8") as f:
                                json.dump(item_data, f, ensure_ascii=False, indent=2)
                            updated_count += 1
                    except Exception as parse_e:
                        print(f"  [-] Failed to parse item {inbox_id}: {parse_e}")

                # Calculate 50% discounted Batch Cost
                # Normal Flash price: Input $0.15/1M, Output $0.60/1M
                # Batch 50% discount: Input $0.075/1M, Output $0.30/1M
                tot_tokens = total_prompt_tokens + total_candidate_tokens
                cost_usd = (total_prompt_tokens / 1_000_000) * 0.075 + (total_candidate_tokens / 1_000_000) * 0.30
                cost_krw = cost_usd * 1380.0

                job_record["completed_at"] = datetime.now().isoformat()
                job_record["status"] = "HARVESTED"
                job_record["total_prompt_tokens"] = total_prompt_tokens
                job_record["total_candidate_tokens"] = total_candidate_tokens
                job_record["total_tokens"] = tot_tokens
                job_record["cost_usd"] = cost_usd
                job_record["cost_krw"] = cost_krw

                # Log to token_usage_ledger.json
                record_token_ledger({
                    "timestamp": datetime.now().isoformat(),
                    "batch_uuid": batch_uuid,
                    "gemini_job_name": job_name,
                    "type": "BATCH_API_ENRICHMENT",
                    "model": job_record.get("model", "gemini-3.6-flash"),
                    "item_count": updated_count,
                    "prompt_tokens": total_prompt_tokens,
                    "candidate_tokens": total_candidate_tokens,
                    "total_tokens": tot_tokens,
                    "is_batch": True,
                    "discount_rate": "50% OFF",
                    "cost_usd": cost_usd,
                    "cost_krw": cost_krw
                })

                print(f"[+] Harvested {updated_count} items from Batch {batch_uuid}.")
                print(f"  - Total Tokens:  {tot_tokens:,} (Prompt: {total_prompt_tokens:,}, Output: {total_candidate_tokens:,})")
                print(f"  - Cost (50% OFF): ${cost_usd:.6f} (about {cost_krw:.2f} KRW)")

                # Update Neon DB
                conn = get_db_connection()
                if conn:
                    try:
                        cur = conn.cursor()
                        cur.execute("""
                            UPDATE ai_batch_jobs
                            SET status = 'HARVESTED',
                                completed_at = CURRENT_TIMESTAMP,
                                token_usage = %s,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE batch_uuid = %s;
                        """, (json.dumps({
                            "prompt_tokens": total_prompt_tokens,
                            "candidate_tokens": total_candidate_tokens,
                            "total_tokens": tot_tokens,
                            "cost_usd": cost_usd,
                            "cost_krw": cost_krw
                        }), batch_uuid))
                        conn.commit()
                        cur.close()
                        conn.close()
                    except Exception as dbe:
                        print(f"[DB Sync Warning]: {dbe}")

        except Exception as poll_e:
            print(f"[-] Error polling batch {batch_uuid}: {poll_e}")

    save_batch_registry(registry)
    return updated_count

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Gemini Batch API Engine")
    parser.add_argument("--status", action="store_true", help="Print status of all batch jobs")
    parser.add_argument("--harvest", action="store_true", help="Harvest completed batches")
    args = parser.parse_args()

    if args.harvest:
        count = harvest_completed_batches()
        print(f"[+] Done. Harvested {count} items.")
    else:
        registry = load_batch_registry()
        print(f"[*] Total Batch Jobs in registry: {len(registry)}")
        for b in registry:
            print(f" - [{b.get('status')}] UUID: {b.get('batch_uuid')} | Job: {b.get('gemini_job_name')} | Items: {b.get('item_count')}")
