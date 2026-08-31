#!/usr/bin/env python3
"""
Fact-Check & Engineering Portfolio Dashboard Builder (2026 SOTA Framework - v4.1)
investigations/ 폴더와 logs/ 수집 헬스 상태를 취합하여 포트폴리오 웹 대시보드를 자동 생성합니다.
"""

import json
import os
import sys

# Ensure UTF-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def scan_investigations():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    inv_dir = os.path.join(base_dir, "investigations")
    
    cases = []
    if not os.path.exists(inv_dir):
        return cases

    for item in sorted(os.listdir(inv_dir)):
        item_path = os.path.join(inv_dir, item)
        if os.path.isdir(item_path):
            meta_path = os.path.join(item_path, "metadata.json")
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                        if "title" in meta and meta.get("title") != "[이슈명]" and meta.get("title") != "[저장소명]":
                            cases.append(meta)
                except Exception as e:
                    print(f"[!] Warning: Failed to read {meta_path}: {e}")
    return cases

def get_harvest_health():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    hist_path = os.path.join(base_dir, "logs", "harvest_history.json")
    if os.path.exists(hist_path):
        try:
            with open(hist_path, "r", encoding="utf-8") as f:
                history = json.load(f)
                if history:
                    return history[0]
        except Exception:
            pass
    return None

