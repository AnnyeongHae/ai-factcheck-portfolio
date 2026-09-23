# 🛡️ AI 팩트체크 허브: 수집 및 파이프라인 아키텍처 정밀 감사 보고서 (SSOT)
> **문서 버전**: v1.0 (2026-09-24)  
> **정본 데이터베이스 (SSOT)**: Aiven Cloud PostgreSQL (`pg-11178328-factchecker.f.aivencloud.com:18164/defaultdb`)  
> **파이프라인 상태**: 100% 정상 가동 (정기 1일 5회 스케줄 및 Vercel Serverless 무결성 검증 완료)

---

## 1. 9월 23일 04:00 KST '337건 수집 급증' 역추적 진단

### 1-1. 발생 현상
- 2026-09-23 04:00 KST (GitHub Actions Run `#35770711109`) 실행 시 단일 회차에서 **337건이 대량 수집**됨.

### 1-2. 데이터베이스 원천 역추적 결과 (`raw_trends_inbox`)
```text
[2026-09-23 04:00 KST 회차 수집 출처별 정확한 분포]
1. 🐙 GitHub Official                 : 91건
2. 🔥 Hacker News                       : 43건
3. 🤗 Hugging Face Spaces (Interactive) : 32건
4. 🤖 OpenAI News (공식 RSS)            : 30건
5. 🌐 Simon Willison Tech Weblog        : 30건
6. 🤗 Hugging Face Models (Trending)    : 28건
7. 📰 주요 글로벌 테크 언론 (Ars/TC/Verge): 58건
8. 📺 유튜브 테크 (Fireship, 조코딩, 슈카) : 12건
9. 💬 Reddit 및 긱뉴스 (GeekNews)       : 13건
--------------------------------------------------
합계: 337건
```

### 1-3. 급증의 근본 원인 (Root Cause)
1. **스캔 상한선 확장**: 직전 회차까지 360건으로 하드코딩되어 있던 스캔 한도를 사용자 요청에 따라 **843건**으로 대폭 상향.
2. **신규 플랫폼 대거 투입**: GitHub Search, Hugging Face Spaces, OpenAI 공식 RSS, 사이먼 윌리슨 블로그, 주요 IT 언론사 및 테크 유튜브 채널이 파이프라인에 신규 편입.
3. **최초 흡수 (Cold Start / Initial Hydration)**: 신규 추가된 플랫폼들은 DB에 과거 데이터가 없었기 때문에, 첫 실행 시 최신 발행된 양질의 글들이 한꺼번에 수집됨.
4. **이후 정상화 추이**: 중복 제거(Deduplication) 엔진이 정상 작동하여, 이후 회차는 일상적인 증분치(**88건 → 73건 → 63건**)로 완전히 안정화됨.

---

## 2. 수집 실행 시간(2분~3분) 및 병목 구간 정밀 감사

### 2-1. 전체 워크플로 시간 구조
- GitHub Actions 대시보드에 표기되는 '2분 8초', '2분 48초'는 수집 스크립트 단독 시간이 아니라, **CI/CD 가상머신 전체의 생애주기 총합**임:
  - Ubuntu VM 프로비저닝 & Git Checkout: ~8초
  - Python 3.12 런타임 & Pip 의존성 설치: ~12초
  - DB 원격 동기화 (`tools/db_bridge.py`): ~4초
  - **Stage 1 수집기 실행 (`tools/harvest_trends.py`)**: **~75초**
  - **Stage 2 AI 3개 국어 요약 (`tools/drain_ai_enrichment.py`)**: **~35초**
  - Stage 3 EOD 랭킹 & 텔레메트리 동기화: ~5초
  - **총 소요 시간**: 약 **2분 15초 ~ 2분 40초**

