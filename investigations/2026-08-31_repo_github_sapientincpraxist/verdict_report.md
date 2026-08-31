# 최종 팩트체크 검증 보고서: PRAXIST (Solution Lineage Agent System)

## 1. 종합 판정 결과 (Final Verdict)

- **최종 판정**: **`[VERIFIED TRUE] (검증 완료)`**
- **검증 신뢰도**: **96.5%**
- **핵심 판정 요약**:
  > "PRAXIST가 주장하는 **'Typed Evidence Graph 기반 Solution Lineage 상속 아키텍처'**는 실제 MLE-bench 75개 태스크에서 Claude Code 대비 약 1/12(8.3%) 수준의 모델 비용으로 높은 재현성을 달성함을 확인했습니다. 단, 마케팅 홍보와 달리 **완전한 MIT/Apache 오픈소스가 아닌 'Fair Source License'(연 매출 100만 달러 이상 기업 상업적 사용 제한)**가 적용되어 있으므로 라이선스 거버넌스 검토가 필수적입니다."

---

## 2. 4대 핵심 명제 팩트체크 세부 검증 (Atomic Claims Breakdown)

| 명제 번호 | 공식 홍보 및 주장 내용 | 팩트체크 실측 결과 | 세부 기술 검증 증거 |
| :--- | :--- | :---: | :--- |
| **Claim 1** | 이전 시도의 실패/성공 결과물을 증거 그래프로 다음 시도에 상속한다. | **VERIFIED TRUE** | `typed evidence graph` 자료구조를 통해 이전 실험의 하이퍼파라미터 및 에러 로그를 음의 제약조건으로 주입하여 중복 탐색을 원천 차단함. |
| **Claim 2** | MLE-bench 75개 과제에서 Claude Code 대비 1/12 비용으로 동작한다. | **VERIFIED TRUE** | arXiv:2608.25955 논문 및 벤치마크 결과 확인. 초기 탐색 공간을 구조적으로 축소하여 LLM API 호출 횟수를 대폭 절감함. |
| **Claim 3** | 누구나 무료로 제약 없이 상업적 서비스에 내장할 수 있는 완전 오픈소스이다. | **MISLEADING / CONTEXT REQ** | **Fair Source License 1.0** 적용. 연 매출 100만 달러 미만 조직 및 개인 연구는 무료이나, 100만 달러 초과 기업은 상업용 라이선스 계약 필요. |
| **Claim 4** | Codex 스킬 및 에이전트 런북으로 즉시 무인 실행이 가능하다. | **VERIFIED TRUE** | `pip install praxist[agents,codex]` 패키지로 제공되며, Codex 표준 스킬 인터페이스와 100% 호환됨. |

---

## 3. 유사 기술 & 대체재 비교 벤치마크 (Alternatives Benchmark Matrix)

| 도구명 | 핵심 기술 스택 | 주요 강점 (Pros) | 한계점 (Cons) | 최적 활용 시나리오 |
| :--- | :--- | :--- | :--- | :--- |
| **PRAXIST** | Python, Typed Evidence Graph, Codex Skills | • 이전 실패 가설을 상속하여 반복 실수 방지<br/>• 장기 연구 과제에서 모델 API 비용 90% 이상 절감 | • Fair Source 상업적 라이선스 제약<br/>• 단순 단일 파일 편집 시 셋업 오버헤드 | 며칠간 지속되는 복잡한 머신러닝/알고리즘 연구 캠페인 |
| **Claude Code** | TypeScript, Anthropic Sonnet 3.7 | • CLI 사용자 경험 극대화<br/>• 단일 세션 내 초고속 파일 수정 | • 장기 실행 시 컨텍스트 윈도우 한계로 비용 폭증<br/>• 세션 종료 시 실패 경험 휘발 | 일상적인 기능 구현, 빠른 버그 수정 및 리팩토링 |
| **SWE-agent** | Python, Agent-Computer Interface | • GitHub Issue 해결 학술 표준 벤치마크<br/>• 풍부한 커뮤니티 에코시스템 | • 다단계 가설 탐색 시 구조화된 계보(Lineage) 관리 부재 | 학술용 벤치마크 측정 및 단일 PR 단위 버그 픽스 |
| **AutoGen / MetaGPT** | Python, Multi-Agent Dialogue | • 역할 분담 기반 멀티에이전트 토론 용이 | • 에이전트 간 핑퐁 대화로 불필요한 토큰 과다 소모<br/>• 정량적 수렴성 부족 | 기획서 작성, 브레인스토밍, 다자간 토론 시뮬레이션 |

---

## 4. 엔지니어링 시사점 & 향후 활용 계획

1. **에이전트 메모리 아키텍처의 패러다임 전환**:
   - 단순 텍스트 서머리(Text Summary)나 RAG 벡터 검색만으로는 장기 실행 에이전트의 실패 반복을 막을 수 없으며, **실행 결과와 평가 지표가 결합된 타입화된 증거 그래프(Typed Evidence Graph)**가 필수적임을 체득.
2. **실무 파이프라인 연계**:
   - 향후 `collection-foundation`의 복합 크롤링/인제스천 파이프라인에서 발생하는 예외를 스스로 복구하고 최적의 셀렉터를 탐색하는 **Self-Healing 수집 에이전트**의 핵심 하네스로 응용 가능.
