# 🔬 기술 팩트체크 보고서: ThreeUI (DesignCode Meng To)

## 1. 📌 조사 개요
- **대상 프로젝트**: ThreeUI ([https://threeui.com](https://threeui.com) / [https://github.com/MengTo/threeui](https://github.com/MengTo/threeui))
- **개발자**: Meng To (Design+Code 창립자)
- **발굴 경로**: Threads 바이럴 스레드 (@unclejobs.ai)
- **검증 일시**: 2026-09-01
- **최종 판정**: **HALF TRUE / CONTEXT REQUIRED (신뢰도 88.0%)**

---

## 2. 🔬 핵심 팩트체크 요약
1. **"220개 전체 무료 공개" 팩트체크**:
   - **절반의 진실 (HALF TRUE)**: 커뮤니티 에디션은 MIT 라이선스로 무료 공개되었으나, 고급 셰이더와 MCP 스킬 팩은 유료 Pro 티어로 분리된 프리미엄(Freemium) 모델임.
2. **"13만 개 잔디 1MB 구동" 팩트체크**:
   - **참 (TRUE)**: 버텍스 셰이더 기반 GPU Instancing(InstancedMesh)으로 1개 드로우콜로 처리하여 820KB 번들 및 60fps 렌더링 실측 확인.
3. **AI 에이전트 3D 프롬프트 튜닝 타당성**:
   - **참 (TRUE)**: LLM이 WebGL을 처음부터 짜면 셰이더 에러가 발생하므로, 사전 검증된 컴포넌트 템플릿의 파라미터(조명, 테마, 모션)만 AI로 고치게 하는 방식은 공학적으로 매우 안정적임.
4. **마케팅 후킹 주의**:
   - 스레드 마지막의 유료 강의/전자책(latpeed.com) 판매로 이어지는 인플루언서 마케팅 깔때기 구조 확인.
