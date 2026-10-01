# AI 팩트체크 허브: 에이전트 핵심 행동 수칙 및 아키텍처 원칙 (AGENTS.md)

---

## 1. DB-First 단일 진실 원천(SSOT) 아키텍처 원칙
1. **중앙 집중식 DB 연결 (Aiven PostgreSQL SSOT / Neon 백업)**:
   - 본 프로젝트의 정본 데이터베이스는 `DATABASE_URL` 환경변수를 통해 중앙 집중식으로 주입됩니다.
   - 모든 메타데이터, 원천 피드(`raw_trends_inbox`), 정밀 팩트체크(`verified_factchecks`)는 오직 DB에 직접 저장/조회됩니다.
   - 로컬 `investigations/` 수작업 폴더 생성 및 Git 커밋을 엄격히 금지합니다.
2. **카테고리 및 지표 집계의 DB 엔진 일임 (No Slice Aggregation)**:
   - 카테고리별 통계, 상태 카운트는 메모리 루프나 부분 슬라이스(`LIMIT 600`)에서 세지 않고, **반드시 SQL `GROUP BY`를 통해 DB 엔진에서 직접 계산**하여 일관성을 100% 보장해야 합니다.
3. **Edge CDN SWR 캐싱**:
   - 프런트엔드는 `/api/portfolios`, `/api/stats`, `/api/inbox`를 통해 글로벌 CDN 에지 캐시(0.05초)로 서빙하여 DB Egress 및 동시 연결을 완벽히 보호합니다.
4. **신규 팩트체크 생산 시 DB 실시간 적재 의무화 (Factcheck DB Ingestion Harness)**:
   - 사용자가 팩트체크 조사, 검증 보고서 작성, 신규 도시에 분석 생성을 요청하는 경우, 에이전트는 **절대로 대화창 텍스트 답변만 출력하고 작업을 끝내서는 안 됩니다.**
   - 분석 완료 즉시 정식 스키마(`case_id`, `title`, `category`, `verdict`, `claims_assessment`, `portfolio_story`, `clustering`, `sources`)를 갖추어 `tools/upsert_factcheck_db.py`를 실행하여 정본 DB(`verified_factchecks`, `factcheck_atomic_claims` 등)에 무조건 즉각 INSERT/UPSERT해야 합니다.
   - 적재 완료 후 부여된 `case_id`와 DB 적재 성공 여부를 최종 응답에 반드시 명시하여 사용자 및 프런트엔드 포트폴리오와 100% 동기화되도록 합니다.

---

## 2. AI 요약/번역 3대 실행 모드(3-Mode AI Enrichment) 및 쿼터 보호 수칙
AI 다국어 요약·번역·분류 작업은 실행 환경과 토큰 상황에 따라 반드시 다음 **3가지 표준 모드**(`configs/ai_enrichment_modes.json`, `.agents/skills/ai-enrichment-pipeline/SKILL.md`) 중 하나로만 진행합니다:

1. **모드 1 — 로컬 기본 진행 (Local Primary: Antigravity `gemini-3.6-flash`, Batch = 10)**:
   - 로컬에서 진행할 때는 가장 저렴하고 빠른 **`gemini-3.6-flash`**(`thinkingBudget: 0` 설정으로 추론 토큰 소모 0)를 사용하여 **10개씩 배치(`batch_size = 10`)**로 진행합니다.
   - 명령어: `python -u tools/re_enrich_all_600.py --mode local-gemini --batch-size 10`
2. **모드 2 — 원격 웹 배포 상태 진행 (Remote Web: OpenRouter 무료 방식, Batch = 1, 1회 클릭 시 끝까지 진행)**:
   - 원격(웹 배포 상태, `/api/enrich-worker`)에서 진행할 때는 **OpenRouter의 기존 무료 모델 방식(`inclusionai/ling-3.0-flash-sante:free`)**을 적용하여 **1개씩 배치(`limit = 1`)**로 진행합니다.
   - **단, UI에서 한 번의 클릭으로 잔여 미분류 건수가 `0건`이 될 때까지 끝까지 연속 진행**되도록 작동합니다 (`src/js/core/api.js`의 `startContinuousAiWorker`).
   - 페이지 로드시 자동 백그라운드 실행은 금지하며, 사용자가 버튼을 1회 클릭했을 때만 시작되고 다시 클릭하면 즉시 일시정지됩니다.
