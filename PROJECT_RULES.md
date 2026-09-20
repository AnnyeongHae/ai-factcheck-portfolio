# AI FactCheck Hub - 에이전트 핵심 운영 원칙 (Agent Rules)

## 🚨 영구 금지사항 (Strict Prohibitions)
1. **외부 API 토큰을 활용한 심층 팩트체크 리포트 자동 생성 절대 금지**:
   - investigations/ 하위의 심층 팩트체크 도시에(Dossier)는 오직 사용자와 Antigravity 에이전트 간의 로컬 대화(페어 프로그래밍) 및 소스코드 직접 분석을 통해서만 작성되어야 합니다.
   - 백그라운드 워커(factcheck_worker.py), GitHub Actions CI, 또는 자동화 스크립트에서 외부 유료 API 토큰(gemini-3.6-flash 등)을 호출하여 심층 도시에를 일괄 생성하는 행위는 엄격히 금지됩니다.

## 💡 유료 API 허용 범위 (Allowed Batch Scope)
1. **인박스 후보 3개국어 번역·요약·분류**:
   - 엔진: Google Gemini 공식 Batch API (batch_manager.py)
   - 모델: models/gemini-3.6-flash
   - 비용 정책: 50% 할인 적용, 500개 안건당 약 160원 수준 유지.
   - 특징: 비동기 배치로 토큰 비용을 최소화하며, 퀄리티와 지능을 보장함.

## 💾 100% DB-First 단일 진실 원천(SSOT) 아키텍처 원칙 (DB-First SSOT Architecture)

1. **Neon PostgreSQL Cloud DB (유일한 단일 진실 원천 / Single Source of Truth)**:
   - 모든 팩트체크(`verified_factchecks`), 원자적 명제(`factcheck_atomic_claims`), 기술 대안(`factcheck_alternatives`), 바이럴 신호(`factcheck_community_signals`), 기술 생태계 분석(`ecosystem_technical_analyses`), 실시간 인박스(`raw_trends_inbox`)의 유일한 정본(SSOT)입니다.
   - **신규 팩트체크 등록 시 로컬 파일 수작업 금지**: 사용자와의 분석이 완료된 팩트체크는 로컬 `investigations/` 디렉토리에 폴더나 `metadata.json`을 새로 만들지 않고, **오직 Neon DB에 직접 INSERT/UPSERT**합니다.
   - 큐레이션 분류: 사용자가 직접 지정하거나 요청한 안건은 `curation.discovery_mode = 'USER_CURATED'`로 명시합니다.

2. **Edge CDN & 프런트엔드 데이터 서빙 (0.05초 초고속 하이드레이션)**:
   - 프런트엔드(`app.js`)는 최초 로딩 시 Vercel Edge Serverless API(`/api/portfolios`)를 통해 Neon DB로부터 실시간 도시에 전체를 직접 하이드레이션(Hydration)합니다.
   - 고성능 SWR 캐싱(`Cache-Control: public, s-maxage=600, stale-while-revalidate=86400`)을 적용하여 99% 사용자는 글로벌 에지 CDN에서 0.05초(30~80ms) 내에 데이터를 즉시 서빙받으며, Neon DB Egress 한도(5GB)를 완벽히 보호합니다.
   - 정적 빌드 파일(`docs/data.json` 등)은 네트워크 단절 시를 위한 비상용 오프라인 스냅샷에 불과하며, 일상적인 포트폴리오 추가 시 수작업으로 재생성하여 Git에 푸시하지 않습니다.

3. **Remote Git (GitHub origin/main - 순수 소스코드 관리)**:
   - 오직 순수 소스코드(.py, .js, .html 템플릿, .css), 워크플로(.yml), 규칙 및 설정(.md, .json 스키마)만 Git으로 관리합니다.
   - 개별 팩트체크 폴더/JSON 덤프 파일(`investigations/*/metadata.json` 등)을 수작업으로 Git에 커밋하거나 푸시하는 것은 엄격히 금지됩니다 (`.gitignore`로 격리).

