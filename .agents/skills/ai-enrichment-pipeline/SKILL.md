---
name: ai-enrichment-pipeline
description: 3-Mode AI Enrichment & Trilingual Translation Pipeline for AI FactCheck Hub. Enforces strict separation between Local Primary (Antigravity gemini-3.6-flash, batch=10), Remote Web Deployed (OpenRouter Free, batch=1, 1-click continuous until completion), and Local Fallback (OpenRouter Free, batch=3 when Gemini tokens are low).
---

# AI Enrichment Pipeline Skill (3-Mode Architecture)

Whenever the user requests AI summarization, trilingual translation (`KO`/`EN`/`ZH`), category classification, or inbox enrichment (`raw_trends_inbox`), you **MUST** strictly follow one of the 3 canonical execution modes defined in [`configs/ai_enrichment_modes.json`](file:///d:/2026.06.21_Antigravity/2026-08-31_WEB_Factcheck/configs/ai_enrichment_modes.json).

---

## Mode 1: 로컬 기본 진행 (Local Primary — Antigravity `gemini-3.6-flash`, Batch = 10)
- **언제 사용하는가**: 로컬 환경에서 AI 미분류/미요약 건들을 일괄 처리할 때 (기본값).
- **적용 모델**: Antigravity `gemini-3.6-flash` (가장 저렴한 Flash 모델, `thinkingBudget: 0` 적용으로 추론 토큰 낭비 제거).
- **배치 크기**: **10건씩 (`batch_size = 10`)**
- **실행 명령어**:
  ```powershell
  python -u tools/re_enrich_all_600.py --mode local-gemini --batch-size 10
  ```
  *(테스트 또는 일부만 실행 시 `--limit 10` 추가)*

---

## Mode 2: 원격 웹 배포 상태 진행 (Remote Web — OpenRouter 무료, Batch = 1, 1-Click 끝까지 진행)
- **언제 사용하는가**: 배포된 웹 대시보드(`https://annyeonghae.github.io/ai-factcheck-portfolio`) 및 Vercel Serverless(`/api/enrich-worker`)에서 실행할 때.
- **적용 모델**: OpenRouter 100% 무료 모델 (`inclusionai/ling-3.0-flash-sante:free` → 폴백 `liquid/lfm-2.5-2.6b:free`).
- **배치 크기**: **1건씩 (`limit = 1`)** — Vercel Serverless 타임아웃 방지 및 무료 쿼터 최적화.
- **UI 작동 방식 (`src/js/core/api.js` - `startContinuousAiWorker`)**:
  - 5건 세션 제한(`MAX_SESSION_CAP`) 없음.
  - **한 번의 클릭으로 잔여 미분류 건수(`remaining_unclassified`)가 `0건`이 될 때까지 1건씩 끝까지 연속 진행** (단, 연속 3회 에러/폴백 또는 HTTP 429 발생 시 서킷 브레이커 작동).

---

## Mode 3: 로컬 폴백 진행 (Local Fallback — OpenRouter 무료, Batch = 3)
- **언제 사용하는가**: 로컬에서 진행할 때 Antigravity Gemini 토큰이 부족하거나 HTTP 429(쿼터 소진)가 발생한 경우.
- **적용 모델**: OpenRouter 100% 무료 모델 (`inclusionai/ling-3.0-flash-sante:free` → `liquid/lfm-2.5-2.6b:free`).
- **배치 크기**: **3건씩 (`batch_size = 3`)**
- **실행 방법**:
  1. **자동 전환**: `tools/re_enrich_all_600.py --mode local-gemini` 실행 중 Gemini 토큰 소진(HTTP 429) 감지 시 자동으로 `local-openrouter` (3건 배치) 모드로 즉시 전환하여 중단 없이 진행.
  2. **수동 지정 실행**:
     ```powershell
     python -u tools/re_enrich_all_600.py --mode local-openrouter --batch-size 3
     ```
