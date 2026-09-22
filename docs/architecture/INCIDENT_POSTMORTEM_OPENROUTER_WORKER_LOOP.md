# 심층 포스트모템 및 재발 방지 아키텍처 보고서
## [장애 분석] OpenRouter 1,000회 무료 쿼터 소각 및 Neon DB 5GB 대역폭 고갈 사건

---

### 1. 사건 개요 (Incident Overview)

* **발생 일시**: 2026년 9월 21일 ~ 22일
* **증상**:
  1. 브라우저 콘솔에 `[AutoWorker] AI models busy or timed out. Retrying in 3s (attempt 1)...` 로그가 수십 회 반복된 후, `[AutoWorker] OpenRouter daily free quota (1,000 requests) exhausted. Halting background worker until 09:00 KST reset.` 경고 발생.
  2. Neon Cloud DB에서 `100% of its monthly 5 GB network transfer allowance used. Your compute is at risk of suspension` 통보 수신.
  3. 실시간 대시보드에서 AI 요약이 진행되지 않고 멈추는 현상 발생.

---

### 2. 근본 원인 정밀 분석 (Root Cause Analysis - 5 Whys)

```
[Why 1] 왜 OpenRouter 일일 무료 쿼터 1,000회가 단 몇 시간 만에 전부 소진되었는가?
  ↳ 브라우저 클라이언트(`src/js/app.js`)의 `startContinuousAiWorker()`가 사용자가 웹페이지를 켜놓고 있는 동안 `while(true)` 무한 루프로 `/api/enrich-worker?limit=1`을 지속 호출했음.

[Why 2] 왜 AI 모델이 계속 실패하고 지연되었는가?
  ↳ OpenRouter 무료 엔드포인트(`free` 태그 모델들)는 전 세계 트래픽 집중으로 인해 503(Service Unavailable), 429(Rate Limit), 10초 타임아웃이 빈번함.

[Why 3] 왜 1회의 클라이언트 호출이 1,000회의 쿼터를 그렇게 빨리 태웠는가?
  ↳ 백엔드 `/api/enrich-worker.js`에 7개 모델 연쇄 폴백(Cascade Fallback) 루프가 있어, 1개 모델 실패 시 다음 모델을 연쇄 호출함 (1회 요청당 최대 7회 API 소모).
  ↳ 클라이언트는 `partial_fallback` 응답을 받으면 3초, 5초, 7초 뒤에 즉시 다시 호출함 (재시도 폭풍: Retry Storm).
  ↳ 150번의 루프만으로도 150 * 7 = 1,050회 API 호출이 발생하여 1,000회 일일 한도가 즉각 고갈됨.

[Why 4] 왜 Neon DB 5GB 대역폭까지 함께 고갈되었는가?
  ↳ 클라이언트의 무한 루프가 매 3~5초마다 Vercel Serverless를 때릴 때마다, `/api/enrich-worker`와 `/api/stats`가 Neon DB에 연결하여 `raw_trends_inbox`의 큰 JSONB 컬럼을 조회하고 `UPDATE` 쿼리를 날렸음.
  ↳ 수천 번의 DB 핸드셰이크와 대용량 JSON 데이터 왕복으로 월 5GB 무료 Egress가 며칠 만에 100% 소각됨.

[Why 5] 왜 이런 구조가 브라우저에 들어가 있었는가?
  ↳ GitHub Actions의 4분 실행 시간 제한을 우회하기 위해, 서버에서 처리해야 할 배치 가공(ETL Enrichment Drain)을 '브라우저 클라이언트 백그라운드 워커'에 떠넘기는 치명적인 아키텍처 역전(Inverted Architecture)이 발생했기 때문임.
```

---

### 3. 핵심 안티패턴 3가지 (Anti-Patterns Identified)

#### 안티패턴 1: Client-Side Batch Worker (클라이언트를 배치 워커로 오용)
* **문제점**: 브라우저는 화면을 보여주는 View 계층입니다. 사용자의 세션 지속 시간, 탭 활성화 여부, 네트워크 상태가 제각각인 브라우저에 `while(true)` 루프를 심어 백그라운드 데이터 가공을 시키면 안 됩니다.
* **결과**: 사용자가 탭을 켜두고 자리를 비우면 브라우저가 'DDoS 공격기'로 변하여 외부 API 쿼터와 DB Egress를 무한히 태웁니다.

