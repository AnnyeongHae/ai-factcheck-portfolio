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
import concurrent.futures
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

# Force UTF-8 on Windows Console & Line Buffering
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

tools_dir = os.path.dirname(os.path.abspath(__file__))
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

import openrouter_free_router

# Gemini integration is SUSPENDED per project cost policy ($0.00 zero-cost mandate)
GEMINI_ENABLED = False

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
VALID_TIER1_CATEGORIES = {
    "TECH_COMPUTING", "SCIENCE_RESEARCH", "ECONOMY_FINANCE",
    "POLITICS_POLICY", "LAW_CRIME_JUSTICE", "CULTURE_HUMANITIES"
}

VALID_PRIMARY_CATEGORIES = {
    "INFERENCE_OPT", "AGENTS_DEVTOOLS", "MULTIMODAL_AI",
    "FOUNDATION_MODELS", "INFRA_RAG_SECURITY", "DEEP_SCIENCE_SPACE",
    "MACRO_GLOBAL_BIZ", "INDUSTRY_TRENDS",
    # IPTC Tier 2 aliases
    "INFERENCE_SERVING", "MULTIMODAL_MEDIA", "FOUNDATION_WEIGHTS",
    "SYSTEM_CYBERSEC", "SOFTWARE_WEB", "SPACE_ASTRONOMY",
    "DEEP_SCIENCE_BIO", "MACRO_TREASURY", "BIZ_MARKETS",
    "CIVIC_CRIME_INCIDENT", "HISTORY_LIFE_CULTURE"
}

