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
import time
import datetime

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
    def is_news_item(it):
        ai = it.get("ai_enrichment") or {}
        cat = it.get("category_type", "")
        return cat == "NEWS" or ai.get("type_classification") == "NEWS"

    def is_model_item(it):
        ai = it.get("ai_enrichment") or {}
        cat = it.get("category_type", "")
        src = it.get("source_platform", "")
        fam = it.get("model_family", "")
        return (
            ai.get("type_classification") == "MODEL" or 
            cat == "model" or 
            "Models" in src or 
            "Spaces" in src or
            (fam and "General" not in fam and "독립" not in fam and "Harness" not in fam)
        )

    # Set of verified case IDs and URLs to exclude from pending inbox
    verified_case_urls = set()
    verified_case_ids = set()
    for c in cases:
        verified_case_ids.add(c.get("case_id"))
        p_url = c.get("raw_viral_post", {}).get("post_url")
        if p_url: verified_case_urls.add(p_url.rstrip("/"))
        for s in c.get("sources", []):
            if s.get("url"): verified_case_urls.add(s.get("url").rstrip("/"))

    def is_already_verified(it):
        if it.get("status") == "FACT_CHECKED":
            return True
        rel_case = it.get("related_dossier", {}).get("case_id")
        if rel_case and rel_case in verified_case_ids:
            return True
        s_url = (it.get("source_url") or "").rstrip("/")
        if s_url and s_url in verified_case_urls:
            return True
        return False

    news_items = [it for it in inbox_items if is_news_item(it)]
    model_items = [it for it in inbox_items if is_model_item(it) and not is_news_item(it)]
    # All active unverified inbox candidates (only excludes already verified & promoted dossiers)
    clean_inbox_items = [
        it for it in inbox_items 
        if not is_already_verified(it)
    ]

    # Calculate Verdict & Quality Statistics
    verified_true_count = len([c for c in cases if c.get("verdict") == "VERIFIED_TRUE"])
    half_true_count = len([c for c in cases if "HALF" in (c.get("verdict") or "")])
    gamed_count = len([c for c in cases if "GAMED" in (c.get("verdict") or "") or "EXAGGERATED" in (c.get("verdict") or "")])
    avg_conf = round(sum(c.get("confidence_score", 90.0) for c in cases) / max(1, len(cases)), 1)

    summary_data = {
        "generated_at": datetime.date.today().strftime("%Y-%m-%d"),
        "total_cases": total_cases,
        "verified_true_count": verified_true_count,
        "half_true_count": half_true_count,
        "gamed_count": gamed_count,
        "avg_confidence": avg_conf,
        "models_total_count": len(model_items),
        "news_total_count": len(news_items),
        "inbox_total_count": len(clean_inbox_items),
        "all_inbox_count": len(inbox_items),
        "admin_stats": admin_stats,
        "model_items": model_items,
        "news_items": news_items,
        "inbox_items": clean_inbox_items,
        "cases": cases,
        "graph": graph_data
    }

    # Write data.json
    for target_dir in [dash_dir, docs_dir, base_dir, public_dir]:
        json_path = os.path.join(target_dir, "data.json")
        for _ in range(3):
            try:
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(summary_data, f, indent=2, ensure_ascii=False)
                break
            except Exception:
                time.sleep(0.5)

    # Generate HTML
    html_content = generate_html(summary_data)
    for target_dir in [dash_dir, docs_dir, base_dir, public_dir]:
        html_path = os.path.join(target_dir, "index.html")
        for _ in range(3):
            try:
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                break
            except Exception:
                time.sleep(0.5)

    print(f"[+] Successfully built Full 18 Dossiers Dashboard v20.0 at:")
    print(f"    - public/index.html & data.json (Vercel CDN Edge)")
    print(f"    - dashboard/index.html (Verified: {total_cases}, Models: {len(model_items)}, News: {len(news_items)}, Inbox: {len(clean_inbox_items)})")
    print(f"    - docs/index.html (GitHub Pages hosting)")