3. **모드 3 — 로컬 폴백 진행 (Local Fallback: OpenRouter 무료 방식, Batch = 3)**:
   - 로컬에서 진행할 때 Antigravity의 Gemini 토큰이 부족하거나 쿼터(HTTP 429)가 소진될 경우, **OpenRouter의 무료 모델 방식으로 3개씩 배치(`batch_size = 3`)**를 돌릴 수 있도록 자동/수동 전환합니다.
   - 명령어: `python -u tools/re_enrich_all_600.py --mode local-openrouter --batch-size 3` (또는 `local-gemini` 실행 중 429 발생 시 자동 폴백).
4. **서킷 브레이커(Circuit Breaker) 및 HTTP 429 즉시 차단**:
   - 외부 LLM API 호출 시 연속 3회 실패(`consecutiveFallbacks >= 3` 또는 `consecutiveErrors >= 3`) 또는 HTTP 429 수신 시 즉시 루프를 탈출(Break)하고 서킷을 차단합니다.
   - 1회의 API 호출에서 최대 2개 모델(Primary 1개 + Fallback 1개)까지만 시도합니다.

---

## 3. 데이터 파이프라인의 명확한 역할 분리 원칙 (GitHub Actions vs Vercel Serverless vs Local CLI)
1. **GitHub Actions: 순수 데이터 수집(Scraping) 및 랭킹 전담 (AI 실행 절대 금지)**:
   - GitHub Actions는 오직 다중 출처 트렌드 수집(`tools/harvest_trends.py`, 72개 피드 병렬 수집 + 본문 GZIP 압축 `raw_content_vault` 적재)과 일일 23:00 KST 핫 랭킹(`tools/run_eod_digest.py`)만 실행합니다.
   - **GitHub Actions 내에서 LLM 호출 및 AI 번역/요약 실행을 엄격히 영구 금지**합니다.
2. **Vercel Serverless (`/api/enrich-worker`): 원격 웹 모드(Mode 2) 전담**:
   - 웹 배포 환경에서는 OpenRouter 무료 모델로 1건씩(`limit=1`) 처리하며, 프런트엔드 UI 1회 클릭 시 잔여 건수가 모두 완료될 때까지 연속 실행됩니다.
3. **Local CLI (`tools/re_enrich_all_600.py`): 로컬 고속 대량 처리(Mode 1 & Mode 3) 전담**:
   - 대량 미분류 건은 로컬에서 Mode 1(`gemini-3.6-flash`, 10건 배치) 또는 Mode 3(Gemini 토큰 부족 시 OpenRouter 무료, 3건 배치)로 고속 처리합니다.

---

