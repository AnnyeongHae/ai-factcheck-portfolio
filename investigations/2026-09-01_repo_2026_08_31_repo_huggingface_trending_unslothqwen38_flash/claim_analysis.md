# 1. 저장소 핵심 클레임 분석 (Claim Analysis)

## 1. 저장소 기본 정보
- **Repo URL**: 
- **커밋 해시 (검증 기준)**: 
- **스타(Star) 수 / 포크(Fork) 수**: 
- **릴리즈 버전**: 

---

## 2. 원자적 명제 분해 (Atomic Claims)

### Claim 1: [핵심 성능/벤치마크 주장]
- **주장 내용**: (예: "MMLU-Pro에서 82.5% 달성")
- **주장 출처**: [README.md L#45 / Paper Table 1]
- **검증 기준 (Verification Criteria)**:
  - 평가 하네스(Zero-shot vs Few-shot)
  - 벤치마크 오염(Contamination) 여부
  - 독립 제3자 리더보드 등재 여부

### Claim 2: [아키텍처/효율성 주장]
- **주장 내용**: (예: "단일 24GB VRAM GPU에서 양자화 없이 서빙 가능")
- **주장 출처**: [README.md L#112]
- **검증 기준**: 메모리 풋프린트, KV-Cache 크기, 컨텍스트 윈도우

### Claim 3: [오픈소스 / 라이선스 주장]
- **주장 내용**: (예: "Apache 2.0 완전 오픈소스")
- **주장 출처**: [LICENSE 파일 및 Model Weights Card]
- **검증 기준**: 코드 라이선스와 모델 가중치 라이선스 일치 여부, 상업적 사용 제한 조항(Non-commercial clauses) 유무
