# [아키텍처 감사 및 적용 보고서] 제로베이스 멀티소스 통합 및 UX/UI 고도화 (2026-09-27)

---

## 1. 개요
* **일자**: 2026-09-27
* **커밋 해시**: `5d04bd8` (`feat(ux/ui): unify multi-source card architecture, earliest date SSOT, and fix sticky header`)
* **목적**: 
  1. 기형적으로 상단(언론사 묶음)과 하단(커뮤니티/원문)으로 분열되어 있던 출처 구조를 완전 제로베이스에서 단일 액션 허브로 통합.
  2. 중복 기사 병합 시 트렌드의 발생 시점이 최신 날짜로 왜곡되던 현상을 해결하고 최초 수집 일자(`earliest_harvested_at`) SSOT 확립.
  3. `body` 태그의 `overflow-x: hidden`으로 인해 스크롤 시 헤더가 고정되지 않고 밀려 올라가던 브라우저 렌더링 버그 해결 (`overflow-x: clip`).
  4. 검색창 원클릭 초기화(`✕`), 팝오버 `Escape` 닫기, 제목 2줄 정돈(`line-clamp-2`), 스켈레톤 로딩(Skeleton Shimmer) 등 5대 UX 디테일 적용.

---

## 2. 출처(Sources) 구조 제로베이스 전면 통합

### A. 레거시 구조의 한계와 비판
* **기존 구조**:
  - 카드 상단: `9개 매체·플랫폼 동시 집중 보도` 배너 내에 9개의 거대한 개별 버튼이 나열되어 본문(제목, Hook, 3줄 요약)을 아래로 밀어냄.
  - 카드 하단: 푸터 액션바에 `🔥 HN 토론`, `🤖 레딧`, `🔗 +1개 출처 ▾`, `📄 원문` 버튼이 또다시 중복 나열됨.
  - 동일한 `Hacker News` 링크가 상단 배너와 하단 푸터 양쪽에 중복 노출되는 등 시선 분산 및 수직 공간 낭비 극심.

### B. 재설계 원칙: "상단은 시그널(Signal), 하단은 액션(Action)"
1. **상단 (Header)**:
   - 복잡한 개별 링크 버튼을 100% 걷어내고, 높이 28px의 세련된 **1줄 크로스 바이럴 시그널 바**로 축약:
     `🔥 {clusterCount}개 매체·커뮤니티 교차 분석 | 📰 언론 {pressCount} · 💬 커뮤니티 {communityCount}`
   - 0.3초 만에 "공신력 언론과 개발자 커뮤니티가 동시에 주목한 중요 이슈"임을 인지시킴.
2. **하단 (Footer Action Bar)**:
   - 상·하단에 흩어져 있던 모든 링크를 **하단 단일 액션 바**로 100% 일원화:
     - 대표 언론 1개(예: `[📰 BBC]`) + 대표 커뮤니티 1개(예: `[🔥 HN (42pts)]`) 다이렉트 1-클릭 버튼.
     - `[🔗 +N개 출처 ▾]` 통합 팝오버:
       - **📰 공식 언론 보도 (N개)** 섹션: `[CBC]`, `[The Hill]`, `[The Verge]`, `[Fortune]` 등 기사 원문.
       - **💬 커뮤니티 & 개발자 반응 (N개)** 섹션: `🔥 HN`, `🤖 레딧`, `💬 긱뉴스` 등 토론 스레드.
     - 하단 우측에 불필요하게 중복 붙던 `📄 원문` 꼬리표 버튼 제거.

---

## 3. 최초 수집 일자 (Initial Harvested Date) SSOT 확립

### A. 문제점
* 기존에는 신규 언론사 보도가 크롤링되어 기존 클러스터에 병합될 때, DB 레코드의 `harvested_date`가 최신 수집일로 갱신되어 "이슈가 며칠 전에 처음 터졌는지"에 대한 트렌드 발생 시점이 왜곡됨.

### B. 해결 방안
* `api/inbox.js`:
  - `harvested_date`, `created_at`, `sources[].created_at`, `cross_posts[].captured_at` 중 **가장 빠른(MIN) 타임스탬프**를 계산하여 `earliest_harvested_at`으로 산출.
* `docs/app.js` (`renderCardStandardFooter`):
  - `📥 최초 포착: YYYY-MM-DD HH:MM` (불변 고정 표시).
  - 추가 보도나 댓글이 업데이트된 경우에만 `(🔄 최신 갱신: YYYY-MM-DD HH:MM)`으로 보조 표시.

---

## 4. 상단 헤더 스크롤 고정 (Fixed Sticky) 버그 해결

### A. 원인 규명
* `<header class="sticky top-0 ...">`로 지정되어 있었으나, `<body>` 태그에 걸려 있던 `overflow-x-hidden` 클래스로 인해 브라우저 뷰포트 스크롤과 헤더의 위치 계산이 단절되어 `position: sticky`가 무력화됨.

### B. 해결 조치
* `html, body { overflow-x: clip; }` 표준 CSS 적용.
* `body` 클래스에서 `overflow-x-hidden` 제거.
* `<header>`에 `shadow-xs` 레이어를 적용하여 스크롤 시 본문 카드와 명확하게 분리되는 시각적 완성도 확보.

---

## 5. UX/UI 5대 편의 기능 적용

1. **검색창 원클릭 초기화 (`✕`) 버튼**: 1글자 이상 입력 시 즉시 활성화, 클릭 시 0ms 즉시 검색어 리셋.
2. **출처 팝오버 `Escape` 키 닫기 & 모바일 클램핑**: 360px~400px 모바일 뷰포트에서도 화면 밖으로 넘치지 않도록 `max-w-[calc(100vw-2.5rem)]` 클램핑.
3. **카드 제목 2줄 정돈 (`line-clamp-2`)**: 3열 카드 그리드에서 제목 길이에 따른 카드 높이 불균일 해소.
4. **Hook 인용구 악센트 바 (`border-l-4 border-l-amber-500`)**: 에디토리얼 스타일의 세련된 인용구 강조.
5. **카드형 스켈레톤 로딩 (Skeleton Shimmer)**: 페이지 이동/필터링 시 레이아웃 시프트(CLS)를 없애고 체감 속도 향상.

---

## 6. 무결성 및 배포 검증
* **3벌 파일 일치**: `docs/` ↔ `public/` ↔ `src/` SHA-256 해시 100% 동일 일치.
* **문법 검사**: Node.js 구문 검사(`node -c`) 0 에러 통과.
* **프로덕션 배포**: `https://github.com/AnnyeongHae/ai-factcheck-portfolio.git` (`main` 브랜치) 푸시 완료.
