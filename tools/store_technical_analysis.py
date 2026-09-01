import json
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

# Ensure UTF-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from tools.db_bridge import load_env_db_url

def store_python_vs_awesome_analysis():
    analysis_data = {
        "analysis_key": "python_stdlib_vs_awesome_python",
        "title": "Python Standard Library vs Awesome-Python: Batteries Included 철학의 한계와 서드파티 고성능 생태계의 기술적 진화",
        "base_standard": "Python Standard Library (Batteries Included / CPython Runtime)",
        "third_party_ecosystem": "Awesome-Python (Third-Party Open-Source Ecosystem)",
        "core_philosophy_comparison": {
            "python_stdlib": {
                "philosophy": "Batteries Included (무설치 완결성 & 극도의 하위 호환성)",
                "creator": "Guido van Rossum (1991)",
                "governance": "PEP (Python Enhancement Proposal) & Python Software Foundation",
                "release_cadence": "1년 주기 마이너 릴리즈 (보수적 진화)",
                "pros": "Zero-dependency 무설치 안정성, 10년 후에도 깨지지 않는 API 계약",
                "cons": "CPython 바이트코드 해석 오버헤드, GIL(Global Interpreter Lock) 제약, 최신 하드웨어(SIMD/GPU) 직접 가속 불가"
            },
            "awesome_python": {
                "philosophy": "Specialized High-Performance & Rapid Innovation (도메인 특화 고성능 & 빠른 파괴적 혁신)",
                "curator": "Vinta Chen (2014) & Global Open Source Community (230k+ Stars)",
                "governance": "탈중앙화 오픈소스 생태계 (PyPI)",
                "release_cadence": "수시 릴리즈 (SemVer 기반 고속 반복)",
                "pros": "C/C++/Rust FFI 바인딩을 통한 10~100배 연산 가속, 현대적 DX (Type Hinting, Asyncio, Pydantic)",
                "cons": "의존성 지옥(Dependency Hell), 공급망 공격 위험, 유지보수 중단/파편화 리스크"
            }
        },
        "domain_lineage_matrix": [
            {
                "domain": "HTTP & Network I/O",
                "stdlib": "urllib.request / http.client (동기 블로킹, 장황한 API)",
                "gen1_thirdparty": "requests (Kenneth Reitz - 인간 친화적 동기 API 표준)",
                "gen2_sota": "httpx / aiohttp (Tom Christie - Asyncio 비동기 + HTTP/2 + 커넥션 풀링)"
            },
            {
                "domain": "Web Data Parsing & Scraping",
                "stdlib": "html.parser / xml.etree (단순 문자열 토크나이저, JS 렌더링 불가)",
                "gen1_thirdparty": "BeautifulSoup / Scrapy (Leonard Richardson / Scrapinghub - DOM 트리 탐색 & 배치 크롤링)",
                "gen2_sota": "Playwright + Crawl4AI (Microsoft / Unclecode - Chromium CDP 조작 + 비동기 LLM 토큰 압축 SOTA)"
            },
            {
                "domain": "Data Serialization & Validation",
                "stdlib": "json / dataclasses (순수 파이썬 dict 파싱, 런타임 타입 검증 부재)",
                "gen1_thirdparty": "marshmallow / ujson (동적 스키마 유효성 검사)",
                "gen2_sota": "Pydantic v2 + orjson (Samuel Colvin - Rust PyO3 Core + SIMD 제로카피 고속 직렬화 SOTA)"
            },
            {
                "domain": "Data Analysis & Tabular Compute",
                "stdlib": "csv / sqlite3 (단일 행 반복 처리, 메모리 비효율)",
                "gen1_thirdparty": "Pandas / NumPy (Wes McKinney - C-배열 메모리 연속 블록 벡터화)",
                "gen2_sota": "Polars (Ritchie Vink - Rust Apache Arrow 기반 멀티스레드 병렬 쿼리 엔진 SOTA)"
            },
            {
                "domain": "High-Throughput Web & LLM Serving",
                "stdlib": "wsgiref / http.server (단일 스레드/프로세스 블로킹)",
                "gen1_thirdparty": "Gunicorn / Flask / Django (WSGI 프로세스 멀티플렉싱)",
                "gen2_sota": "FastAPI + vLLM / SGLang (Tiangolo / Woosuk Kwon - uvloop 비동기 + GPU KV-Cache 페이징 서빙 SOTA)"
            }
        ],
        "performance_bottlenecks": {
            "gil_impact": "Python StdLib 스레딩은 단일 CPU 코어에 고정되나, 서드파티(NumPy, Polars, vLLM)는 C/Rust/CUDA 레벨에서 GIL을 릴리즈(Py_BEGIN_ALLOW_THREADS)하여 멀티코어/GPU 병렬성을 100% 활용함.",
            "memory_overhead": "StdLib의 모든 객체는 PyObject 헤더(8~16바이트) 오버헤드가 발생하나, 서드파티는 Apache Arrow/PyTorch Tensor 등 비관리형 연속 메모리 버퍼를 직접 할당하여 메모리 점유를 80% 이상 절감함."
        },
        "engineering_tradeoffs": {
            "when_to_use_stdlib": [
                "운영체제 시스템 관리 스크립트 및 경량 CLI 도구",
                "보안 감사 요건이 극도로 엄격하여 외부 의존성(pip) 설치가 금지된 에어갭(Air-Gapped) 환경",
                "10년 이상의 장기 유지보수가 요구되는 임베디드 리눅스 데몬"
            ],
            "when_to_use_awesome_ecosystem": [
                "초당 수만 건의 I/O를 처리해야 하는 마이크로서비스 백엔드 (FastAPI/httpx)",
                "수십 기가바이트의 대용량 비정형 데이터 정제 및 RAG 파이프라인 (Polars/Crawl4AI)",
                "최신 생성형 AI 모델의 실시간 양자화 서빙 및 LLM 오케스트레이션 (vLLM/SGLang)"
            ]
        }
    }

    # Save to local docs as well
    local_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "python_vs_awesome_analysis.json")
    with open(local_path, "w", encoding="utf-8") as f:
        json.dump(analysis_data, f, indent=2, ensure_ascii=False)
    print(f"[+] Saved local knowledge file at: {local_path}")

    db_url = load_env_db_url()
    if not db_url:
        print("[!] No DATABASE_URL or NEON_KEY found. DB sync skipped.")
        return

    print("[*] Connecting to Neon Postgres DB...")
    conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ecosystem_technical_analyses (
            id SERIAL PRIMARY KEY,
            analysis_key VARCHAR(120) UNIQUE NOT NULL,
            title VARCHAR(255) NOT NULL,
            base_standard VARCHAR(100) NOT NULL,
            third_party_ecosystem VARCHAR(100) NOT NULL,
            core_philosophy_comparison JSONB NOT NULL,
            domain_lineage_matrix JSONB NOT NULL,
            performance_bottlenecks JSONB NOT NULL,
            engineering_tradeoffs JSONB NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cur.execute("""
        INSERT INTO ecosystem_technical_analyses 
        (analysis_key, title, base_standard, third_party_ecosystem, core_philosophy_comparison, domain_lineage_matrix, performance_bottlenecks, engineering_tradeoffs)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (analysis_key) 
        DO UPDATE SET 
            title = EXCLUDED.title,
            core_philosophy_comparison = EXCLUDED.core_philosophy_comparison,
            domain_lineage_matrix = EXCLUDED.domain_lineage_matrix,
            performance_bottlenecks = EXCLUDED.performance_bottlenecks,
            engineering_tradeoffs = EXCLUDED.engineering_tradeoffs;
    """, (
        analysis_data["analysis_key"],
        analysis_data["title"],
        analysis_data["base_standard"],
        analysis_data["third_party_ecosystem"],
        json.dumps(analysis_data["core_philosophy_comparison"], ensure_ascii=False),
        json.dumps(analysis_data["domain_lineage_matrix"], ensure_ascii=False),
        json.dumps(analysis_data["performance_bottlenecks"], ensure_ascii=False),
        json.dumps(analysis_data["engineering_tradeoffs"], ensure_ascii=False)
    ))

    conn.commit()
    cur.close()
    conn.close()
    print("[+] Successfully persisted 'Python StdLib vs Awesome-Python' Technical Analysis to Neon Postgres DB!")

def store_prompts_chat_analysis():
    prompts_analysis = {
        "analysis_key": "prompts_chat_evolution_analysis",
        "title": "f/prompts.chat (120k Stars): 단순 프롬프트 큐레이션의 바이럴 원인과 4단계 LLM 제어 기술 진화사",
        "base_standard": "Raw Natural Language Text Prompting (Act as Persona Pattern)",
        "third_party_ecosystem": "Model Context Protocol & Virtual Machine Harness (Structured Steering & Agentic SOTA)",
        "core_philosophy_comparison": {
            "gen1_prompts_chat": {
                "philosophy": "Crowdsourced Static Persona Prompting (Act as [Role] 패턴의 집대성)",
                "creator": "Fatih Kadir Akın (@f) - 2022.12",
                "star_metric": "★ 120k+ GitHub Stars",
                "pros": "LLM 초창기 인컨텍스트 페르소나 제어의 대중화, 초저진입장벽(Markdown CSV 기여)",
                "cons": "비구조화된 텍스트로 인한 환각 빈발, 2026년 기준 컨텍스트 윈도우 희석(Attention Dilution) 및 토큰 낭비"
            },
            "gen4_modern_harness": {
                "philosophy": "Deterministic Tool Calling & In-Context Virtual Machine (MCP 및 상태 머신 기반 에이전트 제어)",
                "pioneers": "Anthropic (MCP), DSPy (Stanford), Claude Code, PRAXIST",
                "pros": "JSON Schema 기반 100% 결정론적 데이터 입출력, 도구 실행 컨텍스트 자동 압축 및 가설 상속",
                "cons": "프롬프트 작성보다 높은 시스템 아키텍처 이해도 요구"
            }
        },
        "domain_lineage_matrix": [
            {
                "domain": "LLM 페르소나 & 역할 제어",
                "gen1_prompting": "prompts.chat (2022 - 'Act as a Linux Terminal' 텍스트 주입)",
                "gen2_structured": "OpenAI System Message & Pydantic Instructor (2023 - 시스템 역할과 스키마 분리)",
                "gen3_programmatic": "DSPy (2024 - 프롬프트 수동 작성 폐기, 옵티마이저 기반 자동 컴파일)",
                "gen4_harness_sota": "Model Context Protocol (MCP) & Typed Harness (2026 SOTA - 도구 가상화 및 상태 전이 제어)"
            }
        ],
        "performance_bottlenecks": {
            "why_120k_stars": [
                "1. 퍼스트 무버 타이밍(First-Mover Dominance): ChatGPT 출시 직후(2022.12) 전 세계 최초의 프롬프트 저장소 선점",
                "2. 크라우드소싱 오픈소스 바이럴: 코딩 없이 prompts.csv에 텍스트 1줄만 추가해도 깃허브 기여자가 되는 극저진입장벽",
                "3. 웹 & 익스텐션 배포: prompts.chat 웹 앱 및 크롬 확장 프로그램을 통한 원클릭 복사 생태계 구축"
            ],
            "technical_obsolescence_in_2026": "2026년 최신 모델(Claude 3.5 Sonnet, GPT-4o, DeepSeek-R1)은 Instruction Following 능력이 내재화되어, 구시대의 장황한 'Act as a...' 문구는 어텐션 희석(Context Dilution)을 유발하고 토큰 비용만 낭비하는 레거시 안티패턴으로 전락함."
        },
        "engineering_tradeoffs": {
            "when_simple_prompts_work": "초기 아이디어 브레인스토밍, 단순 카피라이팅 등 비결정론적 창의 작업",
            "when_to_use_modern_harness": "엔터프라이즈 AI 에이전트, DB/API 연동 자동화, 코드 자율 수정 등 0% 오류율이 요구되는 프로덕션 환경"
        }
    }

    # Save local json
    local_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "prompts_chat_analysis.json")
    with open(local_path, "w", encoding="utf-8") as f:
        json.dump(prompts_analysis, f, indent=2, ensure_ascii=False)
    print(f"[+] Saved local knowledge file at: {local_path}")

    db_url = load_env_db_url()
    if not db_url: return

    conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO ecosystem_technical_analyses 
        (analysis_key, title, base_standard, third_party_ecosystem, core_philosophy_comparison, domain_lineage_matrix, performance_bottlenecks, engineering_tradeoffs)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (analysis_key) 
        DO UPDATE SET 
            title = EXCLUDED.title,
            core_philosophy_comparison = EXCLUDED.core_philosophy_comparison,
            domain_lineage_matrix = EXCLUDED.domain_lineage_matrix,
            performance_bottlenecks = EXCLUDED.performance_bottlenecks,
            engineering_tradeoffs = EXCLUDED.engineering_tradeoffs;
    """, (
        prompts_analysis["analysis_key"],
        prompts_analysis["title"],
        prompts_analysis["base_standard"],
        prompts_analysis["third_party_ecosystem"],
        json.dumps(prompts_analysis["core_philosophy_comparison"], ensure_ascii=False),
        json.dumps(prompts_analysis["domain_lineage_matrix"], ensure_ascii=False),
        json.dumps(prompts_analysis["performance_bottlenecks"], ensure_ascii=False),
        json.dumps(prompts_analysis["engineering_tradeoffs"], ensure_ascii=False)
    ))
    conn.commit()
    cur.close()
    conn.close()
    print("[+] Successfully persisted 'prompts.chat Evolution Analysis' to Neon Postgres DB!")

if __name__ == "__main__":
    store_python_vs_awesome_analysis()
    store_prompts_chat_analysis()

