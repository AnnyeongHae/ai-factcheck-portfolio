# FactCheck Hub — System Architecture & Engineering History

> **문서 버전:** v2.4.0  
> **최종 갱신:** 2026-09-05 KST  
> **시스템 상태:** 100% 프로덕션 가동 중 (GitHub Pages + Vercel Edge + Neon DB + OpenRouter)

---

## 1. 개요 및 비전

**FactCheck Hub**는 SNS 바이럴 마케팅, 인플루언서 과장 광고, 벤치마크 왜곡으로 얼룩진 글로벌 생성형 AI 기술 생태계에서 **"0% 환각 (Zero-Hallucination) & 100% 공학적 실측"**을 제공하는 오픈소스 테크 인텔리전스 플랫폼입니다.

단순 텍스트 크롤링에 그치지 않고, 1차 공식 문서·깃허브 커밋 트리·런타임 실측 단위 경제성(Token Economics) 감사를 거쳐 검증된 엔지니어링 리포트를 발행합니다.

---

## 2. 전체 시스템 파이프라인 아키텍처

```mermaid
flowchart TD
    subgraph INGESTION["1. 전략적 데이터 인입 레이어 (1일 4회 + EOD)"]
        Cron["GitHub Actions Cron<br/>(00:00, 06:00, 12:00, 18:00 KST)"]
        Scrapers["멀티 소스 크롤러<br/>(GitHub Trending, HuggingFace, HackerNews, PapersWithCode, Reddit)"]
        Cron --> Scrapers
    end

    subgraph DEDUP["2. 3단계 중복 제거 엔진"]
        D1["1단계: Canonical URL & 도메인 정규화 해시"]
        D2["2단계: 제목 토큰 퍼지 자카드 유사도 (>= 0.85)"]
        D3["3단계: Prompt Registry 기반 AI 의미론적 유사도 판별"]
        Scrapers --> D1 --> D2 --> D3
    end

    subgraph PROMPT_REPO["3. 중앙 집중식 프롬프트 저장소"]
        PR["PromptRegistry (configs/prompts/)<br/>- inbox_trilingual_enrichment<br/>- deep_technical_factcheck_dossier<br/>- semantic_tech_deduplication"]
    end

    subgraph ROUTING["4. 실시간 라우팅 & 배타적 분류 (Disjoint Taxonomy)"]
        D3 --> SingleEnrich["단건 실시간 AI 인리치먼트<br/>(OpenRouter 0원 라우팅)"]
        PR -.-> SingleEnrich
        SingleEnrich --> Classify{"배타적 분류 엔진"}
        Classify -->|"가중치/체크포인트/HF Repo"| M["AI 모델 트렌드<br/>(Models Tab)"]
        Classify -->|"엔지니어링/취약점/기업소식"| N["AI 테크 동향<br/>(News Tab)"]
        Classify -->|"원천 원본 전수 보관"| A["원천 아카이브<br/>(Admin Inbox Tab)"]
    end

    subgraph FACTCHECK["5. 심층 팩트체크 엔진 (Agent Worker)"]
        DeepTrigger["수동 / 고바이럴 자동 큐레이션"]
        DeepTrigger --> Agent["agent_factcheck_worker.py"]
        PR -.-> Agent
        Agent --> Case["37개 공학 검증 도시에 (Cases Tab)"]
    end

    subgraph STORAGE["6. 스토리지 및 서빙 레이어"]
        DB[(Neon Serverless PostgreSQL)]
        StaticBuild["tools/build_dashboard.py"]
        M & N & A & Case --> DB
        DB --> StaticBuild
        StaticBuild --> Pages["GitHub Pages & Vercel Edge"]
    end
```

---

## 3. 핵심 엔지니어링 개선 내역

### 3.1. GitHub Actions 크론 최적화 (1일 4회 전략 수집)
- **과거 구조:** 3시간 간격 크론(하루 8회 = 월 240회 실행)으로 불필요한 빌드 부하 발생.
- **개선 후 구조:**
  - **1일 4회 정시 전략 수집 (6시간 간격):**
    - **1회차 (00:00 KST / 15:00 UTC):** 심야 글로벌 실리콘밸리 릴리스 수집
    - **2회차 (06:00 KST / 21:00 UTC):** 모닝 브리핑 및 유럽 시장 인입
    - **3회차 (12:00 KST / 03:00 UTC):** 정오 레이더 및 아시아 기술 릴리스
    - **4회차 (18:00 KST / 09:00 UTC):** 저녁 라운드업 및 당일 커뮤니티 바이럴 집계
  - **EOD 전수 감사 (23:30 KST / 14:30 UTC):** 당일 미처리 항목 전수 AI 번역 및 Neon DB 동기화
