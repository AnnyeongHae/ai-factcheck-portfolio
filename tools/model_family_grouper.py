#!/usr/bin/env python3
"""
Model Family & Architecture Semantic Grouper (2026 SOTA Framework - v1.0)
- GGUF, AWQ, EXL2, FP8, LoRA 등 수많은 파생/양자화 모델들을 기저 아키텍처(Base Model Family)로 자동 그룹핑
- 예: [unsloth/Qwen3.8-Flash-Next-GGUF, Qwen3.8-Flash-AWQ, Qwen3.8-Flash-Next] ➔ 'Qwen-3.8-Flash-Next' 패밀리로 통합
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

def extract_base_model_family(title: str, item_id: str = "") -> dict:
    """
    Extracts the clean Base Model Family name and detected quantization/variant formats.
    """
    clean_text = f"{title} {item_id}".replace('_', ' ').replace('/', ' ')
    
    # 1. Detect Quantization & Format
    detected_formats = []
    quant_patterns = [
        (r'\b(gguf|dynamic gguf|ud\s*[\d\.]*)\b', 'GGUF (Dynamic/Static)'),
        (r'\b(awq|4bit|int4|int8)\b', 'AWQ / INT4'),
        (r'\b(gptq)\b', 'GPTQ'),
        (r'\b(exl2)\b', 'EXL2'),
        (r'\b(fp8|nvfp4)\b', 'FP8 / NVFP4'),
        (r'\b(safetensors|fp16|bfloat16|bf16)\b', 'Safetensors (Unquantized)'),
        (r'\b(lora|qlora)\b', 'LoRA Adapter')
    ]
    for pattern, fmt_name in quant_patterns:
        if re.search(pattern, clean_text, re.IGNORECASE):
            if fmt_name not in detected_formats:
                detected_formats.append(fmt_name)

    # 2. Extract Base Model Family Canonical Name
    base_family = "기타 독립 모델 (Standalone / Novel)"
    
    # Known Major AI Architectures
    if re.search(r'\b(qwen[\s\-]*3[\.\d]*[\s\-]*flash[\s\-]*next|qwen38[\s\-]*flash)\b', clean_text, re.IGNORECASE):
        base_family = "Qwen-3.8-Flash-Next Family"
    elif re.search(r'\b(qwen[\s\-]*2\.5[\s\-]*coder|qwen25[\s\-]*coder)\b', clean_text, re.IGNORECASE):
        base_family = "Qwen-2.5-Coder Family"
    elif re.search(r'\b(qwen[\s\-]*2\.5|qwen25)\b', clean_text, re.IGNORECASE):
        base_family = "Qwen-2.5 Foundation Family"
    elif re.search(r'\b(deepseek[\s\-]*r1|deepseek[\s\-]*reasoner)\b', clean_text, re.IGNORECASE):
        base_family = "DeepSeek-R1 Reasoning Family"
    elif re.search(r'\b(deepseek[\s\-]*v3|deepseek[\s\-]*v4)\b', clean_text, re.IGNORECASE):
        base_family = "DeepSeek-V3/V4 MoE Family"
    elif re.search(r'\b(llama[\s\-]*3\.3|llama33|llama[\s\-]*3\.2|llama[\s\-]*3\.1)\b', clean_text, re.IGNORECASE):
        base_family = "Llama-3.x Foundation Family"
    elif re.search(r'\b(flux[\s\.]*1|flux)\b', clean_text, re.IGNORECASE):
        base_family = "FLUX.1 Diffusion Family"
    elif re.search(r'\b(stable[\s\-]*diffusion[\s\-]*3\.5|sd3\.5|sdxl)\b', clean_text, re.IGNORECASE):
        base_family = "Stable Diffusion 3.x/XL Family"
    elif re.search(r'\b(wan[\s\-]*2[\.\d]*)\b', clean_text, re.IGNORECASE):
        base_family = "Wan-2.x Video Generation Family"
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
        "detected_formats": detected_formats if detected_formats else ["기본 가중치 (Default Weight)"]
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

                info = extract_base_model_family(
                    title=item.get("title", ""),
                    item_id=item.get("inbox_id", "")
                )

                item["model_family"] = info["base_model_family"]
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

    print(f"\n[+] Successfully grouped {total_scanned} inbox items into {len(family_clusters)} Base Model Families!")
    print("="*80)
    for fam, items in sorted(family_clusters.items(), key=lambda x: len(x[1]), reverse=True):
        formats = set()
        for it in items:
            for fmt in it.get("detected_formats", []):
                formats.add(fmt)
        print(f"📦 [{fam}] : {len(items)}개 변형본 (포맷: {', '.join(formats)})")
    print("="*80 + "\n")

    return family_clusters

if __name__ == "__main__":
    group_all_candidates()
