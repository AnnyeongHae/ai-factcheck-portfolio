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

## 💾 3계층 데이터 아키텍처 및 저장소 분리 원칙 (3-Tier Storage Hierarchy)
1. **Local Disk (원천 저장고 / Primary Origin)**:
   - 개발자 및 에이전트의 작업 원본(`investigations/`, `inbox/`, `docs/` 지식 문서, 소스코드).
   - 로컬 파일은 임의로 삭제하지 않고 온전히 보존합니다.
2. **Neon PostgreSQL Cloud DB (1차 저장소 & 백업 & 프런트엔드 데이터 소스)**:
   - 실시간 수집 인박스(`raw_trends_inbox`), 정밀 팩트체크(`verified_factchecks`), 기술 생태계 분석(`ecosystem_technical_analyses`)의 실시간 단일 진실 원천(Single Source of Truth).
   - 대시보드 빌드 스크립트(`build_dashboard.py`)는 로컬 파일이 아닌 Neon DB에서 직접 쿼리하여 프런트엔드 데이터를 렌더링합니다.
   - 분석 및 수집 완료 시 즉시 Neon DB에 UPSERT 반영해야 합니다.
3. **Remote Git (GitHub origin/main - 순수 소스코드 관리)**:
   - 오직 순수 소스코드(.py, .js, .html 템플릿, .css), 워크플로(.yml), 규칙 및 설정(.md, .json 스키마)만 관리합니다.
   - 대용량 데이터 파일(JSON 덤프, 크롤링 피드 939+개 등)을 Git에 커밋하거나 푸시하는 것은 엄격히 금지됩니다 (`.gitignore`로 격리).
   - GitHub Actions CI 러너는 데이터를 Git에 다시 push하지 않으며, 산출물은 `upload-pages-artifact`로 GitHub Pages에 직접 배포합니다.
