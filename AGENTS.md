# 룰: DB-First 단일 진실 원천(SSOT) 아키텍처 원칙 (DB-First Architecture Rule)

## 1. 핵심 원칙: Neon DB가 유일한 정본(Single Source of Truth)
- 본 프로젝트는 **100% DB-First 아키텍처**로 전환되었습니다.
- 모든 데이터(정밀 팩트체크 erified_factchecks, 기술 분석 ecosystem_technical_analyses, 인박스 
aw_trends_inbox 등)의 생성·수정·조회의 기준점은 오직 **Neon PostgreSQL Cloud DB**입니다.
- 로컬 파일 수작업(metadata.json 생성, 로컬 디렉토리 아카이빙 등)에 의존하는 레거시 방식을 절대 반복하지 않습니다.

---

## 2. 신규 팩트체크 및 분석 등록 시 필수 절차
1. **Neon DB 직접 등록 (Direct DB Insertion)**:
   - 사용자와의 페어 프로그래밍 또는 심층 분석이 완료된 팩트체크는 로컬 investigations/ 폴더를 새로 만들지 않고, **Neon PostgreSQL DB에 직접 INSERT/UPSERT**합니다.
   - 대상 테이블:
     * erified_factchecks (메인 도시에 메타데이터, 훅, 총평 등)
     * actcheck_atomic_claims (원자적 주장 및 검증 증거)
     * actcheck_alternatives (대안 기술 스택 비교)
     * actcheck_community_signals (커뮤니티 바이럴 원문 및 반응)
   - curation.discovery_mode: 사용자가 직접 지정하거나 요청한 건은 반드시 'USER_CURATED'로 등록합니다.

2. **로컬 파일 및 Git 커밋 금지**:
   - investigations/*/metadata.json 또는 대용량 데이터 JSON 파일을 새로 만들어 Git에 커밋하는 행위를 엄격히 금지합니다.
   - Remote Git(origin/main)은 오직 **순수 소스코드(.py, .js, .html, .css), CI 워크플로(.yml), 규칙/설정(.md)**만 추적합니다.

---

## 3. 프런트엔드 서빙 원칙: Edge CDN SWR 캐싱
1. **API 우선 서빙**:
   - 프런트엔드(pp.js)는 최초 부트스트랩 시 Vercel Edge Serverless API(/api/portfolios)를 통해 Neon DB에서 실시간 데이터를 즉시 하이드레이션(Hydration)합니다.
   - Cache-Control: public, s-maxage=600, stale-while-revalidate=86400 헤더를 통해 글로벌 CDN 에지에서 0.05초(30~80ms) 내에 고속 서빙되며, Neon DB Egress 한도(5GB)를 완벽히 보호합니다.
2. **정적 빌드 파일(data.json)의 역할**:
   - data.json은 오프라인 비상용 Fallback 스냅샷일 뿐이며, 일상적인 신규 포트폴리오 추가 시마다 로컬에서 수동으로 재생성하여 Git에 올리지 않습니다.

---

## 4. 에이전트 자율 점검 체크리스트
새로운 팩트체크 또는 기술 분석 요청을 수행할 때 에이전트는 다음 3가지를 반드시 확인합니다:
- [ ] 로컬에 임의로 investigations/ 신규 폴더 및 metadata.json을 생성하여 Git에 커밋하려 하고 있지 않은가?
- [ ] Neon DB에 테이블 스키마에 맞게 직접 UPSERT를 완료하였는가?
- [ ] Vercel API(/api/portfolios)를 통해 실시간으로 조회가 가능한지 확인하였는가?
