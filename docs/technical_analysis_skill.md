# Skill: Technical Ecosystem Evaluator (기술적 생태계 심층 분석 방법론)

이 문서는 Antigravity 에이전트가 모든 프로그래밍 언어, 프레임워크, 도구, 큐레이션 저장소를 분석할 때 준수해야 하는 **엄밀한 기술적 분석 표준 가이드라인**이다.

---

## 1. 🚨 절대 금기 사항 (Anti-Patterns to Avoid)

1. **자화자찬식 비교 금지 (No Self-Promoting Comparisons)**:
   - "A의 한계 vs 우리 허브의 해결책"과 같이 플랫폼 자체를 홍보하거나 우위를 주장하는 주관적 비교를 엄격히 금지한다.
2. **단순 기능 나열 지양 (No Superficial Feature Listing)**:
   - README의 마케팅 문구("가장 빠름", "혁신적임")를 복사해 나열하는 것을 금지한다.
3. **독립된 점(Point) 분석 금지**:
   - 어떤 도구가 독립적으로 존재한다고 보지 말고, 반드시 기저 플랫폼(Base Platform)과의 상호작용 및 의존성 계보 안에서 파악한다.

---

## 2. 🏛️ 핵심 분석 프레임워크: Standard vs Ecosystem

모든 기술 생태계 분석은 다음의 4가지 축을 기준으로 기저 표준(Base Standard)과 확장 생태계(Third-Party Ecosystem)를 상호 대조 분석한다:

```
[ 기저 표준 언어 / 런타임 (Base Standard) ]
          vs
[ 서드파티 확장 생태계 (Third-Party Ecosystem) ]
```

### 축 1: 아키텍처 및 철학적 트레이드오프 (Philosophy & Constraints)
- **표준 라이브러리(StdLib)**의 설계 철학 (예: Python의 *Batteries Included*, 하위 호환성 보존, 1년 주기 릴리즈, 안전한 범용성).
- **서드파티 생태계**의 설계 철학 (예: 고성능 도메인 특화, C/Rust FFI 확장, 빠른 파괴적 혁신).

### 축 2: 성능 및 런타임 병목 (Performance & Memory Bottlenecks)
- 표준 내장 모듈이 갖는 근본적 물리적 한계 (GIL, CPython 바이트코드 인터프리터 오버헤드, I/O 블로킹).
- 서드파티 생태계가 이를 극복하기 위해 도입한 저수준 기법 (SIMD 가속, Rust PyO3 메모리 제로카피, Libuv 이벤트 루프, GPU 텐서 가속).

### 축 3: 4단계 진화 계보 (4-Stage Lineage Evolution)
- 특정 문제 영역(HTTP, DOM 파싱, 직렬화, 데이터프레임)에서 표준 모듈이 어떻게 서드파티 1세대 ➔ 2세대 ➔ 3세대 SOTA로 대체되어 왔는지의 진화 사슬 규명.

### 축 4: 엔지니어링 리스크 및 트레이드오프 (Engineering Trade-offs)
- 표준 라이브러리 유지 시의 비용 (느린 성능, 현대적 DX 부재).
- 서드파티 도입 시의 비용 (의존성 충돌 Dependency Hell, 공급망 보안 취약점, 유지보수 중단 리스크, 라이선스 제약).

---

## 3. 📊 출력 포맷 표준

1. **Executive Summary**: 기술적 실체와 핵심 상호작용 한 줄 요약.
2. **진화 사슬 매트릭스 (Lineage Evolution Matrix)**: 표준 내장 모듈 vs 1~3세대 서드파티 도구 비교표.
3. **심층 아키텍처 비교**: 성능, 메모리, 병렬성 메커니즘 분석.
4. **엔지니어링 의사결정 매트릭스**: 어떤 환경에서 표준 모듈을 고수하고, 어떤 환경에서 서드파티를 채택해야 하는가?
