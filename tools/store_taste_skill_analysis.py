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

def store_taste_skill_analysis():
    analysis_data = {
        "analysis_key": "taste_skill_ai_slop_prevention",
        "title": "Taste-Skill: AI 특유의 네온 다크모드/3-Cards 슬롭을 탈피하기 위한 3-Dial 디자인 취향 주입 프레임워크",
        "base_standard": "Generic AI Frontend Slop (3-Cards, Neon Dark Theme)",
        "third_party_ecosystem": "Taste-Skill Engine (3-Dial Calibration & Anti-Pattern Ban)",
        "core_philosophy_comparison": {
            "generic_ai_frontend": {
                "philosophy": "Statistical Average (통계적 평균 기반의 뻔한 그라데이션 및 3열 카드 복붙)",
                "color_palette": "어두운 사이버펑크 네온 보라/시안 일변도, 쨍한 형광색 보더",
                "layout": "항상 동일한 3-Equal Feature Cards 및 중앙 정렬 텍스트",
                "cons": "웹사이트를 보자마자 'AI가 만든 사이트'라는 기시감과 신뢰도 저하 발생"
            },
            "taste_skill_framework": {
                "philosophy": "Human-Crafted Modernist Editorial (인간 디자이너의 감각적인 웜 미니멀리즘과 스위스 타이포그래피)",
                "creator": "Leon Lin (Leonxlnx, GitHub 83k+ Stars)",
                "color_palette": "정갈한 웜 오프화이트(#FBFBFC) / 크림 샌드 + 차콜 잉크(#0F172A) + 절제된 악센트",
                "layout": "비대칭 히어로 쇼케이스 + 에디토리얼 데이터 그리드 + 넉넉한 네거티브 스페이스",
                "rules": "Pre-flight Anti-Pattern Ban 체크리스트, 하드웨어 가속 트랜지션, 반응형 모바일 폴백"
            }
        },
        "domain_lineage_matrix": [
            {
                "domain": "AI 생성 웹 프론트엔드 디자인 진화사",
                "gen1_boilerplate": "Bootstrap / 기본 HTML 템플릿 (2022~2023 - 무난한 텍스트 중심)",
                "gen2_ai_slop": "v0 / Generic Cursor Output (2023~2024 - 획일화된 네온 다크모드 & 3-Card 슬롭)",
                "gen3_taste_injection": "Taste-Skill / Linear-Stripe Aesthetic (2026 SOTA - 전문 디자이너 취향 사전 주입)"
            }
        ],
        "performance_bottlenecks": {
            "key_innovations": [
                "1. 3-Dial 정밀 조절: DESIGN_VARIANCE(8), MOTION_INTENSITY(6), VISUAL_DENSITY(4)로 프로젝트 성격별 캘리브레이션",
                "2. Anti-Pattern Ban: 네온 다크모드, 3-Card, 뻔한 폰트 등의 AI 텔(Tells)을 시스템적으로 원천 차단",
                "3. 프레임워크 무관 npx 지원: React, Svelte, Tailwind, Pure HTML 어디서든 0ms 주입"
            ],
            "critical_tradeoffs": [
                "1. 대시보드 밀도 튜닝 필요: 복잡한 데이터 테이블에서는 VISUAL_DENSITY를 7 이상으로 조정 필수",
                "2. 브랜딩 자유도: 지나치게 스위스 미니멀리즘으로 획일화되지 않도록 도메인별 컬러 토큰 커스텀 권장"
            ]
        },
        "engineering_tradeoffs": {
            "when_to_use": "브랜드 신뢰도가 중요한 SaaS 랜딩페이지, 테크 포트폴리오, 엔지니어링 지식 허브",
            "when_to_avoid": "단순 백오피스 데이터 CRUD 테이블 관리자 전용 툴"
        }
    }

    # Save to local docs
    local_path = os.path.join(base_dir, "docs", "taste_skill_design_analysis.json")
    with open(local_path, "w", encoding="utf-8") as f:
        json.dump(analysis_data, f, indent=2, ensure_ascii=False)
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
    print("[+] Successfully persisted 'Taste-Skill Design Analysis' to Neon Postgres DB!")

if __name__ == "__main__":
    store_taste_skill_analysis()
