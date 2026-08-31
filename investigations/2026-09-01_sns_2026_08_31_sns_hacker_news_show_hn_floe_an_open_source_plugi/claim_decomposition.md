# 2. 주장 분해 및 증거 수집 (Claim Decomposition & Evidence)

## 1. 감정/마케팅 노이즈 제거 및 원자적 명제 (Atomic Claims)

### Claim 1: [핵심 사실 명제]
- **명제**: 
- **속성**: [ 성능 / 기능 / 비용 / 라이선스 / 출시 일정 ]

### Claim 2: [비교 대상 관련 명제]
- **명제**: 
- **속성**: [ 타 모델 대비 우위 / 벤치마크 점수 비교 ]

---

## 2. 증거 수집 및 Tier 매핑 (Multi-Hop Evidence)

### Evidence for Claim 1
- **출처 1 (Tier 1)**: [공식 ArXiv 논문 / GitHub PR / LiveBench 데이터]
  - 발견 내용: 
  - 신뢰도 가중치: 0.95
- **출처 2 (Tier 2)**: [독립 기술 블로그 / 서드파티 재현]
  - 발견 내용: 
  - 신뢰도 가중치: 0.80

### Evidence for Claim 2
- **출처 1 (Tier 1)**: 
  - 발견 내용: 
- **출처 2 (Tier 3)**: [Reddit 실사용자 토론]
  - 발견 내용: 

---

## 3. End-to-End 파이프라인 원가 분석 (Unit Economics Audit)
*`python tools/estimate_pipeline_cost.py`를 활용하여 1회 실행/1분 영상/1개 작업당 실질 API 원가를 산출합니다.*

- **대본 생성 (LLM)**: $X.XXXX / 회
- **음성 합성 (TTS)**: $X.XXXX / 회
- **영상/에셋 생성 (Video/Image API)**: $XX.XX / 회 (Higgsfield, Seedance, Kling, Pexels 등)
- **Reject Ratio(재시도 배율, 기본 1.5x) 반영 실질 단가**: **$XX.XX / 회**
- **월간 N회(예: 30편) 양산 시 예상 총액**: **$XXX.XX / 월**

---

## 4. 오염 및 하네스 감사 (Contamination & Harness Audit)
- **벤치마크 데이터 유출(Contamination T1~T4) 가능성**: [ LOW / MEDIUM / HIGH ]
- **프롬프트 하네스 변조 여부**: 
- **공식 리더보드 일치 여부**: 
