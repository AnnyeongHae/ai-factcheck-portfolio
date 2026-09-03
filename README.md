# 🌐 AI Fact-Check & Autonomous Tech Intelligence Portfolio

<div align="center">

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue)
![NodeJS](https://img.shields.io/badge/Node.js-22.x-green)
![Neon PostgreSQL](https://img.shields.io/badge/Database-Neon%20Postgres%20(Tier%202)-00E599?logo=postgresql)
![Vercel](https://img.shields.io/badge/Backend-Vercel%20Serverless-black?logo=vercel)
![GitHub Pages](https://img.shields.io/badge/Deployment-GitHub%20Pages%20Live-181717?logo=github)
![Gemini SOTA](https://img.shields.io/badge/AI%20Engine-Gemini%203.6%20%2F%203.8%20Flash-8E75B2?logo=google)

**"소셜 미디어와 기술 마케팅의 자극적인 후킹(Hooking)과 과장 광고의 껍데기를 벗겨내고,  
실제 엔지니어링 실체와 공학적 벤치마크를 정밀 실측하는 오픈소스 팩트체킹 & 자율 인텔리전스 시스템"**

[🔗 라이브 대시보드 열람 (GitHub Pages)](https://annyeonghae.github.io/ai-factcheck-portfolio/) · [⚡ Vercel Edge 프로덕션](https://ai-factcheck-portfolio.vercel.app/)

</div>

---

## 💡 1. 프로젝트 기획 배경 & 엔지니어링 철학 (Philosophy)

> *"요즘 쏟아져 나오는 AI 신기술과 오픈소스 프로젝트들을 보면, 소셜 미디어와 마케팅의 'Hooking'이 지나치게 요란합니다.  
> '누구나 10분 만에 억대 매출', '기존 기술 100배 압도', 'AI가 목소리만 듣고 95% 정확도로 질병 진단'...  
> **엔지니어로서 '저게 진짜 돌아갈까? 실제 하드웨어 대역폭과 비용 한계는 얼마일까?'를 직접 뜯어보고 실측 검증하고 싶어서** 이 서비스를 만들었습니다.  
> 
> 하지만 매일 손으로 찾아다니며 검증하기엔 세상의 변화가 너무 빨랐습니다.  
> 그래서 **Hugging Face, ArXiv, GeekNews, GitHub의 최신 트렌드를 24/7 자율 수집하고, AI가 3개국어로 요약·분류하며, 클라우드 DB에 동기화하는 자율 인텔리전스 파이프라인**까지 구축하게 되었습니다."*

---

## 🏛️ 2. 전체 엔드-투-엔드 시스템 아키텍처 (End-to-End Pipeline)

본 시스템은 **(1) 24/7 멀티 소스 자율 수집 ➔ (2) AI 3개국어 인리치먼트 ➔ (3) Neon DB 클라우드 동기화 ➔ (4) 다단계 에이전틱 팩트체크 위원회 ➔ (5) Vercel 서버리스 & 정적 듀얼 배포**로 순환하는 완전 자동화 파이프라인입니다.

```mermaid
flowchart TD
    subgraph SOURCING["1. 24/7 멀티 소스 자율 수집기 (Harvester)"]
        HF["🤗 Hugging Face<br/>(Trending Models/Spaces)"]
        ARX["📑 ArXiv Preprints<br/>(AI/CS/Bio Papers)"]
        GN["⚡ GeekNews<br/>(국내 개발자 핫 토픽)"]
        GH["🐙 GitHub Trending<br/>(Stars & Fork Spikes)"]
        
        HF & ARX & GN & GH -->|HTTP Polling & RSS| HARVEST["tools/harvest_trends.py<br/>(지문 해시 기반 무중복 수집)"]
        HARVEST --> INBOX[("inbox/*.json<br/>(로컬 큐레이션 인박스)")]
    end

    subgraph ENRICHMENT["2. 지능형 AI 인리치먼트 (Trilingual Engine)"]
        INBOX --> ENRICH["tools/enrich_inbox_with_ai.py<br/>(Gemini Flash Adaptive RPM Throttling)"]
        ENRICH -->|자동 번역 & 분류| META["• KO/EN/ZH 3개국어 완벽 대칭<br/>• 핵심 한 줄 훅(Hook) 추출<br/>• 모델 패밀리 & 기술 도메인 태깅"]
    end

    subgraph CLOUD_DB["3. Neon Postgres Cloud DB (Knowledge Core)"]
        META --> DB_BRIDGE["tools/db_bridge.py<br/>(원자적 배치 동기화)"]
        DB_BRIDGE --> NEON[("Neon Serverless Postgres<br/>• verified_factchecks (32건)<br/>• raw_trends_inbox (230+건)<br/>• factcheck_alternatives<br/>• factcheck_community_signals")]
    end

    subgraph AGENTIC_FACTCHECK["4. 다단계 에이전틱 팩트체크 위원회 (Multi-Agent Council)"]
        NEON -->|분석 대기열 QUEUED| COUNCIL["tools/factcheck_worker.py<br/>(자율 심층 팩트체크 에이전트 연합)"]
        COUNCIL -->|실측 도시에 생성| DOSSIERS[("investigations/<case_id>/<br/>(정밀 공학 검증 도시에)")]
        DOSSIERS --> GRAPH["configs/tech_graph_schema.json<br/>(기술 인용 계보망 자동 노드 연동)"]
        COUNCIL --> LEDGER["logs/token_usage_ledger.json<br/>(실시간 토큰 회계 원장)"]
    end

    subgraph DEPLOYMENT["5. 듀얼 엣지 실시간 배포 (Dual Edge Serving)"]
        GRAPH & DOSSIERS --> BUILD["tools/build_dashboard.py<br/>(Zero-Warning Clean Compiler)"]
        BUILD --> PAGES["GitHub Pages CDN<br/>(annyeonghae.github.io)"]
        BUILD --> VERCEL["Vercel Serverless CDN<br/>(/api/queue, /api/portfolios)"]
    end

    style SOURCING fill:#e0e7ff,stroke:#6366f1
    style ENRICHMENT fill:#fef3c7,stroke:#f59e0b
    style CLOUD_DB fill:#d1fae5,stroke:#10b981
    style AGENTIC_FACTCHECK fill:#f3e8ff,stroke:#8b5cf6
    style DEPLOYMENT fill:#fee2e2,stroke:#ef4444
```

---

## 🔬 3. 차세대 다단계 에이전틱 팩트체커 아키텍처 (Multi-Agent Fact-Check Council)

단순히 텍스트를 요약하는 1회성 LLM 호출은 **"그럴싸한 환각(Plausible Hallucination)"**을 만들어냅니다.  
본 시스템은 이를 극복하기 위해 **4개 영역의 전문 서브에이전트가 상호 대질하는 심의관 체계**를 운영합니다:

```mermaid
flowchart LR
    subgraph INTAKE["1. 분해"]
        Q["대기열 안건"] --> ATOM["🧩 Claim Atomizer<br/>(수치/스펙 단위 명제 분해)"]
    end

    subgraph MULTI_AGENTS["2. 병렬 심층 조사 연합"]
        ATOM --> AG1["📄 Primary Harvester<br/>(원문 전문 스크래핑 & 코드 대조)"]
        ATOM --> AG2["⚖️ Alternatives Matrix Agent<br/>(과거 레거시 vs 현대 대안 기술 장단점)"]
        ATOM --> AG3["💬 Community Signals Agent<br/>(Reddit/HN/GeekNews 긍·부정 실사용례)"]
        ATOM --> AG4["⚔️ Adversarial Red Team<br/>(통계 왜곡, 하드웨어 병목 집요 적발)"]
    end

    subgraph VERDICT["3. 교차 심의 & 최종 판정"]
        AG1 & AG2 & AG3 & AG4 --> AUDIT["⚖️ Lead Auditor Council<br/>(상호 대질 및 Verdict 확정)"]
        AUDIT --> OUT["🏆 VERIFIED_TRUE / HALF_TRUE / GAMED"]
    end

    style ATOM fill:#e0e7ff,stroke:#6366f1
    style AG2 fill:#fef3c7,stroke:#f59e0b
    style AG3 fill:#dbeafe,stroke:#3b82f6
    style AG4 fill:#fee2e2,stroke:#ef4444
    style AUDIT fill:#f3e8ff,stroke:#8b5cf6
```

### 🔍 대표적 에이전틱 실측 성과 (단발성 API vs 에이전틱 모드 비교)
1. **Case #32: ArXiv 외로움 예측 멀티모달 모델 실측 (arXiv:2609.02606)**
   - *단발성 LLM*: "교차 어텐션으로 외로움 91.2% AUC 정확도 진단 성공" (가상 수치 환각 및 무조건 참 판정)
   - *에이전틱 실측*: 310명 전화 인터뷰 원문 발굴 ➔ **실제 상관계수는 \( r = 0.298 \)에 불과** ➔ 연구진 공식 결론 *"단독 진단 도구 사용 절대 불가, 보조 지표에 한정"* 규명 ➔ **`HALF_TRUE` 정정 판정**.
2. **Case #30: M4 Pro Mac mini 로컬 LLM 서버 (48GB UMA)**
   - *실측 결과*: Qwen 35B A3B MoE 구동 시 273GB/s 대역폭에서 **34.2 tok/s** 이론치 완벽 수렴. 아이들 전력 5W(월 전기료 3천원 미만).
   - *커뮤니티 시그널 대조*: 35B MoE는 최적이나 70B 밀집 모델 구동 시 9 tok/s로 급락하며 램 납땜 증설 불가 한계 병기.

---

## 📁 4. 정제된 프로젝트 디렉토리 구조

```
ai-factcheck-portfolio/
├── .github/workflows/          # ⚙️ GitHub Actions CI/CD (수집·번역·팩트체크·DB싱크·배포)
├── api/                        # ⚡ Vercel Serverless Functions
│   ├── health.js               # 백엔드 헬스체크
│   ├── portfolios.js           # 싱글톤 커넥션 풀 기반 포트폴리오 API (정적 폴백 탑재)
│   └── queue.js                # 대기열 등록/토글/조회 API (입력 검증 및 감사 로그)
│
├── configs/                    # 🎯 엔지니어링 설정 및 인용 계보망
│   ├── tech_graph_schema.json  # 인터랙티브 D3.js 3D/2D 기술 인용 계보망 스키마
│   └── user_persona_alignment.json # 사용자 도메인별 큐레이션 가중치
│
├── dashboard/                  # 📊 대시보드 코어 배포본 (Verified: 32, Models: 88, News: 61)
├── docs/                       # 🌐 GitHub Pages 정적 호스팅 루트
├── inbox/                      # 📥 24/7 트렌드 인박스 (JSON 기반 230여 건 원천 데이터)
├── investigations/             # 🏆 [검증 완료 도시에] 32개 공식 심층 팩트체크 리포트 코어
├── logs/                       # 📜 토큰 회계 원장 및 수집·인리치먼트 히스토리
│   ├── token_usage_ledger.json # AI 추론 실측 토큰 및 원화 환산 회계 원장
│   └── ai_enrichment_history.json
│
├── public/                     # 🚀 Vercel Edge 정적 애셋
├── specs/                      # 📑 아키텍처 명세서 및 기술 백서 아카이브
│   ├── CRITICAL_SYSTEM_REVIEW_AND_ROADMAP.md
│   ├── DATABASE_SCHEMA_DESIGN.md
│   └── PIPELINE_ARCHITECTURE.md
│
├── tools/                      # 🛠️ 핵심 자동화 파이프라인 CLI 도구
│   ├── harvest_trends.py       # 1단계: 4대 소스 무중복 자율 수집기
│   ├── enrich_inbox_with_ai.py # 2단계: Gemini AI 3개국어 인리치먼트
│   ├── factcheck_worker.py     # 3단계: 대기열 감지 및 자율 팩트체크 워커
│   ├── db_bridge.py            # 4단계: Neon Postgres 클라우드 양방향 동기화
│   └── build_dashboard.py      # 5단계: 대시보드 컴파일러 (Hash Router & Clean Build)
│
├── server.js                   # 💻 로컬 Express/Node.js 개발 서버
└── README.md                   # 📖 메인 포트폴리오 프로젝트 문서
```

---

## 🚀 5. 로컬 실행 및 재현 가이드

### 1) 환경 변수 설정 (`.env`)
```bash
GEMINI_API_KEY="your-gemini-api-key"
DATABASE_URL="postgresql://neondb_owner:password@ep-host.neon.tech/neondb?sslmode=require"
```

### 2) 의존성 설치
```bash
# Python 패키지
pip install google-genai psycopg2-binary python-dotenv requests beautifulsoup4

# Node.js 패키지
npm install
```

### 3) 로컬 개발 서버 실행
```bash
node server.js
# 브라우저에서 http://localhost:3000 접속
```

### 4) 자율 파이프라인 수동 실행
```bash
# 1. 최신 트렌드 자율 수집
python tools/harvest_trends.py

# 2. 신규 안건 AI 3개국어 번역 및 요약
python tools/enrich_inbox_with_ai.py --all --batch-size 5

# 3. 대기열(Queue) 안건 자율 팩트체크 실행
python tools/factcheck_worker.py --limit 3

# 4. Neon Cloud DB 동기화 및 대시보드 빌드
python tools/db_bridge.py --sync-all
python tools/build_dashboard.py
```

---

## 📊 6. 엔지니어링 메트릭 및 토큰 경제성 (Token Economics)

- **누적 검증 완료 도시에 (Verified Portfolios)**: **32건**
- **인박스 모니터링 안건**: **230여 건** (HF Models 88건, News 61건)
- **도시에 1건당 평균 소모 토큰**: 약 **6,000 ~ 8,000 토큰** (Thinking CoT 포함)
- **도시에 1건당 실측 생성 비용**: **$0.0014 ~ $0.0028 (약 1.9원 ~ 3.8원)** ☕
- **서버리스 응답 속도 (TTFB)**: 싱글톤 커넥션 풀 적용으로 **300ms ➔ 45ms (85% 단축)**

---

## 📜 7. 라이선스 & 기여 (License)
본 프로젝트는 [MIT 라이선스](LICENSE) 하에 자유롭게 열람, 포크 및 응용이 가능합니다.  
소셜 미디어의 기술적 과장을 걸러내고 진정한 공학적 팩트를 추구하는 모든 개발자를 환영합니다!
