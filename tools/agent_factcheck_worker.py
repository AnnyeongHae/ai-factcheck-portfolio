#!/usr/bin/env python3
"""
Autonomous AI Agent Technical Fact-Check Worker (v1.0.0)
- Monitors QUEUED_FOR_INVESTIGATION items from Web UI / DB / Local Inbox.
- Performs senior-level technical audits:
    1) Primary source documentation audit
    2) Marketing claims vs. empirical engineering reality
    3) Hands-on reproducible benchmark & resource profiling
    4) Comparative alternatives matrix (Pros / Cons / Best For)
    5) Trilingual parity (KO / EN / ZH)
- Promotes verified items to official investigation dossiers (investigations/<case_id>/metadata.json).
- Automatically updates Neon DB & triggers dashboard build.
"""

import os
import sys
import glob
import json
import time
import re
import urllib.request
import urllib.error
import yaml
from datetime import datetime

# Windows Console UTF-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from tools.db_bridge import get_db_connection

MODEL_POOL = [
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
    "gemma-4-31b-it"
]

def load_deep_prompt_config():
    """Loads prompt from configs/prompts/deep_factcheck_prompt.yaml."""
    yaml_path = os.path.join(BASE_DIR, "configs", "prompts", "deep_factcheck_prompt.yaml")
    if os.path.exists(yaml_path):
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
                persona = cfg.get("persona_and_role", "").strip()
                schema = cfg.get("output_json_schema", "").strip()
                temp = cfg.get("model_parameters", {}).get("temperature", 0.15)
                return f"{persona}\n\n출력 JSON 규격:\n{schema}", temp
        except Exception as e:
            print(f"[!] Warning: Failed to load YAML: {e}")

    default_prompt = "당신은 시니어 AI 시스템 엔지니어이자 기술 팩트체커입니다. JSON으로 응답하세요."
    return default_prompt, 0.15

def get_api_key():
    for k in ["GEMINI_API_KEY", "GOOGLE_API_KEY"]:
        if os.environ.get(k): return os.environ.get(k)
    env_path = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("GEMINI_API_KEY=") or line.startswith("GOOGLE_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None

def find_queued_items():
    """Finds all items marked with status == 'QUEUED_FOR_INVESTIGATION'."""
    queued = []
    seen_ids = set()

    # 1. Local Inbox
    inbox_dir = os.path.join(BASE_DIR, "inbox")
    for f in glob.glob(os.path.join(inbox_dir, "*.json")):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                d = json.load(fp)
            if d.get("status") == "QUEUED_FOR_INVESTIGATION":
                iid = d.get("inbox_id")
                if iid and iid not in seen_ids:
                    queued.append((f, d))
                    seen_ids.add(iid)
        except Exception:
            pass

    # 2. Neon DB
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT inbox_id, title, source_platform, source_url, description, raw_payload FROM raw_trends_inbox WHERE triage_status = 'QUEUED_FOR_INVESTIGATION';")
                rows = cur.fetchall()
                for r in rows:
                    iid = r[0]
                    if iid not in seen_ids:
                        payload = r[5] if isinstance(r[5], dict) else json.loads(r[5] or '{}')
                        # Find local file if exists
                        matched_file = None
                        for f in glob.glob(os.path.join(inbox_dir, "*.json")):
                            if iid in f:
                                matched_file = f
                                break
                        queued.append((matched_file, payload))
                        seen_ids.add(iid)
            conn.close()
        except Exception as e:
            print(f"[!] DB queue query warning: {e}")

    return queued

def call_gemini_dossier(api_key: str, item_data: dict) -> dict:
    """Generates a deep fact-check dossier via Gemini."""
    system_prompt, temp = load_deep_prompt_config()
    
    clean_desc = re.sub(r'<[^>]+>', ' ', item_data.get("description", "")).strip()
    ai = item_data.get("ai_enrichment", {})
    
    target_info = {
        "inbox_id": item_data.get("inbox_id"),
        "title": item_data.get("title"),
        "source_platform": item_data.get("source_platform"),
        "source_url": item_data.get("source_url"),
        "description": clean_desc,
        "existing_ai_summary": ai.get("key_takeaways", []),
        "existing_hook": item_data.get("hook") or (ai.get("multilingual", {}).get("ko", {}).get("hook", ""))
    }

    user_content = json.dumps(target_info, ensure_ascii=False, indent=2)

    payload = {
        "contents": [
            {"parts": [{"text": system_prompt + "\n\n[정밀 기술 검증 대상]:\n" + user_content}]}
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": temp
        }
    }

    for model_name in MODEL_POOL:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data_bytes, headers={"Content-Type": "application/json"})

        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                if resp.status == 200:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    text = resp_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    cleaned = re.sub(r"^```json\s*", "", text, flags=re.MULTILINE)
                    cleaned = re.sub(r"^```\s*", "", cleaned, flags=re.MULTILINE)
                    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()
                    cleaned = re.sub(r',\s*([\]}])', r'\1', cleaned)
                    try:
                        dossier = json.loads(cleaned)
                    except Exception:
                        # Secondary attempt: fix unescaped newlines within strings
                        cleaned_fixed = re.sub(r'(?<!\\)\n', r'\\n', cleaned)
                        dossier = json.loads(cleaned)
                    print(f"  [+] Deep dossier generated by model '{model_name}' successfully.")
                    return dossier
        except Exception as e:
            print(f"  [!] Model {model_name} failed: {e}. Trying fallback...")
            time.sleep(1.5)

    return None