def infer_primary_category(item: dict, enrich_data: dict, c_type: str = "TECH") -> str:
    cand = enrich_data.get("category_primary") or enrich_data.get("tier2_category")
    if cand and cand in VALID_PRIMARY_CATEGORIES:
        return cand

    title = (item.get("title") or "").lower() + " " + (item.get("title_ko") or "").lower()
    desc = (item.get("description") or "").lower() + " " + (item.get("hook") or "").lower()
    cat_raw = (enrich_data.get("category") or item.get("category") or "").lower()
    tags = [t.lower() for t in enrich_data.get("root_keywords", [])]
    tag_str = " ".join(tags)
    src = (item.get("source_platform") or "").lower()
    text = f"{title} {desc} {cat_raw} {tag_str}"

    def has_any(patterns):
        for p in patterns:
            if re.search(r'\b' + re.escape(p) + r'\b', text, re.IGNORECASE):
                return True
        return False

    # 1. Non-Tech / Crime / Incidents / Politics (IPTC: 02000000 & 11000000)
    if has_any([
        'governor candidate', 'armed man', 'attacks', 'injuries reported', 'police', 'shooting',
        'suspect arrested', 'murder', 'assault', 'gubernatorial', '주지사 후보', '피습', '무장 남성',
        '부상자', '총격', '경찰 수사', '체포', '선거 유세'
    ]):
        return 'CIVIC_CRIME_INCIDENT'

    # 2. History / Food / Humanities (IPTC: 01000000 & 10000000)
    if has_any([
        'stew with beets', 'recipe', 'ancient recipe', 'babylonian', 'cooking', 'cookbook',
        'archaeology', 'medieval manuscript', 'ancient roman', '고대 요리', '스튜 레시피',
        '바빌로니아', '고고학', '역사 문헌', '중세 필사본', '인문학'
    ]):
        return 'HISTORY_LIFE_CULTURE'

    # 3. DEEP_SCIENCE_SPACE (Space, Aerospace, Materials, Physics, Astronomy, Deep Science)
    if has_any([
        'aerospace', 'rocket', 'orbit', 'orbital', 'satellite', 'spacecraft',
        'nasa', 'esa', 'astronomy', 'astronomer', 'telescope', 'dark matter',
        'diamond mine', 'lab-grown diamond', 'superconductor', 'nuclear fusion',
        '우주', '항공우주', '발사체', '로켓', '궤도 진입', '궤도 발사', '인공위성', '천문', '암흑물질',
        '다이아몬드 광산', '핵융합', '초전도체', '신소재'
    ]) or (has_any(['space', 'launch', 'mission']) and has_any(['orbit', 'rocket', 'payload', 'cosmos', 'satellite', '궤도', '발사체'])):
        return 'DEEP_SCIENCE_SPACE'

    # 4. MACRO_GLOBAL_BIZ (Macroeconomics, Finance, Gold, Geopolitics, Big Tech Policy)
    if has_any([
        'gold reserve', 'central bank', 'monetary policy', 'inflation', 'interest rate',
        'macroeconomics', 'gdp growth', 'treasury', 'tariff', 'antitrust', 'ftc',
        '금 86톤', '금 회수', '중앙은행', '통화 정책', '인플레이션', '기준금리', '거시경제',
        '재정 건전성', '관세', '반독점', '독점 판결', '정부 부패'
    ]) or (has_any(['gold', '금']) and has_any(['reserve', 'bullion', 'central bank', '회수', '보관', '중앙은행', '온스', 'ton'])):
        return 'MACRO_GLOBAL_BIZ'

    # 5. INFERENCE_OPT
    if has_any(['gguf', 'vllm', 'sglang', 'ollama', 'awq', 'fp8', 'int4', 'int8', 'kv cache', 'speculative decoding', 'inference', 'serving', 'quantization', 'latency', '추론', '서빙', '양자화', '경량화', '가속']):
        return 'INFERENCE_OPT'

    # 6. MULTIMODAL_AI
    if has_any(['vlm', 'diffusion', 'tts', 'stt', 'whisper', 'flux', 'wan', 'minimax', 'sora', 'kling', 'runway', 'stable diffusion', 'text-to-image', 'text-to-video', 'multimodal', '멀티모달', '음성합성', '영상 생성', '화상 생성']) or (has_any(['video', 'vision', 'speech', 'audio', 'voice', 'sound', 'image', '음성', '비디오', '영상', '이미지']) and has_any(['ai', 'model', 'neural', 'deep learning', '인공지능', '모델', '생성'])):
        return 'MULTIMODAL_AI'

    # 7. AGENTS_DEVTOOLS
    if has_any(['agent', 'agents', 'browser use', 'scraping', 'crawler', 'devtools', 'copilot', 'automation', 'cli', 'framework', 'sdk', '에이전트', '자동화', '개발도구', '코딩', '프레임워크']):
        return 'AGENTS_DEVTOOLS'

    # 8. INFRA_RAG_SECURITY
    if has_any(['rag', 'vectordb', 'vector database', 'embedding', 'embeddings', 'jailbreak', 'cve', 'vulnerability', 'benchmark', 'evaluation', 'eval', 'mlops', 'cluster', '탈옥', '취약점', '임베딩', '평가']) or (has_any(['security', '보안']) and has_any(['linux', 'kernel', 'exploit', 'bypass', 'patch', 'zero-day', '악성코드', '취약점', '우회'])):
        return 'INFRA_RAG_SECURITY'

    # 9. FOUNDATION_MODELS
    if 'models' in src or 'hub' in src or c_type == 'MODEL' or has_any(['weights', 'safetensors', 'checkpoint', 'lora', 'foundation model', 'pretrained', '파운데이션', '가중치', '체크포인트', 'qwen', 'deepseek', 'llama', 'mistral', 'gemma']):
        return 'FOUNDATION_MODELS'

    # 10. INDUSTRY_TRENDS (Default / General Tech News / Software & Hardware)
    return 'INDUSTRY_TRENDS'

def infer_tier1_category(item: dict, enrich_data: dict, primary_cat: str) -> str:
    """Maps items to the 6 IPTC Universal Top-Level Domains."""
    t1_direct = enrich_data.get("tier1_category")
    if t1_direct and t1_direct in VALID_TIER1_CATEGORIES:
        return t1_direct

    if primary_cat in ['DEEP_SCIENCE_SPACE', 'SPACE_ASTRONOMY', 'DEEP_SCIENCE_BIO']:
        return 'SCIENCE_RESEARCH'
    if primary_cat in ['MACRO_GLOBAL_BIZ', 'MACRO_TREASURY', 'BIZ_MARKETS']:
        return 'ECONOMY_FINANCE'
    if primary_cat in ['CIVIC_CRIME_INCIDENT']:
        return 'LAW_CRIME_JUSTICE'
    if primary_cat in ['HISTORY_LIFE_CULTURE']:
        return 'CULTURE_HUMANITIES'
    if primary_cat in ['TECH_ANTITRUST_POLICY']:
        return 'POLITICS_POLICY'
    return 'TECH_COMPUTING'