## 4. 에이전트 자율 점검 체크리스트
에이전트는 작업 시 다음 8가지를 반드시 점검합니다:
- [ ] 신규 팩트체크/검증 보고서 생성 시 `tools/upsert_factcheck_db.py`를 통해 정본 DB(`verified_factchecks`)에 즉각 INSERT/UPSERT하였는가? (텍스트 답변만 남기는 행위 금지)
- [ ] GitHub Actions 워크플로에 AI 번역/요약 스크립트가 포함되어 있지 않은가? (Actions는 순수 수집만 전담)
- [ ] AI 요약/번역 시 3대 실행 모드(1. 로컬 `gemini-3.6-flash` 10건 배치 / 2. 원격 웹 OpenRouter 무료 1건 배치·1회 클릭 끝까지 진행 / 3. 로컬 Gemini 토큰 부족 시 OpenRouter 무료 3건 배치)가 정확히 준수되었는가?
- [ ] 외부 LLM API 연동부에 서킷 브레이커(3회 실패 또는 HTTP 429 시 즉각 중단/폴백)가 구현되어 있는가?
- [ ] 웹 UI에서 1회 클릭 시 중간(5건)에 끊기지 않고 끝까지 연속 실행되며 재클릭 시 일시정지되는가?
- [ ] 카테고리 집계가 임의의 배열 슬라이스가 아닌 DB SQL `GROUP BY` 기반인가?
- [ ] 다중 출처 중복 병합(`api/embed-worker.js`, `tools/recompute_spike_scores.py`) 시 대표 기사 자신(`primaryUrl`)이 `raw_payload.sources[0]`에 반드시 포함되어 `sources.length >= 2` 및 `is_cross_spiking = true` 불변식이 유지되는가?
- [ ] 대량 AI 번역(`tools/re_enrich_all_600.py`) 또는 일일 다이제스트(`tools/run_eod_digest.py`) 완료 직후 `tools/recompute_spike_scores.py --commit`이 자동 연쇄 실행되어 H-V-D 급상승 점수가 즉시 갱신되는가?

---

## 5. 트렌드 수집기(Harvester) 아키텍처 및 벤치마크 고정 수칙
1. **수집기 실행 시간(2분~2분 30초)의 안정성 보장**:
   - GitHub Actions 워크플로 총 실행 시간(환경 셋업 + 수집 + 랭킹) 2분 초반대는 GitHub Actions 제한(10분)의 25%, 월간 쿼터(2,000분)의 18.7% 수준으로 **완벽히 안전한 정상 범위**입니다. 불필요하게 코드를 고치거나 다운그레이드하지 않습니다.
2. **플랫폼 확장 시 콜드 스타트(Cold Start) 인지**:
   - 신규 출처가 투입되거나 스캔 한도가 상향될 때 발생하는 첫 회차 대량 수집(예: 337건)은 신규 데이터 초기 흡수 현상이며, 차기 회차부터 정상 증분치(~60-80건)로 자동 수렴하므로 중복 방지 규칙을 임의로 변경하지 않습니다.
3. **병목 구간(HN/Reddit 댓글) 병렬 처리 검증 자산 (A/B Test 완료)**:
   - 현재 순차 수집(~50초)은 매우 안정적입니다.
   - 향후 출처가 대폭 늘어나 수집기 가속이 필요할 경우, 실측 A/B 테스트로 검증된 `concurrent.futures.ThreadPoolExecutor(max_workers=6)`(4.78배 속도 향상, 100% 데이터 정합성, HTTP 429 0건) 방식을 사용합니다 (`docs/HARVESTER_AND_PIPELINE_ARCHITECTURE_AUDIT.md` 참조).

---

## 6. 🔥 크로스 바이럴 (`CROSS_SPIKE`) & H-V-D Tripod 급상승 엔진 불변 수칙
과거 `Google Gemini 4 Argon` 등 주요 글로벌 이슈가 크로스 바이럴 탭에서 누락되었던 **4대 구조적 원인**을 영구 차단하기 위해 다음 불변식(Invariants)을 엄격히 강제합니다:

1. **불변식 1 — 대표 기사 자기 출처(`sources[0]`) 강제 보존 (Off-by-One 원천 차단)**:
   - `api/embed-worker.js` 및 `tools/recompute_spike_scores.py`에서 중복 기사를 대표 기사의 `raw_payload.sources` 배열로 병합할 때, 반드시 **대표 기사 자신의 출처(`primaryUrl`, `type: "primary"`)를 `sources[0]`에 먼저 삽입(Seed)**한 뒤 중복 출처(`type: "discussion"`)를 추가해야 합니다.
   - 2개 플랫폼에서 보도된 이슈가 `sources.length = 1`이 되어 `is_cross_spiking = false`로 누락되는 현상을 `ensure_primary_in_sources()` 자가 치유(Self-Healing) 로직으로 100% 방지합니다.
