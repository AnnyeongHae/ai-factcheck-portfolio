#!/usr/bin/env python3
"""
Universal AI Citation & Tech Lineage Knowledge Hub (v20.0 - 18 Full Dossiers & Auto-Promotion Criteria)
- 18 Verified Fact-Check Dossiers: Concat added as #18 with comprehensive Tauri/Rust/Whisper benchmark.
- Autonomous Promotion Criteria Guide Box in Harvest Inbox (GitHub ★>500, HN 🔥>150, HF ❤️>100, ArXiv CS.AI).
- Dynamic Metric Upsert for live GitHub Stars / Likes / HN Points updates.
- 4 Clean Core Tabs (Fact-Checks, AI News, Citation Graph, Harvest Inbox).
- Native CJK Font Stack (Noto Sans SC, Pretendard, Geist/Inter).
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
        {"name": "Hacker News Top & Best", "url": "https://hacker-news.firebaseio.com/v0/topstories.json", "type": "AI/Engineering Discussions", "auth": "Unauthenticated (Free)"},
        {"name": "ArXiv Preprint API", "url": "http://export.arxiv.org/api/query?search_query=cat:cs.AI", "type": "1차 연구 논문", "auth": "Unauthenticated (Free)"}
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

    print(f"[+] Successfully built Full 18 Dossiers Dashboard v20.0 at:")
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
  
  <!-- Dedicated Native Fonts for Korean, Chinese, and English -->
  <link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css" />
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com">
  <link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&family=Noto+Sans+SC:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/lucide@latest"></script>
  <script src="https://d3js.org/d3.v7.min.js"></script>

  <script>
    tailwind.config = {{
      theme: {{
        extend: {{
          fontFamily: {{
            sans: ['Pretendard', 'Noto Sans SC', 'Geist', '-apple-system', 'BlinkMacSystemFont', 'system-ui', 'sans-serif'],
            mono: ['JetBrains Mono', 'monospace'],
          }},
          colors: {{
            surface: {{
              canvas: '#f8f9fa',
              subtle: '#f1f3f5',
              card: '#ffffff',
              border: '#e9ecef',
              borderHover: '#ced4da',
            }},
            ink: {{
              primary: '#111827',
              secondary: '#374151',
              muted: '#6b7280',
              faint: '#9ca3af',
            }}
          }}
        }}
      }}
    }}
  </script>

  <style>
    body {{
      font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
      background-color: #f8f9fa;
      color: #111827;
      letter-spacing: -0.012em;
    }}

    .bg-clean-grid {{
      background-image: radial-gradient(#d1d5db 1px, transparent 1px);
      background-size: 24px 24px;
    }}

    .executive-card {{
      background: #ffffff;
      border: 1px solid #e5e7eb;
      border-radius: 14px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 4px 12px -2px rgba(0, 0, 0, 0.03);
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }}
    .executive-card:hover {{
      border-color: #111827;
      box-shadow: 0 8px 24px -4px rgba(0, 0, 0, 0.08);
      transform: translateY(-2px);
    }}

    .segment-btn {{
      transition: all 0.15s ease;
      color: #4b5563;
    }}
    .segment-btn.active {{
      background: #111827;
      color: #ffffff;
      font-weight: 700;
    }}

    .tag-pill {{
      transition: all 0.15s ease;
    }}
    .tag-pill.active {{
      background: #111827;
      color: #ffffff;
      font-weight: 700;
      border-color: #111827;
    }}

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

    .no-scrollbar::-webkit-scrollbar {{
      display: none;
    }}
    .no-scrollbar {{
      -ms-overflow-style: none;
      scrollbar-width: none;
    }}
  </style>
</head>
<body class="bg-surface-canvas text-ink-primary min-h-screen bg-clean-grid pb-24 antialiased selection:bg-ink-primary selection:text-white">

  <!-- ==================== TOP NAVIGATION HEADER ==================== -->
  <header class="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-surface-border">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-3 sm:gap-4">
      
      <!-- Brand Logo -->
      <div class="flex items-center gap-3 shrink-0">
        <div class="w-9 h-9 rounded-xl bg-ink-primary flex items-center justify-center text-white font-bold text-base shadow-sm">
          <i data-lucide="shield-check" class="w-5 h-5 text-white"></i>
        </div>
        <div>
          <div class="flex items-center gap-2">
            <span class="text-base font-extrabold text-ink-primary tracking-tight" id="headerBrandTitle">FactCheck Hub</span>
            <span class="text-[10px] font-mono px-1.5 py-0.2 rounded bg-surface-subtle border border-surface-border text-ink-muted font-bold">2026</span>
          </div>
          <p class="text-[11px] text-ink-muted hidden sm:block" id="headerBrandSubtitle">AI 바이럴 마케팅 실체 & 공학적 원가 검증 포털</p>
        </div>
      </div>

      <!-- Desktop Navigation Tabs (Clean 4 Core Tabs) -->
      <nav class="hidden md:flex items-center gap-1 bg-surface-subtle p-1 rounded-xl border border-surface-border text-xs font-semibold">
        <button onclick="switchView('portfolio')" id="tabPortfolioBtn" class="nav-tab active flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-white bg-ink-primary transition">
          <i data-lucide="check-circle-2" class="w-3.5 h-3.5"></i>
          <span id="navTabPortfolio">기술 검증</span>
          <span class="text-[10px] font-mono px-1.5 py-0.2 rounded bg-white/20 text-white font-bold" id="headerVerifiedCount">{data['total_cases']}</span>
        </button>
        <button onclick="switchView('news')" id="tabNewsBtn" class="nav-tab flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-ink-secondary hover:text-ink-primary transition">
          <i data-lucide="newspaper" class="w-3.5 h-3.5"></i>
          <span id="navTabNews">AI 뉴스</span>
          <span class="text-[10px] font-mono text-ink-muted" id="headerNewsCount">({data['news_total_count']})</span>
        </button>
        <button onclick="switchView('graph')" id="tabGraphBtn" class="nav-tab flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-ink-secondary hover:text-ink-primary transition">
          <i data-lucide="network" class="w-3.5 h-3.5"></i>
          <span id="navTabGraph">인용 계보망</span>
        </button>
        <button onclick="switchView('inbox')" id="tabInboxBtn" class="nav-tab flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-ink-secondary hover:text-ink-primary transition">
          <i data-lucide="inbox" class="w-3.5 h-3.5"></i>
          <span id="navTabInbox">수집 인박스</span>
          <span class="text-[10px] font-mono text-ink-muted" id="headerInboxCount">({data['inbox_total_count']})</span>
        </button>
      </nav>

      <!-- Right Actions: Live DB Badge & Tri-Lingual (KO / ZH / EN) Toggle -->
      <div class="flex items-center gap-2 sm:gap-2.5 shrink-0">
        <!-- Live Neon DB Badge -->
        <div id="dbLiveBadge">
          <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse"></span>
            <span class="hidden xs:inline sm:inline">Neon DB</span> Live
          </span>
        </div>

        <!-- Language Toggle (KO / ZH / EN) -->
        <div class="bg-surface-subtle p-0.5 sm:p-1 rounded-lg border border-surface-border flex items-center text-xs font-semibold gap-0.5">
          <button onclick="setLanguage('KO')" id="langKoBtn" class="px-2 py-0.5 rounded bg-ink-primary text-white transition text-[10px] sm:text-[11px]">KO</button>
          <button onclick="setLanguage('ZH')" id="langZhBtn" class="px-2 py-0.5 rounded text-ink-secondary hover:text-ink-primary transition text-[10px] sm:text-[11px]">中文</button>
          <button onclick="setLanguage('EN')" id="langEnBtn" class="px-2 py-0.5 rounded text-ink-secondary hover:text-ink-primary transition text-[10px] sm:text-[11px]">EN</button>
        </div>
      </div>

    </div>

    <!-- Mobile Scrollable Sub-Navigation Bar -->
    <div class="flex md:hidden items-center gap-1.5 px-3 py-2 overflow-x-auto no-scrollbar border-t border-surface-border bg-white">
      <button onclick="switchView('portfolio')" id="mTabPortfolioBtn" class="mobile-nav-tab active shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-ink-primary transition">
        <i data-lucide="check-circle-2" class="w-3.5 h-3.5"></i>
        <span id="mNavTabPortfolio">기술 검증</span>
        <span class="text-[9px] font-mono px-1 py-0.2 rounded bg-white/20 text-white font-bold" id="mHeaderVerifiedCount">{data['total_cases']}</span>
      </button>
      <button onclick="switchView('news')" id="mTabNewsBtn" class="mobile-nav-tab shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium text-ink-secondary hover:text-ink-primary bg-surface-subtle border border-surface-border transition">
        <i data-lucide="newspaper" class="w-3.5 h-3.5"></i>
        <span id="mNavTabNews">AI 뉴스 ({data['news_total_count']})</span>
      </button>
      <button onclick="switchView('graph')" id="mTabGraphBtn" class="mobile-nav-tab shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium text-ink-secondary hover:text-ink-primary bg-surface-subtle border border-surface-border transition">
        <i data-lucide="network" class="w-3.5 h-3.5"></i>
        <span id="mNavTabGraph">인용 계보망</span>
      </button>
      <button onclick="switchView('inbox')" id="mTabInboxBtn" class="mobile-nav-tab shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium text-ink-secondary hover:text-ink-primary bg-surface-subtle border border-surface-border transition">
        <i data-lucide="inbox" class="w-3.5 h-3.5"></i>
        <span id="mNavTabInbox">수집 인박스 ({data['inbox_total_count']})</span>
      </button>
    </div>
  </header>

  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">

    <!-- ==================== VIEW 1: TECH FACT-CHECK (기술 검증) ==================== -->
    <div id="portfolioView" class="space-y-6">

      <!-- Executive Intro Hero Banner -->
      <div class="bg-white p-6 sm:p-7 rounded-2xl border border-surface-border flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm">
        <div class="max-w-3xl space-y-1.5">
          <div class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md bg-surface-subtle text-ink-secondary text-xs font-mono font-bold border border-surface-border" id="heroBadge">
            ZERO-HALLUCINATION ARCHITECTURE & COST AUDIT
          </div>
          <h2 class="text-xl sm:text-2xl font-extrabold text-ink-primary tracking-tight" id="heroMainTitle">
            소문난 AI 기술의 실체와 공학적 단위 경제성 정밀 검증
          </h2>
          <p class="text-xs sm:text-sm text-ink-secondary leading-relaxed" id="heroMainDesc">
            SNS 바이럴 마케팅의 환각을 걷어내고, <strong>1차 공식 출처 감사</strong>와 <strong>기저 표준 vs 서드파티 실측 벤치마크</strong>를 통해 도출한 100% 실증 보고서입니다.
          </p>
        </div>

        <div class="text-right shrink-0 hidden md:block border-l border-surface-border pl-6">
          <div class="text-xs text-ink-muted font-mono font-medium" id="heroUpdateLabel">LAST AUDITED</div>
          <div class="text-base font-bold text-ink-primary font-mono">2026-09-02</div>
          <div class="text-[11px] text-emerald-700 font-semibold mt-0.5" id="heroAuditCount">{data['total_cases']}개 기술 검증 완료</div>
        </div>
      </div>

      <!-- 🔔 AUTONOMOUS PROMOTION WATCH BANNER (자율 승격 알림 배너) -->
      <div id="promotionWatchBanner" class="bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200/80 p-4 sm:p-4.5 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-sm">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-700 shrink-0">
            <i data-lucide="check-circle" class="w-4 h-4"></i>
          </div>
          <div class="space-y-0.5">
            <div class="text-xs font-bold text-emerald-950 flex items-center gap-2">
              <span id="promoBannerTitle">기술 검증 포트폴리오 최신 상태 알림</span>
              <span class="px-2 py-0.2 rounded bg-emerald-200/80 text-emerald-900 font-mono text-[10px] font-bold" id="promoCountBadge">18건 검증 완료</span>
            </div>
            <p class="text-[11px] text-emerald-800 leading-relaxed" id="promoBannerDesc">
              바이럴 임계치를 초과하여 유입된 주요 오픈소스 및 모델 후보군 총 18건에 대한 심층 실측 벤치마크와 팩트체크가 모두 완료되었습니다.
            </p>
          </div>
        </div>

        <button onclick="switchView('inbox')" class="shrink-0 px-3.5 py-1.5 rounded-xl bg-emerald-900 text-white text-xs font-bold hover:bg-emerald-800 transition flex items-center gap-1 shadow-sm">
          <span id="promoBtnText">수집 인박스 후보군 보기</span> <i data-lucide="arrow-right" class="w-3.5 h-3.5"></i>
        </button>
      </div>

      <!-- HIGH-VISIBILITY CONTROL CENTER -->
      <div class="bg-white p-4 sm:p-5 rounded-2xl border border-surface-border space-y-4 shadow-sm">
        
        <!-- Row 1: 3-Segment Discovery Mode & Sorting Selector -->
        <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
          
          <!-- Mode Segments -->
          <div class="flex items-center bg-surface-subtle p-1 rounded-xl border border-surface-border text-xs w-full md:w-auto">
            <button onclick="setModeFilter('ALL')" id="modeBtnAll" class="segment-btn active flex-1 md:flex-initial px-4 py-2 rounded-lg text-xs font-bold transition flex items-center justify-center gap-1.5">
              <span id="btnLabelAll">전체 검증</span>
              <span class="text-[11px] font-mono px-1.5 py-0.2 rounded bg-black/10 text-white font-bold" id="badgeCountAll">{data['total_cases']}</span>
            </button>
            <button onclick="setModeFilter('USER_CURATED')" id="modeBtnUser" class="segment-btn flex-1 md:flex-initial px-4 py-2 rounded-lg text-xs font-semibold hover:text-ink-primary transition flex items-center justify-center gap-1.5">
              <i data-lucide="user-check" class="w-3.5 h-3.5 text-indigo-600"></i>
              <span id="btnLabelUser">직접 큐레이션</span>
              <span class="text-[11px] font-mono px-1.5 py-0.2 rounded bg-black/5 text-ink-secondary font-bold" id="badgeCountUser">{data['total_cases']}</span>
            </button>
            <button onclick="setModeFilter('AUTO_HARVESTED')" id="modeBtnAuto" class="segment-btn flex-1 md:flex-initial px-4 py-2 rounded-lg text-xs font-semibold hover:text-ink-primary transition flex items-center justify-center gap-1.5">
              <i data-lucide="bot" class="w-3.5 h-3.5 text-emerald-600"></i>
              <span id="btnLabelAuto">자동 트렌드</span>
              <span class="text-[11px] font-mono px-1.5 py-0.2 rounded bg-black/5 text-ink-secondary font-bold" id="badgeCountAuto">0</span>
            </button>
          </div>

          <!-- Sort Select & Results Counter -->
          <div class="flex items-center justify-between w-full md:w-auto gap-3">
            <span class="text-xs text-ink-muted font-mono" id="resultsCountLabel">총 {data['total_cases']}건 표시</span>
            
            <div class="flex items-center gap-2 bg-surface-subtle px-3 py-1.5 rounded-xl border border-surface-border text-xs">
              <i data-lucide="arrow-up-down" class="w-3.5 h-3.5 text-ink-secondary shrink-0"></i>
              <span class="text-ink-secondary text-xs font-medium shrink-0" id="sortLabel">정렬:</span>
              <select id="sortSelect" onchange="changeSort(this.value)" class="bg-transparent text-ink-primary font-bold text-xs focus:outline-none cursor-pointer">
                <option value="date-desc">최신 조사일자순 (기본)</option>
                <option value="date-asc">과거 조사일자순</option>
                <option value="score-desc">높은 신뢰도순</option>
                <option value="title-asc">기술명 가나다순</option>
              </select>
            </div>
          </div>

        </div>

        <!-- Row 2: Search Input & Compact Responsive Domain Tag Filter Pills -->
        <div class="flex flex-col lg:flex-row items-center justify-between gap-3 pt-3 border-t border-surface-border">
          
          <!-- Search Box -->
          <div class="relative w-full lg:w-80">
            <i data-lucide="search" class="w-4 h-4 absolute left-3.5 top-2.5 text-ink-muted"></i>
            <input type="text" id="searchInput" placeholder="기술명, 아키텍처, 큐레이션 동기 검색..." 
                   class="w-full bg-surface-subtle border border-surface-border rounded-xl pl-10 pr-9 py-2 text-xs text-ink-primary placeholder-ink-muted focus:outline-none focus:border-ink-primary transition font-medium">
            <button onclick="clearSearch()" id="clearSearchBtn" class="hidden absolute right-3 top-2.5 text-ink-muted hover:text-ink-primary">
              <i data-lucide="x" class="w-3.5 h-3.5"></i>
            </button>
          </div>

          <!-- Domain Tag Filter Pills (Compact & Responsive) -->
          <div class="flex items-center gap-1.5 w-full lg:w-auto justify-start lg:justify-end overflow-x-auto no-scrollbar py-1">
            <span class="text-[11px] text-ink-muted font-mono mr-1 shrink-0" id="domainFilterLabel">도메인:</span>
            <button onclick="setDomainFilter('ALL')" class="tag-pill active shrink-0 px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-surface-subtle text-ink-secondary border border-surface-border hover:border-ink-primary" data-domain="ALL" id="tagAll">전체</button>
            <button onclick="setDomainFilter('frontend')" class="tag-pill shrink-0 px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-surface-subtle text-ink-secondary border border-surface-border hover:border-ink-primary" data-domain="frontend" id="tagFrontend">프론트엔드</button>
            <button onclick="setDomainFilter('agent')" class="tag-pill shrink-0 px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-surface-subtle text-ink-secondary border border-surface-border hover:border-ink-primary" data-domain="agent" id="tagAgent">AI 에이전트</button>
            <button onclick="setDomainFilter('scraping')" class="tag-pill shrink-0 px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-surface-subtle text-ink-secondary border border-surface-border hover:border-ink-primary" data-domain="scraping" id="tagScraping">웹 스크래핑</button>
            <button onclick="setDomainFilter('doc')" class="tag-pill shrink-0 px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-surface-subtle text-ink-secondary border border-surface-border hover:border-ink-primary" data-domain="doc" id="tagDoc">문서 파싱</button>
            <button onclick="setDomainFilter('3d')" class="tag-pill shrink-0 px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-surface-subtle text-ink-secondary border border-surface-border hover:border-ink-primary" data-domain="3d" id="tag3d">3D/컴포넌트</button>
            <button onclick="setDomainFilter('rust')" class="tag-pill shrink-0 px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-surface-subtle text-ink-secondary border border-surface-border hover:border-ink-primary" data-domain="rust" id="tagRust">Rust/시스템</button>
            <button onclick="setDomainFilter('other')" class="tag-pill shrink-0 px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-surface-subtle text-ink-secondary border border-surface-border hover:border-ink-primary" data-domain="other" id="tagOther">기타/코어 인프라</button>
          </div>

        </div>

      </div>

      <!-- EXECUTIVE SCANNABLE DOSSIER GRID -->
      <div id="cardsGrid" class="grid grid-cols-1 lg:grid-cols-2 gap-6"></div>
    </div>

    <!-- ==================== VIEW 2: AI NEWS & TRENDS ==================== -->
    <div id="newsView" class="hidden space-y-6">
      <div class="bg-white p-6 rounded-2xl border border-surface-border flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-sm">
        <div class="space-y-1">
          <div class="flex items-center gap-2">
            <span class="px-2.5 py-0.5 rounded-md bg-surface-subtle text-ink-primary text-xs font-mono font-bold border border-surface-border" id="newsHeaderBadge">
              GLOBAL AI INTELLIGENCE FEED
            </span>
            <span class="text-xs text-ink-muted font-mono" id="newsHeaderCount">총 {data['news_total_count']}건</span>
          </div>
          <h2 class="text-lg font-bold text-ink-primary" id="newsHeaderTitle">커뮤니티, 해커뉴스, 사설에서 수집된 주요 AI 담론</h2>
          <p class="text-xs text-ink-secondary" id="newsHeaderDesc">
            소프트웨어 저장소뿐만 아니라 엔지니어링 동향, 보안 리포트, 아키텍처 튜토리얼 기사를 선별합니다.
          </p>
        </div>
      </div>

      <div id="newsGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5"></div>
    </div>

    <!-- ==================== VIEW 3: CITATION GRAPH ==================== -->
    <div id="graphView" class="hidden space-y-6">
      <div class="bg-white p-6 rounded-2xl border border-surface-border space-y-4 shadow-sm">
        <div class="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
          <div>
            <div class="flex items-center gap-2 flex-wrap">
              <span class="px-2.5 py-0.5 rounded-md bg-surface-subtle text-ink-primary text-xs font-mono font-bold border border-surface-border" id="graphHeaderBadge">
                MULTI-ENTITY CITATION NETWORK
              </span>
              <span class="text-xs text-ink-muted" id="graphHeaderSub">기술 • 연구자 • 연구소 • 1차 논문</span>
            </div>
            <h2 class="text-lg font-bold text-ink-primary mt-1" id="graphHeaderTitle">인물과 논문 인용 계보를 통한 기술 탄생의 뿌리 지도</h2>
          </div>

          <!-- Entity Group Filters -->
          <div class="flex flex-wrap items-center gap-1.5 bg-surface-subtle p-1.5 rounded-xl border border-surface-border text-xs">
            <button onclick="filterGraphGroup('ALL')" class="graph-group-btn active px-2.5 py-1 rounded-lg bg-ink-primary text-white font-medium transition" data-group="ALL" id="graphBtnAll">전체 보기</button>
            <button onclick="filterGraphGroup('language')" class="graph-group-btn px-2.5 py-1 rounded-lg text-amber-700 hover:bg-white transition" data-group="language" id="graphBtnLang">언어</button>
            <button onclick="filterGraphGroup('technology')" class="graph-group-btn px-2.5 py-1 rounded-lg text-emerald-700 hover:bg-white transition" data-group="technology" id="graphBtnTech">기술/엔진</button>
            <button onclick="filterGraphGroup('organization')" class="graph-group-btn px-2.5 py-1 rounded-lg text-indigo-700 hover:bg-white transition" data-group="organization" id="graphBtnOrg">연구소</button>
            <button onclick="filterGraphGroup('person')" class="graph-group-btn px-2.5 py-1 rounded-lg text-rose-700 hover:bg-white transition" data-group="person" id="graphBtnPerson">인물</button>
            <button onclick="filterGraphGroup('paper')" class="graph-group-btn px-2.5 py-1 rounded-lg text-orange-700 hover:bg-white transition" data-group="paper" id="graphBtnPaper">논문</button>
          </div>
        </div>

        <div class="relative w-full h-[640px] bg-surface-canvas rounded-xl border border-surface-border overflow-hidden">
          <svg id="techGraphSvg" class="w-full h-full cursor-grab active:cursor-grabbing"></svg>
        </div>
      </div>
    </div>

    <!-- ==================== VIEW 4: HARVEST INBOX ==================== -->
    <div id="inboxView" class="hidden space-y-6">
      
      <!-- Inbox Header -->
      <div class="bg-white p-6 rounded-2xl border border-surface-border flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-sm">
        <div class="space-y-1">
          <div class="flex items-center gap-2">
            <span class="px-2.5 py-0.5 rounded-md bg-surface-subtle text-ink-primary text-xs font-mono font-bold border border-surface-border" id="inboxHeaderBadge">
              AUTONOMOUS HARVEST INBOX
            </span>
            <span class="text-xs text-ink-muted font-mono" id="inboxHeaderCount">총 {data['inbox_total_count']}건</span>
          </div>
          <h2 class="text-lg font-bold text-ink-primary" id="inboxHeaderTitle">24시간 자율 크론으로 수집된 오픈소스 및 모델 후보군</h2>
          <p class="text-xs text-ink-secondary" id="inboxHeaderDesc">
            원클릭으로 분석 큐에 등록하여 Neon DB와 실시간 동기화하고 심층 팩트체크를 진행할 수 있습니다.
          </p>
        </div>
      </div>

      <!-- 🌟 AUTONOMOUS PROMOTION CRITERIA GUIDE BOX -->
      <div class="bg-gradient-to-r from-indigo-50/70 via-sky-50/60 to-purple-50/70 p-5 rounded-2xl border border-indigo-100 space-y-3 shadow-sm">
        <div class="flex items-center gap-2 text-xs font-bold text-indigo-950">
          <i data-lucide="sparkles" class="w-4 h-4 text-indigo-600"></i>
          <span id="criteriaTitle">자율 크론 4대 자동 승격(Promotion) 기준 가이드</span>
        </div>
        <p class="text-xs text-indigo-900 leading-relaxed" id="criteriaDesc">
          수집된 수많은 오픈소스 및 논문 중 아래의 4대 바이럴/기술 임계치를 돌파한 항목은 자동으로 <strong>[자동 승격 트렌드 후보]</strong>로 격상되어 최우선 기술 검증 대기열에 등록됩니다.
        </p>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-1 text-xs">
          <div class="p-3 rounded-xl bg-white/90 border border-indigo-100 space-y-1">
            <div class="font-bold text-indigo-950 flex items-center gap-1.5">
              <span>🐙 GitHub Stars</span>
            </div>
            <p class="text-[11px] text-ink-secondary" id="critGithub">최근 14일 이내 생성 & ★ > 500 Stars 돌파</p>
          </div>
          <div class="p-3 rounded-xl bg-white/90 border border-indigo-100 space-y-1">
            <div class="font-bold text-orange-950 flex items-center gap-1.5">
              <span>🔥 Hacker News</span>
            </div>
            <p class="text-[11px] text-ink-secondary" id="critHn">Top/Best 스토리 중 추천 점수 🔥 > 150 Points</p>
          </div>
          <div class="p-3 rounded-xl bg-white/90 border border-indigo-100 space-y-1">
            <div class="font-bold text-amber-950 flex items-center gap-1.5">
              <span>🤗 Hugging Face</span>
            </div>
            <p class="text-[11px] text-ink-secondary" id="critHf">Trending 점수 상위권 & ❤️ > 100 Likes 모델/데모</p>
          </div>
          <div class="p-3 rounded-xl bg-white/90 border border-indigo-100 space-y-1">
            <div class="font-bold text-emerald-950 flex items-center gap-1.5">
              <span>📄 ArXiv CS.AI</span>
            </div>
            <p class="text-[11px] text-ink-secondary" id="critArxiv">MoE, Reasoning, VLM 등 혁신 아키텍처 1차 논문</p>
          </div>
        </div>
      </div>

      <!-- Clean Inbox Controls -->
      <div class="bg-white p-3.5 rounded-2xl flex flex-col md:flex-row items-center justify-between gap-3 border border-surface-border shadow-sm">
        <div class="flex items-center gap-2.5 w-full md:w-auto">
          <div class="relative w-full md:w-80">
            <i data-lucide="search" class="w-4 h-4 absolute left-3.5 top-2.5 text-ink-muted"></i>
            <input type="text" id="inboxSearchInput" placeholder="후보 기술 또는 모델명 검색..." 
                   class="w-full bg-surface-subtle border border-surface-border rounded-xl pl-10 pr-4 py-2 text-xs text-ink-primary placeholder-ink-muted focus:outline-none focus:border-ink-primary transition font-medium">
          </div>

          <button onclick="toggleFamilyGrouping()" id="groupByFamilyBtn" class="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold bg-ink-primary text-white transition shrink-0">
            <i data-lucide="layers" class="w-4 h-4"></i>
            <span id="groupByFamilyText">패밀리 묶음 (ON)</span>
          </button>
        </div>

        <div class="flex items-center gap-2 w-full md:w-auto justify-end">
          <div class="flex items-center gap-1.5 bg-surface-subtle px-3 py-1.5 rounded-xl border border-surface-border text-xs">
            <i data-lucide="filter" class="w-3.5 h-3.5 text-ink-secondary"></i>
            <select id="inboxSourceSelect" onchange="setInboxSourceFilter(this.value)" class="bg-transparent text-ink-primary text-xs font-semibold focus:outline-none cursor-pointer">
              <option value="ALL">전체 수집 플랫폼 ({data['inbox_total_count']}건)</option>
              <option value="Hacker News">🔥 Hacker News Top/Best</option>
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
    <div class="bg-white max-w-4xl w-full rounded-2xl overflow-hidden shadow-2xl border border-surface-border my-8 max-h-[92vh] flex flex-col">
      
      <!-- Modal Header -->
      <div class="p-6 border-b border-surface-border flex items-start justify-between bg-surface-subtle">
        <div class="space-y-2 pr-4">
          <div class="flex items-center gap-2 flex-wrap">
            <span id="modalModeBadge" class="text-xs px-2.5 py-0.5 rounded-md font-semibold"></span>
            <span id="modalClusterBadge" class="text-xs px-2.5 py-0.5 rounded-md bg-white text-ink-primary border border-surface-border font-medium"></span>
            <span id="modalVerdictBadge" class="text-xs px-2.5 py-0.5 rounded-md font-semibold"></span>
            <span id="modalStageBadge" class="text-xs px-2.5 py-0.5 rounded-md font-medium"></span>
          </div>
          <h3 id="modalTitle" class="text-xl font-bold text-ink-primary pt-1"></h3>
        </div>
        <button onclick="closeModal()" class="text-ink-secondary hover:text-ink-primary p-1.5 rounded-lg bg-white border border-surface-border hover:bg-surface-subtle transition">
          <i data-lucide="x" class="w-5 h-5"></i>
        </button>
      </div>

      <!-- Modal Body -->
      <div class="p-6 overflow-y-auto space-y-6 text-sm text-ink-secondary">
        
        <!-- Curation & Intent -->
        <div id="modalCurationBox" class="p-4 rounded-xl border border-surface-border bg-surface-subtle space-y-1.5">
          <div class="flex items-center justify-between">
            <h4 class="text-xs font-bold uppercase tracking-wider text-ink-primary flex items-center gap-1.5">
              <i data-lucide="compass" class="w-3.5 h-3.5 text-indigo-600"></i> <span id="modalSecCurationTitle">Discovery Motivation & Target Workflow</span>
            </h4>
          </div>
          <p id="modalMotivation" class="text-xs text-ink-primary leading-relaxed font-medium"></p>
          <div class="pt-1.5 flex items-center gap-1.5 text-xs text-ink-secondary">
            <span class="text-ink-muted" id="modalWorkflowLabel">🎯 연계 워크플로우:</span>
            <span id="modalWorkflow" class="text-ink-primary font-semibold font-mono"></span>
          </div>
        </div>

        <!-- 🌟 VIRAL CLAIMS DOSSIER (Hides cleanly when quote is missing) -->
        <div id="modalViralPostBox" class="hidden p-4.5 rounded-xl border border-indigo-200/90 bg-indigo-50/50 space-y-3">
          <div class="flex items-center justify-between">
            <h4 class="text-xs font-bold uppercase tracking-wider text-indigo-950 flex items-center gap-1.5">
              <i data-lucide="message-square-quote" class="w-4 h-4 text-indigo-700"></i> <span id="modalSecViralPostTitle">1차 마케팅 원문 & 바이럴 클레임 발췌 (Raw Viral Claim)</span>
            </h4>
            <span id="modalViralPlatformBadge" class="text-[11px] px-2 py-0.5 rounded font-mono font-bold bg-white text-indigo-800 border border-indigo-200"></span>
          </div>

          <div class="bg-white p-3.5 rounded-xl border border-indigo-100 space-y-2">
            <div class="text-[11px] text-indigo-900 font-mono font-semibold" id="modalViralAuthor"></div>
            <p id="modalViralQuote" class="text-xs text-ink-secondary leading-relaxed italic font-sans"></p>
          </div>

          <div class="flex items-center justify-between pt-1">
            <span class="text-[11px] text-indigo-800 font-mono" id="modalViralNote"></span>
            <a id="modalViralDirectLink" href="#" target="_blank" class="px-3 py-1.5 rounded-lg bg-indigo-900 text-white text-xs font-bold hover:bg-indigo-800 transition flex items-center gap-1">
              <span id="modalViralLinkText">원문 포스트 바로가기</span> <i data-lucide="external-link" class="w-3 h-3"></i>
            </a>
          </div>
        </div>

        <!-- Claims Assessment (Claims vs Truth) -->
        <div id="modalClaimsBox" class="hidden space-y-3 p-4 rounded-xl border border-amber-200 bg-amber-50/50">
          <h4 class="text-xs font-bold uppercase tracking-wider text-amber-900 flex items-center gap-1.5">
            <i data-lucide="scale" class="w-3.5 h-3.5"></i> <span id="modalSecClaimsTitle">Marketing Claims vs Empirical Reality</span>
          </h4>
          <div id="modalClaimsList" class="space-y-2.5"></div>
        </div>

        <!-- Story & Empirical Proof -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="p-4 rounded-xl bg-surface-subtle border border-surface-border space-y-2">
            <h4 class="text-xs font-bold uppercase tracking-wider text-ink-primary flex items-center gap-1.5">
              <i data-lucide="eye" class="w-3.5 h-3.5 text-ink-secondary"></i> <span id="modalSecHookTitle">The Hook & Marketing Hype</span>
            </h4>
            <p id="modalHook" class="text-xs text-ink-secondary leading-relaxed"></p>
            <p id="modalHype" class="text-xs text-ink-muted leading-relaxed pt-1 border-t border-surface-border"></p>
          </div>

          <div class="p-4 rounded-xl bg-surface-subtle border border-surface-border space-y-2">
            <h4 class="text-xs font-bold uppercase tracking-wider text-ink-primary flex items-center gap-1.5">
              <i data-lucide="wrench" class="w-3.5 h-3.5 text-emerald-700"></i> <span id="modalSecHandsOnTitle">Hands-on Measured Results</span>
            </h4>
            <div id="modalHandsOnEnv" class="text-xs text-ink-muted font-mono"></div>
            <div id="modalHandsOnMetrics" class="text-xs font-bold text-emerald-800"></div>
            <p id="modalHandsOnDetails" class="text-xs text-ink-secondary leading-relaxed"></p>
          </div>
        </div>

        <!-- Alternatives Matrix -->
        <div class="space-y-3">
          <h4 class="text-xs font-bold uppercase tracking-wider text-ink-primary flex items-center gap-1.5">
            <i data-lucide="git-compare" class="w-3.5 h-3.5 text-ink-secondary"></i> <span id="modalSecAltsTitle">Comparative Alternatives Matrix</span>
          </h4>
          <div class="overflow-x-auto rounded-xl border border-surface-border">
            <table class="w-full text-left text-xs border-collapse">
              <thead class="bg-surface-subtle text-ink-secondary font-mono">
                <tr>
                  <th class="p-3 border-b border-surface-border" id="thTool">Tool / Tech</th>
                  <th class="p-3 border-b border-surface-border" id="thStack">Tech Stack</th>
                  <th class="p-3 border-b border-surface-border" id="thPros">Pros</th>
                  <th class="p-3 border-b border-surface-border" id="thCons">Cons</th>
                  <th class="p-3 border-b border-surface-border" id="thBestFor">Best For</th>
                </tr>
              </thead>
              <tbody id="modalAlternativesBody" class="divide-y divide-surface-border bg-white"></tbody>
            </table>
          </div>
        </div>

        <!-- Primary Sources -->
        <div class="space-y-2.5">
          <h4 class="text-xs font-bold uppercase tracking-wider text-ink-primary flex items-center gap-1.5">
            <i data-lucide="book-open" class="w-3.5 h-3.5 text-ink-secondary"></i> <span id="modalSecSourcesTitle">Audited Primary Sources</span>
          </h4>
          <div id="modalSourcesList" class="grid grid-cols-1 sm:grid-cols-2 gap-2.5"></div>
        </div>

      </div>
    </div>
  </div>

  <!-- Toast Notification -->
  <div id="toast" class="fixed bottom-6 right-6 z-50 bg-ink-primary text-white px-4 py-3 rounded-xl shadow-2xl text-xs font-semibold hidden transition-all duration-300 flex items-center gap-2">
    <i data-lucide="check-circle-2" class="w-4 h-4 text-emerald-400"></i>
    <span id="toastMsg">작업이 완료되었습니다.</span>
  </div>

  <!-- ==================== SCRIPTS & TRI-LINGUAL TRANSLATION SYSTEM ==================== -->
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

    // Complete Tri-Lingual i18n Dictionary (KO / ZH / EN)
    const i18n = {{
      KO: {{
        brandTitle: "FactCheck Hub",
        brandSubtitle: "AI 바이럴 마케팅 실체 & 공학적 원가 검증 포털",
        navPortfolio: "기술 검증",
        navNews: "AI 뉴스",
        navGraph: "인용 계보망",
        navInbox: "수집 인박스",
        heroBadge: "ZERO-HALLUCINATION ARCHITECTURE & COST AUDIT",
        heroMainTitle: "소문난 AI 기술의 실체와 공학적 단위 경제성 정밀 검증",
        heroMainDesc: "SNS 바이럴 마케팅의 환각을 걷어내고, 1차 공식 출처 감사와 기저 표준 vs 서드파티 실측 벤치마크를 통해 도출한 100% 실증 보고서입니다.",
        heroUpdateLabel: "최종 검증일",
        heroAuditCount: "18개 기술 검증 완료",
        promoBannerTitle: "기술 검증 포트폴리오 최신 상태 알림",
        promoCountBadge: "18건 검증 완료",
        promoBannerDesc: "바이럴 임계치를 초과하여 유입된 주요 오픈소스 및 모델 후보군 총 18건에 대한 심층 실측 벤치마크와 팩트체크가 모두 완료되었습니다.",
        promoBtnText: "수집 인박스 후보군 보기",
        btnAll: "전체 검증",
        btnUser: "직접 큐레이션",
        btnAuto: "자동 트렌드",
        sortLabel: "정렬:",
        sortOptions: [
          {{ val: "date-desc", text: "최신 조사일자순 (기본)" }},
          {{ val: "date-asc", text: "과거 조사일자순" }},
          {{ val: "score-desc", text: "높은 신뢰도순" }},
          {{ val: "title-asc", text: "기술명 가나다순" }}
        ],
        searchPlaceholder: "기술명, 아키텍처, 큐레이션 동기 검색...",
        domainLabel: "도메인:",
        tagAll: "전체",
        tagFrontend: "프론트엔드",
        tagAgent: "AI 에이전트",
        tagScraping: "웹 스크래핑",
        tagDoc: "문서 파싱",
        tag3d: "3D/컴포넌트",
        tagRust: "Rust/시스템",
        tagOther: "기타/코어 인프라",
        cardMotivationLabel: "💡 발굴 의도 / 문제의식:",
        cardVerdictLabel: "⚡ 검증 팩트 / 결론:",
        cardConfidenceLabel: "신뢰도",
        cardSourcesLabel: "개 1차 출처",
        cardViewBtn: "심층 보고서 열람",
        newsHeaderBadge: "GLOBAL AI INTELLIGENCE FEED",
        newsHeaderTitle: "커뮤니티, 해커뉴스, 사설에서 수집된 주요 AI 담론",
        newsHeaderDesc: "소프트웨어 저장소뿐만 아니라 엔지니어링 동향, 보안 리포트, 아키텍처 튜토리얼 기사를 선별합니다.",
        newsOriginalLink: "기사 원문",
        graphHeaderBadge: "MULTI-ENTITY CITATION NETWORK",
        graphHeaderTitle: "인물과 논문 인용 계보를 통한 기술 탄생의 뿌리 지도",
        graphHeaderSub: "기술 • 연구자 • 연구소 • 1차 논문",
        graphBtnAll: "전체 보기",
        graphBtnLang: "언어",
        graphBtnTech: "기술/엔진",
        graphBtnOrg: "연구소",
        graphBtnPerson: "인물",
        graphBtnPaper: "논문",
        criteriaTitle: "자율 크론 4대 자동 승격(Promotion) 기준 가이드",
        criteriaDesc: "수집된 수많은 오픈소스 및 논문 중 아래의 4대 바이럴/기술 임계치를 돌파한 항목은 자동으로 [자동 승격 트렌드 후보]로 격상되어 최우선 기술 검증 대기열에 등록됩니다.",
        critGithub: "최근 14일 이내 생성 & ★ > 500 Stars 돌파",
        critHn: "Top/Best 스토리 중 추천 점수 🔥 > 150 Points",
        critHf: "Trending 점수 상위권 & ❤️ > 100 Likes 모델/데모",
        critArxiv: "MoE, Reasoning, VLM 등 혁신 아키텍처 1차 논문",
        inboxHeaderBadge: "AUTONOMOUS HARVEST INBOX",
        inboxHeaderTitle: "24시간 자율 크론으로 수집된 오픈소스 및 모델 후보군",
        inboxHeaderDesc: "원클릭으로 분석 큐에 등록하여 Neon DB와 실시간 동기화하고 심층 팩트체크를 진행할 수 있습니다.",
        inboxFamilyOn: "패밀리 묶음 (ON)",
        inboxFamilyOff: "패밀리 묶음 (OFF)",
        inboxSearchPlaceholder: "후보 기술 또는 모델명 검색...",
        inboxQueueBtn: "분석 큐 담기",
        inboxQueuedBtn: "대기열 등록됨",
        modalSecCurationTitle: "Discovery Motivation & Target Workflow",
        modalSecViralPostTitle: "1차 마케팅 원문 & 바이럴 클레임 발췌 (Raw Viral Claim)",
        modalSecClaimsTitle: "Marketing Claims vs Empirical Reality",
        modalSecHookTitle: "The Hook & Marketing Hype",
        modalSecHandsOnTitle: "Hands-on Measured Results",
        modalSecAltsTitle: "Comparative Alternatives Matrix",
        modalSecSourcesTitle: "Audited Primary Sources",
        modalWorkflowLabel: "🎯 연계 워크플로우:",
        modalViralLinkText: "원문 포스트 바로가기",
        thTool: "도구 / 기술명",
        thStack: "기술 스택",
        thPros: "장점",
        thCons: "단점",
        thBestFor: "적합한 환경"
      }},
      ZH: {{
        brandTitle: "FactCheck Hub",
        brandSubtitle: "AI 营销炒作真相与工程单位经济性审计门户",
        navPortfolio: "技术审计",
        navNews: "AI 资讯",
        navGraph: "引用系谱图",
        navInbox: "采集收件箱",
        heroBadge: "ZERO-HALLUCINATION ARCHITECTURE & COST AUDIT",
        heroMainTitle: "热门 AI 技术的工程真相与单位经济性深度核实",
        heroMainDesc: "摒弃社交媒体营销炒作与幻觉，基于第一手官方源码审计以及基础标准 vs 第三方工具的实测基准，输出 100% 真实客观的工程报告。",
        heroUpdateLabel: "最新审计",
        heroAuditCount: "已完成 18 项技术审计",
        promoBannerTitle: "技术审计档案库最新状态",
        promoCountBadge: "18 项核验完毕",
        promoBannerDesc: "已对突破热度阈值自动晋升的 18 项重点开源项目与前沿模型完成全流程深度实测基准与事实核查。",
        promoBtnText: "查看采集收件箱候选",
        btnAll: "全部审计",
        btnUser: "人工精选",
        btnAuto: "自动趋势",
        sortLabel: "排序:",
        sortOptions: [
          {{ val: "date-desc", text: "最新调查日期 (默认)" }},
          {{ val: "date-asc", text: "最早调查日期" }},
          {{ val: "score-desc", text: "最高可信度得分" }},
          {{ val: "title-asc", text: "技术名称拼音/字母序" }}
        ],
        searchPlaceholder: "搜索技术名、架构或策展动机...",
        domainLabel: "领域:",
        tagAll: "全部",
        tagFrontend: "前端/UI",
        tagAgent: "AI Agent",
        tagScraping: "网页爬虫",
        tagDoc: "文档解析",
        tag3d: "3D/组件",
        tagRust: "Rust系统",
        tagOther: "核心基建",
        cardMotivationLabel: "💡 挖掘动机 / 痛点问题:",
        cardVerdictLabel: "⚡ 审计结论 / 事实核验:",
        cardConfidenceLabel: "可信度",
        cardSourcesLabel: "个一手来源",
        cardViewBtn: "查阅完整报告",
        newsHeaderBadge: "GLOBAL AI INTELLIGENCE FEED",
        newsHeaderTitle: "源自社区、HackerNews 与专栏的前沿 AI 讨论",
        newsHeaderDesc: "不仅追踪开源代码仓库，还精选工程趋势、安全漏洞分析与架构实践教程。",
        newsOriginalLink: "阅读原文",
        graphHeaderBadge: "MULTI-ENTITY CITATION NETWORK",
        graphHeaderTitle: "人物与论文引用系谱技术溯源全景图",
        graphHeaderSub: "技术 • 研究员 • 实验室 • 一手论文",
        graphBtnAll: "查看全部",
        graphBtnLang: "编程语言",
        graphBtnTech: "核心技术/引擎",
        graphBtnOrg: "科研机构",
        graphBtnPerson: "代表人物",
        graphBtnPaper: "经典论文",
        criteriaTitle: "全自动巡检 4 大自动晋升 (Promotion) 判定准则",
        criteriaDesc: "在海量采集的开源项目与前沿论文中，突破以下 4 项热度与技术指标的候选项目将自动晋升至优先核查队列。",
        critGithub: "14 天内新建仓库且 ★ > 500 Stars 突破",
        critHn: "Top/Best 讨论中点赞热度 🔥 > 150 Points",
        critHf: "Trending 趋势榜前列且 ❤️ > 100 Likes 模型/Demo",
        critArxiv: "涵盖 MoE、推理强化、VLM 的第一手经典架构论文",
        inboxHeaderBadge: "AUTONOMOUS HARVEST INBOX",
        inboxHeaderTitle: "24 小时全自动巡检采集的开源仓库与模型候选",
        inboxHeaderDesc: "一键加入审计队列，与 Neon Postgres 数据库实时同步并触发深度事实核查。",
        inboxFamilyOn: "系列聚合 (开)",
        inboxFamilyOff: "系列聚合 (关)",
        inboxSearchPlaceholder: "搜索候选技术或模型名称...",
        inboxQueueBtn: "加入待审队列",
        inboxQueuedBtn: "已在队列中",
        modalSecCurationTitle: "Discovery Motivation & Target Workflow",
        modalSecViralPostTitle: "营销宣传原文摘录与主张证据 (Raw Viral Claim)",
        modalSecClaimsTitle: "Marketing Claims vs Empirical Reality",
        modalSecHookTitle: "The Hook & Marketing Hype",
        modalSecHandsOnTitle: "Hands-on Measured Results",
        modalSecAltsTitle: "Comparative Alternatives Matrix",
        modalSecSourcesTitle: "Audited Primary Sources",
        modalWorkflowLabel: "🎯 协同工作流:",
        modalViralLinkText: "直达原文帖子",
        thTool: "工具 / 技术",
        thStack: "技术栈",
        thPros: "核心优势",
        thCons: "劣势与局限",
        thBestFor: "最适用场景"
      }},
      EN: {{
        brandTitle: "FactCheck Hub",
        brandSubtitle: "Universal AI Viral Marketing Audit & Empirical Cost Portal",
        navPortfolio: "Fact-Checks",
        navNews: "AI News",
        navGraph: "Citation Graph",
        navInbox: "Harvest Inbox",
        heroBadge: "ZERO-HALLUCINATION ARCHITECTURE & COST AUDIT",
        heroMainTitle: "Empirical Truth & Unit Economics of Viral AI Tech",
        heroMainDesc: "A zero-hallucination dossier derived from Tier-1 official source audits and empirical benchmarks comparing base standards with third-party tools.",
        heroUpdateLabel: "LAST AUDITED",
        heroAuditCount: "18 Audits Completed",
        promoBannerTitle: "Dossier Status Update",
        promoCountBadge: "18 Completed",
        promoBannerDesc: "All 18 high-velocity repositories and models that crossed the viral threshold have been rigorously benchmarked and fact-checked.",
        promoBtnText: "Explore Harvest Inbox",
        btnAll: "All Dossiers",
        btnUser: "User Curated",
        btnAuto: "Auto Trends",
        sortLabel: "Sort:",
        sortOptions: [
          {{ val: "date-desc", text: "Latest Audit Date (Default)" }},
          {{ val: "date-asc", text: "Oldest Audit Date" }},
          {{ val: "score-desc", text: "Highest Confidence Score" }},
          {{ val: "title-asc", text: "Title (A to Z)" }}
        ],
        searchPlaceholder: "Search tech, architecture, or motivation...",
        domainLabel: "Domain:",
        tagAll: "All",
        tagFrontend: "Frontend",
        tagAgent: "AI Agents",
        tagScraping: "Scraping",
        tagDoc: "Docs/OCR",
        tag3d: "3D WebGL",
        tagRust: "Rust/Sys",
        tagOther: "Core Infra",
        cardMotivationLabel: "💡 Intent & Problem:",
        cardVerdictLabel: "⚡ Empirical Truth & Verdict:",
        cardConfidenceLabel: "Confidence",
        cardSourcesLabel: "Sources",
        cardViewBtn: "View Full Dossier",
        newsHeaderBadge: "GLOBAL AI INTELLIGENCE FEED",
        newsHeaderTitle: "AI Trends & Engineering Discourse from HackerNews & Communities",
        newsHeaderDesc: "Curated engineering analyses, security vulnerabilities, and architectural tutorials.",
        newsOriginalLink: "Read Source",
        graphHeaderBadge: "MULTI-ENTITY CITATION NETWORK",
        graphHeaderTitle: "Genealogy Map of AI Innovations via Citations",
        graphHeaderSub: "Tech • Researchers • Labs • Primary Papers",
        graphBtnAll: "Show All",
        graphBtnLang: "Language",
        graphBtnTech: "Tech / Engine",
        graphBtnOrg: "Laboratories",
        graphBtnPerson: "People",
        graphBtnPaper: "Papers",
        criteriaTitle: "Autonomous Cron Promotion Criteria Guide",
        criteriaDesc: "Repositories and papers exceeding these 4 viral thresholds are auto-promoted into the priority technical verification queue.",
        critGithub: "Created in last 14 days & > 500 Stars",
        critHn: "Top/Best stories with Score 🔥 > 150 Points",
        critHf: "Top Trending with ❤️ > 100 Likes",
        critArxiv: "Foundational papers on MoE, Reasoning, VLM",
        inboxHeaderBadge: "AUTONOMOUS HARVEST INBOX",
        inboxHeaderTitle: "Open-Source Repositories & Model Candidates Harvested 24/7",
        inboxHeaderDesc: "One-click queuing to sync with Neon Postgres DB and trigger automated verification.",
        inboxFamilyOn: "Family Grouping (ON)",
        inboxFamilyOff: "Family Grouping (OFF)",
        inboxSearchPlaceholder: "Search candidates or model names...",
        inboxQueueBtn: "Queue for Audit",
        inboxQueuedBtn: "Queued",
        modalSecCurationTitle: "Discovery Motivation & Target Workflow",
        modalSecViralPostTitle: "Raw Marketing Post & Claim Dossier",
        modalSecClaimsTitle: "Marketing Claims vs Empirical Reality",
        modalSecHookTitle: "The Hook & Marketing Hype",
        modalSecHandsOnTitle: "Hands-on Measured Results",
        modalSecAltsTitle: "Comparative Alternatives Matrix",
        modalSecSourcesTitle: "Audited Primary Sources",
        modalWorkflowLabel: "🎯 Target Workflow:",
        modalViralLinkText: "Open Original Post",
        thTool: "Tool / Tech",
        thStack: "Tech Stack",
        thPros: "Pros",
        thCons: "Cons",
        thBestFor: "Best For"
      }}
    }};

    // ================= VIEW SWITCHER (Clean 4 Tabs) =================
    function switchView(view) {{
      currentView = view;
      ['portfolio', 'news', 'graph', 'inbox'].forEach(v => {{
        const el = document.getElementById(v + 'View');
        const btn = document.getElementById('tab' + v.charAt(0).toUpperCase() + v.slice(1) + 'Btn');
        const mBtn = document.getElementById('mTab' + v.charAt(0).toUpperCase() + v.slice(1) + 'Btn');
        
        if (el) el.classList.toggle('hidden', v !== view);
        
        if (btn) {{
          if (v === view) {{
            btn.className = 'nav-tab active flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-white bg-ink-primary transition';
          }} else {{
            btn.className = 'nav-tab flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-ink-secondary hover:text-ink-primary transition';
          }}
        }}

        if (mBtn) {{
          if (v === view) {{
            mBtn.className = 'mobile-nav-tab active shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-ink-primary transition';
          }} else {{
            mBtn.className = 'mobile-nav-tab shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium text-ink-secondary hover:text-ink-primary bg-surface-subtle border border-surface-border transition';
          }}
        }}
      }});

      if (view === 'graph' && !simulationRef) {{
        initCitationGraph();
      }}
      lucide.createIcons();
    }}

    // ================= LANGUAGE TOGGLE & HIGH-FIDELITY CJK FONT SWITCHING =================
    function setLanguage(lang) {{
      currentLang = lang;
      
      // Dynamic Native Font Stack Switching
      if (lang === 'ZH') {{
        document.documentElement.lang = 'zh-CN';
        document.body.style.fontFamily = "'Noto Sans SC', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'SimHei', sans-serif";
      }} else if (lang === 'EN') {{
        document.documentElement.lang = 'en';
        document.body.style.fontFamily = "'Geist', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif";
      }} else {{
        document.documentElement.lang = 'ko';
        document.body.style.fontFamily = "'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif";
      }}

      ['KO', 'ZH', 'EN'].forEach(l => {{
        const btn = document.getElementById('lang' + l.charAt(0) + l.slice(1).toLowerCase() + 'Btn');
        if (btn) {{
          btn.className = l === lang ? 'px-2 py-0.5 rounded bg-ink-primary text-white transition text-[10px] sm:text-[11px]' : 'px-2 py-0.5 rounded text-ink-secondary hover:text-ink-primary transition text-[10px] sm:text-[11px]';
        }}
      }});
      
      const t = i18n[lang];
      document.getElementById('headerBrandTitle').innerText = t.brandTitle;
      document.getElementById('headerBrandSubtitle').innerText = t.brandSubtitle;
      document.getElementById('navTabPortfolio').innerText = t.navPortfolio;
      document.getElementById('mNavTabPortfolio').innerText = t.navPortfolio;
      document.getElementById('navTabNews').innerText = t.navNews;
      document.getElementById('navTabGraph').innerText = t.navGraph;
      document.getElementById('mNavTabGraph').innerText = t.navGraph;
      document.getElementById('navTabInbox').innerText = t.navInbox;

      document.getElementById('heroBadge').innerText = t.heroBadge;
      document.getElementById('heroMainTitle').innerText = t.heroMainTitle;
      document.getElementById('heroMainDesc').innerHTML = t.heroMainDesc;
      document.getElementById('heroUpdateLabel').innerText = t.heroUpdateLabel;
      document.getElementById('heroAuditCount').innerText = t.heroAuditCount;

      document.getElementById('promoBannerTitle').innerText = t.promoBannerTitle;
      document.getElementById('promoCountBadge').innerText = t.promoCountBadge;
      document.getElementById('promoBannerDesc').innerText = t.promoBannerDesc;
      document.getElementById('promoBtnText').innerText = t.promoBtnText;

      document.getElementById('criteriaTitle').innerText = t.criteriaTitle;
      document.getElementById('criteriaDesc').innerText = t.criteriaDesc;
      document.getElementById('critGithub').innerText = t.critGithub;
      document.getElementById('critHn').innerText = t.critHn;
      document.getElementById('critHf').innerText = t.critHf;
      document.getElementById('critArxiv').innerText = t.critArxiv;

      document.getElementById('btnLabelAll').innerText = t.btnAll;
      document.getElementById('btnLabelUser').innerText = t.btnUser;
      document.getElementById('btnLabelAuto').innerText = t.btnAuto;
      document.getElementById('sortLabel').innerText = t.sortLabel;
      document.getElementById('searchInput').placeholder = t.searchPlaceholder;
      document.getElementById('domainFilterLabel').innerText = t.domainLabel;

      document.getElementById('tagAll').innerText = t.tagAll;
      document.getElementById('tagFrontend').innerText = t.tagFrontend;
      document.getElementById('tagAgent').innerText = t.tagAgent;
      document.getElementById('tagScraping').innerText = t.tagScraping;
      document.getElementById('tagDoc').innerText = t.tagDoc;
      document.getElementById('tag3d').innerText = t.tag3d;
      document.getElementById('tagRust').innerText = t.tagRust;
      document.getElementById('tagOther').innerText = t.tagOther;

      // Update Sort Select Options
      const sortSel = document.getElementById('sortSelect');
      const curVal = sortSel.value;
      sortSel.innerHTML = t.sortOptions.map(opt => `<option value="${{opt.val}}" ${{opt.val === curVal ? 'selected' : ''}}>${{opt.text}}</option>`).join('');

      // Update Views
      renderCards();
      renderNews();
      renderInbox();
    }}

    // ================= REAL-TIME DB SYNC =================
    async function syncFromNeonLiveDB() {{
      try {{
        const resPort = await fetch('/api/portfolios');
        if (resPort.ok) {{
          const data = await resPort.json();
          if (data.success && data.portfolios && data.portfolios.length > 0) {{
            liveCasesData = data.portfolios;
            liveAnalysesData = data.technical_analyses || [];
            
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

        const resInbox = await fetch('/api/queue?all=true');
        if (resInbox.ok) {{
          const inData = await resInbox.json();
          if (inData.success && inData.items && inData.items.length > 0) {{
            liveInboxData = inData.items;
            renderInbox();
          }}
        }}

        const resNews = await fetch('/api/queue?type=NEWS');
        if (resNews.ok) {{
          const newsData = await resNews.json();
          if (newsData.success && newsData.news && newsData.news.length > 0) {{
            liveNewsData = newsData.news;
            renderNews();
          }}
        }}
      }} catch (err) {{}}
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
        if (btn.dataset.domain === dom) btn.classList.add('active');
        else btn.classList.remove('active');
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

    // ================= RENDER EXECUTIVE SCANNABLE CARDS =================
    function renderCards() {{
      const grid = document.getElementById('cardsGrid');
      grid.innerHTML = '';
      const t = i18n[currentLang];

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
        const fullTxt = (c.title + ' ' + (c.clustering?.cluster_name || '') + ' ' + cat).toLowerCase();

        let matchesDomain = true;
        if (currentDomain === 'frontend') {{
          matchesDomain = cat.includes('design') || cat.includes('frontend') || cat.includes('media') || cluster.includes('design') || cluster.includes('media') || fullTxt.includes('taste') || fullTxt.includes('concat');
        }} else if (currentDomain === 'agent') {{
          matchesDomain = cat.includes('agent') || cluster.includes('agent') || fullTxt.includes('openworker') || fullTxt.includes('praxist');
        }} else if (currentDomain === 'scraping') {{
          matchesDomain = cat.includes('scraping') || cat.includes('browser') || cluster.includes('scraping') || fullTxt.includes('watercrawl') || fullTxt.includes('obscura');
        }} else if (currentDomain === 'doc') {{
          matchesDomain = cat.includes('doc') || cat.includes('ocr') || cluster.includes('doc') || fullTxt.includes('docling') || fullTxt.includes('anydoc');
        }} else if (currentDomain === '3d') {{
          matchesDomain = cat.includes('3d') || cat.includes('graphics') || cluster.includes('3d') || fullTxt.includes('three');
        }} else if (currentDomain === 'rust') {{
          matchesDomain = fullTxt.includes('rust') || fullTxt.includes('omarchy') || fullTxt.includes('serverbox');
        }} else if (currentDomain === 'other') {{
          const isStandard = cat.includes('design') || cat.includes('frontend') || cat.includes('media') || cat.includes('agent') || cat.includes('scraping') || cat.includes('doc') || cat.includes('3d') || fullTxt.includes('rust');
          matchesDomain = !isStandard;
        }}

        const story = c.portfolio_story || {{}};
        const searchTxt = (c.title + ' ' + (c.title_zh || '') + ' ' + (c.title_en || '') + ' ' + cat + ' ' + (story.the_hook || '') + ' ' + (c.curation?.personal_motivation || '')).toLowerCase();
        const matchesSearch = searchTxt.includes(searchQuery.toLowerCase());

        return matchesMode && matchesDomain && matchesSearch;
      }});

      // Sort
      filtered.sort((a, b) => {{
        if (currentSort === 'date-desc') return (b.investigation_date || '').localeCompare(a.investigation_date || '');
        if (currentSort === 'date-asc') return (a.investigation_date || '').localeCompare(b.investigation_date || '');
        if (currentSort === 'score-desc') return (b.confidence_score || 0) - (a.confidence_score || 0);
        if (currentSort === 'title-asc') return (a.title || '').localeCompare(b.title || '');
        return 0;
      }});

      document.getElementById('resultsCountLabel').innerText = currentLang === 'KO' ? `총 ${{filtered.length}}건 표시 (전체 ${{liveCasesData.length}}건 중)` : (currentLang === 'ZH' ? `显示 ${{filtered.length}} 项 (共 ${{liveCasesData.length}} 项)` : `Showing ${{filtered.length}} of ${{liveCasesData.length}} dossiers`);

      if (filtered.length === 0) {{
        grid.innerHTML = `<div class="col-span-full py-16 text-center text-ink-muted font-medium">${{currentLang === 'KO' ? '일치하는 기술 검증 보고서가 없습니다.' : (currentLang === 'ZH' ? '未找到符合条件的技术核查报告。' : 'No matching fact-check dossiers found.')}}</div>`;
        return;
      }}

      // Render Executive Scannable Cards (All 18 Completed Portfolios)
      filtered.forEach((c, idx) => {{
        const story = c.portfolio_story || {{}};
        const curation = c.curation || {{ discovery_mode: 'USER_CURATED' }};
        const isUserMode = curation.discovery_mode === 'USER_CURATED';
        const invDate = c.investigation_date || '2026-09-02';
        const confScore = c.confidence_score || 95.0;
        const isVerifiedTrue = c.verdict === 'VERIFIED_TRUE';
        const isHalfTrue = c.verdict.includes('HALF');

        let displayTitle = c.title;
        let displayMotivation = curation.personal_motivation || story.the_hook || '';
        let displayTruth = story.the_hook || 'Empirical benchmark completed.';

        if (currentLang === 'ZH') {{
          displayTitle = c.title_zh || c.title;
          displayMotivation = curation.personal_motivation_zh || displayMotivation;
          displayTruth = story.the_hook_zh || displayTruth;
        }} else if (currentLang === 'EN') {{
          displayTitle = c.title_en || c.title;
          displayMotivation = curation.personal_motivation_en || displayMotivation;
          displayTruth = story.the_hook_en || displayTruth;
        }}

        // Verdict Badge for Completed Portfolios
        let verdictLabel = '';
        let verdictClass = '';
        let dotClass = '';

        if (isVerifiedTrue) {{
          verdictLabel = currentLang === 'KO' ? '사실 검증됨' : (currentLang === 'ZH' ? '经实测属实' : 'VERIFIED TRUE');
          verdictClass = 'verdict-true';
          dotClass = 'bg-emerald-600';
        }} else if (isHalfTrue) {{
          verdictLabel = currentLang === 'KO' ? '절반의 사실' : (currentLang === 'ZH' ? '部分属实' : 'HALF TRUE');
          verdictClass = 'verdict-half';
          dotClass = 'bg-amber-600';
        }} else {{
          verdictLabel = currentLang === 'KO' ? '과장/왜곡' : (currentLang === 'ZH' ? '夸大/失真' : 'EXAGGERATED');
          verdictClass = 'verdict-gamed';
          dotClass = 'bg-rose-600';
        }}

        const card = document.createElement('div');
        card.className = 'executive-card p-6 flex flex-col justify-between cursor-pointer space-y-4 group';
        card.onclick = () => openModal(c);

        card.innerHTML = `
          <div class="space-y-3.5">
            
            <!-- Tier 1: Header Meta (ID + Mode Badge + Date + Verdict) -->
            <div class="flex items-center justify-between text-xs gap-2 flex-wrap">
              <div class="flex items-center gap-2">
                <span class="text-xs font-mono font-bold text-ink-muted">#${{String(idx + 1).padStart(2, '0')}}</span>
                <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold font-mono bg-indigo-50 text-indigo-700 border border-indigo-200">
                  ${{currentLang === 'KO' ? '기술 검증 리포트' : (currentLang === 'ZH' ? '技术核验报告' : 'AUDITED DOSSIER')}}
                </span>
                <span class="text-ink-muted text-[11px] font-mono">${{invDate}}</span>
              </div>

              <!-- Verdict Pill Badge -->
              <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold font-mono flex items-center gap-1.5 ${{verdictClass}}">
                <span class="w-1.5 h-1.5 rounded-full ${{dotClass}}"></span>
                ${{verdictLabel}}
              </span>
            </div>

            <!-- Tier 2: Bold Headline -->
            <div class="space-y-1">
              <span class="text-[11px] text-ink-muted font-mono font-semibold uppercase tracking-wider">${{c.category || 'AI Technology'}}</span>
              <h3 class="font-bold text-base text-ink-primary group-hover:text-indigo-600 transition leading-snug">
                ${{displayTitle}}
              </h3>
            </div>

            <!-- Tier 3: 2-Tier Structured Scannable Block (Motivation vs Truth) -->
            <div class="space-y-2 pt-1">
              <!-- Block 1: Problem / Motivation -->
              <div class="p-3 rounded-xl bg-surface-subtle border border-surface-border text-xs space-y-1">
                <div class="text-[11px] font-bold text-ink-secondary flex items-center gap-1.5">
                  <i data-lucide="compass" class="w-3.5 h-3.5 text-indigo-600"></i> ${{t.cardMotivationLabel}}
                </div>
                <p class="text-xs text-ink-secondary leading-relaxed line-clamp-2">${{displayMotivation}}</p>
              </div>

              <!-- Block 2: Key Verdict / Truth -->
              <div class="p-3 rounded-xl bg-emerald-50/70 border border-emerald-200 text-xs space-y-1">
                <div class="text-[11px] font-bold text-emerald-900 flex items-center gap-1.5">
                  <i data-lucide="zap" class="w-3.5 h-3.5 text-emerald-700"></i> ${{t.cardVerdictLabel}}
                </div>
                <p class="text-xs text-emerald-950 leading-relaxed font-medium line-clamp-2">${{displayTruth}}</p>
              </div>
            </div>

          </div>

          <!-- Tier 4: Footer Metrics & Action -->
          <div class="pt-3 border-t border-surface-border flex items-center justify-between text-xs">
            <div class="flex items-center gap-3">
              <span class="text-emerald-700 font-mono font-bold text-xs flex items-center gap-1">
                <i data-lucide="shield-check" class="w-3.5 h-3.5"></i> ${{t.cardConfidenceLabel}} ${{confScore.toFixed(1)}}%
              </span>
              <span class="text-surface-border">•</span>
              <span class="text-ink-muted text-[11px] font-mono">${{(c.sources || []).length}}${{t.cardSourcesLabel}}</span>
            </div>

            <button class="text-ink-primary font-bold text-xs group-hover:translate-x-0.5 transition flex items-center gap-1">
              ${{t.cardViewBtn}} <i data-lucide="arrow-right" class="w-3.5 h-3.5 text-ink-primary"></i>
            </button>
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
      const rawPost = c.raw_viral_post || {{}};
      const t = i18n[currentLang];

      let displayTitle = c.title;
      let displayMotivation = curation.personal_motivation || story.the_hook || '';
      let displayQuote = rawPost.quote || '';

      if (currentLang === 'ZH') {{
        displayTitle = c.title_zh || c.title;
        displayMotivation = curation.personal_motivation_zh || displayMotivation;
        displayQuote = rawPost.quote_zh || displayQuote;
      }} else if (currentLang === 'EN') {{
        displayTitle = c.title_en || c.title;
        displayMotivation = curation.personal_motivation_en || displayMotivation;
      }}

      document.getElementById('modalTitle').innerText = displayTitle;
      document.getElementById('modalModeBadge').innerText = currentLang === 'KO' ? '기술 검증 리포트' : (currentLang === 'ZH' ? '技术核验报告' : 'AUDITED DOSSIER');
      document.getElementById('modalModeBadge').className = 'text-xs px-2.5 py-0.5 rounded-md font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200';
      
      document.getElementById('modalClusterBadge').innerText = clustering.cluster_name || c.category || 'Tech';
      document.getElementById('modalVerdictBadge').innerText = c.verdict;
      document.getElementById('modalVerdictBadge').className = c.verdict === 'VERIFIED_TRUE' ? 'text-xs px-2.5 py-0.5 rounded-md font-semibold verdict-true' : 'text-xs px-2.5 py-0.5 rounded-md font-semibold verdict-half';
      document.getElementById('modalStageBadge').innerText = handsOn.status === 'ACTIVE_DEVELOPED' ? (currentLang === 'KO' ? '실제 개발 적용' : (currentLang === 'ZH' ? '生产级落地' : 'Production Active')) : (currentLang === 'KO' ? '기술 조사 완료' : (currentLang === 'ZH' ? '已审计完毕' : 'Audited'));

      document.getElementById('modalMotivation').innerText = displayMotivation;
      document.getElementById('modalWorkflow').innerText = curation.target_workflow || 'Universal AI Pipeline';

      // 🌟 VIRAL CLAIMS DOSSIER (Hides cleanly when quote is missing)
      const viralBox = document.getElementById('modalViralPostBox');
      const hasQuote = displayQuote && displayQuote.trim().length > 0;

      if (hasQuote) {{
        viralBox.classList.remove('hidden');
        document.getElementById('modalSecViralPostTitle').innerText = t.modalSecViralPostTitle;
        document.getElementById('modalViralPlatformBadge').innerText = rawPost.platform || 'Social Post';
        document.getElementById('modalViralAuthor').innerText = (rawPost.author ? (rawPost.author + ' : ') : '') + (rawPost.screenshot_note || 'Viral Marketing Post Evidence');
        document.getElementById('modalViralQuote').innerText = `"${{displayQuote}}"`;
        document.getElementById('modalViralNote').innerText = rawPost.screenshot_note || '';
        document.getElementById('modalViralLinkText').innerText = t.modalViralLinkText;
        
        const directLink = document.getElementById('modalViralDirectLink');
        if (rawPost.post_url) {{
          directLink.href = rawPost.post_url;
          directLink.classList.remove('hidden');
        }} else if (c.sources && c.sources.length > 0) {{
          directLink.href = c.sources[0].url;
          directLink.classList.remove('hidden');
        }} else {{
          directLink.classList.add('hidden');
        }}
      }} else {{
        viralBox.classList.add('hidden');
      }}

      document.getElementById('modalHook').innerText = (currentLang === 'ZH' && story.the_hook_zh) ? story.the_hook_zh : (story.the_hook || '');
      document.getElementById('modalHype').innerText = story.marketing_hype_anatomy ? ((currentLang === 'KO' ? '과장 마케팅 해부: ' : (currentLang === 'ZH' ? '营销炒作解构: ' : 'Marketing Hype Anatomy: ')) + story.marketing_hype_anatomy) : '';
      
      document.getElementById('modalHandsOnEnv').innerText = handsOn.test_environment ? ((currentLang === 'KO' ? '환경: ' : (currentLang === 'ZH' ? '实测环境: ' : 'Env: ')) + handsOn.test_environment) : '';
      document.getElementById('modalHandsOnMetrics').innerText = handsOn.measured_results ? ((currentLang === 'KO' ? '실측치: ' : (currentLang === 'ZH' ? '实测指标: ' : 'Metrics: ')) + handsOn.measured_results) : '';
      document.getElementById('modalHandsOnDetails').innerText = handsOn.details || 'Empirical benchmark verified.';

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
            <div class="text-ink-secondary font-medium">${{currentLang === 'KO' ? '검증 팩트:' : (currentLang === 'ZH' ? '事实核验:' : 'Verified Fact:')}} ${{cl.fact_checked_truth || cl.verification_evidence || ''}}</div>
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
        altBody.innerHTML = `<tr><td colspan="5" class="p-4 text-center text-ink-muted">${{currentLang === 'KO' ? '등록된 대체 기술 비교 데이터가 없습니다.' : (currentLang === 'ZH' ? '暂无替代方案对比数据。' : 'No comparative alternatives registered.')}}</td></tr>`;
      }}

      // Sources
      const sourcesList = document.getElementById('modalSourcesList');
      const sources = c.sources || [];
      sourcesList.innerHTML = sources.map(s => `
        <a href="${{s.url}}" target="_blank" class="p-2.5 rounded-xl bg-surface-subtle border border-surface-border hover:border-ink-primary flex items-center justify-between text-xs text-ink-secondary hover:text-ink-primary transition">
          <div class="space-y-0.5">
            <span class="text-[10px] font-mono text-ink-primary uppercase font-bold">${{s.tier || 'Tier 1'}} • ${{s.type || 'Repository'}}</span>
            <div class="font-medium truncate max-w-[240px] text-ink-primary">${{s.name || s.title || 'Source Link'}}</div>
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
      const t = i18n[currentLang];

      const newsItems = liveNewsData || [];
      if (newsItems.length === 0) {{
        grid.innerHTML = `<div class="col-span-full py-16 text-center text-ink-muted font-medium">${{currentLang === 'KO' ? '수집된 AI 뉴스가 없습니다.' : (currentLang === 'ZH' ? '暂无采集到的 AI 资讯。' : 'No AI news articles available.')}}</div>`;
        return;
      }}

      newsItems.forEach(it => {{
        const card = document.createElement('div');
        card.className = 'executive-card p-5 flex flex-col justify-between space-y-4';

        const displayTitle = currentLang === 'KO' && it.title_ko ? it.title_ko : it.title;
        const displayDesc = currentLang === 'KO' && it.description_ko ? it.description_ko : (it.description || '');

        card.innerHTML = `
          <div class="space-y-2.5">
            <div class="flex items-center justify-between text-xs font-mono">
              <span class="px-2 py-0.5 rounded bg-surface-subtle text-ink-primary font-bold border border-surface-border text-[11px]">
                ${{it.source_platform || 'Tech News'}}
              </span>
              <span class="text-ink-muted text-[11px]">${{it.viral_metric || ''}}</span>
            </div>

            <h3 class="font-bold text-sm text-ink-primary hover:text-indigo-600 transition leading-snug">
              ${{displayTitle}}
            </h3>

            <p class="text-xs text-ink-secondary leading-relaxed line-clamp-3">
              ${{displayDesc}}
            </p>
          </div>

          <div class="pt-3 border-t border-surface-border flex items-center justify-between text-xs">
            <span class="text-ink-muted text-[11px] font-mono">${{it.harvested_date || '2026-09-02'}}</span>
            <a href="${{it.source_url}}" target="_blank" class="text-ink-primary hover:underline font-semibold flex items-center gap-1">
              ${{t.newsOriginalLink}} <i data-lucide="external-link" class="w-3 h-3"></i>
            </a>
          </div>
        `;
        grid.appendChild(card);
      }});

      lucide.createIcons();
    }}

    // ================= INBOX VIEW (DEDUP REGISTRY & GROUPING) =================
    function toggleFamilyGrouping() {{
      isFamilyGroupingActive = !isFamilyGroupingActive;
      const btn = document.getElementById('groupByFamilyBtn');
      const text = document.getElementById('groupByFamilyText');
      const t = i18n[currentLang];
      
      if (isFamilyGroupingActive) {{
        btn.className = 'flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold bg-ink-primary text-white transition shrink-0';
        text.innerText = t.inboxFamilyOn;
      }} else {{
        btn.className = 'flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold bg-surface-subtle text-ink-primary border border-surface-border hover:bg-white transition shrink-0';
        text.innerText = t.inboxFamilyOff;
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
      const t = i18n[currentLang];

      const filtered = liveInboxData.filter(item => {{
        const isNotNews = item.category_type !== 'NEWS';
        const matchesSrc = currentInboxSource === 'ALL' || (item.source_platform && item.source_platform.includes(currentInboxSource));
        const text = (item.title + ' ' + (item.title_ko || '') + ' ' + (item.description || '') + ' ' + (item.model_family || '') + ' ' + (item.variant_role || '')).toLowerCase();
        const matchesSearch = text.includes(inboxSearchQuery.toLowerCase());
        return isNotNews && matchesSrc && matchesSearch;
      }});

      if (filtered.length === 0) {{
        grid.innerHTML = `<div class="col-span-full py-16 text-center text-ink-muted font-medium">${{currentLang === 'KO' ? '수집된 인박스 후보가 없습니다.' : (currentLang === 'ZH' ? '收件箱暂无候选数据。' : 'No candidates in the inbox.')}}</div>`;
        return;
      }}

      if (isFamilyGroupingActive) {{
        const groups = {{}};
        filtered.forEach(it => {{
          const fam = it.model_family || (currentLang === 'KO' ? '독립 모델 (Standalone / Novel)' : (currentLang === 'ZH' ? '独立模型 (Standalone / Novel)' : 'Standalone / Novel Models'));
          if (!groups[fam]) groups[fam] = [];
          groups[fam].push(it);
        }});

        const sortedFamNames = Object.keys(groups).sort((a, b) => {{
          if (a.includes('Standalone') || a.includes('독립') || a.includes('独立')) return 1;
          if (b.includes('Standalone') || b.includes('독립') || b.includes('独立')) return -1;
          return groups[b].length - groups[a].length;
        }});

        sortedFamNames.forEach(famName => {{
          const items = groups[famName];
          const groupCard = document.createElement('div');
          groupCard.className = 'col-span-full executive-card p-6 border-surface-border space-y-4 shadow-sm';

          let subItemsHtml = '';
          items.forEach(it => {{
            const isQueued = queuedItemIds.has(it.inbox_id);
            const displayTitle = currentLang === 'KO' && it.title_ko ? it.title_ko : it.title;
            const roleBadge = it.variant_role || 'Standard';

            subItemsHtml += `
              <div class="bg-surface-subtle p-4 rounded-xl border border-surface-border flex flex-col justify-between space-y-3 hover:border-ink-primary transition">
                <div class="space-y-2">
                  <div class="flex items-center justify-between text-[11px] font-mono">
                    <span class="text-ink-primary font-bold">${{it.source_platform || 'Hub'}}</span>
                    <span class="text-ink-muted">${{it.viral_metric || ''}}</span>
                  </div>
                  
                  <div class="px-2 py-0.5 rounded text-[10px] font-semibold font-mono bg-white text-ink-primary border border-surface-border inline-block">
                    ${{roleBadge}}
                  </div>

                  <h4 class="font-bold text-xs text-ink-primary line-clamp-2 leading-relaxed">${{displayTitle}}</h4>
                  
                  <div class="text-[10px] text-ink-muted font-mono">
                    ${{currentLang === 'KO' ? '제작자:' : (currentLang === 'ZH' ? '创作者:' : 'Creator:')}} <span class="text-ink-primary font-semibold">${{it.creator || 'Community'}}</span>
                  </div>
                </div>

                <div class="pt-2.5 border-t border-surface-border flex items-center justify-between gap-2">
                  <a href="${{it.source_url}}" target="_blank" class="text-[11px] text-ink-secondary hover:text-ink-primary flex items-center gap-0.5 shrink-0 font-medium">
                    ${{currentLang === 'KO' ? '원문' : (currentLang === 'ZH' ? '原文' : 'Source')}} <i data-lucide="external-link" class="w-2.5 h-2.5"></i>
                  </a>
                  
                  <button onclick="toggleQueueItem('${{it.inbox_id}}', '${{displayTitle.replace(/'/g, "")}}')" 
                          class="px-2.5 py-1 rounded-lg text-[10px] font-bold transition flex items-center gap-1 ${{isQueued ? 'bg-emerald-700 text-white font-black' : 'bg-white text-ink-primary hover:bg-ink-primary hover:text-white border border-surface-border'}}">
                    <i data-lucide="${{isQueued ? 'check' : 'zap'}}" class="w-3 h-3"></i>
                    ${{isQueued ? t.inboxQueuedBtn : t.inboxQueueBtn}}
                  </button>
                </div>
              </div>
            `;
          }});

          groupCard.innerHTML = `
            <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-surface-border gap-3">
              <div class="flex items-center gap-2.5 flex-wrap">
                <span class="px-2.5 py-0.5 rounded-md bg-surface-subtle text-ink-primary text-xs font-mono font-bold border border-surface-border flex items-center gap-1">
                  <i data-lucide="layers" class="w-3.5 h-3.5"></i> Model Family
                </span>
                <h3 class="text-base font-bold text-ink-primary">${{famName}}</h3>
                <span class="text-xs px-2 py-0.5 rounded bg-white text-ink-secondary border border-surface-border font-mono font-bold">${{items.length}}${{currentLang === 'KO' ? '개 파생 모델' : (currentLang === 'ZH' ? ' 个衍生模型' : ' Variants')}}</span>
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
              ${{subItemsHtml}}
            </div>
          `;
          grid.appendChild(groupCard);
        }});
      }} else {{
        filtered.forEach(it => {{
          const isQueued = queuedItemIds.has(it.inbox_id);
          const displayTitle = currentLang === 'KO' && it.title_ko ? it.title_ko : it.title;
          const displayDesc = currentLang === 'KO' && it.description_ko ? it.description_ko : (it.description || '');

          const card = document.createElement('div');
          card.className = 'executive-card p-5 flex flex-col justify-between space-y-3.5';

          card.innerHTML = `
            <div class="space-y-2.5">
              <div class="flex items-center justify-between text-xs font-mono">
                <span class="px-2 py-0.5 rounded bg-surface-subtle text-ink-primary font-bold border border-surface-border text-[11px]">
                  ${{it.source_platform || 'Tech Hub'}}
                </span>
                <span class="text-ink-muted text-[11px]">${{it.viral_metric || ''}}</span>
              </div>

              <h3 class="font-bold text-sm text-ink-primary leading-snug">
                ${{displayTitle}}
              </h3>

              <p class="text-xs text-ink-secondary leading-relaxed line-clamp-3">
                ${{displayDesc}}
              </p>

              <div class="text-[11px] text-ink-muted font-mono pt-1">
                ${{currentLang === 'KO' ? '제작자:' : (currentLang === 'ZH' ? '创作者:' : 'Creator:')}} <span class="text-ink-primary font-semibold">${{it.creator || 'Community'}}</span>
              </div>
            </div>

            <div class="pt-3 border-t border-surface-border flex items-center justify-between gap-2">
              <a href="${{it.source_url}}" target="_blank" class="text-xs text-ink-secondary hover:text-ink-primary flex items-center gap-1 font-medium">
                ${{currentLang === 'KO' ? '원문 링크' : (currentLang === 'ZH' ? '原文链接' : 'Source Link')}} <i data-lucide="external-link" class="w-3 h-3"></i>
              </a>

              <button onclick="toggleQueueItem('${{it.inbox_id}}', '${{displayTitle.replace(/'/g, "")}}')" 
                      class="px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1.5 ${{isQueued ? 'bg-emerald-700 text-white font-black' : 'bg-surface-subtle text-ink-primary hover:bg-ink-primary hover:text-white border border-surface-border'}}">
                <i data-lucide="${{isQueued ? 'check' : 'zap'}}" class="w-3.5 h-3.5"></i>
                ${{isQueued ? t.inboxQueuedBtn : t.inboxQueueBtn}}
              </button>
            </div>
          `;
          grid.appendChild(card);
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
        return "#111827";
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
        .attr("font-family", "Pretendard, Noto Sans SC, sans-serif")
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
