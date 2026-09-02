# 🕶️ Stealth & URL Integrity Architecture Specification
> **버전**: v1.0 (2026-09-02)  
> **상태**: Production Live 배포 완료  
> **적용 시스템**: GitHub Actions 크론 수집 엔진(`tools/harvest_trends.py`), 포트폴리오 빌더(`tools/build_dashboard.py`), 웹 프론트엔드 네비게이션  

---

## 1. 개요 및 설계 목적 (Overview & Objective)

본 문서는 AI 기술 팩트체크 플랫폼에서 **(1) 수집 데이터의 정확한 원문 연결(URL Integrity)**과 **(2) 외부 사이트 탐색 및 수집 시 신원/경로를 완전히 은폐하는 스텔스(Stealth & Anti-Tracking)** 아키텍처의 설계 및 구현 명세를 정의합니다.

### 🎯 핵심 해결 과제
1. **Hacker News 및 커뮤니티 원문 불일치 해결**:
   - Hacker News API에서 `story.url`(외부 블로그)과 `item?id=`(토론 쓰레드)가 혼재되어 엉뚱한 사이트로 튀는 현상 방지.
2. **해커뉴스 `Sorry.` 에러 및 봇 차단 극복**:
   - 외부 웹사이트(`localhost`, GitHub Pages)에서 넘어오는 `Referer` 헤더로 인해 해커뉴스 방화벽에 차단되는 문제 원천 해결.
3. **ChatGPT 및 소셜 마케팅 추적 파라미터(UTM/Ref) 영구 박멸**:
   - ChatGPT가 생성한 링크에 자동 부착되는 `utm_source=chatgpt.com`, `ref=chatgpt` 및 각종 소셜 트래커(`fbclid`, `spm` 등)를 수집 및 클릭 단계에서 실시간 소멸.
4. **GitHub Actions 봇 지문 은폐**:
   - Actions 러너에서 실행되는 파이썬 수집기가 대상 서버(GitHub, Hacker News, Hugging Face 등)에 봇이나 크롤러로 감지되지 않고 실제 일반 데스크톱 사용자로 인식되도록 위장.

---

## 2. URL 무결성 및 이중 링크 아키텍처 (URL Integrity Architecture)

### 2.1 Hacker News 이중 링크 (Dual-Link) 체계

Hacker News는 성격상 **외부 소개 기사**와 **개발자 댓글 토론**이라는 2개의 고유한 가치를 지닙니다. 따라서 단일 링크가 아닌 **2개의 분리된 버튼 UI**를 제공합니다.

| 버튼 종류 | 표시 라벨 | 링크 대상 | 설명 |
| :--- | :--- | :--- | :--- |
| **기사 원문** | `[📄 기사 원문]` | `article_url` | 기술 원문 블로그, 공식 릴리즈 노트, GitHub 저장소 |
| **HN 토론** | `[🔥 HN 토론]` | `hn_url` (`item?id=\d+`) | 실제 수백 개 댓글과 반박이 실시간으로 오가는 해커뉴스 쓰레드 |

### 2.2 엄격한 URL 유효성 검증 게이트 (Validation Gate)
`tools/harvest_trends.py` 및 수집 파이프라인에는 아래의 검증 게이트를 통과하지 못한 항목을 즉시 드롭(Drop)합니다:
- **Hacker News**: 반드시 `news.ycombinator.com/item?id=\d+` (정수형 ID) 형태여야 함.
- **GitHub**: 반드시 `github.com/[소유자]/[저장소]` 형태여야 함.
- **루트 도메인 거부**: 단순 포털 주소(`https://news.ycombinator.com`, `https://github.com` 등)는 인용 및 수집 원천 배제.

---

## 3. 엔드투엔드 스텔스 & 안티-트래킹 엔진 명세 (Stealth Engine)

### 3.1 GitHub Actions 백엔드 수집단 스텔스 (Backend Stealth)

#### A. 실시간 트래커 스트리퍼 (`clean_stealth_url`)
수집되는 모든 URL에서 마케팅 및 AI 출처 트래킹 쿼리스트링을 사전 제거합니다.

- **제거 대상 파라미터 (Blacklist)**:
  - `utm_source`, `utm_medium`, `utm_campaign`, `utm_term`, `utm_content`, `utm_id` (및 모든 `utm_*`)
  - **ChatGPT 특화 트래커**: `ref=chatgpt.com`, `utm_source=chatgpt.com`, `source=chatgpt`
  - **소셜/광고 트래커**: `fbclid`, `gclid`, `msclkid`, `twclid`, `si`, `spm`, `igshid`, `yclid`, `mc_cid`, `mc_eid`, `aff`, `affiliate`, `ref`, `ref_src`, `ref_url`

#### B. 최신 데스크톱 브라우저 지문 로테이션 & Client Hints
크롤러 봇(`Python-urllib`, `requests`) 헤더를 완전히 제거하고, 실제 데스크톱 사용자의 브라우저 지문 풀을 순환합니다:
- **User-Agent Pool**: Chrome 131 (Windows 11), Safari 18 (macOS Sonoma), Edge 131, Firefox 132
- **Client Hints**: `Sec-Ch-Ua`, `Sec-Ch-Ua-Mobile: ?0`, `Sec-Ch-Ua-Platform`, `Sec-Fetch-*`, `Accept-Language: ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7`

#### C. 인간 모사 지터(Jitter) 딜레이
- 요청 간 `random.uniform(0.05, 0.15)`초의 미세 불규칙 딜레이를 주입하여 기계적인 호출 주기를 완전히 분쇄.

#### D. Liveness 검증 (삭제/차단 글 수집 방지)
- Hacker News 수집 시 `story.get("dead")` 또는 `story.get("deleted")`가 `true`인 경우 수집 단계에서 즉시 스킵.

---

### 3.2 프론트엔드 전역 스텔스 네비게이션 (Frontend Stealth)

#### A. 브라우저 레벨 정책
- `<head>` 태그 내 `<meta name="referrer" content="no-referrer">` 명시.
- 모든 외부 링크에 `rel="noopener noreferrer"` 부여.

#### B. 전역 클릭 인터셉터 (Global Link Interceptor)
웹페이지 내의 어떤 버튼/링크를 누르더라도 이벤트 캡처링 단계(`capture: true`)에서 스텔스 가로채기가 발생합니다:
- `cleanStealthUrl(rawUrl)`: 클릭하는 순간 브라우저 메모리 상에서 모든 UTM/ChatGPT 파라미터 실시간 박멸.
- `window.open("", "_blank")` 후 `newWin.opener = null; newWin.location.replace(cleanUrl);`: 독립 샌드박스 창으로 이동하여 이전 페이지 기록 및 `document.referrer` 완전 차단.
- **결과**: 상대방 웹서버 로그 상 **주소창에 직접 타이핑해서 들어온 Direct Traffic**으로 완벽하게 기록됨.

---

## 4. 결론 및 향후 관리 지침

1. **신규 수집 소스 추가 시**: 반드시 `tools/harvest_trends.py`의 `clean_stealth_url()`과 `get_stealth_headers()`를 경유하여 호출할 것.
2. **소셜 큐레이션 데이터 등록 시**: 사용자가 수동 큐레이션한 링크에 `utm_`이나 플랫폼 파라미터가 섞여 있어도 수집 엔진과 프론트엔드 인터셉터가 이중으로 자동 정제하므로 안심하고 원본 링크를 등록 가능.
3. **지속적인 모니터링**: 대상 사이트의 봇 탐지 정책 변경 시 `STEALTH_USER_AGENTS` 버전을 최신 브라우저 메이저 버전으로 주기적 갱신.
