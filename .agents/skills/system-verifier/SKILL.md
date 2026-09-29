---
name: system-verifier
description: Autonomous system verification and QA auditing pipeline for AI FactCheck Hub. Use whenever the user requests system verification, pre-deployment checks, regression testing, or commands like "검증 작업 진행", "검증해줘", or "/verify". Enforces a 4-tier fast-fail workflow with zero LLM API costs.
---

# System Verifier Skill (검증 에이전트 표준 수칙)

## 1. 개요 및 목적
본 스킬은 AI 팩트체크 허브의 빌드 무결성, DB SSOT(Aiven PostgreSQL), Voyage AI 벡터 임베딩, 그리고 브라우저 런타임을 **최소한의 자원(Zero LLM Token, 초고속 Fast-Fail)** 으로 전수 검증하는 표준 파이프라인입니다.

사용자가 **"검증 작업 진행"**, **"검증해줘"**, **"/verify"** 등을 요청하거나 배포/리팩토링 전후 무결성을 점검할 때 본 스킬을 적용합니다.

---

## 2. 4단계 Fast-Fail 검증 원칙

```text
[Tier 1: 정적 번들/구문 검증]   node tools/build_frontend.js       (~35ms)  -> 실패 시 즉시 중단
[Tier 2: 백엔드/DB/Voyage 헬스] node tools/verify_agent.js --quick (~300ms) -> 실패 시 즉시 중단
[Tier 3: 무두 브라우저 E2E 슈트] node tools/verify_agent.js         (~5s)    -> 32개 단언 & 0 콘솔에러
[Tier 4: UI/UX 시각 스냅샷]     node tools/verify_agent.js --visual (~8s)    -> 레이아웃/글리프 점검
```

1. **비용 $0 보장**:
   - 검증 과정에서 OpenRouter 등 유료/쿼터 제한 LLM API를 일체 호출하지 않습니다.
   - 정적 구문 파싱, 네이티브 DB 쿼리, HTTP 상태 코드, Puppeteer 무두 브라우저 단언으로만 수행합니다.
2. **Fast-Fail 조기 탈출**:
   - Tier 1 번들 구문 검증에 실패하면 브라우저를 띄우지 않고 35ms 만에 즉각 에러를 보고하여 시스템 자원을 보호합니다.
3. **무결점 0 Console Errors 원칙**:
   - 브라우저 First Paint 및 라우트 이동 간 unhandled exception 및 console.error가 0건이어야만 배포 승인(Pass)을 내립니다.

---

## 3. 실행 방법 (CLI 및 에이전트 명령)

### A. 에이전트 서브태스크 위임
Antigravity에서 검증 작업 수행 시 전용 서브에이전트 `qa_verifier`를 호출합니다:
```json
{
  "Subagents": [
    {
      "TypeName": "qa_verifier",
      "Role": "System QA Verifier",
      "Prompt": "Execute full system verification with minimum resources (node tools/verify_agent.js) and report status."
    }
  ]
}
```

### B. 직접 실행 명령
- **전체 정밀 검증 (기본)**:
  ```bash
  npm run verify
  # 또는 node tools/verify_agent.js
  ```
- **빠른 검증 (빌드 및 DB 상태만 확인)**:
  ```bash
  npm run verify:quick
  ```
- **시각 스냅샷 포함 검증**:
  ```bash
  npm run verify:visual
  ```

---

## 4. 체크리스트 및 최종 판정 기준
- [ ] Tier 1: `build_frontend.js` 실행 시 3개 타깃(`src/js/app.js`, `public/app.js`, `docs/app.js`) 문법 에러 0건.
- [ ] Tier 2: `/api/embed-worker?check_only=true`가 200 OK를 반환하고 DB 아이템 수가 5,000건 이상인가?
- [ ] Tier 3: `verify_frontend_modular.js` 32개 assertion 100% Pass, console.error 0건.
- [ ] Tier 3: 비상 롤백 하네스(`app.legacy.js`)가 정상 주입 및 작동 가능한가?
- [ ] Tier 4: 트렌드 레이더 뱃지 및 이모지가 깨짐 없이 SVG Lucide 아이콘으로 렌더링되는가?