### 2-2. `harvest_trends.py` 출처별 실측 지연시간 (`harvest_source_metrics`)
Aiven PostgreSQL에 1초 단위로 자동 로깅된 출처별 벤치마크 실측치:
| 출처 (Source) | 스캔 건수 | 소요 시간 (초) | 평가 |
| :--- | :---: | :---: | :--- |
| **Hugging Face Models** | 100건 | **0.16초** | ⚡ 초고속 |
| **Hugging Face Spaces** | 165건 | **0.33초** | ⚡ 초고속 |
| **GeekNews (한국)** | 50건 | **0.81초** | ⚡ 초고속 |
| **YouTube Tech** | 60건 | **1.06초** | ⚡ 초고속 |
| **Tech Press (언론사)** | 110건 | **1.81초** | ⚡ 초고속 |
| **GitHub Search** | 143건 | **3.03초** | ⚡ 초고속 |
| **Curated Tech RSS** | 120건 | **3.95초** | ⚡ 초고속 |
| **Reddit Tech** | 25건 | **4.66초 ~ 61.02초** | ⚠️ 레딧 서버 지연 시 편차 발생 |
| **Hacker News (Algolia)** | 70건 | **47.09초 ~ 55.46초** | 🔴 **전체 수집 시간의 65% 이상 독점 (최대 병목)** |

---

## 3. 병목 구간(Hacker News 댓글 수집) A/B 테스트 결과

### 3-1. 실험 설계 (A/B Test Design)
- **대상**: Algolia HN Front Page 활성 댓글이 존재하는 실제 15개 스토리 (총 1,466개 댓글)
- **대조군 (Group A)**: 현재 프로덕션 적용 방식인 **순차 동기 수집 (Sequential for-loop)**
- **실험군 1 (Group B)**: **ThreadPoolExecutor 병렬 수집 (`max_workers=6`)**
- **실험군 2 (Group C)**: **ThreadPoolExecutor 병렬 수집 (`max_workers=8`)**

### 3-2. 실측 벤치마크 데이터
```text
=================================================================
🔬 [A/B Test] Hacker News Comment Ingestion: Sequential vs Parallel
[*] Sample Size: 15 top front-page stories with active comments
=================================================================
1. 지연 시간 (Latency):
   - Group A (현재 순차 방식)   : 13.54초 (1.00x, 건당 0.90초)
   - Group B (병렬 max_workers=6):  2.83초 (4.78배 빠름, 79.1% 시간 단축)
   - Group C (병렬 max_workers=8):  2.24초 (6.03배 빠름, 83.4% 시간 단축)

2. 데이터 정합성 (Data Parity Rate):
   - Group A vs Group B: 100.0% 완벽 일치 (15개 스토리 댓글 1,466건 누락 0)

3. API 안정성 & HTTP 429 레이트 리밋:
   - 오류 발생 0건, Algolia API 차단 또는 타임아웃 전혀 없음.

💡 [전체 70개 HN 스토리 수집 시 예상 소요 시간]:
   - 현재 순차 방식   : 약 63.2초
   - 병렬 방식 (w=6)  : 약 13.2초 (회차당 50.0초 순수 단축 가능)
=================================================================
```

---

## 4. 아키텍처 원칙 및 향후 운영 가이드 (Frozen Rules)

1. **현재 상태 유지 우선 원칙 (Stability First)**:
   - 현재 전체 워크플로 총 2분 15초는 GitHub Actions 제한(10분)의 25%, 월간 쿼터(2,000분)의 18.7% 수준으로 **완벽하게 안전한 정상 범위**에 있습니다.
   - 불필요한 코드 조작으로 인한 부작용을 방지하기 위해 **현재 파이프라인 구조를 그대로 고정**합니다.
2. **병렬 처리 적용 시점**:
   - 향후 수집 출처를 1,500건 이상으로 추가 확장하여 워크플로 시간이 5분을 초과할 조짐이 보일 때, 본 문서의 검증된 `ThreadPoolExecutor(max_workers=6)` 로직을 적용합니다.
3. **AI 요약 모델 단일화 (Ling-3.0-flash SSOT)**:
   - AI 번역/요약은 검증 1위인 `inclusionai/ling-3.0-flash-sante:free`를 기본으로 유지하며, OpenRouter 무료 쿼터 보호를 위해 임의의 클라이언트 브라우저 워커 생성을 영구 금지합니다.
