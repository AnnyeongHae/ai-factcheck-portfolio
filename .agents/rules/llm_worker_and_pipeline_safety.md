# 룰: LLM API 쿼터 보호 및 클라이언트 워커 엄격 금지 원칙 (LLM Worker & Pipeline Safety Rule)

## 1. 핵심 원칙: 브라우저는 View 계층이며, 배치 작업자(Batch Worker)가 아니다
- **클라이언트 무한 루프 금지**: 웹 브라우저(`app.js`) 내부에서 `while(true)` 또는 짧은 주기(`setInterval`)로 외부 AI API나 서버리스 엔드포인트(`/api/enrich-worker`)를 지속 호출하는 코드를 엄격히 금지합니다.
- **백그라운드 방치 누수 방지**: 사용자가 브라우저 탭을 열어두고 자리를 비웠을 때 무한 루프가 돌아 API 쿼터(OpenRouter 1,000req)와 DB 대역폭(Neon/Aiven Egress)을 고갈시키는 사고를 원천 방지해야 합니다.
- **수동 트리거 제한**: 클라이언트 측에서 AI 요약을 트리거하는 UI가 존재할 경우, 반드시 **1회 클릭당 최대 5건(Max Session Batch = 5)**으로 하드 캡을 두고, 배치 완료 시 즉시 정상 종료해야 합니다.

---

## 2. 외부 API 호출 및 서킷 브레이커(Circuit Breaker) 필수 원칙
1. **Bounded Retry (최대 2회 재시도 제한)**:
   - 외부 AI 모델(OpenRouter 무료 모델 등) 호출 시 실패(503, 429, Timeout)가 발생하면 최대 2회까지만 재시도합니다.
2. **Hard Circuit Breaker (연속 3회 실패 시 즉각 중단)**:
   - 연속 3회 실패(`consecutiveErrors >= 3` 또는 `consecutiveFallbacks >= 3`) 발생 시 **즉시 루프를 탈출(Break)**하고 서킷을 차단합니다.
   - 3초, 5초, 7초 단위로 계속 다시 찌르는 '재시도 폭풍(Retry Storm)' 행위를 절대 작성하지 않습니다.
3. **HTTP 429(Rate Limit / Quota Exhausted) 즉시 차단**:
   - HTTP 429를 수신하면 다른 폴백 모델로의 전환을 즉시 중단하고 해당 요청을 즉각 종료합니다.
4. **모델 캐스케이드(Cascade Fallback) 제한**:
   - 단일 엔드포인트 내에서 5개, 7개 이상의 모델을 연쇄 호출하지 않습니다. (최대 Primary 1개 + Fallback 1개로 제한하여 1회 요청당 API 소모를 통제)

---

## 3. 데이터 가공 파이프라인(ETL/Enrichment)의 정석 위치
1. **GitHub Actions 스케줄러(CI/CD) 배치 처리**:
   - 뉴스 수집 및 AI 요약/분석은 사용자의 브라우저 접속에 의존하지 않고, **GitHub Actions 정기 스케줄(00:00, 06:00, 12:00, 18:00 KST)** 또는 독립된 백엔드 배치 워커(`tools/drain_ai_enrichment.py`)에서 일괄 실행되어 정돈된 상태로 DB에 적재되어야 합니다.
2. **DB 트래픽 및 Egress 예산 보호**:
   - 매 루프마다 DB에 불필요한 개별 SELECT/UPDATE 쿼리를 날리지 않고, 트랜잭션 단위로 묶어서 처리합니다.

---

## 4. 에이전트 자율 점검 체크리스트
AI API 연동 및 클라이언트 기능 구현 시 에이전트는 다음 4가지를 반드시 확인합니다:
- [ ] 브라우저 JavaScript 코드에 `while(true)` 형태의 API 폴링/워커 루프가 존재하는가?
- [ ] 외부 LLM API 실패 시 무제한 재시도 대신 서킷 브레이커(3회 실패 시 영구 중단)가 구현되어 있는가?
- [ ] 1회 수동 트리거 시 최대 처리량 캡(Max Batch Cap)이 설정되어 있는가?
- [ ] API 호출 실패가 DB 풀스캔/트래픽 폭증으로 이어지지 않는가?
