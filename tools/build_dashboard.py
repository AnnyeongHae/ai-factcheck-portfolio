#!/usr/bin/env python3
"""
Fact-Check & Universal Tech Lineage Knowledge Graph Hub (2026 SOTA Framework - v11.0)
- 📊 Interactive Unit Economics & ROI Calculator (Web Ingestion & LLM Inference Sliders)
- 🕸️ Multi-Entity Citation Graph with Focus Subgraph (Ego-Network Search Mode)
- 🛡️ Anti-Gaming & Hype Risk Score Indicators
- 🌲 4-Generation Root Ancestry & Legacy Trade-off Visualizer
- 🔗 Obsidian Vault Integration
- 🇰🇷 / 🇺🇸 i18n Language Switcher
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
    if not os.path.exists(inv_dir): return cases

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

def scan_inbox():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    inbox_dir = os.path.join(base_dir, "inbox")
    inbox_items = []
    if not os.path.exists(inbox_dir): return inbox_items

    for f in sorted(os.listdir(inbox_dir), reverse=True):
        if f.endswith(".json"):
            path = os.path.join(inbox_dir, f)
            try:
                with open(path, "r", encoding="utf-8") as fp:
                    item = json.load(fp)
                    if "inbox_id" in item:
                        inbox_items.append(item)
            except Exception:
                pass
    return inbox_items

def load_graph_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    graph_path = os.path.join(base_dir, "configs", "tech_graph_schema.json")
    if os.path.exists(graph_path):
        try:
            with open(graph_path, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                graph = data.get("graph", {"nodes": [], "links": []})
                domains = data.get("domains", [])
                
                # Recalculate dynamic Degree Centrality
                degree_map = {}
                for l in graph.get("links", []):
                    s = l.get("source")
                    t = l.get("target")
                    degree_map[s] = degree_map.get(s, 0) + 1
                    degree_map[t] = degree_map.get(t, 0) + 1

                for n in graph.get("nodes", []):
                    deg = degree_map.get(n["id"], 1)
                    mentions = n.get("mentions", 20)
                    base_r = 13 if n.get("type") in ["person", "org"] else 11
                    n["val"] = int(base_r + (deg * 3.2) + (mentions * 0.22))

                return { "domains": domains, "nodes": graph["nodes"], "links": graph["links"] }
        except Exception as e:
            print(f"[!] Error loading graph schema: {e}")
    return {"domains": [], "nodes": [], "links": []}

def get_harvest_admin_stats():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    hist_path = os.path.join(base_dir, "logs", "harvest_history.json")
    
    registered_endpoints = [
        {"name": "Hugging Face Spaces", "url": "https://huggingface.co/api/spaces?sort=trendingScore", "type": "Interactive AI Demos", "auth": "Unauthenticated (Free)"},
        {"name": "Hugging Face Models", "url": "https://huggingface.co/api/models?sort=trendingScore", "type": "Trending Safetensors", "auth": "Unauthenticated (Free)"},
        {"name": "GitHub Search API", "url": "https://api.github.com/search/repositories", "type": "High-Velocity Repos", "auth": "Unauthenticated (10 req/min)"},
        {"name": "ArXiv Preprint API", "url": "http://export.arxiv.org/api/query?search_query=cat:cs.AI", "type": "1차 연구 논문", "auth": "Unauthenticated (Free)"},
        {"name": "Hacker News Firebase", "url": "https://hacker-news.firebaseio.com/v0/topstories.json", "type": "AI/엔지니어링 토론", "auth": "Unauthenticated (Free)"},
        {"name": "Reddit r/LocalLLaMA", "url": "https://www.reddit.com/r/LocalLLaMA/hot.json", "type": "커뮤니티 루머/피드백", "auth": "Custom User-Agent"}
    ]

    history = []
    if os.path.exists(hist_path):
        try:
            with open(hist_path, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []

    return {
        "endpoints": registered_endpoints,
        "history": history,
        "latest_run": history[0] if history else None
    }

def build_dashboard():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dash_dir = os.path.join(base_dir, "dashboard")
    docs_dir = os.path.join(base_dir, "docs")
    os.makedirs(dash_dir, exist_ok=True)
    os.makedirs(docs_dir, exist_ok=True)

    cases = scan_investigations()
    inbox_items = scan_inbox()
    admin_stats = get_harvest_admin_stats()
    graph_data = load_graph_data()
    
    total_cases = len(cases)
    user_curated_count = sum(1 for c in cases if c.get("curation", {}).get("discovery_mode") == "USER_CURATED")
    auto_harvested_count = sum(1 for c in cases if c.get("curation", {}).get("discovery_mode") == "AUTO_HARVESTED")
    
    active_dev_count = sum(1 for c in cases if c.get("portfolio_story", {}).get("hands_on_log", {}).get("status") == "ACTIVE_DEVELOPED")
    halted_count = sum(1 for c in cases if c.get("portfolio_story", {}).get("hands_on_log", {}).get("status") == "EVALUATED_HALTED")
    pending_count = sum(1 for c in cases if c.get("portfolio_story", {}).get("hands_on_log", {}).get("status") == "PENDING_RESEARCH")

    summary_data = {
        "generated_at": "2026-09-01",
        "total_cases": total_cases,
        "inbox_total_count": len(inbox_items),
        "user_curated_count": user_curated_count,
        "auto_harvested_count": auto_harvested_count,
        "active_dev_count": active_dev_count,
        "halted_count": halted_count,
        "pending_count": pending_count,
        "admin_stats": admin_stats,
        "inbox_items": inbox_items,
        "cases": cases,
        "graph": graph_data
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

    print(f"[+] Successfully built dashboard v11.0 (ROI Calculator & Focus Graph) at:")
    print(f"    - dashboard/index.html (Verified: {total_cases}, Inbox: {len(inbox_items)}, Nodes: {len(graph_data['nodes'])})")
    print(f"    - docs/index.html (GitHub Pages hosting)")

def generate_html(data):
    cases_json = json.dumps(data["cases"], ensure_ascii=False)
    inbox_json = json.dumps(data["inbox_items"], ensure_ascii=False)
    admin_json = json.dumps(data["admin_stats"], ensure_ascii=False)
    graph_json = json.dumps(data["graph"], ensure_ascii=False)
    
    return f"""<!DOCTYPE html>