def generate_html(data):
    cases_json = json.dumps(data["cases"], ensure_ascii=False)
    inbox_json = json.dumps(data["inbox_items"], ensure_ascii=False)
    admin_json = json.dumps(data["admin_stats"], ensure_ascii=False)
    graph_json = json.dumps(data["graph"], ensure_ascii=False)
    models_json = json.dumps(data.get("model_items", []), ensure_ascii=False)
    news_json = json.dumps(data.get("news_items", []), ensure_ascii=False)
    
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="referrer" content="no-referrer">
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

      <!-- Desktop Navigation Tabs (Clean 5 Core Tabs) -->
      <nav class="hidden md:flex items-center gap-1 bg-surface-subtle p-1 rounded-xl border border-surface-border text-xs font-semibold">
        <button onclick="switchView('portfolio')" id="tabPortfolioBtn" class="nav-tab active flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-white bg-ink-primary transition">
          <i data-lucide="check-circle-2" class="w-3.5 h-3.5"></i>
          <span id="navTabPortfolio">기술 검증</span>
          <span class="text-[10px] font-mono text-ink-muted" id="headerVerifiedCount">({data['total_cases']})</span>
        </button>
        <button onclick="switchView('models')" id="tabModelsBtn" class="nav-tab flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-ink-secondary hover:text-ink-primary transition">
          <i data-lucide="cpu" class="w-3.5 h-3.5"></i>
          <span id="navTabModels">AI 모델</span>
          <span class="text-[10px] font-mono text-ink-muted" id="headerModelsCount">({data['models_total_count']})</span>
        </button>
        <button onclick="switchView('news')" id="tabNewsBtn" class="nav-tab flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-ink-secondary hover:text-ink-primary transition">
          <i data-lucide="newspaper" class="w-3.5 h-3.5"></i>
          <span id="navTabNews">AI 뉴스</span>
          <span class="text-[10px] font-mono text-ink-muted" id="headerNewsCount">({data['news_total_count']})</span>
        </button>
        <button onclick="switchView('graph')" id="tabGraphBtn" class="nav-tab flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-ink-secondary hover:text-ink-primary transition">
          <i data-lucide="network" class="w-3.5 h-3.5"></i>
          <span id="navTabGraph">인용 계보망</span>
        </button>
        <button onclick="switchView('inbox')" id="tabInboxBtn" class="nav-tab flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-ink-secondary hover:text-ink-primary transition">
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
        <span class="text-[10px] font-mono text-ink-muted" id="mHeaderVerifiedCount">({data['total_cases']})</span>
      </button>
      <button onclick="switchView('models')" id="mTabModelsBtn" class="mobile-nav-tab shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium text-ink-secondary hover:text-ink-primary bg-surface-subtle border border-surface-border transition">
        <i data-lucide="cpu" class="w-3.5 h-3.5"></i>
        <span id="mNavTabModels">AI 모델 ({data['models_total_count']})</span>
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
          <div class="text-base font-bold text-ink-primary font-mono">{data['generated_at']}</div>
          <div class="text-[11px] text-emerald-700 font-semibold mt-0.5" id="heroAuditCount">{data['total_cases']}개 기술 검증 완료</div>
        </div>
      </div>

      <!-- 🌟 REAL-TIME TELEMETRY & INTELLIGENCE KPI OVERVIEW (실시간 대시보드 종합 통계) -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-3.5 sm:gap-4">
        
        <!-- Metric 1: Verified Dossiers -->
        <div onclick="switchView('portfolio')" class="bg-white p-4 sm:p-5 rounded-2xl border border-surface-border hover:border-emerald-500 hover:shadow-md transition cursor-pointer group">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-ink-muted group-hover:text-emerald-700 transition flex items-center gap-1.5" id="statLabelVerified">
              <i data-lucide="shield-check" class="w-4 h-4 text-emerald-600"></i>
              <span>공식 기술 검증</span>
            </span>
            <span class="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
              Avg {data['avg_confidence']}%
            </span>
          </div>
          <div class="mt-3 flex items-baseline gap-2">
            <span class="text-2xl sm:text-3xl font-black text-ink-primary font-mono" id="statValVerified">{data['total_cases']}</span>
            <span class="text-xs text-ink-muted font-medium">Dossiers</span>
          </div>
          <div class="mt-2 text-[11px] text-ink-secondary flex items-center gap-2 font-mono">
            <span class="text-emerald-700 font-bold" title="사실 검증">● {data['verified_true_count']} 사실</span>
            <span class="text-amber-700 font-bold" title="절반의 사실">● {data['half_true_count']} 부분</span>
            <span class="text-rose-700 font-bold" title="과장/왜곡">● {data['gamed_count']} 과장</span>
          </div>
        </div>

        <!-- Metric 2: Live Harvested Inbox -->
        <div onclick="switchView('inbox')" class="bg-white p-4 sm:p-5 rounded-2xl border border-surface-border hover:border-indigo-500 hover:shadow-md transition cursor-pointer group">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-ink-muted group-hover:text-indigo-600 transition flex items-center gap-1.5" id="statLabelInbox">
              <i data-lucide="inbox" class="w-4 h-4 text-indigo-600"></i>
              <span>수집 인박스</span>
            </span>
            <span class="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
              ⚡ 3h 주기 KST
            </span>
          </div>
          <div class="mt-3 flex items-baseline gap-2">
            <span class="text-2xl sm:text-3xl font-black text-ink-primary font-mono" id="statValInbox">{data['inbox_total_count']}</span>
            <span class="text-xs text-ink-muted font-medium">Candidates</span>
          </div>
          <p class="mt-2 text-[11px] text-ink-secondary truncate" id="statDescInbox">
            HN · GeekNews · GitHub · HF 24/7 수집
          </p>
        </div>

        <!-- Metric 3: Trending AI Models -->
        <div onclick="switchView('models')" class="bg-white p-4 sm:p-5 rounded-2xl border border-surface-border hover:border-purple-500 hover:shadow-md transition cursor-pointer group">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-ink-muted group-hover:text-purple-600 transition flex items-center gap-1.5" id="statLabelModels">
              <i data-lucide="cpu" class="w-4 h-4 text-purple-600"></i>
              <span>추적 AI 모델</span>
            </span>
            <span class="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-purple-50 text-purple-700 border border-purple-200">
              SOTA 가중치
            </span>
          </div>
          <div class="mt-3 flex items-baseline gap-2">
            <span class="text-2xl sm:text-3xl font-black text-ink-primary font-mono" id="statValModels">{data['models_total_count']}</span>
            <span class="text-xs text-ink-muted font-medium">Models</span>
          </div>
          <p class="mt-2 text-[11px] text-ink-secondary truncate" id="statDescModels">
            MoE, VLM, 추론 특화 오픈 가중치
          </p>
        </div>

        <!-- Metric 4: AI News & Industry Reports -->
        <div onclick="switchView('news')" class="bg-white p-4 sm:p-5 rounded-2xl border border-surface-border hover:border-amber-500 hover:shadow-md transition cursor-pointer group">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-ink-muted group-hover:text-amber-700 transition flex items-center gap-1.5" id="statLabelNews">
              <i data-lucide="newspaper" class="w-4 h-4 text-amber-600"></i>
              <span>AI 테크 동향</span>
            </span>
            <span class="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-amber-50 text-amber-800 border border-amber-200">
              글로벌 토픽
            </span>
          </div>
          <div class="mt-3 flex items-baseline gap-2">
            <span class="text-2xl sm:text-3xl font-black text-ink-primary font-mono" id="statValNews">{data['news_total_count']}</span>
            <span class="text-xs text-ink-muted font-medium">Articles</span>
          </div>
          <p class="mt-2 text-[11px] text-ink-secondary truncate" id="statDescNews">
            CVE 취약점, 인프라 장애, 아키텍처 토론
          </p>
        </div>

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
                <option value="date-source-desc">📅 수집/원출처 최신순 (기본)</option>
                <option value="date-source-asc">📅 수집/원출처 오래된순</option>
                <option value="date-audit-desc">🔬 분석일자 최신순</option>
                <option value="date-audit-asc">🔬 분석일자 오래된순</option>
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

    <!-- ==================== VIEW: AI MODELS REGISTRY ==================== -->
    <div id="modelsView" class="hidden space-y-6">
      <!-- Models Header -->
      <div class="bg-white p-6 rounded-2xl border border-surface-border flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-sm">
        <div class="space-y-1">
          <div class="flex items-center gap-2">
            <span class="px-2.5 py-0.5 rounded-md bg-surface-subtle text-ink-primary text-xs font-mono font-bold border border-surface-border" id="modelsHeaderBadge">
              AI MODEL REGISTRY & FAMILIES
            </span>
            <span class="text-xs text-ink-muted font-mono" id="modelsHeaderCount">총 {data['models_total_count']}개 모델</span>
          </div>
          <h2 class="text-lg font-bold text-ink-primary" id="modelsHeaderTitle">AI 파운데이션 및 파생 가중치(LoRA/GGUF) 모델 카탈로그</h2>
          <p class="text-xs text-ink-secondary" id="modelsHeaderDesc">
            단순 AI 모델 및 데모를 패밀리별로 체계적으로 모아 스펙, 가중치 포맷, 원본 다운로드 링크를 제공합니다.
          </p>
        </div>
      </div>

      <!-- Models Controls & Family Filter Bar -->
      <div class="bg-white p-4 rounded-2xl border border-surface-border shadow-sm space-y-3">
        <div class="flex items-center gap-2 flex-wrap text-xs">
          <span class="font-bold text-ink-secondary text-[11px] w-20 shrink-0 flex items-center gap-1">
            🤖 모델 패밀리:
          </span>
          <div class="flex items-center gap-1.5 flex-wrap" id="modelsFamilyFilterRow">
            <button onclick="setModelsFamilyFilter('ALL')" data-fam="ALL" class="model-fam-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition">전체 모델</button>
            <button onclick="setModelsFamilyFilter('Qwen')" data-fam="Qwen" class="model-fam-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition">Qwen-3.8 Family</button>
            <button onclick="setModelsFamilyFilter('DeepSeek')" data-fam="DeepSeek" class="model-fam-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition">DeepSeek Family</button>
            <button onclick="setModelsFamilyFilter('MiniMax')" data-fam="MiniMax" class="model-fam-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition">MiniMax / Video</button>
            <button onclick="setModelsFamilyFilter('Audio')" data-fam="Audio" class="model-fam-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition">Audio / TTS</button>
            <button onclick="setModelsFamilyFilter('Standalone')" data-fam="Standalone" class="model-fam-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition">독립/신규 모델</button>
          </div>
        </div>

        <div class="pt-2 border-t border-surface-border flex flex-col md:flex-row items-center justify-between gap-3">
          <div class="relative w-full md:w-80">
            <i data-lucide="search" class="w-4 h-4 absolute left-3.5 top-2.5 text-ink-muted"></i>
            <input type="text" id="modelsSearchInput" placeholder="모델명, 아키텍처, 포맷 검색..." 
                   class="w-full bg-surface-subtle border border-surface-border rounded-xl pl-10 pr-4 py-2 text-xs text-ink-primary placeholder-ink-muted focus:outline-none focus:border-ink-primary transition font-medium">
          </div>

          <div class="flex items-center gap-3 w-full md:w-auto justify-between md:justify-end">
            <span class="text-xs text-ink-muted font-mono" id="modelsFilteredCount"></span>
            <div class="flex items-center gap-1.5 bg-surface-subtle px-3 py-1.5 rounded-xl border border-surface-border text-xs shrink-0">
              <i data-lucide="arrow-up-down" class="w-3.5 h-3.5 text-indigo-600"></i>
              <span class="text-ink-muted text-[11px] font-mono">정렬:</span>
              <select id="modelsSortSelect" onchange="setModelsSort(this.value)" class="bg-transparent text-ink-primary text-xs font-bold focus:outline-none cursor-pointer">
                <option value="date-source-desc">📅 수집/발표 최신순 (기본)</option>
                <option value="date-source-asc">📅 수집/발표 오래된순</option>
                <option value="date-audit-desc">🔬 AI 분석일 최신순</option>
                <option value="date-audit-asc">🔬 AI 분석일 오래된순</option>
                <option value="title-asc">모델명 가나다순</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <!-- Models Grid -->
      <div id="modelsGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5"></div>
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

      <!-- News Source & Sort Controls -->
      <div class="bg-white p-3.5 rounded-2xl flex flex-col md:flex-row items-center justify-between gap-3 border border-surface-border shadow-sm">
        <div class="flex items-center gap-2 w-full md:w-auto flex-wrap">
          <button onclick="setNewsSourceFilter('ALL')" class="news-src-btn active px-3 py-1.5 rounded-xl text-xs font-bold bg-ink-primary text-white transition" data-src="ALL">전체 ({data['news_total_count']}건)</button>
          <button onclick="setNewsSourceFilter('GeekNews')" class="news-src-btn px-3 py-1.5 rounded-xl text-xs font-bold bg-surface-subtle text-ink-secondary hover:bg-white transition border border-surface-border" data-src="GeekNews">🇰🇷 긱뉴스 (GeekNews)</button>
          <button onclick="setNewsSourceFilter('Hacker News')" class="news-src-btn px-3 py-1.5 rounded-xl text-xs font-bold bg-surface-subtle text-ink-secondary hover:bg-white transition border border-surface-border" data-src="Hacker News">🔥 Hacker News</button>
          <button onclick="setNewsSourceFilter('Blog')" class="news-src-btn px-3 py-1.5 rounded-xl text-xs font-bold bg-surface-subtle text-ink-secondary hover:bg-white transition border border-surface-border" data-src="Blog">🌍 Tech Blogs</button>
        </div>

        <div class="flex items-center gap-1.5 bg-surface-subtle px-3 py-1.5 rounded-xl border border-surface-border text-xs shrink-0">
          <i data-lucide="arrow-up-down" class="w-3.5 h-3.5 text-indigo-600"></i>
          <span class="text-ink-muted text-[11px] font-mono">정렬:</span>
          <select id="newsSortSelect" onchange="setNewsSort(this.value)" class="bg-transparent text-ink-primary text-xs font-bold focus:outline-none cursor-pointer">
            <option value="date-source-desc">📅 수집/발행 최신순 (기본)</option>
            <option value="date-source-asc">📅 수집/발행 오래된순</option>
            <option value="date-audit-desc">🔬 AI 분석일 최신순</option>
            <option value="date-audit-asc">🔬 AI 분석일 오래된순</option>
            <option value="title-asc">제목 가나다순</option>
          </select>
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

      <!-- 🎛️ Multi-Tier Interactive Filter Toolbar (검색창 위쪽 복합 필터 바) -->
      <div class="bg-white p-4 rounded-2xl border border-surface-border shadow-sm space-y-2.5">
        <!-- Row 1: Source Language (원문 언어) -->
        <div class="flex items-center gap-2 flex-wrap text-xs">
          <span class="font-bold text-ink-secondary text-[11px] w-20 shrink-0 flex items-center gap-1">
            🌐 원문 언어:
          </span>
          <div class="flex items-center gap-1.5 flex-wrap" id="filterLangRow">
            <button onclick="setInboxLangFilter('ALL')" data-lang-val="ALL" class="inbox-filter-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition">전체 언어</button>
            <button onclick="setInboxLangFilter('KO')" data-lang-val="KO" class="inbox-filter-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition">🇰🇷 한국어 (KO)</button>
            <button onclick="setInboxLangFilter('EN')" data-lang-val="EN" class="inbox-filter-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition">🇬🇧 영어 (EN)</button>
            <button onclick="setInboxLangFilter('ZH')" data-lang-val="ZH" class="inbox-filter-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition">🇨🇳 중국어 (ZH)</button>
          </div>
        </div>

        <!-- Row 2: 4-Tier Classification (4대 기술 분류) -->
        <div class="flex items-center gap-2 flex-wrap text-xs pt-2 border-t border-surface-border/60">
          <span class="font-bold text-ink-secondary text-[11px] w-20 shrink-0 flex items-center gap-1">
            🏷️ 기술 분류:
          </span>
          <div class="flex items-center gap-1.5 flex-wrap" id="filterTypeRow">
            <button onclick="setInboxTypeFilter('ALL')" data-type-val="ALL" class="inbox-type-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition">전체 분류</button>
            <button onclick="setInboxTypeFilter('TECH')" data-type-val="TECH" class="inbox-type-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition">⚡ 신기술/아키텍처</button>
            <button onclick="setInboxTypeFilter('AGENT')" data-type-val="AGENT" class="inbox-type-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition">🦾 AI 에이전트</button>
            <button onclick="setInboxTypeFilter('MODEL')" data-type-val="MODEL" class="inbox-type-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition">🤖 AI 모델 발표</button>
            <button onclick="setInboxTypeFilter('NEWS')" data-type-val="NEWS" class="inbox-type-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition">📰 업계 동향/뉴스</button>
          </div>
        </div>

        <!-- Row 3: Programming Language (프로그래밍 언어) -->
        <div class="flex items-center gap-2 flex-wrap text-xs pt-2 border-t border-surface-border/60">
          <span class="font-bold text-ink-secondary text-[11px] w-20 shrink-0 flex items-center gap-1">
            💻 기술 스택:
          </span>
          <div class="flex items-center gap-1.5 flex-wrap" id="filterTechRow">
            <button onclick="setInboxTechFilter('ALL')" data-tech-val="ALL" class="inbox-tech-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition">전체 스택</button>
            <button onclick="setInboxTechFilter('Python')" data-tech-val="Python" class="inbox-tech-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition">🐍 Python</button>
            <button onclick="setInboxTechFilter('Rust')" data-tech-val="Rust" class="inbox-tech-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition">🦀 Rust</button>
            <button onclick="setInboxTechFilter('TypeScript')" data-tech-val="TypeScript" class="inbox-tech-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition">📘 TypeScript / JS</button>
            <button onclick="setInboxTechFilter('CUDA')" data-tech-val="CUDA" class="inbox-tech-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition">⚡ CUDA / C++</button>
            <button onclick="setInboxTechFilter('General')" data-tech-val="General" class="inbox-tech-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition">🌐 General / 기타</button>
          </div>
        </div>

        <!-- Row 4: Platform Sources (수집 출처) -->
        <div class="flex items-center gap-2 flex-wrap text-xs pt-2 border-t border-surface-border/60">
          <span class="font-bold text-ink-secondary text-[11px] w-20 shrink-0 flex items-center gap-1">
            📡 수집 출처:
          </span>
          <div class="flex items-center gap-1.5 flex-wrap" id="filterPlatformRow">
            <button onclick="setInboxSourceFilter('ALL')" data-src-val="ALL" class="inbox-src-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition">전체 출처</button>
            <button onclick="setInboxSourceFilter('GeekNews')" data-src-val="GeekNews" class="inbox-src-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition">🇰🇷 GeekNews</button>
            <button onclick="setInboxSourceFilter('Hacker News')" data-src-val="Hacker News" class="inbox-src-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition">🔥 Hacker News</button>
            <button onclick="setInboxSourceFilter('GitHub')" data-src-val="GitHub" class="inbox-src-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition">🐙 GitHub</button>
            <button onclick="setInboxSourceFilter('ArXiv')" data-src-val="ArXiv" class="inbox-src-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition">📄 ArXiv</button>
            <button onclick="setInboxSourceFilter('Hugging Face')" data-src-val="Hugging Face" class="inbox-src-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition">🤗 Hugging Face</button>
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
        </div>

        <div class="flex items-center gap-2 w-full md:w-auto justify-end">
          <!-- 🌟 Standardized Sort Selector (날짜순 / 표준화 인기순) -->
          <div class="flex items-center gap-1.5 bg-surface-subtle px-3 py-1.5 rounded-xl border border-surface-border text-xs shrink-0">
            <i data-lucide="arrow-up-down" class="w-3.5 h-3.5 text-indigo-600"></i>
            <span class="text-ink-muted text-[11px] font-mono">정렬:</span>
            <select id="inboxSortSelect" onchange="setInboxSort(this.value)" class="bg-transparent text-ink-primary text-xs font-bold focus:outline-none cursor-pointer">
              <option value="date-source-desc">📅 수집/발표 최신순 (기본)</option>
              <option value="date-source-asc">📅 수집/발표 오래된순</option>
              <option value="date-audit-desc">🔬 AI 분석일 최신순</option>
              <option value="date-audit-asc">🔬 AI 분석일 오래된순</option>
              <option value="viral-desc">🔥 통합 인기순 (Standardized Viral High)</option>
              <option value="viral-asc">통합 인기 낮은순 (Viral Low)</option>
              <option value="title-asc">제목 오름차순 (A to Z)</option>
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
    const modelsData = {models_json};
    const newsData = {news_json};
    const inboxData = {inbox_json};
    const adminData = {admin_json};
    const graphData = {graph_json};

    let liveCasesData = casesData;
    let liveModelsData = modelsData;
    let liveInboxData = inboxData;
    let liveNewsData = newsData;
    let liveAnalysesData = [];

    const API_BASE = (window.location.hostname.includes('github.io')) ? 'https://ai-factcheck-portfolio.vercel.app' : '';

    let currentLang = 'KO';
    let currentView = 'portfolio';
    let currentMode = 'ALL';
    let currentDomain = 'ALL';
    let currentSort = 'date-source-desc';
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
        navModels: "AI 모델",
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
        navModels: "AI 模型",
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
        navModels: "AI Models",
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

    // ================= VIEW SWITCHER (Clean 5 Core Tabs) =================
    function switchView(view) {{
      currentView = view;
      ['portfolio', 'models', 'news', 'graph', 'inbox'].forEach(v => {{
        const el = document.getElementById(v + 'View');
        const btn = document.getElementById('tab' + v.charAt(0).toUpperCase() + v.slice(1) + 'Btn');
        const mBtn = document.getElementById('mTab' + v.charAt(0).toUpperCase() + v.slice(1) + 'Btn');
        
        if (el) el.classList.toggle('hidden', v !== view);
        
        if (btn) {{
          if (v === view) {{
            btn.className = 'nav-tab active flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-white bg-ink-primary transition shadow-sm';
          }} else {{
            btn.className = 'nav-tab flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-ink-secondary hover:text-ink-primary transition';
          }}
        }}

        if (mBtn) {{
          if (v === view) {{
            mBtn.className = 'mobile-nav-tab active shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-ink-primary transition shadow-sm';
          }} else {{
            mBtn.className = 'mobile-nav-tab shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium text-ink-secondary hover:text-ink-primary bg-surface-subtle border border-surface-border transition';
          }}
        }}
      }});

      // 🌟 Immediate Active View Re-render
      if (view === 'portfolio') {{
        renderCards();
      }} else if (view === 'models') {{
        renderModels();
      }} else if (view === 'news') {{
        renderNews();
      }} else if (view === 'inbox') {{
        renderInbox();
      }} else if (view === 'graph' && !simulationRef) {{
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

      // Language Switcher Button Highlighting
      ['KO', 'ZH', 'EN'].forEach(l => {{
        const btn = document.getElementById('lang' + l.charAt(0) + l.slice(1).toLowerCase() + 'Btn');
        if (btn) {{
          btn.className = l === lang 
            ? 'px-2 py-0.5 rounded bg-ink-primary text-white font-bold transition text-[10px] sm:text-[11px] shadow-sm' 
            : 'px-2 py-0.5 rounded text-ink-secondary hover:text-ink-primary transition text-[10px] sm:text-[11px]';
        }}
      }});
      
      const t = i18n[lang];
      const safeSetText = (id, txt) => {{
        const el = document.getElementById(id);
        if (el) el.innerText = txt;
      }};
      const safeSetHtml = (id, html) => {{
        const el = document.getElementById(id);
        if (el) el.innerHTML = html;
      }};
      const safeSetAttr = (id, attr, val) => {{
        const el = document.getElementById(id);
        if (el) el.setAttribute(attr, val);
      }};

      // Brand & Navigation
      safeSetText('headerBrandTitle', t.brandTitle);
      safeSetText('headerBrandSubtitle', t.brandSubtitle);
      safeSetText('navTabPortfolio', t.navPortfolio);
      safeSetText('mNavTabPortfolio', t.navPortfolio);
      safeSetText('navTabModels', t.navModels);
      safeSetText('mNavTabModels', t.navModels + ' (' + (typeof liveModelsData !== 'undefined' ? liveModelsData.length : {data['models_total_count']}) + ')');
      safeSetText('navTabNews', t.navNews);
      safeSetText('mNavTabNews', t.navNews + ' (' + (typeof liveNewsData !== 'undefined' ? liveNewsData.length : {data['news_total_count']}) + ')');
      safeSetText('navTabGraph', t.navGraph);
      safeSetText('mNavTabGraph', t.navGraph);
      safeSetText('navTabInbox', t.navInbox);
      safeSetText('mNavTabInbox', t.navInbox + ' (' + (typeof liveInboxData !== 'undefined' ? liveInboxData.length : {data['inbox_total_count']}) + ')');

      // Hero Elements
      safeSetText('heroBadge', t.heroBadge);
      safeSetText('heroMainTitle', t.heroMainTitle);
      safeSetHtml('heroMainDesc', t.heroMainDesc);
      safeSetText('heroAuditCount', t.heroAuditCount);

      // Dashboard KPI Telemetry
      safeSetText('statLabelVerified', lang === 'KO' ? '공식 기술 검증' : (lang === 'ZH' ? '官方技术核查' : 'Verified Fact-Checks'));
      safeSetText('statLabelInbox', lang === 'KO' ? '수집 인박스' : (lang === 'ZH' ? '采集收件箱' : 'Harvested Inbox'));
      safeSetText('statLabelModels', lang === 'KO' ? '추적 AI 모델' : (lang === 'ZH' ? '追踪 AI 模型' : 'Tracked AI Models'));
      safeSetText('statLabelNews', lang === 'KO' ? 'AI 테크 동향' : (lang === 'ZH' ? 'AI 科技动态' : 'Tech Intelligence'));
      safeSetText('statDescInbox', lang === 'KO' ? 'HN · GeekNews · GitHub · HF 24/7 수집' : (lang === 'ZH' ? 'HN · GeekNews · GitHub · HF 全天候采集' : 'HN · GeekNews · GitHub · HF 24/7 Ingestion'));
      safeSetText('statDescModels', lang === 'KO' ? 'MoE, VLM, 추론 특화 오픈 가중치' : (lang === 'ZH' ? 'MoE、VLM与推理优化开源权重' : 'MoE, VLM & Reasoning Open Weights'));
      safeSetText('statDescNews', lang === 'KO' ? 'CVE 취약점, 인프라 장애, 아키텍처 토론' : (lang === 'ZH' ? 'CVE 漏洞、基础设施故障与架构实践' : 'CVEs, Infra Outages & Architecture Posts'));



      // Audit Criteria & Labels
      safeSetText('criteriaTitle', t.criteriaTitle);
      safeSetText('criteriaDesc', t.criteriaDesc);
      safeSetText('critGithub', t.critGithub);
      safeSetText('critHn', t.critHn);
      safeSetText('critHf', t.critHf);
      safeSetText('critArxiv', t.critArxiv);

      safeSetText('btnLabelAll', t.btnAll);
      safeSetText('btnLabelUser', t.btnUser);
      safeSetText('btnLabelAuto', t.btnAuto);
      safeSetText('sortLabel', t.sortLabel);
      safeSetAttr('searchInput', 'placeholder', t.searchPlaceholder);
      safeSetText('domainFilterLabel', t.domainLabel);

      safeSetText('tagAll', t.tagAll);
      safeSetText('tagFrontend', t.tagFrontend);
      safeSetText('tagAgent', t.tagAgent);
      safeSetText('tagScraping', t.tagScraping);
      safeSetText('tagDoc', t.tagDoc);
      safeSetText('tag3d', t.tag3d);
      safeSetText('tagRust', t.tagRust);
      safeSetText('tagOther', t.tagOther);

      // Update Sort Select Options
      const sortSel = document.getElementById('sortSelect');
      if (sortSel) {{
        const curVal = sortSel.value;
        sortSel.innerHTML = t.sortOptions.map(opt => `<option value="${{opt.val}}" ${{opt.val === curVal ? 'selected' : ''}}>${{opt.text}}</option>`).join('');
      }}

      // 🌟 Instant Full Re-render on Active Views
      renderCards();
      renderModels();
      renderNews();
      renderInbox();
      lucide.createIcons();
    }}

    // ================= REAL-TIME DB SYNC =================
    async function syncFromNeonLiveDB() {{
      try {{
        const resPort = await fetch(API_BASE + '/api/portfolios');
        if (resPort.ok) {{
          const data = await resPort.json();
          if (data.success && data.portfolios && data.portfolios.length > 0) {{
            const staticCaseMap = new Map();
            casesData.forEach(c => staticCaseMap.set(c.case_id, c));

            liveCasesData = data.portfolios.map(dbCase => {{
              const staticCase = staticCaseMap.get(dbCase.case_id);
              return {{
                ...(staticCase || {{}}),
                ...dbCase,
                source_published_date: (staticCase && staticCase.source_published_date) || dbCase.source_published_date || dbCase.investigation_date,
                investigation_date: (staticCase && staticCase.investigation_date) || dbCase.investigation_date
              }};
            }});
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

        const resInbox = await fetch(API_BASE + '/api/queue?all=true');
        if (resInbox.ok) {{
          const inData = await resInbox.json();
          if (inData.success && inData.items && inData.items.length > 0) {{
            const staticMap = new Map();
            inboxData.forEach(item => staticMap.set(item.inbox_id, item));

            liveInboxData = inData.items.map(dbItem => {{
              const staticItem = staticMap.get(dbItem.inbox_id);
              if (staticItem) {{
                return {{
                  ...staticItem,
                  ...dbItem,
                  ai_enrichment: dbItem.ai_enrichment || staticItem.ai_enrichment,
                  multilingual: dbItem.multilingual || staticItem.multilingual,
                  hook: dbItem.hook || staticItem.hook,
                  hook_ko: dbItem.hook_ko || staticItem.hook_ko,
                  hook_en: dbItem.hook_en || staticItem.hook_en,
                  hook_zh: dbItem.hook_zh || staticItem.hook_zh,
                  title_ko: dbItem.title_ko || staticItem.title_ko,
                  title_en: dbItem.title_en || staticItem.title_en,
                  title_zh: dbItem.title_zh || staticItem.title_zh,
                  related_dossier: dbItem.related_dossier || staticItem.related_dossier,
                  metric_tracking: dbItem.metric_tracking || staticItem.metric_tracking
                }};
              }}
              return dbItem;
            }});
            renderInbox();
          }}
        }}

        const resNews = await fetch(API_BASE + '/api/queue?type=NEWS');
        if (resNews.ok) {{
          const newsData = await resNews.json();
          if (newsData.success && newsData.news && newsData.news.length > 0) {{
            const staticNewsMap = new Map();
            if (typeof newsItems !== 'undefined') {{
              newsItems.forEach(item => staticNewsMap.set(item.inbox_id, item));
            }}

            liveNewsData = newsData.news.map(dbItem => {{
              const staticItem = staticNewsMap.get(dbItem.inbox_id);
              if (staticItem) {{
                return {{
                  ...staticItem,
                  ...dbItem,
                  ai_enrichment: dbItem.ai_enrichment || staticItem.ai_enrichment,
                  multilingual: dbItem.multilingual || staticItem.multilingual,
                  hook: dbItem.hook || staticItem.hook,
                  related_dossier: dbItem.related_dossier || staticItem.related_dossier
                }};
              }}
              return dbItem;
            }});
            renderNews();
          }}
        }}

        // Promotion Watch Banner removed as per user design decision
      }} catch (err) {{}}
    }}

    function updatePromotionBanner() {{}}

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

    // 🌟 Precise DateTime Helpers for Sub-Second Sorting & Multi-Platform Timestamps
    function parseItemTimestamp(item, preferField) {{
      if (!item) return 0;
      let raw = '';
      if (preferField === 'audit') {{
        raw = item.ai_enrichment?.enriched_at || item.audited_at || item.investigation_date || item.harvested_at || item.updated_at || item.created_at || item.harvested_date;
      }} else {{
        raw = item.published_at || item.source_published_date || item.created_at || item.harvested_at || item.harvested_date;
      }}
      if (!raw) return 0;
      const ms = new Date(raw).getTime();
      return isNaN(ms) ? 0 : ms;
    }}

    function formatDateTime(raw) {{
      if (!raw) return '-';
      const d = new Date(raw);
      if (isNaN(d.getTime())) return String(raw).substring(0, 10);
      const y = d.getFullYear();
      const m = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      const hh = String(d.getHours()).padStart(2, '0');
      const mm = String(d.getMinutes()).padStart(2, '0');
      return `${{y}}-${{m}}-${{day}} ${{hh}}:${{mm}}`;
    }}

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
      document.getElementById('headerVerifiedCount').innerText = '(' + liveCasesData.length + ')';
      const mCount = document.getElementById('mHeaderVerifiedCount');
      if (mCount) mCount.innerText = '(' + liveCasesData.length + ')';

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

      // 🌟 Precision DateTime Sorting (Default: Source Date/Time DESC)
      filtered.sort((a, b) => {{
        if (currentSort === 'date-source-desc' || currentSort === 'date-desc') {{
          return parseItemTimestamp(b, 'source') - parseItemTimestamp(a, 'source');
        }}
        if (currentSort === 'date-source-asc') {{
          return parseItemTimestamp(a, 'source') - parseItemTimestamp(b, 'source');
        }}
        if (currentSort === 'date-audit-desc') {{
          return parseItemTimestamp(b, 'audit') - parseItemTimestamp(a, 'audit');
        }}
        if (currentSort === 'date-audit-asc') {{
          return parseItemTimestamp(a, 'audit') - parseItemTimestamp(b, 'audit');
        }}
        if (currentSort === 'score-desc') return (b.confidence_score || 0) - (a.confidence_score || 0);
        if (currentSort === 'title-asc') return (a.title || '').localeCompare(b.title || '');
        return parseItemTimestamp(b, 'source') - parseItemTimestamp(a, 'source');
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
        
        const parseDate = (d) => {{
          if (!d) return '2026-09-02';
          const m = String(d).match(/([0-9][0-9][0-9][0-9])[-_]([0-9][0-9])[-_]([0-9][0-9])/);
          return m ? `${{m[1]}}-${{m[2]}}-${{m[3]}}` : '2026-09-02';
        }};
        const srcDate = parseDate(c.source_published_date || c.investigation_date);
        const invDate = parseDate(c.investigation_date || c.source_published_date);
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

        // 🌟 Engagement Metric Tag Enhancement for Motivation
        let motivationHtml = displayMotivation;
        const tagMatch = displayMotivation.match(new RegExp('^\\\\[(.*?)\\\\]\\\\s*(.*)$'));
        if (tagMatch) {{
          motivationHtml = `<span class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold font-mono bg-indigo-50 text-indigo-700 border border-indigo-200 mr-1.5">${{tagMatch[1]}}</span><span>${{tagMatch[2]}}</span>`;
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
            
            <!-- Tier 1: Header Meta (ID + Mode Badge + Dual Dates + Verdict) -->
            <div class="flex items-center justify-between text-xs gap-2 flex-wrap">
              <div class="flex items-center gap-2">
                <span class="text-xs font-mono font-bold text-ink-muted">#${{String(idx + 1).padStart(2, '0')}}</span>
                <span class="px-2 py-0.5 rounded-full text-[10px] font-bold font-mono ${{isUserMode ? 'bg-indigo-50 text-indigo-700 border border-indigo-200' : 'bg-emerald-50 text-emerald-700 border border-emerald-200'}}">
                  ${{isUserMode ? (currentLang === 'KO' ? '직접 큐레이션' : (currentLang === 'ZH' ? '手动精选' : 'USER CURATED')) : (currentLang === 'KO' ? '자동 트렌드' : (currentLang === 'ZH' ? '自动趋势' : 'AUTO HARVEST'))}}
                </span>
                <div class="flex items-center gap-1.5 text-[11px] font-mono text-ink-muted">
                  <span title="${{currentLang === 'KO' ? '수집/원출처 발행일' : (currentLang === 'ZH' ? '采集/原文发布日' : 'Source Date')}}">📅 ${{srcDate}}</span>
                  <span>•</span>
                  <span title="${{currentLang === 'KO' ? '심층 기술 분석일' : (currentLang === 'ZH' ? '深度分析日' : 'Audit Date')}}" class="text-indigo-700 font-semibold">🔬 ${{invDate}}</span>
                </div>
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
                <p class="text-xs text-ink-secondary leading-relaxed line-clamp-2">${{motivationHtml}}</p>
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

    // ================= MODAL HANDLER & DEEP LINKING ROUTER =================
    function openModal(c, skipHistory = false) {{
      if (!c) return;
      if (!skipHistory && c.case_id) {{
        const targetHash = '#case/' + encodeURIComponent(c.case_id);
        if (window.location.hash !== targetHash) {{
          try {{ history.pushState({{ caseId: c.case_id }}, '', targetHash); }} catch (e) {{}}
        }}
      }}

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
        <a href="${{s.url}}" target="_blank" rel="noopener noreferrer" class="p-2.5 rounded-xl bg-surface-subtle border border-surface-border hover:border-ink-primary flex items-center justify-between text-xs text-ink-secondary hover:text-ink-primary transition">
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

    function closeModal(skipHistory = false) {{
      const modal = document.getElementById('detailModal');
      if (modal) modal.classList.add('hidden');
      if (!skipHistory && window.location.hash.startsWith('#case/')) {{
        try {{
          history.pushState(null, '', window.location.pathname + window.location.search);
        }} catch (e) {{}}
      }}
    }}

    function handleHashRoute() {{
      const hash = window.location.hash;
      if (hash.startsWith('#case/')) {{
        const targetCaseId = decodeURIComponent(hash.replace('#case/', ''));
        const target = (liveCasesData || []).find(c => c.case_id === targetCaseId) || (casesData || []).find(c => c.case_id === targetCaseId);
        if (target) {{
          openModal(target, true);
        }}
      }} else {{
        closeModal(true);
      }}
    }}

    window.addEventListener('popstate', handleHashRoute);
    window.addEventListener('load', () => {{
      setTimeout(handleHashRoute, 300);
    }});

    // ================= NEWS VIEW =================
    let currentNewsSource = 'ALL';
    let currentNewsSort = 'date-source-desc';

    function setNewsSort(sort) {{
      currentNewsSort = sort;
      renderNews();
    }}

    function setNewsSourceFilter(src) {{
      currentNewsSource = src;
      document.querySelectorAll('.news-src-btn').forEach(btn => {{
        if (btn.getAttribute('data-src') === src) {{
          btn.className = 'news-src-btn active px-3 py-1.5 rounded-xl text-xs font-bold bg-ink-primary text-white transition';
        }} else {{
          btn.className = 'news-src-btn px-3 py-1.5 rounded-xl text-xs font-bold bg-surface-subtle text-ink-secondary hover:bg-white transition border border-surface-border';
        }}
      }});
      renderNews();
    }}

    function renderNews() {{
      const grid = document.getElementById('newsGrid');
      grid.innerHTML = '';
      const t = i18n[currentLang];

      const rawNewsItems = liveNewsData || [];
      const newsItems = rawNewsItems.filter(it => {{
        return currentNewsSource === 'ALL' || (it.source_platform && it.source_platform.includes(currentNewsSource));
      }});

      // 🌟 Precision DateTime Sorting (Default: Source Date/Time DESC)
      newsItems.sort((a, b) => {{
        if (currentNewsSort === 'date-source-desc') {{
          return parseItemTimestamp(b, 'source') - parseItemTimestamp(a, 'source');
        }}
        if (currentNewsSort === 'date-source-asc') {{
          return parseItemTimestamp(a, 'source') - parseItemTimestamp(b, 'source');
        }}
        if (currentNewsSort === 'date-audit-desc') {{
          return parseItemTimestamp(b, 'audit') - parseItemTimestamp(a, 'audit');
        }}
        if (currentNewsSort === 'date-audit-asc') {{
          return parseItemTimestamp(a, 'audit') - parseItemTimestamp(b, 'audit');
        }}
        if (currentNewsSort === 'title-asc') return (a.title || '').localeCompare(b.title || '');
        return parseItemTimestamp(b, 'source') - parseItemTimestamp(a, 'source');
      }});

      if (newsItems.length === 0) {{
        grid.innerHTML = `<div class="col-span-full py-16 text-center text-ink-muted font-medium">${{currentLang === 'KO' ? '해당 플랫폼의 수집 AI 뉴스가 없습니다.' : (currentLang === 'ZH' ? '暂无该平台的 AI 资讯。' : 'No AI news articles available for this source.')}}</div>`;
        return;
      }}

      newsItems.forEach(it => {{
        const card = document.createElement('div');
        card.className = 'executive-card p-5 flex flex-col justify-between space-y-4';

        const ai = it.ai_enrichment;
        const multi = ai ? ai.multilingual : null;
        let displayTitle = it.title;
        let displayDesc = it.description || '';
        let displayHook = (ai ? ai.hook : '') || it.hook || '';
        let displayTakeaways = (ai ? ai.key_takeaways : []) || [];

        if (multi) {{
          if (currentLang === 'KO' && multi.ko) {{
            displayTitle = multi.ko.title || it.title_ko || displayTitle;
            displayHook = multi.ko.hook || it.hook_ko || displayHook;
            displayTakeaways = multi.ko.key_takeaways || displayTakeaways;
            displayDesc = displayHook || it.description_ko || displayDesc;
          }} else if (currentLang === 'ZH' && multi.zh) {{
            displayTitle = multi.zh.title || it.title_zh || displayTitle;
            displayHook = multi.zh.hook || it.hook_zh || displayHook;
            displayTakeaways = multi.zh.key_takeaways || displayTakeaways;
            displayDesc = displayHook || it.description_zh || displayDesc;
          }} else if (currentLang === 'EN' && multi.en) {{
            displayTitle = multi.en.title || it.title_en || displayTitle;
            displayHook = multi.en.hook || it.hook_en || displayHook;
            displayTakeaways = multi.en.key_takeaways || displayTakeaways;
            displayDesc = displayHook || it.description_en || displayDesc;
          }}
        }} else {{
          if (currentLang === 'KO' && it.title_ko) displayTitle = it.title_ko;
          if (currentLang === 'ZH' && it.title_zh) displayTitle = it.title_zh;
          if (currentLang === 'EN' && it.title_en) displayTitle = it.title_en;
        }}

        const isHn = (it.source_platform || '').includes('Hacker News') || (it.source_url || '').includes('news.ycombinator.com');
        const isGn = (it.source_platform || '').includes('GeekNews') || (it.source_url || '').includes('hada.io');
        const hnUrl = it.hn_url || ((it.source_url || '').includes('news.ycombinator.com') ? it.source_url : null);
        const gnUrl = isGn ? (it.hn_url || it.source_url) : null;
        const articleUrl = it.article_url || (it.source_url !== (hnUrl || gnUrl) ? it.source_url : null);

        let linksHtml = '';
        if (isHn) {{
          linksHtml = `<div class="flex items-center gap-1.5">`;
          if (articleUrl && articleUrl !== hnUrl) {{
            linksHtml += `<a href="${{articleUrl}}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border text-[11px] font-medium flex items-center gap-1">📄 ${{currentLang === 'KO' ? '기사 원문' : (currentLang === 'ZH' ? '文章原文' : 'Article')}} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>`;
          }}
          if (hnUrl) {{
            linksHtml += `<a href="${{hnUrl}}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded bg-orange-50 text-orange-800 hover:text-orange-950 border border-orange-200 text-[11px] font-bold flex items-center gap-1">🔥 ${{currentLang === 'KO' ? 'HN 토론' : (currentLang === 'ZH' ? 'HN 讨论' : 'HN Thread')}} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>`;
          }}
          linksHtml += `</div>`;
        }} else if (isGn) {{
          linksHtml = `<div class="flex items-center gap-1.5">`;
          if (articleUrl && articleUrl !== gnUrl) {{
            linksHtml += `<a href="${{articleUrl}}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border text-[11px] font-medium flex items-center gap-1">📄 ${{currentLang === 'KO' ? '기사 원문' : (currentLang === 'ZH' ? '文章原文' : 'Article')}} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>`;
          }}
          if (gnUrl) {{
            linksHtml += `<a href="${{gnUrl}}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded bg-indigo-50 text-indigo-800 hover:text-indigo-950 border border-indigo-200 text-[11px] font-bold flex items-center gap-1">💬 ${{currentLang === 'KO' ? '긱뉴스 토론' : (currentLang === 'ZH' ? '极客新闻' : 'GeekNews')}} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>`;
          }}
          linksHtml += `</div>`;
        }} else {{
          linksHtml = `<a href="${{it.source_url}}" target="_blank" rel="noopener noreferrer" class="text-ink-primary hover:underline font-semibold flex items-center gap-1">${{t.newsOriginalLink}} <i data-lucide="external-link" class="w-3 h-3"></i></a>`;
        }}

        let aiBadgeHtml = '';
        let aiSummaryHtml = '';
        let hookHtml = '';
        let relatedHtml = '';

        if (ai) {{
          const tagBg = ai.worth_investigating === 'HIGH' ? 'bg-orange-50 text-orange-950 border-orange-200' : 'bg-indigo-50 text-indigo-950 border-indigo-200';
          const typeLabels = {{
            'MODEL': currentLang === 'KO' ? '🤖 모델 발표' : (currentLang === 'ZH' ? '🤖 模型发布' : '🤖 Model'),
            'AGENT': currentLang === 'KO' ? '🦾 에이전트' : (currentLang === 'ZH' ? '🦾 智能体' : '🦾 Agent'),
            'TECH': currentLang === 'KO' ? '⚡ 신기술/최적화' : (currentLang === 'ZH' ? '⚡ 新技术/架构' : '⚡ Tech/Arch'),
            'NEWS': currentLang === 'KO' ? '📰 업계 동향' : (currentLang === 'ZH' ? '📰 行业资讯' : '📰 News')
          }};
          const typeBadge = typeLabels[ai.type_classification] || (currentLang === 'KO' ? '💡 기술' : '💡 Tech');

          aiBadgeHtml = `
            <div class="flex items-center gap-1.5 flex-wrap my-1">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${{tagBg}}">
                ${{ai.recommended_tag || '💡 추천'}} ★${{ai.score || ai.worth_score || '4.0'}}
              </span>
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-900 border border-indigo-200">
                ${{typeBadge}}
              </span>
              ${{ai.programming_lang && ai.programming_lang !== 'General' ? `<span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-50 text-amber-900 border border-amber-200">💻 ${{ai.programming_lang}}</span>` : ''}}
              ${{ai.source_lang ? `<span class="px-1.5 py-0.2 rounded text-[9px] font-mono font-semibold bg-surface-subtle text-ink-muted border border-surface-border">${{ai.source_lang}}</span>` : ''}}
            </div>
          `;

          if (displayHook) {{
            hookHtml = `
              <div class="p-2.5 rounded-xl bg-amber-50/70 border border-amber-200/80 text-[11px] text-amber-950 font-medium leading-relaxed flex items-start gap-1.5">
                <span class="shrink-0 font-bold text-amber-800">🪝 Hook:</span>
                <span>${{displayHook}}</span>
              </div>
            `;
          }}

          if (displayTakeaways && displayTakeaways.length > 0) {{
            aiSummaryHtml = `
              <div class="p-3 rounded-xl bg-gradient-to-br from-indigo-50/50 via-sky-50/40 to-purple-50/50 border border-indigo-100 text-[11px] space-y-1.5">
                <div class="flex items-center gap-1 text-indigo-950 font-bold text-[10px]">
                  <i data-lucide="sparkles" class="w-3 h-3 text-indigo-600"></i>
                  <span>${{currentLang === 'KO' ? 'AI 3줄 핵심 요약' : (currentLang === 'ZH' ? 'AI 3行核心摘要' : 'AI 3-Line Summary')}}</span>
                </div>
                <ul class="space-y-1 text-ink-secondary leading-relaxed list-disc list-inside">
                  ${{displayTakeaways.map(k => `<li>${{k}}</li>`).join('')}}
                </ul>
              </div>
            `;
          }}
        }}

        if (it.related_dossier) {{
          relatedHtml = `
            <div class="pt-2 border-t border-surface-border">
              <button onclick="openCaseModal('${{it.related_dossier.case_id}}')" class="w-full text-left px-2.5 py-1.5 rounded-lg bg-indigo-50/70 hover:bg-indigo-100/80 border border-indigo-200/80 text-[11px] text-indigo-950 font-semibold flex items-center justify-between transition">
                <span class="flex items-center gap-1.5">
                  <i data-lucide="link-2" class="w-3.5 h-3.5 text-indigo-600"></i>
                  <span>관련 팩트체크: ${{it.related_dossier.target_tech}}</span>
                </span>
                <i data-lucide="arrow-right" class="w-3 h-3 text-indigo-400"></i>
              </button>
            </div>
          `;
        }}

        card.innerHTML = `
          <div class="space-y-2.5">
            <div class="flex items-center justify-between text-xs font-mono">
              <span class="px-2 py-0.5 rounded bg-surface-subtle text-ink-primary font-bold border border-surface-border text-[11px]">
                ${{it.source_platform || 'Tech News'}}
              </span>
              <span class="text-ink-muted text-[11px]">${{it.viral_metric || ''}}</span>
            </div>

            ${{aiBadgeHtml}}

            <h3 class="font-bold text-sm text-ink-primary hover:text-indigo-600 transition leading-snug">
              ${{displayTitle}}
            </h3>

            ${{hookHtml}}

            <p class="text-xs text-ink-secondary leading-relaxed line-clamp-3">
              ${{displayDesc}}
            </p>

            ${{aiSummaryHtml}}
            ${{relatedHtml}}
          </div>

          <div class="pt-3 border-t border-surface-border flex items-center justify-between text-xs">
            <div class="flex items-center gap-1.5 text-[11px] font-mono text-ink-muted">
              <span title="${{currentLang === 'KO' ? '수집/발행 일시' : (currentLang === 'ZH' ? '采集/发布日' : 'Source DateTime')}}">📅 ${{formatDateTime(it.published_at || it.harvested_at || it.harvested_date)}}</span>
              ${{ai?.enriched_at ? `<span>•</span><span title="${{currentLang === 'KO' ? 'AI 분석 일시' : (currentLang === 'ZH' ? 'AI分析日' : 'Analysis DateTime')}}" class="text-indigo-700 font-semibold">🔬 ${{formatDateTime(ai.enriched_at)}}</span>` : ''}}
            </div>
            ${{linksHtml}}
          </div>
        `;
        grid.appendChild(card);
      }});

      lucide.createIcons();
    }}

    // ================= AI MODELS REGISTRY VIEW =================
    let currentModelsFamily = 'ALL';
    let currentModelsSort = 'date-source-desc';
    let modelsSearchQuery = '';

    function setModelsSort(sort) {{
      currentModelsSort = sort;
      renderModels();
    }}

    function setModelsFamilyFilter(fam) {{
      currentModelsFamily = fam;
      document.querySelectorAll('.model-fam-pill').forEach(btn => {{
        if (btn.dataset.fam === fam) {{
          btn.className = 'model-fam-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition';
        }} else {{
          btn.className = 'model-fam-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition';
        }}
      }});
      renderModels();
    }}

    document.getElementById('modelsSearchInput')?.addEventListener('input', (e) => {{
      modelsSearchQuery = e.target.value;
      renderModels();
    }});

    function renderModels() {{
      const grid = document.getElementById('modelsGrid');
      if (!grid) return;
      grid.innerHTML = '';

      const filtered = liveModelsData.filter(item => {{
        const fam = item.model_family || '';
        let matchesFam = true;
        if (currentModelsFamily === 'Qwen') matchesFam = fam.toLowerCase().includes('qwen');
        else if (currentModelsFamily === 'DeepSeek') matchesFam = fam.toLowerCase().includes('deepseek');
        else if (currentModelsFamily === 'MiniMax') matchesFam = fam.toLowerCase().includes('minimax') || fam.toLowerCase().includes('video') || fam.toLowerCase().includes('flux');
        else if (currentModelsFamily === 'Audio') matchesFam = fam.toLowerCase().includes('audio') || fam.toLowerCase().includes('tts');
        else if (currentModelsFamily === 'Standalone') matchesFam = fam.toLowerCase().includes('standalone') || fam.toLowerCase().includes('독립');
        else matchesFam = true;

        const text = (item.title + ' ' + (item.title_ko || '') + ' ' + (item.title_en || '') + ' ' + (item.title_zh || '') + ' ' + (item.description || '') + ' ' + fam).toLowerCase();
        const matchesSearch = text.includes(modelsSearchQuery.toLowerCase());
        return matchesFam && matchesSearch;
      }});

      // 🌟 Precision DateTime Sorting (Default: Source Date/Time DESC)
      filtered.sort((a, b) => {{
        if (currentModelsSort === 'date-source-desc') {{
          return parseItemTimestamp(b, 'source') - parseItemTimestamp(a, 'source');
        }}
        if (currentModelsSort === 'date-source-asc') {{
          return parseItemTimestamp(a, 'source') - parseItemTimestamp(b, 'source');
        }}
        if (currentModelsSort === 'date-audit-desc') {{
          return parseItemTimestamp(b, 'audit') - parseItemTimestamp(a, 'audit');
        }}
        if (currentModelsSort === 'date-audit-asc') {{
          return parseItemTimestamp(a, 'audit') - parseItemTimestamp(b, 'audit');
        }}
        if (currentModelsSort === 'title-asc') return (a.title || '').localeCompare(b.title || '');
        return parseItemTimestamp(b, 'source') - parseItemTimestamp(a, 'source');
      }});

      const countEl = document.getElementById('modelsFilteredCount');
      if (countEl) countEl.innerText = currentLang === 'KO' ? `${{filtered.length}}개 모델 표출` : (currentLang === 'ZH' ? `显示 ${{filtered.length}} 个模型` : `Showing ${{filtered.length}} models`);

      if (filtered.length === 0) {{
        grid.innerHTML = `<div class="col-span-full py-16 text-center text-ink-muted font-medium">${{currentLang === 'KO' ? '일치하는 AI 모델이 없습니다.' : (currentLang === 'ZH' ? '暂无匹配的 AI 模型。' : 'No matching AI models.')}}</div>`;
        return;
      }}

      filtered.forEach(it => {{
        const ai = it.ai_enrichment;
        const multi = ai?.multilingual;
        const lKey = currentLang.toLowerCase();

        let displayTitle = (multi && multi[lKey]?.title) || (currentLang === 'KO' ? it.title_ko : (currentLang === 'ZH' ? it.title_zh : it.title_en)) || it.title;
        let displayHook = (multi && multi[lKey]?.hook) || (currentLang === 'KO' ? it.hook_ko : (currentLang === 'ZH' ? it.hook_zh : it.hook_en)) || it.hook || '';
        let displayDesc = (currentLang === 'KO' ? it.description_ko : (currentLang === 'ZH' ? it.description_zh : it.description_en)) || it.description || '';

        const hasTrilingual = Boolean(multi && multi.zh && multi.ko && multi.en);
        const langBadge = hasTrilingual 
          ? `<span class="px-1.5 py-0.2 rounded bg-emerald-50 text-emerald-800 text-[9px] font-mono font-bold border border-emerald-200">🌐 KO·EN·ZH</span>`
          : `<span class="px-1.5 py-0.2 rounded bg-surface-subtle text-ink-muted text-[9px] font-mono border border-surface-border">🌐 분석 대기</span>`;

        const card = document.createElement('div');
        card.className = 'bg-white rounded-2xl p-5 border border-surface-border hover:border-indigo-400 hover:shadow-md transition flex flex-col justify-between space-y-4';

        const famBadge = it.model_family ? `
          <span class="px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 font-bold border border-indigo-200 text-[11px] font-mono">
            🤖 ${{it.model_family}}
          </span>
        ` : '';

        let hookHtml = '';
        if (displayHook) {{
          hookHtml = `
            <div class="p-2.5 rounded-xl bg-amber-50/70 border border-amber-200/80 text-[11px] text-amber-950 font-medium leading-relaxed flex items-start gap-1.5">
              <span class="shrink-0 font-bold text-amber-800">🪝 Hook:</span>
              <span>${{displayHook}}</span>
            </div>
          `;
        }}

        let relatedHtml = '';
        if (it.related_dossier) {{
          relatedHtml = `
            <div class="pt-2 border-t border-surface-border">
              <button onclick="openCaseModal('${{it.related_dossier.case_id}}')" class="w-full text-left px-2.5 py-1.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 text-[11px] text-emerald-950 font-semibold flex items-center justify-between transition">
                <span class="flex items-center gap-1.5">
                  <i data-lucide="shield-check" class="w-3.5 h-3.5 text-emerald-600"></i>
                  <span>관련 기술 검증: ${{it.related_dossier.target_tech}}</span>
                </span>
                <i data-lucide="arrow-right" class="w-3 h-3 text-emerald-600"></i>
              </button>
            </div>
          `;
        }}

        card.innerHTML = `
          <div class="space-y-3">
            <div class="flex items-center justify-between text-xs font-mono">
              ${{famBadge}}
              <span class="text-ink-muted text-[11px]">${{it.source_platform || 'Hugging Face'}}</span>
            </div>

            <h3 class="font-bold text-sm text-ink-primary hover:text-indigo-600 transition leading-snug">
              ${{displayTitle}}
            </h3>

            ${{hookHtml}}

            <p class="text-xs text-ink-secondary leading-relaxed line-clamp-3">
              ${{displayDesc}}
            </p>

            ${{relatedHtml}}
          </div>

          <div class="pt-3 border-t border-surface-border flex items-center justify-between text-xs">
            <div class="flex items-center gap-1.5 flex-wrap text-[11px] font-mono text-ink-muted">
              <span title="${{currentLang === 'KO' ? '수집/발표 일시' : (currentLang === 'ZH' ? '采集/发布日' : 'Source DateTime')}}">📅 ${{formatDateTime(it.published_at || it.harvested_at || it.harvested_date)}}</span>
              ${{ai?.enriched_at ? `<span>•</span><span title="${{currentLang === 'KO' ? 'AI 분석 일시' : (currentLang === 'ZH' ? 'AI分析日' : 'Analysis DateTime')}}" class="text-indigo-700 font-semibold">🔬 ${{formatDateTime(ai.enriched_at)}}</span>` : ''}}
              ${{ai?.enriched_by_model ? `<span class="px-1.5 py-0.2 rounded text-[9px] font-mono font-medium bg-surface-subtle text-indigo-700 border border-surface-border">🤖 ${{ai.enriched_by_model.replace('gemini-', '')}}</span>` : ''}}
            </div>
            <a href="${{it.source_url}}" target="_blank" class="px-3 py-1.5 rounded-lg bg-surface-subtle hover:bg-ink-primary hover:text-white text-ink-primary font-bold transition text-xs flex items-center gap-1">
              <span>${{currentLang === 'KO' ? '원문 / 다운로드' : (currentLang === 'ZH' ? '原文 / 模型主页' : 'Source / Model')}}</span> <i data-lucide="external-link" class="w-3 h-3"></i>
            </a>
          </div>
        `;

        grid.appendChild(card);
      }});

      lucide.createIcons();
    }}

    // ================= STANDARDIZED CROSS-PLATFORM VIRAL NORMALIZER =================
    function calculateStandardizedViralScore(item) {{
      const src = item.source_platform || '';
      const metric = item.viral_metric || item.description || '';
      let rawNum = 0;

      const nums = (metric.replace(/,/g, '').match(/\\d+/) || []);
      if (nums.length > 0) rawNum = parseInt(nums[0], 10);

      let normScore = 25; // Base fallback score

      if (src.includes('GitHub')) {{
        // GitHub: 5000 stars = 100 pts, 500 stars = ~73 pts
        normScore = rawNum > 0 ? (Math.log10(rawNum + 1) / Math.log10(5000)) * 100 : 25;
      }} else if (src.includes('Hacker News')) {{
        // Hacker News: 800 pts = 100 pts, 150 pts = ~75 pts
        normScore = rawNum > 0 ? (Math.log10(rawNum + 1) / Math.log10(800)) * 100 : 30;
      }} else if (src.includes('Hugging Face')) {{
        // Hugging Face: 300 likes = 100 pts, 50 likes = ~68 pts
        normScore = rawNum > 0 ? (Math.log10(rawNum + 1) / Math.log10(300)) * 100 : 30;
      }} else if (src.includes('GeekNews')) {{
        // GeekNews: 100 pts = 100 pts, 20 pts = ~66 pts
        normScore = rawNum > 0 ? (Math.log10(rawNum + 1) / Math.log10(100)) * 100 : 35;
      }} else if (src.includes('ArXiv')) {{
        normScore = 55; // Peer-reviewed academic baseline
      }}

      normScore = Math.max(5, Math.min(100, Math.round(normScore)));

      // Blend AI enrichment rating if available (70% viral, 30% AI rating)
      const aiScore = item.ai_enrichment ? item.ai_enrichment.score : null;
      if (aiScore && aiScore > 0) {{
        normScore = Math.round((normScore * 0.7) + ((aiScore * 20) * 0.3));
      }}

      return normScore;
    }}

    let currentInboxSort = 'date-desc';

    function setInboxSort(val) {{
      currentInboxSort = val;
      renderInbox();
    }}

    let currentInboxLang = 'ALL';
    let currentInboxType = 'ALL';
    let currentInboxTech = 'ALL';

    function setInboxLangFilter(lang) {{
      currentInboxLang = lang;
      document.querySelectorAll('.inbox-filter-pill').forEach(btn => {{
        if (btn.dataset.langVal === lang) {{
          btn.className = 'inbox-filter-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition';
        }} else {{
          btn.className = 'inbox-filter-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition';
        }}
      }});
      renderInbox();
    }}

    function setInboxTypeFilter(typeVal) {{
      currentInboxType = typeVal;
      document.querySelectorAll('.inbox-type-pill').forEach(btn => {{
        if (btn.dataset.typeVal === typeVal) {{
          btn.className = 'inbox-type-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition';
        }} else {{
          btn.className = 'inbox-type-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition';
        }}
      }});
      renderInbox();
    }}

    function setInboxTechFilter(tech) {{
      currentInboxTech = tech;
      document.querySelectorAll('.inbox-tech-pill').forEach(btn => {{
        if (btn.dataset.techVal === tech) {{
          btn.className = 'inbox-tech-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition';
        }} else {{
          btn.className = 'inbox-tech-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition';
        }}
      }});
      renderInbox();
    }}

    function setInboxSourceFilter(src) {{
      currentInboxSource = src;
      const sel = document.getElementById('inboxSourceSelect');
      if (sel && sel.value !== src) sel.value = src;

      document.querySelectorAll('.inbox-src-pill').forEach(btn => {{
        if (btn.dataset.srcVal === src) {{
          btn.className = 'inbox-src-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition';
        }} else {{
          btn.className = 'inbox-src-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition';
        }}
      }});
      renderInbox();
    }}

    document.getElementById('inboxSearchInput').addEventListener('input', (e) => {{
      inboxSearchQuery = e.target.value;
      renderInbox();
    }});

    function renderInbox() {{
      const grid = document.getElementById('inboxGrid');
      if (!grid) return;
      grid.innerHTML = '';
      const t = i18n[currentLang];

      const filtered = liveInboxData.filter(item => {{
        const ai = item.ai_enrichment;

        // 1. 수집 플랫폼 매칭
        const matchesSrc = currentInboxSource === 'ALL' || (item.source_platform && item.source_platform.includes(currentInboxSource));

        // 2. 원문 언어 매칭 (KO, EN, ZH)
        const itemLang = (ai ? ai.source_lang : null) || item.source_lang || 'EN';
        const matchesLang = currentInboxLang === 'ALL' || itemLang === currentInboxLang;

        // 3. 4대 기술 분류 매칭 (인박스는 기본적으로 뉴스를 제외한 기술/모델/에이전트/미분석 대기열)
        const itemType = (ai ? ai.type_classification : null) || item.category_type || 'TECH';
        const matchesType = currentInboxType === 'ALL' 
          ? (itemType !== 'NEWS') 
          : (itemType === currentInboxType);

        // 4. 기술 스택/프로그래밍 언어 매칭
        const itemTech = (ai ? ai.programming_lang : null) || item.programming_lang || 'General';
        const matchesTech = currentInboxTech === 'ALL' || (itemTech.toLowerCase().includes(currentInboxTech.toLowerCase()));

        // 5. 검색어 매칭
        const text = (item.title + ' ' + (item.title_ko || '') + ' ' + (item.title_en || '') + ' ' + (item.title_zh || '') + ' ' + (item.description || '') + ' ' + (item.model_family || '') + ' ' + (item.variant_role || '') + ' ' + (item.hook || '')).toLowerCase();
        const matchesSearch = text.includes(inboxSearchQuery.toLowerCase());

        return matchesSrc && matchesLang && matchesType && matchesTech && matchesSearch;
      }});

      // 🌟 Precision DateTime Sorting (Default: Source Date/Time DESC)
      filtered.sort((a, b) => {{
        if (currentInboxSort === 'date-source-desc' || currentInboxSort === 'date-desc') {{
          return parseItemTimestamp(b, 'source') - parseItemTimestamp(a, 'source');
        }} else if (currentInboxSort === 'date-source-asc' || currentInboxSort === 'date-asc') {{
          return parseItemTimestamp(a, 'source') - parseItemTimestamp(b, 'source');
        }} else if (currentInboxSort === 'date-audit-desc') {{
          return parseItemTimestamp(b, 'audit') - parseItemTimestamp(a, 'audit');
        }} else if (currentInboxSort === 'date-audit-asc') {{
          return parseItemTimestamp(a, 'audit') - parseItemTimestamp(b, 'audit');
        }} else if (currentInboxSort === 'viral-desc') {{
          return calculateStandardizedViralScore(b) - calculateStandardizedViralScore(a);
        }} else if (currentInboxSort === 'viral-asc') {{
          return calculateStandardizedViralScore(a) - calculateStandardizedViralScore(b);
        }} else if (currentInboxSort === 'title-asc') {{
          return (a.title || '').localeCompare(b.title || '');
        }}
        return parseItemTimestamp(b, 'source') - parseItemTimestamp(a, 'source');
      }});

      if (filtered.length === 0) {{
        grid.innerHTML = `<div class="col-span-full py-16 text-center text-ink-muted font-medium">${{currentLang === 'KO' ? '수집된 인박스 후보가 없습니다.' : (currentLang === 'ZH' ? '收件箱暂无候选数据。' : 'No candidates in the inbox.')}}</div>`;
        return;
      }}

      filtered.forEach(it => {{
        const isQueued = queuedItemIds.has(it.inbox_id);
        const ai = it.ai_enrichment;
        const multi = ai ? ai.multilingual : null;
        const lKey = currentLang.toLowerCase();

        let displayTitle = (multi && multi[lKey] ? multi[lKey].title : null) || (currentLang === 'KO' ? it.title_ko : (currentLang === 'ZH' ? it.title_zh : it.title_en)) || it.title;
        let displayHook = (multi && multi[lKey] ? multi[lKey].hook : null) || (currentLang === 'KO' ? it.hook_ko : (currentLang === 'ZH' ? it.hook_zh : it.hook_en)) || it.hook || '';
        let displayDesc = (currentLang === 'KO' ? it.description_ko : (currentLang === 'ZH' ? it.description_zh : it.description_en)) || it.description || '';
        let displayTakeaways = (multi && multi[lKey] ? multi[lKey].key_takeaways : null) || (ai ? ai.key_takeaways : []) || [];

        const viralScore = calculateStandardizedViralScore(it);
        const tracking = it.metric_tracking || {{}};
        const initDate = tracking.initial_date || (it.harvested_date ? it.harvested_date.substring(5, 10) : '08-31');
        const latestDate = tracking.latest_date || (it.harvested_date ? it.harvested_date.substring(5, 10) : '09-02');
        const initVal = tracking.initial_metric || it.viral_metric || '-';
        const latestVal = tracking.latest_metric || it.viral_metric || '-';
        const delta = tracking.growth_delta || 0;
        const deltaDisplay = delta > 0 ? `+${{delta}}` : (delta < 0 ? `${{delta}}` : '0');

        let typeBadge = currentLang === 'KO' ? '⚡ 신기술' : (currentLang === 'ZH' ? '⚡ 新技术' : '⚡ Tech');
        if (ai && ai.type_classification === 'AGENT') typeBadge = currentLang === 'KO' ? '🦾 에이전트' : (currentLang === 'ZH' ? '🦾 智能体' : '🦾 Agent');
        else if (ai && ai.type_classification === 'MODEL') typeBadge = currentLang === 'KO' ? '🤖 AI 모델' : (currentLang === 'ZH' ? '🤖 AI 模型' : '🤖 AI Model');
        else if (ai && ai.type_classification === 'NEWS') typeBadge = currentLang === 'KO' ? '📰 업계 동향' : (currentLang === 'ZH' ? '📰 行业资讯' : '📰 News');

        const card = document.createElement('div');
        card.className = 'executive-card p-5 flex flex-col justify-between space-y-3.5 hover:border-indigo-400 hover:shadow-md transition';

        let hookHtml = '';
        if (displayHook) {{
          hookHtml = `
            <div class="p-2.5 rounded-xl bg-amber-50/70 border border-amber-200/80 text-[11px] text-amber-950 font-medium leading-relaxed flex items-start gap-1.5">
              <span class="shrink-0 font-bold text-amber-800">🪝 Hook:</span>
              <span>${{displayHook}}</span>
            </div>
          `;
        }}

        let aiSummaryHtml = '';
        if (displayTakeaways && displayTakeaways.length > 0) {{
          aiSummaryHtml = `
            <div class="mt-2 p-3 rounded-xl bg-gradient-to-br from-indigo-50/50 via-sky-50/40 to-purple-50/50 border border-indigo-100 text-[11px] space-y-1 font-sans">
              <div class="flex items-center gap-1 text-indigo-950 font-bold text-[10px]">
                <i data-lucide="sparkles" class="w-3 h-3 text-indigo-600"></i>
                <span>${{currentLang === 'KO' ? 'AI 3줄 핵심 요약' : (currentLang === 'ZH' ? 'AI 3行核心摘要' : 'AI 3-Line Summary')}}</span>
              </div>
              <ul class="space-y-1 text-ink-secondary leading-relaxed list-disc list-inside">
                ${{displayTakeaways.map(k => `<li>${{k}}</li>`).join('')}}
              </ul>
            </div>
          `;
        }}

        let relatedHtml = '';
        if (it.related_dossier) {{
          relatedHtml = `
            <div class="pt-2 border-t border-surface-border">
              <button onclick="openCaseModal('${{it.related_dossier.case_id}}')" class="w-full text-left px-2.5 py-1.5 rounded-lg bg-indigo-50/70 hover:bg-indigo-100/80 border border-indigo-200/80 text-[11px] text-indigo-950 font-semibold flex items-center justify-between transition">
                <span class="flex items-center gap-1.5">
                  <i data-lucide="shield-check" class="w-3.5 h-3.5 text-emerald-600"></i>
                  <span>${{currentLang === 'KO' ? '관련 팩트체크:' : (currentLang === 'ZH' ? '关联事实核查:' : 'Related Audit:')}} ${{it.related_dossier.target_tech}}</span>
                </span>
                <i data-lucide="arrow-right" class="w-3 h-3 text-indigo-400"></i>
              </button>
            </div>
          `;
        }}

        card.innerHTML = `
          <div class="space-y-2.5">
            <div class="flex items-center justify-between text-xs font-mono">
              <span class="px-2 py-0.5 rounded bg-surface-subtle text-ink-primary font-bold border border-surface-border text-[11px]">
                ${{it.source_platform || 'Tech Candidate'}}
              </span>
              <span class="px-2 py-0.5 rounded text-[11px] font-bold font-mono ${{viralScore >= 70 ? 'bg-rose-50 text-rose-700 border border-rose-200' : 'bg-amber-50 text-amber-700 border border-amber-200'}}">
                ${{currentLang === 'KO' ? `🔥 인기 ${{viralScore}}점` : (currentLang === 'ZH' ? `🔥 热度 ${{viralScore}}分` : `🔥 Viral ${{viralScore}} pts`)}}
              </span>
            </div>

            <div class="flex items-center gap-1.5 flex-wrap">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-900 border border-indigo-200">
                ${{typeBadge}}
              </span>
              ${{ai && ai.programming_lang && ai.programming_lang !== 'General' ? `<span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-50 text-amber-900 border border-amber-200">💻 ${{ai.programming_lang}}</span>` : ''}}
              ${{ai && ai.source_lang ? `<span class="px-1.5 py-0.2 rounded text-[9px] font-mono font-semibold bg-surface-subtle text-ink-muted border border-surface-border">🌐 ${{ai.source_lang}}</span>` : ''}}
              ${{multi && multi.zh && multi.ko && multi.en ? `<span class="px-1.5 py-0.2 rounded text-[9px] font-mono font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">🌐 KO·EN·ZH</span>` : `<span class="px-1.5 py-0.2 rounded text-[9px] font-mono font-medium bg-surface-subtle text-ink-muted border border-surface-border">🌐 번역 대기</span>`}}
            </div>

            <h3 class="font-bold text-sm text-ink-primary leading-snug">
              ${{displayTitle}}
            </h3>

            ${{hookHtml}}

            <p class="text-xs text-ink-secondary leading-relaxed line-clamp-3">
              ${{displayDesc}}
            </p>

            ${{aiSummaryHtml}}
            ${{relatedHtml}}

            <!-- 🌟 Dynamic Metric Tracking (Created vs Updated) -->
            <div class="p-2.5 rounded-xl bg-surface-subtle border border-surface-border text-[11px] space-y-1 font-mono">
              <div class="flex items-center justify-between text-ink-muted">
                <span>${{currentLang === 'KO' ? '최초 수집' : (currentLang === 'ZH' ? '首次采集' : 'Created')}} (${{initDate}}):</span>
                <span class="font-semibold text-ink-secondary">${{initVal}}</span>
              </div>
              <div class="flex items-center justify-between pt-0.5 border-t border-surface-border">
                <span class="text-indigo-950 font-bold">${{currentLang === 'KO' ? '최신 갱신' : (currentLang === 'ZH' ? '最新同步' : 'Latest')}} (${{latestDate}}):</span>
                <div class="flex items-center gap-1 font-bold">
                  <span class="${{delta > 0 ? 'text-emerald-700' : 'text-ink-primary'}}">${{latestVal}}</span>
                  ${{delta > 0 ? `<span class="px-1.5 py-0.2 rounded bg-emerald-50 text-emerald-800 text-[10px] border border-emerald-200">${{deltaDisplay}} 🔺</span>` : ''}}
                </div>
              </div>
            </div>

            <div class="text-[11px] text-ink-muted font-mono pt-1 flex items-center justify-between flex-wrap gap-1">
              <div>📅 <span title="${{currentLang === 'KO' ? '수집/발표 일시' : (currentLang === 'ZH' ? '采集/发布日' : 'Source DateTime')}}" class="text-ink-secondary font-semibold">${{formatDateTime(it.published_at || it.created_at || it.harvested_at)}}</span></div>
              <div class="flex items-center gap-1.5">
                ${{ai?.enriched_at ? `<span title="${{currentLang === 'KO' ? 'AI 분석 일시' : (currentLang === 'ZH' ? 'AI分析日' : 'Analysis DateTime')}}" class="text-indigo-700 font-semibold">🔬 ${{formatDateTime(ai.enriched_at)}}</span>` : ''}}
                ${{ai?.enriched_by_model ? `<span class="px-1.5 py-0.2 rounded text-[9px] font-mono font-medium bg-surface-subtle text-indigo-700 border border-surface-border">🤖 ${{ai.enriched_by_model.replace('gemini-', '')}}</span>` : ''}}
              </div>
            </div>
          </div>

          <div class="pt-3 border-t border-surface-border flex items-center justify-between gap-2">
            <a href="${{it.source_url}}" target="_blank" class="px-3 py-1.5 rounded-lg bg-surface-subtle hover:bg-ink-primary hover:text-white text-ink-primary font-bold transition text-xs flex items-center gap-1">
              <span>${{currentLang === 'KO' ? '원문 보기' : (currentLang === 'ZH' ? '查看原文' : 'View Source')}}</span> <i data-lucide="external-link" class="w-3 h-3"></i>
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
        const res = await fetch(API_BASE + '/api/queue', {{
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

    // ================= STEALTH NAVIGATION ENGINE (ANTI-TRACKING & NO-REFERRER) =================
    const STEALTH_TRACKING_KEYS = new Set([
      'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'utm_id',
      'ref', 'ref_src', 'ref_url', 'source', 'fbclid', 'gclid', 'msclkid', 'twclid',
      'si', 'spm', 'igshid', 'yclid', 'mc_cid', 'mc_eid', 'aff', 'affiliate'
    ]);

    function cleanStealthUrl(rawUrl) {{
      if (!rawUrl) return '';
      try {{
        const u = new URL(rawUrl, window.location.origin);
        if (!u.protocol.startsWith('http')) return rawUrl;
        
        const params = new URLSearchParams(u.search);
        const keysToDelete = [];
        for (const k of params.keys()) {{
          const lk = k.toLowerCase();
          if (STEALTH_TRACKING_KEYS.has(lk) || lk.startsWith('utm_') || lk.includes('chatgpt')) {{
            keysToDelete.push(k);
          }}
        }}
        keysToDelete.forEach(k => params.delete(k));
        u.search = params.toString() ? ('?' + params.toString()) : '';
        return u.toString();
      }} catch (e) {{
        return rawUrl;
      }}
    }}

    function stealthNavigate(rawUrl, ev) {{
      if (ev) {{
        ev.preventDefault();
        ev.stopPropagation();
      }}
      const cleanUrl = cleanStealthUrl(rawUrl);
      
      // Strict stealth window open: No opener, no referrer, isolated context
      const newWin = window.open('', '_blank');
      if (newWin) {{
        newWin.opener = null;
        newWin.location.replace(cleanUrl);
      }} else {{
        const a = document.createElement('a');
        a.href = cleanUrl;
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        a.referrerPolicy = 'no-referrer';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      }}
    }}

    // Global click listener to intercept all external link clicks with stealth protection
    document.addEventListener('click', (e) => {{
      const link = e.target.closest('a');
      if (link && link.href && link.href.startsWith('http') && !link.href.includes(window.location.host)) {{
        e.preventDefault();
        e.stopPropagation();
        stealthNavigate(link.href);
      }}
    }}, true);

    // ================= INITIALIZATION =================
    window.addEventListener('DOMContentLoaded', () => {{
      renderCards();
      renderModels();
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
