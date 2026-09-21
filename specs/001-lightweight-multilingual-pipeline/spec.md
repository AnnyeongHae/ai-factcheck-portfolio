# Feature Specification: 100% Multilingual (KO·EN·ZH) & Ultra-Lightweight Pipeline

**Feature Directory**: `specs/001-lightweight-multilingual-pipeline`  
**Created**: 2026-09-21  
**Status**: Specified & Ready for Review  
**Governing Constitution**: `.specify/memory/constitution.md`

---

## 1. User Scenarios & Testing (Mandatory)

### User Story 1 - 100% Multilingual Enrichment of Every Ingested Item (Priority: P1)
사용자는 웹사이트를 방문했을 때, 방금 수집된 최신 AI/테크 뉴스와 오픈소스 모델들이 영어 원문으로 방치되지 않고 **자연스러운 한국어(KO), 영어(EN), 중국어(ZH) 3개 국어 제목, 1줄 훅, 3줄 핵심 요약(Key Takeaways)**으로 완벽하게 번역·정리된 상태로 열람할 수 있어야 한다.

- **Why this priority**: 본 서비스의 핵심 차별점이자 사용자의 절대적 요구사항(다국어 3개 국어 요약 전수 제공).
- **Independent Test**: Neon DB의 신규 레코드에 대해 Vercel 워커를 1회 호출하면, 3초 이내에 KO, EN, ZH 3개 국어 필드가 100% 채워지고 `is_classified = TRUE`로 갱신되어야 함.
- **Acceptance Scenarios**:
  1. **Given** 새로 수집된 영문 기사("DeepSeek releases V3...")가 DB에 `is_classified = FALSE` 상태로 존재할 때,
     **When** Vercel 워커(`/api/enrich-worker?limit=1`)가 호출되면,
     **Then** 3초 이내에 200 OK를 반환하고, `title_ko`, `hook_ko`, `key_takeaways_ko`(3개), `title_zh`, `hook_zh`, `key_takeaways_zh`(3개), `title_en`, `hook_en`, `key_takeaways_en`(3개)이 DB에 원자적으로 저장되어야 한다.
  2. **Given** 한국어 요약(`key_takeaways_ko`)이 생성될 때,
     **When** LLM 출력을 검증하면,
     **Then** 한글(Hangul) 문자가 반드시 포함되어야 하며, 중국어 간체자 한자만 단독으로 누출되는 현상이 차단되어야 한다.

---

### User Story 2 - Zero-Drop Orchestration by GitHub Actions (Priority: P1)
사용자가 직접 웹사이트에 접속하지 않아도, GitHub Actions가 정기 수집(00, 06, 12, 18시) 직후 '스마트 리모컨' 역할을 수행하여 **새로 수집된 모든 미분류 항목(약 15~25건)이 번역 완료될 때까지 1건씩 Vercel을 호출하여 100% 완주**해야 한다.

- **Why this priority**: 사용자가 사이트를 열기 전에 백그라운드에서 모든 번역이 완료되어 대기해야 하므로 필수적임.
- **Independent Test**: `python tools/orchestrate_enrichment.py`를 실행했을 때, 남은 미분류 건수가 0개가 될 때까지 1초 간격으로 순회 호출하고 정상 종료됨.
- **Acceptance Scenarios**:
  1. **Given** 20건의 신규 수집 데이터가 DB에 등록되어 있을 때,
     **When** Actions의 오케스트레이터 스크립트가 실행되면,
     **Then** 1초 간격으로 Vercel을 호출하며, 매 응답마다 `remaining_unclassified`가 감소하고, 0이 되면 50초 이내에 루프를 종료한다.
  2. **Given** 특정 1건 호출 도중 OpenRouter 일시적 503 또는 네트워크 에러가 발생했을 때,
     **When** 오케스트레이터가 에러를 수신하면,
     **Then** 프로세스가 크래시되지 않고 에러 로그를 남긴 후 다음 항목을 계속 처리하여 체인이 끊기지 않아야 한다.

---

### User Story 3 - GitHub Actions 수집기 I/O 초경량화 & 배포 분리 (Priority: P2)
데이터 수집 작업이 불필요하게 1분 이상 가상머신 시간을 낭비하지 않도록, Hacker News 수집 병목을 제거하고, 대중 소스(구글 뉴스 RSS, 유튜브 RSS, 레딧)를 포함해도 **기본 수집 단계가 10초 이내에 완료**되어야 한다.

