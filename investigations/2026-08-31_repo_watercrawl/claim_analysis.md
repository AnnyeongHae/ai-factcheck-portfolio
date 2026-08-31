# 1. WaterCrawl 핵심 클레임 분석 (Claim Analysis)

## 1. 팩트체크 검증 출처 (Verified Sources)
- **공식 저장소 (Tier 1)**: [https://github.com/watercrawl/WaterCrawl](https://github.com/watercrawl/WaterCrawl)
- **공식 아키텍처 문서 (Tier 1)**: [https://watercrawl.dev](https://watercrawl.dev)
- **공급망 보안 권고 (Tier 2)**: Glassworm 악성 써드파티 npm 패키지 스푸핑 주의보

---

## 2. 개발자 커뮤니티 실제 반응 (Community Reactions)
- **GitHub 엔지니어 피드백**:  
  > *"Scrapy의 셀렉터 엔진을 Django/Celery UI와 REST API로 감싸서, 복잡한 커머스 사이트 크롤링 룰셋을 정의하기에 가장 편리하다."*
- **Reddit AI 엔지니어 코멘트**:  
  > *"Dify나 n8n과 연동이 잘 되어 노코드 웹 인제스천에 유리함. 단, 써드파티 npm MCP 패키지에 스푸핑 악성코드가 발견되었으니 공식 GitHub 소스만 빌드할 것."*

---

## 3. 원자적 명제 분해 (Atomic Claims)

### Claim 1: [정밀한 CSS/XPath 셀렉터 기반 크롤링 제어]
- **명제**: 단순 전체 텍스트 추출이 아닌, 복잡한 동적 웹사이트의 특정 영역(본문, 가격, 스펙)만 타겟팅하여 노이즈(헤더, 광고, 푸터)를 제거한다.
- **검증 결과**: Scrapy ItemPipeline 및 커스텀 추출 룰셋 구현 확인 (`[VERIFIED TRUE]`).

### Claim 2: [완전 독립형 셀프호스팅 지원]
- **명제**: Docker Compose를 통해 외부 클라우드 의존성 없이 로컬/온프레미스 인프라에 배포 가능하다.
- **검증 결과**: `docker-compose.yml` (Django, Redis, Celery, PostgreSQL) 정상 구동 확인 (`[VERIFIED TRUE]`).

### Claim 3: [n8n 및 Dify 에코시스템 플러그인 연동]
- **명제**: 자동화 워크플로우 플랫폼과 REST API / 웹훅으로 즉시 연결 가능하다.
- **검증 결과**: 공식 통합 어댑터 코드 확인 (`[VERIFIED TRUE]`).
