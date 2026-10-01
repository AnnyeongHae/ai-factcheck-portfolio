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
에이전트는 작업 시 다음 6가지를 반드시 점검합니다:
- [ ] 신규 팩트체크/검증 보고서 생성 시 `tools/upsert_factcheck_db.py`를 통해 정본 DB(`verified_factchecks`)에 즉각 INSERT/UPSERT하였는가? (텍스트 답변만 남기는 행위 금지)
- [ ] GitHub Actions 워크플로에 AI 번역/요약 스크립트가 포함되어 있지 않은가? (Actions는 순수 수집만 전담)
- [ ] AI 요약/번역 시 3대 실행 모드(1. 로컬 `gemini-3.6-flash` 10건 배치 / 2. 원격 웹 OpenRouter 무료 1건 배치·1회 클릭 끝까지 진행 / 3. 로컬 Gemini 토큰 부족 시 OpenRouter 무료 3건 배치)가 정확히 준수되었는가?
- [ ] 외부 LLM API 연동부에 서킷 브레이커(3회 실패 또는 HTTP 429 시 즉각 중단/폴백)가 구현되어 있는가?
- [ ] 웹 UI에서 1회 클릭 시 중간(5건)에 끊기지 않고 끝까지 연속 실행되며 재클릭 시 일시정지되는가?
- [ ] 카테고리 집계가 임의의 배열 슬라이스가 아닌 DB SQL `GROUP BY` 기반인가?

---

## 5. 트렌드 수집기(Harvester) 아키텍처 및 벤치마크 고정 수칙
1. **수집기 실행 시간(2분~2분 30초)의 안정성 보장**:
   - GitHub Actions 워크플로 총 실행 시간(환경 셋업 + 수집 + AI 요약 + 랭킹) 2분 초반대는 GitHub Actions 제한(10분)의 25%, 월간 쿼터(2,000분)의 18.7% 수준으로 **완벽히 안전한 정상 범위**입니다. 불필요하게 코드를 고치거나 다운그레이드하지 않습니다.
2. **플랫폼 확장 시 콜드 스타트(Cold Start) 인지**:
   - 신규 출처가 투입되거나 스캔 한도가 상향될 때 발생하는 첫 회차 대량 수집(예: 337건)은 신규 데이터 초기 흡수 현상이며, 차기 회차부터 정상 증분치(~60-80건)로 자동 수렴하므로 중복 방지 규칙을 임의로 변경하지 않습니다.
3. **병목 구간(HN/Reddit 댓글) 병렬 처리 검증 자산 (A/B Test 완료)**:
   - 현재 순차 수집(~50초)은 매우 안정적입니다.
   - 향후 출처가 대폭 늘어나 수집기 가속이 필요할 경우, 실측 A/B 테스트로 검증된 `concurrent.futures.ThreadPoolExecutor(max_workers=6)`(4.78배 속도 향상, 100% 데이터 정합성, HTTP 429 0건) 방식을 사용합니다 (`docs/HARVESTER_AND_PIPELINE_ARCHITECTURE_AUDIT.md` 참조).

