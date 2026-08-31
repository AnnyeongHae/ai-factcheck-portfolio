# [Repository 검증 템플릿]

- **대상 저장소 (Target Repo)**: `https://github.com/org/repo`
- **조사 개시일**: YYYY-MM-DD
- **책임 에이전트/조사관**: Antigravity SOTA Factchecker
- **상태**: [ IN PROGRESS / VERIFIED / REFUTED / INCONCLUSIVE ]

---

## 1. 개요 및 배경
- 본 조사는 해당 GitHub 저장소가 주장하는 주요 기능, 성능 수치, 벤치마크 결과, 라이선스의 진위 여부를 기술적으로 감사(Audit)하기 위해 시작되었습니다.

## 2. 조사 파일 목차
1. [claim_analysis.md](./claim_analysis.md): 리포지토리 README/논문에서 주장하는 핵심 클레임 분해
2. [code_audit.md](./code_audit.md): 실제 소스코드, 모델 가중치, 라이선스, CI/CD 재현성 검증
3. [verdict_report.md](./verdict_report.md): 최종 기술 검증 판정서 및 리포트
