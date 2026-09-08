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
import threading
import urllib.request
import socket

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# Set socket timeout for network requests
socket.setdefaulttimeout(18.0)

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if load_dotenv:
    load_dotenv(os.path.join(ROOT_DIR, '.env'))

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

class OpenRouterRateLimiter:
    """
    Thread-safe rate limiter strictly enforcing OpenRouter's free-tier 20 RPM ceiling.
    Defaults to 18 RPM (~3.33s interval) to provide a 10% safety buffer.
    """
    def __init__(self, target_rpm: int = 18):
        self.min_interval = 60.0 / target_rpm  # 3.33s
        self.last_call_time = 0.0
        self.lock = threading.Lock()

    def wait_for_slot(self):
        with self.lock:
            now = time.time()
            elapsed = now - self.last_call_time
            if elapsed < self.min_interval:
                sleep_time = self.min_interval - elapsed
                time.sleep(sleep_time)
            self.last_call_time = time.time()

# Global rate limiter instance shared across threads
RATE_LIMITER = OpenRouterRateLimiter(target_rpm=18)

# Priority clusters of verified active free models (max 3 fallbacks per OpenRouter API spec)
MODEL_CLUSTERS = [
    {
        "primary": "google/gemma-4-31b-it:free",
        "fallbacks": [
            "google/gemma-4-26b-a4b-it:free",
            "nvidia/nemotron-3-super-120b-a12b:free",
            "liquid/lfm-2.5-2.6b:free"
        ]
    },
    {
        "primary": "nvidia/nemotron-3.5-lightning:free",
        "fallbacks": [
            "dots-studio/dots-3-note-preview:free",
            "liquid/lfm-2.5-2.6b:free"
        ]
    }
]

# Backward compatibility alias
FREE_MODEL_FALLBACKS = [
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
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

DUMMY_PROMPT_PATTERNS = [
    "엔지니어가 이 글을 지금 당장 읽어야 하는",
    "1줄 결정적 훅",
    "Compelling 1-line hook for engineers",
    "直击工程师痛点的1句话亮点"
]

def validate_enriched_payload(payload):
    """Guardrail: Detects if a model blindly copied the prompt placeholder text."""
    if not payload:
        return payload
    items = payload if isinstance(payload, list) else [payload]
    for it in items:
        if not isinstance(it, dict):
            continue
        multi = it.get("multilingual", {})
        for lang_code in ["ko", "en", "zh"]:
            hook_text = str(multi.get(lang_code, {}).get("hook", ""))
            for pat in DUMMY_PROMPT_PATTERNS:
                if pat in hook_text:
                    raise ValueError(f"Model echoed prompt placeholder text in '{lang_code}.hook': '{hook_text}'")
    return payload

def clean_json_response(raw_text: str):
    """
    Sanitizes LLM outputs: strips reasoning blocks (<think>), code fences, and whitespace.
    """
    cleaned = raw_text.strip()
    # Strip <think>...</think> reasoning blocks common in reasoning models
    cleaned = re.sub(r'<think>.*?</think>', '', cleaned, flags=re.DOTALL).strip()
    cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*```$', '', cleaned).strip()

    try:
        data = json.loads(cleaned)
        return validate_enriched_payload(data)
    except json.JSONDecodeError:
        pass

    # Regex extraction of outermost JSON array
    array_match = re.search(r'\[.*?\]', cleaned, re.DOTALL)
    if array_match:
        try:
            data = json.loads(array_match.group(0))
            return validate_enriched_payload(data)
        except json.JSONDecodeError:
            pass

    # Regex extraction of outermost JSON object
    obj_match = re.search(r'\{.*?\}', cleaned, re.DOTALL)
    if obj_match:
        try:
            data = [json.loads(obj_match.group(0))]
            return validate_enriched_payload(data)
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse valid JSON from text: {cleaned[:120]}...")

def call_openrouter_free_batch(system_prompt: str, batch_items: list, timeout: int = 18, max_retries: int = 1):
    """
    Calls OpenRouter Free Router using server-side models fallback and 18 RPM pacer.
    Returns: (parsed_results_list, model_name, latency_seconds)
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

    for cluster_idx, cluster in enumerate(MODEL_CLUSTERS):
        primary_model = cluster["primary"]
        fallback_models = cluster["fallbacks"][:3]  # OpenRouter requires <= 3 fallback models

        for attempt in range(1, max_retries + 1):
            # Enforce strict 18 RPM spacing before sending request
            RATE_LIMITER.wait_for_slot()
            t_start = time.time()
            try:
                payload = {
                    "model": primary_model,
                    "models": fallback_models,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": "분석할 항목 목록:\n" + user_content}
                    ],
                    "temperature": 0.1
                }
                data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                req = urllib.request.Request(OPENROUTER_API_URL, data=data_bytes, headers=headers)

                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    routed_model = resp_data.get("model", primary_model)
                    choices = resp_data.get("choices")
                    if not choices or not isinstance(choices, list) or len(choices) == 0:
                        raise ValueError(f"No valid choices returned in response: {str(resp_data)[:100]}")
                    content = choices[0].get("message", {}).get("content", "")
                    parsed = clean_json_response(content)
                    if not isinstance(parsed, list):
                        parsed = [parsed]
                    latency = round(time.time() - t_start, 2)
                    return parsed, routed_model, latency

            except urllib.error.HTTPError as e:
                latency = round(time.time() - t_start, 2)
                err_body = e.read().decode("utf-8", errors="ignore")
                if e.code == 429:
                    wait_sec = 3.5 + random.uniform(0.5, 1.0)
                    print(f"  [-] OpenRouter RPM limit (429, cluster {cluster_idx+1}). Pacing {wait_sec:.1f}s...")
                    time.sleep(wait_sec)
                    continue
                else:
                    print(f"  [-] OpenRouter cluster {cluster_idx+1} HTTP {e.code}: {err_body[:80]}")
                    break
            except Exception as e:
                print(f"  [-] OpenRouter cluster {cluster_idx+1} error: {e}")
                time.sleep(0.5)
                break

    raise RuntimeError("All OpenRouter free model clusters exhausted or timed out!")

def call_openrouter_free_single(system_prompt: str, item: dict, timeout: int = 15, max_retries: int = 1):
    """Convenience wrapper for a single inbox item."""
    results, model, latency = call_openrouter_free_batch(system_prompt, [item], timeout=timeout, max_retries=max_retries)
    return (results[0] if results else {}), model, latency

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
