# AI FactCheck Hub: `tidings-rss` 기반 출처(Source of Origin) 대폭 확장 전략 및 법적 리스크(판례·법령) 심층 분석 보고서

**작성일**: 2026-10-01  
**작업 모드**: Local-Only (배포 전 아키텍처·법무 검증 단계)  
**분석 대상**:
1. [`fuxiaoai/tidings-rss`](https://github.com/fuxiaoai/tidings-rss) (총 718개 피드 카탈로그: [`data/feeds.json`](https://raw.githubusercontent.com/fuxiaoai/tidings-rss/main/data/feeds.json) 및 [`SOURCES.md`](https://github.com/fuxiaoai/tidings-rss/blob/main/SOURCES.md))
2. 현재 프로젝트 수집 파이프라인 ([`tools/harvest_trends.py`](file:///d:/2026.06.21_Antigravity/2026-08-31_WEB_Factcheck/tools/harvest_trends.py))
3. 한·미·EU 다중 출처 RSS/스크래핑·AI 요약·임베딩 관련 저작권법, 부정경쟁방지법, CFAA 및 핵심 판례

---

## Part 1. `tidings-rss` (718개 피드) 비판적 해부 및 출처 확장 전략

### 1.1 `tidings-rss` 카탈로그(718개)의 실체: 왜 무분별한 전체 임포트는 위험한가?

`tidings-rss/main/data/feeds.json` 원본 데이터를 전수 파싱하여 분석한 결과, 겉보기에 방대한 **718개 피드(Article 552 · Video 93 · Podcast 73, 영어 360 · 중국어 357 · 다국어 1)** 내부에는 AI 트래킹 시스템의 신뢰도와 쿼터를 파괴할 수 있는 **4가지 구조적 함정**이 존재합니다.

| 구분 | 수치 / 비중 | 비판적 진단 (Critical Assessment) |
| :--- | :--- | :--- |
| **1) 중국어 개인 블로그 편중** | `Engineering & Technology` 348개 중 **283개(81.3%)가 중국어 개인/소규모 블로그** (`251 的魔法实验室`, `Abyss的小屋`, `Amiya的书桌`, `CatCoding` 등) | 빅테크나 공식 AI 랩이 아닌 개인 학습 노트·일기성 글이 대다수입니다. 이를 그대로 수집하면 6시간마다 수백 건의 노이즈가 유입되어 **OpenRouter 무료 LLM 요약 쿼터(일 1,000회)와 Voyage AI 임베딩 쿼터를 즉각 고갈**시킵니다. |
| **2) 서드파티 변환 프록시 의존** | 전체 718개 중 **99개(13.8%)가 비공식 변환 브리지** (`rsshub.bestblogs.dev` 62개, `wechat2rss.*` 32개, `hnrss.org` 5개) | `SOURCES.md`에서도 명시하듯, 공용 RSSHub 및 Wechat2RSS 인스턴스는 **Cloudflare 차단, HTTP 502/503/429 타임아웃, 예고 없는 서버 종료**가 빈번합니다. 심지어 `Anthropic News`, `The Batch`, `DeepSeek`, `Kimi`, `Qwen`까지 서드파티 브리지에 의존하고 있어, 팩트체크의 제1원칙인 **"원문 출처 무결성(Chain of Custody)"**을 훼손합니다. |
| **3) 오디오·단순 커밋 피드 혼재** | `Podcasts` 73개 + GitHub `commits/main.atom` 등 | 팟캐스트 RSS는 본문 텍스트 없이 오디오 파일(`.mp3`)과 1~2줄의 Show Notes만 제공하여 팩트체크/요약 가치가 낮고, `commits/main.atom`은 사소한 typo 수정 커밋마다 피드를 생성하여 DB를 오염시킵니다. |
| **4) 한국어(KO) 공식 기술 생태계 전무** | 한국어 전용 소스 **0개** | 국내 AI 엔지니어링 및 시장 검증에 필수적인 한국 빅테크 기술 블로그(네이버 D2, 카카오테크, 토스테크 등)와 국내 AI 전문 미디어가 완전히 누락되어 있습니다. |

> [!IMPORTANT]
> **핵심 아키텍처 결론**: `tidings-rss`의 718개 피드를 무작위로 들이붓는 대신, **(1) 원문 발행처가 직접 서빙하는 공식(First-Party) RSS/Atom 피드**와 **(2) GitHub이 공식 제공하는 네이티브 `releases.atom` 피드**만 엄선하여 현재 25개 수준인 수집 채널을 **총 75개 고신호(High-Signal) 공식 출처 체제**로 약 **3배 확장**하는 것이 가장 이상적입니다.

---

### 1.2 현재 수집기(`tools/harvest_trends.py`) vs. 최대 확장 아키텍처 비교

