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

---

## Mandatory Post-Enrichment Step: H-V-D Tripod Cross-Viral Spike Engine (`CROSS_SPIKE`)
AI 번역/요약이 완료된 직후(또는 일일 다이제스트 `tools/run_eod_digest.py` 실행 시)에는 **반드시 `tools/recompute_spike_scores.py --commit`이 연쇄 실행**되어야 합니다 (`tools/re_enrich_all_600.py` 내부에 자동 내장됨).

### 4대 핵심 불변식 (Root-Cause Prevention Invariants)
1. **Primary Source 보존 (`sources[0] = primaryUrl`)**:
   - `api/embed-worker.js` 및 `tools/recompute_spike_scores.py`에서 중복 기사를 대표 기사로 병합할 때, 반드시 대표 기사 자신의 출처(`type: "primary"`)를 `sources[0]`에 먼저 넣고 중복 기사를 추가하여 `sources.length >= 2` 및 `is_cross_spiking = true`가 누락되지 않도록 보장합니다.
2. **애매 구간(`0.78 <= sim < 0.88`) 결정론적 고유 토큰 교집합 판정**:
   - 외부 JEV LLM이 타임아웃되더라도 불용어를 제외한 핵심 고유 토큰(3글자 이상 브랜드/모델명/버전/코드네임)이 2개 이상 겹치면 즉시 결정론적으로 병합합니다.
3. **다국어(`KO`/`ZH`) 원문의 영문 제목(`title_en`) 강제 생성**:
   - 한국/중국 커뮤니티 및 미디어 기사가 영어 기사와 100% 클러스터링되도록 번역 단계에서 `title_en`을 항상 생성하고, `GENERIC_VERSION_PATTERNS` 정규식으로 신규 모델/버전 출시를 자동 그룹핑합니다.
4. **H-V-D Tripod + 36h 반감기 + 7일 활성 윈도우**:
   - $\text{Score} = \text{round}((H \times V \times D \times 10.0) \times e^{-\frac{\ln 2}{36}\Delta t_{\text{hours}}},\; 1)$
   - `created_at >= NOW() - INTERVAL '7 days'` 조건과 결합하여, 실시간 급상승 이슈만 `'🔥 크로스 바이럴 (급상승)'`에 노출하고 7일이 지난 구형 이슈(예: 9~11일 경과한 Meta Muse 등)는 자동 졸업시킵니다.
5. **일자별 크로스 바이럴 랭킹 보드(`cross_viral_daily_rankings`) 및 최고점(`Peak Score/Rank`) DB 영구 적재**:
   - `tools/recompute_spike_scores.py --commit` 실행 시 각 아이템의 `live_spike_score`, `peak_spike_score`, `peak_spike_date`, `best_spike_rank`를 `raw_trends_inbox`에 업데이트하고, 당일(KST) 상위 30개 이슈를 `cross_viral_daily_rankings`에 자동 UPSERT합니다.
   - 과거 일자별 급상승 랭킹 조회: `/api/inbox?facet=CROSS_SPIKE&spike_date=YYYY-MM-DD` (가용 날짜 목록: `/api/inbox?spike_dates_list=true`).


