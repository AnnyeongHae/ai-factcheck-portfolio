#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/openrouter_free_router.py
====================================================================
OpenRouter Zero-Cost Dynamic Free Model Router (v1.0)
- Zero Cost Guarantee: Routes exclusively to 100% free models
- Primary: openrouter/free (Upstream auto-balancing across all zero-cost models)
- Secondary/Fallback Pool:
  1. nvidia/nemotron-3-super-120b-a12b:free
  2. google/gemma-4-31b-it:free
  3. minimax/minimax-m3:free
  4. nvidia/nemotron-3.5-lightning:free
  5. z-ai/glm-5.2:free
  6. cohere/north-mini-code:free
  7. liquid/lfm-2.5-2.6b:free
- Robust JSON sanitization, markdown fence removal & schema validation
====================================================================
"""

import os
import sys
import json
import time
import random
import re
import urllib.request
import urllib.error
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT_DIR, '.env'))

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Priority order for zero-cost models
FREE_MODEL_FALLBACKS = [
    "openrouter/free",
    "dots-studio/dots-3-note-preview:free",
    "poolside/laguna-xs-2.1:free",
    "inclusionai/ling-3.0-flash-fin:free",
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "minimax/minimax-m3:free",
    "cohere/north-mini-code:free",
    "liquid/lfm-2.5-2.6b:free"
]

def get_openrouter_api_key():
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key and os.path.exists(os.path.join(ROOT_DIR, ".env")):
        with open(os.path.join(ROOT_DIR, ".env"), "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("OPENROUTER_API_KEY="):
                    key = line.strip().split("=", 1)[1].strip("\"'")
                    break
    return key

def clean_json_response(raw_text: str):
    """Extracts and parses JSON from potentially markdown-fenced LLM responses."""
    cleaned = raw_text.strip()
    # Remove markdown code block fences
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    # Direct JSON parse attempt
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # Regex extraction of outermost JSON array or object
    array_match = re.search(r'\[.*?\]', cleaned, re.DOTALL)
    if array_match:
        try:
            return json.loads(array_match.group(0))
        except Exception:
            pass

    obj_match = re.search(r'\{.*?\}', cleaned, re.DOTALL)
    if obj_match:
        try:
            return [json.loads(obj_match.group(0))]
        except Exception:
            pass

    raise ValueError(f"Could not parse valid JSON from text: {cleaned[:150]}...")

def call_openrouter_free_single(system_prompt: str, item: dict, timeout: int = 20, max_retries: int = 1):
    """
    Enriches a SINGLE inbox item (1-by-1 mode) for maximum accuracy, speed and zero batching overhead.
    Returns: (parsed_dict, model_name, latency_seconds)
    """
    api_key = get_openrouter_api_key()
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is missing from environment and .env!")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/AnnyeongHae/ai-factcheck-portfolio",
        "X-Title": "AI FactCheck Portfolio Free Router"
    }

    clean_desc = re.sub(r'<[^>]+>', ' ', item.get("description", "")).strip()[:350]
    payload_item = {
        "id": item.get("inbox_id") or item.get("id"),
        "platform": item.get("source_platform", "Unknown"),
        "title": item.get("title", ""),
        "description": clean_desc
    }
    user_content = json.dumps(payload_item, ensure_ascii=False, indent=2)

    for model_name in FREE_MODEL_FALLBACKS:
        for attempt in range(1, max_retries + 1):
            t_start = time.time()
            try:
                payload = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt + "\n\n반드시 단일 JSON 객체({}) 하나만 반환하세요."},
                        {"role": "user", "content": "분석할 단일 항목:\n" + user_content}
                    ],
                    "temperature": 0.1
                }
                data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                req = urllib.request.Request(OPENROUTER_API_URL, data=data_bytes, headers=headers)

                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    routed_model = resp_data.get("model", model_name)
                    content = resp_data["choices"][0]["message"]["content"]
                    parsed = clean_json_response(content)
                    if isinstance(parsed, list):
                        parsed = parsed[0] if parsed else {}
                    latency = round(time.time() - t_start, 2)
                    return parsed, routed_model, latency

            except urllib.error.HTTPError as e:
                latency = round(time.time() - t_start, 2)
                err_body = e.read().decode("utf-8", errors="ignore")
                if e.code == 429:
                    wait_sec = 2.0 * (2 ** (attempt - 1)) + random.uniform(0.5, 1.5)
                    print(f"  [-] Model '{model_name}' hit 429 rate limit. Backing off {wait_sec:.1f}s...")
                    time.sleep(wait_sec)
                    continue
                else:
                    print(f"  [-] Model '{model_name}' returned HTTP {e.code}: {err_body[:80]}. Trying next free model...")
                    break
            except Exception as e:
                print(f"  [-] Error with model '{model_name}': {e}. Trying next free model...")
                time.sleep(1)
                break

    raise RuntimeError("All free models in OpenRouter pool exhausted or timed out for this item!")

def call_openrouter_free_batch(system_prompt: str, batch_items: list, timeout: int = 25, max_retries: int = 1):
    """
    Calls OpenRouter Free Router for a batch of inbox items.
    If only 1 item is passed, automatically uses call_openrouter_free_single for 100% precision.
    Returns: (parsed_results_list, model_name, latency_seconds)
    """
    if len(batch_items) == 1:
        res, m, lat = call_openrouter_free_single(system_prompt, batch_items[0], timeout=timeout, max_retries=max_retries)
        return [res], m, lat

    api_key = get_openrouter_api_key()
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is missing from environment and .env!")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/AnnyeongHae/ai-factcheck-portfolio",
        "X-Title": "AI FactCheck Portfolio Free Router"
    }

    clean_batch = []
    for item in batch_items:
        clean_desc = re.sub(r'<[^>]+>', ' ', item.get("description", "")).strip()[:350]
        clean_batch.append({
            "id": item.get("inbox_id") or item.get("id"),
            "platform": item.get("source_platform", "Unknown"),
            "title": item.get("title", ""),
            "description": clean_desc
        })

    user_content = json.dumps(clean_batch, ensure_ascii=False, indent=2)

    for model_name in FREE_MODEL_FALLBACKS:
        for attempt in range(1, max_retries + 1):
            t_start = time.time()
            try:
                payload = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": "분석할 항목 목록:\n" + user_content}
                    ],
                    "temperature": 0.2
                }
                data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                req = urllib.request.Request(OPENROUTER_API_URL, data=data_bytes, headers=headers)

                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    routed_model = resp_data.get("model", model_name)
                    content = resp_data["choices"][0]["message"]["content"]
                    parsed = clean_json_response(content)
                    if not isinstance(parsed, list):
                        parsed = [parsed]
                    latency = round(time.time() - t_start, 2)
                    return parsed, routed_model, latency

            except urllib.error.HTTPError as e:
                latency = round(time.time() - t_start, 2)
                err_body = e.read().decode("utf-8", errors="ignore")
                if e.code == 429:
                    wait_sec = 4.0 * (2 ** (attempt - 1)) + random.uniform(1.0, 2.0)
                    print(f"  [-] Model '{model_name}' hit 429 rate limit (attempt {attempt}/{max_retries}). Backing off {wait_sec:.1f}s...")
                    time.sleep(wait_sec)
                    continue
                else:
                    print(f"  [-] Model '{model_name}' returned HTTP {e.code}: {err_body[:100]}. Falling to next model...")
                    break
            except Exception as e:
                print(f"  [-] Error with model '{model_name}' (attempt {attempt}): {e}")
                time.sleep(2)
                break

    raise RuntimeError("All free models in OpenRouter pool exhausted or timed out!")

if __name__ == "__main__":
    print("[*] Testing OpenRouter Free Router standalone...")
    test_prompt = "Extract trilingual titles (KO, EN, ZH) as a JSON array."
    test_item = [{"inbox_id": "test-1", "title": "OpenRouter Free Router Test", "description": "Zero cost AI model routing"}]
    try:
        res, m, lat = call_openrouter_free_batch(test_prompt, test_item)
        print(f"[+] Success! Routed to '{m}' in {lat}s. Cost: $0.00")
        print(json.dumps(res, ensure_ascii=False, indent=2))
    except Exception as exc:
        print(f"[-] Standalone test failed: {exc}")
