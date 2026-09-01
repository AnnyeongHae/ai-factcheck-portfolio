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

def store_threeui_analysis():
    threeui_analysis = {
        "analysis_key": "threeui_threejs_components_factcheck",
        "title": "ThreeUI (DesignCode Meng To): 220개 Three.js 컴포넌트 무료 공개의 기술적 실체와 AI 에이전트 3D 디자인 시스템 팩트체크",
        "base_standard": "Raw Three.js WebGL Boilerplate (From-Scratch Generation)",
        "third_party_ecosystem": "ThreeUI Promptable Component Library (GPU Instancing + Shader Skills + Shadcn Workflow)",
        "core_philosophy_comparison": {
            "from_scratch_threejs": {
                "philosophy": "Raw WebGL/Three.js Code Synthesis (LLM이 맨땅에서 3D 씬 작성)",
                "cons": "버텍스 셰이더 GLSL 문법 에러, 렌더 루프 메모리 누수, 모바일 GPU 드로우콜 병목으로 인한 캔버스 크래시 빈발"
            },
            "threeui_ecosystem": {
                "philosophy": "Promptable Pre-validated 3D Components (검증된 3D 템플릿에 파라미터만 AI로 튜닝)",
                "creator": "Meng To (Design+Code Founder)",
                "tech_stack": "React + Three.js + WebGL Shaders + GPU InstancedMesh",
                "pros": "10만 개 잔디 버텍스 셰이더 1MB 미만 60fps 렌더링, Shadcn CLI 호환, 에이전트용 스킬 팩 제공",
                "cons": "Pro 핵심 셰이더 및 MCP 스킬은 유료(Freemium), 모바일 배터리 소모 및 발열 이슈"
            }
        },
        "domain_lineage_matrix": [
            {
                "domain": "웹 3D & UI 컴포넌트 진화",
                "gen1_webgl": "Raw WebGL / Canvas2D (2011~2015 - 저수준 C 스타일 그래픽 API)",
                "gen2_threejs": "Three.js / React Three Fiber (2016~2022 - 선언적 3D 씬 그래프 표준화)",
                "gen3_shadcn_ui": "Shadcn UI (2023~2024 - 2D 복사-붙여넣기 컴포넌트 패러다임)",
                "gen4_threeui_agent": "ThreeUI (2026 SOTA - 3D 셰이더 및 AI 에이전트 프롬프트 튜닝 컴포넌트)"
            }
        ],
        "performance_bottlenecks": {
            "verified_facts": [
                "1. Meng To의 ThreeUI 커뮤니티 에디션(MIT)이 npm(@designcodeio/threeui) 및 깃허브에 무료 공개된 것은 사실임.",
                "2. Sylva 프로젝트의 10만+ 잔디 블레이드는 GPU Instancing(InstancedMesh) 단일 드로우콜로 1MB 미만 60fps 구동 검증됨.",
                "3. AI 에이전트에게 3D를 처음부터 짜게 하지 않고 검증된 템플릿의 파라미터(조명, 테마, 모션)만 고치게 하는 전략은 WebGL 안정성에 매우 효과적임."
            ],
            "marketing_hype_and_traps": [
                "1. '220개가 통째로 무료'는 과장: 기본 컴포넌트만 무료이며 고급 셰이더/스킬은 유료 Pro 티어로 분리된 Freemium 모델임.",
                "2. 인플루언서 강의 판매 깔때기: 본문 말미에 유료 콘텐츠(latpeed.com) 구매를 유도하는 전형적인 바이럴 마케팅.",
                "3. 모바일 환경 배터리 쓰로틀링: 저사양 모바일 기기 접속 시 WebGL GPU 연산으로 인한 발열/배터리 소모가 심하므로 2D CSS 폴백 설계 필수."
            ]
        },
        "engineering_tradeoffs": {
            "when_to_use": "SaaS 랜딩페이지 히어로 3D 인터랙션, 인터랙티브 3D 데이터 시각화, AI 에이전트 웹 디자인 자동화",
            "when_to_avoid": "초저전력/저사양 모바일 중심 B2B 관리자 대시보드"
        }
    }

    # Save to local docs
    local_path = os.path.join(base_dir, "docs", "threeui_threejs_components_analysis.json")
    with open(local_path, "w", encoding="utf-8") as f:
        json.dump(threeui_analysis, f, indent=2, ensure_ascii=False)
    print(f"[+] Saved local knowledge file at: {local_path}")

    # Store in Neon DB
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
        threeui_analysis["analysis_key"],
        threeui_analysis["title"],
        threeui_analysis["base_standard"],
        threeui_analysis["third_party_ecosystem"],
        json.dumps(threeui_analysis["core_philosophy_comparison"], ensure_ascii=False),
        json.dumps(threeui_analysis["domain_lineage_matrix"], ensure_ascii=False),
        json.dumps(threeui_analysis["performance_bottlenecks"], ensure_ascii=False),
        json.dumps(threeui_analysis["engineering_tradeoffs"], ensure_ascii=False)
    ))

    conn.commit()
    cur.close()
    conn.close()
    print("[+] Successfully persisted 'ThreeUI Analysis' to Neon Postgres DB!")

if __name__ == "__main__":
    store_threeui_analysis()