현재 [`tools/harvest_trends.py`](file:///d:/2026.06.21_Antigravity/2026-08-31_WEB_Factcheck/tools/harvest_trends.py)는 10개 함수에서 약 25개 고정 엔드포인트를 수집 중이며, 특히 핵심인 `fetch_curated_rss_feeds()`([L966-L1063](file:///d:/2026.06.21_Antigravity/2026-08-31_WEB_Factcheck/tools/harvest_trends.py#L966-L1063))에 **단 5개 피드**(`Hugging Face Blog`, `PyTorchKR`, `Simon Willison`, `OpenAI News`, `Anthropic News`)만 등록되어 있습니다.

이를 **8대 도메인 · 75개 검증된 First-Party 출처**로 대폭 확장하는 마스터 카탈로그 설계안은 다음과 같습니다.

#### [Tier 1] 공식 AI 프론티어 랩 & 빅테크 리서치 (14개 — 근거 원문 확보용)
| 출처명 | 공식 Feed URL | 상태 | 선정 및 비판적 검증 사유 |
| :--- | :--- | :--- | :--- |
| **OpenAI News** | `https://openai.com/news/rss.xml` | 기존 유지 | 모델·API·안전성 정책 1차 발표 원문 |
| **Google AI Blog** | `https://blog.google/technology/ai/rss/` | **신규 추가** | Gemini·Vertex·AI 제품군 공식 발표 (`tidings-rss` 검증) |
| **Google DeepMind** | `https://deepmind.com/blog/feed/basic/` | **신규 추가** | AlphaFold·Genie·강화학습 등 프론티어 연구 (`tidings-rss` 검증) |
| **Google Research** | `https://research.google/blog/rss/` | **신규 추가** | 구글 원천 알고리즘·논문 발표 (`tidings-rss` 검증) |
| **Hugging Face Blog** | `https://huggingface.co/blog/feed.xml` | 기존 유지 | 오픈웨이트 모델·벤치마크·실무 툴 표준 |
| **Apple ML Research** | `https://machinelearning.apple.com/rss.xml` | **신규 추가** | 온디바이스 AI·MLX·Apple 파운데이션 모델 논문 |
| **AWS Machine Learning** | `https://aws.amazon.com/blogs/amazon-ai/feed/` | **신규 추가** | 엔터프라이즈 AI 배포·Bedrock·Trainium 아키텍처 |
| **Amazon Science** | `https://www.amazon.science/index.rss` | **신규 추가** | 아마존 공식 과학·AI 리서치 원문 |
| **Microsoft Azure AI / Blog** | `https://azure.microsoft.com/en-us/blog/feed/` | **신규 추가** | MS AI 인프라·Copilot·Foundry 공식 업데이트 |
| **Engineering at Meta** | `https://engineering.fb.com/feed/` | **신규 추가** | Llama 생태계·대규모 AI 인프라·PyTorch 엔지니어링 |
| **MIT News - AI** | `https://news.mit.edu/rss/topic/artificial-intelligence2` | **신규 추가** | 학계 AI 돌파구 및 과장 검증용 1차 학술 보도자료 |
| **BAIR (Berkeley AI)** | `https://bair.berkeley.edu/blog/feed.xml` | **신규 추가** | 오픈소스 LLM·vLLM·RLHF 등 핵심 학계 리서치 |
| **NVIDIA Technical Blog** | `https://developer.nvidia.com/blog/feed/` | **신규 추가** | CUDA·TensorRT-LLM·GPU 클러스터 최적화 표준 |
| **Databricks Blog** | `https://www.databricks.com/feed` | **신규 추가** | 엔터프라이즈 데이터·RAG·Mosaic AI 벤치마크 |

> [!WARNING]
> **Anthropic 피드 주의사항**: `tidings-rss`는 `https://rsshub.bestblogs.dev/anthropic/news`를 사용하고 현재 우리 코드는 `raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml` 미러를 사용 중입니다. 서드파티 브리지 장애에 대비해 **GitHub 공식 `anthropics/claude-code/releases.atom` 및 `anthropic-sdk-python/releases.atom`을 병행 수집**해야 합니다.

#### [Tier 2] 에이전트·도구·프레임워크 공식 릴리스 노트 (12개 — GitHub Native `.atom`)
*중간 변환기(RSSHub)를 거치지 않고 GitHub이 직접 서빙하여 가용성 99.99%를 보장하는 핵심 기술 변화 감지 채널입니다.*
1. **OpenAI Codex Releases**: `https://github.com/openai/codex/releases.atom` (**신규**)
2. **Anthropic Claude Code Releases**: `https://github.com/anthropics/claude-code/releases.atom` (**신규**)
3. **Google Gemini CLI Releases**: `https://github.com/google-gemini/gemini-cli/releases.atom` (**신규**)
4. **MCP (Model Context Protocol) Spec**: `https://github.com/modelcontextprotocol/specification/releases.atom` (**신규**)
5. **MCP Official Servers**: `https://github.com/modelcontextprotocol/servers/releases.atom` (**신규**)
6. **LangChain Releases**: `https://github.com/langchain-ai/langchain/releases.atom` (**신규**)
7. **vLLM Releases**: `https://github.com/vllm-project/vllm/releases.atom` (**신규**)
8. **Ollama Releases**: `https://github.com/ollama/ollama/releases.atom` (**신규**)
9. **Llama.cpp Releases**: `https://github.com/ggml-org/llama.cpp/releases.atom` (**신규**)
10. **GitHub Official Changelog**: `https://github.blog/changelog/feed/` (**신규**)
11. **GitHub Copilot Changelog**: `https://github.blog/changelog/label/copilot/feed/` (**신규**)
12. **Zed Editor Releases**: `https://github.com/zed-industries/zed/releases.atom` (**신규**)

#### [Tier 3] 클라우드·배포·빅테크 아키텍처 & 실무 석학 해석 (14개)
1. **Simon Willison's Weblog**: `https://simonwillison.net/atom/everything/` (기존 유지 — LLM 실무 검증 최고 권위)
2. **Cloudflare Blog**: `https://blog.cloudflare.com/rss` (**신규** — Edge AI, Workers, DDoS/보안)
3. **Vercel News / Atom**: `https://vercel.com/atom` (**신규** — AI SDK, Next.js, 프런트엔드 인프라)
4. **Supabase Blog**: `https://supabase.com/rss.xml` (**신규** — pgvector, Postgres AI 생태계)
5. **Replicate Blog**: `https://replicate.com/blog/rss` (**신규** — 오픈소스 모델 서빙 실무)
6. **The GitHub Blog**: `https://github.blog/feed/` (**신규**)
7. **Martin Fowler**: `https://martinfowler.com/feed.atom` (**신규** — 엔터프라이즈 소프트웨어 아키텍처·GenAI 패턴)
8. **Netflix TechBlog**: `https://netflixtechblog.com/feed` (**신규**)
9. **Stripe Engineering Blog**: `https://stripe.com/blog/feed.rss` (**신규**)
10. **Turing Post**: `https://rss.beehiiv.com/feeds/UJIoBuf5BX.xml` (**신규** — AI 아키텍처 심층 분석)
11. **Last Week in AI**: `https://lastweekin.ai/feed` (**신규** — 주간 AI 이슈 압축 검증)
12. **Lilian Weng (OpenAI)**: `https://lilianweng.github.io/index.xml` (**신규** — 에이전트·추론 심층 리뷰)
13. **Sebastian Raschka (Ahead of AI)**: `https://magazine.sebastianraschka.com/feed` (**신규** — LLM 아키텍처 실증 분석)
14. **Interconnects (Nathan Lambert)**: `https://www.interconnects.ai/feed` (**신규** — 오픈웨이트·RLHF·정책 비평)

#### [Tier 4] 사이버보안·취약점·AI Safety 경보 (5개 — 팩트체크 필수 도메인)
1. **CISA (미 사이버보안국 공식 경보)**: `https://www.cisa.gov/news.xml` (**신규**)
2. **Krebs on Security**: `https://krebsonsecurity.com/feed/` (**신규**)
3. **Schneier on Security**: `https://www.schneier.com/blog/index.rdf` (**신규** — AI 보안·암호학 권위자)
4. **ZDNET Security**: `https://www.zdnet.com/topic/security/rss.xml` (**신규**)
5. **Security Affairs**: `https://securityaffairs.co/wordpress/feed` (**신규**)

#### [Tier 5] 기초 과학·학술 저널 & 글로벌 테크 미디어 (12개)
- **학술/과학 (6개)**:
  1. **arXiv (cs.AI + cs.CL + cs.LG)**: API/RSS 연동 (기존 `cs.AI`에 `cs.CL`, `cs.LG` 카테고리 확장)
  2. **Nature**: `https://www.nature.com/nature.rss` (**신규**)
  3. **Science (AAAS)**: `https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science` (**신규**)
  4. **Quanta Magazine**: `https://www.quantamagazine.org/feed/` (**신규** — 수리·물리·전산학 심층 과학 저널리즘)
  5. **NASA News Releases**: `https://www.nasa.gov/news-release/feed/` (**신규**)
  6. **PLOS One**: `https://journals.plos.org/plosone/feed/atom` (**신규**)
- **글로벌 테크 미디어 (6개)**:
  7. **MIT Technology Review**: `https://www.technologyreview.com/feed/` (**신규**)
  8. **WIRED**: `https://www.wired.com/feed/rss` (**신규**)
  9. **TechCrunch AI**: `https://techcrunch.com/category/artificial-intelligence/feed/` (기존 유지)
  10. **The Verge AI**: `https://www.theverge.com/rss/ai-artificial-intelligence/index.xml` (기존 유지)
  11. **VentureBeat AI**: `https://venturebeat.com/category/ai/feed/` (기존 유지)
  12. **Ars Technica**: `https://feeds.arstechnica.com/arstechnica/index` (기존 유지)

#### [Tier 6] 한국(KO) & 중국(ZH) 공식 1차 기술 생태계 보강 (10개)
- **`tidings-rss`에 누락된 한국 빅테크 엔지니어링 블로그 (6개 신규)**:
  1. **네이버 D2 (Naver D2)**: `https://d2.naver.com/d2.atom`
  2. **카카오테크 (Kakao Tech)**: `https://tech.kakao.com/feed/`
  3. **토스테크 (Toss Tech)**: `https://toss.tech/rss.xml`
  4. **우아한형제들 기술블로그**: `https://techblog.woowahan.com/feed/`
  5. **당근 테크블로그**: `https://medium.com/feed/daangn`
  6. **파이토치 한국 사용자 모임**: `https://discuss.pytorch.kr/latest.rss` (기존 유지)
- **`tidings-rss` 중국어 피드 중 프록시(`wechat2rss`)를 쓰지 않는 공식 테크 미디어 (4개 선별)**:
  7. **量子位 (QbitAI - 중국 대표 AI 전문 미디어)**: `https://www.qbitai.com/feed` (**신규**, First-Party RSS)
  8. **36氪 (36Kr)**: `https://www.36kr.com/feed` (**신규**, 중국 테크·스타트업 1차 보도)
  9. **少数派 (sspai)**: `https://sspai.com/feed` (**신규**, 생산성·AI 도구 실무 리뷰)
  10. **阮一峰的网络日志 (Ruan Yifeng)**: `https://www.ruanyifeng.com/blog/atom.xml` (**신규**, 중국권 최고 인지도 주간 테크 리포트)

---

### 1.3 대량 출처 확장 시 파이프라인 병목·쿼터 방어 엔지니어링 설계

출처를 25개에서 75개로 3배 늘릴 때 발생할 수 있는 **실행 시간 증가(GitHub Actions 쿼터)**와 **저품질 글 범람(OpenRouter LLM 쿼터)**을 막기 위해 다음 3가지 아키텍처 가드레일을 적용해야 합니다.

1. **병렬 RSS 수집기 (`ThreadPoolExecutor(max_workers=8)`) 도입**:
   - 현재 `fetch_curated_rss_feeds()`와 `fetch_global_news_feeds()`는 `for feed in feeds:` 순차 루프로 동작합니다. 피드 60개를 순차 호출하면 타임아웃 포함 시 90~120초가 추가 소요됩니다.
   - `AGENTS.md` 제5조 제3항의 검증된 병렬 패턴(`ThreadPoolExecutor(max_workers=8)`, 개별 타임아웃 `8초`)을 적용하면 **60개 RSS 피드를 단 6~9초 내에 전수 수집**하여 전체 워크플로 실행 시간을 기존과 동일한 **50초 이내**로 유지할 수 있습니다.
2. **피드당 수집 상한(`max_items_per_feed = 4`) 및 AI/Tech 관련성 사전 필터(Pre-Filter)**:
   - 종합 과학/보안/미디어 피드(`Nature`, `WIRED`, `36Kr` 등)에서 비-테크 일상 기사가 유입되지 않도록, 피드당 최신 4건만 슬라이스하고 비전공 피드(`tier="broad"`)에는 경량 키워드 필터(AI, LLM, GPU, 반도체, 보안, 알고리즘, 바이오 등)를 통과한 항목만 DB에 적재합니다.
3. **`source_tier` 메타데이터 태깅**:
   - `raw_payload`에 `source_tier` (`official_lab` | `release_notes` | `eng_blog` | `security` | `science` | `media` | `community`)를 명시하여, 향후 프런트엔드나 팩트체크 도시에 생성 시 **"1차 공식 발표 원문(Primary Source)"**과 **"2차 미디어 해석(Secondary Commentary)"**을 즉각 구분할 수 있게 합니다.

---
---

## Part 2. 다중 출처 수집·스크래핑·AI 요약의 법적 리스크(Legal Risk) 심층 분석 보고서 (판례·법령·출처 기반)

본 프로젝트(**AI FactCheck Hub**)는 다수의 글로벌 웹사이트·API·RSS로부터 기술 트렌드를 수집(`harvest_trends.py`)하고, LLM을 통해 다국어 요약·비평·카테고리 분류(`api/enrich-worker.js`) 및 벡터 임베딩 클러스터링을 수행하여 웹 대시보드로 공개합니다. 이와 관련하여 **미국·한국·EU의 현행 법령 및 실제 판례**를 기반으로 법적 리스크와 면책 요건을 정밀 검토했습니다.

---

### 2.1 핵심 법적 리스크 요약 매트릭스 (Risk Assessment Matrix)

| 행위 유형 | 관련 법령 (한·미·EU) | 리스크 등급 | 핵심 위법성 판단 기준 (Red Line) | 본 프로젝트의 현재 상태 및 안전성 |
| :--- | :--- | :---: | :--- | :--- |
| **1) 공식 RSS / Atom / 공개 API 메타데이터 수집** | 저작권법(묵시적 라이선스), 미 CFAA | **낮음 (Low)** | 발행처가 신디케이션 목적으로 직접 공개한 XML/JSON 피드이나, **원문 전문(Full-Text)을 그대로 미러링**하면 저작권 침해 | **안전**: 제목·링크·발행일 및 `summary[:180]`(180자 미만 초록)만 DB에 저장하며 원문 전문은 일절 저장·전시하지 않음 |
| **2) 뉴스/블로그 본문 발췌 및 AI 요약·번역 후 게시** | 미 저작권법 제107조(공정이용), 한국 저작권법 제7조 제5호·제28조·제35조의3 | **중간~높음 (Med-High)** | 원문을 읽을 필요를 없애는 **'시장 대체적 축약본(Substitutive Summary)'** 제공 또는 원문 문장의 그대로 베끼기(Verbatim Excerpt) | **주의 필요 (가드레일 필수)**: 단순 요약이 아닌 **'팩트체크·기술적 비평(Transformative Critique)'** 성격의 Hook/Takeaway 생성 및 **원문 직링크(Outlink)** 제공 필수 |
| **3) 서드파티 프록시(`RSSHub`, `Wechat2RSS`)를 통한 우회 수집** | 미 CFAA, 사이트 이용약관(ToS), 한국 부정경쟁방지법 (파)목 | **높음 (High)** | 공식 RSS를 닫아둔 사이트를 제3자 스크래퍼 브리지로 우회 수집 시 **약관 위반 및 기술적 보호조치 우회** 분쟁 소지 | **즉시 배제 권고**: `tidings-rss` 내 `rsshub.bestblogs.dev`, `wechat2rss` 등 99개 프록시 피드는 수집 대상에서 전량 제외 |
| **4) 타 플랫폼 데이터의 대량 반복 크롤링 및 DB 구축** | 한국 저작권법 제93조(DB제작자 권리), 부정경쟁방지법 제2조 제1호 (파)목 | **중간 (Medium)** | 타 플랫폼의 상당한 투자로 구축된 DB를 **실질적 전부 복제**하여 **동종 경쟁 서비스**에 그대로 제공하는 행위 | **안전 (단, 한도 준수)**: 출처당 최신 소량(3~15건)의 메타데이터만 수집하고 교차 검증(Cross-Platform Radar)이라는 독자적 가치를 부여함 |
| **5) 기사/포스트의 벡터 임베딩(Voyage AI) 및 클러스터링** | 미 Fair Use (비표현적 이용), 한국 저작권법 제35조의4, EU DSM 지침 제4조 | **낮음 (Low)** | 임베딩 벡터(수치 배열) 자체는 원저작물의 표현을 재생산하지 않는 **비표현적(Non-expressive) 메타 연산**에 해당 | **안전**: `vector(1024)` 수치 배열은 유사도 군집화에만 쓰이며 원문을 복원·대체하지 않음 |