- **Why this priority**: 월간 GitHub Actions 무료 시간(2,000분)의 90% 이상을 절약하고, CI/CD 안정성을 극대화하기 위함.
- **Independent Test**: `python tools/harvest_trends.py` 실행 시 10초 이내에 모든 소스(HN, HF, GitHub, ArXiv, Reddit, Google News, YouTube, GeekNews) 수집을 마쳐야 함.
- **Acceptance Scenarios**:
  1. **Given** Hacker News 수집이 시작될 때,
     **When** 기존 60회 순차 호출 대신 Algolia 검색 API 1회 호출을 수행하면,
     **Then** 0.5초 이내에 상위 50개 글이 JSON으로 파싱되어야 한다.
  2. **Given** 6시간 주기 크론 워크플로가 실행될 때,
     **When** 사이트 배포(`deploy-pages`) 단계가 생략되면,
     **Then** 워크플로 전체 소요 시간이 50초 이내로 단축되어야 한다.

---

### User Story 4 - Daily EOD 23:00 KST 핫 랭킹 자동 태깅 (Priority: P2)
매일 밤 23:00 KST(14:00 UTC)에 하루 동안 수집된 데이터의 델타($\Delta$)를 비교하여, 오늘 가장 폭발적으로 성장한 상위 10개 항목에 `curation_tier = 'DAILY_HOT'` 배지를 자동 부착하여 프론트엔드 최상단에 노출한다.

- **Why this priority**: 단순 최신순 나열을 넘어 '오늘 하루 인터넷에서 가장 핫했던 기술'을 한눈에 식별할 수 있는 사용자 가치 제공.
- **Independent Test**: `python tools/run_eod_digest.py` 실행 시 최근 24시간 스냅샷 델타를 계산해 상위 10건의 DB 플래그를 갱신함.

---

## 2. Edge Cases

- **EC-001 (OpenRouter 무료 쿼터 일일 1,000회 일시 소진)**:
  - 시스템은 크래시되지 않고 `status: 'quota_exhausted'`를 반환하며, 키워드 기반 카테고리 분류(`inferCategoriesAndArtifact`)를 안전망으로 수행.
- **EC-002 (신규 수집 건수가 비정상적으로 폭증할 때 - 50건 이상)**:
  - Actions 오케스트레이터에 `MAX_ITERATIONS = 30` 안전 상한선을 두어 Actions가 10분 타임아웃에 걸리는 것을 원천 방지.
- **EC-003 (동일 주제의 크로스 플랫폼 동시 수집)**:
  - `Canonical Key` 정규화로 URL이 달라도 동일 기술(예: `qwen-image-2.1`)이면 단일 클러스터로 집계하여 중복 요약 방지.

---

## 3. Functional Requirements (FR)

- **FR-001**: Vercel `api/enrich-worker.js`는 `limit=1` 요청 시 단 1개의 미분류 레코드만 가져와 배타적 잠금(`FOR UPDATE SKIP LOCKED`)을 걸어야 한다.
- **FR-002**: Vercel 워커는 `title_ko`, `hook_ko`, `key_takeaways_ko`(배열 3개), `title_en`, `hook_en`, `key_takeaways_en`(배열 3개), `title_zh`, `hook_zh`, `key_takeaways_zh`(배열 3개)를 반드시 JSON으로 반환 및 DB 커밋해야 한다.
- **FR-003**: `tools/harvest_trends.py`는 Hacker News 수집에 Algolia API(`https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=50`)를 사용해야 한다.
- **FR-004**: `tools/harvest_trends.py`는 구글 뉴스 RSS, 유튜브 테크 채널 RSS, 레딧(`r/technology`, `r/singularity`)을 신규 수집 채널로 포함해야 한다.
- **FR-005**: `tools/orchestrate_enrichment.py`는 Vercel 워커를 1초 간격으로 순회 호출하며, `remaining_unclassified == 0` 시 즉시 루프를 종료해야 한다.
- **FR-006**: `.github/workflows/deploy_pages.yml`의 6시간 크론은 `deploy-pages` 단계를 생략하고, `requirements-harvest.txt`로 의존성을 최소화해야 한다.

---

## 4. Success Criteria (SC)

- **SC-001 (속도)**: GitHub Actions 기본 수집 단계 소요 시간 $\le$ **10초**.
- **SC-002 (완전성)**: 1회 수집 시 유입된 신규 아이템의 다국어 3개 국어 요약 완료율 = **100%**.
- **SC-003 (안정성)**: Vercel 워커 1회 호출당 소요 시간 $\le$ **3.5초** (10초 타임아웃 발생률 0%).
- **SC-004 (비용)**: 유료 API 결제 금액 = **$0.00 / 월**.
