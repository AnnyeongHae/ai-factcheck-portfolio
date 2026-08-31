# [Repository 팩트체크] WaterCrawl 웹 크롤러 & LLM 마크다운 변환 플랫폼

- **대상 저장소**: [https://github.com/watercrawl/WaterCrawl](https://github.com/watercrawl/WaterCrawl)
- **조사 개시일**: 2026-08-31
- **발굴 구분**: `[ 👤 USER CURATED ]` (사용자 직접 발굴 & 의문 검증)
- **기술 클러스터**: `[ 🌐 웹 데이터 ➔ LLM 마크다운 변환기 (Web-to-Markdown Scrapers) ]`
- **최종 판정**: `[ VERIFIED TRUE ]` (Django/Scrapy 기반 정밀 크롤링 및 LLM 마크다운 변환 입증)
- **Hands-on 상태**: `[ PENDING_RESEARCH ]` (아키텍처 및 공급망 보안 감사 완료)

---

## 1. 기술 개요
웹 데이터를 LLM이 처리하기 쉬운 구조화된 마크다운/JSON으로 추출하는 오픈소스 플랫폼으로, Django, Scrapy, Celery, Redis 기반의 분산 아키텍처와 Dify/n8n 플러그인을 지원합니다.

## 2. 조사 파일 목차
1. [claim_analysis.md](./claim_analysis.md): Scrapy 기반 세밀 제어, 셀프호스팅, LLM 구조화 등 핵심 클레임 분해
2. [code_audit.md](./code_audit.md): Docker 스택 감사, Firecrawl/Crawl4AI 비교 매트릭스, 공급망 보안 감사
3. [verdict_report.md](./verdict_report.md): 최종 팩트체크 판정서 및 실무 엔지니어링 활용 가이드
