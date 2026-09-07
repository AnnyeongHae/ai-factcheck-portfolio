# 📰 IPTC 기반 2계층 뉴스 분류 체계 & AI 모델 생태계 세분화 명세서

> **문서 버전**: v2.0 | **작성 일자**: 2026-09-07  
> **분류 표준 기반**: IPTC (International Press Telecommunications Council) Media Topics Standard (NewsCodes v1.3+) & ACM Computing Classification System (CCS)

---

## 1. 도입 배경 및 비판적 반성 (Why Two-Tier?)

### 1.1 기존 1계층(단일 플랫) 카테고리의 붕괴
기존 시스템은 기술 중심의 8대 단일 카테고리(INFERENCE_OPT, AGENTS_DEVTOOLS, MULTIMODAL_AI, FOUNDATION_MODELS, INFRA_RAG_SECURITY, DEEP_SCIENCE_SPACE, MACRO_GLOBAL_BIZ, INDUSTRY_TRENDS)를 운용했습니다.
그러나 실제 수집 소스(Hacker News, GeekNews, Reddit 등)는 순수 AI 연구실 피드가 아닌 **범용 테크·교양 커뮤니티**입니다.

이로 인해 다음과 같은 치명적 오분류와 품질 문제가 발생했습니다:
1. **정치·사회 기사의 기술 침범**:
   - 기사: *"무장 남성이 오하이오 주지사 후보 에이미 액튼을 공격해 여러 명 부상"*
   - 결과: 본문에 *"보안 우려(security concerns)"*, *"attack"*이라는 단어가 들어있다는 이유로 **INFRA_RAG_SECURITY(사이버보안/인프라)**로 강제 할당됨.
2. **역사·인문학 기사의 갈 길 상실**:
   - 기사: *"고대 바빌로니아 사탕무 양고기 스튜 레시피 (기원전 1750년)"*
   - 결과: 갈 곳이 없어 강제로 INDUSTRY_TRENDS(일반 테크·SW)로 분류됨.
3. **단순 '기타' 격리의 위험성**:
   - 비기술 기사를 단순한 단일 쓰레기통(NON_TECH_GENERAL)에 몰아넣으면, 향후 수천 건의 다양한 글로벌 뉴스가 쌓였을 때 분류가 마비되고 검색 및 통계가 불가능해짐.

---

## 2. 권위 있는 표준 분류 체계의 이식 (Authoritative Foundations)

본 시스템은 로이터(Reuters), AP, AFP, 블룸버그(Bloomberg), 뉴욕타임스(NYT), 구글 뉴스(Google News) 등 글로벌 정통 언론사와 애그리게이터가 사용하는 국제 표준을 전면 이식했습니다.

### 2.1 IPTC Media Topics (NewsCodes)
* **제정 기구**: IPTC (International Press Telecommunications Council, 1965년 설립)
* **핵심 철학**: 모든 인간 사회의 정보와 사건을 17대 최상위 개념(Top-level Descriptors)으로 구분하고, 하위 세부 개념으로 다층 트리 전개.

### 2.2 ACM Computing Classification System (CCS)
* **제정 기구**: ACM (Association for Computing Machinery) & IEEE Computer Society
* **핵심 철학**: 컴퓨팅, 인공지능, 분산 시스템, 사이버보안의 하위 엔지니어링 세부 분야를 표준화.

---

## 3. 정식 2계층(Two-Tier) 계층형 분류 구조

### Tier 1: 글로벌 뉴스 보편 대분류 (Universal Domain - 대시보드 1차 필터)
사용자 UI 및 대시보드 메인 탭에서 노출되는 6대 핵심 대분류입니다:

| Tier 1 코드 | 표시 라벨 | IPTC 매핑 | 포함 범위 |
|:---|:---|:---|:---|
| **TECH_COMPUTING** | 💻 IT·컴퓨팅 | 13000000 (Science & Tech / IT) | AI 모델, 소프트웨어, 클라우드, 오픈소스, 하드웨어, 인터넷, 개발도구 |
| **SCIENCE_RESEARCH** | 🚀 과학·우주 | 13000000 (Science) | 우주로켓, 천문학, 양자물리, 생명과학, 첨단소재, 의학 연구 |
| **ECONOMY_FINANCE** | 🏦 경제·금융 | 04000000 (Economy, Business, Finance) | 거시경제, 중앙은행, 통화/금리, 금(Gold), 자산시장, 기업경영, 무역 |
| **POLITICS_POLICY** | 🏛️ 정치·정책 | 11000000 (Politics) | 정부 행정, 의회 선거, 외교 관계, 국가 안보, 공공 정책 |
| **LAW_CRIME_JUSTICE** | ⚖️ 사회·법률 | 02000000 (Crime, Law, Justice) | 사건사고, 강력범죄, 법원 판결, 빅테크 규제 단속, 시민 권리 |
| **CULTURE_HUMANITIES** | 🌿 문화·인문 | 01000000 (Arts, Culture) / 10000000 | 역사, 도서/서평, 요리/음식, 철학, 라이프스타일, 인간사 |

---

### Tier 2: 도메인별 엔지니어링 & 시사 소분류 (Engineering Specialization)
각 Tier 1 내부에서 작동하는 정밀 소분류입니다:

