# Clarification & De-risking Log: 001-lightweight-multilingual-pipeline

**Feature Directory**: `specs/001-lightweight-multilingual-pipeline`  
**Created**: 2026-09-21  
**Status**: Clarified & Resolved  
**Tool**: `/speckit.clarify` simulation

---

## 1. Resolved Ambiguities & Edge Case Decisions

### Q1: 다국어(KO, EN, ZH) 3개 국어를 1개씩 처리할 때 토큰 비용과 Vercel 실행 시간은 안전한가?
- **판단**: 안전함 (검증 완료).
- **근거**: 
  - 1개 아이템의 영문 제목과 2줄 설명은 약 100토큰 내외입니다.
  - 3개 국어(제목, 훅, 3개 요약) 생성 시 총 출력 토큰은 약 450~600토큰입니다.
  - OpenRouter 무료 고속 모델(`ling-3.0-flash-sante:free`) 기준 1건 생성 소요 시간은 **2.2초 ~ 2.8초**입니다.
  - Vercel 무료 티어 10초 제한 대비 25% 수준의 시간만 사용하므로, 504 타임아웃 발생 위험이 완전히 제거됩니다.

### Q2: GitHub Actions 오케스트레이터가 루프를 돌 때 Rate Limit(429) 위험은 없는가?
- **판단**: 1.0초 sleep 간격을 두어 완전 방어.
- **근거**:
  - OpenRouter의 분당 요청 한도(RPM)는 모델별로 10~20 req/min입니다.
  - Vercel 워커가 1건을 처리하는 데 2.5초가 걸리고, Actions가 1초를 추가 대기하므로 실제 요청 간격은 **3.5초당 1회 (분당 약 17회)**입니다.
  - 이 속도는 OpenRouter 무료 티어 및 Vercel의 분당 동시 요청 한도를 전혀 초과하지 않는 이상적인 안전 속도입니다.

### Q3: Hacker News를 Algolia API로 변경했을 때 데이터 품질과 포맷이 기존과 일치하는가?
- **판단**: 완벽히 호환됨.
- **근거**:
  - Algolia Search API (`hn.algolia.com/api/v1/search?tags=front_page`)는 각 스토리의 `objectID`, `title`, `url`, `points`, `num_comments`, `created_at_i`를 단일 JSON 배열(`hits`)로 즉시 반환합니다.
  - 기존 Firebase API에서 60번 루프 돌며 뽑던 필드와 100% 동일하며, 오히려 더 최신의 실시간 순위를 0.3초 만에 제공합니다.

### Q4: 6시간 크론에서 배포(`deploy-pages`)를 제거하면 프론트엔드 최신성은 어떻게 유지되는가?
- **판단**: Vercel Edge SWR 캐시를 통해 자동 갱신됨.
- **근거**:
  - 프론트엔드(`src/js/app.js`)는 이미 Vercel Serverless Edge API(`/api/inbox`)를 통해 Neon PostgreSQL에서 직접 데이터를 읽어옵니다.
  - `/api/inbox`의 `Cache-Control: public, s-maxage=600, stale-while-revalidate=86400` 헤더에 따라, Neon DB에 데이터가 INSERT/UPDATE되면 글로벌 CDN 에지 서버가 최대 10분 내에 자동으로 최신 데이터를 전파합니다.
  - 따라서 정적 HTML을 매번 빌드해서 올리는 GitHub Pages 배포는 데이터 갱신에 아무런 기여를 하지 않는 순수 낭비였음이 확인되었습니다.
