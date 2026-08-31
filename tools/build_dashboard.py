#!/usr/bin/env python3
"""
Fact-Check & Engineering Portfolio Dashboard Builder (2026 SOTA Framework - v6.0)
- 🏆 공식 팩트체크 포트폴리오 (Verified Projects)
- 📥 수집 인박스 & 승인 큐 (Inbox & Triage Management - All Candidates)
- ⚙️ 소스별 수집 엔드포인트 & 관리자 통계 (Harvester Admin Stats)
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

def scan_inbox():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    inbox_dir = os.path.join(base_dir, "inbox")
    
    inbox_items = []
    if not os.path.exists(inbox_dir):
        return inbox_items

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
    
    total_cases = len(cases)
    user_curated_count = sum(1 for c in cases if c.get("curation", {}).get("discovery_mode") == "USER_CURATED")
    auto_harvested_count = sum(1 for c in cases if c.get("curation", {}).get("discovery_mode") == "AUTO_HARVESTED")
    
    active_dev_count = sum(1 for c in cases if c.get("portfolio_story", {}).get("hands_on_log", {}).get("status") == "ACTIVE_DEVELOPED")
    halted_count = sum(1 for c in cases if c.get("portfolio_story", {}).get("hands_on_log", {}).get("status") == "EVALUATED_HALTED")
    pending_count = sum(1 for c in cases if c.get("portfolio_story", {}).get("hands_on_log", {}).get("status") == "PENDING_RESEARCH")

    summary_data = {
        "generated_at": "2026-08-31",
        "total_cases": total_cases,
        "inbox_total_count": len(inbox_items),
        "user_curated_count": user_curated_count,
        "auto_harvested_count": auto_harvested_count,
        "active_dev_count": active_dev_count,
        "halted_count": halted_count,
        "pending_count": pending_count,
        "admin_stats": admin_stats,
        "inbox_items": inbox_items,
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

    print(f"[+] Successfully built dashboard v6.0 at:")
    print(f"    - dashboard/index.html (Verified: {total_cases}, Inbox: {len(inbox_items)})")
    print(f"    - docs/index.html (GitHub Pages hosting)")

def generate_html(data):
    cases_json = json.dumps(data["cases"], ensure_ascii=False)
    inbox_json = json.dumps(data["inbox_items"], ensure_ascii=False)
    admin_json = json.dumps(data["admin_stats"], ensure_ascii=False)
    
    return f"""<!DOCTYPE html>
