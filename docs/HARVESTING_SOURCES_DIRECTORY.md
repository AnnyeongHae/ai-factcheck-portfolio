# 📚 Multi-Source Trend Harvesting Directory & Master Registry
> **버전**: v1.0 (2026-09-02)  
> **상태**: Active Production Live  
> **자동화 스케줄**: GitHub Actions 6시간 단위 자동 크론 (`0 */6 * * *`)  
> **엔진**: `tools/harvest_trends.py` (3-Step Pipeline: 100% Ingest -> Metric Upsert -> Novel Deduplication)  
> **원칙**: 향후 신규 수집 채널이 추가될 때마다 본 문서를 동기화하여 아키텍처와 출처 인벤토리를 영구 보존할 것.

---

## 1. 수집 파이프라인 개요 (Pipeline Overview)

FactCheck Hub 수집 엔진은 전 세계 오픈소스 생태계, 글로벌 AI 연구소, 국내외 개발자 커뮤니티의 트렌드를 다채널로 모니터링합니다.

### 4대 수집 원칙
1. **No Early Drop (1단계 100% 수집)**: 사전 필터링 없이 일단 전 채널 후보를 무조건 수집하여 메트릭을 추적.
2. **Metric Lifecyle Tracking (2단계 갱신)**: 기존 항목 매칭 시 `created_at` 수치 보존 + `updated_at` 수치 갱신 및 delta/growth_rate 계산.
3. **Strict Validation & Deduplication (3단계 정제)**: 이미 포트폴리오로 검증된 URL 배제, 루트 도메인 차단, 순수 신규 아이템만 저장.
4. **Stealth & Anti-Tracking**: 최신 데스크톱 브라우저 지문 로테이션, UTM 및 ChatGPT 트래커 사전 제거, 레퍼러 차단.

---

## 2. 채널별 수집 소스 마스터 인벤토리 (Source Inventory)

| # | 채널명 | 플랫폼 | 엔드포인트 / 프로토콜 | 수집 주기 | 수집 데이터 & 특징 | 상태 |
|---|:---|:---|:---|:---|:---|:---:|
| **1** | **GeekNews (긱뉴스)** | 🇰🇷 한국판 HN | `https://news.hada.io/rss/news` (Atom) | 6시간 크론 | 국내 개발자 AI/오픈소스 큐레이션 및 토론 (25건) | **LIVE** |
| **2** | **Hacker News Top/Best** | 🌍 글로벌 커뮤니티 | `https://hacker-news.firebaseio.com/v0/` (REST) | 6시간 크론 | 상위 80개 스토리 중 AI/Tech 키워드 매칭 및 점수 > 150 | **LIVE** |
| **3** | **Hugging Face Models** | 🌍 오픈소스 AI 허브 | `https://huggingface.co/api/models` (REST) | 6시간 크론 | Trending Score 상위 30개 오픈 가중치 모델 | **LIVE** |
| **4** | **Hugging Face Spaces** | 🌍 AI 데모 허브 | `https://huggingface.co/api/spaces` (REST) | 6시간 크론 | Trending 상위 25개 인터랙티브 웹 데모 | **LIVE** |
| **5** | **GitHub High-Velocity** | 🐙 글로벌 오픈소스 | `https://api.github.com/search/repositories` | 6시간 크론 | 최근 14일 이내 신규 생성 & Stars > 30 급상승 레포 | **LIVE** |
| **6** | **ArXiv CS.AI / CS.CL** | 📄 학술 논문 | `http://export.arxiv.org/api/query` (Atom) | 6시간 크론 | MoE, Reasoning, VLM 등 최신 AI/CL 논문 20건 | **LIVE** |
| **7** | **Hugging Face Blog** | 🌍 공식 기술 블로그 | `https://huggingface.co/blog/feed.xml` (RSS) | 6시간 크론 | 양자화, 추론 최적화, 벤치마크 공식 기술 릴리즈 | **LIVE** |
| **8** | **Simon Willison Weblog** | 🌍 AI 엔지니어링 | `https://simonwillison.net/atom/everything/` | 6시간 크론 | 온디바이스 AI, LLM 툴링, 팩트체크 권위자 분석 | **LIVE** |
| **9** | **Reddit r/LocalLLaMA** | 🌍 오픈 LLM 커뮤니티 | `https://www.reddit.com/r/LocalLLaMA/hot.json` | 6시간 크론 | 온디바이스 경량 모델 및 파인튜닝 실무 토론 (보안 우회 모니터링) | **MONITOR** |

---

## 3. 향후 추가 연동 예정 레퍼런스 (Backlog Sources)

| 소스명 | 유형 | 공식 피드 / API 엔드포인트 | 기대 효과 |
|:---|:---|:---|:---|
| **요즘IT (Yozm IT)** | 🇰🇷 테크 매거진 | `https://yozm.wishket.com/magazine/feed/` (RSS) | 국내 IT 기업들의 실무 LLM 도입기 및 아키텍처 칼럼 |
| **Latent Space** | 🌍 AI 엔지니어링 | `https://www.latent.space/feed` (Substack RSS) | 최상위 AI 랩 연구원 인터뷰 및 SOTA 트렌드 |
| **Lobste.rs** | 🌍 엄격한 초대제 테크 | `https://lobste.rs/rss` (RSS) | 노이즈 없는 고밀도 시스템 프로그래밍 & AI 토론 |
| **Google DeepMind Blog** | 🌍 프론티어 AI 랩 | `https://blog.google/technology/ai/rss/` (RSS) | Gemini, AlphaFold 공식 릴리즈 |
| **OpenAI Research News** | 🌍 공식 리서치 | `https://openai.com/news/rss.xml` (RSS) | OpenAI 공식 발표 및 모델 출시 |

---

## 4. 신규 소스 확장 시 Agent 작업 수칙 (Agent Protocol)

추후 사용자가 신규 수집 출처를 추가하거나 확장을 요구할 경우, Agent는 다음 4단계를 수행해야 합니다:

1. **URL & 스텔스 검증**: 해당 출처의 RSS/Atom/API가 유효한지 파이썬으로 사전 검증.
2. **`tools/harvest_trends.py` 모듈 연동**:
   - `fetch_json` 또는 `fetch_xml`을 사용해 스텔스 헤더 및 UTM 스트립을 자동 적용.
   - `add_candidate()`에 규격화된 딕셔너리로 삽입.
3. **UI 셀렉터 및 듀얼 링크 갱신**: `tools/build_dashboard.py`의 필터 옵션과 카드 링크 버튼에 대응.
4. **본 문서(`docs/HARVESTING_SOURCES_DIRECTORY.md`) 업데이트**: 인벤토리 표에 소스 추가 및 버전 갱신.