`
[Tier 1: TECH_COMPUTING]
  ├─ INFERENCE_SERVING  : 추론/서빙 최적화 (vLLM, SGLang, Ollama, AWQ, GGUF, FP8, CUDA)
  ├─ AGENTS_DEVTOOLS    : AI 에이전트 & 개발도구 (Browser Use, 코딩도구, CLI, 자동화 프레임워크)
  ├─ MULTIMODAL_MEDIA   : 멀티모달 & 미디어 (비전, 영상 Wan/MiniMax, 이미지 FLUX, 음성 Whisper)
  ├─ FOUNDATION_WEIGHTS : 파운데이션 & 오픈 가중치 (Qwen, DeepSeek, Llama 가중치/체크포인트)
  ├─ SYSTEM_CYBERSEC    : 인프라, 시스템 & 사이버보안 (Linux 커널, 컴파일러, strip 도구, 취약점)
  └─ SOFTWARE_WEB       : 일반 테크 & 소프트웨어 (웹 프레임워크, 브라우저, 셀프호스팅, 앱 개발)

[Tier 1: SCIENCE_RESEARCH]
  ├─ SPACE_ASTRONOMY    : 우주 발사체, 궤도 진입, 위성, 천체물리학 (Isar Aerospace, NASA 등)
  └─ DEEP_SCIENCE_BIO   : 신소재, 다이아몬드, 핵융합, 바이오/의학 연구

[Tier 1: ECONOMY_FINANCE]
  ├─ MACRO_TREASURY     : 중앙은행 금 회수, 통화정책, 금리, 인플레이션
  └─ BIZ_MARKETS        : 빅테크 실적, M&A, 자본시장, 스타트업 펀딩

[Tier 1: LAW_CRIME_JUSTICE & POLITICS_POLICY]
  ├─ TECH_ANTITRUST_POLICY: 빅테크 반독점 소송, AI 규제법, 개인정보 보호 정책
  └─ CIVIC_CRIME_INCIDENT : 시민사회 사건사고, 선거 유세, 강력 범죄 (← 오하이오 후보 피습 안착)

[Tier 1: CULTURE_HUMANITIES]
  └─ HISTORY_LIFE_CULTURE : 역사 유물, 고대 요리법, 인문학 에세이 (← 바빌로니아 양고기 스튜 안착)
`

---

## 4. 🤖 AI 모델 트렌드 생태계 세분화 (rtifact_type)

기존 "AI 모델 트렌드" 탭에는 모델 가중치 자체와 데모 웹앱, 에이전트 도구가 혼재되어 있었습니다. 이를 4대 서브 생태계로 세분화합니다:

`
┌──────────────────────────────────────────────────────────────┐
│ 1. 🤖 WEIGHTS (순수 파운데이션 & 가중치)                      │
│    - 정의: 다운로드하여 직접 서빙할 수 있는 모델 가중치 파일 │
│    - 포맷: GGUF, Safetensors, FP8, Base/Instruct 체크포인트 │
│    - 예시: deepseek-ai/DeepSeek-V3, Qwen/Qwen2.5-Coder       │
├──────────────────────────────────────────────────────────────┤
│ 2. 🛠️ SKILL_AGENT (AI 스킬 & 에이전트 하네스)               │
│    - 정의: 프롬프트 스킬셋, 도구 연동 하네스, CLI 에이전트    │
│    - 포맷: Python SDK, MCP 서버, Agent Framework             │
│    - 예시: ByteDance CUDA Agent, PRAXIST, Browser Use        │
├──────────────────────────────────────────────────────────────┤
│ 3. 🌐 WEB_SERVICE (인터랙티브 웹 & Spaces 데모)              │
│    - 정의: 브라우저에서 직접 체험하고 실행하는 라이브 서비스 │
│    - 포맷: Hugging Face Spaces, Gradio 앱, SaaS 데모         │
│    - 예시: enzostvs/deepsite, Virtual Try-On Web App         │
├──────────────────────────────────────────────────────────────┤
│ 4. 🎯 FINETUNE (도메인 특화 미세조정 / 어댑터)               │
│    - 정의: 특정 산업군(의료/법률/코딩) 맞춤형 LoRA 및 어댑터 │
│    - 포맷: LoRA 어댑터, 산업 특화 가중치                     │
│    - 예시: Med-Llama-Adapter, Financial-Qwen-LoRA            │
└──────────────────────────────────────────────────────────────┘
`

---

## 5. 🛡️ LLM 모델 풀 재편 및 더미 생성 방어 가드레일

### 5.1 cohere/north-mini-code 사태의 원인 및 재발 방지
* **문제 분석**: 코드 전용 모델에 복잡한 다국어 지시(Instruction)를 내리자, 스키마 설명 텍스트("hook": "엔지니어가 이 글을 지금 당장 읽어야 하는 1줄 결정적 훅 (한국어)")를 그대로 복사해 출력함.
* **대책 1 (우선순위 재편)**:
  
vidia/nemotron-3-super-120b-a12b:free, google/gemma-4-31b-it:free, minimax/minimax-m3:free를 최우선으로 배치하고, 
orth-mini-code는 텍스트 요약 풀에서 강등.
* **대책 2 (런타임 가드레일)**:
  출력된 텍스트에 프롬프트 지시문 문구가 포함될 경우 alidate_enriched_payload()에서 즉시 예외를 발생시키고 차순위 고성능 모델로 자동 페일오버.
* **대책 3 (프롬프트 예시 현실화)**:
  프롬프트 스키마의 지시문을 실제 모범 생성 사례로 변경하여 모델이 지침을 텍스트 값으로 오인하지 못하도록 차단.