<html lang="ko" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Universal AI Citation & Tech Lineage Knowledge Hub</title>
  <!-- Tailwind CSS & Lucide Icons & D3.js -->
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/lucide@latest"></script>
  <script src="https://d3js.org/d3.v7.min.js"></script>
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
    
    .badge-user {{ background: rgba(99, 102, 241, 0.18); color: #a5b4fc; border: 1px solid rgba(99, 102, 241, 0.4); }}
    .badge-auto {{ background: rgba(14, 165, 233, 0.15); color: #38bdf8; border: 1px solid rgba(14, 165, 233, 0.3); }}

    .badge-dev {{ background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }}
    .badge-halted {{ background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }}
    .badge-pending {{ background: rgba(148, 163, 184, 0.15); color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.3); }}
    
    /* Force Graph Highlighting */
    .node-dimmed {{ opacity: 0.10 !important; }}
    .link-dimmed {{ opacity: 0.03 !important; }}
    .node-highlighted {{ stroke: #ffffff !important; stroke-width: 3.5px !important; opacity: 1 !important; filter: drop-shadow(0 0 12px rgba(99,102,241,0.95)); }}
    .link-highlighted {{ stroke: #6366f1 !important; stroke-width: 3px !important; opacity: 1 !important; }}
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen">

  <!-- Navigation Bar -->
  <header class="sticky top-0 z-40 glass border-b border-slate-800">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
          <i data-lucide="shield-check" class="w-6 h-6 text-white"></i>
        </div>
        <div>
          <h1 class="text-lg font-bold tracking-tight text-white flex items-center gap-2">
            AI Citation & Lineage Graph
            <span class="text-xs px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-medium border border-indigo-500/30">v11.0</span>
          </h1>
          <p class="text-xs text-slate-400" id="i18nSubtitle">인물 • 연구소 • 논문 인용망 • 실시간 ROI 계산기</p>
        </div>
      </div>

      <!-- Main Controls -->
      <div class="flex items-center gap-2 sm:gap-3">
        
        <!-- Language Switcher (Default: KO) -->
        <div class="bg-slate-900 p-1 rounded-xl border border-slate-800 flex items-center text-xs font-semibold">
          <button onclick="setLanguage('KO')" id="langKoBtn" class="px-2.5 py-1 rounded-lg bg-indigo-600 text-white transition">🇰🇷 한국어</button>
          <button onclick="setLanguage('EN')" id="langEnBtn" class="px-2.5 py-1 rounded-lg text-slate-400 hover:text-white transition">🇺🇸 English</button>
        </div>

        <!-- 4-Tab Switcher (Portfolio / Graph / ROI / Inbox) -->
        <div class="bg-slate-900/90 p-1 rounded-xl border border-slate-800 flex items-center gap-1">
          <button onclick="switchView('portfolio')" id="tabPortfolioBtn" class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 text-white transition shadow-sm">
            <i data-lucide="award" class="w-4 h-4"></i>
            <span id="i18nTabPortfolio">🏆 공식 포트폴리오</span> ({data['total_cases']})
          </button>
          <button onclick="switchView('graph')" id="tabGraphBtn" class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-400 hover:text-white transition">
            <i data-lucide="network" class="w-4 h-4 text-emerald-400"></i>
            <span id="i18nTabGraph">🕸️ 인용 계보망</span>
          </button>
          <button onclick="switchView('roi')" id="tabRoiBtn" class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-400 hover:text-white transition">
            <i data-lucide="calculator" class="w-4 h-4 text-cyan-400"></i>
            <span id="i18nTabRoi">📊 단위 경제성 계산기</span>
          </button>
          <button onclick="switchView('inbox')" id="tabInboxBtn" class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-400 hover:text-white transition">
            <i data-lucide="inbox" class="w-4 h-4 text-amber-400"></i>
            <span id="i18nTabInbox">📥 수집 인박스 큐</span> ({data['inbox_total_count']})
          </button>
        </div>

        <button onclick="openAdminModal()" class="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-slate-900 text-emerald-400 font-medium border border-emerald-500/30 hover:bg-emerald-500/10 transition">
          <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span id="i18nBtnAdmin">⚙️ 관리자</span>
        </button>
      </div>
    </div>
  </header>

  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
    
    <!-- ==================== VIEW 1: PORTFOLIO VIEW ==================== -->
    <div id="portfolioView" class="space-y-8">
      
      <!-- Hero Banner -->
      <div class="glass p-6 sm:p-8 rounded-2xl relative overflow-hidden">
        <div class="relative z-10 max-w-3xl space-y-3">
          <h2 class="text-2xl sm:text-3xl font-extrabold text-white" id="i18nHeroTitle">
            "소문난 AI 기술, 진짜 작동하고 경제성이 있을까?"
          </h2>
          <p class="text-sm sm:text-base text-slate-300 leading-relaxed" id="i18nHeroDesc">
            내가 직접 문제의식을 갖고 발굴한 <strong>[👤 직접 큐레이션]</strong> 프로젝트와, 
            시스템이 24시간 실시간 트래킹한 <strong>[🤖 자동 트렌드 발굴]</strong> 프로젝트를 
            <strong>명확한 출처(Tier 1~4), 4세대 기술 계보도, 실질 단위 원가 역산</strong>을 통해 입증한 포트폴리오입니다.
          </p>
        </div>
        <div class="absolute -right-10 -bottom-10 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none"></div>
      </div>

      <!-- Metric Cards -->
      <div class="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <div class="glass p-4 rounded-xl space-y-1">
          <div class="text-xs font-medium text-slate-400" id="i18nMetricTotal">총 팩트체크 프로젝트</div>
          <div class="text-2xl font-black text-white">{data['total_cases']} <span class="text-xs text-slate-400">Projects</span></div>
        </div>
        <div class="glass p-4 rounded-xl space-y-1 border-indigo-500/30">
          <div class="text-xs font-medium text-indigo-300" id="i18nMetricUser">👤 직접 문제해결 큐레이션</div>
          <div class="text-2xl font-black text-indigo-400">{data['user_curated_count']} <span class="text-xs text-slate-400">건</span></div>
        </div>
        <div class="glass p-4 rounded-xl space-y-1 border-sky-500/30">
          <div class="text-xs font-medium text-sky-300" id="i18nMetricAuto">🤖 자율 트렌드 감사</div>
          <div class="text-2xl font-black text-sky-400">{data['auto_harvested_count']} <span class="text-xs text-slate-400">건</span></div>
        </div>
        <div class="glass p-4 rounded-xl space-y-1 border-emerald-500/30">
          <div class="text-xs font-medium text-emerald-300" id="i18nMetricDev">🟢 실제 개발 & 활용 완료</div>
          <div class="text-2xl font-black text-emerald-400">{data['active_dev_count']} <span class="text-xs text-slate-400">건</span></div>
        </div>
        <div class="glass p-4 rounded-xl space-y-1 border-amber-500/30">
          <div class="text-xs font-medium text-amber-300" id="i18nMetricHalted">🟡 성능/과금 개발 중단</div>
          <div class="text-2xl font-black text-amber-400">{data['halted_count']} <span class="text-xs text-slate-400">건</span></div>
        </div>
      </div>

      <!-- Filters Toolbar -->
      <div class="glass p-4 rounded-xl space-y-3">
        <div class="flex flex-col md:flex-row items-center justify-between gap-4">
          <div class="relative w-full md:w-80">
            <i data-lucide="search" class="w-4 h-4 absolute left-3.5 top-3 text-slate-400"></i>
            <input type="text" id="searchInput" placeholder="기술명, 대체재, 출처, 키워드 검색..." 
                   class="w-full bg-slate-900/80 border border-slate-700/60 rounded-lg pl-10 pr-4 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition">
          </div>

          <div class="flex flex-wrap items-center gap-2">
            <button onclick="setModeFilter('ALL')" class="mode-btn active px-3 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 text-white border border-indigo-500 transition" data-mode="ALL" id="i18nFilterAllMode">전체 발굴 경로</button>
            <button onclick="setModeFilter('USER_CURATED')" class="mode-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-900 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-500/10 transition" data-mode="USER_CURATED" id="i18nFilterUserMode">👤 내가 직접 큐레이션</button>
            <button onclick="setModeFilter('AUTO_HARVESTED')" class="mode-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-900 text-sky-300 border border-sky-500/30 hover:bg-sky-500/10 transition" data-mode="AUTO_HARVESTED" id="i18nFilterAutoMode">🤖 자동 트렌드 발굴</button>
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-800">
          <span class="text-xs text-slate-400 mr-2" id="i18nStageLabel">실측 상태:</span>
          <button onclick="setStageFilter('ALL')" class="stage-btn active px-2.5 py-1 rounded-md text-xs font-medium bg-slate-800 text-white transition" data-stage="ALL" id="i18nStageAll">전체</button>
          <button onclick="setStageFilter('ACTIVE_DEVELOPED')" class="stage-btn px-2.5 py-1 rounded-md text-xs font-medium bg-slate-900 text-emerald-400 border border-emerald-500/20 hover:bg-slate-800 transition" data-stage="ACTIVE_DEVELOPED" id="i18nStageDev">🟢 개발 완료</button>
          <button onclick="setStageFilter('EVALUATED_HALTED')" class="stage-btn px-2.5 py-1 rounded-md text-xs font-medium bg-slate-900 text-amber-400 border border-amber-500/20 hover:bg-slate-800 transition" data-stage="EVALUATED_HALTED" id="i18nStageHalted">🟡 개발 중단</button>
          <button onclick="setStageFilter('PENDING_RESEARCH')" class="stage-btn px-2.5 py-1 rounded-md text-xs font-medium bg-slate-900 text-slate-300 border border-slate-700 hover:bg-slate-800 transition" data-stage="PENDING_RESEARCH" id="i18nStagePending">⚪ 사전 조사</button>
        </div>
      </div>

      <!-- Case Cards Grid -->
      <div id="cardsGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"></div>
    </div>

    <!-- ==================== VIEW 2: MULTI-ENTITY CITATION & FOCUS GRAPH VIEW ==================== -->
    <div id="graphView" class="hidden space-y-6">
      <div class="glass p-6 rounded-2xl space-y-4">
        <div class="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
          <div>
            <div class="flex items-center gap-2 flex-wrap">
              <span class="px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 text-xs font-bold border border-indigo-500/30">
                🕸️ Multi-Entity Citation & Lineage Network
              </span>
              <span class="text-xs text-slate-400">기술 • 👤 연구자 • 🏛️ 연구소 • 📄 1차 논문 인용망</span>
            </div>
            <h2 class="text-xl font-bold text-white mt-1">인물과 논문 인용 계보를 통한 기술 탄생의 뿌리 지도</h2>
            <p class="text-xs text-slate-300">
              노드를 호버하면 <strong>[연구자 ➔ 소속 연구소 ➔ 발표 논문 ➔ 탄생한 SOTA 기술]</strong>이 광선으로 유기적으로 하이라이트됩니다.
            </p>
          </div>

          <!-- Entity Type Filter Buttons -->
          <div class="flex flex-wrap items-center gap-1.5 bg-slate-900/90 p-1.5 rounded-xl border border-slate-800 text-xs">
            <button onclick="filterGraphType('ALL')" class="graph-type-btn active px-2.5 py-1 rounded-lg bg-indigo-600 text-white font-medium transition" data-type="ALL">전체 엔티티</button>
            <button onclick="filterGraphType('person')" class="graph-type-btn px-2.5 py-1 rounded-lg text-amber-400 hover:bg-slate-800 transition" data-type="person">👤 핵심 연구자</button>
            <button onclick="filterGraphType('org')" class="graph-type-btn px-2.5 py-1 rounded-lg text-yellow-400 hover:bg-slate-800 transition" data-type="org">🏛️ 연구소/기업</button>
            <button onclick="filterGraphType('paper')" class="graph-type-btn px-2.5 py-1 rounded-lg text-emerald-400 hover:bg-slate-800 transition" data-type="paper">📄 1차 논문</button>
            <button onclick="filterGraphType('tech')" class="graph-type-btn px-2.5 py-1 rounded-lg text-cyan-400 hover:bg-slate-800 transition" data-type="tech">⚡ 소프트웨어/기술</button>
          </div>
        </div>

        <!-- Graph Canvas Container -->
        <div class="relative w-full h-[720px] bg-slate-950/95 rounded-xl border border-slate-800 overflow-hidden shadow-2xl flex items-center justify-center">
          <svg id="techGraphSvg" class="w-full h-full cursor-grab active:cursor-grabbing"></svg>
          
          <!-- Dynamic Floating Tooltip Card -->
          <div id="graphTooltip" class="absolute bottom-5 left-5 p-4 rounded-xl glass border border-slate-700 text-xs max-w-sm hidden shadow-2xl transition space-y-1.5 pointer-events-none z-20">
            <div class="flex items-center justify-between gap-2">
              <span id="tooltipLabel" class="font-bold text-sm text-white"></span>
              <span id="tooltipTypeBadge" class="px-2 py-0.5 rounded text-[10px] font-bold"></span>
            </div>
            <div class="text-[11px] text-slate-400">
              엔티티 분류: <span id="tooltipType" class="font-semibold text-indigo-300 uppercase"></span> | 인용 중심성: <span id="tooltipVal" class="font-mono text-emerald-400"></span>
            </div>
            <p id="tooltipDesc" class="text-slate-300 text-[11px] leading-relaxed pt-1 border-t border-slate-800"></p>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== VIEW 3: INTERACTIVE UNIT ECONOMICS CALCULATOR ==================== -->
    <div id="roiView" class="hidden space-y-8">
      <div class="glass p-6 sm:p-8 rounded-2xl space-y-3">
        <div class="flex items-center gap-2">
          <span class="px-2.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 text-xs font-bold border border-cyan-500/30">
            📊 Interactive Unit Economics & ROI Simulator
          </span>
          <span class="text-xs text-slate-400">상용 API vs 오픈소스 자가호스팅 실측 원가 비교</span>
        </div>
        <h2 class="text-2xl font-extrabold text-white">"실제 도입 시 인프라 비용이 얼마나 절감되는가?"</h2>
        <p class="text-sm text-slate-300 leading-relaxed max-w-3xl">
          슬라이더를 조절하여 귀사의 워크로드에 맞는 <strong>예상 월간 클라우드 비용, 서버 호스팅 비용, 토큰 절감액</strong>을 실시간으로 역산해보세요.
        </p>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        <!-- Calculator 1: Web Ingestion & Scrapers (Firecrawl vs WaterCrawl vs Scrapy) -->
        <div class="glass-card p-6 rounded-2xl space-y-6 border-emerald-500/30">
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-bold text-white flex items-center gap-2">
              <i data-lucide="globe" class="w-5 h-5 text-emerald-400"></i>
              1. 웹 데이터 수집 & LLM 마크다운 변환
            </h3>
            <span class="text-xs text-slate-400">단위 원가 시뮬레이션</span>
          </div>

          <div class="space-y-2">
            <div class="flex justify-between text-xs">
              <span class="text-slate-300 font-semibold">월간 크롤링 페이지 수:</span>
              <span id="scrapingPagesDisplay" class="font-mono font-bold text-emerald-400 text-sm">100,000 페이지/월</span>
            </div>
            <input type="range" id="scrapingPagesSlider" min="10000" max="2000000" step="10000" value="100000" 
                   class="w-full accent-emerald-500 cursor-pointer h-2 bg-slate-800 rounded-lg">
            <div class="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>1만 건</span>
              <span>50만 건</span>
              <span>100만 건</span>
              <span>200만 건</span>
            </div>
          </div>

          <!-- Comparison Results Table -->
          <div class="space-y-3 pt-2">
            <div class="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between">
              <div>
                <div class="text-xs font-bold text-slate-200">🔥 Firecrawl Cloud API (SaaS)</div>
                <div class="text-[11px] text-slate-400">$0.0025 / page (종량제 요금)</div>
              </div>
              <div id="costFirecrawl" class="text-base font-black text-rose-400 font-mono">$250 /월</div>
            </div>

            <div class="p-3.5 rounded-xl bg-slate-900/90 border border-emerald-500/40 flex items-center justify-between">
              <div>
                <div class="text-xs font-bold text-emerald-300 flex items-center gap-1.5">
                  <i data-lucide="check-circle" class="w-3.5 h-3.5"></i> 🛡️ WaterCrawl Docker (자가호스팅 SOTA)
                </div>
                <div class="text-[11px] text-slate-400">AWS t4g.xlarge ($38) + 고정 트래픽</div>
              </div>
              <div id="costWatercrawl" class="text-base font-black text-emerald-400 font-mono">$45 /월</div>
            </div>

            <div class="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between">
              <div>
                <div class="text-xs font-bold text-slate-400">📄 Scrapy Raw 0세대 (정적 크롤링)</div>
                <div class="text-[11px] text-slate-500">t4g.small ($10) / JS 렌더링 불가</div>
              </div>
              <div id="costScrapy" class="text-base font-bold text-slate-300 font-mono">$10 /월</div>
            </div>
          </div>

          <!-- Summary Badge -->
          <div class="p-4 rounded-xl bg-emerald-950/30 border border-emerald-500/30 text-xs flex items-center justify-between">
            <span class="text-emerald-300 font-bold">월간 예상 인프라 비용 절감액:</span>
            <span id="scrapingSavings" class="text-base font-black text-emerald-400 font-mono">+$205 /월 (82% 절감)</span>
          </div>
        </div>

        <!-- Calculator 2: LLM Agent & Long Research (Claude Code vs PRAXIST + SGLang) -->
        <div class="glass-card p-6 rounded-2xl space-y-6 border-indigo-500/30">
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-bold text-white flex items-center gap-2">
              <i data-lucide="cpu" class="w-5 h-5 text-indigo-400"></i>
              2. 장기 AI 에이전트 & LLM 추론 비용
            </h3>
            <span class="text-xs text-slate-400">토큰 원가 시뮬레이션</span>
          </div>

          <div class="space-y-2">
            <div class="flex justify-between text-xs">
              <span class="text-slate-300 font-semibold">월간 에이전트 토큰 소모량:</span>
              <span id="agentTokensDisplay" class="font-mono font-bold text-indigo-400 text-sm">5억 토큰 (500M Tokens)</span>
            </div>
            <input type="range" id="agentTokensSlider" min="50000000" max="2000000000" step="50000000" value="500000000" 
                   class="w-full accent-indigo-500 cursor-pointer h-2 bg-slate-800 rounded-lg">
            <div class="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>5천만</span>
              <span>5억</span>
              <span>10억</span>
              <span>20억 토큰</span>
            </div>
          </div>

          <!-- Comparison Results Table -->
          <div class="space-y-3 pt-2">
            <div class="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between">
              <div>
                <div class="text-xs font-bold text-slate-200">🤖 Claude 3.7 Sonnet / Claude Code</div>
                <div class="text-[11px] text-slate-400">입력 $3 / 출력 $15 per 1M tokens</div>
              </div>
              <div id="costClaude" class="text-base font-black text-rose-400 font-mono">$3,000 /월</div>
            </div>

            <div class="p-3.5 rounded-xl bg-slate-900/90 border border-indigo-500/40 flex items-center justify-between">
              <div>
                <div class="text-xs font-bold text-indigo-300 flex items-center gap-1.5">
                  <i data-lucide="zap" class="w-3.5 h-3.5"></i> 🧬 PRAXIST + SGLang (가설 상속 SOTA)
                </div>
                <div class="text-[11px] text-slate-400">1/12 토큰 절감 + Radix 캐시 가속</div>
              </div>
              <div id="costPraxist" class="text-base font-black text-indigo-400 font-mono">$250 /월</div>
            </div>

            <div class="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between">
              <div>
                <div class="text-xs font-bold text-slate-400">🧠 DeepSeek-R1 로컬 서빙 (Dual 4090)</div>
                <div class="text-[11px] text-slate-500">전기세 + 하드웨어 상각비 고정 ($120)</div>
              </div>
              <div id="costDeepseek" class="text-base font-bold text-slate-300 font-mono">$120 /월</div>
            </div>
          </div>

          <!-- Summary Badge -->
          <div class="p-4 rounded-xl bg-indigo-950/30 border border-indigo-500/30 text-xs flex items-center justify-between">
            <span class="text-indigo-300 font-bold">월간 모델 API 비용 절감액:</span>
            <span id="agentSavings" class="text-base font-black text-indigo-400 font-mono">+$2,750 /월 (91.6% 절감)</span>
          </div>
        </div>

      </div>
    </div>

    <!-- ==================== VIEW 4: INBOX & TRIAGE VIEW ==================== -->
    <div id="inboxView" class="hidden space-y-6">
      
      <!-- Inbox Header & Explanation -->
      <div class="glass p-6 rounded-2xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-amber-500/20">
        <div class="space-y-1">
          <div class="flex items-center gap-2">
            <span class="px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 text-xs font-bold border border-amber-500/30" id="i18nInboxBadge">
              📥 미승인 트렌드 대기 큐 (Inbox Queue)
            </span>
            <span class="text-xs text-slate-400">총 {data['inbox_total_count']}건 대기 중</span>
          </div>
          <h2 class="text-xl font-bold text-white" id="i18nInboxHeaderTitle">"수집된 최신 기술 중 마음에 드는 것만 골라 분석을 의뢰하세요"</h2>
          <p class="text-xs text-slate-300" id="i18nInboxHeaderDesc">
            원문을 확인하고 <strong>[⚡ 분석 큐에 담기]</strong>를 누르면 Neon DB의 대기열에 담겨 Antigravity AI가 심층 리서치에 착수합니다.
          </p>
        </div>

        <div class="bg-slate-900/90 p-3 rounded-xl border border-slate-800 text-xs space-y-1 shrink-0">
          <div class="text-slate-400 font-semibold" id="i18nBatchLabel">💡 일괄 승격 명령어:</div>
          <code class="text-amber-300 bg-black/50 px-2 py-0.5 rounded font-mono block">python tools/triage.py --promote-top 3</code>
        </div>
      </div>

      <!-- Inbox Filters & Search -->
      <div class="glass p-4 rounded-xl flex flex-col md:flex-row items-center justify-between gap-4">
        <div class="flex items-center gap-3 w-full md:w-auto">
          <div class="relative w-full md:w-72">
            <i data-lucide="search" class="w-4 h-4 absolute left-3.5 top-3 text-slate-400"></i>
            <input type="text" id="inboxSearchInput" placeholder="인박스 후보 또는 모델명 검색..." 
                   class="w-full bg-slate-900/80 border border-slate-700/60 rounded-lg pl-10 pr-4 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500 transition">
          </div>

          <!-- Group by Family Toggle Switch -->
          <button onclick="toggleFamilyGrouping()" id="groupByFamilyBtn" class="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold bg-slate-900 text-purple-300 border border-purple-500/30 hover:bg-purple-500/10 transition shrink-0">
            <i data-lucide="layers" class="w-4 h-4"></i>
            <span id="groupByFamilyText">🧬 기저 모델 패밀리별 그룹화 (OFF)</span>
          </button>
        </div>

        <!-- Platform Source Filters -->
        <div class="flex flex-wrap items-center gap-2">
          <button onclick="setInboxSourceFilter('ALL')" class="inbox-src-btn active px-3 py-1.5 rounded-lg text-xs font-medium bg-amber-600 text-white transition" data-src="ALL">전체 소스</button>
          <button onclick="setInboxSourceFilter('Hugging Face Spaces')" class="inbox-src-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-900 text-amber-300 border border-amber-500/30 hover:bg-slate-800 transition" data-src="Hugging Face Spaces">🤗 HF Spaces (데모)</button>
          <button onclick="setInboxSourceFilter('Hugging Face Models')" class="inbox-src-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-900 text-sky-300 border border-sky-500/30 hover:bg-slate-800 transition" data-src="Hugging Face Models">🤗 HF Models</button>
          <button onclick="setInboxSourceFilter('GitHub Official')" class="inbox-src-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-900 text-slate-300 border border-slate-700 hover:bg-slate-800 transition" data-src="GitHub Official">🐙 GitHub</button>
          <button onclick="setInboxSourceFilter('ArXiv Preprint')" class="inbox-src-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-900 text-purple-300 border border-purple-500/30 hover:bg-slate-800 transition" data-src="ArXiv Preprint">📄 ArXiv</button>
          <button onclick="setInboxSourceFilter('Hacker News')" class="inbox-src-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-900 text-orange-300 border border-orange-500/30 hover:bg-slate-800 transition" data-src="Hacker News">🔥 Hacker News</button>
        </div>
      </div>

      <!-- Inbox Grid -->
      <div id="inboxGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5"></div>
    </div>

  </main>

  <!-- Detailed Portfolio Modal -->
  <div id="detailModal" class="fixed inset-0 z-50 bg-black/85 backdrop-blur-sm hidden flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
    <div class="glass max-w-4xl w-full rounded-2xl overflow-hidden shadow-2xl border border-slate-700/80 my-8 max-h-[92vh] flex flex-col">
      <div class="p-6 border-b border-slate-800 flex items-start justify-between bg-slate-900/60">
        <div class="space-y-1 pr-4">
          <div class="flex items-center gap-2 flex-wrap">
            <span id="modalModeBadge" class="text-xs px-2.5 py-0.5 rounded-md font-semibold"></span>
            <span id="modalClusterBadge" class="text-xs px-2.5 py-0.5 rounded-md bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 font-medium"></span>
            <span id="modalVerdictBadge" class="text-xs px-2.5 py-0.5 rounded-md font-semibold"></span>
            <span id="modalStageBadge" class="text-xs px-2.5 py-0.5 rounded-md font-medium"></span>
          </div>
          <h3 id="modalTitle" class="text-xl font-bold text-white pt-1"></h3>
        </div>
        <button onclick="closeModal()" class="text-slate-400 hover:text-white p-1 rounded-lg bg-slate-800/60 hover:bg-slate-700 transition">
          <i data-lucide="x" class="w-5 h-5"></i>
        </button>
      </div>

      <div class="p-6 overflow-y-auto space-y-6 text-sm text-slate-200">
        
        <!-- Curation Motivation Box -->
        <div id="modalCurationBox" class="p-4 rounded-xl border space-y-1.5">
          <div class="flex items-center justify-between">
            <h4 class="text-xs font-bold uppercase tracking-wider flex items-center gap-1.5" id="modalCurationTitle">
              <i data-lucide="user-check" class="w-4 h-4"></i> 큐레이션 동기 및 문제의식 (Discovery Motivation)
            </h4>
            <span id="modalCuratorName" class="text-xs text-slate-400 font-mono"></span>
          </div>
          <p id="modalPersonalMotivation" class="text-xs leading-relaxed text-slate-300"></p>
          <div class="text-[11px] text-indigo-400 font-medium pt-1">
            🎯 연계 워크플로우: <span id="modalTargetWorkflow" class="text-slate-300 font-normal"></span>
          </div>
        </div>

        <!-- Root Ancestry & Why Legacy Persists Box -->
        <div id="modalRootAncestryBox" class="p-4 rounded-xl border border-purple-500/30 bg-purple-950/20 space-y-2">
          <h4 class="text-xs font-bold uppercase tracking-wider text-purple-300 flex items-center gap-1.5">
            <i data-lucide="git-fork" class="w-4 h-4"></i> 🌲 4세대 기술 계보 & 레거시 잔존 트레이드오프 (Root Ancestry & Legacy Trade-off)
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs pt-1">
            <div class="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800 space-y-1">
              <span class="text-slate-400 font-semibold">🏛️ 근본 뿌리 역사 (Roots):</span>
              <div id="modalRootsList" class="text-slate-300 text-[11px] space-y-0.5"></div>
            </div>
            <div class="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800 space-y-1">
              <span class="text-amber-400 font-semibold">💡 SOTA가 있어도 구기술을 쓰는 이유:</span>
              <p id="modalWhyLegacy" class="text-slate-300 text-[11px] leading-relaxed"></p>
            </div>
          </div>
        </div>

        <!-- Alternatives Comparison Matrix -->
        <div class="space-y-2">
          <h4 class="text-xs font-bold uppercase tracking-wider text-sky-400 flex items-center gap-1.5">
            <i data-lucide="git-compare" class="w-4 h-4"></i> 유사 기술 & 대체재 비교 매트릭스 (Alternatives Benchmark)
          </h4>
          <div class="overflow-x-auto rounded-xl border border-slate-800">
            <table class="w-full text-left text-xs border-collapse bg-slate-900/60">
              <thead class="bg-slate-950/80 text-slate-400 border-b border-slate-800">
                <tr>
                  <th class="p-2.5 font-semibold">도구명</th>
                  <th class="p-2.5 font-semibold">핵심 스택</th>
                  <th class="p-2.5 font-semibold text-emerald-400">주요 강점 (Pros)</th>
                  <th class="p-2.5 font-semibold text-amber-400">한계점 (Cons)</th>
                </tr>
              </thead>
              <tbody id="modalAlternativesBody" class="divide-y divide-slate-800/60"></tbody>
            </table>
          </div>
        </div>

        <!-- Verified Sources List -->
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

        <!-- The Hook -->
        <div class="space-y-1.5">
          <h4 class="text-xs font-bold uppercase tracking-wider text-indigo-300 flex items-center gap-1.5">
            <i data-lucide="sparkles" class="w-4 h-4"></i> 1. The Hook (왜 찾아보게 되었는가? / 매력 포인트)
          </h4>
          <p id="modalHook" class="bg-slate-900/70 p-3.5 rounded-xl border border-slate-800 text-slate-300 leading-relaxed"></p>
        </div>

        <!-- Hype Anatomy -->
        <div class="space-y-1.5">
          <h4 class="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1.5">
            <i data-lucide="megaphone" class="w-4 h-4"></i> 2. Marketing Hype Anatomy (어떤 식으로 홍보/과장했는가?)
          </h4>
          <p id="modalHype" class="bg-slate-900/70 p-3.5 rounded-xl border border-slate-800 text-slate-300 leading-relaxed"></p>
        </div>

        <!-- Engineering Takeaways -->
        <div class="space-y-1.5">
          <h4 class="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
            <i data-lucide="book-open" class="w-4 h-4"></i> 3. Engineering Takeaways (엔지니어로서 배운 점 & 기술적 실체)
          </h4>
          <p id="modalTakeaways" class="bg-slate-900/70 p-3.5 rounded-xl border border-slate-800 text-slate-300 leading-relaxed whitespace-pre-line"></p>
        </div>

        <!-- Future Applications -->
        <div class="space-y-1.5">
          <h4 class="text-xs font-bold uppercase tracking-wider text-sky-400 flex items-center gap-1.5">
            <i data-lucide="rocket" class="w-4 h-4"></i> 4. Future Applications (추후 어떤 곳에 활용 가능한가?)
          </h4>
          <p id="modalFuture" class="bg-slate-900/70 p-3.5 rounded-xl border border-slate-800 text-slate-300 leading-relaxed whitespace-pre-line"></p>
        </div>

        <!-- Hands-on Box -->
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

      <div class="p-4 border-t border-slate-800 bg-slate-900/60 flex justify-end">
        <button onclick="closeModal()" class="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition">
          닫기 (Close)
        </button>
      </div>
    </div>
  </div>

  <!-- Toast Notification -->
  <div id="toast" class="fixed bottom-6 right-6 z-50 bg-indigo-600 text-white px-4 py-2.5 rounded-xl shadow-2xl text-xs font-semibold hidden transition-all duration-300 flex items-center gap-2">
    <i data-lucide="check" class="w-4 h-4"></i>
    <span id="toastMsg">클립보드에 복사되었습니다!</span>
  </div>

  <script>
    const casesData = {cases_json};
    const inboxData = {inbox_json};
    const adminData = {admin_json};
    const graphData = {graph_json};

    let currentLang = 'KO';
    let currentView = 'portfolio';
    let currentMode = 'ALL';
    let currentStage = 'ALL';
    let searchQuery = '';

    let currentInboxSource = 'ALL';
    let inboxSearchQuery = '';
    let currentGraphType = 'ALL';
    let graphInitialized = false;

    let svgSelection, nodeSelection, linkSelection, textSelection, simulationRef;

    const entityColorMap = {{
      'person': '#f59e0b',
      'org': '#eab308',
      'paper': '#10b981',
      'root': '#a855f7',
      'ancestor': '#3b82f6',
      'pioneer': '#f97316',
      'sota': '#06b6d4'
    }};

    const domainColorMap = {{
      'inference_serving': '#06b6d4',
      'vision_diffusion': '#ec4899',
      'agent_lineage': '#8b5cf6',
      'web_scraping': '#10b981',
      'voice_tts': '#f59e0b',
      'reasoning_moe': '#6366f1',
      'person': '#f59e0b',
      'org': '#eab308',
      'paper': '#10b981'
    }};

    const i18nDict = {{
      KO: {{
        subtitle: '인물 • 연구소 • 논문 인용망 • 실시간 ROI 계산기',
        tabPortfolio: '🏆 공식 포트폴리오',
        tabGraph: '🕸️ 인용 계보망',
        tabRoi: '📊 단위 경제성 계산기',
        tabInbox: '📥 수집 인박스 큐',
        btnAdmin: '⚙️ 관리자',
        heroTitle: '"소문난 AI 기술, 진짜 작동하고 경제성이 있을까?"',
        heroDesc: '내가 직접 문제의식을 갖고 발굴한 [👤 직접 큐레이션] 프로젝트와, 시스템이 24시간 실시간 트래킹한 [🤖 자동 트렌드 발굴] 프로젝트를 명확한 출처(Tier 1~4), 4세대 기술 계보도, 실질 단위 원가 역산을 통해 입증한 포트폴리오입니다.',
        metricTotal: '총 팩트체크 프로젝트',
        metricUser: '👤 직접 문제해결 큐레이션',
        metricAuto: '🤖 자율 트렌드 감사',
        metricDev: '🟢 실제 개발 & 활용 완료',
        metricHalted: '🟡 성능/과금 개발 중단',
        filterAllMode: '전체 발굴 경로',
        filterUserMode: '👤 내가 직접 큐레이션',
        filterAutoMode: '🤖 자동 트렌드 발굴',
        stageLabel: '실측 상태:',
        stageAll: '전체',
        stageDev: '🟢 개발 완료',
        stageHalted: '🟡 개발 중단',
        stagePending: '⚪ 사전 조사',
        inboxBadge: '📥 미승인 트렌드 대기 큐 (Inbox Queue)',
        inboxHeaderTitle: '"수집된 최신 기술 중 마음에 드는 것만 골라 분석을 의뢰하세요"',
        inboxHeaderDesc: '원문을 확인하고 [⚡ 분석 큐에 담기]를 누르면 Neon DB 대기열에 담겨 Antigravity AI가 심층 리서치에 착수합니다.',
        batchLabel: '💡 일괄 승격 명령어:',
        btnRequestAnalysis: '⚡ 분석 큐에 담기',
        btnCopyCmd: '📋 CLI 명령 복사'
      }},
      EN: {{
        subtitle: 'Multi-Entity Citation & Lineage Graph • Unit Economics ROI Simulator',
        tabPortfolio: '🏆 Verified Portfolio',
        tabGraph: '🕸️ Citation Lineage Graph',
        tabRoi: '📊 Unit Economics ROI',
        tabInbox: '📥 Inbox Triage Queue',
        btnAdmin: '⚙️ Harvester Admin',
        heroTitle: '"Viral AI & Tech Claims: Do They Actually Work & Make Economic Sense?"',
        heroDesc: 'A rigorous engineering portfolio proving both [👤 User-Curated] and [🤖 Auto-Harvested] projects with Tier 1~4 verified citations, 4-generation lineage trees, and unit economics cost audits.',
        metricTotal: 'Total Fact-Checks',
        metricUser: '👤 User-Curated Issues',
        metricAuto: '🤖 Autonomous Tracked',
        metricDev: '🟢 Active Developed',
        metricHalted: '🟡 Halted (Cost/Perf)',
        filterAllMode: 'All Discovery Modes',
        filterUserMode: '👤 User-Curated Only',
        filterAutoMode: '🤖 Auto-Harvested Only',
        stageLabel: 'Hands-on Status:',
        stageAll: 'All',
        stageDev: '🟢 Developed',
        stageHalted: '🟡 Halted (Cost/Perf)',
        stagePending: '⚪ Research Pending',
        inboxBadge: '📥 Unverified Candidate Queue (Inbox)',
        inboxHeaderTitle: '"Select & Queue Deep Fact-Checks on Freshly Discovered AI Trends"',
        inboxHeaderDesc: 'Inspect the source and click [⚡ Add to Analysis Queue] to store in Neon DB for Antigravity deep investigation.',
        batchLabel: '💡 Batch CLI Promotion:',
        btnRequestAnalysis: '⚡ Add to Analysis Queue',
        btnCopyCmd: '📋 Copy CLI Command'
      }}
    }};

    function setLanguage(lang) {{
      currentLang = lang;
      const dict = i18nDict[lang];
      
      const koBtn = document.getElementById('langKoBtn');
      const enBtn = document.getElementById('langEnBtn');
      if (lang === 'KO') {{
        koBtn.className = 'px-2.5 py-1 rounded-lg bg-indigo-600 text-white transition';
        enBtn.className = 'px-2.5 py-1 rounded-lg text-slate-400 hover:text-white transition';
      }} else {{
        koBtn.className = 'px-2.5 py-1 rounded-lg text-slate-400 hover:text-white transition';
        enBtn.className = 'px-2.5 py-1 rounded-lg bg-indigo-600 text-white transition';
      }}

      document.getElementById('i18nSubtitle').innerText = dict.subtitle;
      document.getElementById('i18nTabPortfolio').innerText = dict.tabPortfolio;
      document.getElementById('i18nTabGraph').innerText = dict.tabGraph;
      document.getElementById('i18nTabRoi').innerText = dict.tabRoi;
      document.getElementById('i18nTabInbox').innerText = dict.tabInbox;
      document.getElementById('i18nBtnAdmin').innerText = dict.btnAdmin;
      document.getElementById('i18nHeroTitle').innerText = dict.heroTitle;
      document.getElementById('i18nHeroDesc').innerHTML = dict.heroDesc;
      document.getElementById('i18nMetricTotal').innerText = dict.metricTotal;
      document.getElementById('i18nMetricUser').innerText = dict.metricUser;
      document.getElementById('i18nMetricAuto').innerText = dict.metricAuto;
      document.getElementById('i18nMetricDev').innerText = dict.metricDev;
      document.getElementById('i18nMetricHalted').innerText = dict.metricHalted;
      document.getElementById('i18nFilterAllMode').innerText = dict.filterAllMode;
      document.getElementById('i18nFilterUserMode').innerText = dict.filterUserMode;
      document.getElementById('i18nFilterAutoMode').innerText = dict.filterAutoMode;
      document.getElementById('i18nStageLabel').innerText = dict.stageLabel;
      document.getElementById('i18nStageAll').innerText = dict.stageAll;
      document.getElementById('i18nStageDev').innerText = dict.stageDev;
      document.getElementById('i18nStageHalted').innerText = dict.stageHalted;
      document.getElementById('i18nStagePending').innerText = dict.stagePending;
      document.getElementById('i18nInboxBadge').innerText = dict.inboxBadge;
      document.getElementById('i18nInboxHeaderTitle').innerText = dict.inboxHeaderTitle;
      document.getElementById('i18nInboxHeaderDesc').innerHTML = dict.inboxHeaderDesc;
      document.getElementById('i18nBatchLabel').innerText = dict.batchLabel;

      renderCards();
      renderInbox();
      updateRoiCalculators();
    }}

    function switchView(view) {{
      currentView = view;
      const portView = document.getElementById('portfolioView');
      const gView = document.getElementById('graphView');
      const roiView = document.getElementById('roiView');
      const inView = document.getElementById('inboxView');
      
      const pBtn = document.getElementById('tabPortfolioBtn');
      const gBtn = document.getElementById('tabGraphBtn');
      const rBtn = document.getElementById('tabRoiBtn');
      const iBtn = document.getElementById('tabInboxBtn');

      portView.classList.add('hidden');
      gView.classList.add('hidden');
      roiView.classList.add('hidden');
      inView.classList.add('hidden');

      pBtn.className = 'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-400 hover:text-white transition';
      gBtn.className = 'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-400 hover:text-white transition';
      rBtn.className = 'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-400 hover:text-white transition';
      iBtn.className = 'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-400 hover:text-white transition';

      if (view === 'portfolio') {{
        portView.classList.remove('hidden');
        pBtn.className = 'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 text-white transition shadow-sm';
        renderCards();
      }} else if (view === 'graph') {{
        gView.classList.remove('hidden');
        gBtn.className = 'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 text-white transition shadow-sm';
        if (!graphInitialized) {{
          initCitationGraph();
          graphInitialized = true;
        }}
      }} else if (view === 'roi') {{
        roiView.classList.remove('hidden');
        rBtn.className = 'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-cyan-600 text-white transition shadow-sm';
        updateRoiCalculators();
      }} else {{
        inView.classList.remove('hidden');
        iBtn.className = 'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-amber-600 text-white transition shadow-sm';
        renderInbox();
      }}
      lucide.createIcons();
    }}

    // ================= ROI CALCULATOR LOGIC =================
    function updateRoiCalculators() {{
      // 1. Scraping Calculator
      const pages = parseInt(document.getElementById('scrapingPagesSlider').value);
      document.getElementById('scrapingPagesDisplay').innerText = pages.toLocaleString() + ' 페이지/월';

      const firecrawlCost = Math.round(pages * 0.0025);
      const watercrawlCost = Math.round(38 + (pages / 1000000) * 15);
      const scrapyCost = Math.round(10 + (pages / 1000000) * 5);
      const scrapSavings = Math.max(0, firecrawlCost - watercrawlCost);
      const scrapSavingsPercent = Math.round((scrapSavings / firecrawlCost) * 100);

      document.getElementById('costFirecrawl').innerText = '$' + firecrawlCost.toLocaleString() + ' /월';
      document.getElementById('costWatercrawl').innerText = '$' + watercrawlCost.toLocaleString() + ' /월';
      document.getElementById('costScrapy').innerText = '$' + scrapyCost.toLocaleString() + ' /월';
      document.getElementById('scrapingSavings').innerText = '+$' + scrapSavings.toLocaleString() + ' /월 (' + scrapSavingsPercent + '% 절감)';

      // 2. Agent Inference Calculator
      const tokens = parseInt(document.getElementById('agentTokensSlider').value);
      const mTokens = tokens / 1000000;
      document.getElementById('agentTokensDisplay').innerText = (mTokens >= 1000 ? (mTokens/1000).toFixed(1) + 'B' : mTokens.toFixed(0) + 'M') + ' 토큰/월';

      const claudeCost = Math.round(mTokens * 6.0); // Avg input/output token price
      const praxistCost = Math.round((mTokens / 12) * 6.0); // 1/12 token reduction
      const deepseekCost = Math.round(120 + (mTokens / 1000) * 15); // Fixed server + electricity
      const agentSavings = Math.max(0, claudeCost - praxistCost);
      const agentSavingsPercent = Math.round((agentSavings / claudeCost) * 100);

      document.getElementById('costClaude').innerText = '$' + claudeCost.toLocaleString() + ' /월';
      document.getElementById('costPraxist').innerText = '$' + praxistCost.toLocaleString() + ' /월';
      document.getElementById('costDeepseek').innerText = '$' + deepseekCost.toLocaleString() + ' /월';
      document.getElementById('agentSavings').innerText = '+$' + agentSavings.toLocaleString() + ' /월 (' + agentSavingsPercent + '% 절감)';
    }}

    document.getElementById('scrapingPagesSlider').addEventListener('input', updateRoiCalculators);
    document.getElementById('agentTokensSlider').addEventListener('input', updateRoiCalculators);

    function initCitationGraph() {{
      const svg = d3.select("#techGraphSvg");
      const container = document.getElementById("graphView");
      const width = container.clientWidth || 1100;
      const height = 720;
      svg.attr("viewBox", [-width / 2, -height / 2, width, height]);

      const g = svg.append("g");

      svg.call(d3.zoom().scaleExtent([0.2, 4.0]).on("zoom", (e) => g.attr("transform", e.transform)));

      simulationRef = d3.forceSimulation(graphData.nodes)
        .force("link", d3.forceLink(graphData.links).id(d => d.id).distance(100))
        .force("charge", d3.forceManyBody().strength(-380))
        .force("center", d3.forceCenter(0, 0))
        .force("collision", d3.forceCollide().radius(d => (d.val || 15) + 14));

      linkSelection = g.append("g")
        .selectAll("line")
        .data(graphData.links)
        .join("line")
        .attr("stroke", "rgba(255, 255, 255, 0.2)")
        .attr("stroke-width", 1.5);

      const nodeGroup = g.append("g")
        .selectAll("g")
        .data(graphData.nodes)
        .join("g")
        .call(d3.drag()
          .on("start", dragstarted)
          .on("drag", dragged)
          .on("end", dragended));

      function getNodeColor(d) {{
        if (d.type === "person") return "#f59e0b";
        if (d.type === "org") return "#eab308";
        if (d.type === "paper") return "#10b981";
        return domainColorMap[d.group] || "#6366f1";
      }}

      nodeSelection = nodeGroup.append("circle")
        .attr("r", d => d.val || 16)
        .attr("fill", d => getNodeColor(d))
        .attr("stroke", "#ffffff")
        .attr("stroke-width", d => (d.type === "person" || d.type === "org") ? 2.5 : 1)
        .attr("opacity", 0.92)
        .attr("cursor", "pointer")
        .on("mouseover", (event, d) => highlightCitationFlow(d))
        .on("mouseout", () => resetHighlight())
        .on("click", (event, d) => {{
          const matchedCase = casesData.find(c => c.case_id.toLowerCase().includes(d.id.replace('p_', '').replace('org_', '').replace('_', '')) || (c.clustering && c.clustering.cluster_id.includes(d.group)));
          if (matchedCase) {{
            openModal(matchedCase);
          }}
        }});

      textSelection = nodeGroup.append("text")
        .text(d => d.label.split('(')[0].trim())
        .attr("x", 0)
        .attr("y", d => (d.val || 16) + 12)
        .attr("text-anchor", "middle")
        .attr("fill", "#f1f5f9")
        .attr("font-size", d => (d.type === "person" || d.type === "org" ? "11px" : (d.val > 24 ? "11px" : "9.5px")))
        .attr("font-weight", d => (d.type === "person" || d.type === "org" ? "700" : "600"))
        .attr("pointer-events", "none");

      simulationRef.on("tick", () => {{
        linkSelection
          .attr("x1", d => d.source.x)
          .attr("y1", d => d.source.y)
          .attr("x2", d => d.target.x)
          .attr("y2", d => d.target.y);

        nodeGroup
          .attr("transform", d => `translate(${{d.x}},${{d.y}})`);
      }});

      function dragstarted(event, d) {{
        if (!event.active) simulationRef.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      }}

      function dragged(event, d) {{
        d.fx = event.x;
        d.fy = event.y;
      }}

      function dragended(event, d) {{
        if (!event.active) simulationRef.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      }}
    }}

    function highlightCitationFlow(selectedNode) {{
      const connectedNodeIds = new Set();
      connectedNodeIds.add(selectedNode.id);

      graphData.links.forEach(l => {{
        const sId = typeof l.source === 'object' ? l.source.id : l.source;
        const tId = typeof l.target === 'object' ? l.target.id : l.target;
        if (sId === selectedNode.id) connectedNodeIds.add(tId);
        if (tId === selectedNode.id) connectedNodeIds.add(sId);
      }});

      nodeSelection.classed("node-dimmed", d => !connectedNodeIds.has(d.id));
      nodeSelection.classed("node-highlighted", d => connectedNodeIds.has(d.id));
      
      linkSelection.classed("link-dimmed", l => {{
        const sId = typeof l.source === 'object' ? l.source.id : l.source;
        const tId = typeof l.target === 'object' ? l.target.id : l.target;
        return sId !== selectedNode.id && tId !== selectedNode.id;
      }});
      linkSelection.classed("link-highlighted", l => {{
        const sId = typeof l.source === 'object' ? l.source.id : l.source;
        const tId = typeof l.target === 'object' ? l.target.id : l.target;
        return sId === selectedNode.id || tId === selectedNode.id;
      }});

      // Show floating tooltip
      const tt = document.getElementById("graphTooltip");
      document.getElementById("tooltipLabel").innerText = selectedNode.label;
      document.getElementById("tooltipTypeBadge").innerText = (selectedNode.type || 'tech').toUpperCase();
      document.getElementById("tooltipType").innerText = selectedNode.type || 'tech';
      document.getElementById("tooltipVal").innerText = selectedNode.val + ' pt';
      document.getElementById("tooltipDesc").innerText = selectedNode.desc || "인물/논문/기술 상세 계보 설명";
      tt.classList.remove("hidden");
    }}

    function resetHighlight() {{
      if (nodeSelection) {{
        nodeSelection.classed("node-dimmed", false);
        nodeSelection.classed("node-highlighted", false);
      }}
      if (linkSelection) {{
        linkSelection.classed("link-dimmed", false);
        linkSelection.classed("link-highlighted", false);
      }}
      document.getElementById("graphTooltip").classList.add("hidden");
    }}

    function filterGraphType(entityType) {{
      currentGraphType = entityType;
      document.querySelectorAll('.graph-type-btn').forEach(btn => {{
        if (btn.dataset.type === entityType) {{
          btn.classList.add('bg-indigo-600', 'text-white');
          btn.classList.remove('text-amber-400', 'text-yellow-400', 'text-emerald-400', 'text-cyan-400');
        }} else {{
          btn.classList.remove('bg-indigo-600', 'text-white');
        }}
      }});

      if (nodeSelection) {{
        nodeSelection.attr("opacity", d => {{
          if (entityType === 'ALL') return 0.95;
          if (entityType === 'tech') return (d.type !== 'person' && d.type !== 'org' && d.type !== 'paper') ? 0.95 : 0.1;
          return d.type === entityType ? 0.95 : 0.1;
        }});
        textSelection.attr("opacity", d => {{
          if (entityType === 'ALL') return 1;
          if (entityType === 'tech') return (d.type !== 'person' && d.type !== 'org' && d.type !== 'paper') ? 1 : 0.15;
          return d.type === entityType ? 1 : 0.15;
        }});
      }}
    }}

    function copyToClipboard(text) {{
      navigator.clipboard.writeText(text).then(() => {{
        const toast = document.getElementById('toast');
        document.getElementById('toastMsg').innerText = (currentLang === 'KO' ? '명령어가 클립보드에 복사되었습니다:\n' : 'Command copied to clipboard:\n') + text;
        toast.classList.remove('hidden');
        setTimeout(() => toast.classList.add('hidden'), 4000);
      }});
    }}

    let isFamilyGroupingActive = false;

    function toggleFamilyGrouping() {{
      isFamilyGroupingActive = !isFamilyGroupingActive;
      const btn = document.getElementById('groupByFamilyBtn');
      const text = document.getElementById('groupByFamilyText');
      if (isFamilyGroupingActive) {{
        btn.className = 'flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold bg-purple-600 text-white shadow-lg shadow-purple-500/20 transition shrink-0';
        text.innerText = currentLang === 'KO' ? '🧬 기저 모델 패밀리별 그룹화 (ON)' : '🧬 Group by Model Family (ON)';
      }} else {{
        btn.className = 'flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold bg-slate-900 text-purple-300 border border-purple-500/30 hover:bg-purple-500/10 transition shrink-0';
        text.innerText = currentLang === 'KO' ? '🧬 기저 모델 패밀리별 그룹화 (OFF)' : '🧬 Group by Model Family (OFF)';
      }}
      renderInbox();
    }}

    function renderInbox() {{
      const grid = document.getElementById('inboxGrid');
      grid.innerHTML = '';

      const filtered = inboxData.filter(item => {{
        const matchesSrc = currentInboxSource === 'ALL' || (item.source_platform && item.source_platform.includes(currentInboxSource));
        const text = (item.title + ' ' + (item.description || '') + ' ' + (item.source_platform || '') + ' ' + (item.model_family || '')).toLowerCase();
        const matchesSearch = text.includes(inboxSearchQuery.toLowerCase());
        return matchesSrc && matchesSearch;
      }});

      if (filtered.length === 0) {{
        grid.innerHTML = `<div class="col-span-full py-16 text-center text-slate-500">${{currentLang === 'KO' ? '인박스에 일치하는 후보가 없습니다.' : 'No matching inbox items found.'}}</div>`;
        return;
      }}

      if (isFamilyGroupingActive) {{
        const groups = {{}};
        filtered.forEach(it => {{
          const fam = it.model_family || '기타 독립 모델 (Standalone / Novel)';
          if (!groups[fam]) groups[fam] = [];
          groups[fam].push(it);
        }});

        Object.keys(groups).forEach(famName => {{
          const items = groups[famName];
          const groupCard = document.createElement('div');
          groupCard.className = 'col-span-full glass-card p-5 rounded-2xl border-purple-500/30 space-y-4';

          const formats = new Set();
          items.forEach(it => (it.detected_formats || []).forEach(f => formats.add(f)));

          let subItemsHtml = '';
          items.forEach(it => {{
            const promoteCmd = 'python tools/triage.py --promote ' + it.inbox_id;
            const audit = it.audit_risk || {{ hype_risk_score: 15, risk_level: "LOW_RISK" }};
            const isHighRisk = audit.risk_level === "HIGH_GAMING_RISK";
            subItemsHtml += `
              <div class="bg-slate-900/90 p-3.5 rounded-xl border border-slate-800 flex flex-col justify-between space-y-2">
                <div class="space-y-1.5">
                  <div class="flex items-center justify-between text-[11px]">
                    <span class="text-amber-400 font-bold">${{it.source_platform || 'Hub'}}</span>
                    <span class="text-slate-400 font-mono">${{it.viral_metric || ''}}</span>
                  </div>
                  <h4 class="font-bold text-xs text-white line-clamp-2">${{it.title}}</h4>
                  <div class="text-[10px] text-slate-400">포맷: <span class="text-purple-300">${{(it.detected_formats || []).join(', ')}}</span></div>
                </div>
                <div class="pt-2 border-t border-slate-800 flex items-center justify-between">
                  <a href="${{it.source_url}}" target="_blank" class="text-[11px] text-slate-400 hover:text-white flex items-center gap-0.5">원문 <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>
                  <button onclick="copyToClipboard('${{promoteCmd}}')" class="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 hover:bg-amber-500 hover:text-white text-[10px] font-bold transition">⚡ 분석 큐 담기</button>
                </div>
              </div>
            `;
          }});

          groupCard.innerHTML = `
            <div class="flex items-center justify-between pb-3 border-b border-slate-800 flex-wrap gap-2">
              <div class="flex items-center gap-2">
                <span class="px-2.5 py-0.5 rounded-full bg-purple-500/20 text-purple-300 text-xs font-bold border border-purple-500/30">
                  🧬 Base Model Family
                </span>
                <h3 class="text-base font-extrabold text-white">${{famName}}</h3>
                <span class="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">총 ${{items.length}}개 변형/양자화본</span>
              </div>
              <div class="flex items-center gap-1.5 flex-wrap">
                ${{Array.from(formats).map(fmt => `<span class="px-2 py-0.5 rounded bg-slate-900 text-indigo-300 text-[10px] border border-slate-700 font-semibold">${{fmt}}</span>`).join('')}}
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              ${{subItemsHtml}}
            </div>
          `;
          grid.appendChild(groupCard);
        }});

      }} else {{
        filtered.forEach((it) => {{
          const card = document.createElement('div');
          card.className = 'glass-card p-4 rounded-xl flex flex-col justify-between space-y-3 border-slate-800';

          const promoteCmd = `python tools/triage.py --promote ${{it.inbox_id}}`;
          const audit = it.audit_risk || {{ hype_risk_score: 15, risk_level: "LOW_RISK" }};
          const isHighRisk = audit.risk_level === "HIGH_GAMING_RISK";

          card.innerHTML = `
            <div class="space-y-2.5">
              <div class="flex items-center justify-between text-xs gap-1">
                <span class="px-2 py-0.5 rounded text-[11px] font-bold bg-amber-500/10 text-amber-300 border border-amber-500/20 truncate">
                  ${{it.source_platform || 'Tech'}}
                </span>
                <span class="px-2 py-0.5 rounded text-[10px] font-bold ${{isHighRisk ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' : 'bg-slate-800 text-slate-400'}}">
                  ${{isHighRisk ? '⚠️ 과장/슬롭 의심 (' + audit.hype_risk_score + '점)' : (it.viral_metric || 'Viral')}}
                </span>
              </div>

              <h4 class="font-bold text-sm text-white line-clamp-2 hover:text-amber-300 transition">
                ${{it.title}}
              </h4>

              <p class="text-xs text-slate-300 line-clamp-2 leading-relaxed">
                ${{it.description || '상세 내용 없음'}}
              </p>

              <div class="text-[11px] text-slate-400">
                🧬 <span class="text-purple-300 font-semibold">${{it.model_family || '독립 모델'}}</span>
              </div>
            </div>

            <div class="pt-3 border-t border-slate-800/80 flex flex-col gap-2">
              <div class="flex items-center justify-between">
                <a href="${{it.source_url}}" target="_blank" class="text-xs text-slate-400 hover:text-white flex items-center gap-1">
                  ${{currentLang === 'KO' ? '원문 링크' : 'Source Link'}} <i data-lucide="external-link" class="w-3 h-3"></i>
                </a>

                <button onclick="copyToClipboard('${{promoteCmd}}')" class="text-slate-400 hover:text-amber-300 text-[11px] flex items-center gap-1">
                  <i data-lucide="copy" class="w-3 h-3"></i> ${{i18nDict[currentLang].btnCopyCmd}}
                </button>
              </div>

              <button onclick="copyToClipboard('${{promoteCmd}}')" class="w-full text-center py-1.5 rounded-lg bg-amber-500/15 hover:bg-amber-500 text-amber-300 hover:text-white text-xs font-bold border border-amber-500/30 transition flex items-center justify-center gap-1.5 shadow-sm">
                <i data-lucide="zap" class="w-3.5 h-3.5"></i>
                ${{i18nDict[currentLang].btnRequestAnalysis}}
              </button>
            </div>
          `;
          grid.appendChild(card);
        }});
      }}

      lucide.createIcons();
    }}

      lucide.createIcons();
    }}

    function setInboxSourceFilter(src) {{
      currentInboxSource = src;
      document.querySelectorAll('.inbox-src-btn').forEach(btn => {{
        if (btn.dataset.src === src) {{
          btn.classList.add('bg-amber-600', 'text-white');
          btn.classList.remove('bg-slate-900', 'text-slate-300', 'text-amber-300');
        }} else {{
          btn.classList.remove('bg-amber-600', 'text-white');
          btn.classList.add('bg-slate-900');
        }}
      }});
      renderInbox();
    }}

    document.getElementById('inboxSearchInput').addEventListener('input', (e) => {{
      inboxSearchQuery = e.target.value;
      renderInbox();
    }});

    function getVerdictBadgeClass(verdict) {{
      if (verdict === 'VERIFIED_TRUE') return 'badge-true';
      if (verdict === 'HALF_TRUE_CONTEXT_REQUIRED' || verdict === 'HALF_TRUE') return 'badge-half';
      if (verdict === 'MISLEADING_GAMED' || verdict === 'CONFIRMED_FALSE') return 'badge-gamed';
      return 'bg-slate-800 text-slate-300 border-slate-700';
    }}

    function getVerdictLabel(verdict) {{
      if (verdict === 'VERIFIED_TRUE') return 'VERIFIED TRUE';
      if (verdict === 'HALF_TRUE_CONTEXT_REQUIRED' || verdict === 'HALF_TRUE') return currentLang === 'KO' ? 'HALF TRUE (맥락 필요)' : 'HALF TRUE (Context Req)';
      if (verdict === 'MISLEADING_GAMED') return currentLang === 'KO' ? 'MISLEADING (왜곡/과장)' : 'MISLEADING (Gamed)';
      if (verdict === 'CONFIRMED_FALSE') return 'CONFIRMED FALSE';
      return verdict;
    }}

    function getStageBadgeInfo(status) {{
      if (status === 'ACTIVE_DEVELOPED') {{
        return {{ class: 'badge-dev', label: currentLang === 'KO' ? '🟢 실제 개발 & 활용 완료' : '🟢 Active Developed', boxBorder: 'border-emerald-500/30' }};
      }}
      if (status === 'EVALUATED_HALTED') {{
        return {{ class: 'badge-halted', label: currentLang === 'KO' ? '🟡 성능/과금 문제로 개발 중단' : '🟡 Evaluated & Halted', boxBorder: 'border-amber-500/30' }};
      }}
      return {{ class: 'badge-pending', label: currentLang === 'KO' ? '⚪ 아직 개발 전 (기술 조사 완료)' : '⚪ Research Pending', boxBorder: 'border-slate-700' }};
    }}

    function renderCards() {{
      const grid = document.getElementById('cardsGrid');
      grid.innerHTML = '';

      const filtered = casesData.filter(c => {{
        const story = c.portfolio_story || {{}};
        const handsOn = story.hands_on_log || {{}};
        const stage = handsOn.status || 'PENDING_RESEARCH';
        const mode = c.curation ? c.curation.discovery_mode : 'USER_CURATED';
        
        const matchesMode = currentMode === 'ALL' || mode === currentMode;
        const matchesStage = currentStage === 'ALL' || stage === currentStage;
        const text = (c.title + ' ' + (c.category || '') + ' ' + (story.the_hook || '') + ' ' + (c.curation ? c.curation.personal_motivation : '')).toLowerCase();
        const matchesSearch = text.includes(searchQuery.toLowerCase());
        return matchesMode && matchesStage && matchesSearch;
      }});

      if (filtered.length === 0) {{
        grid.innerHTML = `<div class="col-span-full py-16 text-center text-slate-500">${{currentLang === 'KO' ? '조건에 맞는 팩트체크 케이스가 없습니다.' : 'No matching fact-checks found.'}}</div>`;
        return;
      }}

      filtered.forEach((c) => {{
        const story = c.portfolio_story || {{}};
        const handsOn = story.hands_on_log || {{}};
        const curation = c.curation || {{ discovery_mode: 'USER_CURATED' }};
        const clustering = c.clustering || {{ cluster_name: c.category || 'Tech' }};
        const badgeClass = getVerdictBadgeClass(c.verdict);
        const verdictLabel = getVerdictLabel(c.verdict);
        const stageInfo = getStageBadgeInfo(handsOn.status);

        const isUserMode = curation.discovery_mode === 'USER_CURATED';

        const card = document.createElement('div');
        card.className = 'glass-card p-5 rounded-xl flex flex-col justify-between cursor-pointer space-y-4';
        card.onclick = () => openModal(c);

        card.innerHTML = `
          <div class="space-y-3">
            <div class="flex items-center justify-between text-xs flex-wrap gap-1">
              <span class="px-2 py-0.5 rounded font-bold ${{isUserMode ? 'badge-user' : 'badge-auto'}} flex items-center gap-1">
                <i data-lucide="${{isUserMode ? 'user-check' : 'bot'}}" class="w-3 h-3"></i>
                ${{isUserMode ? (currentLang === 'KO' ? '👤 직접 큐레이션' : '👤 User-Curated') : (currentLang === 'KO' ? '🤖 자동 트렌드 발굴' : '🤖 Auto-Harvested')}}
              </span>
              <span class="px-2 py-0.5 rounded font-bold ${{badgeClass}}">${{verdictLabel}}</span>
            </div>
            
            <h3 class="font-bold text-base text-white hover:text-indigo-300 transition line-clamp-2">${{c.title}}</h3>
            
            <div class="flex items-center gap-1.5 text-xs flex-wrap">
              <span class="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 text-[11px]">
                ${{clustering.cluster_name ? clustering.cluster_name.split('(')[0].trim() : (c.category || 'Tech')}}
              </span>
              <span class="px-2 py-0.5 rounded font-medium ${{stageInfo.class}} text-[11px] flex items-center gap-1">
                ${{stageInfo.label}}
              </span>
            </div>

            <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800/80 space-y-1">
              <span class="text-[11px] font-semibold ${{isUserMode ? 'text-indigo-300' : 'text-sky-300'}} uppercase tracking-wider flex items-center gap-1">
                <i data-lucide="${{isUserMode ? 'help-circle' : 'trending-up'}}" class="w-3 h-3"></i>
                ${{isUserMode ? (currentLang === 'KO' ? '직접 발굴한 문제의식' : 'User Motivation') : (currentLang === 'KO' ? '트렌드 감사 동기' : 'Auto Trigger Reason')}}
              </span>
              <p class="text-xs text-slate-300 line-clamp-2">${{curation.personal_motivation || story.the_hook || '분석 진행 중'}}</p>
            </div>
          </div>

          <div class="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
            <span class="flex items-center gap-1">
              <i data-lucide="link" class="w-3 h-3"></i> ${{currentLang === 'KO' ? '출처 ' + (c.sources ? c.sources.length : 1) + '개 감사' : (c.sources ? c.sources.length : 1) + ' Sources Cited'}}
            </span>
            <span class="text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1">
              ${{currentLang === 'KO' ? '상세 계보 & 대체재 보기' : 'View Lineage & Audit'}} <i data-lucide="chevron-right" class="w-3.5 h-3.5"></i>
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
      const curation = c.curation || {{ discovery_mode: 'USER_CURATED', curator: 'Anyong Cheong' }};
      const clustering = c.clustering || {{ cluster_name: c.category || 'Tech', alternatives: [] }};
      const stageInfo = getStageBadgeInfo(handsOn.status);
      const isUserMode = curation.discovery_mode === 'USER_CURATED';
      
      const mBadge = document.getElementById('modalModeBadge');
      mBadge.className = 'text-xs px-2.5 py-0.5 rounded-md font-semibold ' + (isUserMode ? 'badge-user' : 'badge-auto');
      mBadge.innerText = isUserMode ? (currentLang === 'KO' ? '👤 직접 문제해결 큐레이션' : '👤 User Problem-Solving') : (currentLang === 'KO' ? '🤖 자율 트렌드 감사 발굴' : '🤖 Autonomous Audit');

      document.getElementById('modalClusterBadge').innerText = clustering.cluster_name || (c.category || 'Tech');
      
      const vBadge = document.getElementById('modalVerdictBadge');
      vBadge.className = 'text-xs px-2.5 py-0.5 rounded-md font-semibold ' + getVerdictBadgeClass(c.verdict);
      vBadge.innerText = getVerdictLabel(c.verdict);

      const sBadge = document.getElementById('modalStageBadge');
      sBadge.className = 'text-xs px-2.5 py-0.5 rounded-md font-medium ' + stageInfo.class;
      sBadge.innerText = stageInfo.label;

      document.getElementById('modalTitle').innerText = c.title;

      const cBox = document.getElementById('modalCurationBox');
      cBox.className = 'p-4 rounded-xl border space-y-1.5 ' + (isUserMode ? 'bg-indigo-950/30 border-indigo-500/30' : 'bg-sky-950/30 border-sky-500/30');
      document.getElementById('modalCurationTitle').className = 'text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 ' + (isUserMode ? 'text-indigo-300' : 'text-sky-300');
      document.getElementById('modalCuratorName').innerText = 'Curator: ' + (curation.curator || 'Anyong Cheong');
      document.getElementById('modalPersonalMotivation').innerText = curation.personal_motivation || story.the_hook || '내용 없음';
      document.getElementById('modalTargetWorkflow').innerText = curation.target_workflow || '일반 엔지니어링 파이프라인';

      // Root Ancestry Box
      const rootsList = document.getElementById('modalRootsList');
      rootsList.innerHTML = '';
      if (clustering.root_ancestry) {{
        const r = clustering.root_ancestry;
        if (r.core_parser_root) rootsList.innerHTML += `<div>• 코어 파서 뿌리: <span class="text-white font-medium">${{r.core_parser_root}}</span></div>`;
        if (r.automation_root) rootsList.innerHTML += `<div>• 브라우저 자동화: <span class="text-white font-medium">${{r.automation_root}}</span></div>`;
        if (r.direct_predecessor) rootsList.innerHTML += `<div>• 직전 선조 기술: <span class="text-indigo-300 font-medium">${{r.direct_predecessor}}</span></div>`;
      }} else {{
        rootsList.innerHTML = '<span class="text-slate-500">원시 파서 계보 확인 중</span>';
      }}
      document.getElementById('modalWhyLegacy').innerText = clustering.why_legacy_still_used || '단순 작업 시 0ms 결정론적 실행 및 $0 비용으로 인해 레거시 기술 지속 선호됨.';

      const altBody = document.getElementById('modalAlternativesBody');
      altBody.innerHTML = '';
      if (clustering.alternatives && clustering.alternatives.length > 0) {{
        clustering.alternatives.forEach(alt => {{
          const tr = document.createElement('tr');
          tr.className = 'hover:bg-slate-800/40 transition';
          tr.innerHTML = `
            <td class="p-2.5 font-bold text-white whitespace-nowrap">${{alt.name}}</td>
            <td class="p-2.5 text-slate-400 font-mono text-[11px] whitespace-nowrap">${{alt.tech_stack || 'N/A'}}</td>
            <td class="p-2.5 text-emerald-300">${{alt.pros || '-'}}</td>
            <td class="p-2.5 text-amber-300">${{alt.cons || '-'}}</td>
          `;
          altBody.appendChild(tr);
        }});
      }} else {{
        altBody.innerHTML = '<tr><td colspan="4" class="p-3 text-center text-slate-500">등록된 대체재 정보가 없습니다.</td></tr>';
      }}

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

    function setModeFilter(mode) {{
      currentMode = mode;
      document.querySelectorAll('.mode-btn').forEach(btn => {{
        if (btn.dataset.mode === mode) {{
          btn.classList.add('bg-indigo-600', 'text-white', 'border-indigo-500');
          btn.classList.remove('bg-slate-900');
        }} else {{
          btn.classList.remove('bg-indigo-600', 'text-white', 'border-indigo-500');
          btn.classList.add('bg-slate-900');
        }}
      }});
      renderCards();
    }}

    function setStageFilter(stage) {{
      currentStage = stage;
      document.querySelectorAll('.stage-btn').forEach(btn => {{
        if (btn.dataset.stage === stage) {{
          btn.classList.add('bg-slate-800', 'text-white');
          btn.classList.remove('bg-slate-900');
        }} else {{
          btn.classList.remove('bg-slate-800', 'text-white');
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

    document.addEventListener('DOMContentLoaded', () => {{
      lucide.createIcons();
      setLanguage('KO');
    }});
  </script>
</body>
</html>"""

if __name__ == "__main__":
    build_dashboard()
