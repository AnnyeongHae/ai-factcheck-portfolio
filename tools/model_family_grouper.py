#!/usr/bin/env python3
"""
Advanced Model Family & Universal Architecture Grouper (2026 SOTA Framework - v2.0)
- GLM-5.3, Qwen-3.8-27B, Wan-2.x 등 파생 모델(양자화/Abliteration/MLX/Demo Space)을 기저 패밀리로 전면 통합
- 개별 개발자의 기여(Abliterated, GGUF, MLX, Space Demo)를 'variant_role'로 존중하면서 분석은 '패밀리 대표 모델' 단위로 묶는 아키텍처
"""

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

def extract_advanced_family_info(title: str, item_id: str = "", source_url: str = "") -> dict:
    """
    Extracts Base Family Name, Variant Role, Creator, and Formats.
    """
    clean_text = f"{title} {item_id} {source_url}".replace('_', ' ').replace('/', ' ').replace(':', ' ')
    
    # 1. Detect Creator / Org
    creator = "Community"
    creator_match = re.search(r'\b(zai[\-_]org|unsloth|qwen|deepseek[\-_]ai|black[\-_]forest[\-_]labs|orcarouter|huihui[\-_]ai|jonathancoletti|hauhaucs|obliteratus|meta|mistralai|google)\b', clean_text, re.IGNORECASE)
    if creator_match:
        c_raw = creator_match.group(1).lower()
        creator_map = {
            "zai-org": "Zhipu AI (GLM Org)", "zai_org": "Zhipu AI (GLM Org)",
            "unsloth": "Unsloth AI", "qwen": "Qwen Alibaba",
            "deepseek-ai": "DeepSeek AI", "deepseek_ai": "DeepSeek AI",
            "orcarouter": "OrcaRouter Community", "huihui-ai": "Huihui AI",
            "jonathancoletti": "Jonathan Coletti", "hauhaucs": "HauhauCS",
            "obliteratus": "OBLITERATUS Project", "meta": "Meta AI",
            "mistralai": "Mistral AI", "google": "Google DeepMind"
        }
        creator = creator_map.get(c_raw, c_raw.capitalize())

    # 2. Detect Variant Role & Quant Format
    detected_formats = []
    variant_role = "일반 파생/배포본 (Standard Release)"

    if re.search(r'\b(demo|space|gradio|hf space)\b', clean_text, re.IGNORECASE):
        variant_role = "🚀 인터랙티브 웹 데모 (Web Space Demo)"
        detected_formats.append("Interactive Web Demo")
    elif re.search(r'\b(abliterated|obliterated|uncensored|jailbreak|mtp)\b', clean_text, re.IGNORECASE):
        variant_role = "🔓 검열해제 / 어블리터레이션 (Abliterated Fine-tune)"
        detected_formats.append("Fine-tune / Uncensored")
    elif re.search(r'\b(dynamic gguf|unsloth.*gguf)\b', clean_text, re.IGNORECASE):
        variant_role = "⚡ Unsloth 선택적 동적 양자화 (Dynamic GGUF)"
        detected_formats.append("Dynamic GGUF v3.0")
    elif re.search(r'\b(gguf|q4_k_m|q8_0|ud[\-_]\d+)\b', clean_text, re.IGNORECASE):
        variant_role = "💾 표준 GGUF 양자화본 (llama.cpp/vLLM)"
        detected_formats.append("GGUF")
    elif re.search(r'\b(mlx)\b', clean_text, re.IGNORECASE):
        variant_role = "🍎 Apple Silicon MLX 네이티브 최적화본"
        detected_formats.append("Apple MLX")
    elif re.search(r'\b(fp8|nvfp4|awq|gptq|exl2)\b', clean_text, re.IGNORECASE):
        variant_role = "⚡ GPU 전용 고속 양자화 (FP8/AWQ)"
        detected_formats.append("FP8/AWQ")
    elif re.search(r'\b(base|instruct|official|safetensors)\b', clean_text, re.IGNORECASE) and not re.search(r'(gguf|awq|mlx)', clean_text, re.IGNORECASE):
        variant_role = "👑 기저 공식 원본 모델 (Base Official Model)"
        detected_formats.append("Safetensors (FP16/BF16)")

    # Fallback format detection
    if not detected_formats:
        if "gguf" in clean_text.lower(): detected_formats.append("GGUF")
        elif "fp8" in clean_text.lower(): detected_formats.append("FP8")
        elif "mlx" in clean_text.lower(): detected_formats.append("MLX")
        else: detected_formats.append("기본 가중치 (Default Weight)")

    # 3. Base Model Family Canonical Mapping
    base_family = "기타 독립 모델 (Standalone / Novel)"

    if re.search(r'\b(glm[\s\-]*5[\.\d]*|glm5)\b', clean_text, re.IGNORECASE):
        base_family = "GLM-5.3 Multi-Modal Foundation Family"
    elif re.search(r'\b(qwen[\s\-]*3[\.\d]*[\s\-]*27b|qwen38[\s\-]*27b)\b', clean_text, re.IGNORECASE):
        base_family = "Qwen-3.8-27B Dense/MoE Family"
    elif re.search(r'\b(qwen[\s\-]*3[\.\d]*[\s\-]*flash|qwen38[\s\-]*flash)\b', clean_text, re.IGNORECASE):
        base_family = "Qwen-3.8-Flash-Next Family"
    elif re.search(r'\b(qwen[\s\-]*2\.5[\s\-]*coder|qwen25[\s\-]*coder)\b', clean_text, re.IGNORECASE):
        base_family = "Qwen-2.5-Coder Family"
    elif re.search(r'\b(qwen[\s\-]*2\.5|qwen25)\b', clean_text, re.IGNORECASE):
        base_family = "Qwen-2.5 Foundation Family"
    elif re.search(r'\b(deepseek[\s\-]*r1|deepseek[\s\-]*reasoner)\b', clean_text, re.IGNORECASE):
        base_family = "DeepSeek-R1 Reasoning Family"
    elif re.search(r'\b(deepseek[\s\-]*v3|deepseek[\s\-]*v4)\b', clean_text, re.IGNORECASE):
        base_family = "DeepSeek-V3/V4 MoE Family"
    elif re.search(r'\b(wan[\s\-]*2[\.\d]*)\b', clean_text, re.IGNORECASE):
        base_family = "Wan-2.x Video Generation Family"
    elif re.search(r'\b(flux[\s\.]*1|flux)\b', clean_text, re.IGNORECASE):
        base_family = "FLUX.1 Diffusion Family"
    elif re.search(r'\b(llama[\s\-]*3[\.\d]*)\b', clean_text, re.IGNORECASE):
        base_family = "Llama-3.x Foundation Family"
    elif re.search(r'\b(whisper|kokoro|breeze[\s\-]*tts)\b', clean_text, re.IGNORECASE):
        base_family = "Audio/TTS Foundation Family"
    elif re.search(r'\b(watercrawl|firecrawl|crawl4ai|anydoc)\b', clean_text, re.IGNORECASE):
        base_family = "Web/Doc Ingestion Engine Family"
    elif re.search(r'\b(praxist|swe[\s\-]*agent|claude[\s\-]*code)\b', clean_text, re.IGNORECASE):
        base_family = "Autonomous Agent Harness Family"
    elif re.search(r'\b(sglang|vllm|tensorrt)\b', clean_text, re.IGNORECASE):
        base_family = "High-Throughput Serving Engine Family"

    return {
        "base_model_family": base_family,
        "variant_role": variant_role,
        "creator": creator,
        "detected_formats": detected_formats
    }