#### 안티패턴 2: Missing Circuit Breaker & Retry Storm (서킷 브레이커 부재 및 재시도 폭풍)
* **문제점**: 외부 무료 API가 과부하(503/429) 상태일 때, '성공할 때까지 3초마다 계속 찌르는' 코드는 장애를 해결하는 것이 아니라 장애를 가속화합니다.
* **결과**: 3회 실패 시 영구 중단하는 하드 서킷 브레이커가 없어 1,000회 쿼터가 낭비되었습니다.

#### 안티패턴 3: Deep Model Cascading (과도한 모델 연쇄 폴백)
* **문제점**: 1회의 서버리스 함수 요청 안에서 7개의 모델을 `for...of`로 전수 순회하며 찔렀습니다.
* **결과**: 단 1회의 프런트엔드 요청이 7번의 OpenRouter API 콜을 소모하여 쿼터 소진 속도를 7배로 가속했습니다.

---

### 4. 재발 방지 해결 조치 (Architecture Fixes Applied)

```mermaid
flowchart TD
    subgraph Legacy [이전 안티패턴 구조]
        Client1[웹 브라우저] -->|while 무한 루프 / 3초마다| Worker1[/api/enrich-worker]
        Worker1 -->|7개 모델 전수 연쇄 호출| OR1[OpenRouter 1,000회 쿼터 순식간 고갈]
        Worker1 -->|매 루프마다 무제한 쿼리| DB1[Neon DB 5GB 대역폭 소각]
    end

    subgraph Modern [개선된 안전 아키텍처]
        Client2[웹 브라우저] -->|수동 클릭 시만 작동| Guard[안전 가드: Max 5건 세션 캡]
        Guard -->|1회성 마이크로 배치| Worker2[/api/enrich-worker]
        Worker2 -->|Primary 1개 + Fallback 1개만| OR2[OpenRouter API 보호]
        Worker2 -->|연속 3회 실패 시| CB[Hard Circuit Breaker 즉각 차단 & 쿨다운]
        GHA[GitHub Actions 정기 스케줄] -.->|일괄 배치 정돈| DB2[Aiven Cloud DB Egress 보호]
    end
```

#### 1) 클라이언트 측 하드 서킷 브레이커 & 세션 캡 도입 (`src/js/app.js`)
* **Hard Circuit Breaker**: 연속 실패(`consecutiveFallbacks >= 3` 또는 `consecutiveErrors >= 3`) 발생 시 루프를 즉시 영구 종료(`break`)하고 UI에 "AI 서비스 지연으로 자동 일시정지됨" 표시.
* **Session Safety Cap**: 수동으로 실행하더라도 1회 세션당 **최대 5건(Max Session Batch = 5)**만 처리하고 즉시 정상 종료. 사용자가 브라우저를 방치해도 1,000회 소진 불가.
* **자동 실행 원천 차단**: 페이지 진입 시 자동으로 워커가 돌지 않도록 보장.

#### 2) 서버리스 엔드포인트 방어 (`api/enrich-worker.js`)
* **HTTP 429 즉시 루프 탈출**: 429(Rate Limit / Quota Exhausted) 수신 시 다른 모델로 넘어가지 않고 즉시 요청 중단.
* **Cascade Fallback 축소**: 최대 모델 시도 횟수를 7개에서 **2개(Primary 1개 + Fallback 1개)**로 엄격 제한.

#### 3) 프로젝트 영구 룰 명문화 (`AGENTS.md`, `.agents/rules/llm_worker_and_pipeline_safety.md`)
* 모든 AI 에이전트가 앞으로 코드를 작성할 때 다음 원칙을 위반하지 않도록 시스템 룰로 강제:
  1. 클라이언트 브라우저 내 무한 루프 워커 작성 금지.
  2. 외부 API 호출 시 Bounded Retry(최대 2회) 및 Circuit Breaker(연속 3회 실패 시 즉각 탈출) 필수.
  3. ETL/Enrichment는 CI/CD 스케줄 배치에서 처리.