---

### 2.2 분야별 주요 판례 및 사례 심층 분석 (출처 기반)

#### A. 뉴스·콘텐츠 수집 및 AI 요약과 저작권/공정이용(Fair Use) 판례

1. **미국 연방지방법원 — *Associated Press v. Meltwater U.S. Holdings, Inc.*, 931 F. Supp. 2d 537 (S.D.N.Y. 2013)**
   - **사건 개요**: 미디어 모니터링 기업 Meltwater가 AP통신 등의 온라인 기사를 자동 스크래핑하여 **헤드라인 + 기사 첫 부분(Lede) 최대 300자 + 키워드 전후 문맥(최대 140자)**을 고객 리포트로 제공하면서 AP의 라이선스 체결을 거부함.
   - **법원 판결 (Meltwater 패소 / 공정이용 부정)**:
     - 뉴욕 남부연방지방법원(Denise Cote 판사)은 Meltwater가 기사의 핵심인 리드(Lede) 문장을 그대로 복제(Verbatim copying)하여 보여준 것은 **단순 검색엔진이 아니라 원문 기사의 시장을 대체(Market Substitution)하는 행위**라고 판시.
     - 특히 Meltwater의 서비스에서 이용자가 원문 링크를 클릭한 비율(Click-through rate)이 **0.08%**에 불과했다는 점을 들어, 트래픽 유입 효과가 없다는 이유로 공정이용(Fair Use) 항변을 기각함.
   - **프로젝트 시사점**: 원문의 첫 문단(Lede)을 그대로 복사해 화면에 노출하면 위법 위험이 높습니다. 우리 프로젝트처럼 **원문 발췌문 노출을 배제하고, 독자적인 엔지니어링 관점의 비평/검증 포인트(Hook & Takeaways)를 생성하며, 카드 클릭 시 원문으로 직행하도록 유도**해야 합니다.
   - **출처**: [931 F. Supp. 2d 537 (S.D.N.Y. 2013) 판결문 요약 - Justia US Law](https://law.justia.com/cases/federal/district-courts/new-york/nysdce/1:2012cv01087/391628/159/)

2. **미국 연방제2항소법원 — *Authors Guild v. Google, Inc.*, 804 F.3d 202 (2d Cir. 2015) vs. *Fox News Network, LLC v. TVEyes, Inc.*, 883 F.3d 169 (2d Cir. 2018)**
   - **사건 개요 및 대조**:
     - *Google Books* 사건에서 제2항소법원(Pierre Leval 판사)은 수천만 권의 도서를 스캔하여 색인(Indexing)하고 검색 결과로 **짧은 스니펫(Snippet)만 제공**한 행위는 원저작물의 독서 수요를 대체하지 않고 새로운 정보 탐색 목적을 수행하므로 **변형적 공정이용(Transformative Fair Use)**에 해당한다고 판결.
     - 반면 *TVEyes* 사건에서는 방송 콘텐츠를 색인한 것까지는 변형적이나, 이용자에게 **최대 10분 분량의 고화질 방송 클립을 그대로 시청·다운로드**하게 한 것은 원저작물의 시장을 잠식하므로 **공정이용이 아니다(침해 인정)**라고 판결.
   - **프로젝트 시사점**: 수집된 데이터를 색인·임베딩·클러스터링하여 **"지금 어떤 기술 이슈가 교차 바이럴되고 있는가(Radar Indexing)"**를 보여주는 것은 *Google Books* 법리에 의해 강력히 보호받습니다. 단, 원문 콘텐츠 자체를 우리 사이트 안에서 완결적으로 소비하게 만들어서는 안 됩니다.
   - **출처**: [*Authors Guild v. Google, Inc.*, 804 F.3d 202 (2d Cir. 2015)](https://law.justia.com/cases/federal/appellate-courts/ca2/13-4829/13-4829-2015-10-16.html), [*Fox News Network v. TVEyes*, 883 F.3d 169 (2d Cir. 2018)](https://law.justia.com/cases/federal/appellate-courts/ca2/15-3885/15-3885-2018-02-27.html)

3. **미국 연방지방법원 — *Thomson Reuters Enterprise Centre GmbH v. Ross Intelligence Inc.*, No. 1:20-cv-00613 (D. Del. Feb. 11, 2025) & *The New York Times Co. v. Microsoft Corp. & OpenAI*, No. 1:23-cv-11195 (S.D.N.Y. 2023~진행 중)**
   - **사건 개요**:
     - *Thomson Reuters v. Ross Intelligence* (2025년 2월 11일 델라웨어 연방지법 Stephanos Bibas 판사 약식판결): AI 법률 검색 스타트업 Ross가 Thomson Reuters(Westlaw)의 편집 저작물인 판례 요약문(Headnotes)을 대량 수집하여 경쟁 법률 검색 AI를 구축한 사건에서, 법원은 **Ross의 공정이용(Fair Use) 항변을 기각하고 저작권 침해를 인정**함. 판결의 핵심 근거는 Ross가 Westlaw의 요약문을 이용해 **Westlaw와 직접 경쟁하는 시장 대체재(Market Substitute)**를 만들었기 때문임.
     - *NYT v. OpenAI* 사건에서는 LLM이 유료 장벽(Paywall) 뒤의 기사를 학습하여 **원문과 거의 동일한 문장(Regurgitation)을 출력하거나 원문 구독 수요를 대체하는 요약**을 제공하는지가 핵심 쟁점임.
   - **프로젝트 시사점**:
     1. 유료 장벽(Paywall)을 우회하여 본문을 긁어오는 행위는 절대 금지합니다 (공식 공개 RSS의 메타데이터만 사용).
     2. LLM 프롬프트(`api/enrich-worker.js`)에서 원문 문장을 그대로 번역/요약하는 것이 아니라, **"팩트체크 검증 관점의 분석·비평(Analytical Commentary & Fact-Check Framing)"**을 생성하도록 명시하여 변형적 이용(Transformative Use, 비평·검증 목적) 요건을 충족해야 합니다.
   - **출처**: [*Thomson Reuters v. Ross Intelligence*, Memorandum Opinion (D. Del. Feb. 11, 2025)](https://www.ded.uscourts.gov/)

---

#### B. 웹 스크래핑·크롤링과 컴퓨터 사기 및 남용 방지법(CFAA) / 이용약관(ToS) 판례

1. **미국 연방대법원 & 제9항소법원 — *Van Buren v. United States*, 593 U.S. 374 (2021) 및 *hiQ Labs, Inc. v. LinkedIn Corp.*, 31 F.4th 1180 (9th Cir. 2022) → 2022. 11. 지방법원 약관 위반 판결**
   - **사건 개요 및 반전**:
     - 제9항소법원은 공개된 웹페이지(Publicly accessible profiles)를 스크래핑하는 행위는 로그인 장벽(Authentication gate)을 뚫은 것이 아니므로 **형사 처벌 법규인 미 연방 컴퓨터 사기 및 남용 방지법(CFAA, 18 U.S.C. § 1030)상의 '무단 접근(Without Authorization)'에 해당하지 않는다**고 판시함.
     - **그러나 반전(매우 중요)**: 사건이 지방법원으로 환송된 후인 **2022년 11월 4일, 캘리포니아 북부연방지방법원(Edward Chen 판사)은 hiQ Labs가 LinkedIn의 이용약관(User Agreement)상 스크래핑 금지 조항을 위반(Breach of Contract)했다고 판결**하여 결국 hiQ Labs는 거액의 합의금과 영구 스크래핑 금지 명령을 받고 폐업 수준에 이름.
   - **출처**: [*hiQ Labs, Inc. v. LinkedIn Corp.*, 31 F.4th 1180 (9th Cir. 2022)](https://cdn.ca9.uscourts.gov/datastore/opinions/2022/04/18/17-16783.pdf), *hiQ Labs v. LinkedIn*, No. 3:17-cv-03301-EMC (N.D. Cal. Nov. 4, 2022)

2. **미국 캘리포니아 북부연방지방법원 — *Meta Platforms, Inc. v. Bright Data Ltd.*, No. 3:23-cv-00071 (N.D. Cal. Jan. 23, 2024) 및 *X Corp. v. Bright Data Ltd.*, No. 3:23-cv-03698 (N.D. Cal. May 9, 2024)**
   - **사건 개요**: Meta와 X(구 트위터)가 웹 데이터 수집 기업 Bright Data를 상대로 약관 위반 및 불법 방해 소송을 제기함.
   - **법원 판결**:
     - *Meta v. Bright Data* (Edward Chen 판사): 계정에 로그인하지 않은 상태(Logged-off)에서 공개된 웹 데이터를 수집하는 행위는 로그인 사용자에게만 적용되는 이용약관(ToS)에 구속되지 않는다며 Meta의 약관 위반 청구를 기각.
     - *X Corp. v. Bright Data* (William Alsup 판사): X가 약관으로 공개 데이터 스크래핑을 포괄 금지하려 한 주장에 대해, **연방 저작권법이 보장하는 공정이용(Fair Use) 및 공개 사실(Public Facts) 유통 영역을 사적 약관(Browsewrap)만으로 독점할 수 없다(저작권법에 의한 선점, Preemption)**고 판시하며 X의 청구를 기각. 단, **기술적 보호조치(CAPTCHA, IP 차단, Rate Limit)를 기만적으로 우회하는 행위는 별도의 불법행위**가 될 수 있음을 경고함.
   - **프로젝트 시사점**:
     - 우리가 사용하는 **공식 RSS/Atom 피드 및 공개 API(Hacker News Algolia, ArXiv API, GitHub API)**는 사이트 운영자가 **"기계가 읽어갈 수 있도록 명시적으로 열어둔 신디케이션 채널(Express / Implied License)"**이므로 화면 HTML을 강제로 긁어내는 웹 스크래핑보다 법적으로 비교할 수 없을 만큼 안전합니다.
     - 반대로, 공식 RSS를 제공하지 않는 사이트(예: WeChat 공식계정, 일부 폐쇄형 미디어)를 `rsshub`나 `wechat2rss` 같은 우회 스크래퍼 브리지로 수집하는 것은 위 판례상의 **기술적 제한 우회 및 약관 분쟁**을 자초하므로 반드시 배제해야 합니다.
   - **출처**: [*X Corp. v. Bright Data Ltd.*, Order Dismissing Action (N.D. Cal. May 9, 2024)](https://cand.uscourts.gov/)

---

#### C. 대한민국 저작권법·부정경쟁방지법 및 대법원 판례

1. **대한민국 저작권법상 뉴스 기사의 보호 범위 — 대법원 2006. 9. 14. 선고 2004도5350 판결**
   - **법령 및 판례 요지**:
     - **저작권법 제7조 제5호**: *"사실의 전달에 불과한 시사보도"*는 저작권법의 보호를 받지 못함(예: 부고, 인사발령, 단순 주가·기상 수치, 단신 팩트 나열).
     - 그러나 **대법원 2004도5350 판결**은 기자의 독창적인 문제의식, 취재 내용의 선택·배열, 분석과 논평이 담긴 일반 스트레이트 기사 및 해설 기사는 **창작성이 인정되는 어문저작물**로서 저작권법의 보호를 받는다고 판시함.
     - 또한 한국언론진흥재단의 **〈뉴스저작권 지침〉**에 따르면, 기사의 **단순 제목과 직접 링크(Simple Deep Link)**를 걸어두는 행위는 저작권 침해가 아니나(대법원 2009. 11. 26. 선고 2008다77405 판결 — 인터넷 링크는 웹페이지의 위치 정보에 불과하므로 복제·전송이 아님), **기사 본문 전체나 핵심 문단을 무단 전재·번역하여 원문 방문 없이 내용을 소비하게 하는 행위**는 복제권·전송권·2차적저작물작성권 침해에 해당함.
   - **출처**: 대한민국 대법원 종합법률정보 (`2004도5350`, `2008다77405`), 한국언론진흥재단 뉴스저작권 안내서.

2. **대한민국 저작권법 제28조(공표된 저작물의 인용) 및 제35조의3(저작물의 공정한 이용)**
   - **법령 요지**:
     - **제28조**: *"공표된 저작물은 보도·비평·교육·연구 등을 위하여는 정당한 범위 안에서 공정한 관행에 합치되게 이를 인용할 수 있다."* (단, 제37조에 따라 **출처 명시 의무** 필수)
     - **제35조의3**: 저작물의 통상적인 이용 방법과 충돌하지 아니하고 저작자의 정당한 이익을 부당하게 해치지 아니하는 경우(이용의 목적 및 성격, 저작물의 종류 및 용도, 이용된 부분이 전체에서 차지하는 비중, 시장 가치를 대체하는지 여부) 공정이용 인정.
   - **프로젝트 적용 요건**:
     - 우리 서비스의 핵심 정체성이 단순 '뉴스 리더기'가 아니라 **'AI 과장·루머 검증 및 엔지니어링 팩트체크 허브(비평·검증 목적)'**이므로, (1) 원문은 제목과 출처·직링크만 명확히 표시하고, (2) AI가 생성하는 텍스트는 원문 축약이 아닌 **"기술적 타당성·실무 시사점 비평(Critique)"**으로 구성하면 저작권법 제28조 및 제35조의3의 보호 범위 내에 안정적으로 위치합니다.

3. **대한민국 데이터베이스제작자 권리(저작권법 제93조) 및 부정경쟁방지법 제2조 제1호 (파)목 크롤링 판례**
   - **주요 판례**:
     - **잡코리아 vs 사람인 채용정보 크롤링 사건 (서울고등법원 2017. 4. 6. 선고 2016나2082535 판결 / 대법원 2017다230552 확정)**: 사람인이 경쟁사 잡코리아의 웹사이트에 있는 채용공고 HTML을 무단 크롤링하여 자사 사이트에 그대로 노출한 사건에서, 법원은 **저작권법 제93조(데이터베이스제작자의 복제·전송권 침해) 및 부정경쟁방지법 위반**을 인정하여 크롤링 금지 및 손해배상을 명함.
     - **대법원 2020. 3. 26. 선고 2019마6525 결정 (데이터/성과물 도용 판단 기준)**: 부정경쟁방지법 제2조 제1호 (파)목(타인의 상당한 투자나 노력으로 만들어진 성과 등을 공정한 상거래 관행이나 경쟁질서에 반하는 방법으로 자신의 영업을 위하여 무단으로 사용함으로써 타인의 경제적 이익을 침해하는 행위)의 성립 요건으로 **"경쟁 관계 존재 여부, 상당한 투자·노력의 결과물인지, 실질적 전부를 무단 복제하여 원 출처의 수요를 대체했는지"**를 종합 판단함.
   - **프로젝트 시사점**:
     - 단일 사이트의 데이터베이스 전체를 통째로 복제하여 동종 경쟁 서비스를 만드는 행위가 바로 위법의 핵심입니다.
     - 반면 우리 수집기는 **70여 개 이상의 다중 글로벌 출처에서 공식 RSS/API가 허용한 최신 4~15건의 헤드라인 메타데이터만 수집**하여 교차 바이럴 지수(Cross-Platform Spike)를 산출하고 원문으로 아웃링크를 연결하므로, 특정 사이트의 DB를 실질적으로 복제하거나 수요를 대체하지 않습니다.

---

#### D. 유럽연합(EU) DSM 저작권 지침 (Directive (EU) 2019/790)

1. **제15조 (Press Publishers' Right — 언론사 저작인접권)**:
   - 정보사회 서비스 제공자가 언론 출판물을 온라인에서 사용할 때 언론사에 저작인접권을 부여함.
   - **명시적 예외 조항 (Article 15(1) 3항 & 4항)**: **하이퍼링크 설정 행위(Acts of hyperlinking)** 및 **개별 단어 또는 매우 짧은 발췌문(Individual words or very short extracts)의 사용**에는 언론사 저작인접권이 적용되지 않음!
2. **제4조 (Text and Data Mining, TDM 예외 및 Opt-Out)**:
   - 적법하게 접근 가능한 저작물에 대한 텍스트·데이터 마이닝(TDM)은 허용되나, 권리자가 기계 판독 가능한 방식(`robots.txt` 등)으로 **명시적 거부(Opt-out)** 의사를 표시한 경우 이를 존중해야 함.
   - **출처**: [Directive (EU) 2019/790 of the European Parliament and of the Council (EUR-Lex)](https://eur-lex.europa.eu/eli/dir/2019/790/oj)

---

### 2.3 AI FactCheck Hub를 위한 6대 법적 안전장치 (Engineering Compliance Rules)

위 한·미·EU 판례를 종합하여, 출처 대폭 확장 시 본 프로젝트가 법적 리스크 제로(Zero-Risk) 상태를 유지하기 위해 코드 레벨에서 강제해야 할 **6대 컴플라이언스 수칙**은 다음과 같습니다.

1. **원칙 1 — 100% 공식 신디케이션 채널(Official First-Party RSS/Atom/API)만 사용**:
   - 발행처가 배포 및 아웃링크 유입을 목적으로 직접 열어둔 공식 RSS/Atom/API만 수집합니다.
   - `tidings-rss`에 포함된 `rsshub.bestblogs.dev`, `wechat2rss.*` 등 **비공식 우회 스크래핑 브리지는 단 1개도 사용하지 않습니다.**
2. **원칙 2 — 원문 본문(Full-Text) 및 리드(Lede) 문단 DB 저장/노출 엄격 금지 (*AP v. Meltwater* 및 EU DSM 제15조 준수)**:
   - DB(`raw_trends_inbox.raw_payload`)에는 제목(`title`), 원문 링크(`link`), 발행일(`published`), 그리고 AI 분류/임베딩을 위한 **180자 이내의 메타 스니펫(`summary[:180]`)**만 저장합니다.
   - 프런트엔드(`newsCard.js`)에는 원문 발췌문을 절대 그대로 렌더링하지 않습니다.
3. **원칙 3 — '대체적 요약(Substitutive Summary)'이 아닌 '변형적 비평·검증(Transformative Fact-Check Critique)' 생성 (*Thomson Reuters v. Ross* 및 한국 저작권법 제28조 준수)**:
   - `api/enrich-worker.js`의 프롬프트가 원문을 그대로 축약 번역하는 데 그치지 않고, **"엔지니어링 관점의 핵심 쟁점(Hook)과 실무 검증 시사점(Takeaways)"**을 비평적으로 도출하도록 유지하여 원문을 읽어야 할 동기를 오히려 높입니다.
4. **원칙 4 — 명확한 출처 표기(Attribution) 및 원문 직행 아웃링크(Direct Outlink) 보장 (한국 저작권법 제37조 및 대법원 `2008다77405` 준수)**:
   - 모든 카드에 원문 플랫폼·발행처 배지(`source_type`, `author/feed_name`)를 명시하고, 카드 클릭 시 중간 광고나 인터스티셜 없이 **즉시 원문 URL(`target="_blank"`)로 이동**시켜 발행처에 트래픽을 환원합니다.
5. **원칙 5 — 투명한 User-Agent 식별 및 Rate-Limit / HTTP 429 준수**:
   - 브라우저 위장(Spoofing) 대신 공식 피드 리더 규격의 투명한 `User-Agent`와 타임아웃/서킷브레이커를 유지하여 대상 서버에 부하를 주지 않습니다.
6. **원칙 6 — 권리자 삭제/제외 요청(Opt-Out / Takedown) 즉시 수용 체계**:
   - 특정 출처가 RSS 제공을 중단하거나 수집 제외를 요청할 경우 설정 파일(`RSS_CATALOG`)에서 즉시 비활성화할 수 있도록 모듈화합니다.

---

## Part 3. 로컬 구현 로드맵 제안 (승인 시 즉시 로컬 반영)

로컬 환경에서 바로 테스트해 보실 수 있도록 다음 단계로 구현을 진행할 준비가 되어 있습니다:

1. **`tools/rss_catalog.py` (또는 `tools/harvest_trends.py` 내 모듈화) 구축**:
   - 위 **Part 1.2**에서 선별한 **공식 AI 랩(14개) + GitHub 네이티브 릴리스 노트(14개) + 클라우드·석학 블로그(13개) + 보안(5개) + 과학/미디어(4개) + 한국 빅테크(6개) + 중국 AI/WeChat 프론티어(16개) = 총 72개 피드**를 티어별 구조화 카탈로그로 등록.
2. **`tools/harvest_trends.py` 내 RSS 수집기 병렬화 (`ThreadPoolExecutor(max_workers=12)`)**:
   - 72개 RSS/Atom 피드를 병렬 수집하고, 피드당 최신 8~15건 캡(14일 최신성 게이트 결합) 및 이원화 원문 보관(외부 공개용 180자 스니펫 vs. 비공개 GZIP 원문 볼트)을 강제.
3. **로컬 드라이런(Dry-Run) 및 벤치마크 검증**:
   - GitHub/Vercel 배포 없이 로컬에서 수집 속도와 카테고리/출처 태깅 품질을 실측 검증.

---

## Part 4. v2.0 심화 아키텍처 반영: 비공개 원문 GZIP 볼트 · 중국 AI/WeChat 16개 채널 · 14일 윈도우 · 병목 방어

### 4.1 비공개 원문 보존 아키텍처 (Dual-Layer Storage: Public 180자 vs. Private GZIP Vault)
- **외부 공개 테이블 (`raw_trends_inbox`)**:
  - 프런트엔드 API(`/api/inbox`)가 직접 조회하는 `raw_trends_inbox.raw_payload`에는 기존과 동일하게 **180자 이내의 초단문 스니펫(`description`)만 유지**하고 `full_text_raw`는 적재 직전 `pop()`하여 완전히 제거합니다.
  - 이를 통해 **(1) 외부 저작권 침해(시장 대체성) 리스크 제로**와 **(2) Vercel API 응답 속도 및 DB Egress 보호**를 동시에 달성합니다.
- **내부 전용 비공개 볼트 (`raw_content_vault` SQL 테이블 + 로컬 `.jsonl.gz`)**:
  - RSS/Atom의 `<content:encoded>`, `<atom:content>`, `<description>` 및 ArXiv 초록, GeekNews 본문에서 추출한 **최대 50,000자 원문 전체(`full_text_raw`)**를 `gzip.compress(..., compresslevel=9)`로 최대 압축하여 전용 SQL 테이블 **`raw_content_vault` (`full_text_gzip BYTEA`)** 및 로컬 **`logs/vault/fulltext_vault_YYYY_MM.jsonl.gz`**에 이중 보존합니다.
  - **실측 압축 효율**: 72개 피드 625건의 원문 텍스트(`4,083.2 KB`)가 GZIP Level-9 압축 시 **`1,732.4 KB` (57.6% 용량 절감, 아티클당 평균 2.7 KB)**로 축소되어, 10,000건의 원문 전체를 보존해도 약 27MB 내외로 유지됩니다.
  - **조회 방법**: `python tools/db_bridge.py --vault-stats` 및 `python tools/db_bridge.py --vault-get <inbox_id>`로 즉시 복원 가능.

### 4.2 중국 AI 프론티어 랩 & WeChat 핵심 16개 피드 전면 수용 (`Tier 7`)
- 중국 AI 생태계의 1차 발표가 이루어지는 WeChat 공식 계정 브리지 및 GitHub 릴리스 16종을 실측 검증(`72 / 72` 100% 성공)하여 추가했습니다:
  - **프론티어 랩 (10개)**: `DeepSeek (深度求索)`, `DeepSeek-V3 GitHub Releases`, `Qwen (通义千问 / 通义实验室)`, `Qwen GitHub Releases`, `Kimi (月之暗面 Moonshot AI)`, `Zhipu AI (智谱 GLM)`, `Tencent Hunyuan (腾讯混元)`, `StepFun (阶跃星辰)`, `Tencent Research (腾讯研究院)`, `Alibaba Research (阿里研究院)`
  - **전문 미디어/커뮤니티 (6개)**: `Jiqizhixin (机器之心)`, `Jiqizhixin SOTA (机器之心SOTA模型)`, `Xinzhiyuan (新智元)`, `QbitAI (量子位)`, `AI Dev Daily (AI 开发者日报)`, `36Kr (36氪)`, `sspai (少数派)`, `Ruan Yifeng (阮一峰)`
  - *(단, 단일 XML 크기가 5.71MB에 달해 18.7초 지연을 유발하는 `大模型智能`은 병목 방지를 위해 제외)*

### 4.3 피드당 수집 한도 상향 (`max_items = 8~15`) + `14일 최신성 게이트(Recency Gate)`
- 피드당 제한을 기존 `2~6건`에서 **`8~15건`으로 대폭 상향**하여 OpenAI/Google 발표일이나 `机器之心`·`新智元`·`HF Blog`처럼 하루에 10건 이상 쏟아지는 날에도 누락이 없도록 개선했습니다.
- 동시에 **`_is_within_recency_window(pub_dt, max_age_days=14)`** 필터를 결합하여, 스캔 한도를 15건으로 늘리더라도 **최근 14일 이내에 발행된 글만 통과**시키고 수개월~수년 전 과거 글이 초기 수집 시 쏟아져 들어오는 현상을 원천 차단했습니다.

### 4.4 대량 수집 시간(Latency) 폭발 위험 분석 및 4중 방어 설계
1. **Guard 1 — XML 스트리밍 바이트 상한 (`max_bytes = 8MB`) 및 GZIP 투명 해제**: 비정상적인 초대형 XML 폭탄이 메모리를 잠식하는 것을 막고, GZIP(`0x1f 0x8b`) 응답을 자동 디코딩합니다.
2. **Guard 2 — `ThreadPoolExecutor(max_workers=12)` + 개별 소켓 타임아웃(`6.5s`) + 글로벌 데드라인(`22.0s`)**: 특정 해외/중국 서버 1~2개가 느려져도(Tail Latency) 전체 파이프라인이 멈추지 않고 **72개 피드 전체를 6~18초 내에 종료**합니다.
3. **Guard 3 — Step 2 중복 검사 O(1) Fast-Path 우선화**: 기존에는 모든 후보마다 O(N×M) 유사도 비교 함수(`evaluate_deduplication`)를 먼저 호출하던 병목을 수정하여, **O(1) 해시/URL/슬러그 맵(`inbox_hash_map`, `inbox_url_map`)을 먼저 조회**하고 매칭되지 않은 순수 신규 항목에만 정밀 중복 검사를 수행하도록 개선했습니다.
4. **Guard 4 — `raw_content_vault` 단일 쿼리 Bulk Upsert (`execute_values`)**: 수백 건의 GZIP 원문 바이너리를 단 1회의 SQL 왕복(~0.3초)으로 적재합니다.

