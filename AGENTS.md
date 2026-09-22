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

## 3. 데이터 파이프라인(ETL/Enrichment)의 정석 위치
1. **GitHub Actions 스케줄러(CI/CD) 배치 처리**:
   - 데이터 수집 및 AI 요약은 정기 스케줄(00:00, 06:00, 12:00, 18:00 KST) 또는 독립된 파이썬 배치 스크립트(`tools/drain_ai_enrichment.py`)를 통해 안전한 예산 내에서 실행됩니다.
2. **클라이언트 의존성 제로**:
   - 사용자의 브라우저 접속이나 새로고침에 파이프라인 가공을 의존하지 않습니다.

---

## 4. 에이전트 자율 점검 체크리스트
에이전트는 작업 시 다음 5가지를 반드시 점검합니다:
- [ ] 로컬에 임의로 `investigations/` 신규 폴더 및 `metadata.json`을 생성하려 하고 있지 않은가?
- [ ] 프런트엔드 JS에 `while(true)` 형태의 백그라운드 API 폴링/워커 루프가 존재하는가?
- [ ] 외부 LLM API 연동부에 서킷 브레이커(3회 실패 시 즉각 중단)가 구현되어 있는가?
- [ ] 1회 수동 트리거 시 최대 처리량 캡(Max Batch Cap = 5)이 설정되어 있는가?
- [ ] 카테고리 집계가 임의의 배열 슬라이스가 아닌 DB SQL `GROUP BY` 기반인가?
