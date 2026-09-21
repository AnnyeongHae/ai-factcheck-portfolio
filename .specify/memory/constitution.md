# AI Fact-Check & Trend Radar Project Constitution

## Core Principles

### I. 100% DB-First 단일 진실 원천 (Single Source of Truth)
- 본 프로젝트의 모든 원천 데이터(`raw_trends_inbox`, `verified_factchecks`, `ecosystem_technical_analyses`)의 생성·수정·조회는 오직 **Neon PostgreSQL Cloud DB**를 기준으로 한다.
- 로컬 파일 수작업(임시 JSON 생성, 대용량 `data.json` 정적 덤프 등)에 의존하는 레거시 방식을 엄격히 금지한다.
- 깃허브 저장소는 오직 순수 소스코드, 워크플로, 규칙만 추적한다.

### II. $0.00 유지 비용 원칙 (Zero-Cost Guarantee)
- 모든 외부 API 및 클라우드 서비스는 무료 티어 할당량 내에서만 영구 동작하도록 설계한다.
- OpenRouter 무료 모델 (`inclusionai/ling-3.0-flash-sante:free`, `openrouter/free` 등, 일일 1,000회 한도) 활용.
- GitHub Actions 월간 2,000분 한도 중 10% 미만(월 200분 이내) 소비 보장.
- Neon DB 월간 Egress 5GB 보호 (Vercel Edge CDN SWR 캐싱 필수).

### III. 다국어(KO·EN·ZH) 3개 국어 무결성 원칙 (Multilingual Invariance)
- 수집된 모든 신규 테크/뉴스 데이터는 예외 없이 **한국어(KO), 영어(EN), 중국어(ZH)** 3개 국어의 정제된 제목, 1줄 훅(Hook), 그리고 **3줄 핵심 요약(Key Takeaways)**이 생성되어야 한다.
- 한 언어의 문자가 다른 언어로 누출(예: 한국어 요약에 한자 누출)되어서는 안 되며, 언어별 엄격한 유효성 가드레일을 통과해야 한다.

### IV. 서버리스 타임아웃 방어 & 1건 단위 처리 (Serverless Timeout Safety)
- Vercel Serverless 무료 티어의 10초 타임아웃을 방어하기 위해, AI 인리치먼트 처리는 **1회 호출당 1건(`limit=1`)** 단독 처리를 원칙으로 한다.
- 단일 호출 소요 시간을 2.5~3.5초 이내로 묶어 타임아웃 발생률 0%를 유지한다.

### V. 데이터 수집 파이프라인과 사이트 배포의 완전 분리 (Decoupled Pipeline)
- 6시간 주기 데이터 수집 크론 작업은 데이터를 긁어 Neon DB에 넣고 AI 번역을 완주하는 것만 담당한다.
- 정적 사이트 재빌드 및 배포(`actions/deploy-pages`)는 프론트엔드 코드 Git push 시에만 수행하며, 수집 크론에서는 일절 실행하지 않는다.

## Governance
- 본 헌법(Constitution)은 프로젝트 내의 모든 구현 계획(`plan.md`), 작업 명세(`tasks.md`), 및 소스코드보다 상위의 효력을 갖는다.
- 에이전트는 본 헌법에 위배되는 코드(예: investigations/ 폴더 임의 생성, 다국어 필드 누락, 묶음 배치로 인한 타임아웃 유발 등)를 작성할 수 없다.

**Version**: 1.0.0 | **Ratified**: 2026-09-21
