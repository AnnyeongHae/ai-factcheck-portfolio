#!/usr/bin/env python3
"""
Pipeline End-to-End Cost Estimator (2026 SOTA Framework)
최신 생성형 AI 파이프라인(LLM + TTS + Video Generation + Compute)의 실제 단위 제작 원가 및 대량 양산 비용을 계산합니다.

Usage:
    python tools/estimate_pipeline_cost.py --video higgsfield_seedance_2_0_720p --tts elevenlabs_turbo_v2 --llm openai_gpt4o --duration 60
    python tools/estimate_pipeline_cost.py --preset viral_free_stock
    python tools/estimate_pipeline_cost.py --compare-all
"""

import argparse
import json
import os
import sys

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def load_benchmarks():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "configs", "pipeline_cost_benchmark.json")
    if not os.path.exists(config_path):
        print(f"[!] Error: Benchmark config not found at {config_path}")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

PRESETS = {
    "viral_free_stock": {
        "name": "완전 무료 스톡 비디오 조합 (SNS 바이럴 주장 기본형)",
        "llm": "deepseek_v3",
        "tts": "edge_tts_free",
        "video": "pexels_pixabay_stock_api",
        "compute": "ffmpeg_local_cpu"
    },
    "commercial_stock_realistic": {
        "name": "상용 고품질 스톡 비디오 조합 (OpenAI + ElevenLabs)",
        "llm": "openai_gpt4o",
        "tts": "elevenlabs_turbo_v2",
        "video": "pexels_pixabay_stock_api",
        "compute": "ffmpeg_local_cpu"
    },
    "higgsfield_seedance_720p_shorts": {
        "name": "Higgsfield Seedance 2.0 (720p) 순수 AI 생성 영상 조합",
        "llm": "openai_gpt4o",
        "tts": "elevenlabs_turbo_v2",
        "video": "higgsfield_seedance_2_0_720p",
        "compute": "cloud_modal_or_runpod_serverless_gpu"
    },
    "higgsfield_seedance_1080p_cinematic": {
        "name": "Higgsfield Seedance 2.0 (1080p 고화질) 시네마틱 조합",
        "llm": "anthropic_claude_3_5_sonnet",
        "tts": "elevenlabs_turbo_v2",
        "video": "higgsfield_seedance_2_0_1080p",
        "compute": "cloud_modal_or_runpod_serverless_gpu"
    }
}

def calculate_cost(llm_key, tts_key, video_key, duration_sec=60, reject_ratio=1.5, batch_count=30):
    data = load_benchmarks()
    
    # 1. LLM
    llm_info = data["llm_script_generation"].get(llm_key, {"cost_per_60s_script": 0.005})
    llm_cost = (llm_info["cost_per_60s_script"] / 60.0) * duration_sec

    # 2. TTS
    tts_info = data["tts_voice_synthesis"].get(tts_key, {"cost_per_60s_audio": 0.0})
    tts_cost = (tts_info["cost_per_60s_audio"] / 60.0) * duration_sec

    # 3. Video
    vid_info = data["video_generation_and_stock"].get(video_key, {"cost_per_second": 0.0})
    cost_per_sec = vid_info.get("cost_per_second", 0.0)
    raw_video_cost = cost_per_sec * duration_sec
    effective_video_cost = raw_video_cost * reject_ratio

    # 4. Total
    raw_unit_cost = llm_cost + tts_cost + raw_video_cost
    effective_unit_cost = llm_cost + tts_cost + effective_video_cost
    monthly_batch_cost = effective_unit_cost * batch_count

    return {
        "duration_sec": duration_sec,
        "reject_ratio": reject_ratio,
        "batch_count": batch_count,
        "breakdown": {
            "llm": {"provider": llm_key, "cost": round(llm_cost, 4)},
            "tts": {"provider": tts_key, "cost": round(tts_cost, 4)},
            "video_raw": {"provider": video_key, "cost": round(raw_video_cost, 2)},
            "video_effective": {"cost": round(effective_video_cost, 2)}
        },
        "raw_unit_cost": round(raw_unit_cost, 2),
        "effective_unit_cost": round(effective_unit_cost, 2),
        "monthly_batch_cost": round(monthly_batch_cost, 2)
    }

def print_summary(res, title="파이프라인 원가 분석 결과"):
    print(f"\n=======================================================")
    print(f" [REPORT] {title}")
    print(f"=======================================================")
    print(f"- 영상 길이: {res['duration_sec']}초 (1분 기준)")
    print(f"- 재시도 배율(Reject Ratio): {res['reject_ratio']}x (실패/재시도 반영)")
    print(f"- 월간 양산 수량: {res['batch_count']}편")
    print(f"-------------------------------------------------------")
    print(f" 1. 대본(LLM) 비용:        ${res['breakdown']['llm']['cost']:.4f} ({res['breakdown']['llm']['provider']})")
    print(f" 2. 음성(TTS) 비용:        ${res['breakdown']['tts']['cost']:.4f} ({res['breakdown']['tts']['provider']})")
    print(f" 3. 영상(Video) 순수 비용:  ${res['breakdown']['video_raw']['cost']:.2f} ({res['breakdown']['video_raw']['provider']})")
    print(f" 4. 영상 유효 실질 비용:   ${res['breakdown']['video_effective']['cost']:.2f} (재시도 반영)")
    print(f"-------------------------------------------------------")
    print(f" -> 1편당 표기 원가 (Sticker Price):     ${res['raw_unit_cost']:.2f}")
    print(f" -> 1편당 유효 실질 원가 (Effective Cost): ${res['effective_unit_cost']:.2f}")
    print(f" -> 월간 {res['batch_count']}편 양산 시 예상 총액:       ${res['monthly_batch_cost']:.2f}")
    print(f"=======================================================\n")

def main():
    parser = argparse.ArgumentParser(description="2026 AI Pipeline Cost Estimator")
    parser.add_argument("--preset", choices=list(PRESETS.keys()), help="Preset pipeline configuration")
    parser.add_argument("--llm", default="openai_gpt4o", help="LLM model key")
    parser.add_argument("--tts", default="elevenlabs_turbo_v2", help="TTS model key")
    parser.add_argument("--video", default="higgsfield_seedance_2_0_720p", help="Video generation provider key")
    parser.add_argument("--duration", type=int, default=60, help="Video duration in seconds")
    parser.add_argument("--reject-ratio", type=float, default=1.5, help="Reject/Retry multiplier")
    parser.add_argument("--batch", type=int, default=30, help="Batch count per month (e.g. 1 short per day = 30)")
    parser.add_argument("--compare-all", action="store_true", help="Compare all standard presets")

    args = parser.parse_args()

    if args.compare_all:
        print("\n[2026 파이프라인 시나리오별 1분 영상 원가 종합 비교표]")
        for key, p in PRESETS.items():
            res = calculate_cost(p["llm"], p["tts"], p["video"], args.duration, args.reject_ratio, args.batch)
            print_summary(res, title=f"[{key}] {p['name']}")
        return

    if args.preset:
        p = PRESETS[args.preset]
        res = calculate_cost(p["llm"], p["tts"], p["video"], args.duration, args.reject_ratio, args.batch)
        print_summary(res, title=f"Preset: {p['name']}")
    else:
        res = calculate_cost(args.llm, args.tts, args.video, args.duration, args.reject_ratio, args.batch)
        print_summary(res, title=f"Custom Pipeline ({args.video} + {args.tts})")

if __name__ == "__main__":
    main()