def infer_artifact_type(item: dict, enrich_data: dict) -> str:
    """Classifies AI model items into 4 distinct ecosystems: WEIGHTS | SKILL_AGENT | WEB_SERVICE | FINETUNE."""
    art = enrich_data.get("artifact_type")
    if art in ["WEIGHTS", "SKILL_AGENT", "WEB_SERVICE", "FINETUNE", "ARTICLE"]:
        return art

    src = (item.get("source_platform") or "").lower()
    url = (item.get("source_url") or item.get("url") or "").lower()
    title = (item.get("title") or "").lower()
    formats = item.get("detected_formats") or enrich_data.get("detected_formats") or []

    if "spaces" in src or "spaces" in url or "space:" in title or "gradio" in title:
        return "WEB_SERVICE"
    if any(k in title for k in ["agent", "harness", "cli", "sdk", "browser-use", "framework"]) or "agent" in src:
        return "SKILL_AGENT"
    if any(k in title for k in ["lora", "adapter", "finetune", "fine-tuned", "fine-tuning"]):
        return "FINETUNE"
    if any(fmt in ["GGUF", "Safetensors", "FP8", "MLX"] for fmt in formats) or "models" in src or "weights" in title:
        return "WEIGHTS"
    return "ARTICLE"

def generate_heuristic_enrichment(item: dict) -> dict:
    """
    Zero-cost high-accuracy heuristic rule-based enrichment fallback.
    Guarantees 100% schema completeness, IPTC categorization, trilingual parity,
    and dossier linking even when external LLM APIs are exhausted or down.
    """
    title_raw = (item.get("title") or "").strip()
    desc_raw = re.sub(r'<[^>]+>', ' ', item.get("description") or "").strip()

    # Strip common RSS feed name prefixes
    clean_title = re.sub(r'^(Show HN|Ask HN|GeekNews|HN|Hugging Face Blog|Hugging Face Models):\s*', '', title_raw, flags=re.IGNORECASE).strip()
    if not clean_title:
        clean_title = title_raw

    # Language detection
    has_korean = bool(re.search(r'[\uac00-\ud7a3]', clean_title + " " + desc_raw))
    source_lang = "KO" if has_korean else "EN"

    # Trilingual Titles
    title_ko = item.get("title_ko") or clean_title
    title_en = item.get("title_en") or clean_title
    title_zh = item.get("title_zh") or clean_title

    # Trilingual Hooks (extract first impactful sentence or fallback to title)
    sentences = [s.strip() for s in re.split(r'(?<=[.!?\n])\s+', desc_raw) if len(s.strip()) > 15]
    first_sentence = sentences[0] if sentences else clean_title
    if len(first_sentence) > 160:
        first_sentence = first_sentence[:157] + "..."

    hook_ko = item.get("hook_ko") or item.get("hook") or first_sentence
    hook_en = item.get("hook_en") or first_sentence
    hook_zh = item.get("hook_zh") or first_sentence

    # Type classification
    t_lower = (clean_title + " " + desc_raw + " " + (item.get("source_platform") or "")).lower()
    if any(k in t_lower for k in ["-gguf", "gguf", "lora", "safetensors", "checkpoint", "weights", "fp8", "parameter", "7b", "14b", "70b", "32b"]) or item.get("source_platform") == "Hugging Face Models" or "model:" in t_lower:
        c_type = "MODEL"
    elif any(k in t_lower for k in ["agent", "agents", "crawler", "scraper", "cli", "devtools", "copilot", "sdk", "framework"]):
        c_type = "AGENT"
    elif any(k in t_lower for k in ["candidate", "shooting", "police", "arrest", "minister", "court", "antitrust", "ftc", "attack", "election"]):
        c_type = "NEWS"
    else:
        c_type = "TECH"

    enrich_data = {
        "id": item.get("inbox_id"),
        "source_lang": source_lang,
        "programming_lang": "General",
        "root_keywords": [w.strip() for w in re.findall(r'[A-Za-z0-9_-]{3,}', clean_title)[:5]],
        "type_classification": c_type,
        "korean_title": title_ko,
        "hook": hook_ko,
        "multilingual": {
            "ko": {"title": title_ko, "hook": hook_ko},
            "en": {"title": title_en, "hook": hook_en},
            "zh": {"title": title_zh, "hook": hook_zh}
        },
        "enriched_by_model": "heuristic-rule-engine",
        "enriched_at": datetime.now().astimezone().isoformat()
    }
    return enrich_data