<html lang="ko" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI & Tech Fact-Check Engineering Hub & Inbox</title>
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
    
    .badge-user {{ background: rgba(99, 102, 241, 0.18); color: #a5b4fc; border: 1px solid rgba(99, 102, 241, 0.4); }}
    .badge-auto {{ background: rgba(14, 165, 233, 0.15); color: #38bdf8; border: 1px solid rgba(14, 165, 233, 0.3); }}

    .badge-dev {{ background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }}
    .badge-halted {{ background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }}
    .badge-pending {{ background: rgba(148, 163, 184, 0.15); color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.3); }}
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen">

  <!-- Navigation Bar with View Switcher -->
  <header class="sticky top-0 z-40 glass border-b border-slate-800">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
          <i data-lucide="shield-check" class="w-6 h-6 text-white"></i>
        </div>
        <div>
          <h1 class="text-lg font-bold tracking-tight text-white flex items-center gap-2">
            AI Fact-Check Hub & Inbox
            <span class="text-xs px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-medium border border-indigo-500/30">v6.0</span>
          </h1>
          <p class="text-xs text-slate-400">자율 트렌드 수집 • 인박스 승인 큐 • 엔지니어링 포트폴리오</p>
        </div>
      </div>

      <!-- Main Tab Switcher -->
      <div class="flex items-center gap-2">
        <div class="bg-slate-900/90 p-1 rounded-xl border border-slate-800 flex items-center gap-1">
          <button onclick="switchView('portfolio')" id="tabPortfolioBtn" class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 text-white transition shadow-sm">
            <i data-lucide="award" class="w-4 h-4"></i>
            🏆 공식 포트폴리오 ({data['total_cases']})
          </button>
          <button onclick="switchView('inbox')" id="tabInboxBtn" class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-400 hover:text-white transition">
            <i data-lucide="inbox" class="w-4 h-4 text-amber-400"></i>
            📥 수집 인박스 큐 ({data['inbox_total_count']})
          </button>
        </div>

        <button onclick="openAdminModal()" class="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-slate-900 text-emerald-400 font-medium border border-emerald-500/30 hover:bg-emerald-500/10 transition">
          <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          ⚙️ 수집 관리자
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
          <h2 class="text-2xl sm:text-3xl font-extrabold text-white">
            "소문난 AI 기술, 진짜 작동하고 경제성이 있을까?"
          </h2>
          <p class="text-sm sm:text-base text-slate-300 leading-relaxed">
            내가 직접 문제의식을 갖고 발굴한 <strong>[👤 직접 큐레이션]</strong> 프로젝트와, 
            시스템이 24시간 실시간 트래킹한 <strong>[🤖 자동 트렌드 발굴]</strong> 프로젝트를 
            <strong>명확한 출처(Tier 1~4), 유사 기술 대체재 비교표, 실질 단위 원가 역산</strong>을 통해 입증한 포트폴리오입니다.
          </p>
        </div>
        <div class="absolute -right-10 -bottom-10 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none"></div>
      </div>

      <!-- Metric Cards: Discovery & Hands-on -->
      <div class="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <div class="glass p-4 rounded-xl space-y-1">
          <div class="text-xs font-medium text-slate-400">총 팩트체크 프로젝트</div>
          <div class="text-2xl font-black text-white">{data['total_cases']} <span class="text-xs text-slate-400">Projects</span></div>
        </div>
        <div class="glass p-4 rounded-xl space-y-1 border-indigo-500/30">
          <div class="text-xs font-medium text-indigo-300">👤 직접 문제해결 큐레이션</div>
          <div class="text-2xl font-black text-indigo-400">{data['user_curated_count']} <span class="text-xs text-slate-400">건</span></div>
        </div>
        <div class="glass p-4 rounded-xl space-y-1 border-sky-500/30">
          <div class="text-xs font-medium text-sky-300">🤖 자율 트렌드 감사</div>
          <div class="text-2xl font-black text-sky-400">{data['auto_harvested_count']} <span class="text-xs text-slate-400">건</span></div>
        </div>
        <div class="glass p-4 rounded-xl space-y-1 border-emerald-500/30">
          <div class="text-xs font-medium text-emerald-300">🟢 실제 개발 & 활용 완료</div>
          <div class="text-2xl font-black text-emerald-400">{data['active_dev_count']} <span class="text-xs text-slate-400">건</span></div>
        </div>
        <div class="glass p-4 rounded-xl space-y-1 border-amber-500/30">
          <div class="text-xs font-medium text-amber-300">🟡 성능/과금 개발 중단</div>
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
            <button onclick="setModeFilter('ALL')" class="mode-btn active px-3 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 text-white border border-indigo-500 transition" data-mode="ALL">전체 발굴 경로</button>
            <button onclick="setModeFilter('USER_CURATED')" class="mode-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-900 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-500/10 transition" data-mode="USER_CURATED">👤 내가 직접 큐레이션</button>
            <button onclick="setModeFilter('AUTO_HARVESTED')" class="mode-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-900 text-sky-300 border border-sky-500/30 hover:bg-sky-500/10 transition" data-mode="AUTO_HARVESTED">🤖 자동 트렌드 발굴</button>
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-800">
          <span class="text-xs text-slate-400 mr-2">실측 상태:</span>
          <button onclick="setStageFilter('ALL')" class="stage-btn active px-2.5 py-1 rounded-md text-xs font-medium bg-slate-800 text-white transition" data-stage="ALL">전체</button>
          <button onclick="setStageFilter('ACTIVE_DEVELOPED')" class="stage-btn px-2.5 py-1 rounded-md text-xs font-medium bg-slate-900 text-emerald-400 border border-emerald-500/20 hover:bg-slate-800 transition" data-stage="ACTIVE_DEVELOPED">🟢 개발 완료</button>
          <button onclick="setStageFilter('EVALUATED_HALTED')" class="stage-btn px-2.5 py-1 rounded-md text-xs font-medium bg-slate-900 text-amber-400 border border-amber-500/20 hover:bg-slate-800 transition" data-stage="EVALUATED_HALTED">🟡 개발 중단</button>
          <button onclick="setStageFilter('PENDING_RESEARCH')" class="stage-btn px-2.5 py-1 rounded-md text-xs font-medium bg-slate-900 text-slate-300 border border-slate-700 hover:bg-slate-800 transition" data-stage="PENDING_RESEARCH">⚪ 사전 조사</button>
        </div>
      </div>

      <!-- Case Cards Grid -->
      <div id="cardsGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"></div>
    </div>

    <!-- ==================== VIEW 2: INBOX & TRIAGE VIEW ==================== -->
    <div id="inboxView" class="hidden space-y-6">
      
      <!-- Inbox Header & Explanation -->
      <div class="glass p-6 rounded-2xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-amber-500/20">
        <div class="space-y-1">
          <div class="flex items-center gap-2">
            <span class="px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 text-xs font-bold border border-amber-500/30">
              📥 미승인 트렌드 대기 큐 (Inbox Queue)
            </span>
            <span class="text-xs text-slate-400">총 {data['inbox_total_count']}건 대기 중</span>
          </div>
          <h2 class="text-xl font-bold text-white">"수집된 최신 기술 중 마음에 드는 것만 골라 승인하세요"</h2>
          <p class="text-xs text-slate-300">
            허깅페이스 스페이스, 깃허브, 아카이브, 해커뉴스에서 자동 수집된 후보들입니다. 
            원문을 직접 확인하고 <strong>[승격 명령어 복사]</strong>를 눌러 터미널에서 승인하면 공식 포트폴리오로 즉시 승격됩니다.
          </p>
        </div>

        <div class="bg-slate-900/90 p-3 rounded-xl border border-slate-800 text-xs space-y-1 shrink-0">
          <div class="text-slate-400 font-semibold">💡 일괄 승격 명령어:</div>
          <code class="text-amber-300 bg-black/50 px-2 py-0.5 rounded font-mono block">python tools/triage.py --promote-top 3</code>
        </div>
      </div>

      <!-- Inbox Filters & Search -->
      <div class="glass p-4 rounded-xl flex flex-col md:flex-row items-center justify-between gap-4">
        <div class="relative w-full md:w-80">
          <i data-lucide="search" class="w-4 h-4 absolute left-3.5 top-3 text-slate-400"></i>
          <input type="text" id="inboxSearchInput" placeholder="인박스 후보 검색..." 
                 class="w-full bg-slate-900/80 border border-slate-700/60 rounded-lg pl-10 pr-4 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500 transition">
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

  <!-- Admin & Harvester Monitoring Modal -->
  <div id="adminModal" class="fixed inset-0 z-50 bg-black/85 backdrop-blur-sm hidden flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
    <div class="glass max-w-3xl w-full rounded-2xl overflow-hidden shadow-2xl border border-slate-700 my-8">
      <div class="p-6 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
        <div class="flex items-center gap-2.5">
          <i data-lucide="settings" class="w-5 h-5 text-emerald-400"></i>
          <div>
            <h3 class="text-base font-bold text-white">수집 시스템 관리자 & 엔드포인트 모니터</h3>
            <p class="text-xs text-slate-400">어떤 링크에서 매번 수집하고 있는지 실시간 감시</p>
          </div>
        </div>
        <button onclick="closeAdminModal()" class="text-slate-400 hover:text-white p-1 rounded-lg bg-slate-800/60 hover:bg-slate-700">
          <i data-lucide="x" class="w-5 h-5"></i>
        </button>
      </div>

      <div class="p-6 space-y-6 text-xs text-slate-300 max-h-[75vh] overflow-y-auto">
        
        <!-- Summary Counters -->
        <div class="grid grid-cols-3 gap-3">
          <div class="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
            <span class="text-slate-400">최근 수집 일시</span>
            <div id="adminLatestDate" class="text-xs font-bold text-white mt-1"></div>
          </div>
          <div class="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
            <span class="text-slate-400">현재 대기 인박스</span>
            <div class="text-sm font-bold text-amber-400 mt-1">{data['inbox_total_count']} 건</div>
          </div>
          <div class="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
            <span class="text-slate-400">공식 승격 프로젝트</span>
            <div class="text-sm font-bold text-emerald-400 mt-1">{data['total_cases']} 건</div>
          </div>
        </div>

        <!-- Registered Harvester Endpoints -->
        <div>
          <h4 class="font-bold text-slate-200 mb-2 flex items-center gap-1.5 text-sm">
            <i data-lucide="radio" class="w-4 h-4 text-indigo-400"></i> 등록된 정기 수집 엔드포인트 목록
          </h4>
          <div id="adminEndpointsList" class="space-y-2"></div>
        </div>

        <!-- Latest Run Health Logs -->
        <div>
          <h4 class="font-bold text-slate-200 mb-2 flex items-center gap-1.5 text-sm">
            <i data-lucide="activity" class="w-4 h-4 text-emerald-400"></i> 최근 수집 실행 헬스 & 레이턴시
          </h4>
          <div id="adminHealthLogs" class="space-y-2"></div>
        </div>

      </div>

      <div class="p-4 border-t border-slate-800 bg-slate-900/60 flex justify-end">
        <button onclick="closeAdminModal()" class="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold">닫기</button>
      </div>
    </div>
  </div>

  <!-- Detailed Portfolio Modal -->
  <div id="detailModal" class="fixed inset-0 z-50 bg-black/85 backdrop-blur-sm hidden flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
    <div class="glass max-w-4xl w-full rounded-2xl overflow-hidden shadow-2xl border border-slate-700/80 my-8 max-h-[92vh] flex flex-col">
      <!-- Modal Header -->
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

      <!-- Modal Body -->
      <div class="p-6 overflow-y-auto space-y-6 text-sm text-slate-200">
        
        <!-- Curation Motivation Box (Personal Intent) -->
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

      <!-- Modal Footer -->
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

    let currentView = 'portfolio';
    let currentMode = 'ALL';
    let currentStage = 'ALL';
    let searchQuery = '';

    let currentInboxSource = 'ALL';
    let inboxSearchQuery = '';

    function switchView(view) {{
      currentView = view;
      const portView = document.getElementById('portfolioView');
      const inView = document.getElementById('inboxView');
      const pBtn = document.getElementById('tabPortfolioBtn');
      const iBtn = document.getElementById('tabInboxBtn');

      if (view === 'portfolio') {{
        portView.classList.remove('hidden');
        inView.classList.add('hidden');
        pBtn.className = 'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 text-white transition shadow-sm';
        iBtn.className = 'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-400 hover:text-white transition';
        renderCards();
      }} else {{
        portView.classList.add('hidden');
        inView.classList.remove('hidden');
        pBtn.className = 'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-400 hover:text-white transition';
        iBtn.className = 'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-amber-600 text-white transition shadow-sm';
        renderInbox();
      }}
      lucide.createIcons();
    }}

    function copyToClipboard(text) {{
      navigator.clipboard.writeText(text).then(() => {{
        const toast = document.getElementById('toast');
        document.getElementById('toastMsg').innerText = '승격 명령어가 클립보드에 복사되었습니다:\\n' + text;
        toast.classList.remove('hidden');
        setTimeout(() => toast.classList.add('hidden'), 4000);
      }});
    }}

    function renderInbox() {{
      const grid = document.getElementById('inboxGrid');
      grid.innerHTML = '';

      const filtered = inboxData.filter(item => {{
        const matchesSrc = currentInboxSource === 'ALL' || (item.source_platform && item.source_platform.includes(currentInboxSource));
        const text = (item.title + ' ' + (item.description || '') + ' ' + (item.source_platform || '')).toLowerCase();
        const matchesSearch = text.includes(inboxSearchQuery.toLowerCase());
        return matchesSrc && matchesSearch;
      }});

      if (filtered.length === 0) {{
        grid.innerHTML = '<div class="col-span-full py-16 text-center text-slate-500">인박스에 일치하는 후보가 없습니다.</div>';
        return;
      }}

      filtered.forEach((it, idx) => {{
        const card = document.createElement('div');
        card.className = 'glass-card p-4 rounded-xl flex flex-col justify-between space-y-3 border-slate-800';

        const promoteCmd = `python tools/triage.py --promote ${{it.inbox_id}}`;

        card.innerHTML = `
          <div class="space-y-2.5">
            <div class="flex items-center justify-between text-xs gap-1">
              <span class="px-2 py-0.5 rounded text-[11px] font-bold bg-amber-500/10 text-amber-300 border border-amber-500/20 truncate">
                ${{it.source_platform || 'Tech'}}
              </span>
              <span class="text-[11px] font-medium text-slate-400 shrink-0">
                ${{it.viral_metric || 'Viral'}}
              </span>
            </div>

            <h4 class="font-bold text-sm text-white line-clamp-2 hover:text-amber-300 transition">
              ${{it.title}}
            </h4>

            <p class="text-xs text-slate-300 line-clamp-2 leading-relaxed">
              ${{it.description || '상세 내용 없음'}}
            </p>

            <div class="text-[11px] text-slate-400">
              🎯 맞춤 도메인: <span class="text-indigo-300">${{(it.matched_user_domains || ['일반']).join(', ')}}</span>
            </div>
          </div>

          <div class="pt-3 border-t border-slate-800/80 flex items-center justify-between gap-2">
            <a href="${{it.source_url}}" target="_blank" class="text-xs text-slate-400 hover:text-white flex items-center gap-1">
              원문 링크 <i data-lucide="external-link" class="w-3 h-3"></i>
            </a>

            <button onclick="copyToClipboard('${{promoteCmd}}')" class="px-2.5 py-1 rounded bg-amber-600/20 hover:bg-amber-600 text-amber-300 hover:text-white text-xs font-semibold border border-amber-500/30 transition flex items-center gap-1">
              <i data-lucide="copy" class="w-3 h-3"></i> 승격 명령 복사
            </button>
          </div>
        `;
        grid.appendChild(card);
      }});

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

    function openAdminModal() {{
      if (adminData) {{
        document.getElementById('adminLatestDate').innerText = adminData.latest_run ? adminData.latest_run.timestamp : '2026-08-31';

        // Render Endpoints
        const epList = document.getElementById('adminEndpointsList');
        epList.innerHTML = '';
        if (adminData.endpoints) {{
          adminData.endpoints.forEach(ep => {{
            const div = document.createElement('div');
            div.className = 'p-2.5 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between text-xs';
            div.innerHTML = `
              <div class="space-y-0.5 truncate pr-2">
                <div class="font-bold text-white flex items-center gap-1.5">
                  <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
                  ${{ep.name}} <span class="text-[10px] text-slate-400 font-normal">(${{ep.type}})</span>
                </div>
                <div class="text-[11px] text-indigo-300 truncate font-mono">${{ep.url}}</div>
              </div>
              <span class="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 border border-slate-700 shrink-0 font-medium">${{ep.auth}}</span>
            `;
            epList.appendChild(div);
          }});
        }}

        // Render Health Logs
        const hLogs = document.getElementById('adminHealthLogs');
        hLogs.innerHTML = '';
        if (adminData.latest_run && adminData.latest_run.sources) {{
          Object.entries(adminData.latest_run.sources).forEach(([src, info]) => {{
            const isSuccess = info.status === 'SUCCESS';
            const div = document.createElement('div');
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
            hLogs.appendChild(div);
          }});
        }}
      }}
      document.getElementById('adminModal').classList.remove('hidden');
      lucide.createIcons();
    }}

    function closeAdminModal() {{
      document.getElementById('adminModal').classList.add('hidden');
    }}

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
        grid.innerHTML = '<div class="col-span-full py-16 text-center text-slate-500">조건에 맞는 팩트체크 케이스가 없습니다.</div>';
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
                ${{isUserMode ? '👤 직접 큐레이션' : '🤖 자동 트렌드 발굴'}}
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
                ${{isUserMode ? '직접 발굴한 문제의식' : '트렌드 감사 동기'}}
              </span>
              <p class="text-xs text-slate-300 line-clamp-2">${{curation.personal_motivation || story.the_hook || '분석 진행 중'}}</p>
            </div>
          </div>

          <div class="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
            <span class="flex items-center gap-1">
              <i data-lucide="link" class="w-3 h-3"></i> 출처 ${{c.sources ? c.sources.length : 1}}개 감사
            </span>
            <span class="text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1">
              상세 분석 및 대체재 보기 <i data-lucide="chevron-right" class="w-3.5 h-3.5"></i>
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
      mBadge.innerText = isUserMode ? '👤 직접 문제해결 큐레이션' : '🤖 자율 트렌드 감사 발굴';

      document.getElementById('modalClusterBadge').innerText = clustering.cluster_name || (c.category || 'Tech');
      
      const vBadge = document.getElementById('modalVerdictBadge');
      vBadge.className = 'text-xs px-2.5 py-0.5 rounded-md font-semibold ' + getVerdictBadgeClass(c.verdict);
      vBadge.innerText = getVerdictLabel(c.verdict);

      const sBadge = document.getElementById('modalStageBadge');
      sBadge.className = 'text-xs px-2.5 py-0.5 rounded-md font-medium ' + stageInfo.class;
      sBadge.innerText = stageInfo.label;

      document.getElementById('modalTitle').innerText = c.title;

      // Curation Motivation Box
      const cBox = document.getElementById('modalCurationBox');
      cBox.className = 'p-4 rounded-xl border space-y-1.5 ' + (isUserMode ? 'bg-indigo-950/30 border-indigo-500/30' : 'bg-sky-950/30 border-sky-500/30');
      document.getElementById('modalCurationTitle').className = 'text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 ' + (isUserMode ? 'text-indigo-300' : 'text-sky-300');
      document.getElementById('modalCuratorName').innerText = 'Curator: ' + (curation.curator || 'Anyong Cheong');
      document.getElementById('modalPersonalMotivation').innerText = curation.personal_motivation || story.the_hook || '내용 없음';
      document.getElementById('modalTargetWorkflow').innerText = curation.target_workflow || '일반 엔지니어링 파이프라인';

      // Alternatives Table
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
    document.getElementById('adminModal').addEventListener('click', (e) => {{
      if (e.target.id === 'adminModal') closeAdminModal();
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
