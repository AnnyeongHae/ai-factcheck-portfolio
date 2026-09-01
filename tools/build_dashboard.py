#!/usr/bin/env python3
"""
Universal AI Citation & Tech Lineage Knowledge Hub (v15.0 - Taste-Skill Editorial Edition)
- 100% Anti-AI Slop: Warm Off-White / Swiss Editorial Canvas (#FBFBFA), zero neon cyberpunk glow, high-agency typography.
- 100% Live Neon DB Integration: Real-time queries for 17 Verified Cases, Technical Analyses, Inbox, and News.
- Dynamic Hero Featured Case + Asymmetric Editorial Grid Layout.
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
    public_dir = os.path.join(base_dir, "public")
    
    os.makedirs(dash_dir, exist_ok=True)
    os.makedirs(docs_dir, exist_ok=True)
    os.makedirs(public_dir, exist_ok=True)

    cases = scan_investigations()
    inbox_items = scan_inbox()
    admin_stats = get_harvest_admin_stats()
    graph_data = load_graph_data()
    
    total_cases = len(cases)
    news_items = [it for it in inbox_items if it.get("category_type") == "NEWS"]
    tech_inbox_items = [it for it in inbox_items if it.get("category_type") != "NEWS"]

    summary_data = {
        "generated_at": "2026-09-02",
        "total_cases": total_cases,
        "news_total_count": len(news_items),
        "inbox_total_count": len(tech_inbox_items),
        "all_inbox_count": len(inbox_items),
        "admin_stats": admin_stats,
        "inbox_items": inbox_items,
        "cases": cases,
        "graph": graph_data
    }

    # Write data.json
    for target_dir in [dash_dir, docs_dir, base_dir, public_dir]:
        json_path = os.path.join(target_dir, "data.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)

    # Generate HTML
    html_content = generate_html(summary_data)
    for target_dir in [dash_dir, docs_dir, base_dir, public_dir]:
        html_path = os.path.join(target_dir, "index.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

    print(f"[+] Successfully built Taste-Skill Editorial Dashboard v15.0 at:")
    print(f"    - public/index.html & data.json (Vercel CDN Edge)")
    print(f"    - index.html & data.json (Root entry)")
    print(f"    - dashboard/index.html (Verified: {total_cases}, News: {len(news_items)}, Inbox: {len(tech_inbox_items)})")
    print(f"    - docs/index.html (GitHub Pages hosting)")

def generate_html(data):
    cases_json = json.dumps(data["cases"], ensure_ascii=False)
    inbox_json = json.dumps(data["inbox_items"], ensure_ascii=False)
    admin_json = json.dumps(data["admin_stats"], ensure_ascii=False)
    graph_json = json.dumps(data["graph"], ensure_ascii=False)
    
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FactCheck Hub — Universal AI Tech Intelligence</title>
  
  <!-- Fonts: Pretendard + Geist + Newsreader + JetBrains Mono -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,600;1,6..72,400&family=Pretendard:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/lucide@latest"></script>
  <script src="https://d3js.org/d3.v7.min.js"></script>

  <script>
    tailwind.config = {{
      theme: {{
        extend: {{
          fontFamily: {{
            sans: ['Pretendard', 'Geist', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
            serif: ['Newsreader', 'Georgia', 'serif'],
            mono: ['JetBrains Mono', 'monospace'],
          }},
          colors: {{
            canvas: {{
              base: '#fbfbfa',
              subtle: '#f4f4f2',
              card: '#ffffff',
              border: '#e6e6e3',
              borderDark: '#1e2433',
            }},
            ink: {{
              primary: '#111827',
              secondary: '#4b5563',
              muted: '#9ca3af',
            }},
            accent: {{
              forest: '#047857',
              amber: '#b45309',
              terracotta: '#c2410c',
              navy: '#1e3a8a',
            }}
          }}
        }}
      }}
    }}
  </script>

  <style>
    body {{
      font-family: 'Pretendard', 'Geist', -apple-system, BlinkMacSystemFont, sans-serif;
      background-color: #fbfbfa;
      color: #111827;
      letter-spacing: -0.015em;
    }}

    /* Subtle Paper Texture Line Grid */
    .bg-paper-grid {{
      background-image: linear-gradient(to right, rgba(0, 0, 0, 0.03) 1px, transparent 1px),
                        linear-gradient(to bottom, rgba(0, 0, 0, 0.03) 1px, transparent 1px);
      background-size: 32px 32px;
    }}

    /* Editorial Card Surface */
    .editorial-card {{
      background: #ffffff;
      border: 1px solid #e6e6e3;
      border-radius: 12px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03), 0 6px 16px -4px rgba(0, 0, 0, 0.02);
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }}
    .editorial-card:hover {{
      border-color: #111827;
      box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.08);
      transform: translateY(-2px);
    }}

    /* Hero Featured Card */
    .hero-card {{
      background: #ffffff;
      border: 1.5px solid #111827;
      border-radius: 16px;
      box-shadow: 0 8px 30px -6px rgba(0, 0, 0, 0.08);
    }}

    /* Segment Buttons */
    .segment-btn {{
      transition: all 0.15s ease;
      color: #6b7280;
    }}
    .segment-btn.active {{
      background: #111827;
      color: #ffffff;
      font-weight: 700;
    }}

    /* Tag Pills */
    .tag-pill {{
      transition: all 0.15s ease;
    }}
    .tag-pill.active {{
      background: #111827;
      color: #ffffff;
      font-weight: 700;
      border-color: #111827;
    }}

    /* Verdict Indicators */
    .verdict-true {{
      color: #047857;
      background: #ecfdf5;
      border: 1px solid #a7f3d0;
    }}
    .verdict-half {{
      color: #b45309;
      background: #fffbeb;
      border: 1px solid #fde68a;
    }}
    .verdict-gamed {{
      color: #b91c1c;
      background: #fef2f2;
      border: 1px solid #fecaca;
    }}

    /* Hide scrollbar for Chrome, Safari and Opera */
    .no-scrollbar::-webkit-scrollbar {{
      display: none;
    }}
    .no-scrollbar {{
      -ms-overflow-style: none;
      scrollbar-width: none;
    }}
  </style>
</head>
<body class="bg-canvas-base text-ink-primary min-h-screen bg-paper-grid pb-24 antialiased selection:bg-ink-primary selection:text-white">

  <!-- ==================== EDITORIAL HEADER ==================== -->
  <header class="sticky top-0 z-40 bg-canvas-base/95 backdrop-blur-md border-b border-canvas-border">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-3 sm:gap-4">
      
      <!-- Brand Logo (Swiss Minimalist) -->
      <div class="flex items-center gap-3 shrink-0">
        <div class="w-9 h-9 rounded-lg bg-ink-primary flex items-center justify-center text-white font-serif font-bold text-lg shadow-sm">
          F
        </div>
        <div>
          <div class="flex items-center gap-2">
            <span class="text-base font-extrabold text-ink-primary tracking-tight font-serif">FactCheck Hub</span>
            <span class="text-[10px] font-mono px-1.5 py-0.2 rounded bg-canvas-subtle border border-canvas-border text-ink-secondary font-bold">2026</span>
          </div>
          <p class="text-[11px] text-ink-secondary hidden sm:block">Empirical Architecture & Cost Intelligence</p>
        </div>
      </div>

      <!-- Desktop Navigation Tabs -->
      <nav class="hidden md:flex items-center gap-1 bg-canvas-subtle p-1 rounded-xl border border-canvas-border text-xs font-semibold">
        <button onclick="switchView('portfolio')" id="tabPortfolioBtn" class="nav-tab active flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-white bg-ink-primary transition">
          <i data-lucide="check-circle" class="w-3.5 h-3.5 text-white"></i>
          <span>기술 검증</span>
          <span class="text-[10px] font-mono px-1.5 py-0.2 rounded bg-white/20 text-white font-bold" id="headerVerifiedCount">{data['total_cases']}</span>
        </button>
        <button onclick="switchView('news')" id="tabNewsBtn" class="nav-tab flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-ink-secondary hover:text-ink-primary transition">
          <i data-lucide="newspaper" class="w-3.5 h-3.5"></i>
          <span>AI 뉴스</span>
          <span class="text-[10px] font-mono text-ink-muted">({data['news_total_count']})</span>
        </button>
        <button onclick="switchView('graph')" id="tabGraphBtn" class="nav-tab flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-ink-secondary hover:text-ink-primary transition">
          <i data-lucide="network" class="w-3.5 h-3.5"></i>
          <span>인용 계보망</span>
        </button>
        <button onclick="switchView('roi')" id="tabRoiBtn" class="nav-tab flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-ink-secondary hover:text-ink-primary transition">
          <i data-lucide="calculator" class="w-3.5 h-3.5"></i>
          <span>원가 시뮬레이터</span>
        </button>
        <button onclick="switchView('inbox')" id="tabInboxBtn" class="nav-tab flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-ink-secondary hover:text-ink-primary transition">
          <i data-lucide="inbox" class="w-3.5 h-3.5"></i>
          <span>수집 인박스</span>
          <span class="text-[10px] font-mono text-ink-muted">({data['inbox_total_count']})</span>
        </button>
      </nav>

      <!-- Right Header Actions (Live DB Status + Lang) -->
      <div class="flex items-center gap-2 sm:gap-2.5 shrink-0">
        <!-- Live DB Sync Badge -->
        <div id="dbLiveBadge">
          <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse"></span>
            <span class="hidden xs:inline sm:inline">Neon DB</span> Live
          </span>
        </div>

        <!-- Language Toggle -->
        <div class="bg-canvas-subtle p-0.5 sm:p-1 rounded-lg border border-canvas-border flex items-center text-xs font-semibold">
          <button onclick="setLanguage('KO')" id="langKoBtn" class="px-2 py-0.5 rounded bg-ink-primary text-white transition text-[10px] sm:text-[11px]">KO</button>
          <button onclick="setLanguage('EN')" id="langEnBtn" class="px-2 py-0.5 rounded text-ink-secondary hover:text-ink-primary transition text-[10px] sm:text-[11px]">EN</button>
        </div>
      </div>

    </div>

    <!-- Mobile Scrollable Sub-Navigation Bar -->
    <div class="flex md:hidden items-center gap-1.5 px-3 py-2 overflow-x-auto no-scrollbar border-t border-canvas-border bg-canvas-base">
      <button onclick="switchView('portfolio')" id="mTabPortfolioBtn" class="mobile-nav-tab active shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-ink-primary transition">
        <i data-lucide="check-circle" class="w-3.5 h-3.5 text-white"></i>
        <span>기술 검증</span>
        <span class="text-[9px] font-mono px-1 py-0.2 rounded bg-white/20 text-white font-bold" id="mHeaderVerifiedCount">{data['total_cases']}</span>
      </button>
      <button onclick="switchView('news')" id="mTabNewsBtn" class="mobile-nav-tab shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium text-ink-secondary hover:text-ink-primary bg-white border border-canvas-border transition">
        <i data-lucide="newspaper" class="w-3.5 h-3.5"></i>
        <span>AI 뉴스 ({data['news_total_count']})</span>
      </button>
      <button onclick="switchView('graph')" id="mTabGraphBtn" class="mobile-nav-tab shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium text-ink-secondary hover:text-ink-primary bg-white border border-canvas-border transition">
        <i data-lucide="network" class="w-3.5 h-3.5"></i>
        <span>인용 계보망</span>
      </button>
      <button onclick="switchView('roi')" id="mTabRoiBtn" class="mobile-nav-tab shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium text-ink-secondary hover:text-ink-primary bg-white border border-canvas-border transition">
        <i data-lucide="calculator" class="w-3.5 h-3.5"></i>
        <span>원가 시뮬레이터</span>
      </button>
      <button onclick="switchView('inbox')" id="mTabInboxBtn" class="mobile-nav-tab shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium text-ink-secondary hover:text-ink-primary bg-white border border-canvas-border transition">
        <i data-lucide="inbox" class="w-3.5 h-3.5"></i>
        <span>수집 인박스 ({data['inbox_total_count']})</span>
      </button>
    </div>
  </header>

  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">

    <!-- ==================== VIEW 1: TECH FACT-CHECK (기술 검증) ==================== -->
    <div id="portfolioView" class="space-y-8">

      <!-- Editorial Intro Manifesto -->
      <div class="border-b border-canvas-border pb-6 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div class="max-w-3xl space-y-2">
          <div class="text-[11px] font-mono font-bold tracking-widest text-ink-muted uppercase">
            Empirical Architecture & Fact-Check Journal
          </div>
          <h2 class="text-2xl sm:text-3xl font-extrabold text-ink-primary tracking-tight font-serif">
            소문난 AI 기술의 실체와 공학적 단위 경제성
          </h2>
          <p class="text-xs sm:text-sm text-ink-secondary leading-relaxed">
            AI 바이럴 마케팅의 환각을 걷어내고, <strong>1차 공식 출처 감사</strong>와 <strong>기저 표준 vs 서드파티 아키텍처 실측 벤치마크</strong>를 통해 도출한 기술 검증 보고서입니다.
          </p>
        </div>

        <div class="text-right shrink-0 hidden md:block">
          <div class="text-xs text-ink-muted font-mono font-medium">LATEST UPDATE</div>
          <div class="text-sm font-bold text-ink-primary font-mono">2026-09-02</div>
        </div>
      </div>

      <!-- HIGH-VISIBILITY CONTROL CENTER (선명한 에디토리얼 컨트롤 바) -->
      <div class="bg-white p-4 sm:p-5 rounded-2xl border border-canvas-border space-y-4 shadow-sm">
        
        <!-- Row 1: 3-Segment Discovery Mode & Sorting Selector -->
        <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
          
          <!-- Mode Segments -->
          <div class="flex items-center bg-canvas-subtle p-1 rounded-xl border border-canvas-border text-xs w-full md:w-auto">
            <button onclick="setModeFilter('ALL')" id="modeBtnAll" class="segment-btn active flex-1 md:flex-initial px-4 py-2 rounded-lg text-xs font-bold transition flex items-center justify-center gap-1.5">
              <span>전체 검증</span>
              <span class="text-[11px] font-mono px-1.5 py-0.2 rounded bg-black/10 text-white font-bold" id="badgeCountAll">17</span>
            </button>
            <button onclick="setModeFilter('USER_CURATED')" id="modeBtnUser" class="segment-btn flex-1 md:flex-initial px-4 py-2 rounded-lg text-xs font-semibold hover:text-ink-primary transition flex items-center justify-center gap-1.5">
              <i data-lucide="user-check" class="w-3.5 h-3.5"></i>
              <span>직접 큐레이션</span>
              <span class="text-[11px] font-mono px-1.5 py-0.2 rounded bg-black/5 text-ink-secondary font-bold" id="badgeCountUser">10</span>
            </button>
            <button onclick="setModeFilter('AUTO_HARVESTED')" id="modeBtnAuto" class="segment-btn flex-1 md:flex-initial px-4 py-2 rounded-lg text-xs font-semibold hover:text-ink-primary transition flex items-center justify-center gap-1.5">
              <i data-lucide="bot" class="w-3.5 h-3.5"></i>
              <span>자동 트렌드</span>
              <span class="text-[11px] font-mono px-1.5 py-0.2 rounded bg-black/5 text-ink-secondary font-bold" id="badgeCountAuto">7</span>
            </button>
          </div>

          <!-- Sort Select & Results Counter -->
          <div class="flex items-center justify-between w-full md:w-auto gap-3">
            <span class="text-xs text-ink-secondary font-mono" id="resultsCountLabel">총 17건 표시</span>
            
            <div class="flex items-center gap-2 bg-canvas-subtle px-3 py-1.5 rounded-xl border border-canvas-border text-xs">
              <i data-lucide="arrow-up-down" class="w-3.5 h-3.5 text-ink-secondary shrink-0"></i>
              <span class="text-ink-secondary text-xs font-medium shrink-0">정렬:</span>
              <select id="sortSelect" onchange="changeSort(this.value)" class="bg-transparent text-ink-primary font-bold text-xs focus:outline-none cursor-pointer">
                <option value="date-desc">최신 조사일자순 (기본)</option>
                <option value="date-asc">과거 조사일자순</option>
                <option value="score-desc">높은 신뢰도순</option>
                <option value="title-asc">기술명 가나다순</option>
              </select>
            </div>
          </div>

        </div>

        <!-- Row 2: Search Input & Domain Tag Filter Pills -->
        <div class="flex flex-col lg:flex-row items-center justify-between gap-3 pt-3 border-t border-canvas-border">
          
          <!-- Search Box -->
          <div class="relative w-full lg:w-96">
            <i data-lucide="search" class="w-4 h-4 absolute left-3.5 top-2.5 text-ink-muted"></i>
            <input type="text" id="searchInput" placeholder="기술명, 아키텍처, 큐레이션 동기 검색..." 
                   class="w-full bg-canvas-subtle border border-canvas-border rounded-xl pl-10 pr-9 py-2 text-xs text-ink-primary placeholder-ink-muted focus:outline-none focus:border-ink-primary transition font-medium">
            <button onclick="clearSearch()" id="clearSearchBtn" class="hidden absolute right-3 top-2.5 text-ink-muted hover:text-ink-primary">
              <i data-lucide="x" class="w-3.5 h-3.5"></i>
            </button>
          </div>

          <!-- Domain Tag Filter Pills (Horizontal Touch Swipe) -->
          <div class="flex items-center gap-1.5 w-full lg:w-auto justify-start lg:justify-end overflow-x-auto no-scrollbar py-1">
            <span class="text-[11px] text-ink-muted font-mono mr-1 shrink-0">도메인:</span>
            <button onclick="setDomainFilter('ALL')" class="tag-pill active shrink-0 px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-canvas-subtle text-ink-secondary border border-canvas-border hover:border-ink-primary" data-domain="ALL">전체</button>
            <button onclick="setDomainFilter('frontend')" class="tag-pill shrink-0 px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-canvas-subtle text-ink-secondary border border-canvas-border hover:border-ink-primary" data-domain="frontend">프론트엔드/디자인</button>
            <button onclick="setDomainFilter('agent')" class="tag-pill shrink-0 px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-canvas-subtle text-ink-secondary border border-canvas-border hover:border-ink-primary" data-domain="agent">AI 에이전트</button>
            <button onclick="setDomainFilter('scraping')" class="tag-pill shrink-0 px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-canvas-subtle text-ink-secondary border border-canvas-border hover:border-ink-primary" data-domain="scraping">웹 스크래핑/브라우저</button>
            <button onclick="setDomainFilter('doc')" class="tag-pill shrink-0 px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-canvas-subtle text-ink-secondary border border-canvas-border hover:border-ink-primary" data-domain="doc">문서 파싱/OCR</button>
            <button onclick="setDomainFilter('3d')" class="tag-pill shrink-0 px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-canvas-subtle text-ink-secondary border border-canvas-border hover:border-ink-primary" data-domain="3d">3D/컴포넌트</button>
            <button onclick="setDomainFilter('rust')" class="tag-pill shrink-0 px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-canvas-subtle text-ink-secondary border border-canvas-border hover:border-ink-primary" data-domain="rust">Rust/시스템</button>
          </div>

        </div>

      </div>

      <!-- FEATURED HERO DOSSIER (1위 최신 케이스 와이드 쇼케이스) -->
      <div id="featuredHeroContainer"></div>

      <!-- ASYMMETRIC EDITORIAL DOSSIER GRID -->
      <div id="cardsGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6"></div>
    </div>

    <!-- ==================== VIEW 2: AI NEWS & TRENDS (AI 뉴스 피드) ==================== -->
    <div id="newsView" class="hidden space-y-6">
      <div class="editorial-card p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div class="space-y-1">
          <div class="flex items-center gap-2">
            <span class="px-2.5 py-0.5 rounded-md bg-canvas-subtle text-ink-primary text-xs font-mono font-bold border border-canvas-border">
              GLOBAL AI INTELLIGENCE FEED
            </span>
            <span class="text-xs text-ink-secondary font-mono">총 {data['news_total_count']}건</span>
          </div>
          <h2 class="text-lg font-bold text-ink-primary font-serif">커뮤니티, 해커뉴스, 사설에서 수집된 주요 AI 담론</h2>
          <p class="text-xs text-ink-secondary">
            소프트웨어 저장소뿐만 아니라 엔지니어링 동향, 보안 리포트, 아키텍처 튜토리얼 기사를 선별합니다.
          </p>
        </div>
      </div>

      <div id="newsGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5"></div>
    </div>

    <!-- ==================== VIEW 3: CITATION & LINEAGE GRAPH ==================== -->
    <div id="graphView" class="hidden space-y-6">
      <div class="editorial-card p-6 space-y-4">
        <div class="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
          <div>
            <div class="flex items-center gap-2 flex-wrap">
              <span class="px-2.5 py-0.5 rounded-md bg-canvas-subtle text-ink-primary text-xs font-mono font-bold border border-canvas-border">
                MULTI-ENTITY CITATION NETWORK
              </span>
              <span class="text-xs text-ink-secondary">기술 • 연구자 • 연구소 • 1차 논문</span>
            </div>
            <h2 class="text-lg font-bold text-ink-primary mt-1 font-serif">인물과 논문 인용 계보를 통한 기술 탄생의 뿌리 지도</h2>
          </div>

          <!-- Entity Group Filters -->
          <div class="flex flex-wrap items-center gap-1.5 bg-canvas-subtle p-1.5 rounded-xl border border-canvas-border text-xs">
            <button onclick="filterGraphGroup('ALL')" class="graph-group-btn active px-2.5 py-1 rounded-lg bg-ink-primary text-white font-medium transition" data-group="ALL">전체 보기</button>
            <button onclick="filterGraphGroup('language')" class="graph-group-btn px-2.5 py-1 rounded-lg text-amber-700 hover:bg-white transition" data-group="language">언어</button>
            <button onclick="filterGraphGroup('technology')" class="graph-group-btn px-2.5 py-1 rounded-lg text-emerald-700 hover:bg-white transition" data-group="technology">기술/엔진</button>
            <button onclick="filterGraphGroup('organization')" class="graph-group-btn px-2.5 py-1 rounded-lg text-indigo-700 hover:bg-white transition" data-group="organization">연구소</button>
            <button onclick="filterGraphGroup('person')" class="graph-group-btn px-2.5 py-1 rounded-lg text-rose-700 hover:bg-white transition" data-group="person">인물</button>
            <button onclick="filterGraphGroup('paper')" class="graph-group-btn px-2.5 py-1 rounded-lg text-orange-700 hover:bg-white transition" data-group="paper">논문</button>
          </div>
        </div>

        <div class="relative w-full h-[640px] bg-white rounded-xl border border-canvas-border overflow-hidden">
          <svg id="techGraphSvg" class="w-full h-full cursor-grab active:cursor-grabbing"></svg>
          
          <div class="absolute bottom-4 left-4 bg-white/95 backdrop-blur p-3 rounded-xl border border-canvas-border text-xs space-y-1 shadow-sm">
            <div class="text-ink-secondary font-semibold text-[11px]">네트워크 인터랙션:</div>
            <div class="text-ink-primary text-[11px]">• 노드 드래그 및 마우스 휠 줌/팬</div>
            <div class="text-ink-primary text-[11px]">• 노드 호버 시 직접 인용 연결선 하이라이트</div>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== VIEW 4: ROI UNIT ECONOMICS SIMULATOR ==================== -->
    <div id="roiView" class="hidden space-y-6">
      <div class="editorial-card p-6 sm:p-8 space-y-6">
        <div class="max-w-2xl space-y-1.5">
          <div class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md bg-canvas-subtle text-ink-primary text-xs font-mono font-bold border border-canvas-border">
            UNIT ECONOMICS CALCULATOR
          </div>
          <h2 class="text-xl font-bold text-ink-primary font-serif">상용 유료 SaaS vs 오픈소스 자체 구축 원가 역산</h2>
          <p class="text-xs text-ink-secondary">
            팩트체크 검증 과정에서 실측한 단위 원가를 기반으로 월간 운영 비용을 실시간 비교합니다.
          </p>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          <!-- Scraping ROI Box -->
          <div class="bg-canvas-subtle p-6 rounded-2xl border border-canvas-border space-y-4">
            <div class="flex items-center justify-between">
              <h3 class="text-sm font-bold text-ink-primary flex items-center gap-2">
                <i data-lucide="globe" class="w-4 h-4 text-ink-secondary"></i> 웹 스크래핑 파이프라인
              </h3>
              <span class="text-xs font-mono text-ink-primary font-bold" id="scrapingPagesDisplay">100,000 페이지/월</span>
            </div>

            <input type="range" id="scrapingPagesSlider" min="10000" max="1000000" step="10000" value="100000" class="w-full accent-ink-primary cursor-pointer">

            <div class="grid grid-cols-2 gap-3 pt-2 text-xs">
              <div class="p-3 rounded-xl bg-white border border-canvas-border space-y-1">
                <div class="text-ink-muted text-[11px]">Firecrawl Cloud SaaS</div>
                <div class="text-base font-bold text-rose-600" id="costFirecrawl">$250 /월</div>
              </div>
              <div class="p-3 rounded-xl bg-white border border-canvas-border space-y-1">
                <div class="text-emerald-700 text-[11px] font-semibold">WaterCrawl 자체 구축</div>
                <div class="text-base font-bold text-emerald-600" id="costWatercrawl">$40 /월</div>
              </div>
            </div>

            <div class="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 font-semibold flex items-center justify-between" id="scrapingSavings">
              +$210 /월 절감 (84% 절약)
            </div>
          </div>

          <!-- Agent Token ROI Box -->
          <div class="bg-canvas-subtle p-6 rounded-2xl border border-canvas-border space-y-4">
            <div class="flex items-center justify-between">
              <h3 class="text-sm font-bold text-ink-primary flex items-center gap-2">
                <i data-lucide="bot" class="w-4 h-4 text-ink-secondary"></i> AI 에이전트 토큰 파이프라인
              </h3>
              <span class="text-xs font-mono text-ink-primary font-bold" id="agentTokensDisplay">50M 토큰/월</span>
            </div>

            <input type="range" id="agentTokensSlider" min="10000000" max="500000000" step="10000000" value="50000000" class="w-full accent-ink-primary cursor-pointer">

            <div class="grid grid-cols-2 gap-3 pt-2 text-xs">
              <div class="p-3 rounded-xl bg-white border border-canvas-border space-y-1">
                <div class="text-ink-muted text-[11px]">Claude 3.5 Sonnet 직접 호출</div>
                <div class="text-base font-bold text-rose-600" id="costClaude">$300 /월</div>
              </div>
              <div class="p-3 rounded-xl bg-white border border-canvas-border space-y-1">
                <div class="text-indigo-700 text-[11px] font-semibold">PRAXIST 그래프 프루닝</div>
                <div class="text-base font-bold text-emerald-600" id="costPraxist">$25 /월</div>
              </div>
            </div>

            <div class="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 font-semibold flex items-center justify-between" id="agentSavings">
              +$275 /월 절감 (92% 절약)
            </div>
          </div>

        </div>
      </div>
    </div>

    <!-- ==================== VIEW 5: HARVEST INBOX ==================== -->
    <div id="inboxView" class="hidden space-y-6">
      
      <div class="editorial-card p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div class="space-y-1">
          <div class="flex items-center gap-2">
            <span class="px-2.5 py-0.5 rounded-md bg-canvas-subtle text-ink-primary text-xs font-mono font-bold border border-canvas-border">
              AUTONOMOUS HARVEST INBOX
            </span>
            <span class="text-xs text-ink-secondary font-mono">총 {data['inbox_total_count']}건</span>
          </div>
          <h2 class="text-lg font-bold text-ink-primary font-serif">24시간 자율 크론으로 수집된 오픈소스 및 모델 후보군</h2>
          <p class="text-xs text-ink-secondary">
            원클릭으로 분석 큐에 등록하여 Neon DB와 실시간 동기화하고 심층 팩트체크를 진행할 수 있습니다.
          </p>
        </div>
      </div>

      <!-- Clean Inbox Controls -->
      <div class="bg-white p-3.5 rounded-2xl flex flex-col md:flex-row items-center justify-between gap-3 border border-canvas-border">
        <div class="flex items-center gap-2.5 w-full md:w-auto">
          <div class="relative w-full md:w-80">
            <i data-lucide="search" class="w-4 h-4 absolute left-3.5 top-2.5 text-ink-muted"></i>
            <input type="text" id="inboxSearchInput" placeholder="후보 기술 또는 모델명 검색..." 
                   class="w-full bg-canvas-subtle border border-canvas-border rounded-xl pl-10 pr-4 py-2 text-xs text-ink-primary placeholder-ink-muted focus:outline-none focus:border-ink-primary transition font-medium">
          </div>

          <button onclick="toggleFamilyGrouping()" id="groupByFamilyBtn" class="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold bg-ink-primary text-white transition shrink-0">
            <i data-lucide="layers" class="w-4 h-4"></i>
            <span id="groupByFamilyText">패밀리 묶음 (ON)</span>
          </button>
        </div>

        <div class="flex items-center gap-2 w-full md:w-auto justify-end">
          <div class="flex items-center gap-1.5 bg-canvas-subtle px-3 py-1.5 rounded-xl border border-canvas-border text-xs">
            <i data-lucide="filter" class="w-3.5 h-3.5 text-ink-secondary"></i>
            <select id="inboxSourceSelect" onchange="setInboxSourceFilter(this.value)" class="bg-transparent text-ink-primary text-xs font-semibold focus:outline-none cursor-pointer">
              <option value="ALL">전체 수집 플랫폼 ({data['inbox_total_count']}건)</option>
              <option value="Hugging Face Spaces">🤗 Hugging Face Spaces</option>
              <option value="Hugging Face Models">🤗 Hugging Face Models</option>
              <option value="GitHub Official">🐙 GitHub Official</option>
              <option value="ArXiv Preprint">📄 ArXiv Preprint</option>
            </select>
          </div>
        </div>
      </div>

      <div id="inboxGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5"></div>
    </div>

  </main>

  <!-- ==================== DETAILED TECHNICAL DOSSIER MODAL ==================== -->
  <div id="detailModal" class="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm hidden flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
    <div class="editorial-card max-w-4xl w-full rounded-2xl overflow-hidden shadow-2xl border border-canvas-border my-8 max-h-[92vh] flex flex-col bg-white">
      
      <!-- Modal Header -->
      <div class="p-6 border-b border-canvas-border flex items-start justify-between bg-canvas-subtle">
        <div class="space-y-1.5 pr-4">
          <div class="flex items-center gap-2 flex-wrap">
            <span id="modalModeBadge" class="text-xs px-2.5 py-0.5 rounded-md font-semibold"></span>
            <span id="modalClusterBadge" class="text-xs px-2.5 py-0.5 rounded-md bg-white text-ink-primary border border-canvas-border font-medium"></span>
            <span id="modalVerdictBadge" class="text-xs px-2.5 py-0.5 rounded-md font-semibold"></span>
            <span id="modalStageBadge" class="text-xs px-2.5 py-0.5 rounded-md font-medium"></span>
          </div>
          <h3 id="modalTitle" class="text-xl font-bold text-ink-primary pt-1 font-serif"></h3>
        </div>
        <button onclick="closeModal()" class="text-ink-secondary hover:text-ink-primary p-1.5 rounded-lg bg-white border border-canvas-border hover:bg-canvas-subtle transition">
          <i data-lucide="x" class="w-5 h-5"></i>
        </button>
      </div>

      <!-- Modal Body -->
      <div class="p-6 overflow-y-auto space-y-6 text-sm text-ink-secondary">
        
        <!-- Curation & Intent -->
        <div id="modalCurationBox" class="p-4 rounded-xl border border-canvas-border bg-canvas-subtle space-y-1.5">
          <div class="flex items-center justify-between">
            <h4 class="text-xs font-bold uppercase tracking-wider text-ink-primary flex items-center gap-1.5">
              <i data-lucide="compass" class="w-3.5 h-3.5"></i> Discovery Motivation & Target Workflow
            </h4>
            <span class="text-[11px] text-ink-muted font-mono" id="modalCurator"></span>
          </div>
          <p id="modalMotivation" class="text-xs text-ink-primary leading-relaxed font-medium"></p>
          <div class="pt-1.5 flex items-center gap-1.5 text-xs text-ink-secondary">
            <span class="text-ink-muted">🎯 연계 워크플로우:</span>
            <span id="modalWorkflow" class="text-ink-primary font-semibold font-mono"></span>
          </div>
        </div>

        <!-- Claims Assessment (Claims vs Truth) -->
        <div id="modalClaimsBox" class="hidden space-y-3 p-4 rounded-xl border border-amber-200 bg-amber-50/50">
          <h4 class="text-xs font-bold uppercase tracking-wider text-amber-900 flex items-center gap-1.5">
            <i data-lucide="scale" class="w-3.5 h-3.5"></i> Marketing Claims vs Empirical Reality
          </h4>
          <div id="modalClaimsList" class="space-y-2.5"></div>
        </div>

        <!-- Technical Ecosystem Analysis (Standard vs 3rd-party) -->
        <div id="modalTechAnalysisBox" class="hidden space-y-4 p-4 rounded-xl border border-canvas-border bg-canvas-subtle">
          <h4 class="text-xs font-bold uppercase tracking-wider text-ink-primary flex items-center gap-1.5">
            <i data-lucide="cpu" class="w-3.5 h-3.5"></i> Ecosystem Technical Analysis & Architecture
          </h4>
          <div id="modalTechAnalysisContent" class="space-y-3 text-xs"></div>
        </div>

        <!-- Story & Empirical Proof -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="p-4 rounded-xl bg-canvas-subtle border border-canvas-border space-y-2">
            <h4 class="text-xs font-bold uppercase tracking-wider text-ink-primary flex items-center gap-1.5">
              <i data-lucide="eye" class="w-3.5 h-3.5 text-ink-secondary"></i> The Hook & Anatomy
            </h4>
            <p id="modalHook" class="text-xs text-ink-secondary leading-relaxed"></p>
            <p id="modalHype" class="text-xs text-ink-muted leading-relaxed pt-1 border-t border-canvas-border"></p>
          </div>

          <div class="p-4 rounded-xl bg-canvas-subtle border border-canvas-border space-y-2">
            <h4 class="text-xs font-bold uppercase tracking-wider text-ink-primary flex items-center gap-1.5">
              <i data-lucide="wrench" class="w-3.5 h-3.5 text-emerald-700"></i> Hands-on Measured Results
            </h4>
            <div id="modalHandsOnEnv" class="text-xs text-ink-muted font-mono"></div>
            <div id="modalHandsOnMetrics" class="text-xs font-bold text-emerald-800"></div>
            <p id="modalHandsOnDetails" class="text-xs text-ink-secondary leading-relaxed"></p>
          </div>
        </div>

        <!-- Alternatives Matrix -->
        <div class="space-y-3">
          <h4 class="text-xs font-bold uppercase tracking-wider text-ink-primary flex items-center gap-1.5">
            <i data-lucide="git-compare" class="w-3.5 h-3.5 text-ink-secondary"></i> Comparative Alternatives Matrix
          </h4>
          <div class="overflow-x-auto rounded-xl border border-canvas-border">
            <table class="w-full text-left text-xs border-collapse">
              <thead class="bg-canvas-subtle text-ink-secondary font-mono">
                <tr>
                  <th class="p-3 border-b border-canvas-border">Tool / Tech</th>
                  <th class="p-3 border-b border-canvas-border">Tech Stack</th>
                  <th class="p-3 border-b border-canvas-border">Pros</th>
                  <th class="p-3 border-b border-canvas-border">Cons</th>
                  <th class="p-3 border-b border-canvas-border">Best For</th>
                </tr>
              </thead>
              <tbody id="modalAlternativesBody" class="divide-y divide-canvas-border bg-white"></tbody>
            </table>
          </div>
        </div>

        <!-- Primary Sources -->
        <div class="space-y-2.5">
          <h4 class="text-xs font-bold uppercase tracking-wider text-ink-primary flex items-center gap-1.5">
            <i data-lucide="book-open" class="w-3.5 h-3.5 text-ink-secondary"></i> Audited Primary Sources
          </h4>
          <div id="modalSourcesList" class="grid grid-cols-1 sm:grid-cols-2 gap-2.5"></div>
        </div>

      </div>
    </div>
  </div>

  <!-- Toast Notification -->
  <div id="toast" class="fixed bottom-6 right-6 z-50 bg-ink-primary text-white px-4 py-3 rounded-xl shadow-2xl text-xs font-semibold hidden transition-all duration-300 flex items-center gap-2">
    <i data-lucide="check-circle" class="w-4 h-4 text-emerald-400"></i>
    <span id="toastMsg">작업이 완료되었습니다.</span>
  </div>

  <!-- ==================== SCRIPTS ==================== -->
  <script>
    const casesData = {cases_json};
    const inboxData = {inbox_json};
    const adminData = {admin_json};
    const graphData = {graph_json};

    let liveCasesData = casesData;
    let liveInboxData = inboxData;
    let liveNewsData = inboxData.filter(it => it.category_type === 'NEWS');
    let liveAnalysesData = [];

    let currentLang = 'KO';
    let currentView = 'portfolio';
    let currentMode = 'ALL';
    let currentDomain = 'ALL';
    let currentSort = 'date-desc';
    let searchQuery = '';

    let currentInboxSource = 'ALL';
    let inboxSearchQuery = '';
    let isFamilyGroupingActive = true;
    let currentGraphType = 'ALL';
    let simulationRef = null;
    let linkSelection = null;
    let nodeSelection = null;

    const queuedItemIds = new Set(JSON.parse(localStorage.getItem('queued_factchecks') || '[]'));

    // Domain Color Palette for Graph
    const domainColorMap = {{
      'cluster_frontend_design_system': '#0f172a',
      'cluster_web_scraping': '#0284c7',
      'cluster_doc_parsing': '#2563eb',
      'cluster_agent_framework': '#7c3aed',
      'cluster_local_llm': '#059669',
      'cluster_3d_graphics': '#db2777',
      'cluster_browser_engine': '#d97706',
      'general': '#64748b'
    }};

    // ================= VIEW SWITCHER =================
    function switchView(view) {{
      currentView = view;
      ['portfolio', 'news', 'graph', 'roi', 'inbox'].forEach(v => {{
        const el = document.getElementById(v + 'View');
        const btn = document.getElementById('tab' + v.charAt(0).toUpperCase() + v.slice(1) + 'Btn');
        const mBtn = document.getElementById('mTab' + v.charAt(0).toUpperCase() + v.slice(1) + 'Btn');
        
        if (el) el.classList.toggle('hidden', v !== view);
        
        if (btn) {{
          if (v === view) {{
            btn.className = 'nav-tab active flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-white bg-ink-primary transition';
          }} else {{
            btn.className = 'nav-tab flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-ink-secondary hover:text-ink-primary transition';
          }}
        }}

        if (mBtn) {{
          if (v === view) {{
            mBtn.className = 'mobile-nav-tab active shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-ink-primary transition';
          }} else {{
            mBtn.className = 'mobile-nav-tab shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium text-ink-secondary hover:text-ink-primary bg-white border border-canvas-border transition';
          }}
        }}
      }});

      if (view === 'graph' && !simulationRef) {{
        initCitationGraph();
      }}
      lucide.createIcons();
    }}

    function setLanguage(lang) {{
      currentLang = lang;
      document.getElementById('langKoBtn').className = lang === 'KO' ? 'px-2 py-0.5 rounded bg-ink-primary text-white text-[10px] sm:text-[11px]' : 'px-2 py-0.5 rounded text-ink-secondary hover:text-ink-primary text-[10px] sm:text-[11px]';
      document.getElementById('langEnBtn').className = lang === 'EN' ? 'px-2 py-0.5 rounded bg-ink-primary text-white text-[10px] sm:text-[11px]' : 'px-2 py-0.5 rounded text-ink-secondary hover:text-ink-primary text-[10px] sm:text-[11px]';
      renderCards();
      renderNews();
      renderInbox();
    }}

    // ================= REAL-TIME DB SYNC =================
    async function syncFromNeonLiveDB() {{
      try {{
        // 1. Fetch Verified Portfolios
        const resPort = await fetch('/api/portfolios');
        if (resPort.ok) {{
          const data = await resPort.json();
          if (data.success && data.portfolios && data.portfolios.length > 0) {{
            liveCasesData = data.portfolios;
            liveAnalysesData = data.technical_analyses || [];
            console.log(`[Neon DB] Synced ${{data.portfolios.length}} live verified cases`);
            
            const badge = document.getElementById('dbLiveBadge');
            if (badge) {{
              badge.innerHTML = `
                <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
                  <span class="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse"></span> Neon DB Live (${{data.portfolios.length}})
                </span>
              `;
            }}
            renderCards();
          }}
        }}

        // 2. Fetch Inbox Candidates
        const resInbox = await fetch('/api/queue?all=true');
        if (resInbox.ok) {{
          const inData = await resInbox.json();
          if (inData.success && inData.items && inData.items.length > 0) {{
            liveInboxData = inData.items;
            renderInbox();
          }}
        }}

        // 3. Fetch AI News
        const resNews = await fetch('/api/queue?type=NEWS');
        if (resNews.ok) {{
          const newsData = await resNews.json();
          if (newsData.success && newsData.news && newsData.news.length > 0) {{
            liveNewsData = newsData.news;
            renderNews();
          }}
        }}

      }} catch (err) {{
        console.warn("[Neon DB] Fetch notice:", err);
      }}
    }}

    // ================= FILTER & SORT HANDLERS =================
    function setModeFilter(mode) {{
      currentMode = mode;
      document.querySelectorAll('.segment-btn').forEach(btn => btn.classList.remove('active'));
      if (mode === 'ALL') document.getElementById('modeBtnAll').classList.add('active');
      if (mode === 'USER_CURATED') document.getElementById('modeBtnUser').classList.add('active');
      if (mode === 'AUTO_HARVESTED') document.getElementById('modeBtnAuto').classList.add('active');
      renderCards();
    }}

    function setDomainFilter(dom) {{
      currentDomain = dom;
      document.querySelectorAll('.tag-pill').forEach(btn => {{
        if (btn.dataset.domain === dom) {{
          btn.classList.add('active');
        }} else {{
          btn.classList.remove('active');
        }}
      }});
      renderCards();
    }}

    function changeSort(val) {{
      currentSort = val;
      renderCards();
    }}

    function clearSearch() {{
      const input = document.getElementById('searchInput');
      input.value = '';
      searchQuery = '';
      document.getElementById('clearSearchBtn').classList.add('hidden');
      renderCards();
    }}

    document.getElementById('searchInput').addEventListener('input', (e) => {{
      searchQuery = e.target.value;
      document.getElementById('clearSearchBtn').classList.toggle('hidden', !searchQuery);
      renderCards();
    }});

    // ================= RENDER FACT-CHECK CARDS =================
    function renderCards() {{
      const grid = document.getElementById('cardsGrid');
      const heroContainer = document.getElementById('featuredHeroContainer');
      grid.innerHTML = '';
      heroContainer.innerHTML = '';

      // Update Counts
      const countUser = liveCasesData.filter(c => (c.curation?.discovery_mode || 'USER_CURATED') === 'USER_CURATED').length;
      const countAuto = liveCasesData.filter(c => (c.curation?.discovery_mode || 'USER_CURATED') === 'AUTO_HARVESTED').length;
      document.getElementById('badgeCountAll').innerText = liveCasesData.length;
      document.getElementById('badgeCountUser').innerText = countUser;
      document.getElementById('badgeCountAuto').innerText = countAuto;
      document.getElementById('headerVerifiedCount').innerText = liveCasesData.length;
      const mCount = document.getElementById('mHeaderVerifiedCount');
      if (mCount) mCount.innerText = liveCasesData.length;

      const filtered = liveCasesData.filter(c => {{
        const mode = c.curation ? c.curation.discovery_mode : 'USER_CURATED';
        const matchesMode = currentMode === 'ALL' || mode === currentMode;
        
        const cat = (c.category || '').toLowerCase();
        const cluster = (c.clustering?.cluster_id || '').toLowerCase();
        let matchesDomain = true;
        if (currentDomain === 'frontend') matchesDomain = cat.includes('design') || cat.includes('frontend') || cluster.includes('design');
        else if (currentDomain === 'agent') matchesDomain = cat.includes('agent') || cluster.includes('agent');
        else if (currentDomain === 'scraping') matchesDomain = cat.includes('scraping') || cat.includes('browser') || cluster.includes('scraping');
        else if (currentDomain === 'doc') matchesDomain = cat.includes('doc') || cat.includes('ocr') || cluster.includes('doc');
        else if (currentDomain === '3d') matchesDomain = cat.includes('3d') || cat.includes('graphics') || cluster.includes('3d');
        else if (currentDomain === 'rust') matchesDomain = (c.title + ' ' + (c.clustering?.cluster_name || '')).toLowerCase().includes('rust');

        const story = c.portfolio_story || {{}};
        const text = (c.title + ' ' + (c.category || '') + ' ' + (story.the_hook || '') + ' ' + (c.curation?.personal_motivation || '')).toLowerCase();
        const matchesSearch = text.includes(searchQuery.toLowerCase());

        return matchesMode && matchesDomain && matchesSearch;
      }});

      // Dynamic Sorting Engine
      filtered.sort((a, b) => {{
        if (currentSort === 'date-desc') {{
          return (b.investigation_date || '').localeCompare(a.investigation_date || '');
        }} else if (currentSort === 'date-asc') {{
          return (a.investigation_date || '').localeCompare(b.investigation_date || '');
        }} else if (currentSort === 'score-desc') {{
          return (b.confidence_score || 0) - (a.confidence_score || 0);
        }} else if (currentSort === 'title-asc') {{
          return (a.title || '').localeCompare(b.title || '');
        }}
        return 0;
      }});

      document.getElementById('resultsCountLabel').innerText = `총 ${{filtered.length}}건 표시 (전체 ${{liveCasesData.length}}건 중)`;

      if (filtered.length === 0) {{
        grid.innerHTML = `<div class="col-span-full py-16 text-center text-ink-muted font-medium">검색 및 필터 조건에 일치하는 기술 검증 보고서가 없습니다.</div>`;
        return;
      }}

      // Featured Hero Case (First Top Item when in Default Sort & No Search)
      if (currentSort === 'date-desc' && !searchQuery && currentDomain === 'ALL' && filtered.length > 0) {{
        const hero = filtered[0];
        const heroStory = hero.portfolio_story || {{}};
        const heroCuration = hero.curation || {{}};
        const isUserMode = heroCuration.discovery_mode === 'USER_CURATED';
        const isTrue = hero.verdict === 'VERIFIED_TRUE';

        heroContainer.innerHTML = `
          <div class="hero-card p-6 sm:p-8 cursor-pointer hover:border-black transition group" onclick="openModal(liveCasesData.find(x => x.case_id === '${{hero.case_id}}'))">
            <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
              <div class="space-y-3.5 max-w-3xl">
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold ${{isUserMode ? 'bg-ink-primary text-white' : 'bg-canvas-subtle text-ink-primary border border-canvas-border'}}">
                    FEATURED DOSSIER
                  </span>
                  <span class="text-xs text-ink-muted font-mono">${{hero.investigation_date}}</span>
                  <span class="px-2 py-0.5 rounded text-[11px] font-bold font-mono ${{isTrue ? 'verdict-true' : 'verdict-half'}}">
                    ● ${{hero.verdict.replace('_', ' ')}}
                  </span>
                </div>

                <h3 class="text-xl sm:text-2xl font-bold text-ink-primary font-serif leading-snug group-hover:underline">
                  ${{hero.title}}
                </h3>

                <p class="text-xs sm:text-sm text-ink-secondary leading-relaxed">
                  ${{heroCuration.personal_motivation || heroStory.the_hook}}
                </p>
              </div>

              <div class="flex lg:flex-col items-center lg:items-end justify-between gap-3 shrink-0 pt-4 lg:pt-0 border-t lg:border-t-0 border-canvas-border">
                <div class="text-right">
                  <div class="text-[11px] font-mono text-ink-muted">CONFIDENCE SCORE</div>
                  <div class="text-2xl font-black font-mono text-emerald-700">${{(hero.confidence_score || 95.0).toFixed(1)}}%</div>
                </div>
                <button class="px-4 py-2 rounded-xl bg-ink-primary text-white text-xs font-bold group-hover:bg-black transition flex items-center gap-1.5 shadow-sm">
                  심층 보고서 열람 <i data-lucide="arrow-up-right" class="w-4 h-4"></i>
                </button>
              </div>
            </div>
          </div>
        `;
      }}

      // Render Editorial Cards
      const itemsToRender = (currentSort === 'date-desc' && !searchQuery && currentDomain === 'ALL') ? filtered.slice(1) : filtered;

      itemsToRender.forEach((c, idx) => {{
        const story = c.portfolio_story || {{}};
        const curation = c.curation || {{ discovery_mode: 'USER_CURATED' }};
        const isUserMode = curation.discovery_mode === 'USER_CURATED';
        const invDate = c.investigation_date || '2026-09-01';
        const confScore = c.confidence_score || 95.0;
        const isVerifiedTrue = c.verdict === 'VERIFIED_TRUE';
        const isHalfTrue = c.verdict.includes('HALF');

        const card = document.createElement('div');
        card.className = 'editorial-card p-6 flex flex-col justify-between cursor-pointer space-y-4 group';
        card.onclick = () => openModal(c);

        card.innerHTML = `
          <div class="space-y-3">
            <!-- Card Header -->
            <div class="flex items-center justify-between text-xs gap-1.5 flex-wrap">
              <div class="flex items-center gap-2">
                <span class="text-xs font-mono font-bold text-ink-muted">#${{String(idx + 1).padStart(2, '0')}}</span>
                <span class="px-2 py-0.5 rounded text-[11px] font-bold font-mono ${{isUserMode ? 'bg-canvas-subtle text-ink-primary border border-canvas-border' : 'bg-canvas-subtle text-ink-secondary'}}">
                  ${{isUserMode ? 'USER-CURATED' : 'AUTO-TREND'}}
                </span>
                <span class="text-ink-muted text-[11px] font-mono">${{invDate}}</span>
              </div>

              <!-- Verdict Badge -->
              <span class="px-2 py-0.5 rounded text-[11px] font-bold font-mono flex items-center gap-1.5 ${{isVerifiedTrue ? 'verdict-true' : (isHalfTrue ? 'verdict-half' : 'verdict-gamed')}}">
                ● ${{c.verdict.replace('_', ' ')}}
              </span>
            </div>

            <!-- Title & Domain -->
            <div class="space-y-1">
              <span class="text-[11px] text-ink-muted font-mono font-semibold uppercase tracking-wider">${{c.category || 'Tech General'}}</span>
              <h3 class="font-bold text-base text-ink-primary group-hover:text-black transition leading-snug font-serif">
                ${{c.title}}
              </h3>
            </div>

            <!-- Discovery Motivation Quote -->
            <div class="bg-canvas-subtle p-3 rounded-lg border border-canvas-border text-xs text-ink-secondary leading-relaxed line-clamp-2">
              ${{curation.personal_motivation || story.the_hook || '공학적 실체와 비용 분석 검증 완료.'}}
            </div>
          </div>

          <!-- Card Footer -->
          <div class="pt-3 border-t border-canvas-border flex items-center justify-between text-xs">
            <div class="flex items-center gap-2">
              <span class="text-emerald-700 font-mono font-bold text-[11px]">신뢰도 ${{confScore.toFixed(1)}}%</span>
              <span class="text-canvas-border">•</span>
              <span class="text-ink-muted text-[11px] font-mono">${{(c.sources || []).length}}개 1차 출처</span>
            </div>

            <span class="text-ink-primary group-hover:translate-x-0.5 transition font-semibold text-xs flex items-center gap-1">
              보고서 <i data-lucide="arrow-right" class="w-3.5 h-3.5"></i>
            </span>
          </div>
        `;
        grid.appendChild(card);
      }});

      lucide.createIcons();
    }}

    // ================= MODAL HANDLER =================
    function openModal(c) {{
      const modal = document.getElementById('detailModal');
      const story = c.portfolio_story || {{}};
      const handsOn = story.hands_on_log || {{}};
      const curation = c.curation || {{}};
      const clustering = c.clustering || {{}};

      document.getElementById('modalTitle').innerText = c.title;
      document.getElementById('modalModeBadge').innerText = curation.discovery_mode === 'USER_CURATED' ? '직접 큐레이션' : '자동 트렌드';
      document.getElementById('modalModeBadge').className = curation.discovery_mode === 'USER_CURATED' ? 'text-xs px-2.5 py-0.5 rounded-md font-semibold bg-canvas-subtle text-ink-primary border border-canvas-border' : 'text-xs px-2.5 py-0.5 rounded-md font-semibold bg-canvas-subtle text-ink-secondary';
      
      document.getElementById('modalClusterBadge').innerText = clustering.cluster_name || c.category || 'Tech';
      document.getElementById('modalVerdictBadge').innerText = c.verdict;
      document.getElementById('modalVerdictBadge').className = c.verdict === 'VERIFIED_TRUE' ? 'text-xs px-2.5 py-0.5 rounded-md font-semibold verdict-true' : 'text-xs px-2.5 py-0.5 rounded-md font-semibold verdict-half';
      document.getElementById('modalStageBadge').innerText = handsOn.status === 'ACTIVE_DEVELOPED' ? '실제 개발 적용' : '기술 조사 완료';

      document.getElementById('modalCurator').innerText = '발굴자: ' + (curation.curator || 'Anyong Cheong');
      document.getElementById('modalMotivation').innerText = curation.personal_motivation || story.the_hook || '';
      document.getElementById('modalWorkflow').innerText = curation.target_workflow || '범용 AI 기술 스택 연계';

      document.getElementById('modalHook').innerText = story.the_hook || '';
      document.getElementById('modalHype').innerText = story.marketing_hype_anatomy ? ('과장 마케팅 해부: ' + story.marketing_hype_anatomy) : '';
      
      document.getElementById('modalHandsOnEnv').innerText = handsOn.test_environment ? ('환경: ' + handsOn.test_environment) : '';
      document.getElementById('modalHandsOnMetrics').innerText = handsOn.measured_results ? ('실측: ' + handsOn.measured_results) : '';
      document.getElementById('modalHandsOnDetails').innerText = handsOn.details || '실측 벤치마크 완료.';

      // Claims vs Reality
      const claimsBox = document.getElementById('modalClaimsBox');
      const claimsList = document.getElementById('modalClaimsList');
      if (c.claims_assessment && c.claims_assessment.length > 0) {{
        claimsBox.classList.remove('hidden');
        claimsList.innerHTML = c.claims_assessment.map(cl => `
          <div class="p-3 rounded-lg bg-white border border-amber-200 text-xs space-y-1">
            <div class="flex items-center justify-between font-mono text-[11px]">
              <span class="text-ink-primary font-bold">Claim: "${{cl.statement || cl.claim_title || ''}}"</span>
              <span class="px-2 py-0.2 rounded font-bold ${{cl.status === 'VERIFIED_TRUE' ? 'text-emerald-700' : 'text-amber-800'}}">${{cl.status || cl.claim_verdict || 'VERIFIED'}}</span>
            </div>
            <div class="text-ink-secondary font-medium">검증 팩트: ${{cl.fact_checked_truth || cl.verification_evidence || ''}}</div>
          </div>
        `).join('');
      }} else {{
        claimsBox.classList.add('hidden');
      }}

      // Alternatives Table
      const altBody = document.getElementById('modalAlternativesBody');
      const alts = clustering.alternatives || [];
      if (alts.length > 0) {{
        altBody.innerHTML = alts.map(a => `
          <tr>
            <td class="p-3 font-bold text-ink-primary">${{a.name || a.tool_name || ''}}</td>
            <td class="p-3 font-mono text-ink-secondary text-[11px]">${{a.tech_stack || '-'}}</td>
            <td class="p-3 text-emerald-700">${{a.pros || '-'}}</td>
            <td class="p-3 text-rose-700">${{a.cons || '-'}}</td>
            <td class="p-3 text-ink-secondary font-medium">${{a.best_for || '-'}}</td>
          </tr>
        `).join('');
      }} else {{
        altBody.innerHTML = `<tr><td colspan="5" class="p-4 text-center text-ink-muted">등록된 대체 기술 비교 데이터가 없습니다.</td></tr>`;
      }}

      // Sources
      const sourcesList = document.getElementById('modalSourcesList');
      const sources = c.sources || [];
      sourcesList.innerHTML = sources.map(s => `
        <a href="${{s.url}}" target="_blank" class="p-2.5 rounded-xl bg-canvas-subtle border border-canvas-border hover:border-ink-primary flex items-center justify-between text-xs text-ink-secondary hover:text-ink-primary transition">
          <div class="space-y-0.5">
            <span class="text-[10px] font-mono text-ink-primary uppercase font-bold">${{s.tier || 'Tier 1'}} • ${{s.type || 'Repository'}}</span>
            <div class="font-medium truncate max-w-[240px] text-ink-primary">${{s.name || s.title || '출처 링크'}}</div>
          </div>
          <i data-lucide="external-link" class="w-3.5 h-3.5 text-ink-muted shrink-0"></i>
        </a>
      `).join('');

      modal.classList.remove('hidden');
      lucide.createIcons();
    }}

    function closeModal() {{
      document.getElementById('detailModal').classList.add('hidden');
    }}

    // ================= NEWS VIEW =================
    function renderNews() {{
      const grid = document.getElementById('newsGrid');
      grid.innerHTML = '';

      const newsItems = liveNewsData || [];
      if (newsItems.length === 0) {{
        grid.innerHTML = `<div class="col-span-full py-16 text-center text-ink-muted font-medium">수집된 AI 뉴스가 없습니다.</div>`;
        return;
      }}

      newsItems.forEach(it => {{
        const card = document.createElement('div');
        card.className = 'editorial-card p-5 flex flex-col justify-between space-y-4';

        const displayTitle = currentLang === 'KO' && it.title_ko ? it.title_ko : it.title;
        const displayDesc = currentLang === 'KO' && it.description_ko ? it.description_ko : (it.description || '');

        card.innerHTML = `
          <div class="space-y-2.5">
            <div class="flex items-center justify-between text-xs font-mono">
              <span class="px-2 py-0.5 rounded bg-canvas-subtle text-ink-primary font-bold border border-canvas-border text-[11px]">
                ${{it.source_platform || 'Tech News'}}
              </span>
              <span class="text-ink-muted text-[11px]">${{it.viral_metric || ''}}</span>
            </div>

            <h3 class="font-bold text-sm text-ink-primary hover:text-black transition leading-snug font-serif">
              ${{displayTitle}}
            </h3>

            <p class="text-xs text-ink-secondary leading-relaxed line-clamp-3">
              ${{displayDesc}}
            </p>
          </div>

          <div class="pt-3 border-t border-canvas-border flex items-center justify-between text-xs">
            <span class="text-ink-muted text-[11px] font-mono">${{it.harvested_date || '2026-09-02'}}</span>
            <a href="${{it.source_url}}" target="_blank" class="text-ink-primary hover:underline font-semibold flex items-center gap-1">
              기사 원문 <i data-lucide="external-link" class="w-3 h-3"></i>
            </a>
          </div>
        `;
        grid.appendChild(card);
      }});

      lucide.createIcons();
    }}

    // ================= INBOX VIEW =================
    function toggleFamilyGrouping() {{
      isFamilyGroupingActive = !isFamilyGroupingActive;
      const btn = document.getElementById('groupByFamilyBtn');
      const text = document.getElementById('groupByFamilyText');
      if (isFamilyGroupingActive) {{
        btn.className = 'flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold bg-ink-primary text-white transition shrink-0';
        text.innerText = '패밀리 묶음 (ON)';
      }} else {{
        btn.className = 'flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold bg-white text-ink-primary border border-canvas-border hover:bg-canvas-subtle transition shrink-0';
        text.innerText = '패밀리 묶음 (OFF)';
      }}
      renderInbox();
    }}

    function setInboxSourceFilter(src) {{
      currentInboxSource = src;
      const sel = document.getElementById('inboxSourceSelect');
      if (sel && sel.value !== src) sel.value = src;
      renderInbox();
    }}

    document.getElementById('inboxSearchInput').addEventListener('input', (e) => {{
      inboxSearchQuery = e.target.value;
      renderInbox();
    }});

    function renderInbox() {{
      const grid = document.getElementById('inboxGrid');
      grid.innerHTML = '';

      const filtered = liveInboxData.filter(item => {{
        const isNotNews = item.category_type !== 'NEWS';
        const matchesSrc = currentInboxSource === 'ALL' || (item.source_platform && item.source_platform.includes(currentInboxSource));
        const text = (item.title + ' ' + (item.title_ko || '') + ' ' + (item.description || '') + ' ' + (item.model_family || '') + ' ' + (item.variant_role || '')).toLowerCase();
        const matchesSearch = text.includes(inboxSearchQuery.toLowerCase());
        return isNotNews && matchesSrc && matchesSearch;
      }});

      if (filtered.length === 0) {{
        grid.innerHTML = `<div class="col-span-full py-16 text-center text-ink-muted font-medium">수집된 인박스 후보가 없습니다.</div>`;
        return;
      }}

      if (isFamilyGroupingActive) {{
        const groups = {{}};
        filtered.forEach(it => {{
          const fam = it.model_family || '독립 모델 (Standalone / Novel)';
          if (!groups[fam]) groups[fam] = [];
          groups[fam].push(it);
        }});

        const sortedFamNames = Object.keys(groups).sort((a, b) => {{
          if (a.includes('독립') && !b.includes('독립')) return 1;
          if (!a.includes('독립') && b.includes('독립')) return -1;
          return groups[b].length - groups[a].length;
        }});

        sortedFamNames.forEach(famName => {{
          const items = groups[famName];
          const groupCard = document.createElement('div');
          groupCard.className = 'col-span-full editorial-card p-6 border-canvas-border space-y-4 shadow-sm';

          let subItemsHtml = '';
          items.forEach(it => {{
            const isQueued = queuedItemIds.has(it.inbox_id);
            const displayTitle = currentLang === 'KO' && it.title_ko ? it.title_ko : it.title;
            const roleBadge = it.variant_role || 'Standard';

            subItemsHtml += `
              <div class="bg-canvas-subtle p-4 rounded-xl border border-canvas-border flex flex-col justify-between space-y-3 hover:border-ink-primary transition">
                <div class="space-y-2">
                  <div class="flex items-center justify-between text-[11px] font-mono">
                    <span class="text-ink-primary font-bold">${{it.source_platform || 'Hub'}}</span>
                    <span class="text-ink-muted">${{it.viral_metric || ''}}</span>
                  </div>
                  
                  <div class="px-2 py-0.5 rounded text-[10px] font-semibold font-mono bg-white text-ink-primary border border-canvas-border inline-block">
                    ${{roleBadge}}
                  </div>

                  <h4 class="font-bold text-xs text-ink-primary line-clamp-2 leading-relaxed">${{displayTitle}}</h4>
                  
                  <div class="text-[10px] text-ink-muted font-mono">
                    제작: <span class="text-ink-primary font-semibold">${{it.creator || 'Community'}}</span>
                  </div>
                </div>

                <div class="pt-2.5 border-t border-canvas-border flex items-center justify-between gap-2">
                  <a href="${{it.source_url}}" target="_blank" class="text-[11px] text-ink-secondary hover:text-ink-primary flex items-center gap-0.5 shrink-0">
                    원문 <i data-lucide="external-link" class="w-2.5 h-2.5"></i>
                  </a>
                  
                  <button onclick="toggleQueueItem('${{it.inbox_id}}', '${{displayTitle.replace(/'/g, "")}}')" 
                          class="px-2.5 py-1 rounded-lg text-[10px] font-bold transition flex items-center gap-1 ${{isQueued ? 'bg-emerald-700 text-white font-black' : 'bg-white text-ink-primary hover:bg-ink-primary hover:text-white border border-canvas-border'}}">
                    <i data-lucide="${{isQueued ? 'check' : 'zap'}}" class="w-3 h-3"></i>
                    ${{isQueued ? '대기열 등록됨' : '분석 큐 담기'}}
                  </button>
                </div>
              </div>
            `;
          }});

          groupCard.innerHTML = `
            <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-canvas-border gap-3">
              <div class="flex items-center gap-2.5 flex-wrap">
                <span class="px-2.5 py-0.5 rounded-md bg-canvas-subtle text-ink-primary text-xs font-mono font-bold border border-canvas-border flex items-center gap-1">
                  <i data-lucide="layers" class="w-3.5 h-3.5"></i> Model Family
                </span>
                <h3 class="text-base font-bold text-ink-primary font-serif">${{famName}}</h3>
                <span class="text-xs px-2 py-0.5 rounded bg-white text-ink-secondary border border-canvas-border font-mono font-bold">${{items.length}}개 파생 모델</span>
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
              ${{subItemsHtml}}
            </div>
          `;
          grid.appendChild(groupCard);
        }});
      }}

      lucide.createIcons();
    }}

    async function toggleQueueItem(inboxId, title) {{
      const isCurrentlyQueued = queuedItemIds.has(inboxId);
      const action = isCurrentlyQueued ? 'unqueue' : 'queue';
      
      if (isCurrentlyQueued) {{
        queuedItemIds.delete(inboxId);
      }} else {{
        queuedItemIds.add(inboxId);
      }}
      localStorage.setItem('queued_factchecks', JSON.stringify(Array.from(queuedItemIds)));
      renderInbox();

      try {{
        const res = await fetch('/api/queue', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ inbox_id: inboxId, action: action }})
        }});
        if (res.ok) {{
          showToast(action === 'queue' ? `[${{title}}] 항목이 Neon Postgres DB 실시간 큐에 등록되었습니다!` : `대기열에서 제외되었습니다.`);
          return;
        }}
      }} catch (err) {{}}

      showToast(isCurrentlyQueued ? `대기열에서 제외되었습니다.` : `[${{title}}] 항목이 대기열에 등록되었습니다.`);
    }}

    function showToast(msg) {{
      const toast = document.getElementById('toast');
      document.getElementById('toastMsg').innerText = msg;
      toast.classList.remove('hidden');
      setTimeout(() => toast.classList.add('hidden'), 3500);
    }}

    // ================= ROI CALCULATORS =================
    function updateRoiCalculators() {{
      const pages = parseInt(document.getElementById('scrapingPagesSlider').value);
      document.getElementById('scrapingPagesDisplay').innerText = pages.toLocaleString() + ' 페이지/월';

      const firecrawlCost = Math.round(pages * 0.0025);
      const watercrawlCost = Math.round(38 + (pages / 1000000) * 15);
      const scrapSavings = Math.max(0, firecrawlCost - watercrawlCost);
      const scrapSavingsPercent = Math.round((scrapSavings / firecrawlCost) * 100);

      document.getElementById('costFirecrawl').innerText = '$' + firecrawlCost.toLocaleString() + ' /월';
      document.getElementById('costWatercrawl').innerText = '$' + watercrawlCost.toLocaleString() + ' /월';
      document.getElementById('scrapingSavings').innerText = '+$' + scrapSavings.toLocaleString() + ' /월 (' + scrapSavingsPercent + '% 절감)';

      const tokens = parseInt(document.getElementById('agentTokensSlider').value);
      const mTokens = tokens / 1000000;
      document.getElementById('agentTokensDisplay').innerText = (mTokens >= 1000 ? (mTokens/1000).toFixed(1) + 'B' : mTokens.toFixed(0) + 'M') + ' 토큰/월';

      const claudeCost = Math.round(mTokens * 6.0);
      const praxistCost = Math.round((mTokens / 12) * 6.0);
      const agentSavings = Math.max(0, claudeCost - praxistCost);
      const agentSavingsPercent = Math.round((agentSavings / claudeCost) * 100);

      document.getElementById('costClaude').innerText = '$' + claudeCost.toLocaleString() + ' /월';
      document.getElementById('costPraxist').innerText = '$' + praxistCost.toLocaleString() + ' /월';
      document.getElementById('agentSavings').innerText = '+$' + agentSavings.toLocaleString() + ' /월 (' + agentSavingsPercent + '% 절감)';
    }}

    document.getElementById('scrapingPagesSlider').addEventListener('input', updateRoiCalculators);
    document.getElementById('agentTokensSlider').addEventListener('input', updateRoiCalculators);

    // ================= CITATION GRAPH =================
    function initCitationGraph() {{
      const svg = d3.select("#techGraphSvg");
      const container = document.getElementById("graphView");
      const width = container.clientWidth || 1100;
      const height = 640;
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
        .attr("stroke", "rgba(0, 0, 0, 0.12)")
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
        if (d.group === "language") return "#b45309";
        if (d.group === "technology") return "#047857";
        if (d.group === "organization") return "#4338ca";
        if (d.group === "person") return "#be185d";
        if (d.group === "paper") return "#c2410c";
        return domainColorMap[d.group] || "#111827";
      }}

      nodeSelection = nodeGroup.append("circle")
        .attr("r", d => d.val || 15)
        .attr("fill", d => getNodeColor(d))
        .attr("stroke", "#ffffff")
        .attr("stroke-width", 2.5);

      nodeGroup.append("text")
        .text(d => d.name || d.id)
        .attr("x", 0)
        .attr("y", d => (d.val || 15) + 14)
        .attr("text-anchor", "middle")
        .attr("fill", "#111827")
        .attr("font-size", "11px")
        .attr("font-family", "Geist, sans-serif")
        .attr("font-weight", "600");

      simulationRef.on("tick", () => {{
        linkSelection
          .attr("x1", d => d.source.x)
          .attr("y1", d => d.source.y)
          .attr("x2", d => d.target.x)
          .attr("y2", d => d.target.y);

        nodeGroup.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
      }});

      function dragstarted(event, d) {{
        if (!event.active) simulationRef.alphaTarget(0.3).restart();
        d.fx = d.x; d.fy = d.y;
      }}
      function dragged(event, d) {{
        d.fx = event.x; d.fy = event.y;
      }}
      function dragended(event, d) {{
        if (!event.active) simulationRef.alphaTarget(0);
        d.fx = null; d.fy = null;
      }}
    }}

    function filterGraphGroup(group) {{
      currentGraphType = group;
      document.querySelectorAll('.graph-group-btn').forEach(btn => {{
        if (btn.dataset.group === group) {{
          btn.classList.add('active', 'bg-ink-primary', 'text-white');
        }} else {{
          btn.classList.remove('active', 'bg-ink-primary', 'text-white');
        }}
      }});

      if (nodeSelection) {{
        nodeSelection.attr("opacity", d => (group === 'ALL' || d.group === group) ? 0.95 : 0.08);
      }}
      if (linkSelection) {{
        linkSelection.attr("opacity", l => {{
          if (group === 'ALL') return 0.4;
          const s = typeof l.source === 'object' ? l.source : graphData.nodes.find(n => n.id === l.source);
          const t = typeof l.target === 'object' ? l.target : graphData.nodes.find(n => n.id === l.target);
          return (s && s.group === group) || (t && t.group === group) ? 0.8 : 0.04;
        }});
      }}
    }}

    // ================= INITIALIZATION =================
    window.addEventListener('DOMContentLoaded', () => {{
      renderCards();
      renderNews();
      renderInbox();
      syncFromNeonLiveDB();
      lucide.createIcons();
    }});
  </script>
</body>
</html>
"""

if __name__ == "__main__":
    build_dashboard()
