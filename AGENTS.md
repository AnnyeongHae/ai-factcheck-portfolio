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

## 2. LLM API 쿼터 보호 및 클라이언트 워커 엄격 금지 원칙 (Worker Safety)
1. **클라이언트 브라우저 배치 무한 루프 엄격 금지**:
   - 웹 브라우저(`app.js`)는 사용자 View 계층입니다. 브라우저에서 `while(true)` 루프를 돌려 외부 AI API나 서버리스 엔드포인트(`/api/enrich-worker`)를 무한 호출하는 행위를 영구 금지합니다.
   - 탭을 열어두고 자리를 비웠을 때 무한 루프로 인해 OpenRouter 1,000회 쿼터와 DB Egress(5GB)가 소각되는 안티패턴을 절대 작성하지 않습니다.
2. **수동 트리거 세션 하드 캡 (Max Session Cap = 5)**:
   - 사용자가 UI 상에서 명시적으로 AI 요약을 트리거할 경우, 1회 클릭당 **최대 5건**까지만 처리하고 루프를 즉시 정상 종료해야 합니다.
3. **서킷 브레이커(Circuit Breaker) 필수**:
   - 외부 LLM API(OpenRouter 무료 모델 등) 호출 시 연속 3회 실패(`consecutiveFallbacks >= 3` 또는 `consecutiveErrors >= 3`) 발생 시 **즉시 루프를 탈출(Break)**하고 서킷을 차단합니다.
   - 3초, 5초 식의 단순 재시도 폭풍(Retry Storm)을 절대 유발하지 않습니다.
4. **HTTP 429(Rate Limit / Quota Exhausted) 즉시 차단**:
   - HTTP 429 수신 시 다른 모델로의 전환을 즉시 중단하고 해당 요청을 즉각 종료합니다.
5. **모델 캐스케이드(Cascade Fallback) 제한**:
   - 1회의 API 호출에서 7개 이상의 모델을 연쇄 호출하지 않으며, 최대 2개 모델(Primary 1개 + Fallback 1개)까지만 시도합니다.

---

## 3. 데이터 파이프라인의 명확한 역할 분리 원칙 (GitHub Actions vs Vercel Serverless)
1. **GitHub Actions: 순수 데이터 수집(Scraping) 및 랭킹 전담 (AI 실행 절대 금지)**:
   - GitHub Actions는 오직 다중 출처 트렌드 수집(`tools/harvest_trends.py`, 병렬화 적용 후 ~44초)과 일일 23:00 KST 핫 랭킹(`tools/run_eod_digest.py`, ~3초)만 실행합니다.
   - **GitHub Actions 내에서 LLM 호출 및 AI 번역/요약(`drain_ai_enrichment.py`) 실행을 엄격히 영구 금지**합니다 (월 2,000분 무료 러너 쿼터의 낭비 원천 차단).
2. **Vercel Serverless: 모든 AI 번역/요약/분류 단독 전담 (`/api/enrich-worker`)**:
   - 모든 AI 다국어(KO/EN/ZH) 번역, 후킹 요약, 4-Tier 카테고리 분류는 오직 Vercel Serverless Worker(`api/enrich-worker.js`)가 전담합니다 (Vercel 1,000,000회 무료 Serverless 호출 쿼터 및 OpenRouter 무료 모델 활용).
3. **클라이언트 의존성 제로 및 안전 트리거**:
   - 사용자 브라우저의 무한 폴링 루프를 엄격히 금지하며, 사용자의 UI 수동 요청(1회 5건 캡) 또는 Vercel Cron/SWR을 통해 안전하게 분산 처리합니다.

---

## 4. 에이전트 자율 점검 체크리스트
에이전트는 작업 시 다음 6가지를 반드시 점검합니다:
- [ ] 신규 팩트체크/검증 보고서 생성 시 `tools/upsert_factcheck_db.py`를 통해 Neon DB(`verified_factchecks`)에 즉각 INSERT/UPSERT하였는가? (텍스트 답변만 남기는 행위 금지)
- [ ] GitHub Actions 워크플로에 AI 번역/요약 스크립트가 포함되어 있지 않은가? (Actions는 순수 수집만 전담)
- [ ] 프런트엔드 JS에 `while(true)` 형태의 백그라운드 API 폴링/워커 루프가 존재하는가?
- [ ] 외부 LLM API 연동부에 서킷 브레이커(3회 실패 시 즉각 중단)가 구현되어 있는가?
- [ ] 1회 수동 트리거 시 최대 처리량 캡(Max Batch Cap = 5)이 설정되어 있는가?
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