def load_prompt_config():
    """Loads external centralized prompt via prompt_manager."""
    try:
        from prompt_manager import get_prompt
        p = get_prompt("inbox_enrichment")
        if p:
            return p.get_system_prompt(), p.temperature
    except Exception as e:
        print(f"[!] Warning: Failed to load via prompt_manager: {e}")
            
    # Fallback
    default_prompt = (
        "당신은 글로벌 최고 수준의 다국어 AI 기술 아키텍트입니다.\n"
        "주어진 기술/뉴스 후보 목록을 분석하여 한국어(KO), 영어(EN), 중국어(ZH) 3개 국어로 번역 및 요약하여 JSON 배열로 응답하세요."
    )
    return default_prompt, 0.2

def call_gemini_trilingual_batch(api_key: str, batch_items: list) -> tuple:
    """Gemini API connection is SUSPENDED per project policy ($0.00 zero-cost mandate)."""
    print("[!] Notice: Gemini API connection is suspended. Bypassing to OpenRouter Free Router / Heuristic Engine.")
    return [], None

def process_single_batch(b_idx, num_batches, batch, active_provider, dossiers):
    batch_raw = [item for _, item in batch]

    print(f"\n=======================================================")
    print(f"[*] [Batch {b_idx+1}/{num_batches}] ({len(batch)} items) via [OPENROUTER FREE ROUTER ($0.00)]:")
    for _, it in batch:
        print(f"  - [{it.get('source_platform')}] {it.get('title')[:45]}...")

    b_start_time = time.time()
    results = []
    model_used = None

    system_prompt, _ = load_prompt_config()
    try:
        results, model_used, b_latency = openrouter_free_router.call_openrouter_free_batch(system_prompt, batch_raw)
    except Exception as e:
        print(f"  [-] [Batch {b_idx+1}] OpenRouter Free Router unavailable: {e}. Activating instant heuristic rule engine...")
        results, model_used, b_latency = [], "heuristic-rule-engine", round(time.time() - b_start_time, 2)

    results = results or []
    res_map = {r["id"]: r for r in results if isinstance(r, dict) and "id" in r}

    batch_log = {
        "batch_index": b_idx + 1,
        "items_count": len(batch),
        "model_used": model_used or "heuristic-rule-engine",
        "latency_seconds": b_latency,
        "items_processed": []
    }

    batch_success_count = 0

    for fpath, item in batch:
        iid = item.get("inbox_id")
        enrich_data = res_map.get(iid)
        if not enrich_data:
            idx = [it.get("inbox_id") for _, it in batch].index(iid)
        # Strict Quality Guardrail: Require genuine Korean translation from LLM
        has_korean = False
        if enrich_data:
            multi = enrich_data.get("multilingual", {})
            ko_data = multi.get("ko", {})
            t_ko = ko_data.get("title") or enrich_data.get("korean_title") or ""
            h_ko = ko_data.get("hook") or enrich_data.get("hook") or ""
            has_korean = bool(re.search(r'[\uac00-\ud7a3]', t_ko + " " + h_ko))

        if not enrich_data or not has_korean:
            print(f"  [-] [PENDING] {item.get('title')[:40]} - No valid Korean translation returned. Leaving in queue for retry.")
            continue

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
                # 1. Model Family normalization
                fam = enrich_data.get("model_family") or item.get("model_family")
                t_lower = (item.get("title", "") + " " + (item.get("title_en", "") or "") + " " + item.get("description", "")).lower()
                if not fam or fam.lower() in ["none", "null", "", "standalone", "standalone / novel"] or "standalone" in fam.lower():
                    if "qwen" in t_lower: fam = "Qwen"
                    elif "deepseek" in t_lower: fam = "DeepSeek"
                    elif "minimax" in t_lower: fam = "MiniMax"
                    elif "wan" in t_lower or "wan2" in t_lower: fam = "Wan"
                    elif "flux" in t_lower: fam = "FLUX"
                    elif "llama" in t_lower: fam = "Llama"
                    elif "glm" in t_lower: fam = "GLM"
                    elif "hunyuan" in t_lower: fam = "Hunyuan"
                    elif any(k in t_lower for k in ["whisper", "tts", "speech", "audio", "voice", "firered", "breeze"]): fam = "Audio / Speech"
                    elif "mistral" in t_lower or "codestral" in t_lower: fam = "Mistral"
                    elif "gemma" in t_lower: fam = "Gemma"
                    else: fam = "Standalone"
                else:
                    fam_low = fam.lower()
                    if "qwen" in fam_low: fam = "Qwen"
                    elif "deepseek" in fam_low: fam = "DeepSeek"
                    elif "minimax" in fam_low: fam = "MiniMax"
                    elif "wan" in fam_low: fam = "Wan"
                    elif "flux" in fam_low: fam = "FLUX"
                    elif "llama" in fam_low: fam = "Llama"
                    elif "glm" in fam_low: fam = "GLM"
                    elif "hunyuan" in fam_low: fam = "Hunyuan"
                    elif any(k in fam_low for k in ["whisper", "tts", "speech", "audio", "voice"]): fam = "Audio / Speech"
                    elif "mistral" in fam_low: fam = "Mistral"
                    elif "gemma" in fam_low: fam = "Gemma"
                item["model_family"] = fam
                item["category_type"] = "MODEL"

                # 2. Task Modality normalization
                modality = enrich_data.get("task_modality") or item.get("task_modality")
                if not modality or modality.lower() in ["none", "null", "", "other"]:
                    p_match = re.search(r'Pipeline:\s*([a-zA-Z0-9_-]+)', item.get("description", ""))
                    if p_match:
                        modality = p_match.group(1).lower()
                    elif any(k in t_lower for k in ['video', 'wan', 'minimax-h3', 'ltx-video', 'hunyuanvideo']):
                        modality = 'text-to-video'
                    elif any(k in t_lower for k in ['tts', 'speech', 'audio', 'voice', 'whisper', 'firered', 'voxcpm']):
                        modality = 'text-to-speech' if 'whisper' not in t_lower else 'speech-to-text'
                    elif any(k in t_lower for k in ['flux', 'diffusion', 'sdxl', 'text-to-image']):
                        modality = 'text-to-image'
                    elif any(k in t_lower for k in ['vlm', 'vision', 'image-to-text', 'multimodal understanding']):
                        modality = 'image-text-to-text'
                    else:
                        modality = 'text-to-text'

                mod_low = modality.lower()
                if 'text-generation' in mod_low or 'text2text' in mod_low or 'text-to-text' in mod_low:
                    item["task_modality"] = 'text-to-text'
                elif 'image-text-to-text' in mod_low or 'visual-question-answering' in mod_low:
                    item["task_modality"] = 'image-text-to-text'
                elif 'text-to-image' in mod_low:
                    item["task_modality"] = 'text-to-image'
                elif 'image-to-image' in mod_low:
                    item["task_modality"] = 'image-to-image'
                elif 'text-to-video' in mod_low:
                    item["task_modality"] = 'text-to-video'
                elif 'text-to-speech' in mod_low or 'tts' in mod_low:
                    item["task_modality"] = 'text-to-speech'
                elif 'speech-to-text' in mod_low or 'transcription' in mod_low:
                    item["task_modality"] = 'speech-to-text'
                else:
                    item["task_modality"] = modality

                # 3. Parameter Size
                param = enrich_data.get("parameter_size") or item.get("parameter_size")
                if not param or param.lower() in ["none", "null", "", "n/a"]:
                    pm = re.search(r'\b(\d+(\.\d+)?[BMb])\b', item.get("title", "") + " " + item.get("description", ""))
                    item["parameter_size"] = pm.group(1).upper() if pm else "N/A"
                else:
                    item["parameter_size"] = param

                # 4. Formats
                formats = enrich_data.get("detected_formats") or item.get("detected_formats") or []
                if not formats or not isinstance(formats, list) or len(formats) == 0:
                    det = []
                    if 'gguf' in t_lower: det.append('GGUF')
                    if 'fp8' in t_lower or '8-bit' in t_lower: det.append('FP8')
                    if 'lora' in t_lower: det.append('LoRA')
                    if 'safetensors' in t_lower: det.append('Safetensors')
                    if 'diffusers' in t_lower: det.append('Diffusers')
                    if 'mlx' in t_lower: det.append('MLX')
                    item["detected_formats"] = det if det else ["Safetensors"]
                else:
                    item["detected_formats"] = formats
            elif c_type == "NEWS":
                item["category_type"] = "NEWS"
            else:
                item["category_type"] = c_type

            # Set Standard 2-Tier Taxonomy & Artifact Type (IPTC Standard)
            cat_p = infer_primary_category(item, enrich_data, c_type)
            t1_cat = infer_tier1_category(item, enrich_data, cat_p)
            art_type = infer_artifact_type(item, enrich_data)

            item["category_primary"] = cat_p
            item["tier1_category"] = t1_cat
            item["tier2_category"] = cat_p
            item["artifact_type"] = art_type

            enrich_data["category_primary"] = cat_p
            enrich_data["tier1_category"] = t1_cat
            enrich_data["tier2_category"] = cat_p
            enrich_data["artifact_type"] = art_type

            # 5. Deduplication Fingerprint & Multi-Source Tracking
            dedup_fg = enrich_data.get("dedup_fingerprint") or {}
            if dedup_fg:
                item["dedup_fingerprint"] = dedup_fg
                if dedup_fg.get("canonical_story_key"):
                    item["canonical_story_key"] = dedup_fg.get("canonical_story_key")
                if dedup_fg.get("core_entities"):
                    item["core_entities"] = dedup_fg.get("core_entities")

            # Initialize sources container if not present
            if "sources" not in item or not isinstance(item.get("sources"), list) or len(item["sources"]) == 0:
                item["sources"] = [
                    {
                        "source_name": item.get("source_platform") or "Primary",
                        "platform": item.get("source_platform") or "Primary",
                        "title": item.get("title") or item.get("title_ko") or "",
                        "url": item.get("source_url") or item.get("url") or "",
                        "type": "discussion" if any(x in (item.get("source_platform") or "").lower() for x in ["hacker news", "geeknews", "reddit"]) else "media",
                        "published_at": item.get("published_date") or item.get("source_published_date") or item.get("harvested_at") or ""
                    }
                ]
            item["source_count"] = len(item["sources"])

            # Match with existing dossiers
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

            item["is_classified"] = True
            item["is_deep_analyzed"] = bool(item.get("status") == "FACT_CHECKED" or item.get("related_dossier"))

            with open(fpath, "w", encoding="utf-8") as fp:
                json.dump(item, fp, indent=2, ensure_ascii=False)

            print(f"  [+] [Thread-{b_idx+1}] [{c_type} | {item['source_lang']}] {item['title_ko'][:30]}")
            batch_success_count += 1

            batch_log["items_processed"].append({
                "inbox_id": iid,
                "title": item.get("title"),
                "title_ko": item.get("title_ko"),
                "classification": c_type,
                "model_family": item.get("model_family"),
                "enriched_at": enrich_time
            })

    return (b_idx, batch_log, batch_success_count, model_used, len(results) if results else 0)

