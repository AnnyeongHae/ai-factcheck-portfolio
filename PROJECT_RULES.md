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
