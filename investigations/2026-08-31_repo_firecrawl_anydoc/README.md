# [Repository 기술 심층 분석] Firecrawl AnyDoc (`firecrawl/anydoc`)

- **대상 저장소 (Target Repo)**: `https://github.com/firecrawl/anydoc`
- **조사 개시일**: 2026-08-31
- **책임 에이전트/조사관**: Antigravity SOTA Factchecker
- **최종 판정 상태**: `[ VERIFIED TRUE ]` (기술적 성능 및 로컬 무결성 입증)

---

## 1. 개요 및 분석 배경
Firecrawl 팀에서 공개한 **AnyDoc**은 Word, Excel, PowerPoint 등 14개 이상의 오피스 문서를 **Rust 기반 코어로 단 4ms 만에 LLM용 클린 마크다운으로 변환**하는 오픈소스 라이브러리입니다. 
공개 직후 수천 개의 GitHub Star를 획득하며 RAG 및 AI Agent 커뮤니티에서 폭발적인 관심을 받고 있어, **성능 벤치마크 진위, Star 급증 원인, 실무 활용 방안 및 단위 경제학**을 심층 분석했습니다.

## 2. 조사 파일 목차
1. [claim_analysis.md](./claim_analysis.md): 핵심 성능 수치(4.4ms), 지원 포맷(14종), 로컬 실행 주장 분해
2. [code_audit.md](./code_audit.md): Rust 코어 아키텍처, 의존성, LlamaParse/Pandoc 대비 속도 및 비용(Unit Economics) 비교
3. [verdict_report.md](./verdict_report.md): Star 급증 요인, AI Agent 및 엔터프라이즈 RAG 실무 활용 가이드, 한계점 및 최종 판정서