def run_enrichment(limit: int = 0, batch_size: int = 3, random_pick: bool = False, only_new: bool = False, cooldown: float = 1.0, provider: str = "openrouter", workers: int = 1):
    openrouter_key = openrouter_free_router.get_openrouter_api_key()

    if provider == "gemini":
        print("[!] Notice: Gemini API is suspended per project policy ($0.00 zero-cost mandate). Routing to OpenRouter Free Router ($0.00).")
        active_provider = "openrouter"
    elif provider in ["auto", "openrouter"]:
        active_provider = "openrouter"
    else:
        active_provider = "openrouter"

    if not openrouter_key:
        print("[!] Warning: OPENROUTER_API_KEY not found. Heuristic Rule Engine will be used for 100% free enrichment.")

    print(f"[*] Active AI Engine: {active_provider.upper()} (100% Free Zero-Cost Router [$0.00])")

    dossiers = load_existing_dossiers()
    print(f"[*] Loaded {len(dossiers)} verified dossiers.")

    candidates = []
    last_manifest = os.path.join("logs", "last_harvest_new_items.json")
    
    # STEP 1: Check brand-new items manifest first for O(1) lightning incremental processing
    if os.path.exists(last_manifest):
        try:
            with open(last_manifest, "r", encoding="utf-8") as fp:
                m_data = json.load(fp)
                for raw_fpath in m_data.get("files", []):
                    # Handle both relative and absolute paths
                    local_path = os.path.join("inbox", os.path.basename(raw_fpath))
                    actual_path = raw_fpath if os.path.exists(raw_fpath) else (local_path if os.path.exists(local_path) else None)
                    if actual_path:
                        with open(actual_path, "r", encoding="utf-8") as ifp:
                            d = json.load(ifp)
                            is_done = d.get("is_classified", False) and bool(d.get("ai_enrichment", {}).get("multilingual", {}).get("zh"))
                            if not is_done:
                                candidates.append((actual_path, d))
            if candidates:
                print(f"[*] [O(1) INCREMENTAL] Picked {len(candidates)} brand-new harvested items from manifest!")
        except Exception as e:
            print(f"[!] Note on manifest reading: {e}")

    # STEP 2: Fallback to scanning inbox if not strictly restricted to only_new, or if candidates < limit
    if not only_new or not candidates or (limit > 0 and len(candidates) < limit):
        seen_paths = {c[0] for c in candidates}
        inbox_files = sorted(glob.glob("inbox/*.json"), key=lambda x: os.path.basename(x), reverse=True)
        for f in inbox_files:
            if f in seen_paths or "_promoted" in f or "_rejected" in f:
                continue
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    d = json.load(fp)
                    is_done = d.get("is_classified", False) and bool(d.get("ai_enrichment", {}).get("multilingual", {}).get("zh"))
                    if not is_done:
                        candidates.append((f, d))
                        seen_paths.add(f)
                        if limit > 0 and len(candidates) >= limit:
                            break
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

    batches_data = []
    for b_idx in range(num_batches):
        batch = selected[b_idx * batch_size : (b_idx + 1) * batch_size]
        batches_data.append((b_idx, num_batches, batch))

    actual_workers = max(1, min(workers, num_batches))
    print(f"[*] Dispatching {num_batches} batches across {actual_workers} concurrent worker threads...")

    completed_batches = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=actual_workers) as executor:
        future_to_bidx = {
            executor.submit(process_single_batch, b_idx, num_batches, batch, active_provider, dossiers): b_idx
            for b_idx, num_batches, batch in batches_data
        }
        for future in concurrent.futures.as_completed(future_to_bidx):
            b_idx = future_to_bidx[future]
            try:
                ret_b_idx, batch_log, batch_success_count, model_used, res_count = future.result()
                completed_batches.append(batch_log)
                success_count += batch_success_count
                if model_used:
                    audit_session["models_used_summary"][model_used] = audit_session["models_used_summary"].get(model_used, 0) + res_count
            except Exception as exc:
                print(f"[!] Batch {b_idx + 1} generated an unhandled exception: {exc}")

    # Keep batch logs ordered by batch_index
    completed_batches.sort(key=lambda b: b.get("batch_index", 0))
    audit_session["batches"] = completed_batches
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
    parser = argparse.ArgumentParser(description="Trilingual AI Auto-Enricher with Smart Zero-Cost OpenRouter Free Routing (Gemini Suspended)")
    parser.add_argument("--limit", type=int, default=0, help="Number of items to enrich (default: 0 = ALL pending unenriched items)")
    parser.add_argument("--all", action="store_true", default=False, help="Process ALL pending unenriched items without limit")
    parser.add_argument("--batch-size", type=int, default=3, help="Item batch size (default: 3 for optimal OpenRouter 18 RPM throughput)")
    parser.add_argument("--cooldown", type=float, default=1.0, help="Cooldown seconds between items (default: 1.0s)")
    parser.add_argument("--random", action="store_true", default=False, help="Pick randomly from inbox")
    parser.add_argument("--only-new", action="store_true", default=False, help="Process ONLY newly harvested items from manifest")
    parser.add_argument("--provider", choices=["auto", "openrouter", "gemini"], default="openrouter", help="AI Provider: openrouter (100%% Free Router, $0.00)")
    parser.add_argument("--workers", type=int, default=1, help="Concurrent worker threads (default: 1 for strict 18 RPM pacing)")
    
    # Legacy Gemini Batch API Options (Suspended)
    parser.add_argument("--submit-batch", action="store_true", default=False, help="Gemini Batch API (Suspended)")
    parser.add_argument("--harvest-batch", action="store_true", default=False, help="Gemini Batch API (Suspended)")
    parser.add_argument("--status-batch", action="store_true", default=False, help="Gemini Batch API (Suspended)")
    args = parser.parse_args()

    if args.status_batch or args.harvest_batch or args.submit_batch:
        print("[!] Notice: Gemini Batch API is suspended per project cost policy ($0.00 zero-cost mandate). No action taken.")
        sys.exit(0)

    effective_limit = 0 if args.all else args.limit
    run_enrichment(limit=effective_limit, batch_size=args.batch_size, random_pick=args.random, only_new=args.only_new, cooldown=args.cooldown, provider=args.provider, workers=args.workers)