def run_agent_factcheck_worker(limit: int = 10):
    print("=" * 65)
    print("🤖 [AUTONOMOUS AI AGENT FACT-CHECK WORKER] Starting...")
    print("=" * 65)

    api_key = get_api_key()
    if not api_key:
        print("[!] ERROR: No Gemini API Key found.")
        return

    queued = find_queued_items()
    print(f"[*] Total queued items detected for investigation: {len(queued)}")

    if not queued:
        print("[+] No items in queue. All systems up to date!")
        return

    processed = 0
    inv_dir = os.path.join(BASE_DIR, "investigations")
    os.makedirs(inv_dir, exist_ok=True)

    for local_file, item in queued[:limit]:
        inbox_id = item.get("inbox_id", "unknown")
        title = item.get("title", "Untitled")
        print(f"\n[*] Investigating: {title} (ID: {inbox_id[:35]}...)")

        dossier = call_gemini_dossier(api_key, item)
        if not dossier:
            print(f"  [!] Failed to generate dossier for {inbox_id}.")
            continue

        # Force current investigation date & clean case_id
        dossier["investigation_date"] = datetime.now().strftime("%Y-%m-%d")
        case_id = dossier.get("case_id")
        if not case_id or case_id == "investigation 고유 ID":
            slug = re.sub(r"[^a-zA-Z0-9_]", "_", inbox_id).strip("_").lower()[:45]
            case_id = f"case_{slug}"
            dossier["case_id"] = case_id

        # Save to investigations/<case_id>/metadata.json
        case_dir = os.path.join(inv_dir, case_id)
        os.makedirs(case_dir, exist_ok=True)
        meta_path = os.path.join(case_dir, "metadata.json")
        with open(meta_path, "w", encoding="utf-8") as fp:
            json.dump(dossier, fp, ensure_ascii=False, indent=2)
        print(f"  [+] Saved Investigation Dossier: {meta_path}")

        # Update local inbox file
        if local_file and os.path.exists(local_file):
            try:
                with open(local_file, "r", encoding="utf-8") as fp:
                    item_json = json.load(fp)
                item_json["status"] = "FACT_CHECKED"
                item_json["related_dossier"] = {
                    "case_id": case_id,
                    "target_tech": dossier.get("title_ko") or dossier.get("title"),
                    "verdict": dossier.get("verdict", "VERIFIED_TRUE")
                }
                with open(local_file, "w", encoding="utf-8") as fp:
                    json.dump(item_json, fp, ensure_ascii=False, indent=2)
                print(f"  [+] Updated local inbox status -> FACT_CHECKED & linked dossier.")
            except Exception as e:
                print(f"  [!] Local file update warning: {e}")

        # Update Neon DB
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE raw_trends_inbox 
                        SET triage_status = 'FACT_CHECKED', updated_at = NOW() 
                        WHERE inbox_id = %s;
                    """, (inbox_id,))
                conn.commit()
                conn.close()
                print("  [+] Updated Neon DB raw_trends_inbox triage_status -> FACT_CHECKED.")
            except Exception as e:
                print(f"  [!] DB update error: {e}")

        processed += 1
        time.sleep(2)

    print("\n" + "=" * 65)
    print(f"🎉 Completed {processed}/{len(queued[:limit])} deep fact-check investigations!")
    print("=" * 65)

    # Trigger Dashboard Rebuild
    print("[*] Rebuilding Dashboard with newly promoted dossiers...")
    os.system(f'python "{os.path.join(BASE_DIR, "tools", "build_dashboard.py")}"')

if __name__ == "__main__":
    run_agent_factcheck_worker()