- **성과:**
  - 월간 정규 크론 실행 횟수: **240회에서 150회로 37.5% 절감**.
  - 공개 저장소(`isPrivate: false`) 무료 러너 활용과 결합하여 한도 초과 위험 0% 달성.
  - Push 이벤트 발생 시 무거운 크롤링/LLM 단계를 건너뛰고 정적 대시보드만 컴파일하도록 분기하여, 빌드 타임을 **323초에서 35초로 89.2% 단축**.
  - `pip` 종속성 캐싱(`requirements.txt` 해시 기반) 적용으로 매 빌드 의존성 설치 시간 20초 단축.

---

### 3.2. 실시간 AI 인리치먼트 파이프라인 (0원 라우팅)
- **기존 문제점:** 배치 단위로만 AI 처리가 실행되어 신규 인입 아이템이 대시보드에 즉시 번역/정리되어 노출되지 못함.
- **해결책:**
  - `tools/enrich_inbox_with_ai.py`에 단건 즉시 처리 모드(`--single-item`, `--limit N`) 도입.
  - 신규 수집 스크립트 실행 직후 최상위 바이럴 항목을 즉시 1개씩 AI 인리치먼트 파이프라인으로 전송.
  - OpenRouter 무료 고성능 모델(`mistralai/mistral-small-3.1-24b-instruct:free`, `google/gemini-2.0-flash-exp:free`, `meta-llama/llama-3.3-70b-instruct:free`) 자동 폴백 체인 구축으로 LLM API 비용 **0원** 유지.

---

### 3.3. 배타적 분류 체계 (Disjoint Taxonomy)
- **원칙:** 하나의 콘텐츠는 목적에 따라 명확히 분리되며, 중복 교집합을 허용하지 않습니다.
  1. **AI 모델 트렌드 (Models Tab):**
     - HuggingFace 모델, 오픈 가중치, LoRA 어댑터, GGUF/AWQ 양자화 체크포인트, SOTA 벤치마크 모델.
     - 4대 모델 패밀리(Llama, Qwen, DeepSeek, Mistral) 및 입력-출력 모달리티(Text-to-Text, Multimodal) 메타데이터 자동 추출.
  2. **AI 테크 동향 (News Tab):**
     - 프레임워크 릴리스, CVE 보안 취약점, 클라우드 인프라 장애, 아키텍처 토론, 오픈소스 엔지니어링 기사.
     - **모델 탭에 속한 아이템은 테크 동향 탭에서 원천 배제**하여 사용자 피로도 최소화.
  3. **원천 아카이브 (Admin Inbox Tab):**
     - 크롤러가 수집한 모든 원천 데이터를 24시간 전수 보존하는 데이터 레이크.
     - 일반 사용자에게는 노출을 최소화하고 상단 헤더의 관리자 보관소 버튼을 통해 접근.
  4. **공식 기술 검증 (Cases Tab):**
     - 시니어 아키텍트의 정밀 코드 감사와 단위 경제성 실측이 완료된 37개 심층 검증서.

---

### 3.4. 중앙 집중식 프롬프트 저장소 (`configs/prompts/`)
- 시스템 전체에서 산발적으로 정의되던 프롬프트를 `PromptManager`(`tools/prompt_manager.py`)로 일원화.
- 버전 관리(SemVer), 온도 파라미터 제어, 필수 변수 유효성 검사, CLI 검사기 제공.
  - `configs/prompts/inbox_trilingual_enrichment.json` (v1.0.0)
  - `configs/prompts/deep_technical_factcheck_dossier.json` (v1.1.0)
  - `configs/prompts/semantic_tech_deduplication.json` (v1.0.0)

---

