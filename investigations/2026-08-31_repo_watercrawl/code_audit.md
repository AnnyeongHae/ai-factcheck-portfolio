# 2. 코드 및 대체재 비교 감사 (Code & Alternatives Audit)

## 1. LLM 웹 데이터 인제스천 대체재 비교 매트릭스 (Alternatives Matrix)

| 도구명 (Tool) | 핵심 기술 스택 | 주요 장점 (Pros) | 주요 한계점 (Cons) | 추천 사용 시나리오 (Best For) |
| :--- | :--- | :--- | :--- | :--- |
| **WaterCrawl** | Python, Django, Scrapy, Celery | CSS/XPath 세밀 제어, 자가호스팅, n8n 연동 | Scrapy/Django 리소스 오버헤드 | **복잡한 엔터프라이즈/이커머스 정밀 크롤링** |
| **Firecrawl** | TypeScript, Playwright | 대중적 생태계, 손쉬운 클라우드 API | SaaS 종속성, 셀프호스팅 복잡 | **빠른 RAG 프로토타이핑 및 클라우드 호출** |
| **Crawl4AI** | Python, Playwright, Asyncio | 비동기 초고속 로컬 크롤링, 경량화 | 분산 큐 자체 구축 필요 | **로컬 파이썬 파이프라인 단독 구동** |
| **AnyDoc** | Rust (Zero-copy) | 4.4ms 초고속 오피스(.docx 등) 파싱 | 웹 크롤링 불가 (로컬 파일 전용) | **로컬 사내 문서의 초고속 마크다운 변환** |

---

## 2. 보안 공급망 감사 (Supply Chain Security Audit)
- **발견된 위협**: 2026년 초 비공식 npm 패키지(예: `@iflow-mcp/watercrawl-watercrawl-mcp`)가 Glassworm 공급망 공격에 노출된 사례 확인.
- **감사 결과**: 공식 저장소(`github.com/watercrawl/WaterCrawl`)의 소스코드는 안전하며 악성코드가 없음.
- **보안 수칙**: 반드시 공식 Docker 이미지 및 공식 소스코드만 체크아웃하여 사용할 것.

---

## 3. 단위 경제학 (Unit Economics) 비교
- 일 50,000 페이지 크롤링 기준:
  - **상용 API (Firecrawl Cloud)**: 월 약 $250 ~ $400 소요.
  - **자가호스팅 WaterCrawl (단일 클라우드 인스턴스 $40/mo)**: 월 $40 고정으로 약 85% 비용 절감.