def build_dashboard():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dash_dir = os.path.join(base_dir, "dashboard")
    docs_dir = os.path.join(base_dir, "docs")
    os.makedirs(dash_dir, exist_ok=True)
    os.makedirs(docs_dir, exist_ok=True)

    cases = scan_investigations()
    harvest_health = get_harvest_health()
    
    # Statistics
    total_cases = len(cases)
    active_dev_count = sum(1 for c in cases if c.get("portfolio_story", {}).get("hands_on_log", {}).get("status") == "ACTIVE_DEVELOPED")
    halted_count = sum(1 for c in cases if c.get("portfolio_story", {}).get("hands_on_log", {}).get("status") == "EVALUATED_HALTED")
    pending_count = sum(1 for c in cases if c.get("portfolio_story", {}).get("hands_on_log", {}).get("status") == "PENDING_RESEARCH")
    
    verdict_counts = {}
    category_counts = {}
    for c in cases:
        v = c.get("verdict", "UNVERIFIED")
        verdict_counts[v] = verdict_counts.get(v, 0) + 1
        cat = c.get("category", "General Tech")
        category_counts[cat] = category_counts.get(cat, 0) + 1

    summary_data = {
        "generated_at": "2026-08-31",
        "harvest_health": harvest_health,
        "total_cases": total_cases,
        "active_dev_count": active_dev_count,
        "halted_count": halted_count,
        "pending_count": pending_count,
        "verdict_counts": verdict_counts,
        "category_counts": category_counts,
        "cases": cases
    }

    # Write data.json
    for target_dir in [dash_dir, docs_dir]:
        json_path = os.path.join(target_dir, "data.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)

    # Generate HTML
    html_content = generate_html(summary_data)
    for target_dir in [dash_dir, docs_dir]:
        html_path = os.path.join(target_dir, "index.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

    print(f"[+] Successfully built dashboard at:")
    print(f"    - dashboard/index.html (Local view)")
    print(f"    - docs/index.html (GitHub Pages hosting)")

def generate_html(data):
    cases_json = json.dumps(data["cases"], ensure_ascii=False)
    health_json = json.dumps(data.get("harvest_health", {}), ensure_ascii=False)
    
    return f"""<!DOCTYPE html>
<html lang="ko" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI & Tech Fact-Check Engineering Portfolio</title>
  <!-- Tailwind CSS & Lucide Icons -->
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/lucide@latest"></script>
  <script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          colors: {{
            brand: {{
              50: '#eef2ff',
              500: '#6366f1',
              600: '#4f46e5',
              900: '#312e81',
            }}
          }}
        }}
      }}
    }}
  </script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;500;600;700;800&display=swap');
    body {{ font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif; }}
    .glass {{ background: rgba(30, 41, 59, 0.75); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }}
    .glass-card {{ background: rgba(15, 23, 42, 0.65); backdrop-filter: blur(8px); border: 1px solid rgba(255, 255, 255, 0.06); transition: all 0.2s ease; }}
    .glass-card:hover {{ border-color: rgba(99, 102, 241, 0.45); transform: translateY(-2px); }}
    .badge-true {{ background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }}
    .badge-half {{ background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }}
    .badge-gamed {{ background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }}
    
    /* 3-Stage Hands-on Badges */
    .badge-dev {{ background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }}
    .badge-halted {{ background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }}
    .badge-pending {{ background: rgba(148, 163, 184, 0.15); color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.3); }}
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen">

  <!-- Navigation Bar -->
  <header class="sticky top-0 z-40 glass border-b border-slate-800">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
          <i data-lucide="shield-check" class="w-6 h-6 text-white"></i>
        </div>
        <div>
          <h1 class="text-lg font-bold tracking-tight text-white flex items-center gap-2">
            AI Fact-Check & Engineering Portfolio
            <span class="text-xs px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-medium border border-indigo-500/30">2026 SOTA</span>
          </h1>
          <p class="text-xs text-slate-400">SNS 최신 기술 비판적 검증 • 출처 감사 • 3단계 실무 실측 아카이브</p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <button onclick="openHealthModal()" class="flex items-center gap-2 text-xs px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-300 font-medium border border-emerald-500/30 hover:bg-emerald-500/20 transition">
          <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          수집 시스템 헬스 모니터 (Live)
        </button>
      </div>
    </div>
  </header>

  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
    
    <!-- Hero / Portfolio Intro Banner -->
    <div class="glass p-6 sm:p-8 rounded-2xl relative overflow-hidden">
      <div class="relative z-10 max-w-3xl space-y-3">
        <h2 class="text-2xl sm:text-3xl font-extrabold text-white">
          "소문난 AI 기술, 진짜 작동하고 경제성이 있을까?"
        </h2>
        <p class="text-sm sm:text-base text-slate-300 leading-relaxed">
          SNS(X, Reddit, 유튜브)에서 쏟아지는 수많은 최신 AI 트렌드를 무비판적으로 수용하지 않고, 
          <strong>명확한 출처(Tier 1~4)와 커뮤니티 반응을 교차 감사하고, 데이터 오염(Contamination)과 실질 API 원가를 역산하여 
          실제 개발 여부(3단계)를 투명하게 기록</strong>한 엔지니어링 포트폴리오입니다.
        </p>
      </div>
      <div class="absolute -right-10 -bottom-10 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none"></div>
    </div>

    <!-- KPI Metric Cards (3-Stage Hands-on Status) -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="glass p-5 rounded-xl space-y-2">
        <div class="flex items-center justify-between text-slate-400">
          <span class="text-xs font-medium uppercase tracking-wider">총 팩트체크 완료</span>
          <i data-lucide="layers" class="w-4 h-4 text-indigo-400"></i>
        </div>
        <div class="text-3xl font-black text-white">{data['total_cases']} <span class="text-sm font-normal text-slate-400">Projects</span></div>
        <p class="text-xs text-slate-400">출처 기반 심층 감사 완료</p>
      </div>

      <div class="glass p-5 rounded-xl space-y-2 border-emerald-500/20">
        <div class="flex items-center justify-between text-slate-400">
          <span class="text-xs font-medium uppercase tracking-wider text-emerald-400">1. 실제 개발/활용 완료</span>
          <i data-lucide="check-circle" class="w-4 h-4 text-emerald-400"></i>
        </div>
        <div class="text-3xl font-black text-emerald-400">{data['active_dev_count']} <span class="text-sm font-normal text-slate-400">건</span></div>
        <p class="text-xs text-slate-400">사내/프로젝트 실제 파이프라인 배포</p>
      </div>

      <div class="glass p-5 rounded-xl space-y-2 border-amber-500/20">
        <div class="flex items-center justify-between text-slate-400">
          <span class="text-xs font-medium uppercase tracking-wider text-amber-400">2. 성능/과금 개발 중단</span>
          <i data-lucide="x-circle" class="w-4 h-4 text-amber-400"></i>
        </div>
        <div class="text-3xl font-black text-amber-400">{data['halted_count']} <span class="text-sm font-normal text-slate-400">건</span></div>
        <p class="text-xs text-slate-400">원가/플랫폼 제재 리스크로 중단</p>
      </div>

      <div class="glass p-5 rounded-xl space-y-2 border-slate-700">
        <div class="flex items-center justify-between text-slate-400">
          <span class="text-xs font-medium uppercase tracking-wider text-slate-400">3. 아직 개발 전 (조사)</span>
          <i data-lucide="clock" class="w-4 h-4 text-slate-400"></i>
        </div>
        <div class="text-3xl font-black text-slate-300">{data['pending_count']} <span class="text-sm font-normal text-slate-400">건</span></div>
        <p class="text-xs text-slate-400">하네스 오류 확인 및 사전 조사 단계</p>
      </div>
    </div>

    <!-- Filters & Search Toolbar -->
    <div class="glass p-4 rounded-xl flex flex-col md:flex-row items-center justify-between gap-4">
      <!-- Search Input -->
      <div class="relative w-full md:w-80">
        <i data-lucide="search" class="w-4 h-4 absolute left-3.5 top-3 text-slate-400"></i>
        <input type="text" id="searchInput" placeholder="기술명, SNS 출처, 키워드 검색..." 
               class="w-full bg-slate-900/80 border border-slate-700/60 rounded-lg pl-10 pr-4 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition">
      </div>

      <!-- Filter Buttons (Hands-on 3-Stage Filter) -->
      <div class="flex flex-wrap items-center gap-2 w-full md:w-auto">
        <button onclick="setStageFilter('ALL')" class="stage-btn active px-3 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 text-white border border-indigo-500 transition" data-stage="ALL">전체 보기</button>
        <button onclick="setStageFilter('ACTIVE_DEVELOPED')" class="stage-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-900 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/10 transition" data-stage="ACTIVE_DEVELOPED">🟢 실제 개발 완료</button>
        <button onclick="setStageFilter('EVALUATED_HALTED')" class="stage-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-900 text-amber-400 border border-amber-500/30 hover:bg-amber-500/10 transition" data-stage="EVALUATED_HALTED">🟡 성능/과금 중단</button>
        <button onclick="setStageFilter('PENDING_RESEARCH')" class="stage-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-900 text-slate-300 border border-slate-700 hover:bg-slate-800 transition" data-stage="PENDING_RESEARCH">⚪ 개발 전 (사전 조사)</button>
      </div>
    </div>

    <!-- Case Cards Grid -->
    <div id="cardsGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <!-- Dynamically Rendered via JS -->
    </div>

  </main>

  <!-- Health & Harvester Monitoring Modal -->
  <div id="healthModal" class="fixed inset-0 z-50 bg-black/85 backdrop-blur-sm hidden flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
    <div class="glass max-w-2xl w-full rounded-2xl overflow-hidden shadow-2xl border border-slate-700 my-8">
      <div class="p-6 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
        <div class="flex items-center gap-2.5">
          <i data-lucide="activity" class="w-5 h-5 text-emerald-400"></i>
          <h3 class="text-base font-bold text-white">자동 수집 시스템 실시간 헬스 모니터</h3>
        </div>
        <button onclick="closeHealthModal()" class="text-slate-400 hover:text-white p-1 rounded-lg bg-slate-800/60 hover:bg-slate-700">
          <i data-lucide="x" class="w-5 h-5"></i>
        </button>
      </div>
      <div class="p-6 space-y-4 text-xs text-slate-300">
        <div class="grid grid-cols-3 gap-3">
          <div class="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
            <span class="text-slate-400">최근 수집 일자</span>
            <div id="healthDate" class="text-sm font-bold text-white mt-1"></div>
          </div>
          <div class="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
            <span class="text-slate-400">신규 발굴 후보</span>
            <div id="healthNewSaved" class="text-sm font-bold text-emerald-400 mt-1"></div>
          </div>
          <div class="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
            <span class="text-slate-400">중복 차단 건수</span>
            <div id="healthDupSkipped" class="text-sm font-bold text-indigo-300 mt-1"></div>
          </div>
        </div>
        <div>
          <h4 class="font-bold text-slate-200 mb-2">소스별 수집 헬스 & 레이턴시</h4>
          <div id="healthSourcesList" class="space-y-2"></div>
        </div>
      </div>
      <div class="p-4 border-t border-slate-800 bg-slate-900/60 flex justify-end">
        <button onclick="closeHealthModal()" class="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold">닫기</button>
      </div>
    </div>
  </div>

  <!-- Detailed Portfolio Modal -->
  <div id="detailModal" class="fixed inset-0 z-50 bg-black/85 backdrop-blur-sm hidden flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
    <div class="glass max-w-3xl w-full rounded-2xl overflow-hidden shadow-2xl border border-slate-700/80 my-8 max-h-[92vh] flex flex-col">
      <!-- Modal Header -->
      <div class="p-6 border-b border-slate-800 flex items-start justify-between bg-slate-900/60">
        <div class="space-y-1 pr-4">
          <div class="flex items-center gap-2 flex-wrap">
            <span id="modalCategory" class="text-xs px-2.5 py-0.5 rounded-md bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 font-medium"></span>
            <span id="modalVerdictBadge" class="text-xs px-2.5 py-0.5 rounded-md font-semibold"></span>
            <span id="modalStageBadge" class="text-xs px-2.5 py-0.5 rounded-md font-medium"></span>
          </div>
          <h3 id="modalTitle" class="text-xl font-bold text-white pt-1"></h3>
        </div>
        <button onclick="closeModal()" class="text-slate-400 hover:text-white p-1 rounded-lg bg-slate-800/60 hover:bg-slate-700 transition">
          <i data-lucide="x" class="w-5 h-5"></i>
        </button>
      </div>

      <!-- Modal Body -->
      <div class="p-6 overflow-y-auto space-y-6 text-sm text-slate-200">
        <!-- 0. Verified Sources List -->
        <div class="space-y-2">
          <h4 class="text-xs font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-1.5">
            <i data-lucide="link-2" class="w-4 h-4"></i> 명확한 팩트체크 검증 출처 (Verified Sources)
          </h4>
          <div id="modalSourcesList" class="bg-slate-900/80 p-3.5 rounded-xl border border-slate-800 space-y-2"></div>
        </div>

        <!-- Community Reactions -->
        <div class="space-y-2">
          <h4 class="text-xs font-bold uppercase tracking-wider text-sky-400 flex items-center gap-1.5">
            <i data-lucide="message-square" class="w-4 h-4"></i> 개발자 커뮤니티 반응 (Community Reactions)
          </h4>
          <div id="modalCommunityList" class="space-y-2"></div>
        </div>

        <!-- 1. The Hook -->
        <div class="space-y-1.5">
          <h4 class="text-xs font-bold uppercase tracking-wider text-indigo-300 flex items-center gap-1.5">
            <i data-lucide="sparkles" class="w-4 h-4"></i> 1. The Hook (왜 찾아보게 되었는가? / 매력 포인트)
          </h4>
          <p id="modalHook" class="bg-slate-900/70 p-3.5 rounded-xl border border-slate-800 text-slate-300 leading-relaxed"></p>
        </div>

        <!-- 2. Hype Anatomy -->
        <div class="space-y-1.5">
          <h4 class="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1.5">
            <i data-lucide="megaphone" class="w-4 h-4"></i> 2. Marketing Hype Anatomy (어떤 식으로 홍보/과장했는가?)
          </h4>
          <p id="modalHype" class="bg-slate-900/70 p-3.5 rounded-xl border border-slate-800 text-slate-300 leading-relaxed"></p>
        </div>

        <!-- 3. Engineering Takeaways -->
        <div class="space-y-1.5">
          <h4 class="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
            <i data-lucide="book-open" class="w-4 h-4"></i> 3. Engineering Takeaways (엔지니어로서 배운 점 & 기술적 실체)
          </h4>
          <p id="modalTakeaways" class="bg-slate-900/70 p-3.5 rounded-xl border border-slate-800 text-slate-300 leading-relaxed whitespace-pre-line"></p>
        </div>

        <!-- 4. Future Applications -->
        <div class="space-y-1.5">
          <h4 class="text-xs font-bold uppercase tracking-wider text-sky-400 flex items-center gap-1.5">
            <i data-lucide="rocket" class="w-4 h-4"></i> 4. Future Applications (추후 어떤 곳에 활용 가능한가?)
          </h4>
          <p id="modalFuture" class="bg-slate-900/70 p-3.5 rounded-xl border border-slate-800 text-slate-300 leading-relaxed whitespace-pre-line"></p>
        </div>

        <!-- 5. Hands-on Empirical Proof -->
        <div class="space-y-2">
          <h4 class="text-xs font-bold uppercase tracking-wider text-purple-400 flex items-center gap-1.5">
            <i data-lucide="flask-conical" class="w-4 h-4"></i> 5. Hands-on 실무 실측 및 활용 상태 (No-Hallucination Proof)
          </h4>
          <div id="modalHandsOnBox" class="bg-slate-900/90 p-4 rounded-xl border space-y-2.5">
            <div class="flex items-center justify-between pb-2 border-b border-slate-800">
              <span class="text-xs text-slate-400 font-medium">실측 진행 상태:</span>
              <span id="modalHandsOnStatusText" class="text-xs font-bold px-2 py-0.5 rounded"></span>
            </div>
            <div class="space-y-1 text-xs">
              <div><span class="text-slate-400 font-medium">파이프라인 / URL:</span> <span id="modalHandsOnPipeline" class="text-purple-300 font-semibold break-all"></span></div>
              <div><span class="text-slate-400 font-medium">실측 환경:</span> <span id="modalTestEnv" class="text-slate-200"></span></div>
              <div><span class="text-slate-400 font-medium">실측 지표:</span> <span id="modalTestMetrics" class="text-slate-200 font-mono"></span></div>
            </div>
            <div class="text-xs pt-2 border-t border-slate-800 text-slate-300 leading-relaxed" id="modalHandsOnDetails"></div>
          </div>
        </div>

      </div>

      <!-- Modal Footer -->
      <div class="p-4 border-t border-slate-800 bg-slate-900/60 flex justify-end">
        <button onclick="closeModal()" class="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition">
          닫기 (Close)
        </button>
      </div>
    </div>
  </div>

  <script>
    const casesData = {cases_json};
    const healthData = {health_json};
    let currentStage = 'ALL';
    let searchQuery = '';

    function getVerdictBadgeClass(verdict) {{
      if (verdict === 'VERIFIED_TRUE') return 'badge-true';
      if (verdict === 'HALF_TRUE_CONTEXT_REQUIRED' || verdict === 'HALF_TRUE') return 'badge-half';
      if (verdict === 'MISLEADING_GAMED' || verdict === 'CONFIRMED_FALSE') return 'badge-gamed';
      return 'bg-slate-800 text-slate-300 border-slate-700';
    }}

    function getVerdictLabel(verdict) {{
      if (verdict === 'VERIFIED_TRUE') return 'VERIFIED TRUE';
      if (verdict === 'HALF_TRUE_CONTEXT_REQUIRED' || verdict === 'HALF_TRUE') return 'HALF TRUE (맥락 필요)';
      if (verdict === 'MISLEADING_GAMED') return 'MISLEADING (왜곡/과장)';
      if (verdict === 'CONFIRMED_FALSE') return 'CONFIRMED FALSE';
      return verdict;
    }}

    function getStageBadgeInfo(status) {{
      if (status === 'ACTIVE_DEVELOPED') {{
        return {{ class: 'badge-dev', label: '🟢 실제 개발 & 활용 완료', boxBorder: 'border-emerald-500/30' }};
      }}
      if (status === 'EVALUATED_HALTED') {{
        return {{ class: 'badge-halted', label: '🟡 성능/과금 문제로 개발 중단', boxBorder: 'border-amber-500/30' }};
      }}
      return {{ class: 'badge-pending', label: '⚪ 아직 개발 전 (기술 조사 완료)', boxBorder: 'border-slate-700' }};
    }}

    function openHealthModal() {{
      if (healthData && healthData.date) {{
        document.getElementById('healthDate').innerText = healthData.date;
        document.getElementById('healthNewSaved').innerText = (healthData.summary ? healthData.summary.new_saved : 0) + ' 건';
        document.getElementById('healthDupSkipped').innerText = (healthData.summary ? healthData.summary.duplicates_skipped : 0) + ' 건';
        
        const slist = document.getElementById('healthSourcesList');
        slist.innerHTML = '';
        if (healthData.sources) {{
          Object.entries(healthData.sources).forEach(([src, info]) => {{
            const div = document.createElement('div');
            const isSuccess = info.status === 'SUCCESS';
            div.className = 'flex items-center justify-between p-2 rounded-lg bg-slate-900 border ' + (isSuccess ? 'border-emerald-500/20' : 'border-amber-500/20');
            div.innerHTML = `
              <div class="flex items-center gap-2">
                <span class="w-2 h-2 rounded-full ${{isSuccess ? 'bg-emerald-400' : 'bg-amber-400'}}"></span>
                <span class="font-bold text-slate-200 uppercase">${{src}}</span>
              </div>
              <div class="text-slate-400">
                ${{isSuccess ? '<span class="text-emerald-400 font-semibold">' + (info.items_found || 0) + ' 건 수집</span>' : '<span class="text-amber-400">차단/에러 감지</span>'}} 
                (${{info.duration_sec || 0}}s)
              </div>
            `;
            slist.appendChild(div);
          }});
        }}
      }}
      document.getElementById('healthModal').classList.remove('hidden');
      lucide.createIcons();
    }}

    function closeHealthModal() {{
      document.getElementById('healthModal').classList.add('hidden');
    }}

    function renderCards() {{
      const grid = document.getElementById('cardsGrid');
      grid.innerHTML = '';

      const filtered = casesData.filter(c => {{
        const story = c.portfolio_story || {{}};
        const handsOn = story.hands_on_log || {{}};
        const stage = handsOn.status || 'PENDING_RESEARCH';
        
        const matchesStage = currentStage === 'ALL' || stage === currentStage;
        const text = (c.title + ' ' + (c.category || '') + ' ' + (story.the_hook || '')).toLowerCase();
        const matchesSearch = text.includes(searchQuery.toLowerCase());
        return matchesStage && matchesSearch;
      }});

      if (filtered.length === 0) {{
        grid.innerHTML = '<div class="col-span-full py-16 text-center text-slate-500">조건에 맞는 팩트체크 케이스가 없습니다.</div>';
        return;
      }}

      filtered.forEach((c) => {{
        const story = c.portfolio_story || {{}};
        const handsOn = story.hands_on_log || {{}};
        const badgeClass = getVerdictBadgeClass(c.verdict);
        const verdictLabel = getVerdictLabel(c.verdict);
        const stageInfo = getStageBadgeInfo(handsOn.status);

        const card = document.createElement('div');
        card.className = 'glass-card p-5 rounded-xl flex flex-col justify-between cursor-pointer space-y-4';
        card.onclick = () => openModal(c);

        card.innerHTML = `
          <div class="space-y-3">
            <div class="flex items-center justify-between text-xs">
              <span class="px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 font-medium border border-indigo-500/20">${{c.category || 'Tech'}}</span>
              <span class="px-2 py-0.5 rounded font-bold ${{badgeClass}}">${{verdictLabel}}</span>
            </div>
            
            <h3 class="font-bold text-base text-white hover:text-indigo-300 transition line-clamp-2">${{c.title}}</h3>
            
            <div class="flex items-center gap-1.5 text-xs">
              <span class="px-2 py-0.5 rounded font-medium ${{stageInfo.class}} flex items-center gap-1">
                ${{stageInfo.label}}
              </span>
            </div>

            <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800/80 space-y-1">
              <span class="text-[11px] font-semibold text-indigo-400 uppercase tracking-wider flex items-center gap-1">
                <i data-lucide="sparkles" class="w-3 h-3"></i> The Hook (매력 포인트)
              </span>
              <p class="text-xs text-slate-300 line-clamp-2">${{story.the_hook || '분석 진행 중'}}</p>
            </div>
          </div>

          <div class="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
            <span class="flex items-center gap-1">
              <i data-lucide="link" class="w-3 h-3"></i> 출처 ${{c.sources ? c.sources.length : 1}}개 감사 완료
            </span>
            <span class="text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1">
              상세 분석 보기 <i data-lucide="chevron-right" class="w-3.5 h-3.5"></i>
            </span>
          </div>
        `;

        grid.appendChild(card);
      }});

      lucide.createIcons();
    }}

    function openModal(c) {{
      const story = c.portfolio_story || {{}};
      const handsOn = story.hands_on_log || {{}};
      const stageInfo = getStageBadgeInfo(handsOn.status);
      
      document.getElementById('modalCategory').innerText = c.category || 'Tech';
      
      const vBadge = document.getElementById('modalVerdictBadge');
      vBadge.className = 'text-xs px-2.5 py-0.5 rounded-md font-semibold ' + getVerdictBadgeClass(c.verdict);
      vBadge.innerText = getVerdictLabel(c.verdict);

      const sBadge = document.getElementById('modalStageBadge');
      sBadge.className = 'text-xs px-2.5 py-0.5 rounded-md font-medium ' + stageInfo.class;
      sBadge.innerText = stageInfo.label;

      document.getElementById('modalTitle').innerText = c.title;

      // Render Sources List
      const sourcesList = document.getElementById('modalSourcesList');
      sourcesList.innerHTML = '';
      if (c.sources && c.sources.length > 0) {{
        c.sources.forEach(s => {{
          const item = document.createElement('div');
          item.className = 'flex items-center justify-between text-xs py-1 border-b border-slate-800/60 last:border-0';
          item.innerHTML = `
            <div class="flex items-center gap-2 truncate pr-2">
              <span class="px-1.5 py-0.2 rounded text-[10px] font-bold bg-slate-800 text-indigo-300 border border-slate-700">${{s.tier || 'Ref'}}</span>
              <span class="text-slate-300 font-medium truncate">${{s.name}}</span>
            </div>
            <a href="${{s.url}}" target="_blank" class="text-indigo-400 hover:text-indigo-300 flex items-center gap-1 shrink-0 font-medium hover:underline">
              원문 보기 <i data-lucide="external-link" class="w-3 h-3"></i>
            </a>
          `;
          sourcesList.appendChild(item);
        }});
      }} else {{
        sourcesList.innerHTML = '<span class="text-xs text-slate-500">등록된 출처 없음</span>';
      }}

      // Render Community Reactions
      const commList = document.getElementById('modalCommunityList');
      commList.innerHTML = '';
      if (c.community_reactions && c.community_reactions.length > 0) {{
        c.community_reactions.forEach(cr => {{
          const card = document.createElement('div');
          card.className = 'bg-slate-900/70 p-3 rounded-xl border border-slate-800 text-xs space-y-1';
          card.innerHTML = `
            <div class="flex items-center justify-between text-slate-400">
              <span class="font-bold text-sky-400">${{cr.platform}} (${{cr.author_type}})</span>
              <a href="${{cr.url}}" target="_blank" class="text-slate-500 hover:text-sky-300 flex items-center gap-0.5">스레드 <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>
            </div>
            <p class="text-slate-300 italic">"${{cr.quote}}"</p>
          `;
          commList.appendChild(card);
        }});
      }} else {{
        commList.innerHTML = '<div class="text-xs text-slate-500 bg-slate-900/50 p-2.5 rounded-lg">수집된 커뮤니티 스레드 없음</div>';
      }}
      
      document.getElementById('modalHook').innerText = story.the_hook || '내용 없음';
      document.getElementById('modalHype').innerText = story.marketing_hype_anatomy || '내용 없음';
      document.getElementById('modalTakeaways').innerText = story.engineering_takeaways || '내용 없음';
      document.getElementById('modalFuture').innerText = story.future_applications || '내용 없음';

      // Hands-on Box
      const hBox = document.getElementById('modalHandsOnBox');
      hBox.className = 'bg-slate-900/90 p-4 rounded-xl border space-y-2.5 ' + stageInfo.boxBorder;
      
      const hStatus = document.getElementById('modalHandsOnStatusText');
      hStatus.className = 'text-xs font-bold px-2 py-0.5 rounded ' + stageInfo.class;
      hStatus.innerText = stageInfo.label;

      document.getElementById('modalHandsOnPipeline').innerText = handsOn.pipeline_or_url || 'N/A';
      document.getElementById('modalTestEnv').innerText = handsOn.test_environment || 'N/A';
      document.getElementById('modalTestMetrics').innerText = handsOn.measured_results || 'N/A';
      document.getElementById('modalHandsOnDetails').innerText = handsOn.details || '';

      document.getElementById('detailModal').classList.remove('hidden');
      lucide.createIcons();
    }}

    function closeModal() {{
      document.getElementById('detailModal').classList.add('hidden');
    }}

    function setStageFilter(stage) {{
      currentStage = stage;
      document.querySelectorAll('.stage-btn').forEach(btn => {{
        if (btn.dataset.stage === stage) {{
          btn.classList.add('bg-indigo-600', 'text-white', 'border-indigo-500');
          btn.classList.remove('bg-slate-900');
        }} else {{
          btn.classList.remove('bg-indigo-600', 'text-white', 'border-indigo-500');
          btn.classList.add('bg-slate-900');
        }}
      }});
      renderCards();
    }}

    document.getElementById('searchInput').addEventListener('input', (e) => {{
      searchQuery = e.target.value;
      renderCards();
    }});

    document.getElementById('detailModal').addEventListener('click', (e) => {{
      if (e.target.id === 'detailModal') closeModal();
    }});
    document.getElementById('healthModal').addEventListener('click', (e) => {{
      if (e.target.id === 'healthModal') closeHealthModal();
    }});

    document.addEventListener('DOMContentLoaded', () => {{
      lucide.createIcons();
      renderCards();
    }});
  </script>
</body>
</html>"""

if __name__ == "__main__":
    build_dashboard()