def group_all_candidates():
    inbox_dir = os.path.join(base_dir, "inbox")
    if not os.path.exists(inbox_dir):
        return {}

    family_clusters = {}
    total_scanned = 0

    for f in sorted(os.listdir(inbox_dir)):
        if f.endswith(".json"):
            path = os.path.join(inbox_dir, f)
            try:
                with open(path, "r", encoding="utf-8") as fp:
                    item = json.load(fp)

                info = extract_advanced_family_info(
                    title=item.get("title", ""),
                    item_id=item.get("inbox_id", ""),
                    source_url=item.get("source_url", "")
                )

                item["model_family"] = info["base_model_family"]
                item["variant_role"] = info["variant_role"]
                item["creator"] = info["creator"]
                item["detected_formats"] = info["detected_formats"]

                # Save enriched metadata
                with open(path, "w", encoding="utf-8") as fp:
                    json.dump(item, fp, indent=2, ensure_ascii=False)

                fam = info["base_model_family"]
                if fam not in family_clusters:
                    family_clusters[fam] = []
                family_clusters[fam].append(item)
                total_scanned += 1
            except Exception:
                pass

    print(f"\n[+] Successfully grouped {total_scanned} inbox items into {len(family_clusters)} Advanced Model Families!")
    print("="*80)
    for fam, items in sorted(family_clusters.items(), key=lambda x: len(x[1]), reverse=True):
        roles = set(it.get("variant_role", "") for it in items)
        print(f"📦 [{fam}] : 총 {len(items)}개 파생 모델")
        for r in roles:
            sub_count = len([it for it in items if it.get("variant_role") == r])
            print(f"   ├─ {r}: {sub_count}개")
    print("="*80 + "\n")

    return family_clusters

if __name__ == "__main__":
    group_all_candidates()
