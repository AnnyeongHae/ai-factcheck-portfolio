# 2. 주장 분해 및 증거 수집 (Claim Decomposition & Evidence)

## 1. 감정/마케팅 노이즈 제거 및 원자적 명제 (Atomic Claims)

### Claim 1: [성능 및 벤치마크 주장]
- **명제**: DeepSeek 추론 모델이 AIME 2025/2026 수학 평가에서 88.4%를 기록하여 OpenAI o1(83.3%)을 능가했다.
- **속성**: 성능 / 벤치마크

### Claim 2: [하드웨어 요구사양 주장]
- **명제**: 풀(Full) 비양자화(Unquantized) 모델을 단일 RTX 4090 (24GB VRAM)에서 초당 120토큰으로 구동할 수 있다.
- **속성**: 하드웨어 효율성 / VRAM

### Claim 3: [오픈소스 라이선스 주장]
- **명제**: 학습 레시피와 가중치를 포함하여 완전한 MIT 오픈소스 라이선스로 공개되었다.
- **속성**: 오픈소스 / 라이선스

---

## 2. 증거 수집 및 Tier 매핑 (Multi-Hop Evidence)

### Evidence for Claim 1 (AIME 88.4% 점수)
- **출처 1 (Tier 1 - 원저자 논문/GitHub Table 3)**:
  - 저자가 공개한 공식 ArXiv 논문에서 AIME 점수는 실제로 **88.4%**로 기재됨.
  - **결정적 단서**: 논문 각주 4번에 `Pass@64 with Cons-Maj@64` (64회 샘플링 다수결) 조건임이 명시됨. 단일 패스(Pass@1) 기준 점수는 **79.8%**임.
  - 반면 비교군으로 사용된 OpenAI o1의 83.3%는 `Pass@1 single run` 기준임.
  - 신뢰도 가중치: 0.95

### Evidence for Claim 2 (단일 RTX 4090 구동)
- **출처 1 (Tier 1 - SafeTensors 헤더 및 아키텍처 감사)**:
  - 플래그십 풀 모델은 **671B 총 파라미터(활성 37B MoE)** 아키텍처임.
  - BF16 원본 가중치 크기는 약 **700GB**에 달함.
  - 단일 24GB GPU에 올라가는 모델은 풀 모델이 아니라 증류된 **Distill 8B 모델** 또는 **1.58-bit 극단 양자화 버전**뿐임.
  - 신뢰도 가중치: 1.0 (물리적 VRAM 한계)

### Evidence for Claim 3 (MIT 라이선스)
- **출처 1 (Tier 1 - GitHub repo LICENSE & Model Card)**:
  - 코드는 MIT 라이선스이나, 모델 가중치는 `DeepSeek Model License Agreement`(일정 사용량 이상 라이선스 동의 및 특정 유해 사용 금지 조항 포함)가 적용됨.
  - 순수 OSI 승인 완전 MIT 오픈소스는 아님.
  - 신뢰도 가중치: 0.95

---

## 3. 오염 및 하네스 감사 (Contamination & Harness Audit)
- **벤치마크 하네스 변조**:
  - `Pass@64 Majority Vote`와 `Pass@1`을 동일 선상에서 단순 비교하는 전형적인 **Harness Manipulation (하네스 왜곡)** 확인.