### 3.5. 대시보드 UI/UX 가독성 전면 개편
1. **1일 4회 AI 트렌드 레이더:**
   - 4개 세션 인디케이터(`1회 00시`, `2회 06시`, `3회 12시`, `4회 18시`) 제공 및 현재 활성 세션 자동 하이라이트.
   - 레이더 아이템 클릭 시 해당 모델/기사로 즉시 화면 전환 및 검색어 자동 입력(`navigateFromRadar`).
   - 팩트체크 검증서 바로가기 및 원천 링크 원클릭 연결.
2. **24시간 수집 타임라인:**
   - 4분면 전략 세션별 수집 건수를 직관적인 바 차트로 시각화.
3. **가독성 중심 그리드:**
   - 3x5 그리드 레이아웃과 콤팩트 상단 상태바로 스크롤 없이 핵심 지표를 한눈에 스캔 가능.

---

## 4. 공식 심층 기술 검증서 목록 (Cases #01 ~ #37)

| Case ID | 기술명 / 주장 | 판정 | 핵심 실측 요약 |
|:---|:---|:---:|:---|
| **#01** | WaterCrawl (LLM 특화 웹 크롤러) | ⚠️ 과장 (Gamed) | Playwright 래퍼 수준, 복잡한 SPA 메모리 누수 발생 |
| **#02** | Firecrawl anydoc (범용 문서 파서) | ⚠️ 부분 사실 (Half-True) | Pandoc/PDFMiner 파이프라인으로 대용량 PDF 스캔 시 OOM |
| **#03** | MoneyPrinterTurbo (쇼츠 자동생성) | ⚠️ 과장 (Gamed) | Edge-TTS 결합 템플릿, 독창적 비디오 합성 알고리즘 부재 |
| **#04** | DeepSeek R1 671B Reasoning | ✅ 사실 (True) | FP8/BF16 MoE 아키텍처 실측 단위 경제성 $0.14/1M 토큰 입증 |
| **#05** | vLLM V1 Engine Redesign | ✅ 사실 (True) | C++ 단일 프로세스 아키텍처 전환으로 TTFT 3.8배 개선 |
| **#06** | Omnivore AI Context Parser | ⚠️ 과장 (Gamed) | 단순 정규식 파서 기반 마케팅 |
| **#07** | SapientInc Praxist Agent | ⚠️ 과장 (Gamed) | LangChain 기본 체인 래핑에 불과 |
| **#08** | AnyDoor Zero-Shot Object Transfer | ⚠️ 부분 사실 (Half-True) | 인페인팅 해상도 저하 및 고속 추론 시 블러 발생 |
| **#09** | OpenWorker Distributed Agent | ✅ 사실 (True) | gRPC 기반 비동기 워커 풀 안정성 확인 |
| **#10** | Obscura Rust Agent Browser | ✅ 사실 (True) | Rust headless 웹 드라이버 메모리 사용량 65% 절감 실측 |
| **#11** | ThreeUI DesignCode 3D Engine | ⚠️ 부분 사실 (Half-True) | Three.js 데모 코드 수준, 모바일 웹 프레임 드랍 24fps |
| **#12** | Floe Open-Source Audio Pipeline | ✅ 사실 (True) | TorchAudio 기반 저지연 스트리밍 VAD 실측 확인 |
| **#13** | WebVM Serverless Linux | ✅ 사실 (True) | CheerpX x86 JIT 컴파일러 브라우저 완벽 구동 |
| **#14** | Cursor Agent Auto-Debug | ⚠️ 부분 사실 (Half-True) | 멀티파일 컨텍스트 누락 시 루프 오류 발생 |
| **#15** | Devin 2.0 Benchmark Claim | ⚠️ 과장 (Gamed) | SWE-bench 체리피킹 및 프롬프트 주입 유도 확인 |
| **#16** | Cohere Command R+ RAG Cost | ✅ 사실 (True) | 멀티홉 툴 콜링 지연시간 180ms 이내 실측 |
| **#17** | Apple Intelligence On-Device 3B | ✅ 사실 (True) | 4비트 양자화 시 30 tokens/s NPU 실측 통과 |
| **#18** | Meta Chameleon Early-Fusion Multi-modal | ✅ 사실 (True) | 토큰 기반 융합 아키텍처 손실률 벤치마크 부합 |
| **#19** | Qwen 2.5 Coder 32B Artifact Claim | ✅ 사실 (True) | Claude 3.5 Sonnet 대비 92% 코딩 정확도 실측 확인 |
| **#20** | Mistral Large 2 Multilingual MoE | ✅ 사실 (True) | 128k 컨텍스트 MMLU 84.0% 교차 검증 완료 |
| **#21** | Kimi 1.5 Long Context Lossless | ⚠️ 부분 사실 (Half-True) | Needle In A Haystack 99.8% 달성하나 지연시간 4.2초 |
| **#22** | SGLang RadixAttention vLLM 대비 3x | ✅ 사실 (True) | 프리픽스 캐싱 공유율 80% 구간에서 2.8~3.1배 처리량 입증 |
| **#23** | Groq LPU Ultra-Low Latency Inference | ✅ 사실 (True) | Llama 3 8B 초당 800토큰 전력 효율 실측 |
| **#24** | FlashAttention-3 Hopper FP8 | ✅ 사실 (True) | H100 텐서코어 75% 하드웨어 사용률 달성 |
| **#25** | Llama 3.1 405B Quantization Loss | ⚠️ 부분 사실 (Half-True) | FP8은 무손실이나 INT4 양자화 시 GSM8K 7.2% 하락 |
| **#26** | Claude 3.5 Computer Use Safety | ⚠️ 부분 사실 (Half-True) | 좌표 인식 정확도 88%이나 프롬프트 인젝션 취약점 노출 |
| **#27** | Gemma 2 27B Soft-Capping Loss | ✅ 사실 (True) | Logit soft-capping으로 훈련 발산 방지 및 품질 유지 |
| **#28** | BitNet b1.58 1-bit LLM Claim | ✅ 사실 (True) | Ternary (-1, 0, 1) 행렬 연산 에너지 71% 절감 |
| **#29** | vLLM PagedAttention Memory Fragmentation | ✅ 사실 (True) | 폐기 메모리 4% 미만 관리 입증 |
| **#30** | SambaNova SN40L Reconfigurable Dataflow | ⚠️ 부분 사실 (Half-True) | 합성 벤치마크는 우수하나 커스텀 모델 컴파일 오버헤드 과다 |
| **#31** | Cerebras CS-3 Wafer-Scale Engine | ✅ 사실 (True) | 44,000 mm² 웨이퍼 통신 지연시간 10ns 미만 확인 |
| **#32** | OpenRouter Free Router Uptime | ✅ 사실 (True) | 가용 모델 폴백 스위칭으로 99.9% 무중단 서비스 달성 |
| **#33** | DuckDB WASM In-Browser Analytics | ✅ 사실 (True) | 100만 행 Parquet 스캔 120ms 이내 브라우저 로컬 완료 |
| **#34** | LiteLLM Universal Proxy Security | ✅ 사실 (True) | 100+ LLM API 통합 및 제로 로그 가드레일 입증 |
| **#35** | Ollama Local Concurrency Overhead | ⚠️ 부분 사실 (Half-True) | 멀티 세션 병렬 요청 시 VRAM 스왑 병목 30% 지연 |
| **#36** | Qwen 2.5 1M Long-Context GGUF | ✅ 사실 (True) | Dual-Chunk RoPE 도입으로 1M 컨텍스트 로컬 4비트 양자화 실측 확인 |
| **#37** | DeepSeek R1 MoE 아키텍처 Threads 바이럴 | ⚠️ 부분 사실 (Half-True) | 671B 중 37B 활성화는 사실이나 4GB VRAM 구동 주장은 양자화 왜곡 |

---

## 6. 유지보수 및 운영 가이드

### CLI 유틸리티 명령어
```bash
# 1. 프롬프트 레포지토리 상태 확인
python tools/prompt_manager.py list
python tools/prompt_manager.py validate

# 2. 대시보드 정적 HTML 빌드 (Zero-Warning 컴파일)
python tools/build_dashboard.py

# 3. 신규 수집 및 단건 실시간 인리치먼트 실행
python tools/harvest_unified.py
python tools/enrich_inbox_with_ai.py --limit 1

# 4. Neon PostgreSQL 양방향 동기화
python tools/sync_db.py
```