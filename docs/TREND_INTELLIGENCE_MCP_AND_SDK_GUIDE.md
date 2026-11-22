# 🌐 Trend & Tech Intelligence: Python SDK & FastMCP 사용 가이드

본 프로젝트(`2026-08-31_WEB_Factcheck`)에 구축된 **20,000여 건의 글로벌 테크 트렌드·논문·GitHub·팩트체크 벡터 DB**를 다른 어떤 프로젝트나 AI 에이전트에서도 손쉽게 호출할 수 있도록 제공되는 **Python SDK** 및 **FastMCP 서버** 가이드입니다.

---

## 1. ⚡ FastMCP 서버 설정 (어느 프로젝트/에이전트에서나 3줄 등록)

Claude Desktop, Cursor, Antigravity, Windsurf 등 MCP를 지원하는 모든 클라이언트의 설정 파일(`mcp_config.json` 또는 `claude_desktop_config.json`)에 아래 블록을 추가하기만 하면 즉시 연동됩니다.

```json
{
  "mcpServers": {
    "trend-intelligence": {
      "command": "python",
      "args": [
        "d:/2026.06.21_Antigravity/2026-08-31_WEB_Factcheck/tools/trend_mcp_server.py"
      ],
      "env": {
        "DATABASE_URL": "postgresql://...",
        "VOYAGE_API_KEY": "pa-..."
      }
    }
  }
}
```
*(※ 본 저장소의 `.env` 파일이 이미 세팅되어 있다면 `env` 필드는 생략 가능합니다.)*

### 🛠️ 제공되는 6대 MCP 도구 (Tools)

1. `search_tech_trends(query, top_k=5, platform=None, category=None, min_similarity=0.35, sort_mode='balanced')`
   - 자연어 질문을 1024차원 벡터로 변환하여 24,000+건 DB에서 2단계 하이브리드 리랭킹(Sim + H-V-D + Stability + Recency) 적용 인출.
2. `compare_tech_ab_test(tech_a, tech_b)`
   - 두 기술(예: `Jev` vs `Jeva`, `Playwright` vs `Puppeteer`)의 실제 개발자 평판, 관련 논문/리포, 장단점을 DB 기반으로 대조.
3. `get_tech_deep_dive(keyword_or_repo)`
   - 특정 오픈소스 저장소나 프레임워크의 상세 지표, 스타 수, 한글 통찰(`hook_ko`), 인용 원문 링크 조회.
4. `get_daily_viral_spikes(target_date=None, limit=10)`
   - 언론·커뮤니티·코드가 동시 폭발한 H-V-D 크로스 바이럴 급상승 TOP 10 랭킹 조회.
5. `query_verified_factchecks(topic, limit=5)`
   - AI 기술 과장(Hype), 루머, 아키텍처 팩트체크 정본 보고서 조회.
6. `conduct_4pillar_factcheck(claim_or_topic, repo_name="", academic_query="", community_query="")` ⚡ **NEW in v2.1**
   - **Track B 온디맨드 사실 검증(Fact-Check) 전용 도구**: 사용자의 검증 요청 시 4대 정밀 기둥(학술 ArXiv, 개발자 HN Algolia, 원격 GitHub API Zero-Clone, 뉴스/사내 RAG)에서 노이즈 없는 시맨틱 카드를 추출하여 토큰을 99.8% 절약하면서 정밀 팩트체크 리포트를 생성.

---

## 2. 🐍 Python SDK (`trend_rag_sdk`) 직접 사용법

다른 파이썬 스크립트나 백엔드 서버에서 데이터베이스를 직접 쿼리하고 싶을 때 사용합니다.

### 1) 설치 및 경로 추가
```python
import sys
# 本 저장소 경로를 sys.path에 추가 (또는 pip install -e .)
sys.path.append("d:/2026.06.21_Antigravity/2026-08-31_WEB_Factcheck")

from trend_rag_sdk import TrendRAGClient
```

### 2) 핵심 사용 예제
```python
from trend_rag_sdk import TrendRAGClient

# 1. 클라이언트 생성 (자동으로 .env 및 VOYAGE_API_KEY 인식)
client = TrendRAGClient()

# 2. 자연어 시맨틱 검색
results = client.search("self-healing crawler agent stealth bypass", top_k=3)
for item in results:
    print(f"[{item.similarity:.4f}] {item.title}")
    print(f"  - 인사이트: {item.hook_ko}")
    print(f"  - 링크: {item.url}")

# 3. 기술 A/B 테스트 대조
comparison = client.compare_technologies("FastMCP", "REST API")
print("Option A matches:", len(comparison["tech_a"]["matches"]))
print("Option B matches:", len(comparison["tech_b"]["matches"]))

# 4. 실시간 바이럴 급상승 이슈 5건
spikes = client.get_daily_viral_spikes(limit=5)
for s in spikes:
    print(f"🔥 [{s['platform']}] {s['title']} (Peak: {s['peak_score']})")

# 5. Track B 온디맨드 4-Pillar 팩트체크 검증 (토큰 99% 절약)
verification = client.verify_claim_4pillar(
    claim_or_topic="vLLM PagedAttention KV cache memory efficiency",
    repo_name="vllm-project/vllm",
    academic_query="vLLM PagedAttention",
    community_query="vLLM memory leak OOM"
)
print("Token Reduction:", verification["token_diet_metrics"]["token_reduction_rate"])
print(verification["report_markdown"])
```

---

## 3. 🏗️ 아키텍처: Track A (자동 레이더) vs Track B (온디맨드 팩트체크)