2. **불변식 2 — 애매 구간(`0.78 <= sim < 0.88`) 결정론적 토큰 교집합 판정기 (Zero-LLM-Failure Fallback)**:
   - `api/embed-worker.js`에서 코사인 유사도 `0.78 ~ 0.88` 구간의 제목 쌍을 병합할 때, 외부 OpenRouter JEV LLM 타임아웃이나 429 에러로 인해 병합이 증발하지 않도록 **불용어를 제외한 핵심 고유 토큰(브랜드·모델명·버전·코드네임 등 3글자 이상 토큰)이 2개 이상 일치하면 LLM 호출 없이 즉시 결정론적으로 병합**합니다.
3. **불변식 3 — 다국어(`KO`/`ZH`) 원문 기사의 영어 표준 제목(`title_en`) 강제 생성 및 정규식 릴리즈 클러스터링**:
   - 한국(GeekNews, 파이토치 한국 사용자 모임 등)·중국(Jiqizhixin, QbitAI 등) 원문 기사도 영어권 기사와 100% 의미론적·키워드 매칭이 되도록 `tools/re_enrich_all_600.py`에서 반드시 영문 번역 제목(`title_en`)을 함께 생성합니다.
   - `tools/recompute_spike_scores.py`의 `extract_release_cluster_key()`는 다국어 별칭 및 범용 정규식(`GENERIC_VERSION_PATTERNS`: `{모델패밀리} + {버전} + {코드네임}`)을 통해 최근 7일 이내 동일 릴리즈/이슈를 자동 허브 클러스터링합니다.
4. **불변식 4 — 파이프라인 자동 연쇄 실행 및 7일 활성 윈도우 + 36시간 반감기 수식**:
   - `tools/re_enrich_all_600.py` 및 `tools/run_eod_digest.py` 실행 완료 시 자동으로 `tools/recompute_spike_scores.py --commit`이 호출되어 DB의 `spike_analysis`와 `is_cross_spiking`을 즉시 최신화합니다.
   - **H-V-D Tripod 공식**:
     $$\text{Spike Score} = \text{round}\left( (H \times V \times D \times 10.0) \times e^{-\frac{\ln 2}{36.0} \cdot \Delta t_{\text{hours}}},\; 1 \right)$$
     - **$H$ (Heterogeneity, 3축 교차 가중치)**: `PRESS`(언론) / `COMMUNITY`(HN, Reddit, GeekNews 등) / `CODE`(GitHub, HuggingFace, ArXiv, 공식 리서치) 중 1축=`1.0x`, 2축=`2.5x`, 3축=`5.0x` (`3-Axis SUPER SPIKE`).
     - **$V$ (Velocity, 시간당 확산 및 시계열 급증 속도)**: $\left(\frac{N_{\text{sources}}}{\sqrt{\max(1.0, \Delta t_{\text{hours}})}}\right) \times \left(1.0 + \min\left(2.5, \frac{\Delta_{\text{metric}}}{40.0}\right)\right)$ (`trend_metric_snapshots` 시계열 $\Delta$ 반영).
     - **$D$ (Depth, 커뮤니티 반응 깊이)**: $\log_{10}\left(\max\left(1.0,\; 10.0 + 2.0 \cdot N_{\text{comments}} + 0.5 \cdot S_{\text{viral}} + 0.5 \cdot \Delta_{\text{metric}}\right)\right)$.
     - **Decay & Window**: 36시간 반감기 지수 감쇠($\lambda = \ln 2 / 36$) 및 `/api/inbox?category=CROSS_SPIKE`의 **최근 7일(`created_at >= NOW() - INTERVAL '7 days'`) 활성 윈도우**를 적용하여 오래된 이슈(예: 7일 경과한 Meta Muse 등)는 실시간 급상승 레이더에서 자연 졸업시킵니다.