```
[ Track A: 실시간 자동 트렌드 레이더 (100% Zero-LLM-Actions) ]
1. 다중 수집기 (GitHub Actions 1일 4회)
   ↓ (72개 피드 병렬 수집, raw_content_vault 적재)
2. 인세션 AI 정제 (Antigravity Cron 11:00/23:00 KST)
   ↓ (Flash Subagents 번역/요약 $0.00)
3. 크로스 바이럴 & H-V-D 랭킹 엔진 (recompute_spike_scores.py)
   ↓ (7일 활성 윈도우, Daily Hot 10 자동 선별)
4. SSOT 정본 DB & Edge CDN 서빙 (raw_trends_inbox)


[ Track B: 온디맨드 팩트체커 (Human Request 전용) ]
사용자/엔지니어 사실 검증 요청 (Human Request)
   ↓
conduct_4pillar_factcheck (tools/trend_mcp_server.py / trend_rag_sdk)
   ├── 1. Academic: ArXiv API (논문 이론 한계/수식)
   ├── 2. Developer Community: HN Algolia (실제 재현 버그/OOM)
   ├── 3. Remote Code: GitHub API (Strictly Zero-Clone 호스트 보안)
   └── 4. News & RAG: 사내 24k+ DB 교차 대조
   ↓
Token-Diet 시맨틱 카드 압축 (~99% 노이즈 제거, 89k -> ~1k 토큰)
   ↓
검증 리포트 생성 및 tools/upsert_factcheck_db.py 정본 DB 적재
```

---

## 4. 🎯 대화방 실전 활용 시나리오 (`5743f939-...` 스타일)

신기술 탐색이나 A/B 테스트 대화방에서 다음과 같이 자연어로 질문하면 에이전트가 MCP 도구를 통해 실시간 데이터를 주입받아 답변합니다:

- **프롬프트 1 (온디맨드 팩트체크 검증)**:
  > *"이번에 오픈소스 X가 기존 vLLM보다 메모리를 10배 아낀다는 소문이 도는데 `conduct_4pillar_factcheck`로 아카이브 논문 한계랑 깃허브 라이선스, HN 실사용 이슈 좀 교차 검증해줘."*
- **프롬프트 2 (A/B 테스트 검증)**:
  > *"이번에 봇 우회 크롤러를 만드는데, Playwright-Stealth와 Crawlee 중에 우리 DB 트렌드와 개발자 반응 상 어떤 게 더 안정적인지 `compare_tech_ab_test`로 비교해줘."*
- **프롬프트 3 (신기술 탐색)**:
  > *"2026년 최신 오픈소스 중에 Agent Harness 관련해서 토큰 비용 줄인 연구나 프로젝트가 있어? `search_tech_trends`로 5개만 뽑아줘."*
- **프롬프트 4 (급상승 테크 확인)**:
  > *"오늘 엔지니어링 커뮤니티에서 가장 화제가 된 기술 이슈 3개만 `get_daily_viral_spikes`로 가져와서 브리핑해줘."*

---

## 5. 📜 버전 히스토리 (Changelog)

### `v2.1.0` (2026-11-22) — *Track B 4-Pillar Factcheck & Token-Diet SDK/MCP 정식 탑재*
- **핵심 업그레이드**:
  - `conduct_4pillar_factcheck` MCP 도구 신설 (총 6대 표준 도구 완성).
  - `trend_rag_sdk/factcheck.py` 모듈 구축: `FourPillarEvidenceHarvester`, `FactcheckEngine`, `estimate_tokens`.
  - **4대 정밀 검증 기둥**:
    1. 학술(ArXiv API - 이론적 상한/벤치마크 한계)
    2. 개발자 커뮤니티(Hacker News Algolia - 실제 재현 버그/OOM/반응)
    3. 원격 코드 검증(GitHub REST API - Host Immunity 유지를 위한 Strictly Zero-Clone)
    4. 뉴스 및 사내 RAG 교차 대조(24k+ DB)
  - **99% 토큰 다이어트**: 웹페이지 Raw HTML 덤프(~89,000 토큰) 대신 핵심 시맨틱 카드만 추출하여 150~1,000 토큰(98.8~99.8% 절감)으로 사실 검증 수행.
  - Track A(자동 레이더)와 Track B(온디맨드 팩트체커)의 완벽한 파이프라인 분리 반영.

### `v2.0.0` (2026-11-17) — *2-Stage Hybrid Reranking Engine 탑재*
- **핵심 업그레이드**:
  - 단순 벡터 유사도 기반 Top-K 반환에서 **1차 Recall (Top 50) + 2차 4-Axis Hybrid Reranking** 구조로 전면 고도화.
  - **4대 결합 지표**: 의미 적합도(`Cosine Sim`) + 로그 정규화 H-V-D 화제성(`HVD_log` + Cross-Spike 가산) + 엔지니어링 안정성(`Stars/Forks/Comments`) + 최신성(`30일 반감기`).
  - `sort_mode` 지원: `'balanced'`(기본), `'stable_tech'`(검증된 기술 우선), `'hvd'`(바이럴 급상승 우선), `'similarity'`(순수 벡터).
- **DB 커버리지**: 24,200+건 (100% Voyage `voyage-4-lite` 1024-dim 임베딩).

### `v1.0.0` (2026-11-06) — *Initial Release*
- `trend_rag_sdk` Python 패키지 및 `tools/trend_mcp_server.py` (FastMCP 5대 표준 도구) 최초 구축.
