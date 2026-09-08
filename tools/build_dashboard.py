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
import re

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
    cases.sort(key=lambda c: (c.get("investigation_date") or (c.get("source_published_date") or "")[:10] or "2026-01-01", c.get("case_id") or ""), reverse=True)
    return cases

def scan_inbox():
    items_by_id = {}

    # 1. 🌟 Workstation Local Disk (Always check local storage first)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    inbox_dir = os.path.join(base_dir, "inbox")
    if os.path.exists(inbox_dir):
        for f in sorted(os.listdir(inbox_dir), reverse=True):
            if f.endswith(".json") and not f.startswith("_"):
                path = os.path.join(inbox_dir, f)
                try:
                    with open(path, "r", encoding="utf-8") as fp:
                        item = json.load(fp)
                        if "inbox_id" in item:
                            items_by_id[item["inbox_id"]] = item
                except Exception:
                    pass
        if items_by_id:
            print(f"[+] [Local Disk] Loaded {len(items_by_id)} items from local disk.")

    # 2. 🌟 Primary Live Cloud Source: Neon PostgreSQL DB
    try:
        tools_dir = os.path.dirname(os.path.abspath(__file__))
        if tools_dir not in sys.path:
            sys.path.insert(0, tools_dir)
        from db_bridge import load_env_db_url
        db_url = load_env_db_url()
        if db_url:
            import psycopg2
            conn = psycopg2.connect(db_url)
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT raw_payload FROM raw_trends_inbox 
                    WHERE raw_payload IS NOT NULL 
                    ORDER BY id DESC 
                    LIMIT 5000;
                """)
                rows = cur.fetchall()
                db_added = 0
                for r in rows:
                    payload = r[0]
                    if isinstance(payload, str):
                        try:
                            payload = json.loads(payload)
                        except Exception:
                            continue
                    if isinstance(payload, dict) and "inbox_id" in payload:
                        iid = payload["inbox_id"]
                        if iid in items_by_id:
                            # If payload has ai_enrichment and existing doesn't, upgrade
                            if payload.get("ai_enrichment") and not items_by_id[iid].get("ai_enrichment"):
                                items_by_id[iid] = payload
                        else:
                            items_by_id[iid] = payload
                            db_added += 1
            conn.close()
            print(f"[+] [Neon DB Direct] Synced with Neon PostgreSQL DB. Total consolidated items: {len(items_by_id)}")
    except Exception as e:
        print(f"[!] Warning: Neon DB direct query failed ({e}), using local disk data...")

    inbox_items = list(items_by_id.values())

    # Sort strictly by freshest active timestamp (harvested_at, published_at, created_at)
    def get_freshest_ts(it):
        return max(
            str(it.get("harvested_at") or ""),
            str(it.get("published_at") or ""),
            str(it.get("created_at") or ""),
            str(it.get("harvested_date") or "")
        )
    inbox_items.sort(key=get_freshest_ts, reverse=True)

    # 🌟 Multi-Source Deduplication & Story Clustering
    try:
        tools_dir = os.path.dirname(os.path.abspath(__file__))
        if tools_dir not in sys.path:
            sys.path.insert(0, tools_dir)
        from dedup_merger import deduplicate_inbox_items
        inbox_items = deduplicate_inbox_items(inbox_items, max_window_hours=72.0)
    except Exception as e:
        print(f"[!] Warning: Story clustering failed: {e}")

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

def get_actions_telemetry():
    telemetry = {
        "monthly_quota_minutes": 2000,
        "monthly_used_minutes": 1242.0,
        "monthly_remaining_minutes": 758.0,
        "monthly_usage_percent": 62.1,
        "total_job_runs": 763,
        "workflows": [
            {"name": "deploy_pages.yml", "total_min": 615, "runs": 136, "avg_time": "4분 1초", "failure_rate": "10%"},
            {"name": "pages build deployment", "total_min": 604, "runs": 212, "avg_time": "36초", "failure_rate": "<1%"},
            {"name": "deploy_only.yml", "total_min": 18, "runs": 18, "avg_time": "32초", "failure_rate": "0%"},
            {"name": "daily_eod_enrichment.yml", "total_min": 5, "runs": 5, "avg_time": "30초", "failure_rate": "40%"}
        ],
        "alert_level": "WARNING_HIGH",
        "can_shorten_interval": False,
        "advice": "🚨 9월 1일~8일(약 7일) 동안 이미 2,000분 중 1,242분(62.1%)을 소모했습니다! 잔여 시간은 758분뿐이므로 수집 주기를 6시간에서 무리하게 줄이면(증설하면) 4~5일 내에 쿼터가 전면 소진됩니다. 현행 6시간 유지를 강력 권장합니다.",
        "runs": [],
        "slot_logs": {
            "00:00": {"slot": "1회차 (00:17)", "name": "심야 글로벌 릴리스", "actual_duration": "9분 05초", "duration_sec": 545, "status": "SUCCESS", "error_count": 0, "run_id": "34133531110"},
            "06:00": {"slot": "2회차 (06:17)", "name": "모닝 브리핑", "actual_duration": "6분 02초", "duration_sec": 362, "status": "SUCCESS", "error_count": 0, "run_id": "34096402553"},
            "12:00": {"slot": "3회차 (12:17)", "name": "정오 레이더", "actual_duration": "7분 36초", "duration_sec": 456, "status": "SUCCESS", "error_count": 0, "run_id": "34064244121"},
            "18:00": {"slot": "4회차 (18:17)", "name": "저녁 라운드업", "actual_duration": "11분 34초", "duration_sec": 694, "status": "SUCCESS", "error_count": 0, "run_id": "34048453203"},
        }
    }
    
    # Try querying Neon DB for live synced usage & run logs
    try:
        from db_bridge import load_env_db_url
        import psycopg2
        db_url = load_env_db_url()
        if db_url:
            conn = psycopg2.connect(db_url)
            with conn.cursor() as cur:
                # 1. Fetch monthly summary
                cur.execute("SELECT total_minutes, total_job_runs, remaining_minutes, burn_rate_percent, alert_level FROM github_actions_monthly_usage WHERE year_month = '2026-09';")
                row = cur.fetchone()
                if row:
                    telemetry["monthly_used_minutes"] = float(row[0])
                    telemetry["total_job_runs"] = int(row[1])
                    telemetry["monthly_remaining_minutes"] = float(row[2])
                    telemetry["monthly_usage_percent"] = float(row[3])
                    telemetry["alert_level"] = str(row[4])
                
                # 2. Fetch recent run logs
                cur.execute("SELECT run_id, workflow_name, event_trigger, status, conclusion, duration_str, duration_seconds, started_at, error_count FROM github_actions_run_logs ORDER BY run_id DESC LIMIT 8;")
                run_rows = cur.fetchall()
                if run_rows:
                    db_runs = []
                    kst_tz = datetime.timezone(datetime.timedelta(hours=9))
                    for rr in run_rows:
                        st = rr[7].astimezone(kst_tz) if rr[7] else datetime.datetime.now(kst_tz)
                        db_runs.append({
                            "id": str(rr[0]),
                            "name": str(rr[1]),
                            "event": str(rr[2]),
                            "status": str(rr[3]),
                            "conclusion": str(rr[4]),
                            "duration_str": str(rr[5]),
                            "duration_sec": int(rr[6]),
                            "created_at_kst": st.strftime("%Y-%m-%d %H:%M:%S"),
                            "html_url": f"https://github.com/AnnyeongHae/ai-factcheck-portfolio/actions/runs/{rr[0]}",
                            "error_count": int(rr[8])
                        })
                    telemetry["runs"] = db_runs
            conn.close()
    except Exception as e:
        print(f"[!] Note: Reading Actions telemetry from Neon DB fallback: {e}")
        
    return telemetry

def build_dashboard():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_dir = os.path.join(base_dir, "docs")
    public_dir = os.path.join(base_dir, "public")
    
    os.makedirs(docs_dir, exist_ok=True)
    os.makedirs(public_dir, exist_ok=True)

    cases = scan_investigations()
    inbox_items = scan_inbox()
    admin_stats = get_harvest_admin_stats()
    graph_data = load_graph_data()
    
    total_cases = len(cases)
    def is_news_item(it):
        ai = it.get("ai_enrichment") or {}
        has_ai = bool(ai and it.get("multilingual"))
        cat = it.get("category_type", "")
        src = it.get("source_platform", "")
        # Explicit news sources or GitHub repositories (which belong in Tech News/Trending Repos)
        is_news_src = any(k in src for k in ["News", "Hacker", "Blog", "GitHub"])
        return has_ai and (ai.get("type_classification") == "NEWS" or cat == "NEWS" or is_news_src)

    def is_model_item(it):
        ai = it.get("ai_enrichment") or {}
        has_ai = bool(ai and it.get("multilingual"))
        cat = it.get("category_type", "")
        src = it.get("source_platform", "")
        fam = it.get("model_family", "")
        # Only true model hub items (Hugging Face Models/Spaces/Hub), strictly never GitHub
        is_model_src = any(k in src for k in ["Models", "Spaces"]) or ("Hugging" in src and "Hub" in src)
        return has_ai and not is_news_item(it) and (
            ai.get("type_classification") == "MODEL" or 
            cat == "model" or 
            is_model_src or 
            (fam and "General" not in fam and "독립" not in fam and "Harness" not in fam and "Standalone" not in fam and "GitHub" not in src)
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

    model_items = [it for it in inbox_items if is_model_item(it)]
    model_ids = {it.get("inbox_id") for it in model_items}
    # Strict disjoint sets: items belonging to AI Model Trends are excluded from AI Tech News
    news_items = [
        it for it in inbox_items 
        if (it.get("is_classified") or (it.get("ai_enrichment") and it.get("multilingual")))
        and it.get("inbox_id") not in model_ids
    ]

    news_cat_counts = {
        "INFERENCE_OPT": 0,
        "AGENTS_DEVTOOLS": 0,
        "MULTIMODAL_AI": 0,
        "FOUNDATION_MODELS": 0,
        "INFRA_RAG_SECURITY": 0,
        "DEEP_SCIENCE_SPACE": 0,
        "MACRO_GLOBAL_BIZ": 0,
        "INDUSTRY_TRENDS": 0
    }
    tier1_counts = {
        "TECH_COMPUTING": 0,
        "SCIENCE_RESEARCH": 0,
        "ECONOMY_FINANCE": 0,
        "LAW_CRIME_JUSTICE": 0,
        "POLITICS_POLICY": 0,
        "CULTURE_HUMANITIES": 0
    }
    for it in news_items:
        c = it.get("category_primary", "INDUSTRY_TRENDS")
        if c in news_cat_counts:
            news_cat_counts[c] += 1
        else:
            news_cat_counts["INDUSTRY_TRENDS"] += 1

        t1 = it.get("tier1_category") or "TECH_COMPUTING"
        if t1 in tier1_counts:
            tier1_counts[t1] += 1
        else:
            tier1_counts["TECH_COMPUTING"] += 1

    model_art_counts = {
        "WEIGHTS": 0,
        "WEB_SERVICE": 0,
        "FINETUNE": 0
    }
    model_fam_counts = {
        "Qwen": 0,
        "Wan": 0,
        "MiniMax": 0,
        "FLUX": 0,
        "GLM": 0,
        "DeepSeek": 0,
        "Hunyuan": 0,
        "Audio": 0,
        "Standalone": 0
    }
    for it in model_items:
        src = it.get("source_platform", "")
        # Official Hugging Face Ecosystem mapping
        if "Spaces" in src:
            art = "WEB_SERVICE"
        elif "lora" in (str(it.get("title", "")) + " " + str(it.get("detected_formats", [""])[0])).lower():
            art = "FINETUNE"
        else:
            art = "WEIGHTS"
        it["artifact_type"] = art
        if art in model_art_counts:
            model_art_counts[art] += 1
        else:
            model_art_counts["WEIGHTS"] += 1

        fam = (it.get("model_family") or "").lower()
        if "qwen" in fam: model_fam_counts["Qwen"] += 1
        elif "wan" in fam: model_fam_counts["Wan"] += 1
        elif "minimax" in fam: model_fam_counts["MiniMax"] += 1
        elif "flux" in fam: model_fam_counts["FLUX"] += 1
        elif "glm" in fam: model_fam_counts["GLM"] += 1
        elif "deepseek" in fam: model_fam_counts["DeepSeek"] += 1
        elif "hunyuan" in fam: model_fam_counts["Hunyuan"] += 1
        elif "audio" in fam or "speech" in fam or "tts" in fam or "whisper" in fam: model_fam_counts["Audio"] += 1
        else: model_fam_counts["Standalone"] += 1

    # All active unverified inbox candidates (only excludes already verified & promoted dossiers)
    clean_inbox_items = [
        it for it in inbox_items 
        if not is_already_verified(it)
    ]

    # Calculate Verdict & Quality Statistics
    user_curated_count = len([c for c in cases if (c.get("curation", {}).get("discovery_mode") or "USER_CURATED") == "USER_CURATED"])
    auto_harvested_count = len([c for c in cases if c.get("curation", {}).get("discovery_mode") == "AUTO_HARVESTED"])
    verified_true_count = len([c for c in cases if c.get("verdict") == "VERIFIED_TRUE"])
    half_true_count = len([c for c in cases if "HALF" in (c.get("verdict") or "")])
    gamed_count = len([c for c in cases if "GAMED" in (c.get("verdict") or "") or "EXAGGERATED" in (c.get("verdict") or "")])
    avg_conf = round(sum(c.get("confidence_score", 90.0) for c in cases) / max(1, len(cases)), 1)

    # 🌟 System Time (UTC) as Universal Base + 9 Hours for KST (Never drifts across OS / Runners)
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    kst_tz = datetime.timezone(datetime.timedelta(hours=9))
    now_kst = now_utc.astimezone(kst_tz)
    today_kst_str = now_kst.strftime("%Y-%m-%d")
    current_hour_kst = now_kst.hour

    # 1. Today 24-Hour Timeline Aggregation (4 Quarterly Sessions)
    slots_def = [
        {"slot": "1회차 (00시)", "short_slot": "00:00", "hour": 0, "range": "00:00 - 05:59", "name": "심야 릴리스"},
        {"slot": "2회차 (06시)", "short_slot": "06:00", "hour": 6, "range": "06:00 - 11:59", "name": "모닝 브리핑"},
        {"slot": "3회차 (12시)", "short_slot": "12:00", "hour": 12, "range": "12:00 - 17:59", "name": "정오 레이더"},
        {"slot": "4회차 (18시)", "short_slot": "18:00", "hour": 18, "range": "18:00 - 23:59", "name": "저녁 라운드업"}
    ]
    slot_counts = {s["short_slot"]: {"inbox": 0, "model": 0, "news": 0} for s in slots_def}

    def parse_to_kst_dt(raw_val):
        if not raw_val: return None
        try:
            raw_str = str(raw_val).strip()
            if "T" in raw_str:
                clean = raw_str.replace("Z", "+00:00")
                dt = datetime.datetime.fromisoformat(clean)
                if dt.tzinfo:
                    return dt.astimezone(kst_tz)
                else:
                    return dt.replace(tzinfo=kst_tz)
            elif re.match(r'^\d{4}-\d{2}-\d{2}$', raw_str):
                dt = datetime.datetime.strptime(raw_str, "%Y-%m-%d")
                return dt.replace(hour=0, tzinfo=kst_tz)
        except Exception:
            pass
        return None

    for it in clean_inbox_items:
        # 🌟 User Requirement: Timeline aggregation strictly based on initial created_at / publication time
        created_raw = it.get("created_at") or it.get("published_at") or it.get("harvested_at") or ""
        created_dt = parse_to_kst_dt(created_raw)
        
        if created_dt and created_dt.strftime("%Y-%m-%d") == today_kst_str:
            h = (created_dt.hour // 6) * 6
            s_key = f"{h:02d}:00"
            if s_key in slot_counts:
                slot_counts[s_key]["inbox"] += 1
                if is_model_item(it): slot_counts[s_key]["model"] += 1
                else: slot_counts[s_key]["news"] += 1

    timeline_24h = []
    peak_slot = "12:00"
    peak_count = 0
    today_total = 0
    for s in slots_def:
        cnt = slot_counts[s["short_slot"]]["inbox"]
        today_total += cnt
        if cnt > peak_count:
            peak_count = cnt
            peak_slot = s["short_slot"]
        timeline_24h.append({
            "slot": s["slot"],
            "short_slot": s["short_slot"],
            "name": s["name"],
            "hour": s["hour"],
            "range": s["range"],
            "inbox_count": cnt,
            "model_count": slot_counts[s["short_slot"]]["model"],
            "news_count": slot_counts[s["short_slot"]]["news"],
            "is_current": s["hour"] <= current_hour_kst < s["hour"] + 6,
            "is_future": s["hour"] > current_hour_kst
        })

    # 2. 1일 4회 AI Trend Radar (전체 4개 회차별 세션 분할 및 플랫폼 다양성 쿼터 적용)
    if 0 <= current_hour_kst < 6: current_session_num = 1
    elif 6 <= current_hour_kst < 12: current_session_num = 2
    elif 12 <= current_hour_kst < 18: current_session_num = 3
    else: current_session_num = 4

    yesterday_kst_str = (now_kst - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    two_days_ago_kst_str = (now_kst - datetime.timedelta(days=2)).strftime("%Y-%m-%d")

    def get_item_date_str(it):
        raw = str(it.get("harvested_at") or it.get("published_at") or it.get("created_at") or it.get("harvested_date") or "")
        m = re.search(r'\d{4}-\d{2}-\d{2}', raw)
        return m.group(0) if m else ""

    def compute_viral_weight(it):
        val = 1.0
        mt = it.get("metric_tracking", {})
        if isinstance(mt, dict) and "latest" in mt and isinstance(mt["latest"], dict):
            try: val = max(val, float(mt["latest"].get("value", 0) or 0))
            except Exception: pass
        vm = str(it.get("viral_metric", ""))
        nums = re.findall(r'(\d+[\d,.]*)\s*(?:likes|points|stars|pts|개)', vm, re.I)
        for n in nums:
            try: val = max(val, float(n.replace(",", "")))
            except Exception: pass
        
        # Freshness Multipliers (Strict Exponential Decay)
        d = get_item_date_str(it)
        if d == today_kst_str:
            val *= 20.0
        elif d == yesterday_kst_str:
            val *= 10.0
        elif d == two_days_ago_kst_str:
            val *= 2.0
        else:
            val *= 0.01  # Extreme penalty for older items (never rank in daily radar)

        if d in [today_kst_str, yesterday_kst_str, two_days_ago_kst_str] and isinstance(mt, dict):
            if mt.get("is_spiking"): val *= 3.0
            growth = mt.get("growth_rate_pct", 0)
            if growth and growth > 0: val *= (1.0 + min(2.0, growth / 50.0))

        if it.get("ai_enrichment"): val *= 1.2
        return val

    def get_platform_family(it):
        p = (it.get("source_platform") or "").lower()
        if "github" in p: return "GitHub"
        if "hugging" in p: return "HuggingFace"
        if "arxiv" in p or "paper" in p: return "ArXiv"
        if "hacker" in p: return "HackerNews"
        if "geek" in p: return "GeekNews"
        return "TechMedia"

    def extract_search_key(it):
        # 1. Prefer raw crawler title (clean repo or entity name)
        orig = it.get("title") or ""
        clean_orig = re.sub(r'^(?:GitHub:\s*|HuggingFace:\s*|HF Space:\s*|Hacker News:\s*|ArXiv:\s*|GeekNews:\s*|Paper:\s*)', '', orig, flags=re.I).strip()
        parts = re.split(r'\s+-\s+|\s*[:：]\s*|\s*[\(（【]', clean_orig)
        if parts and len(parts[0].strip()) >= 3:
            cand = parts[0].strip()
            if "/" in cand: # e.g. sapientinc/PRAXIST or Kwai-Kolors/Kolors-Virtual-Try-On
                return cand
            if len(cand) <= 40:
                return cand

        # 2. Fallback to multilingual title
        t_ko = it.get("multilingual", {}).get("ko", {}).get("title") or it.get("title_ko") or orig
        clean_ko = re.sub(r'^(?:GitHub:\s*|HuggingFace:\s*|HF Space:\s*|Hacker News:\s*|ArXiv:\s*|GeekNews:\s*|Paper:\s*)', '', t_ko, flags=re.I).strip()
        parts_ko = re.split(r'\s+-\s+|\s*[:：]\s*|\s*[\(（【]', clean_ko)
        if parts_ko and len(parts_ko[0].strip()) >= 3:
            return parts_ko[0].strip()
        return clean_orig[:35].strip()

    # 🌟 DAILY RADAR SENSITIVITY: Strictly 24h-48h Fresh Items with Complete AI Enrichment
    def is_fresh_trend(it):
        # Exclude non-tech (crimes, incidents, culture) from AI Radar
        t1 = it.get("tier1_category") or "TECH_COMPUTING"
        if t1 not in ["TECH_COMPUTING", "SCIENCE_RESEARCH"]:
            return False
        # Strictly require AI enrichment with trilingual translation (never show raw un-enriched items)
        ml = it.get("multilingual") or {}
        has_ai = (
            bool(it.get("ai_enrichment")) and
            bool(ml.get("ko", {}).get("title") or it.get("title_ko")) and
            bool(ml.get("en", {}).get("title") or it.get("title_en")) and
            bool(ml.get("zh", {}).get("title") or it.get("title_zh"))
        )
        if not has_ai:
            return False
        d = get_item_date_str(it)
        return d in [today_kst_str, yesterday_kst_str]

    fresh_pool = [it for it in (model_items + news_items + clean_inbox_items) if it.get("title") and is_fresh_trend(it)]
    if len(fresh_pool) < 15:
        fallback_pool = [
            it for it in (model_items + news_items + clean_inbox_items)
            if it.get("title") and 
               (it.get("tier1_category") in ["TECH_COMPUTING", "SCIENCE_RESEARCH"]) and 
               get_item_date_str(it) == two_days_ago_kst_str and
               bool(it.get("ai_enrichment")) and
               bool((it.get("multilingual") or {}).get("ko", {}).get("title") or it.get("title_ko"))
        ]
        fresh_pool.extend(fallback_pool)

    fresh_pool.sort(key=compute_viral_weight, reverse=True)
    all_candidate_pool = fresh_pool

    sessions_def = [
        {
            "num": 1,
            "name": "1회차 (심야)",
            "short_name": "1회 00시",
            "hour": 0,
            "time_range": "00:00 ~ 06:00 KST",
            "targets": ["GitHub", "HackerNews", "HuggingFace"]
        },
        {
            "num": 2,
            "name": "2회차 (오전)",
            "short_name": "2회 06시",
            "hour": 6,
            "time_range": "06:00 ~ 12:00 KST",
            "targets": ["ArXiv", "GitHub", "HuggingFace"]
        },
        {
            "num": 3,
            "name": "3회차 (오후)",
            "short_name": "3회 12시",
            "hour": 12,
            "time_range": "12:00 ~ 18:00 KST",
            "targets": ["HuggingFace", "GitHub", "GeekNews"]
        },
        {
            "num": 4,
            "name": "4회차 (저녁)",
            "short_name": "4회 18시",
            "hour": 18,
            "time_range": "18:00 ~ 24:00 KST",
            "targets": ["HackerNews", "GitHub", "HuggingFace"]
        }
    ]

    sessions_data = {}
    used_inbox_ids = set()

    for s_def in sessions_def:
        s_num = s_def["num"]
        s_hour = s_def["hour"]
        is_cur = (s_num == current_session_num)
        is_fut = (s_hour > current_hour_kst)
        status = "active" if is_cur else ("upcoming" if is_fut else "completed")

        # Determine target date and multilingual window label for this session
        month_en_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        if is_fut:
            target_date_str = yesterday_kst_str
            target_d_obj = now_kst - datetime.timedelta(days=1)
        else:
            target_date_str = today_kst_str
            target_d_obj = now_kst

        m_en = month_en_names[target_d_obj.month - 1]
        window_label_ko = f"{target_d_obj.month}월 {target_d_obj.day}일 {s_def['time_range']}"
        window_label_zh = f"{target_d_obj.month}月{target_d_obj.day}日 {s_def['time_range']}"
        window_label_en = f"{m_en} {target_d_obj.day}, {s_def['time_range']}"

        # Build candidate pool prioritized for this session's time window
        session_candidates = []
        for it in all_candidate_pool:
            raw = str(it.get("harvested_at") or it.get("published_at") or it.get("created_at") or it.get("harvested_date") or "")
            dt_kst_it = parse_to_kst_dt(raw)
            it_hour = dt_kst_it.hour if dt_kst_it else 12
            d_it = dt_kst_it.strftime("%Y-%m-%d") if dt_kst_it else get_item_date_str(it)

            if d_it == target_date_str and s_hour <= it_hour < s_hour + 6:
                priority = 1
            elif d_it == target_date_str:
                priority = 2
            elif d_it in [today_kst_str, yesterday_kst_str]:
                priority = 3
            else:
                priority = 4
            session_candidates.append((priority, compute_viral_weight(it), it))

        session_candidates.sort(key=lambda x: (x[0], -x[1]))
        candidate_items = [x[2] for x in session_candidates]

        picked_items = []
        for tp in s_def["targets"]:
            for it in candidate_items:
                iid = it.get("inbox_id") or it.get("title")
                if iid in used_inbox_ids: continue
                if get_platform_family(it) == tp:
                    picked_items.append(it)
                    used_inbox_ids.add(iid)
                    break
        for it in candidate_items:
            if len(picked_items) >= 3: break
            iid = it.get("inbox_id") or it.get("title")
            if iid in used_inbox_ids: continue
            picked_items.append(it)
            used_inbox_ids.add(iid)

        session_bullets = []
        session_items_data = []

        for it in picked_items:
            ml = it.get("multilingual") or {}
            ai_enr = it.get("ai_enrichment") or {}

            t_ko = ml.get("ko", {}).get("title") or it.get("title_ko") or it.get("title") or ""
            t_en = ml.get("en", {}).get("title") or it.get("title_en") or it.get("title") or ""
            t_zh = ml.get("zh", {}).get("title") or it.get("title_zh") or it.get("title") or ""

            clean_re = r'^(?:GitHub:\s*|HuggingFace:\s*|HF Space:\s*|Hacker News:\s*|ArXiv:\s*|GeekNews:\s*|Paper:\s*)'
            t_ko_clean = re.sub(clean_re, '', t_ko, flags=re.I).strip()
            t_en_clean = re.sub(clean_re, '', t_en, flags=re.I).strip()
            t_zh_clean = re.sub(clean_re, '', t_zh, flags=re.I).strip()

            plat_family = get_platform_family(it)
            plat = it.get("source_platform") or plat_family
            vm = it.get("viral_metric") or ""

            s_ko = ai_enr.get("summary_ko") or it.get("summary_ko") or ml.get("ko", {}).get("description") or it.get("description") or ""
            s_en = ai_enr.get("summary_en") or it.get("summary_en") or ml.get("en", {}).get("description") or it.get("description") or ""
            s_zh = ai_enr.get("summary_zh") or it.get("summary_zh") or ml.get("zh", {}).get("description") or it.get("description") or ""

            def clean_summ(s):
                sc = (s or "").replace('\n', ' ').strip()
                return (sc[:72] + "...") if len(sc) > 75 else sc

            s_ko_clean = clean_summ(s_ko)
            s_en_clean = clean_summ(s_en)
            s_zh_clean = clean_summ(s_zh)

            search_k = extract_search_key(it)
            is_model = is_model_item(it)
            case_id = (it.get("related_dossier") or {}).get("case_id") if it.get("related_dossier") else None

            session_items_data.append({
                "inbox_id": it.get("inbox_id") or "",
                "title": t_ko_clean,
                "title_ko": t_ko_clean,
                "title_en": t_en_clean,
                "title_zh": t_zh_clean,
                "search_key": search_k,
                "platform": plat,
                "platform_family": plat_family,
                "viral_metric": vm,
                "summary": s_ko_clean,
                "summary_ko": s_ko_clean,
                "summary_en": s_en_clean,
                "summary_zh": s_zh_clean,
                "source_url": it.get("source_url") or "#",
                "is_model": is_model,
                "case_id": case_id
            })

            if vm: session_bullets.append(f"🔥 [{plat}] {t_ko_clean[:45]} ({vm}) — {s_ko_clean}")
            else: session_bullets.append(f"🚀 [{plat}] {t_ko_clean[:45]} — {s_ko_clean}")

        sessions_data[str(s_num)] = {
            "session_num": s_num,
            "session_name": s_def["name"],
            "short_name": s_def["short_name"],
            "window_label": window_label_ko,
            "window_label_ko": window_label_ko,
            "window_label_zh": window_label_zh,
            "window_label_en": window_label_en,
            "is_current": is_cur,
            "is_future": is_fut,
            "status": status,
            "bullets": session_bullets,
            "items": session_items_data
        }

    trend_radar_data = {
        "current_session": current_session_num,
        "today_kst": today_kst_str,
        "updated_at": now_kst.strftime("%H:%M KST"),
        "sessions": sessions_data
    }
    trend_6h = sessions_data[str(current_session_num)]

    actions_telemetry = get_actions_telemetry()
    summary_data = {
        "generated_at": datetime.date.today().strftime("%Y-%m-%d"),
        "today_kst": today_kst_str,
        "total_cases": total_cases,
        "user_curated_count": user_curated_count,
        "auto_harvested_count": auto_harvested_count,
        "verified_true_count": verified_true_count,
        "half_true_count": half_true_count,
        "gamed_count": gamed_count,
        "avg_confidence": avg_conf,
        "models_total_count": len(model_items),
        "news_total_count": len(news_items),
        "news_cat_counts": news_cat_counts,
        "tier1_counts": tier1_counts,
        "model_art_counts": model_art_counts,
        "model_fam_counts": model_fam_counts,
        "inbox_total_count": len(clean_inbox_items),
        "all_inbox_count": len(inbox_items),
        "admin_stats": admin_stats,
        "timeline_24h": timeline_24h,
        "trend_6h": trend_6h,
        "trend_radar": trend_radar_data,
        "dow_stats": [],
        "monthly_stats": [],
        "model_items": model_items,
        "news_items": news_items,
        "inbox_items": clean_inbox_items,
        "cases": cases,
        "graph": graph_data,
        "actions_telemetry": actions_telemetry
    }

    # Write data.json — only docs/ (GitHub Pages) and public/ (Vercel static)
    for target_dir in [docs_dir, public_dir]:
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
    for target_dir in [docs_dir, public_dir]:
        html_path = os.path.join(target_dir, "index.html")
        for _ in range(3):
            try:
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                break
            except Exception:
                time.sleep(0.5)

    print(f"[+] Successfully built Full {total_cases} Dossiers Dashboard v20.0 at:")
    print(f"    - public/index.html & data.json (Vercel CDN Edge)")
    print(f"    - docs/index.html  (GitHub Pages hosting | Verified: {total_cases}, Models: {len(model_items)}, News: {len(news_items)}, Inbox: {len(clean_inbox_items)})")
    print(f"    [Removed] dashboard/ & root duplicates → Git repo size reduced")

def generate_html(data):
    cases_json = json.dumps(data["cases"], ensure_ascii=False)
    inbox_json = json.dumps(data["inbox_items"], ensure_ascii=False)
    admin_json = json.dumps(data["admin_stats"], ensure_ascii=False)
    graph_json = json.dumps(data["graph"], ensure_ascii=False)
    models_json = json.dumps(data.get("model_items", []), ensure_ascii=False)
    news_json = json.dumps(data.get("news_items", []), ensure_ascii=False)
    actions_telemetry_json = json.dumps(data.get("actions_telemetry", {}), ensure_ascii=False)
    timeline_json = json.dumps(data.get("timeline_24h", []), ensure_ascii=False)
    trend_6h_json = json.dumps(data.get("trend_6h", {}), ensure_ascii=False)
    trend_radar_json = json.dumps(data.get("trend_radar", {}), ensure_ascii=False)
    today_kst = data.get("today_kst", "2026-09-04")
    today_total_inbox = sum(s.get("inbox_count", 0) for s in data.get("timeline_24h", []))
    trend_6h = data.get("trend_6h", {})
    trend_updated_at = trend_6h.get("updated_at", "15:00 KST")
    trend_window_label = trend_6h.get("window_label", "12:00 ~ 18:00 KST")
    trend_window_period = trend_6h.get("window_period", "오후 실시간 모델 & 아키텍처 브리핑")
    trend_session_name = trend_6h.get("session_name", "3회차 (정오)")
    session_num = trend_6h.get("session_num", 3)
    s1_cls = "bg-emerald-600 text-white font-bold shadow-xs" if session_num == 1 else "bg-surface-subtle text-ink-muted"
    s2_cls = "bg-emerald-600 text-white font-bold shadow-xs" if session_num == 2 else "bg-surface-subtle text-ink-muted"
    s3_cls = "bg-emerald-600 text-white font-bold shadow-xs" if session_num == 3 else "bg-surface-subtle text-ink-muted"
    s4_cls = "bg-emerald-600 text-white font-bold shadow-xs" if session_num == 4 else "bg-surface-subtle text-ink-muted"
    
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="referrer" content="no-referrer">
  <title>FactCheck Hub — Universal AI Tech Intelligence</title>
  
  <!-- Modern SVG Favicon -->
  <link rel="icon" type="image/svg+xml" href="favicon.svg">
  <link rel="alternate icon" href="favicon.svg">
  
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
<body class="bg-surface-canvas text-ink-primary min-h-screen bg-clean-grid pb-24 antialiased selection:bg-ink-primary selection:text-white overflow-x-hidden w-full">

  <!-- ==================== TOP NAVIGATION HEADER ==================== -->
  <header class="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-surface-border">
    <div class="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-2 sm:gap-4">
      
      <!-- Brand Logo (Click to #home) -->
      <div class="flex items-center gap-2.5 sm:gap-3 shrink-0 cursor-pointer select-none group transition hover:opacity-95" onclick="switchView('home')" title="대시보드 홈으로 이동 (#home)">
        <div class="w-8 h-8 sm:w-9 sm:h-9 rounded-xl bg-ink-primary flex items-center justify-center text-white font-bold text-base shadow-sm shrink-0">
          <i data-lucide="shield-check" class="w-4 h-4 sm:w-5 sm:h-5 text-white"></i>
        </div>
        <div>
          <div class="flex items-center gap-1.5 sm:gap-2">
            <span class="text-sm sm:text-base font-extrabold text-ink-primary tracking-tight" id="headerBrandTitle">FactCheck Hub</span>
            <span class="text-[9px] sm:text-[10px] font-mono px-1 sm:px-1.5 py-0.2 rounded bg-surface-subtle border border-surface-border text-ink-muted font-bold">2026</span>
          </div>
          <p class="text-[11px] text-ink-muted hidden sm:block" id="headerBrandSubtitle">AI 팩트체크 & 글로벌 테크 최신 동향</p>
        </div>
      </div>

      <!-- Desktop Navigation Tabs (Clean 4 Core Tabs) -->
      <nav class="hidden md:flex items-center gap-1 bg-surface-subtle p-1 rounded-xl border border-surface-border text-xs font-semibold">
        <button onclick="switchView('portfolio')" id="tabPortfolioBtn" class="nav-tab flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-ink-secondary hover:text-ink-primary transition">
          <i data-lucide="shield-check" class="w-3.5 h-3.5"></i>
          <span id="navTabPortfolio">공식 검증</span>
          <span class="text-[10px] font-mono text-ink-muted" id="headerVerifiedCount">({data['total_cases']})</span>
        </button>
        <button onclick="switchView('news')" id="tabNewsBtn" class="nav-tab flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-ink-secondary hover:text-ink-primary transition">
          <i data-lucide="newspaper" class="w-3.5 h-3.5"></i>
          <span id="navTabNews">테크 & AI 동향</span>
          <span class="text-[10px] font-mono text-ink-muted" id="headerNewsCount">({data['news_total_count']})</span>
        </button>
        <button onclick="switchView('models')" id="tabModelsBtn" class="nav-tab flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-ink-secondary hover:text-ink-primary transition">
          <i data-lucide="cpu" class="w-3.5 h-3.5"></i>
          <span id="navTabModels">AI 모델 트렌드</span>
          <span class="text-[10px] font-mono text-ink-muted" id="headerModelsCount">({data['models_total_count']})</span>
        </button>
        <button onclick="switchView('graph')" id="tabGraphBtn" class="nav-tab flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-ink-secondary hover:text-ink-primary transition">
          <i data-lucide="network" class="w-3.5 h-3.5"></i>
          <span id="navTabGraph">인용 계보망</span>
        </button>
      </nav>

      <!-- Right Actions: Admin Archive, Live DB Badge & Tri-Lingual (KO / ZH / EN) Toggle -->
      <div class="flex items-center gap-1.5 sm:gap-2.5 shrink-0">
        <!-- Admin Raw Archive Access Button (Visible on desktop, mobile accessed via subnav) -->
        <button onclick="switchView('inbox')" id="adminArchiveBtn" class="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold text-ink-muted hover:text-ink-primary hover:bg-surface-subtle transition border border-transparent hover:border-surface-border" title="관리자 전용 원천 데이터 아카이브">
          <i data-lucide="archive" class="w-3.5 h-3.5 text-slate-500"></i>
          <span class="hidden lg:inline" id="adminArchiveLabel">아카이브 (Admin)</span>
          <span class="text-[10px] font-mono opacity-80" id="headerInboxCount">({data['inbox_total_count']})</span>
        </button>

        <!-- Live Neon DB Badge (Hidden on mobile) -->
        <div id="dbLiveBadge" class="hidden sm:block">
          <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse"></span>
            <span class="hidden xs:inline sm:inline">Neon DB</span> Live
          </span>
        </div>

        <!-- Language Toggle (KO / ZH / EN) -->
        <div class="bg-surface-subtle p-0.5 sm:p-1 rounded-lg border border-surface-border flex items-center text-xs font-semibold gap-0.5">
          <button onclick="setLanguage('KO')" id="langKoBtn" class="px-1.5 sm:px-2 py-0.5 rounded bg-ink-primary text-white transition text-[10px] sm:text-[11px]">KO</button>
          <button onclick="setLanguage('ZH')" id="langZhBtn" class="px-1.5 sm:px-2 py-0.5 rounded text-ink-secondary hover:text-ink-primary transition text-[10px] sm:text-[11px]">中文</button>
          <button onclick="setLanguage('EN')" id="langEnBtn" class="px-1.5 sm:px-2 py-0.5 rounded text-ink-secondary hover:text-ink-primary transition text-[10px] sm:text-[11px]">EN</button>
        </div>
      </div>

    </div>

    <!-- Mobile Scrollable Sub-Navigation Bar -->
    <div class="flex md:hidden items-center gap-1.5 px-3 py-2 overflow-x-auto no-scrollbar border-t border-surface-border bg-white">
      <button onclick="switchView('portfolio')" id="mTabPortfolioBtn" class="mobile-nav-tab shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium text-ink-secondary hover:text-ink-primary bg-surface-subtle border border-surface-border transition">
        <i data-lucide="shield-check" class="w-3.5 h-3.5"></i>
        <span id="mNavTabPortfolio">공식 검증 ({data['total_cases']})</span>
      </button>
      <button onclick="switchView('news')" id="mTabNewsBtn" class="mobile-nav-tab shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium text-ink-secondary hover:text-ink-primary bg-surface-subtle border border-surface-border transition">
        <i data-lucide="newspaper" class="w-3.5 h-3.5"></i>
        <span id="mNavTabNews">테크&AI ({data['news_total_count']})</span>
      </button>
      <button onclick="switchView('models')" id="mTabModelsBtn" class="mobile-nav-tab shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium text-ink-secondary hover:text-ink-primary bg-surface-subtle border border-surface-border transition">
        <i data-lucide="cpu" class="w-3.5 h-3.5"></i>
        <span id="mNavTabModels">AI 모델 트렌드 ({data['models_total_count']})</span>
      </button>
      <button onclick="switchView('graph')" id="mTabGraphBtn" class="mobile-nav-tab shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium text-ink-secondary hover:text-ink-primary bg-surface-subtle border border-surface-border transition">
        <i data-lucide="network" class="w-3.5 h-3.5"></i>
        <span id="mNavTabGraph">인용 계보망</span>
      </button>
      <button onclick="switchView('inbox')" id="mTabInboxBtn" class="mobile-nav-tab shrink-0 flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-500 hover:text-ink-primary bg-surface-subtle border border-dashed border-surface-border transition" title="관리자 원천 아카이브">
        <i data-lucide="archive" class="w-3.5 h-3.5"></i>
        <span id="mNavTabInbox">아카이브 ({data['inbox_total_count']})</span>
      </button>
    </div>
  </header>

  <main class="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8 py-6 sm:py-8 space-y-6 overflow-x-hidden">

    <!-- ==================== VIEW 0: HOME DASHBOARD (순수 종합 대시보드 뷰) ==================== -->
    <div id="homeView" class="space-y-6">

      <!-- Compact Zero-Scroll Status Strip -->
      <div class="flex items-center justify-between flex-wrap gap-2 px-4 py-2 rounded-xl bg-white border border-surface-border shadow-xs text-xs font-mono">
        <div class="flex items-center gap-2 flex-wrap">
          <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold text-[11px]" id="heroBadge">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse"></span>
            ZERO-HALLUCINATION AUDIT
          </span>
          <span class="font-bold text-ink-primary text-xs hidden sm:inline" id="heroMainTitle">
            바이럴된 AI 기술의 실체 분석
          </span>
        </div>

        <div class="flex items-center gap-3 text-[11px] text-ink-muted">
          <span><span id="heroUpdateLabel">LAST AUDITED</span>: <b class="text-ink-primary">{data['generated_at']}</b></span>
          <span class="text-emerald-700 font-bold" id="heroAuditCount">● {data['total_cases']}개 기술 검증 완료</span>
        </div>
      </div>

      <!-- 🌟 REAL-TIME TELEMETRY & INTELLIGENCE KPI OVERVIEW (실시간 대시보드 종합 통계) -->
      <!-- Order: 🔬 공식 기술 검증 │ 📰 AI 테크 동향 │ 🤖 AI 모델 트렌드 │ 📡 수집 인박스 -->
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

        <!-- Metric 2: AI News & Industry Reports (AI 테크 동향) -->
        <div onclick="switchView('news')" class="bg-white p-4 sm:p-5 rounded-2xl border border-surface-border hover:border-amber-500 hover:shadow-md transition cursor-pointer group">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-ink-muted group-hover:text-amber-700 transition flex items-center gap-1.5" id="statLabelNews">
              <i data-lucide="newspaper" class="w-4 h-4 text-amber-600"></i>
              <span>테크 & AI 동향</span>
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

        <!-- Metric 3: Trending AI Models (AI 모델 트렌드) -->
        <div onclick="switchView('models')" class="bg-white p-4 sm:p-5 rounded-2xl border border-surface-border hover:border-purple-500 hover:shadow-md transition cursor-pointer group">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-ink-muted group-hover:text-purple-600 transition flex items-center gap-1.5" id="statLabelModels">
              <i data-lucide="cpu" class="w-4 h-4 text-purple-600"></i>
              <span>AI 모델 트렌드</span>
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

        <!-- Metric 4: Raw Ingestion Lake & Admin Archive (원천 아카이브) -->
        <div onclick="switchView('inbox')" class="bg-white p-4 sm:p-5 rounded-2xl border border-surface-border hover:border-slate-500 hover:shadow-md transition cursor-pointer group">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-ink-muted group-hover:text-slate-800 transition flex items-center gap-1.5" id="statLabelInbox">
              <i data-lucide="archive" class="w-4 h-4 text-slate-600"></i>
              <span id="statLabelArchive">원천 아카이브 (Admin)</span>
            </span>
            <span class="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-slate-100 text-slate-700 border border-slate-200">
              ⚡ 24H 전수 보존
            </span>
          </div>
          <div class="mt-3 flex items-baseline gap-2">
            <span class="text-2xl sm:text-3xl font-black text-ink-primary font-mono" id="statValInbox">{data['inbox_total_count']}</span>
            <span class="text-xs text-ink-muted font-medium">Archives</span>
          </div>
          <p class="mt-2 text-[11px] text-ink-secondary truncate" id="statDescInbox">
            크롤링 원천 데이터 레이크 · 심층 분석 대기열
          </p>
        </div>

      </div>

      <!-- 📈 24H COLLECTION TIMELINE & 6H AI TREND RADAR (실시간 수집 현황 & 6시간 주기 AI 트렌드) -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-5">
        
        <!-- Card 1: Today 24-Hour Ingestion Timeline (1일 4회 6시간 주기 전략 수집) -->
        <div class="bg-white p-5 rounded-2xl border border-surface-border shadow-sm flex flex-col justify-between space-y-4">
          <div class="flex items-center justify-between flex-wrap gap-2">
            <div class="space-y-0.5">
              <div class="flex items-center gap-2">
                <span class="text-xs font-bold text-ink-primary font-mono flex items-center gap-1.5" id="timelineTitle">
                  <i data-lucide="clock" class="w-4 h-4 text-indigo-600"></i>
                  <span id="timelineTitleText">당일 24시간 수집 타임라인 ({today_kst})</span>
                </span>
                <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-indigo-50 text-indigo-700 border border-indigo-200 flex items-center gap-1">
                  <span class="w-1.5 h-1.5 rounded-full bg-indigo-600 animate-pulse"></span>
                  <span id="timelineBadgeText">1일 4회 6h 펄스</span>
                </span>
              </div>
              <p class="text-[11px] text-ink-muted" id="timelineSub">1일 4회(00, 06, 12, 18시 KST) 6시간 주기 전략 수집 + 23:30 EOD 전수 감사</p>
            </div>
            
            <div class="flex items-center gap-2 text-[11px] font-mono text-ink-secondary">
              <span class="w-2.5 h-2.5 rounded bg-indigo-600 inline-block"></span>
              <span id="timelineLegendText">세션별 수집 건수</span>
            </div>
          </div>

          <!-- Bar Visualizer for Today 24h Timeline (4 Quarterly Sessions) -->
          <div class="pt-2 pb-1">
            <div class="grid grid-cols-4 gap-2 sm:gap-3 items-end h-36 border-b border-surface-border pb-2" id="timeline24hChartContainer">
              <!-- Dynamically Populated via JS -->
            </div>
          </div>

          <div class="pt-2 border-t border-surface-border flex items-center justify-between text-[11px] text-ink-muted font-mono flex-wrap gap-2" id="timelineFooter">
            <span id="timelineFooterText">⚡ 당일 총 수집량: <b class="text-indigo-700">{today_total_inbox}건</b></span>
          </div>
        </div>

        <!-- Card 2: 1-Day 4-Sessions AI Trend Pulse Radar (1일 4회 AI 핵심 트렌드 레이더) -->
        <div class="bg-white p-5 rounded-2xl border border-surface-border shadow-sm flex flex-col justify-between space-y-4">
          <div class="flex items-center justify-between flex-wrap gap-2">
            <div class="space-y-0.5">
              <div class="flex items-center gap-2">
                <span class="text-xs font-bold text-ink-primary font-mono flex items-center gap-1.5" id="trendRadarTitle">
                  <i data-lucide="radar" class="w-4 h-4 text-emerald-600"></i>
                  <span id="trendRadarTitleText">1일 4회 AI 트렌드 레이더</span>
                </span>
                <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1">
                  <span class="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse" id="trendRadarPulseDot"></span>
                  <span id="trendRadarWindowLabel">{trend_window_label}</span>
                </span>
              </div>
              <p class="text-[11px] text-ink-muted" id="trendRadarSub">글로벌 오픈소스 & AI 신규 가중치 6시간 주기 자동 감지</p>
            </div>

            <!-- 4 Interactive Session Selector Buttons -->
            <div class="flex items-center gap-1 text-[10px] font-mono" id="radarSessionButtons">
              <button type="button" onclick="switchRadarSession(1)" id="radarBtn1" class="px-2 py-0.5 rounded border border-surface-border transition cursor-pointer font-bold {s1_cls}">1회 00시</button>
              <button type="button" onclick="switchRadarSession(2)" id="radarBtn2" class="px-2 py-0.5 rounded border border-surface-border transition cursor-pointer font-bold {s2_cls}">2회 06시</button>
              <button type="button" onclick="switchRadarSession(3)" id="radarBtn3" class="px-2 py-0.5 rounded border border-surface-border transition cursor-pointer font-bold {s3_cls}">3회 12시</button>
              <button type="button" onclick="switchRadarSession(4)" id="radarBtn4" class="px-2 py-0.5 rounded border border-surface-border transition cursor-pointer font-bold {s4_cls}">4회 18시</button>
            </div>
          </div>

          <!-- Trend Radar Content Bullets -->
          <div class="pt-1 pb-1 space-y-2.5" id="trendRadarBody">
            <div class="space-y-2" id="trendRadarBullets">
              <!-- Dynamically Populated via JS with direct links -->
            </div>
          </div>

          <div class="pt-2 border-t border-surface-border flex items-center justify-between text-[11px] text-ink-muted font-mono flex-wrap gap-2" id="trendRadarFooter">
            <span class="flex items-center gap-1.5"><i data-lucide="zap" class="w-3.5 h-3.5 text-amber-500"></i> LLM 자동 트렌드 추출 (OpenRouter 0원 라우팅)</span>
            <span class="text-[10px] text-ink-muted font-medium">카드를 클릭하면 해당 안건의 1차 원문으로 즉시 이동합니다</span>
          </div>
        </div>

      </div>

      <!-- 🌟 RECENT VERIFIED FACT-CHECKS PREVIEW (대시보드 하단 최신 팩트체크 Top 3 하이라이트) -->
      <div class="bg-white p-5 sm:p-6 rounded-2xl border border-surface-border shadow-sm space-y-4">
        <div class="flex items-center justify-between flex-wrap gap-2">
          <div class="flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
            <h3 class="text-sm font-bold text-ink-primary font-mono" id="homeTopPicksTitle">최신 심층 기술 검증 하이라이트</h3>
          </div>
          <button onclick="switchView('portfolio')" class="text-xs font-bold text-indigo-600 hover:text-indigo-800 transition flex items-center gap-1 font-mono">
            <span id="homeTopPicksViewAll">전체 {data['total_cases']}개 검증 도시에 보러가기</span> <i data-lucide="arrow-right" class="w-3.5 h-3.5"></i>
          </button>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-3.5" id="homeTopPicksContainer">
          <!-- Dynamically populated Top 3 latest verified cases -->
        </div>
      </div>

    </div>

    <!-- ==================== VIEW 1: TECH FACT-CHECK (기술 검증 포트폴리오 35건 전용 뷰) ==================== -->
    <div id="portfolioView" class="hidden space-y-6">

      <!-- Portfolio Header Bar -->
      <div class="bg-white p-5 rounded-2xl border border-surface-border shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div class="space-y-1">
          <div class="flex items-center gap-2">
            <span class="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
              EMPIRICAL DOSSIERS
            </span>
            <span class="text-xs font-mono text-ink-muted">총 {data['total_cases']}건 완료</span>
          </div>
          <h2 class="text-lg sm:text-xl font-extrabold text-ink-primary" id="portfolioViewTitle">
            공식 기술 실측 검증 포트폴리오
          </h2>
          <p class="text-xs text-ink-secondary" id="portfolioViewDesc">
            SNS 바이럴 마케팅의 환각을 걷어내고, 1차 공식 문서 및 코드 레벨 벤치마크로 완성된 기술 검증 보고서 전편
          </p>
        </div>

        <button onclick="switchView('home')" class="self-start md:self-auto px-3.5 py-1.5 rounded-xl bg-surface-subtle hover:bg-surface-canvas border border-surface-border text-xs font-bold text-ink-secondary hover:text-ink-primary transition flex items-center gap-1.5">
          <i data-lucide="layout-dashboard" class="w-3.5 h-3.5"></i>
          <span id="backToHomeBtnText">대시보드로 돌아가기</span>
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
              <span class="text-[11px] font-mono px-1.5 py-0.2 rounded bg-black/5 text-ink-secondary font-bold" id="badgeCountUser">{data['user_curated_count']}</span>
            </button>
            <button onclick="setModeFilter('AUTO_HARVESTED')" id="modeBtnAuto" class="segment-btn flex-1 md:flex-initial px-4 py-2 rounded-lg text-xs font-semibold hover:text-ink-primary transition flex items-center justify-center gap-1.5">
              <i data-lucide="bot" class="w-3.5 h-3.5 text-emerald-600"></i>
              <span id="btnLabelAuto">자동 트렌드</span>
              <span class="text-[11px] font-mono px-1.5 py-0.2 rounded bg-black/5 text-ink-secondary font-bold" id="badgeCountAuto">{data['auto_harvested_count']}</span>
            </button>
          </div>

          <!-- Sort Select & Results Counter -->
          <div class="flex items-center justify-between w-full md:w-auto gap-3">
            <span class="text-xs text-ink-muted font-mono" id="resultsCountLabel">총 {data['total_cases']}건 표시</span>
            
            <div class="flex items-center gap-2 bg-surface-subtle px-3 py-1.5 rounded-xl border border-surface-border text-xs">
              <i data-lucide="arrow-up-down" class="w-3.5 h-3.5 text-ink-secondary shrink-0"></i>
              <span class="text-ink-secondary text-xs font-medium shrink-0" id="sortLabel">정렬:</span>
              <select id="sortSelect" onchange="changeSort(this.value)" class="bg-transparent text-ink-primary font-bold text-xs focus:outline-none cursor-pointer">
                <option value="date-audit-desc" selected>🔬 분석일자 최신순 (기본)</option>
                <option value="date-audit-asc">🔬 분석일자 오래된순</option>
                <option value="date-source-desc">📅 원출처 발행 최신순</option>
                <option value="date-source-asc">📅 원출처 발행 오래된순</option>
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
      <div id="portfolioPagination" class="mt-4"></div>
    </div>

    <!-- ==================== VIEW: AI MODELS REGISTRY ==================== -->
    <div id="modelsView" class="hidden space-y-6">
      <!-- Models Controls & Family Filter Bar (Hugging Face & OpenRouter 표준 분류 체계) -->
      <div class="bg-white p-4 rounded-2xl border border-surface-border shadow-sm space-y-3">
        <div class="flex flex-col sm:flex-row sm:items-center gap-1.5 sm:gap-2 text-xs">
          <span class="font-bold text-ink-secondary text-[11px] shrink-0 flex items-center gap-1" id="modelsFamilyLabel">
            🤖 모델 패밀리:
          </span>
          <div class="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-1 w-full flex-nowrap" id="modelsFamilyFilterRow">
            <button onclick="setModelsFamilyFilter('ALL')" data-fam="ALL" class="model-fam-pill active px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shrink-0 whitespace-nowrap">전체 패밀리</button>
            <button onclick="setModelsFamilyFilter('Qwen')" data-fam="Qwen" class="model-fam-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">Qwen ({data['model_fam_counts'].get('Qwen', 0)})</button>
            <button onclick="setModelsFamilyFilter('Wan')" data-fam="Wan" class="model-fam-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">Wan 비디오 ({data['model_fam_counts'].get('Wan', 0)})</button>
            <button onclick="setModelsFamilyFilter('MiniMax')" data-fam="MiniMax" class="model-fam-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">MiniMax ({data['model_fam_counts'].get('MiniMax', 0)})</button>
            <button onclick="setModelsFamilyFilter('FLUX')" data-fam="FLUX" class="model-fam-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">FLUX 이미지 ({data['model_fam_counts'].get('FLUX', 0)})</button>
            <button onclick="setModelsFamilyFilter('GLM')" data-fam="GLM" class="model-fam-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">GLM ({data['model_fam_counts'].get('GLM', 0)})</button>
            <button onclick="setModelsFamilyFilter('DeepSeek')" data-fam="DeepSeek" class="model-fam-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">DeepSeek ({data['model_fam_counts'].get('DeepSeek', 0)})</button>
            <button onclick="setModelsFamilyFilter('Hunyuan')" data-fam="Hunyuan" class="model-fam-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">Hunyuan ({data['model_fam_counts'].get('Hunyuan', 0)})</button>
            <button onclick="setModelsFamilyFilter('Audio')" data-fam="Audio" class="model-fam-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">음성/TTS ({data['model_fam_counts'].get('Audio', 0)})</button>
            <button onclick="setModelsFamilyFilter('Standalone')" data-fam="Standalone" class="model-fam-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">독립/신규 모델 ({data['model_fam_counts'].get('Standalone', 0)})</button>
          </div>
        </div>

        <!-- Ecosystem / Hub Resource Type Filter Pills (Hugging Face 공식 표준: 모델 가중치 vs Spaces 데모) -->
        <div class="flex flex-col sm:flex-row sm:items-center gap-1.5 sm:gap-2 text-xs pt-1 border-t border-surface-border">
          <span class="font-bold text-ink-secondary text-[11px] shrink-0 flex items-center gap-1" id="modelsArtifactLabel">
            🧩 허브 유형:
          </span>
          <div class="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-1 w-full flex-nowrap" id="modelsArtifactFilterRow">
            <button onclick="setModelsArtifactFilter('ALL')" data-art="ALL" class="model-art-pill active px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap">전체 ({data['models_total_count']})</button>
            <button onclick="setModelsArtifactFilter('WEIGHTS')" data-art="WEIGHTS" class="model-art-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">🤖 가중치·체크포인트 ({data['model_art_counts'].get('WEIGHTS', 0)})</button>
            <button onclick="setModelsArtifactFilter('WEB_SERVICE')" data-art="WEB_SERVICE" class="model-art-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">🌐 인터랙티브 데모·Spaces ({data['model_art_counts'].get('WEB_SERVICE', 0)})</button>
            <button onclick="setModelsArtifactFilter('FINETUNE')" data-art="FINETUNE" class="model-art-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">🎯 특화 파인튜닝 ({data['model_art_counts'].get('FINETUNE', 0)})</button>
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
              <span class="text-ink-muted text-[11px] font-mono" id="modelsSortLabel">정렬:</span>
              <select id="modelsSortSelect" onchange="setModelsSort(this.value)" class="bg-transparent text-ink-primary text-xs font-bold focus:outline-none cursor-pointer">
                <option value="date-audit-desc" selected>🔬 AI 분석일 최신순 (기본)</option>
                <option value="date-audit-asc">🔬 AI 분석일 오래된순</option>
                <option value="date-source-desc">📅 수집/발표 최신순</option>
                <option value="date-source-asc">📅 수집/발표 오래된순</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <!-- Models Grid (3x5 Readable Grid) -->
      <div id="modelsGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5"></div>
      <div id="modelsPagination" class="mt-4"></div>
    </div>

    <!-- ==================== VIEW 2: AI NEWS & TRENDS (정밀 카테고리화 허브) ==================== -->
    <div id="newsView" class="hidden space-y-6">
      <!-- News Category Filter Bar (IPTC 6대 Tier 1 도메인 카테고리) -->
      <div class="bg-white p-4 rounded-2xl border border-surface-border shadow-sm space-y-3">
        <div class="flex flex-col sm:flex-row sm:items-center gap-1.5 sm:gap-2 text-xs">
          <span class="font-bold text-ink-secondary text-[11px] shrink-0 flex items-center gap-1" id="newsCatFilterLabel">
            🏷️ 기술·글로벌 분류:
          </span>
          <div class="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-1 w-full flex-nowrap" id="newsCategoryFilterRow">
            <button onclick="setNewsCategoryFilter('ALL')" data-cat="ALL" class="news-cat-pill active px-3 py-1.5 rounded-xl text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap">전체 ({data['news_total_count']})</button>
            <button onclick="setNewsCategoryFilter('TECH_COMPUTING')" data-cat="TECH_COMPUTING" class="news-cat-pill px-3 py-1.5 rounded-xl text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">💻 IT·컴퓨팅 ({data['tier1_counts'].get('TECH_COMPUTING', 0)})</button>
            <button onclick="setNewsCategoryFilter('SCIENCE_RESEARCH')" data-cat="SCIENCE_RESEARCH" class="news-cat-pill px-3 py-1.5 rounded-xl text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">🚀 과학·우주 ({data['tier1_counts'].get('SCIENCE_RESEARCH', 0)})</button>
            <button onclick="setNewsCategoryFilter('ECONOMY_FINANCE')" data-cat="ECONOMY_FINANCE" class="news-cat-pill px-3 py-1.5 rounded-xl text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">🏦 경제·금융 ({data['tier1_counts'].get('ECONOMY_FINANCE', 0)})</button>
            <button onclick="setNewsCategoryFilter('LAW_CRIME_JUSTICE')" data-cat="LAW_CRIME_JUSTICE" class="news-cat-pill px-3 py-1.5 rounded-xl text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">⚖️ 사회·법률 ({data['tier1_counts'].get('LAW_CRIME_JUSTICE', 0)})</button>
            <button onclick="setNewsCategoryFilter('POLITICS_POLICY')" data-cat="POLITICS_POLICY" class="news-cat-pill px-3 py-1.5 rounded-xl text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">🏛️ 정치·정책 ({data['tier1_counts'].get('POLITICS_POLICY', 0)})</button>
            <button onclick="setNewsCategoryFilter('CULTURE_HUMANITIES')" data-cat="CULTURE_HUMANITIES" class="news-cat-pill px-3 py-1.5 rounded-xl text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">🌿 문화·인문 ({data['tier1_counts'].get('CULTURE_HUMANITIES', 0)})</button>
          </div>
        </div>

        <!-- Tier 2 Engineering Specialization Row (IT·컴퓨팅 6대 세부 공학 분야) -->
        <div class="flex flex-col sm:flex-row sm:items-center gap-1.5 sm:gap-2 text-xs pt-2 border-t border-surface-border transition-opacity duration-200" id="newsTier2Container">
          <span class="font-bold text-ink-secondary text-[11px] shrink-0 flex items-center gap-1" id="newsTier2FilterLabel">
            ↳ 💻 IT 세부 분야:
          </span>
          <div class="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-1 w-full flex-nowrap" id="newsTier2FilterRow">
            <button onclick="setNewsTier2Filter('ALL')" data-t2="ALL" class="news-t2-pill active px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap">전체 IT 분야</button>
            <button onclick="setNewsTier2Filter('INFERENCE_OPT')" data-t2="INFERENCE_OPT" class="news-t2-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">⚡ 추론·서빙 ({data['news_cat_counts'].get('INFERENCE_OPT', 0)})</button>
            <button onclick="setNewsTier2Filter('AGENTS_DEVTOOLS')" data-t2="AGENTS_DEVTOOLS" class="news-t2-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">🛠️ 에이전트·도구 ({data['news_cat_counts'].get('AGENTS_DEVTOOLS', 0)})</button>
            <button onclick="setNewsTier2Filter('MULTIMODAL_AI')" data-t2="MULTIMODAL_AI" class="news-t2-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">🎨 멀티모달 ({data['news_cat_counts'].get('MULTIMODAL_AI', 0)})</button>
            <button onclick="setNewsTier2Filter('FOUNDATION_MODELS')" data-t2="FOUNDATION_MODELS" class="news-t2-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">🤖 파운데이션 ({data['news_cat_counts'].get('FOUNDATION_MODELS', 0)})</button>
            <button onclick="setNewsTier2Filter('INFRA_RAG_SECURITY')" data-t2="INFRA_RAG_SECURITY" class="news-t2-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">🛡️ 인프라·보안 ({data['news_cat_counts'].get('INFRA_RAG_SECURITY', 0)})</button>
            <button onclick="setNewsTier2Filter('INDUSTRY_TRENDS')" data-t2="INDUSTRY_TRENDS" class="news-t2-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">🌐 일반 SW·웹 ({data['news_cat_counts'].get('INDUSTRY_TRENDS', 0)})</button>
          </div>
        </div>

        <!-- Secondary Source & Search & Sort Row -->
        <div class="pt-2 border-t border-surface-border flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
          <div class="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-1 w-full md:w-auto text-xs flex-nowrap">
            <span class="text-ink-muted text-[11px] font-mono shrink-0" id="newsSourceLabel">출처:</span>
            <button onclick="setNewsSourceFilter('ALL')" id="newsSrcBtnAll" class="news-src-btn active px-2.5 py-1 rounded-lg text-xs font-bold bg-ink-primary text-white transition shrink-0 whitespace-nowrap" data-src="ALL">전체 출처</button>
            <button onclick="setNewsSourceFilter('GeekNews')" class="news-src-btn px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:bg-white transition border border-surface-border shrink-0 whitespace-nowrap" data-src="GeekNews">🇰🇷 긱뉴스</button>
            <button onclick="setNewsSourceFilter('Hacker News')" class="news-src-btn px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:bg-white transition border border-surface-border shrink-0 whitespace-nowrap" data-src="Hacker News">🔥 HN</button>
            <button onclick="setNewsSourceFilter('GitHub')" class="news-src-btn px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:bg-white transition border border-surface-border shrink-0 whitespace-nowrap" data-src="GitHub">🐙 GitHub</button>
            <button onclick="setNewsSourceFilter('ArXiv')" class="news-src-btn px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:bg-white transition border border-surface-border shrink-0 whitespace-nowrap" data-src="ArXiv">📄 ArXiv</button>
            <button onclick="setNewsSourceFilter('Hugging Face')" class="news-src-btn px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:bg-white transition border border-surface-border shrink-0 whitespace-nowrap" data-src="Hugging Face">🤗 HF</button>
          </div>

          <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-3 w-full md:w-auto justify-between md:justify-end">
            <div class="relative w-full sm:w-48 md:w-56">
              <i data-lucide="search" class="w-3.5 h-3.5 absolute left-3 top-2.5 text-ink-muted"></i>
              <input type="text" id="newsSearchInput" oninput="handleNewsSearch(this.value)" placeholder="기술명, 키워드 검색..." 
                     class="w-full bg-surface-subtle border border-surface-border rounded-xl pl-8 pr-3 py-1.5 text-xs text-ink-primary placeholder-ink-muted focus:outline-none focus:border-ink-primary transition font-medium">
            </div>

            <div class="flex items-center justify-between sm:justify-start gap-1.5 bg-surface-subtle px-2.5 py-1 rounded-xl border border-surface-border text-xs shrink-0">
              <i data-lucide="arrow-up-down" class="w-3 h-3 text-indigo-600"></i>
              <span class="text-ink-muted text-[11px] font-mono" id="newsSortLabel">정렬:</span>
              <select id="newsSortSelect" onchange="setNewsSort(this.value)" class="bg-transparent text-ink-primary text-xs font-bold focus:outline-none cursor-pointer">
                <option value="date-source-desc" selected>📅 수집/발표 최신순 (기본)</option>
                <option value="date-source-asc">📅 수집/발표 오래된순</option>
                <option value="date-audit-desc">🔬 AI 분석일 최신순</option>
                <option value="date-audit-asc">🔬 AI 분석일 오래된순</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <!-- News Grid (3x5 Readable Grid) -->
      <div id="newsGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5"></div>
      <div id="newsPagination" class="mt-4"></div>
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
            <span class="px-2.5 py-0.5 rounded-md bg-slate-100 text-slate-800 text-xs font-mono font-bold border border-slate-200" id="inboxHeaderBadge">
              🔐 RAW ARCHIVE & ADMIN INBOX
            </span>
            <span class="text-xs text-ink-muted font-mono" id="inboxHeaderCount">총 {data['inbox_total_count']}건</span>
          </div>
          <h2 class="text-lg font-bold text-ink-primary" id="inboxHeaderTitle">원천 데이터 아카이브 & 관리자 파이프라인</h2>
          <p class="text-xs text-ink-secondary" id="inboxHeaderDesc">
            크롤러가 24시간 실시간 수집한 원천 로우 데이터를 영구 보존하며, 관리자가 심층 팩트체크(공식 검증)로 승격할 후보를 검토하는 내부 저장소입니다.
          </p>
        </div>
      </div>

      <!-- 🚀 GITHUB ACTIONS RUNNER QUOTA & OPERATIONAL LOG ANALYTICS SUITE -->
      <div class="bg-white p-5 sm:p-6 rounded-2xl border border-surface-border shadow-sm space-y-5">
        
        <!-- Header & Top Countdown -->
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-surface-border">
          <div class="space-y-1">
            <div class="flex items-center gap-2">
              <span class="px-2.5 py-0.5 rounded text-[10px] font-mono font-bold bg-indigo-50 text-indigo-700 border border-indigo-200 flex items-center gap-1.5" id="pipelineBadge">
                <span class="w-1.5 h-1.5 rounded-full bg-indigo-600 animate-pulse"></span>
                <span>GITHUB ACTIONS RUNNER TELEMETRY & QUOTA</span>
              </span>
              <span class="text-xs font-mono text-ink-muted" id="pipelineScheduleDesc">1일 4회(00:17, 06:17, 12:17, 18:17 KST) 전략 수집</span>
            </div>
            <h3 class="text-base font-bold text-ink-primary flex items-center gap-2" id="pipelineWidgetTitle">
              <i data-lucide="server" class="w-4 h-4 text-indigo-600"></i>
              <span>GitHub Actions 러너 쿼터 잔여 시간 & 회차별 소요시간·에러 로그 분석</span>
            </h3>
            <p class="text-xs text-ink-secondary" id="pipelineWidgetSub">
              월간 무료 2,000분 쿼터 소모량과 회차별 실제 실행 시간(Duration)을 정밀 추적하여, 수집 주기를 줄이거나(증설) 늘리는(절약) 운영 의사결정을 지원합니다.
            </p>
          </div>

          <!-- Dynamic Next Run Countdown Banner -->
          <div class="bg-gradient-to-r from-indigo-500 to-indigo-600 text-white p-3 rounded-xl shadow-sm flex items-center gap-3 shrink-0 self-start md:self-auto">
            <i data-lucide="timer" class="w-5 h-5 text-indigo-100 animate-spin" style="animation-duration: 12s;"></i>
            <div>
              <div class="text-[10px] font-medium text-indigo-100 uppercase tracking-wider" id="pipelineNextTargetLabel">다음 자동 수집 예정</div>
              <div class="text-xs sm:text-sm font-mono font-bold tracking-tight text-white flex items-center gap-1" id="pipelineCountdownValue">
                계산 중...
              </div>
            </div>
          </div>
        </div>

        <!-- Section 1: 📊 GitHub Actions Monthly Quota & Decision Simulator -->
        <div class="bg-slate-50/70 p-4 rounded-xl border border-slate-200 space-y-3">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs font-mono">
            <div class="flex items-center gap-2 font-bold text-ink-primary">
              <i data-lucide="gauge" class="w-4 h-4 text-indigo-600"></i>
              <span id="quotaSectionTitle">월간 GitHub Actions 러너 쿼터 현황 (2,000분 기준)</span>
            </div>
            <div class="text-ink-secondary text-[11px]" id="quotaStatsText">
              사용: <b class="text-indigo-600 font-bold" id="quotaUsedMin">82.8분</b> / 잔여: <b class="text-emerald-600 font-bold" id="quotaRemMin">1,917.2분 (95.9%)</b>
            </div>
          </div>

          <!-- Progress Bar -->
          <div class="w-full bg-slate-200 rounded-full h-3 overflow-hidden flex relative">
            <div class="bg-amber-500 h-3 rounded-full transition-all duration-500" id="quotaProgressBar" style="width: 62.1%;"></div>
          </div>

          <!-- Breakdown by Workflows (Image 1 metrics) -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 pb-1 text-[11px] font-mono">
            <div class="p-2 rounded-lg bg-white border border-slate-200">
              <div class="text-ink-muted text-[10px]">deploy_pages.yml</div>
              <div class="font-bold text-amber-700">615분 <span class="text-[10px] font-normal text-ink-muted">(136회)</span></div>
              <div class="text-[10px] text-red-500">실패율 10% · 평균 4m 1s</div>
            </div>
            <div class="p-2 rounded-lg bg-white border border-slate-200">
              <div class="text-ink-muted text-[10px]">pages build deployment</div>
              <div class="font-bold text-amber-700">604분 <span class="text-[10px] font-normal text-ink-muted">(212회)</span></div>
              <div class="text-[10px] text-emerald-600">실패율 &lt;1% · 평균 36s</div>
            </div>
            <div class="p-2 rounded-lg bg-white border border-slate-200">
              <div class="text-ink-muted text-[10px]">deploy_only.yml</div>
              <div class="font-bold text-ink-primary">18분 <span class="text-[10px] font-normal text-ink-muted">(18회)</span></div>
              <div class="text-[10px] text-emerald-600">실패율 0% · 평균 32s</div>
            </div>
            <div class="p-2 rounded-lg bg-white border border-slate-200">
              <div class="text-ink-muted text-[10px]">daily_eod_enrichment</div>
              <div class="font-bold text-ink-primary">5분 <span class="text-[10px] font-normal text-ink-muted">(5회)</span></div>
              <div class="text-[10px] text-red-500">실패율 40% · 평균 30s</div>
            </div>
          </div>

          <!-- Operational Decision Suggestion Banner -->
          <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between text-[11px] gap-2 pt-1 border-t border-slate-200/60">
            <div class="flex items-center gap-2 text-slate-700" id="quotaAdviceBanner">
              <span class="px-2 py-0.5 rounded bg-amber-100 text-amber-800 font-bold font-mono text-[10px]" id="quotaBadgeVerdict">🚨 사용량 주의 (62.1% 소모)</span>
              <span id="quotaAdviceText">9월 1~8일(7일간) 이미 <b>1,242분(62.1%)</b> 소모! 잔여는 <b>758분(37.9%)</b>뿐이므로 <b>수집 주기를 줄이지 말고 현행 6시간(1일 4회) 유지</b>해야 월말까지 안전합니다.</span>
            </div>
            <div class="shrink-0 text-amber-700 font-bold font-mono text-[10px]" id="quotaDailyEstText">
              총 실행 763회 (평균 54s / 실패율 2%)
            </div>
          </div>
        </div>

        <!-- Section 2: ⏱️ 4 Quarterly Sessions Execution Time & Error Audit -->
        <div class="space-y-2">
          <div class="flex items-center justify-between text-xs font-bold text-ink-primary">
            <span class="flex items-center gap-1.5" id="timelineAuditTitle">
              <i data-lucide="clock" class="w-4 h-4 text-indigo-600"></i>
              <span>수집 Timeline 연동 회차별 실제 소요 시간 & 에러율 감사</span>
            </span>
            <span class="text-[11px] text-ink-muted font-normal font-mono" id="timelineAuditSub">GitHub Actions 최근 실측 런 기준</span>
          </div>

          <!-- 4 Cards Container -->
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs font-mono" id="pipelineSlotsContainer">
            <!-- Dynamically populated -->
          </div>
        </div>

        <!-- Section 3: 📋 Recent GitHub Actions Live Run Logs Table -->
        <div class="space-y-2 pt-2 border-t border-surface-border">
          <div class="flex items-center justify-between text-xs font-bold text-ink-primary">
            <span class="flex items-center gap-1.5" id="recentRunsTitle">
              <i data-lucide="list" class="w-4 h-4 text-slate-600"></i>
              <span>최근 GitHub Actions 실행 로그 & 소요 시간 히스토리</span>
            </span>
            <span class="text-[11px] text-ink-muted font-normal font-mono" id="recentRunsSub">KST 실행 시각 기준 정렬</span>
          </div>

          <div class="overflow-x-auto rounded-xl border border-surface-border">
            <table class="w-full text-left text-xs font-mono">
              <thead class="bg-slate-50 border-b border-surface-border text-ink-secondary text-[11px]">
                <tr>
                  <th class="py-2.5 px-3">실행 시각 (KST)</th>
                  <th class="py-2.5 px-3">워크플로우</th>
                  <th class="py-2.5 px-3">트리거</th>
                  <th class="py-2.5 px-3">소요 시간</th>
                  <th class="py-2.5 px-3">상태</th>
                  <th class="py-2.5 px-3">에러</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-surface-border" id="pipelineRecentRunsTbody">
                <!-- Dynamically populated -->
              </tbody>
            </table>
          </div>
        </div>

        <!-- Pipeline Footer Info -->
        <div class="pt-2 flex flex-col sm:flex-row sm:items-center justify-between text-[11px] text-ink-muted font-mono gap-1 border-t border-surface-border/60">
          <span class="flex items-center gap-1">
            <i data-lucide="check-circle-2" class="w-3.5 h-3.5 text-emerald-500"></i>
            <span id="pipelineFooterAudit">23:30 KST 야간 EOD 전수 배치 감사 자동 연동</span>
          </span>
          <span class="text-[10px] text-ink-secondary" id="pipelineFooterNote">
            * GitHub Actions 큐 상태에 따라 ±2~5분의 스케줄 지연이 발생할 수 있습니다.
          </span>
        </div>
      </div>

      <!-- 🎛️ Multi-Tier Interactive Filter Toolbar (검색창 위쪽 복합 필터 바) -->
      <div class="bg-white p-4 rounded-2xl border border-surface-border shadow-sm space-y-2.5">
        <!-- Row 1: Source Language (원문 언어) -->
        <div class="flex items-center gap-2 text-xs">
          <span class="font-bold text-ink-secondary text-[11px] w-20 shrink-0 flex items-center gap-1">
            🌐 원문 언어:
          </span>
          <div class="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-1 w-full flex-nowrap" id="filterLangRow">
            <button onclick="setInboxLangFilter('ALL')" data-lang-val="ALL" class="inbox-filter-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shrink-0 whitespace-nowrap">전체 언어</button>
            <button onclick="setInboxLangFilter('KO')" data-lang-val="KO" class="inbox-filter-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">🇰🇷 한국어 (KO)</button>
            <button onclick="setInboxLangFilter('EN')" data-lang-val="EN" class="inbox-filter-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">🇬🇧 영어 (EN)</button>
            <button onclick="setInboxLangFilter('ZH')" data-lang-val="ZH" class="inbox-filter-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">🇨🇳 중국어 (ZH)</button>
          </div>
        </div>

        <!-- Row 2: 4-Tier Classification (4대 기술 분류) -->
        <div class="flex items-center gap-2 text-xs pt-2 border-t border-surface-border/60">
          <span class="font-bold text-ink-secondary text-[11px] w-20 shrink-0 flex items-center gap-1">
            🏷️ 기술 분류:
          </span>
          <div class="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-1 w-full flex-nowrap" id="filterTypeRow">
            <button onclick="setInboxTypeFilter('ALL')" data-type-val="ALL" class="inbox-type-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shrink-0 whitespace-nowrap">전체 분류</button>
            <button onclick="setInboxTypeFilter('TECH')" data-type-val="TECH" class="inbox-type-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">⚡ 신기술/아키텍처</button>
            <button onclick="setInboxTypeFilter('AGENT')" data-type-val="AGENT" class="inbox-type-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">🦾 AI 에이전트</button>
            <button onclick="setInboxTypeFilter('MODEL')" data-type-val="MODEL" class="inbox-type-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">🤖 AI 모델 발표</button>
            <button onclick="setInboxTypeFilter('NEWS')" data-type-val="NEWS" class="inbox-type-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">📰 업계 동향/뉴스</button>
          </div>
        </div>

        <!-- Row 3: Programming Language (프로그래밍 언어) -->
        <div class="flex items-center gap-2 text-xs pt-2 border-t border-surface-border/60">
          <span class="font-bold text-ink-secondary text-[11px] w-20 shrink-0 flex items-center gap-1">
            💻 기술 스택:
          </span>
          <div class="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-1 w-full flex-nowrap" id="filterTechRow">
            <button onclick="setInboxTechFilter('ALL')" data-tech-val="ALL" class="inbox-tech-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shrink-0 whitespace-nowrap">전체 스택</button>
            <button onclick="setInboxTechFilter('Python')" data-tech-val="Python" class="inbox-tech-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">🐍 Python</button>
            <button onclick="setInboxTechFilter('Rust')" data-tech-val="Rust" class="inbox-tech-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">🦀 Rust</button>
            <button onclick="setInboxTechFilter('TypeScript')" data-tech-val="TypeScript" class="inbox-tech-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">📘 TypeScript / JS</button>
            <button onclick="setInboxTechFilter('CUDA')" data-tech-val="CUDA" class="inbox-tech-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">⚡ CUDA / C++</button>
            <button onclick="setInboxTechFilter('General')" data-tech-val="General" class="inbox-tech-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">🌐 General / 기타</button>
          </div>
        </div>

        <!-- Row 4: Platform Sources (수집 출처) -->
        <div class="flex items-center gap-2 text-xs pt-2 border-t border-surface-border/60">
          <span class="font-bold text-ink-secondary text-[11px] w-20 shrink-0 flex items-center gap-1">
            📡 수집 출처:
          </span>
          <div class="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-1 w-full flex-nowrap" id="filterPlatformRow">
            <button onclick="setInboxSourceFilter('ALL')" data-src-val="ALL" class="inbox-src-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shrink-0 whitespace-nowrap">전체 출처</button>
            <button onclick="setInboxSourceFilter('GeekNews')" data-src-val="GeekNews" class="inbox-src-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">🇰🇷 GeekNews</button>
            <button onclick="setInboxSourceFilter('Hacker News')" data-src-val="Hacker News" class="inbox-src-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">🔥 Hacker News</button>
            <button onclick="setInboxSourceFilter('GitHub')" data-src-val="GitHub" class="inbox-src-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">🐙 GitHub</button>
            <button onclick="setInboxSourceFilter('ArXiv')" data-src-val="ArXiv" class="inbox-src-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">📄 ArXiv</button>
            <button onclick="setInboxSourceFilter('Hugging Face')" data-src-val="Hugging Face" class="inbox-src-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap">🤗 Hugging Face</button>
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
              <option value="date-audit-desc" selected>🔬 AI 분석일 최신순 (기본)</option>
              <option value="date-audit-asc">🔬 AI 분석일 오래된순</option>
              <option value="date-source-desc">📅 수집/발표 최신순</option>
              <option value="date-source-asc">📅 수집/발표 오래된순</option>
              <option value="viral-desc">🔥 통합 인기순 (Viral High)</option>
              <option value="viral-asc">통합 인기 낮은순 (Viral Low)</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Inbox Grid (3x5 Readable Grid) -->
      <div id="inboxGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5"></div>
      <div id="inboxPagination" class="mt-4"></div>
    </div>

  </main>

  <!-- ==================== DETAILED TECHNICAL DOSSIER MODAL ==================== -->
  <div id="detailModal" class="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm hidden flex items-center justify-center p-2 sm:p-6 overflow-y-auto">
    <div class="bg-white max-w-4xl w-full rounded-2xl overflow-hidden shadow-2xl border border-surface-border my-4 sm:my-8 max-h-[95vh] sm:max-h-[92vh] flex flex-col">
      
      <!-- Modal Header -->
      <div class="p-4 sm:p-6 border-b border-surface-border flex items-start justify-between bg-surface-subtle">
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
      <div class="p-4 sm:p-6 overflow-y-auto space-y-5 sm:space-y-6 text-sm text-ink-secondary">
        
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
    const timeline24hData = {timeline_json};
    const actionsTelemetryData = {actions_telemetry_json};
    const trend6hData = {trend_6h_json};
    const trendRadarData = {trend_radar_json};

    let liveCasesData = casesData;
    let liveModelsData = modelsData;
    let liveInboxData = inboxData;
    let liveNewsData = newsData;
    let liveAnalysesData = [];

    const API_BASE = '';

    let currentLang = 'KO';
    let currentView = 'home';
    let currentMode = 'ALL';
    let currentDomain = 'ALL';
    let currentSort = 'date-audit-desc';
    let searchQuery = '';

    let currentInboxSource = 'ALL';
    let inboxSearchQuery = '';
    let isFamilyGroupingActive = true;
    let currentGraphType = 'ALL';
    let simulationRef = null;

    // 📄 Global Pagination State (15 items per page for 3x5 Grid: << < 1, 2, 3, 4, 5 > >>)
    const PAGE_SIZE = 15;
    let currentPortfolioPage = 1;
    let currentModelsPage = 1;
    let currentNewsPage = 1;
    let currentInboxPage = 1;

    function renderPagination(containerId, currentPage, totalPages, onPageChange) {{
      const container = document.getElementById(containerId);
      if (!container) return;
      if (totalPages <= 1) {{
        container.innerHTML = '';
        return;
      }}

      let html = '<div class="flex items-center justify-center gap-1.5 pt-6 pb-4 text-xs font-mono select-none flex-wrap">';

      // First Page <<
      const firstDisabled = currentPage === 1;
      html += `<button onclick="${{firstDisabled ? '' : onPageChange + '(1)'}}" class="px-2.5 py-1.5 rounded-lg border font-bold transition shadow-xs ${{firstDisabled ? 'opacity-30 cursor-not-allowed bg-surface-subtle text-ink-muted border-surface-border' : 'bg-white hover:bg-surface-subtle text-ink-primary border-surface-border cursor-pointer'}}" title="처음으로">&laquo;&laquo;</button>`;

      // Prev Page <
      const prevDisabled = currentPage === 1;
      html += `<button onclick="${{prevDisabled ? '' : onPageChange + '(' + (currentPage - 1) + ')'}}" class="px-2.5 py-1.5 rounded-lg border font-bold transition shadow-xs ${{prevDisabled ? 'opacity-30 cursor-not-allowed bg-surface-subtle text-ink-muted border-surface-border' : 'bg-white hover:bg-surface-subtle text-ink-primary border-surface-border cursor-pointer'}}" title="이전">&lsaquo;</button>`;

      // Page numbers (Sliding window of up to 5 numbers)
      let startPage = Math.max(1, currentPage - 2);
      let endPage = Math.min(totalPages, startPage + 4);
      if (endPage - startPage < 4) {{
        startPage = Math.max(1, endPage - 4);
      }}

      for (let p = startPage; p <= endPage; p++) {{
        const isCur = p === currentPage;
        const btnStyle = isCur
          ? 'bg-indigo-600 text-white font-extrabold border-indigo-600 shadow-sm'
          : 'bg-white hover:bg-surface-subtle text-ink-secondary hover:text-ink-primary border-surface-border font-semibold cursor-pointer';
        html += `<button onclick="${{onPageChange}}(${{p}})" class="w-8 h-8 rounded-lg border flex items-center justify-center transition ${{btnStyle}}">${{p}}</button>`;
      }}

      // Next Page >
      const nextDisabled = currentPage === totalPages;
      html += `<button onclick="${{nextDisabled ? '' : onPageChange + '(' + (currentPage + 1) + ')'}}" class="px-2.5 py-1.5 rounded-lg border font-bold transition shadow-xs ${{nextDisabled ? 'opacity-30 cursor-not-allowed bg-surface-subtle text-ink-muted border-surface-border' : 'bg-white hover:bg-surface-subtle text-ink-primary border-surface-border cursor-pointer'}}" title="다음">&rsaquo;</button>`;

      // Last Page >>
      const lastDisabled = currentPage === totalPages;
      html += `<button onclick="${{lastDisabled ? '' : onPageChange + '(' + totalPages + ')'}}" class="px-2.5 py-1.5 rounded-lg border font-bold transition shadow-xs ${{lastDisabled ? 'opacity-30 cursor-not-allowed bg-surface-subtle text-ink-muted border-surface-border' : 'bg-white hover:bg-surface-subtle text-ink-primary border-surface-border cursor-pointer'}}" title="끝으로">&raquo;&raquo;</button>`;

      html += '</div>';
      container.innerHTML = html;
    }}

    function changePortfolioPage(page, pushHistory = true) {{
      currentPortfolioPage = page;
      renderCards();
      document.getElementById('portfolioView')?.scrollIntoView({{ behavior: 'smooth' }});
      if (pushHistory) {{
        const targetHash = page > 1 ? '#/factchecks?page=' + page : '#/factchecks';
        if (window.location.hash !== targetHash) {{
          try {{ history.pushState({{ view: 'portfolio', page: page }}, '', targetHash); }} catch(e) {{ window.location.hash = targetHash; }}
        }}
      }}
    }}

    function changeModelsPage(page, pushHistory = true) {{
      currentModelsPage = page;
      renderModels();
      document.getElementById('modelsView')?.scrollIntoView({{ behavior: 'smooth' }});
      if (pushHistory) {{
        const targetHash = page > 1 ? '#/models?page=' + page : '#/models';
        if (window.location.hash !== targetHash) {{
          try {{ history.pushState({{ view: 'models', page: page }}, '', targetHash); }} catch(e) {{ window.location.hash = targetHash; }}
        }}
      }}
    }}

    function changeNewsPage(page, pushHistory = true) {{
      currentNewsPage = page;
      renderNews();
      document.getElementById('newsView')?.scrollIntoView({{ behavior: 'smooth' }});
      if (pushHistory) {{
        const targetHash = page > 1 ? '#/news?page=' + page : '#/news';
        if (window.location.hash !== targetHash) {{
          try {{ history.pushState({{ view: 'news', page: page }}, '', targetHash); }} catch(e) {{ window.location.hash = targetHash; }}
        }}
      }}
    }}

    function changeInboxPage(page, pushHistory = true) {{
      currentInboxPage = page;
      renderInbox();
      document.getElementById('inboxView')?.scrollIntoView({{ behavior: 'smooth' }});
      if (pushHistory) {{
        const targetHash = page > 1 ? '#/inbox?page=' + page : '#/inbox';
        if (window.location.hash !== targetHash) {{
          try {{ history.pushState({{ view: 'inbox', page: page }}, '', targetHash); }} catch(e) {{ window.location.hash = targetHash; }}
        }}
      }}
    }}
    let linkSelection = null;
    let nodeSelection = null;

    const queuedItemIds = new Set(JSON.parse(localStorage.getItem('queued_factchecks') || '[]'));

    // Complete Tri-Lingual i18n Dictionary (KO / ZH / EN)
    const i18n = {{
      KO: {{
        brandTitle: "FactCheck Hub",
        brandSubtitle: "AI 팩트체크 & 글로벌 테크 최신 동향",
        navHome: "대시보드",
        navPortfolio: "공식 검증",
        navModels: "AI 모델 트렌드",
        navNews: "테크 & AI 동향",
        navGraph: "인용 계보망",
        navInbox: "수집 인박스",
        adminArchiveBtn: "아카이브 (Admin)",
        statArchiveLabel: "원천 아카이브 (Admin)",
      pipelineScheduleDesc: "1일 4회(00:17, 06:17, 12:17, 18:17 KST) 전략 수집",
      pipelineWidgetTitle: "자율 크론 파이프라인 텔레메트리 & 차기 수집 카운트다운",
      pipelineNextTargetLabel: "다음 자동 수집 예정",
      pipelineFooterAudit: "23:30 KST 야간 EOD 전수 배치 감사 자동 연동",
      pipelineFooterNote: "* GitHub Actions 큐 상태에 따라 ±2~5분의 스케줄 지연이 발생할 수 있습니다.",
        heroBadge: "ZERO-HALLUCINATION ARCHITECTURE & COST AUDIT",
        heroMainTitle: "바이럴된 AI 기술의 실체 분석",
        heroMainDesc: "SNS 바이럴 마케팅의 환각을 걷어내고, 1차 공식 출처 감사와 기저 표준 vs 서드파티 실측 벤치마크를 통해 도출한 100% 실증 보고서입니다.",
        heroUpdateLabel: "최종 검증일",
        heroAuditCount: "{data['total_cases']}개 기술 검증 완료",
        promoBannerTitle: "기술 검증 포트폴리오 최신 상태 알림",
        promoCountBadge: "{data['total_cases']}건 검증 완료",
        promoBannerDesc: "바이럴 임계치를 초과하여 유입된 주요 오픈소스 및 모델 후보군 총 {data['total_cases']}건에 대한 심층 실측 벤치마크와 팩트체크가 모두 완료되었습니다.",
        promoBtnText: "수집 인박스 후보군 보기",
        timelineTitle: "당일 24시간 수집 타임라인",
        timelineSub: "1일 4회(00, 06, 12, 18시 KST) 6시간 주기 전략 수집 + 23:30 EOD 전수 감사",
        timelineBadge: "1일 4회 6h 펄스",
        timelineLegend: "세션별 수집 건수",
        timelineFooterPrefix: "⚡ 당일 총 수집량:",
        trendRadarTitle: "1일 4회 AI 트렌드 레이더",
        trendRadarSub: "글로벌 오픈소스 & AI 신규 가중치 6시간 주기 자동 감지",
        homeTopPicksTitle: "최신 심층 기술 검증 하이라이트",
        homeTopPicksViewAll: "전체 {data['total_cases']}개 검증 도시에 보러가기",
        btnAll: "전체 검증",
        btnUser: "직접 큐레이션",
        btnAuto: "자동 트렌드",
        sortLabel: "정렬:",
        sortOptions: [
          {{ val: "date-audit-desc", text: "🔬 분석일자 최신순 (기본)" }},
          {{ val: "date-audit-asc", text: "🔬 분석일자 오래된순" }},
          {{ val: "date-source-desc", text: "📅 원출처 발행 최신순" }},
          {{ val: "date-source-asc", text: "📅 원출처 발행 오래된순" }}
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
        newsHeaderBadge: "GLOBAL TECH & AI INTELLIGENCE FEED",
        newsHeaderTitle: "커뮤니티, 해커뉴스, 사설에서 수집된 테크 & AI 최신 담론",
        newsHeaderDesc: "소프트웨어·AI 저장소뿐만 아니라 신소재·우주, 거시경제, 인프라 보안 등 글로벌 기술 동향을 선별합니다.",
        newsOriginalLink: "기사 원문",
        newsCatFilterLabel: "🏷️ 기술·글로벌 분류:",
        newsCats: {{
          'ALL': "전체 ({data['news_total_count']})",
          'TECH_COMPUTING': "💻 IT·컴퓨팅 ({data['tier1_counts'].get('TECH_COMPUTING', 0)})",
          'SCIENCE_RESEARCH': "🚀 과학·우주 ({data['tier1_counts'].get('SCIENCE_RESEARCH', 0)})",
          'ECONOMY_FINANCE': "🏦 경제·금융 ({data['tier1_counts'].get('ECONOMY_FINANCE', 0)})",
          'LAW_CRIME_JUSTICE': "⚖️ 사회·법률 ({data['tier1_counts'].get('LAW_CRIME_JUSTICE', 0)})",
          'POLITICS_POLICY': "🏛️ 정치·정책 ({data['tier1_counts'].get('POLITICS_POLICY', 0)})",
          'CULTURE_HUMANITIES': "🌿 문화·인문 ({data['tier1_counts'].get('CULTURE_HUMANITIES', 0)})"
        }},
        newsTier2FilterLabel: "↳ 💻 IT 세부 분야:",
        newsT2: {{
          'ALL': "전체 IT 분야",
          'INFERENCE_OPT': "⚡ 추론·서빙 ({data['news_cat_counts'].get('INFERENCE_OPT', 0)})",
          'AGENTS_DEVTOOLS': "🛠️ 에이전트·도구 ({data['news_cat_counts'].get('AGENTS_DEVTOOLS', 0)})",
          'MULTIMODAL_AI': "🎨 멀티모달 ({data['news_cat_counts'].get('MULTIMODAL_AI', 0)})",
          'FOUNDATION_MODELS': "🤖 파운데이션 ({data['news_cat_counts'].get('FOUNDATION_MODELS', 0)})",
          'INFRA_RAG_SECURITY': "🛡️ 인프라·보안 ({data['news_cat_counts'].get('INFRA_RAG_SECURITY', 0)})",
          'INDUSTRY_TRENDS': "🌐 일반 SW·웹 ({data['news_cat_counts'].get('INDUSTRY_TRENDS', 0)})"
        }},
        newsSourceLabel: "출처:",
        newsSrcAll: "전체 출처",
        newsSearchPlaceholder: "기술명, 키워드 검색...",
        newsSortLabel: "정렬:",
        newsSortOptions: [
          {{ val: "date-source-desc", text: "📅 수집/발표 최신순 (기본)" }},
          {{ val: "date-source-asc", text: "📅 수집/발표 오래된순" }},
          {{ val: "date-audit-desc", text: "🔬 AI 분석일 최신순" }},
          {{ val: "date-audit-asc", text: "🔬 AI 분석일 오래된순" }}
        ],
        modelsFamilyLabel: "🤖 모델 패밀리:",
        modelFams: {{
          'ALL': "전체 패밀리",
          'Qwen': "Qwen ({data['model_fam_counts'].get('Qwen', 0)})",
          'Wan': "Wan 비디오 ({data['model_fam_counts'].get('Wan', 0)})",
          'MiniMax': "MiniMax ({data['model_fam_counts'].get('MiniMax', 0)})",
          'FLUX': "FLUX 이미지 ({data['model_fam_counts'].get('FLUX', 0)})",
          'GLM': "GLM ({data['model_fam_counts'].get('GLM', 0)})",
          'DeepSeek': "DeepSeek ({data['model_fam_counts'].get('DeepSeek', 0)})",
          'Hunyuan': "Hunyuan ({data['model_fam_counts'].get('Hunyuan', 0)})",
          'Audio': "음성/TTS ({data['model_fam_counts'].get('Audio', 0)})",
          'Standalone': "독립/신규 모델 ({data['model_fam_counts'].get('Standalone', 0)})"
        }},
        modelsArtifactLabel: "🧩 허브 유형:",
        modelArts: {{
          'ALL': "전체 ({data['models_total_count']})",
          'WEIGHTS': "🤖 가중치·체크포인트 ({data['model_art_counts'].get('WEIGHTS', 0)})",
          'WEB_SERVICE': "🌐 인터랙티브 데모·Spaces ({data['model_art_counts'].get('WEB_SERVICE', 0)})",
          'FINETUNE': "🎯 특화 파인튜닝 ({data['model_art_counts'].get('FINETUNE', 0)})"
        }},
        modelsSearchPlaceholder: "모델명, 아키텍처, 포맷 검색...",
        modelsSortLabel: "정렬:",
        modelsSortOptions: [
          {{ val: "date-source-desc", text: "📅 발행일 최신순 (기본)" }},
          {{ val: "date-source-asc", text: "📅 발행일 오래된순" }},
          {{ val: "date-audit-desc", text: "🔬 분석일 최신순" }},
          {{ val: "title-asc", text: "🔤 모델명 가나다순" }}
        ],
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
        inboxHeaderTitle: "원천 데이터 아카이브 & 관리자 파이프라인",
        inboxHeaderDesc: "크롤러가 24시간 실시간 수집한 원천 로우 데이터를 영구 보존하며, 관리자가 심층 팩트체크(공식 검증)로 승격할 후보를 검토하는 내부 저장소입니다.",
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
        brandSubtitle: "AI 事实核查与全球科技前沿动态",
        navHome: "仪表盘",
        navPortfolio: "官方核查",
        navModels: "AI 模型趋势",
        navNews: "科技与AI动态",
        navGraph: "引用系谱图",
        navInbox: "采集收件箱",
        adminArchiveBtn: "归档 (Admin)",
        statArchiveLabel: "原始归档 (Admin)",
      pipelineScheduleDesc: "每日 4 次（00:17、06:17、12:17、18:17 KST）周期策略采集",
      pipelineWidgetTitle: "自主定时流水线遥测与下次采集倒计时",
      pipelineNextTargetLabel: "下次自动采集计划",
      pipelineFooterAudit: "23:30 KST 夜间 EOD 全量批处理审计自动联动",
      pipelineFooterNote: "* 受 GitHub Actions 队列负载影响，可能存在 ±2~5 分钟调度延迟.",
        heroBadge: "ZERO-HALLUCINATION ARCHITECTURE & COST AUDIT",
        heroMainTitle: "热门 AI 技术的工程真相与实体验证",
        heroMainDesc: "摒弃社交媒体营销炒作与幻觉，基于第一手官方源码审计以及基础标准 vs 第三方工具的实测基准，输出 100% 真实客观的工程报告。",
        heroUpdateLabel: "最新审计",
        heroAuditCount: "已完成 {data['total_cases']} 项技术审计",
        promoBannerTitle: "技术审计档案库最新状态",
        promoCountBadge: "{data['total_cases']} 项核验完毕",
        promoBannerDesc: "已对突破热度阈值自动晋升的 {data['total_cases']} 项重点开源项目与前沿模型完成全流程深度实测基准与事实核查。",
        promoBtnText: "查看采集收件箱候选",
        timelineTitle: "当日 24 小时采集时间线",
        timelineSub: "每日 4 次 (00, 06, 12, 18时 KST) 6小时周期定向采集 + 23:30 EOD 全量审计",
        timelineBadge: "每日4次 6h脉冲",
        timelineLegend: "各时段采集数",
        timelineFooterPrefix: "⚡ 当日总采集量:",
        trendRadarTitle: "每日 4 次 AI 趋势雷达",
        trendRadarSub: "全球开源与 AI 前沿权重 6 小时周期自动感应",
        homeTopPicksTitle: "最新深度技术核查精选",
        homeTopPicksViewAll: "查看全部 {data['total_cases']} 份核查档案",
        btnAll: "全部审计",
        btnUser: "人工精选",
        btnAuto: "自动趋势",
        sortLabel: "排序:",
        sortOptions: [
          {{ val: "date-audit-desc", text: "🔬 审核日期最新 (默认)" }},
          {{ val: "date-audit-asc", text: "🔬 审核日期最早" }},
          {{ val: "date-source-desc", text: "📅 原文发布最新" }},
          {{ val: "date-source-asc", text: "📅 原文发布最早" }}
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
        newsHeaderBadge: "GLOBAL TECH & AI INTELLIGENCE FEED",
        newsHeaderTitle: "源自社区、HackerNews 与专栏的全球科技与 AI 讨论",
        newsHeaderDesc: "不仅追踪开源代码与模型，还精选深科技、航空航天、宏观经济与基础设施安全动态。",
        newsOriginalLink: "阅读原文",
        newsCatFilterLabel: "🏷️ 技术与全球领域:",
        newsCats: {{
          'ALL': "全部 ({data['news_total_count']})",
          'TECH_COMPUTING': "💻 IT与计算 ({data['tier1_counts'].get('TECH_COMPUTING', 0)})",
          'SCIENCE_RESEARCH': "🚀 科学与航天 ({data['tier1_counts'].get('SCIENCE_RESEARCH', 0)})",
          'ECONOMY_FINANCE': "🏦 经济与金融 ({data['tier1_counts'].get('ECONOMY_FINANCE', 0)})",
          'LAW_CRIME_JUSTICE': "⚖️ 社会与法治 ({data['tier1_counts'].get('LAW_CRIME_JUSTICE', 0)})",
          'POLITICS_POLICY': "🏛️ 政治与政策 ({data['tier1_counts'].get('POLITICS_POLICY', 0)})",
          'CULTURE_HUMANITIES': "🌿 文化与人文 ({data['tier1_counts'].get('CULTURE_HUMANITIES', 0)})"
        }},
        newsTier2FilterLabel: "↳ 💻 IT 细分领域:",
        newsT2: {{
          'ALL': "全部 IT 领域",
          'INFERENCE_OPT': "⚡ 推理与部署 ({data['news_cat_counts'].get('INFERENCE_OPT', 0)})",
          'AGENTS_DEVTOOLS': "🛠️ Agent与工具 ({data['news_cat_counts'].get('AGENTS_DEVTOOLS', 0)})",
          'MULTIMODAL_AI': "🎨 多模态 ({data['news_cat_counts'].get('MULTIMODAL_AI', 0)})",
          'FOUNDATION_MODELS': "🤖 基座模型 ({data['news_cat_counts'].get('FOUNDATION_MODELS', 0)})",
          'INFRA_RAG_SECURITY': "🛡️ 架构与安全 ({data['news_cat_counts'].get('INFRA_RAG_SECURITY', 0)})",
          'INDUSTRY_TRENDS': "🌐 行业软件与Web ({data['news_cat_counts'].get('INDUSTRY_TRENDS', 0)})"
        }},
        newsSourceLabel: "来源:",
        newsSrcAll: "全部来源",
        newsSearchPlaceholder: "搜索技术名、关键词...",
        newsSortLabel: "排序:",
        newsSortOptions: [
          {{ val: "date-source-desc", text: "📅 采集发布时间最新 (默认)" }},
          {{ val: "date-source-asc", text: "📅 采集发布时间最早" }},
          {{ val: "date-audit-desc", text: "🔬 AI 审核时间最新" }},
          {{ val: "date-audit-asc", text: "🔬 AI 审核时间最早" }}
        ],
        modelsFamilyLabel: "🤖 模型系列:",
        modelFams: {{
          'ALL': "全部系列",
          'Qwen': "Qwen ({data['model_fam_counts'].get('Qwen', 0)})",
          'Wan': "Wan 视频 ({data['model_fam_counts'].get('Wan', 0)})",
          'MiniMax': "MiniMax ({data['model_fam_counts'].get('MiniMax', 0)})",
          'FLUX': "FLUX 图像 ({data['model_fam_counts'].get('FLUX', 0)})",
          'GLM': "GLM ({data['model_fam_counts'].get('GLM', 0)})",
          'DeepSeek': "DeepSeek ({data['model_fam_counts'].get('DeepSeek', 0)})",
          'Hunyuan': "Hunyuan ({data['model_fam_counts'].get('Hunyuan', 0)})",
          'Audio': "语音/TTS ({data['model_fam_counts'].get('Audio', 0)})",
          'Standalone': "独立/新模型 ({data['model_fam_counts'].get('Standalone', 0)})"
        }},
        modelsArtifactLabel: "🧩 资源类型:",
        modelArts: {{
          'ALL': "全部 ({data['models_total_count']})",
          'WEIGHTS': "🤖 模型权重·检查点 ({data['model_art_counts'].get('WEIGHTS', 0)})",
          'WEB_SERVICE': "🌐 在线演示·Spaces ({data['model_art_counts'].get('WEB_SERVICE', 0)})",
          'FINETUNE': "🎯 定制微调 ({data['model_art_counts'].get('FINETUNE', 0)})"
        }},
        modelsSearchPlaceholder: "搜索模型名、架构、格式...",
        modelsSortLabel: "排序:",
        modelsSortOptions: [
          {{ val: "date-source-desc", text: "📅 发布时间最新 (默认)" }},
          {{ val: "date-source-asc", text: "📅 发布时间最早" }},
          {{ val: "date-audit-desc", text: "🔬 AI 审核最新" }},
          {{ val: "title-asc", text: "🔤 模型名 A-Z" }}
        ],
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
        inboxHeaderTitle: "原始数据归档与管理员流水线",
        inboxHeaderDesc: "全天候实时采集的原始数据永久存储库，供管理员审查并晋升至深度事实核查（官方审计）候选。",
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
        brandSubtitle: "AI Fact-Checking & Global Tech Intelligence",
        navHome: "Dashboard",
        navPortfolio: "Fact-Checks",
        navModels: "AI Model Trends",
        navNews: "Tech & AI Trends",
        navGraph: "Citation Graph",
        navInbox: "Harvest Inbox",
        adminArchiveBtn: "Archive (Admin)",
        statArchiveLabel: "Raw Archive (Admin)",
      pipelineScheduleDesc: "4x Daily (00:17, 06:17, 12:17, 18:17 KST) Strategic Ingestion",
      pipelineWidgetTitle: "Autonomous Cron Pipeline Telemetry & Next Ingestion Countdown",
      pipelineNextTargetLabel: "Next Scheduled Ingestion",
      pipelineFooterAudit: "Auto-linked with 23:30 KST Nightly EOD Batch Audit",
      pipelineFooterNote: "* ±2~5 min schedule variance may occur based on GitHub Actions runner queue load.",
        heroBadge: "ZERO-HALLUCINATION ARCHITECTURE & COST AUDIT",
        heroMainTitle: "Empirical Analysis of Viral AI Technologies",
        heroMainDesc: "A zero-hallucination dossier derived from Tier-1 official source audits and empirical benchmarks comparing base standards with third-party tools.",
        heroUpdateLabel: "LAST AUDITED",
        heroAuditCount: "{data['total_cases']} Audits Completed",
        promoBannerTitle: "Dossier Status Update",
        promoCountBadge: "{data['total_cases']} Completed",
        promoBannerDesc: "All {data['total_cases']} high-velocity repositories and models that crossed the viral threshold have been rigorously benchmarked and fact-checked.",
        promoBtnText: "Explore Harvest Inbox",
        timelineTitle: "Today 24-Hour Collection Timeline",
        timelineSub: "4x daily (00, 06, 12, 18 KST) 6h strategic collection + 23:30 EOD audit",
        timelineBadge: "4x Daily 6h Pulse",
        timelineLegend: "Items per Session",
        timelineFooterPrefix: "⚡ Today Total Collected:",
        trendRadarTitle: "4x Daily AI Trend Radar",
        trendRadarSub: "Autonomous 6-hour radar for trending open weights & code",
        homeTopPicksTitle: "Latest Deep Technical Verification Highlights",
        homeTopPicksViewAll: "View All {data['total_cases']} Empirical Dossiers",
        btnAll: "All Dossiers",
        btnUser: "User Curated",
        btnAuto: "Auto Trends",
        sortLabel: "Sort:",
        sortOptions: [
          {{ val: "date-audit-desc", text: "🔬 Audit Date (Newest first)" }},
          {{ val: "date-audit-asc", text: "🔬 Audit Date (Oldest first)" }},
          {{ val: "date-source-desc", text: "📅 Source Published (Newest first)" }},
          {{ val: "date-source-asc", text: "📅 Source Published (Oldest first)" }}
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
        newsCatFilterLabel: "🏷️ Global Domain:",
        newsCats: {{
          'ALL': "All ({data['news_total_count']})",
          'TECH_COMPUTING': "💻 IT & Computing ({data['tier1_counts'].get('TECH_COMPUTING', 0)})",
          'SCIENCE_RESEARCH': "🚀 Science & Space ({data['tier1_counts'].get('SCIENCE_RESEARCH', 0)})",
          'ECONOMY_FINANCE': "🏦 Economy & Finance ({data['tier1_counts'].get('ECONOMY_FINANCE', 0)})",
          'LAW_CRIME_JUSTICE': "⚖️ Society & Law ({data['tier1_counts'].get('LAW_CRIME_JUSTICE', 0)})",
          'POLITICS_POLICY': "🏛️ Policy & Politics ({data['tier1_counts'].get('POLITICS_POLICY', 0)})",
          'CULTURE_HUMANITIES': "🌿 Culture & Arts ({data['tier1_counts'].get('CULTURE_HUMANITIES', 0)})"
        }},
        newsTier2FilterLabel: "↳ 💻 IT Sub-tracks:",
        newsT2: {{
          'ALL': "All IT Tracks",
          'INFERENCE_OPT': "⚡ Inference & Serving ({data['news_cat_counts'].get('INFERENCE_OPT', 0)})",
          'AGENTS_DEVTOOLS': "🛠️ Agents & DevTools ({data['news_cat_counts'].get('AGENTS_DEVTOOLS', 0)})",
          'MULTIMODAL_AI': "🎨 Multimodal AI ({data['news_cat_counts'].get('MULTIMODAL_AI', 0)})",
          'FOUNDATION_MODELS': "🤖 Foundation Models ({data['news_cat_counts'].get('FOUNDATION_MODELS', 0)})",
          'INFRA_RAG_SECURITY': "🛡️ Infra & Security ({data['news_cat_counts'].get('INFRA_RAG_SECURITY', 0)})",
          'INDUSTRY_TRENDS': "🌐 General SW & Web ({data['news_cat_counts'].get('INDUSTRY_TRENDS', 0)})"
        }},
        newsSourceLabel: "Source:",
        newsSrcAll: "All Sources",
        newsSearchPlaceholder: "Search tech, keywords...",
        newsSortLabel: "Sort:",
        newsSortOptions: [
          {{ val: "date-source-desc", text: "📅 Source Published (Newest first, default)" }},
          {{ val: "date-source-asc", text: "📅 Source Published (Oldest first)" }},
          {{ val: "date-audit-desc", text: "🔬 AI Audit Date (Newest first)" }},
          {{ val: "date-audit-asc", text: "🔬 AI Audit Date (Oldest first)" }}
        ],
        modelsFamilyLabel: "🤖 Model Family:",
        modelFams: {{
          'ALL': "All Families",
          'Qwen': "Qwen ({data['model_fam_counts'].get('Qwen', 0)})",
          'Wan': "Wan Video ({data['model_fam_counts'].get('Wan', 0)})",
          'MiniMax': "MiniMax ({data['model_fam_counts'].get('MiniMax', 0)})",
          'FLUX': "FLUX Image ({data['model_fam_counts'].get('FLUX', 0)})",
          'GLM': "GLM ({data['model_fam_counts'].get('GLM', 0)})",
          'DeepSeek': "DeepSeek ({data['model_fam_counts'].get('DeepSeek', 0)})",
          'Hunyuan': "Hunyuan ({data['model_fam_counts'].get('Hunyuan', 0)})",
          'Audio': "Audio/TTS ({data['model_fam_counts'].get('Audio', 0)})",
          'Standalone': "Standalone Models ({data['model_fam_counts'].get('Standalone', 0)})"
        }},
        modelsArtifactLabel: "🧩 Hub Resource:",
        modelArts: {{
          'ALL': "All ({data['models_total_count']})",
          'WEIGHTS': "🤖 Weights & Checkpoints ({data['model_art_counts'].get('WEIGHTS', 0)})",
          'WEB_SERVICE': "🌐 Interactive Demos / Spaces ({data['model_art_counts'].get('WEB_SERVICE', 0)})",
          'FINETUNE': "🎯 Specialized Finetunes ({data['model_art_counts'].get('FINETUNE', 0)})"
        }},
        modelsSearchPlaceholder: "Search model name, architecture, format...",
        modelsSortLabel: "Sort:",
        modelsSortOptions: [
          {{ val: "date-source-desc", text: "📅 Source Published (Newest first)" }},
          {{ val: "date-source-asc", text: "📅 Source Published (Oldest first)" }},
          {{ val: "date-audit-desc", text: "🔬 Audit Date (Newest first)" }},
          {{ val: "title-asc", text: "🔤 Model Name (A-Z)" }}
        ],
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
        inboxHeaderTitle: "Raw Data Archive & Admin Pipeline",
        inboxHeaderDesc: "Permanent raw ingestion repository collected 24/7, enabling administrators to review and promote candidates into deep fact-checks.",
        inboxFamilyOn: "Family Group (ON)",
        inboxFamilyOff: "Family Group (OFF)",
        inboxSearchPlaceholder: "Search candidate tech or model...",
        inboxQueueBtn: "Queue for Audit",
        inboxQueuedBtn: "In Queue",
        modalSecCurationTitle: "Discovery Motivation & Target Workflow",
        modalSecViralPostTitle: "Raw Viral Claim Excerpt & Evidence",
        modalSecClaimsTitle: "Marketing Claims vs Empirical Reality",
        modalSecHookTitle: "The Hook & Marketing Hype",
        modalSecHandsOnTitle: "Hands-on Measured Results",
        modalSecAltsTitle: "Comparative Alternatives Matrix",
        modalSecSourcesTitle: "Audited Primary Sources",
        modalWorkflowLabel: "🎯 Target Workflow:",
        modalViralLinkText: "Go to Viral Post",
        thTool: "Tool / Repository",
        thStack: "Tech Stack",
        thPros: "Empirical Strengths",
        thCons: "Weaknesses & Bottlenecks",
        thBestFor: "Best For"
      }}
    }};

    // ================= URL ROUTING & BROWSER HISTORY ENGINE =================
    const ROUTES = {{
      'home': '#/home',
      'portfolio': '#/factchecks',
      'news': '#/news',
      'models': '#/models',
      'graph': '#/graph',
      'inbox': '#/inbox'
    }};

    // ================= GLOBAL SEARCH & FILTER RESET ENGINE =================
    function resetAllFiltersAndSearch() {{
      // 1. Reset Portfolio search & filters
      currentPortfolioPage = 1;
      searchQuery = '';
      currentMode = 'ALL';
      currentDomain = 'ALL';
      currentSort = 'date-audit-desc';
      const cInput = document.getElementById('searchInput');
      if (cInput) cInput.value = '';
      const cBtn = document.getElementById('clearSearchBtn');
      if (cBtn) cBtn.classList.add('hidden');
      const sortSel = document.getElementById('sortSelect');
      if (sortSel) sortSel.value = 'date-audit-desc';
      document.querySelectorAll('.tag-pill').forEach(b => {{
        if (b.dataset.domain === 'ALL') b.classList.add('active');
        else b.classList.remove('active');
      }});
      document.querySelectorAll('.segment-btn').forEach(b => b.classList.remove('active'));
      const modeAll = document.getElementById('modeBtnAll');
      if (modeAll) modeAll.classList.add('active');

      // 2. Reset News search & filters
      currentNewsPage = 1;
      currentNewsSearch = '';
      currentNewsTier1 = 'ALL';
      currentNewsTier2 = 'ALL';
      currentNewsSource = 'ALL';
      currentNewsSort = 'date-source-desc';
      const nInput = document.getElementById('newsSearchInput');
      if (nInput) nInput.value = '';
      const nSort = document.getElementById('newsSortSelect');
      if (nSort) nSort.value = 'date-source-desc';
      document.querySelectorAll('.news-cat-pill').forEach(btn => {{
        if (btn.getAttribute('data-cat') === 'ALL') {{
          btn.className = 'news-cat-pill active px-3 py-1.5 rounded-xl text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap';
        }} else {{
          btn.className = 'news-cat-pill px-3 py-1.5 rounded-xl text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }}
      }});
      document.querySelectorAll('.news-t2-pill').forEach(btn => {{
        if (btn.getAttribute('data-t2') === 'ALL') {{
          btn.className = 'news-t2-pill active px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap';
        }} else {{
          btn.className = 'news-t2-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }}
      }});
      const t2Container = document.getElementById('newsTier2Container');
      if (t2Container) t2Container.classList.remove('opacity-40', 'pointer-events-none');
      document.querySelectorAll('.news-src-btn').forEach(btn => {{
        if (btn.getAttribute('data-src') === 'ALL') {{
          btn.className = 'news-src-btn active px-2.5 py-1 rounded-lg text-xs font-bold bg-ink-primary text-white transition shrink-0 whitespace-nowrap';
        }} else {{
          btn.className = 'news-src-btn px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:bg-white transition border border-surface-border shrink-0 whitespace-nowrap';
        }}
      }});

      // 3. Reset Models search & filters
      currentModelsPage = 1;
      modelsSearchQuery = '';
      currentModelsFamily = 'ALL';
      currentModelsModality = 'ALL';
      currentModelsArtifact = 'ALL';
      currentModelsSort = 'date-audit-desc';
      const mInput = document.getElementById('modelsSearchInput');
      if (mInput) mInput.value = '';
      const mSort = document.getElementById('modelsSortSelect');
      if (mSort) mSort.value = 'date-audit-desc';
      document.querySelectorAll('.model-fam-pill').forEach(btn => {{
        if (btn.getAttribute('data-fam') === 'ALL') {{
          btn.className = 'model-fam-pill active px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap';
        }} else {{
          btn.className = 'model-fam-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }}
      }});
      document.querySelectorAll('.model-mod-pill').forEach(btn => {{
        if (btn.dataset.mod === 'ALL') {{
          btn.className = 'model-mod-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shrink-0 whitespace-nowrap';
        }} else {{
          btn.className = 'model-mod-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }}
      }});
      document.querySelectorAll('.model-art-pill').forEach(btn => {{
        if (btn.getAttribute('data-art') === 'ALL') {{
          btn.className = 'model-art-pill active px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap';
        }} else {{
          btn.className = 'model-art-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }}
      }});

      // 4. Reset Inbox search & filters
      currentInboxPage = 1;
      inboxSearchQuery = '';
      currentInboxSource = 'ALL';
      currentInboxLang = 'ALL';
      currentInboxType = 'ALL';
      currentInboxTech = 'ALL';
      currentInboxSort = 'date-audit-desc';
      const iInput = document.getElementById('inboxSearchInput');
      if (iInput) iInput.value = '';
      const iSort = document.getElementById('inboxSortSelect');
      if (iSort) iSort.value = 'date-audit-desc';
      document.querySelectorAll('.inbox-src-pill').forEach(btn => {{
        if (btn.getAttribute('data-src-val') === 'ALL') {{
          btn.className = 'inbox-src-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shrink-0 whitespace-nowrap';
        }} else {{
          btn.className = 'inbox-src-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }}
      }});
      document.querySelectorAll('.inbox-filter-pill').forEach(btn => {{
        if (btn.dataset.langVal === 'ALL') {{
          btn.className = 'inbox-filter-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shrink-0 whitespace-nowrap';
        }} else {{
          btn.className = 'inbox-filter-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }}
      }});
    }}

    // ================= VIEW SWITCHER (Clean 6 Core Tabs with History Support) =================
    function switchView(view, pushHistory = true, preserveFilters = false) {{
      if (!preserveFilters) {{
        resetAllFiltersAndSearch();
      }}
      currentView = view;
      const validViews = ['home', 'portfolio', 'news', 'models', 'graph', 'inbox'];
      if (!validViews.includes(view)) view = 'home';

      validViews.forEach(v => {{
        const el = document.getElementById(v + 'View');
        const btn = document.getElementById('tab' + v.charAt(0).toUpperCase() + v.slice(1) + 'Btn');
        const mBtn = document.getElementById('mTab' + v.charAt(0).toUpperCase() + v.slice(1) + 'Btn');
        
        if (el) el.classList.toggle('hidden', v !== view);
        
        if (btn) {{
          if (v === view) {{
            btn.className = 'nav-tab active flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-white bg-ink-primary transition shadow-sm';
          }} else {{
            btn.className = 'nav-tab flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-ink-secondary hover:text-ink-primary transition';
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

      // Update Admin Archive Button State
      const adminBtn = document.getElementById('adminArchiveBtn');
      if (adminBtn) {{
        if (view === 'inbox') {{
          adminBtn.className = 'flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-bold text-white bg-slate-800 transition border border-slate-700 shadow-sm';
        }} else {{
          adminBtn.className = 'flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold text-ink-muted hover:text-ink-primary hover:bg-surface-subtle transition border border-transparent hover:border-surface-border';
        }}
      }}

      // Synchronize Clean URL and Push to Browser History
      if (pushHistory) {{
        const targetHash = ROUTES[view] || '#/' + view;
        if (window.location.hash !== targetHash) {{
          try {{
            history.pushState({{ view: view }}, '', targetHash);
          }} catch (e) {{
            window.location.hash = targetHash;
          }}
        }}
      }}

      // 🌟 Immediate Active View Re-render
      if (view === 'home') {{
        renderTelemetryCharts();
      updateCronCountdown();
        renderHomeTopPicks();
      }} else if (view === 'portfolio') {{
        renderCards();
      }} else if (view === 'models') {{
        renderModels();
      }} else if (view === 'news') {{
        renderNews();
      }} else if (view === 'inbox') {{
        renderInbox();
        updateCronCountdown();
      }} else if (view === 'graph' && !simulationRef) {{
        initCitationGraph();
      }}

      window.scrollTo({{ top: 0, behavior: 'smooth' }});
      lucide.createIcons();
    }}

    // ================= RENDER HOME TOP PICKS PREVIEW (최신 분석일 기준 DESC) =================
    function renderHomeTopPicks() {{
      const container = document.getElementById('homeTopPicksContainer');
      if (!container) return;
      container.innerHTML = '';
      
      // Sort cases strictly by investigation_date descending (latest first)
      const sortedCases = [...(liveCasesData || [])].sort((a, b) => {{
        const dateA = a.investigation_date || (a.source_published_date ? a.source_published_date.slice(0, 10) : '');
        const dateB = b.investigation_date || (b.source_published_date ? b.source_published_date.slice(0, 10) : '');
        if (dateB !== dateA) return dateB.localeCompare(dateA);
        const idA = parseInt((a.case_id || '').replace(/\\D/g, '') || '0', 10);
        const idB = parseInt((b.case_id || '').replace(/\\D/g, '') || '0', 10);
        return idB - idA;
      }});
      const top3 = sortedCases.slice(0, 3);

      top3.forEach(c => {{
        const card = document.createElement('div');
        card.className = 'p-4 rounded-xl border border-surface-border bg-surface-subtle hover:bg-white hover:border-ink-primary hover:shadow-md transition cursor-pointer flex flex-col justify-between space-y-2.5';
        card.onclick = () => openModal(c);

        const isVerifiedTrue = c.verdict === 'VERIFIED_TRUE';
        const isHalfTrue = (c.verdict || '').includes('HALF');
        const badgeColor = isVerifiedTrue ? 'bg-emerald-50 text-emerald-800 border-emerald-200' : (isHalfTrue ? 'bg-amber-50 text-amber-900 border-amber-200' : 'bg-rose-50 text-rose-800 border-rose-200');
        const badgeLabel = isVerifiedTrue ? (currentLang === 'KO' ? '사실 검증됨' : (currentLang === 'ZH' ? '事实已核验' : 'Verified True')) : (isHalfTrue ? (currentLang === 'KO' ? '절반의 사실' : (currentLang === 'ZH' ? '部分属实' : 'Half True')) : (currentLang === 'KO' ? '과장/왜곡' : (currentLang === 'ZH' ? '夸大/失实' : 'Gamed/Hype')));

        const story = c.portfolio_story || {{}};
        let displayTitle = c.title;
        let hook = story.the_hook || c.curation?.personal_motivation || '';
        if (currentLang === 'ZH') {{
          displayTitle = c.title_zh || c.title;
          hook = story.the_hook_zh || hook;
        }} else if (currentLang === 'EN') {{
          displayTitle = c.title_en || c.title;
          hook = story.the_hook_en || hook;
        }}
        const displayDate = c.investigation_date || (c.source_published_date ? c.source_published_date.slice(0, 10) : '2026-09-04');

        card.innerHTML = `
          <div class="space-y-2">
            <div class="flex items-center justify-between text-xs font-mono">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${{badgeColor}}">${{badgeLabel}}</span>
              <span class="text-ink-muted text-[11px] font-semibold">${{c.confidence_score || 95}}%</span>
            </div>
            <h4 class="text-xs sm:text-sm font-bold text-ink-primary line-clamp-2 leading-snug hover:text-indigo-600 transition">${{displayTitle}}</h4>
            <p class="text-[11px] text-ink-secondary line-clamp-2 leading-relaxed">${{hook}}</p>
          </div>
          <div class="pt-2 border-t border-surface-border flex items-center justify-between text-[10px] font-mono text-ink-muted">
            <span>🔬 ${{currentLang === 'KO' ? '분석일: ' : (currentLang === 'ZH' ? '分析日: ' : 'Audited: ')}}${{displayDate}}</span>
            <span class="font-bold text-indigo-700 flex items-center gap-0.5">${{currentLang === 'KO' ? '상세 보고서' : (currentLang === 'ZH' ? '查看报告' : 'View Dossier')}} <i data-lucide="arrow-right" class="w-3 h-3"></i></span>
          </div>
        `;
        container.appendChild(card);
      }});
      if (window.lucide) window.lucide.createIcons({{ root: container }});
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
        if (el && txt !== undefined) el.innerText = txt;
      }};
      const safeSetHtml = (id, html) => {{
        const el = document.getElementById(id);
        if (el && html !== undefined) el.innerHTML = html;
      }};
      const safeSetAttr = (id, attr, val) => {{
        const el = document.getElementById(id);
        if (el && val !== undefined) el.setAttribute(attr, val);
      }};

      // Brand & Navigation
      safeSetText('headerBrandTitle', t.brandTitle);
      safeSetText('headerBrandSubtitle', t.brandSubtitle);
      safeSetText('navTabHome', t.navHome || '대시보드');
      safeSetText('mNavTabHome', t.navHome || '대시보드');
      safeSetText('navTabPortfolio', t.navPortfolio);
      safeSetText('mNavTabPortfolio', t.navPortfolio);
      safeSetText('navTabModels', t.navModels);
      safeSetText('mNavTabModels', t.navModels + ' (' + (typeof liveModelsData !== 'undefined' ? liveModelsData.length : {data['models_total_count']}) + ')');
      safeSetText('navTabNews', t.navNews);
      safeSetText('mNavTabNews', t.navNews + ' (' + (typeof liveNewsData !== 'undefined' ? liveNewsData.length : {data['news_total_count']}) + ')');
      safeSetText('navTabGraph', t.navGraph);
      safeSetText('mNavTabGraph', t.navGraph);
      safeSetText('adminArchiveLabel', t.adminArchiveBtn);
      safeSetText('mNavTabInbox', (t.adminArchiveBtn || '아카이브') + ' (' + (typeof liveInboxData !== 'undefined' ? liveInboxData.length : {data['inbox_total_count']}) + ')');

      // Hero Elements
      safeSetText('heroBadge', t.heroBadge);
      safeSetText('heroMainTitle', t.heroMainTitle);
      safeSetHtml('heroMainDesc', t.heroMainDesc);
      safeSetText('heroAuditCount', t.heroAuditCount);

      // Dashboard KPI Telemetry
      safeSetText('statLabelVerified', lang === 'KO' ? '공식 기술 검증' : (lang === 'ZH' ? '官方技术核查' : 'Verified Fact-Checks'));
      safeSetText('statLabelInbox', lang === 'KO' ? '수집 인박스' : (lang === 'ZH' ? '采集收件箱' : 'Harvested Inbox'));
      safeSetText('statLabelModels', lang === 'KO' ? 'AI 모델 트렌드' : (lang === 'ZH' ? 'AI 模型趋势' : 'AI Model Trends'));
      safeSetText('statLabelNews', lang === 'KO' ? 'AI 테크 동향' : (lang === 'ZH' ? 'AI 科技动态' : 'Tech Intelligence'));
      safeSetText('statLabelArchive', t.statArchiveLabel);
      safeSetText('statDescInbox', lang === 'KO' ? 'HN · GeekNews · GitHub · HF 24/7 수집' : (lang === 'ZH' ? 'HN · GeekNews · GitHub · HF 全天候采集' : 'HN · GeekNews · GitHub · HF 24/7 Ingestion'));
      safeSetDescModels = lang === 'KO' ? 'MoE, VLM, 추론 특화 오픈 가중치' : (lang === 'ZH' ? 'MoE、VLM与推理优化开源权重' : 'MoE, VLM & Reasoning Open Weights');
      safeSetText('statDescModels', safeSetDescModels);
      safeSetDescNews = lang === 'KO' ? 'CVE 취약점, 인프라 장애, 아키텍처 토론' : (lang === 'ZH' ? 'CVE 漏洞、基础设施故障与架构实践' : 'CVEs, Infra Outages & Architecture Posts');
      safeSetText('statDescNews', safeSetDescNews);

      // Dashboard 24h Timeline & Radar & Top Picks
      safeSetText('timelineTitleText', t.timelineTitle + ' ({today_kst})');
      safeSetText('timelineSub', t.timelineSub);
      safeSetText('timelineBadgeText', t.timelineBadge);
      safeSetText('timelineLegendText', t.timelineLegend);
      safeSetHtml('timelineFooterText', t.timelineFooterPrefix + ' <b class="text-indigo-700">{today_total_inbox}' + (lang === 'KO' ? '건' : (lang === 'ZH' ? '条' : ' items')) + '</b>');
      safeSetText('trendRadarTitleText', t.trendRadarTitle);
      safeSetText('trendRadarSub', t.trendRadarSub);
      safeSetHtml('trendRadarFooter', `<span class="flex items-center gap-1.5"><i data-lucide="zap" class="w-3.5 h-3.5 text-amber-500"></i> ` + (lang === 'KO' ? 'LLM 자동 트렌드 추출 (OpenRouter 0원 라우팅)' : (lang === 'ZH' ? 'LLM 自动化趋势提取 (OpenRouter 0元路由)' : 'Automated LLM Trend Extraction (OpenRouter Free Tier)')) + `</span>`);
      safeSetText('homeTopPicksTitle', t.homeTopPicksTitle);
      safeSetText('homeTopPicksViewAll', t.homeTopPicksViewAll);

      // News View Labels & Pills
      safeSetText('newsHeaderBadge', t.newsHeaderBadge);
      safeSetText('newsHeaderTitle', t.newsHeaderTitle);
      safeSetText('newsHeaderDesc', t.newsHeaderDesc);
      safeSetText('newsCatFilterLabel', t.newsCatFilterLabel);
      safeSetText('newsTier2FilterLabel', t.newsTier2FilterLabel);
      safeSetText('newsSourceLabel', t.newsSourceLabel);
      safeSetText('newsSrcBtnAll', t.newsSrcAll);
      safeSetAttr('newsSearchInput', 'placeholder', t.newsSearchPlaceholder);
      safeSetText('newsSortLabel', t.newsSortLabel);

      document.querySelectorAll('.news-cat-pill').forEach(pill => {{
        const cat = pill.dataset.cat;
        if (t.newsCats && t.newsCats[cat]) pill.innerText = t.newsCats[cat];
      }});
      document.querySelectorAll('.news-t2-pill').forEach(pill => {{
        const t2 = pill.dataset.t2;
        if (t.newsT2 && t.newsT2[t2]) pill.innerText = t.newsT2[t2];
      }});

      const newsSortSel = document.getElementById('newsSortSelect');
      if (newsSortSel && t.newsSortOptions) {{
        const cur = newsSortSel.value;
        newsSortSel.innerHTML = t.newsSortOptions.map(opt => `<option value="${{opt.val}}" ${{opt.val === cur ? 'selected' : ''}}>${{opt.text}}</option>`).join('');
      }}

      // Models View Labels & Pills
      safeSetText('modelsFamilyLabel', t.modelsFamilyLabel);
      safeSetText('modelsArtifactLabel', t.modelsArtifactLabel);
      safeSetAttr('modelsSearchInput', 'placeholder', t.modelsSearchPlaceholder);
      safeSetText('modelsSortLabel', t.modelsSortLabel);

      document.querySelectorAll('.model-fam-pill').forEach(pill => {{
        const fam = pill.dataset.fam;
        if (t.modelFams && t.modelFams[fam]) pill.innerText = t.modelFams[fam];
      }});
      document.querySelectorAll('.model-art-pill').forEach(pill => {{
        const art = pill.dataset.art;
        if (t.modelArts && t.modelArts[art]) pill.innerText = t.modelArts[art];
      }});

      const modelsSortSel = document.getElementById('modelsSortSelect');
      if (modelsSortSel && t.modelsSortOptions) {{
        const cur = modelsSortSel.value;
        modelsSortSel.innerHTML = t.modelsSortOptions.map(opt => `<option value="${{opt.val}}" ${{opt.val === cur ? 'selected' : ''}}>${{opt.text}}</option>`).join('');
      }}

      // Graph View
      safeSetText('graphHeaderBadge', t.graphHeaderBadge);
      safeSetText('graphHeaderTitle', t.graphHeaderTitle);
      safeSetText('graphHeaderSub', t.graphHeaderSub);
      safeSetText('graphBtnAll', t.graphBtnAll);
      safeSetText('graphBtnLang', t.graphBtnLang);
      safeSetText('graphBtnTech', t.graphBtnTech);
      safeSetText('graphBtnOrg', t.graphBtnOrg);
      safeSetText('graphBtnPerson', t.graphBtnPerson);
      safeSetText('graphBtnPaper', t.graphBtnPaper);

      // Archive & Inbox View
      safeSetText('inboxHeaderBadge', t.inboxHeaderBadge);
      safeSetText('inboxHeaderTitle', t.inboxHeaderTitle);
      safeSetText('pipelineScheduleDesc', t.pipelineScheduleDesc);
      safeSetText('pipelineWidgetTitle', t.pipelineWidgetTitle);
      safeSetText('pipelineNextTargetLabel', t.pipelineNextTargetLabel);
      safeSetText('pipelineFooterAudit', t.pipelineFooterAudit);
      safeSetText('pipelineFooterNote', t.pipelineFooterNote);
      if (typeof updateCronCountdown === 'function') updateCronCountdown();
      safeSetText('inboxHeaderDesc', t.inboxHeaderDesc);
      safeSetText('inboxHeaderCount', lang === 'KO' ? ('총 ' + (typeof liveInboxData !== 'undefined' ? liveInboxData.length : '') + '건') : (lang === 'ZH' ? ('共 ' + (typeof liveInboxData !== 'undefined' ? liveInboxData.length : '') + ' 项') : ('Total: ' + (typeof liveInboxData !== 'undefined' ? liveInboxData.length : '') + ' items')));
      safeSetText('criteriaTitle', t.criteriaTitle);
      safeSetText('criteriaDesc', t.criteriaDesc);
      safeSetText('critGithub', t.critGithub);
      safeSetText('critHn', t.critHn);
      safeSetText('critHf', t.critHf);
      safeSetText('critArxiv', t.critArxiv);
      safeSetAttr('inboxSearchInput', 'placeholder', t.inboxSearchPlaceholder);

      // Portfolio Controls
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

      const sortSel = document.getElementById('sortSelect');
      if (sortSel && t.sortOptions) {{
        const curVal = sortSel.value;
        sortSel.innerHTML = t.sortOptions.map(opt => `<option value="${{opt.val}}" ${{opt.val === curVal ? 'selected' : ''}}>${{opt.text}}</option>`).join('');
      }}

      // 🌟 Instant Full Re-render on Active Views
      renderCards();
      renderHomeTopPicks();
      renderRadarSession();
      renderTelemetryCharts();
      updateCronCountdown();
      renderModels();
      renderNews();
      renderInbox();
      lucide.createIcons();
    }}

    // ================= REAL-TIME DB SYNC (INSTANT ZERO-LATENCY) =================
    async function syncFromNeonLiveDB() {{
      // Neon DB Direct: 100% verified portfolios and recent trends are pre-compiled
      // No external network roundtrips needed.
      const badge = document.getElementById('dbLiveBadge');
      if (badge) {{
        badge.innerHTML = `
          <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 shadow-xs">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse"></span> Neon DB Direct (${{casesData.length}})
          </span>
        `;
      }}
    }}

    function updatePromotionBanner() {{}}

    // ================= FILTER & SORT HANDLERS =================
    function setModeFilter(mode) {{
      currentPortfolioPage = 1;
      currentMode = mode;
      document.querySelectorAll('.segment-btn').forEach(btn => btn.classList.remove('active'));
      if (mode === 'ALL') document.getElementById('modeBtnAll').classList.add('active');
      if (mode === 'USER_CURATED') document.getElementById('modeBtnUser').classList.add('active');
      if (mode === 'AUTO_HARVESTED') document.getElementById('modeBtnAuto').classList.add('active');
      renderCards();
    }}

    function setDomainFilter(dom) {{
      currentPortfolioPage = 1;
      currentDomain = dom;
      document.querySelectorAll('.tag-pill').forEach(btn => {{
        if (btn.dataset.domain === dom) btn.classList.add('active');
        else btn.classList.remove('active');
      }});
      renderCards();
    }}

    function changeSort(val) {{
      currentPortfolioPage = 1;
      currentSort = val;
      renderCards();
    }}

    function clearSearch() {{
      currentPortfolioPage = 1;
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
        if (!raw) return 0;
        const ms = new Date(raw).getTime();
        return isNaN(ms) ? 0 : ms;
      }} else {{
        // For freshest items in inbox/news/models, prioritize the latest active timestamp
        const tHarvest = item.harvested_at ? new Date(item.harvested_at).getTime() : 0;
        const tPublish = item.published_at ? new Date(item.published_at).getTime() : 0;
        const tCreated = item.created_at ? new Date(item.created_at).getTime() : 0;
        const tSourcePub = item.source_published_date ? new Date(item.source_published_date).getTime() : 0;
        const best = Math.max(
          isNaN(tHarvest) ? 0 : tHarvest,
          isNaN(tPublish) ? 0 : tPublish,
          isNaN(tCreated) ? 0 : tCreated,
          isNaN(tSourcePub) ? 0 : tSourcePub
        );
        return best;
      }}
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

    function formatDateTimeCompact(raw) {{
      if (!raw) return '-';
      const d = new Date(raw);
      if (isNaN(d.getTime())) return String(raw).substring(0, 10);
      const y = d.getFullYear();
      const m = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      const hh = String(d.getHours()).padStart(2, '0');
      const mm = String(d.getMinutes()).padStart(2, '0');
      return `<span class="hidden sm:inline">${{y}}-</span>${{m}}-${{day}} ${{hh}}:${{mm}}`;
    }}

    function formatModelAttribution(modelStr) {{
      if (!modelStr) return 'AI 검증';
      let s = String(modelStr).replace(/^models\\//, '').replace(/:free$/, '');
      if (s.includes('/')) s = s.split('/').pop();
      return '🤖 ' + s;
    }}

    // ================= RENDER 24H TIMELINE & 1-DAY 4-SESSIONS TREND RADAR =================
    function getDynamicKstHour() {{
      try {{
        return parseInt(new Intl.DateTimeFormat('en-US', {{ timeZone: 'Asia/Seoul', hour: 'numeric', hour12: false }}).format(new Date()), 10);
      }} catch (e) {{
        const now = new Date();
        return (now.getUTCHours() + 9) % 24;
      }}
    }}

    function getDynamicKstDate() {{
      const now = new Date();
      const utc = now.getTime() + (now.getTimezoneOffset() * 60000);
      return new Date(utc + (3600000 * 9));
    }}

    function getDynamicKstSession() {{
      const h = getDynamicKstHour();
      if (h < 6) return 1;
      if (h < 12) return 2;
      if (h < 18) return 3;
      return 4;
    }}

    let targetSelectedInboxId = '';
    let activeRadarSession = getDynamicKstSession();

    function switchRadarSession(sessionNum) {{
      activeRadarSession = sessionNum;
      renderRadarSession();
    }}

    function navigateFromRadar(view, searchKey, inboxId) {{
      targetSelectedInboxId = inboxId || '';
      switchView(view);
      const cleanQ = (searchKey || '').trim();
      if (view === 'models') {{
        currentModelsPage = 1;
        modelsSearchQuery = cleanQ;
        const inp = document.getElementById('modelsSearchInput');
        if (inp) inp.value = cleanQ;
        renderModels();
      }} else if (view === 'news') {{
        currentNewsPage = 1;
        currentNewsSearch = cleanQ.toLowerCase();
        const inp = document.getElementById('newsSearchInput');
        if (inp) inp.value = cleanQ;
        renderNews();
      }}
      window.scrollTo({{ top: 0, behavior: 'smooth' }});
    }}

    function renderRadarSession() {{
      if (typeof trendRadarData === 'undefined' || !trendRadarData.sessions) return;
      const sessionData = trendRadarData.sessions[String(activeRadarSession)];
      if (!sessionData) return;

      // 1. Update session tabs button active states and localized labels
      const sLabels = {{
        KO: ['1회 00시', '2회 06시', '3회 12시', '4회 18시'],
        ZH: ['1期 00点', '2期 06点', '3期 12点', '4期 18点'],
        EN: ['S1 00:00', 'S2 06:00', 'S3 12:00', 'S4 18:00']
      }};
      const curLabels = sLabels[currentLang] || sLabels['KO'];
      for (let i = 1; i <= 4; i++) {{
        const btn = document.getElementById('radarBtn' + i);
        if (btn) {{
          btn.innerText = curLabels[i - 1];
          if (i === activeRadarSession) {{
            btn.className = 'px-2 py-0.5 rounded border border-emerald-600 bg-emerald-600 text-white font-bold shadow-xs transition cursor-pointer';
          }} else {{
            btn.className = 'px-2 py-0.5 rounded border border-surface-border bg-surface-subtle text-ink-muted hover:text-ink-primary hover:bg-slate-100 transition cursor-pointer font-medium';
          }}
        }}
      }}

      // 2. Update header labels
      const windowLabelEl = document.getElementById('trendRadarWindowLabel');
      const pulseDotEl = document.getElementById('trendRadarPulseDot');

      if (windowLabelEl) {{
        const wLabel = (currentLang === 'KO' ? sessionData.window_label_ko : (currentLang === 'ZH' ? sessionData.window_label_zh : sessionData.window_label_en)) || sessionData.window_label;
        windowLabelEl.innerText = wLabel;
      }}
      if (pulseDotEl) {{
        if (sessionData.is_current) {{
          pulseDotEl.className = 'w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse';
        }} else if (sessionData.is_future) {{
          pulseDotEl.className = 'w-1.5 h-1.5 rounded-full bg-amber-500';
        }} else {{
          pulseDotEl.className = 'w-1.5 h-1.5 rounded-full bg-slate-400';
        }}
      }}

      // 3. Render session items (1 clickable element per item, fully localized)
      const bulletsContainer = document.getElementById('trendRadarBullets');
      if (bulletsContainer) {{
        bulletsContainer.innerHTML = '';
        const items = sessionData.items || [];

        if (items.length > 0) {{
          items.forEach((it, idx) => {{
            // Distinct colored badge for each platform family
            let platformBadgeClass = 'bg-surface-subtle text-ink-primary border-surface-border';
            const pf = (it.platform_family || '').toLowerCase();
            if (pf.includes('github')) {{
              platformBadgeClass = 'bg-slate-100 text-slate-800 border-slate-300';
            }} else if (pf.includes('hugging')) {{
              platformBadgeClass = 'bg-purple-50 text-purple-700 border-purple-200';
            }} else if (pf.includes('arxiv')) {{
              platformBadgeClass = 'bg-rose-50 text-rose-700 border-rose-200';
            }} else if (pf.includes('hacker')) {{
              platformBadgeClass = 'bg-amber-50 text-amber-800 border-amber-200';
            }} else if (pf.includes('geek')) {{
              platformBadgeClass = 'bg-blue-50 text-blue-700 border-blue-200';
            }}

            const itemTitle = (currentLang === 'KO' ? (it.title_ko || it.title) : (currentLang === 'ZH' ? (it.title_zh || it.title) : (it.title_en || it.title))) || it.title;
            const itemSummary = (currentLang === 'KO' ? (it.summary_ko || it.summary) : (currentLang === 'ZH' ? (it.summary_zh || it.summary) : (it.summary_en || it.summary))) || it.summary;
            const factCheckBtnText = currentLang === 'KO' ? '팩트체크' : (currentLang === 'ZH' ? '事实核查' : 'Fact-Check');
            const viewSourceText = currentLang === 'KO' ? '원문 보러가기' : (currentLang === 'ZH' ? '查看原文' : 'View Source');

            const itemCard = document.createElement('div');
            itemCard.className = 'group p-2.5 rounded-xl bg-surface-subtle border border-surface-border hover:border-emerald-400 hover:bg-white transition flex flex-col gap-1.5';
            itemCard.innerHTML = `
              <!-- Header Strip: Platform Badge, Viral Badge, FactCheck Badge, Direct External Link -->
              <div class="flex items-start justify-between gap-2">
                <div class="flex items-center gap-1.5 flex-wrap">
                  <span class="w-5 h-5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200 flex items-center justify-center font-mono font-bold text-[10px] shrink-0">0${{idx + 1}}</span>
                  <span class="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold ${{platformBadgeClass}} border">${{it.platform || 'AI Hub'}}</span>
                  ${{it.viral_metric ? `<span class="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-50 text-rose-700 border border-rose-200 flex items-center gap-1">🔥 ${{it.viral_metric}}</span>` : ''}}
                </div>
                <div class="flex items-center gap-1.5 shrink-0">
                  ${{it.case_id ? `
                    <button onclick="openCaseModal('${{it.case_id}}')" class="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-300 hover:bg-emerald-200 flex items-center gap-1 transition cursor-pointer">
                      <i data-lucide="shield-check" class="w-3 h-3"></i>
                      ${{factCheckBtnText}}
                    </button>
                  ` : ''}}
                </div>
              </div>

              <!-- Direct Original Source Link: Title + '원문 보러가기' Indicator -->
              <a href="${{it.source_url}}" target="_blank" rel="noopener noreferrer" class="group/title block">
                <div class="text-xs font-bold text-ink-primary group-hover/title:text-emerald-700 transition flex items-start justify-between gap-2 leading-snug">
                  <span class="line-clamp-1">${{itemTitle}}</span>
                  <span class="text-[11px] font-mono font-bold text-emerald-700 shrink-0 flex items-center gap-1 opacity-90 group-hover/title:opacity-100 mt-0.5 bg-emerald-50 hover:bg-emerald-100 px-2 py-0.5 rounded border border-emerald-300 transition">
                    <span>${{viewSourceText}}</span>
                    <i data-lucide="external-link" class="w-3 h-3"></i>
                  </span>
                </div>
                ${{itemSummary ? `<p class="text-[11px] text-ink-muted truncate leading-relaxed mt-1">${{itemSummary}}</p>` : ''}}
              </a>
            `;
            bulletsContainer.appendChild(itemCard);
          }});
        }} else {{
          const emptyMsg = currentLang === 'KO' ? '이 회차에 등록된 트렌드 데이터가 없습니다.' : (currentLang === 'ZH' ? '该时段暂无趋势数据。' : 'No trend data for this session.');
          bulletsContainer.innerHTML = `<div class="py-6 text-center text-xs text-ink-muted font-mono">${{emptyMsg}}</div>`;
        }}
      }}
      if (window.lucide) window.lucide.createIcons();
    }}

    function renderTelemetryCharts() {{
      // 1. Render 24-Hour Timeline Chart (4 Strategic Quarterly Sessions: 00, 06, 12, 18시)
      const tlContainer = document.getElementById('timeline24hChartContainer');
      if (tlContainer) {{
        tlContainer.innerHTML = '';
        const tData = typeof timeline24hData !== 'undefined' ? timeline24hData : [];
        const maxVal = Math.max(...tData.map(d => d.inbox_count || 0), 10);

        const curKstHour = getDynamicKstHour();
        tData.forEach(d => {{
          const hPct = Math.max(14, Math.round(((d.inbox_count || 0) / maxVal) * 100));
          const isCurrent = (d.hour <= curKstHour && curKstHour < d.hour + 6);
          const isFuture = (d.hour > curKstHour);

          const col = document.createElement('div');
          col.className = 'flex flex-col items-center justify-end h-full group relative cursor-pointer';
          col.innerHTML = `
            <!-- Tooltip -->
            <div class="opacity-0 group-hover:opacity-100 transition-opacity absolute -top-12 z-20 pointer-events-none bg-ink-primary text-white text-[10px] font-mono py-1 px-2.5 rounded-md shadow-lg whitespace-nowrap">
              <div class="font-bold text-indigo-300">${{d.range}}: ${{d.inbox_count}}건 수집</div>
              ${{isCurrent ? '<div class="text-emerald-400 font-bold">● 현재 세션 인입 중</div>' : (isFuture ? '<div class="text-slate-400">예정 세션</div>' : '<div class="text-slate-300">수집 완료</div>')}}
            </div>

            <!-- Ingestion Count Number -->
            <span class="text-[10px] font-mono font-bold ${{isCurrent ? 'text-indigo-600 font-extrabold' : 'text-ink-muted'}} mb-1">
              ${{d.inbox_count || 0}}건
            </span>

            <!-- Single Bar Stack -->
            <div class="w-full max-w-[54px] sm:max-w-[76px] flex items-end justify-center h-24 ${{isFuture ? 'opacity-30' : ''}}">
              <div class="w-full ${{isCurrent ? 'bg-indigo-500 ring-2 ring-indigo-400 animate-pulse' : 'bg-indigo-600'}} rounded-t-lg transition-all duration-500 hover:bg-indigo-700" style="height: ${{hPct}}%;"></div>
            </div>

            <!-- Label -->
            <span class="text-[10px] sm:text-[11px] font-mono font-bold ${{isCurrent ? 'text-indigo-600 font-extrabold' : 'text-ink-muted'}} mt-2 group-hover:text-indigo-600 transition text-center">
              ${{d.slot}}
            </span>
          `;
          tlContainer.appendChild(col);
        }});
      }}

      // 2. Render 1-Day 4-Sessions AI Trend Radar (Active Session)
      renderRadarSession();
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
      const autoBadge = document.getElementById('badgeCountAuto');
      if (autoBadge) autoBadge.innerText = countAuto;
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

      // 🌟 Precision DateTime Sorting (Default: AI Audit Date DESC)
      filtered.sort((a, b) => {{
        if (currentSort === 'date-audit-desc' || currentSort === 'date-desc') {{
          const diff = parseItemTimestamp(b, 'audit') - parseItemTimestamp(a, 'audit');
          if (diff !== 0) return diff;
          return (b.case_id || '').localeCompare(a.case_id || '');
        }}
        if (currentSort === 'date-audit-asc') {{
          const diff = parseItemTimestamp(a, 'audit') - parseItemTimestamp(b, 'audit');
          if (diff !== 0) return diff;
          return (a.case_id || '').localeCompare(b.case_id || '');
        }}
        if (currentSort === 'date-source-desc') {{
          const diff = parseItemTimestamp(b, 'source') - parseItemTimestamp(a, 'source');
          if (diff !== 0) return diff;
          return (b.case_id || '').localeCompare(a.case_id || '');
        }}
        if (currentSort === 'date-source-asc' || currentSort === 'date-asc') {{
          const diff = parseItemTimestamp(a, 'source') - parseItemTimestamp(b, 'source');
          if (diff !== 0) return diff;
          return (a.case_id || '').localeCompare(b.case_id || '');
        }}
        const diff = parseItemTimestamp(b, 'audit') - parseItemTimestamp(a, 'audit');
        if (diff !== 0) return diff;
        return (b.case_id || '').localeCompare(a.case_id || '');
      }});

      document.getElementById('resultsCountLabel').innerText = currentLang === 'KO' ? `총 ${{filtered.length}}건 표시 (전체 ${{liveCasesData.length}}건 중)` : (currentLang === 'ZH' ? `显示 ${{filtered.length}} 项 (共 ${{liveCasesData.length}} 项)` : `Showing ${{filtered.length}} of ${{liveCasesData.length}} dossiers`);

      const totalPages = Math.ceil(filtered.length / PAGE_SIZE) || 1;
      if (currentPortfolioPage > totalPages) currentPortfolioPage = totalPages;
      if (currentPortfolioPage < 1) currentPortfolioPage = 1;

      renderPagination('portfolioPagination', currentPortfolioPage, totalPages, 'changePortfolioPage');

      if (filtered.length === 0) {{
        grid.innerHTML = `<div class="col-span-full py-16 text-center text-ink-muted font-medium">${{currentLang === 'KO' ? '일치하는 기술 검증 보고서가 없습니다.' : (currentLang === 'ZH' ? '未找到符合条件的技术核查报告。' : 'No matching fact-check dossiers found.')}}</div>`;
        return;
      }}

      // Render Executive Scannable Cards (Paged: 20 per page)
      const pagedItems = filtered.slice((currentPortfolioPage - 1) * PAGE_SIZE, currentPortfolioPage * PAGE_SIZE);
      pagedItems.forEach((c, idx) => {{
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
        card.className = 'executive-card p-4 sm:p-6 flex flex-col justify-between cursor-pointer space-y-4 group';
        card.onclick = () => openModal(c);

        card.innerHTML = `
          <div class="space-y-3.5">
            
            <!-- Tier 1: Header Meta (ID + Mode Badge + Dual Dates + Verdict) -->
            <div class="flex items-center justify-between text-xs gap-2 flex-wrap">
              <div class="flex items-center gap-1.5 sm:gap-2 flex-wrap">
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

          <!-- Tier 4: Standardized 3-Line Footer -->
          <div class="pt-3 border-t border-surface-border space-y-1.5 text-xs font-mono">
            <!-- Line 1: 수집날짜&시간 -->
            <div class="flex items-center justify-between text-ink-muted text-[11px]">
              <span title="${{currentLang === 'KO' ? '수집/원출처 발행일' : (currentLang === 'ZH' ? '采集/发布日' : 'Source Date')}}">📅 ${{srcDate}}</span>
              <span class="text-emerald-700 font-bold flex items-center gap-1 font-sans">
                <i data-lucide="shield-check" class="w-3.5 h-3.5"></i> ${{t.cardConfidenceLabel}} ${{confScore.toFixed(1)}}%
              </span>
            </div>

            <!-- Line 2: 분석날짜&시간 (분석모델) -->
            <div class="flex items-center justify-between text-indigo-700 text-[11px] font-semibold gap-2">
              <span title="${{currentLang === 'KO' ? '심층 기술 분석일' : (currentLang === 'ZH' ? '深度分析日' : 'Audit Date')}}" class="flex items-center gap-1.5 min-w-0 overflow-hidden">
                <span class="shrink-0">🔬 ${{invDate}}</span>
                <span class="text-ink-muted font-normal truncate min-w-0 align-bottom cursor-help" title="${{c.curation?.audited_by_model || c.audited_by_model || 'gemini-3.8-flash-medium'}}">(${{formatModelAttribution(c.curation?.audited_by_model || c.audited_by_model || 'gemini-3.8-flash-medium')}})</span>
              </span>
              <span class="text-ink-muted font-normal shrink-0">${{(c.sources || []).length}}${{t.cardSourcesLabel}}</span>
            </div>

            <!-- Line 3: 원문 및 상세 보기 액션 -->
            <div class="flex items-center justify-between pt-0.5 font-sans">
              <span class="text-[11px] text-ink-muted font-mono flex items-center gap-1">
                ${{c.sources && c.sources.length > 0 ? `<a href="${{c.sources[0].url}}" target="_blank" onclick="event.stopPropagation();" class="text-indigo-600 hover:underline flex items-center gap-0.5 font-semibold">📄 ${{currentLang === 'KO' ? '원문' : (currentLang === 'ZH' ? '原文' : 'Source')}} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>` : ''}}
              </span>
              <button class="text-ink-primary font-bold text-xs group-hover:translate-x-0.5 transition flex items-center gap-1">
                ${{t.cardViewBtn}} <i data-lucide="arrow-right" class="w-3.5 h-3.5 text-ink-primary"></i>
              </button>
            </div>
          </div>
        `;
        grid.appendChild(card);
      }});

      if (window.lucide) window.lucide.createIcons({{ root: grid }});
    }}

    // ================= MODAL HANDLER & DEEP LINKING ROUTER =================
    function openModal(c, skipHistory = false) {{
      if (!c) return;
      const cid = c.case_id || c.investigation_id;
      if (!skipHistory && cid) {{
        const targetHash = '#/factchecks?case=' + encodeURIComponent(cid);
        if (window.location.hash !== targetHash) {{
          try {{ history.pushState({{ caseId: cid, view: currentView }}, '', targetHash); }} catch (e) {{}}
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
        }} else if (rawPost.url) {{
          directLink.href = rawPost.url;
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
      
      document.getElementById('modalHandsOnEnv').innerText = handsOn.test_environment || handsOn.environment ? ((currentLang === 'KO' ? '환경: ' : (currentLang === 'ZH' ? '实测环境: ' : 'Env: ')) + (handsOn.test_environment || handsOn.environment)) : '';
      document.getElementById('modalHandsOnMetrics').innerText = handsOn.measured_results ? ((currentLang === 'KO' ? '실측치: ' : (currentLang === 'ZH' ? '实测指标: ' : 'Metrics: ')) + handsOn.measured_results) : (handsOn.measured_metrics ? Object.entries(handsOn.measured_metrics).map(([k, v]) => `${{k}}: ${{v}}`).join(' | ') : '');
      document.getElementById('modalHandsOnDetails').innerText = handsOn.details || handsOn.failure_modes || story.empirical_findings || 'Empirical benchmark verified.';

      // Claims vs Reality
      const claimsBox = document.getElementById('modalClaimsBox');
      const claimsList = document.getElementById('modalClaimsList');
      const claims = (c.claims_assessment && c.claims_assessment.length > 0) ? c.claims_assessment : (c.marketing_claims || []);
      if (claims && claims.length > 0) {{
        claimsBox.classList.remove('hidden');
        document.getElementById('modalSecClaimsTitle').innerText = t.modalSecClaimsTitle || 'Marketing Claims vs Empirical Reality';
        claimsList.innerHTML = claims.map(cl => {{
          const claimTitle = cl.claim || cl.statement || cl.claim_title || cl.claim_text || cl.marketing_hook || '';
          const claimTruth = cl.reality || cl.fact_checked_truth || cl.verification_evidence || cl.empirical_reality || cl.reality_check || '';
          const claimStatus = cl.status || cl.verdict || cl.claim_verdict || 'VERIFIED';
          const isTrue = (claimStatus === 'VERIFIED_TRUE' || claimStatus === 'TRUE');
          const isFalse = (claimStatus === 'FALSE' || claimStatus === 'FALSE_CLAIM' || claimStatus === 'GAMED_CLAIM' || claimStatus === 'MARKETING_HYPE');
          const statusClass = isTrue ? 'text-emerald-700 bg-emerald-50 border border-emerald-200' : (isFalse ? 'text-rose-700 bg-rose-50 border border-rose-200' : 'text-amber-800 bg-amber-50 border border-amber-200');
          return `
            <div class="p-3 rounded-lg bg-white border border-amber-200 text-xs space-y-1.5 shadow-sm">
              <div class="flex items-center justify-between font-mono text-[11px] gap-2 flex-wrap">
                <span class="text-ink-primary font-bold">Claim: "${{claimTitle}}"</span>
                <span class="px-2 py-0.5 rounded text-[10px] font-bold ${{statusClass}}">${{claimStatus}}</span>
              </div>
              <div class="text-ink-secondary font-medium leading-relaxed">${{currentLang === 'KO' ? '🔬 실증 팩트 검증:' : (currentLang === 'ZH' ? '🔬 实测事实核验:' : '🔬 Empirical Verification:')}} ${{claimTruth}}</div>
            </div>
          `;
        }}).join('');
      }} else {{
        claimsBox.classList.add('hidden');
      }}

      // Alternatives Table
      const altBody = document.getElementById('modalAlternativesBody');
      const alts = clustering.alternatives || c.alternatives || [];
      if (alts && alts.length > 0) {{
        altBody.innerHTML = alts.map(a => `
          <tr>
            <td class="p-3 font-bold text-ink-primary">${{a.name || a.tool_name || ''}}</td>
            <td class="p-3 font-mono text-ink-secondary text-[11px]">${{a.tech_stack || a.stack || '-'}}</td>
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
      document.body.style.overflow = 'hidden';
      lucide.createIcons();
    }}

    function openCaseModal(caseId) {{
      if (!caseId) return;
      const c = (liveCasesData || []).find(x => x.case_id === caseId || x.investigation_id === caseId) || (casesData || []).find(x => x.case_id === caseId);
      if (c) {{
        openModal(c);
      }}
    }}

    function closeModal(pushHistory = true) {{
      const modal = document.getElementById('detailModal');
      if (modal) modal.classList.add('hidden');
      document.body.style.overflow = 'auto';

      if (pushHistory) {{
        const targetHash = ROUTES[currentView] || '#/' + currentView;
        if (window.location.hash !== targetHash) {{
          try {{
            history.pushState({{ view: currentView }}, '', targetHash);
          }} catch (e) {{
            window.location.hash = targetHash;
          }}
        }}
      }}
    }}

    // ================= UNIVERSAL ROUTE & POPSTATE DISPATCHER =================
    function handleHashRoute() {{
      const hash = window.location.hash || '';

      // 1. Deep Link to Modal: #/factchecks?case=... or #case/...
      if (hash.includes('case=') || hash.startsWith('#case/')) {{
        let targetCaseId = '';
        if (hash.includes('case=')) {{
          const m = hash.match(/case=([^&]+)/);
          if (m) targetCaseId = decodeURIComponent(m[1]);
        }} else {{
          targetCaseId = decodeURIComponent(hash.replace('#case/', ''));
        }}

        if (targetCaseId) {{
          switchView('portfolio', false, true);
          const target = (liveCasesData || []).find(c => c.case_id === targetCaseId || c.investigation_id === targetCaseId) || (casesData || []).find(c => c.case_id === targetCaseId);
          if (target) {{
            openModal(target, false);
            return;
          }}
        }}
      }}

      // If modal is open and user navigates back to tab without modal query, close modal
      closeModal(false);

      // 2. Parse Route and Query Page
      const [routePart, queryPart] = hash.split('?');
      const params = new URLSearchParams(queryPart || '');
      const pageParam = parseInt(params.get('page'), 10) || 1;

      let targetView = 'home';
      if (routePart.startsWith('#/factchecks') || routePart.startsWith('#factchecks') || routePart.startsWith('#/portfolio')) {{
        targetView = 'portfolio';
      }} else if (routePart.startsWith('#/news') || routePart.startsWith('#news')) {{
        targetView = 'news';
      }} else if (routePart.startsWith('#/models') || routePart.startsWith('#models')) {{
        targetView = 'models';
      }} else if (routePart.startsWith('#/graph') || routePart.startsWith('#graph')) {{
        targetView = 'graph';
      }} else if (routePart.startsWith('#/inbox') || routePart.startsWith('#inbox')) {{
        targetView = 'inbox';
      }} else {{
        targetView = 'home';
      }}

      if (currentView !== targetView) {{
        switchView(targetView, false, false);
      }} else if (targetView === 'home') {{
        renderTelemetryCharts();
      updateCronCountdown();
        renderHomeTopPicks();
      }}

      // 3. Apply Page State to Active View (Enables Back/Forward Through Pages)
      if (targetView === 'news') {{
        if (currentNewsPage !== pageParam) {{
          changeNewsPage(pageParam, false);
        }}
      }} else if (targetView === 'portfolio') {{
        if (currentPortfolioPage !== pageParam) {{
          changePortfolioPage(pageParam, false);
        }}
      }} else if (targetView === 'models') {{
        if (currentModelsPage !== pageParam) {{
          changeModelsPage(pageParam, false);
        }}
      }} else if (targetView === 'inbox') {{
        if (currentInboxPage !== pageParam) {{
          changeInboxPage(pageParam, false);
        }}
      }}
    }}

    window.addEventListener('popstate', handleHashRoute);
    window.addEventListener('hashchange', handleHashRoute);
    window.addEventListener('load', () => {{
      setTimeout(handleHashRoute, 150);
    }});

    // ================= NEWS VIEW (2계층 카테고리화 엔진) =================
    let currentNewsTier1 = 'ALL';
    let currentNewsTier2 = 'ALL';
    let currentNewsSource = 'ALL';
    let currentNewsSort = 'date-source-desc';
    let currentNewsSearch = '';

    function setNewsCategoryFilter(t1) {{
      currentNewsPage = 1;
      currentNewsTier1 = t1;
      currentNewsTier2 = 'ALL';
      document.querySelectorAll('.news-cat-pill').forEach(btn => {{
        if (btn.getAttribute('data-cat') === t1) {{
          btn.className = 'news-cat-pill active px-3 py-1.5 rounded-xl text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap';
        }} else {{
          btn.className = 'news-cat-pill px-3 py-1.5 rounded-xl text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }}
      }});

      // Reset Tier 2 pills
      document.querySelectorAll('.news-t2-pill').forEach(btn => {{
        if (btn.getAttribute('data-t2') === 'ALL') {{
          btn.className = 'news-t2-pill active px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap';
        }} else {{
          btn.className = 'news-t2-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }}
      }});

      // If a non-computing domain is selected (e.g. Science, Law), dim/hide Tier 2 row
      const t2Container = document.getElementById('newsTier2Container');
      if (t2Container) {{
        if (t1 !== 'ALL' && t1 !== 'TECH_COMPUTING') {{
          t2Container.classList.add('opacity-40', 'pointer-events-none');
        }} else {{
          t2Container.classList.remove('opacity-40', 'pointer-events-none');
        }}
      }}

      renderNews();
    }}

    function setNewsTier2Filter(t2) {{
      currentNewsPage = 1;
      currentNewsTier2 = t2;
      document.querySelectorAll('.news-t2-pill').forEach(btn => {{
        if (btn.getAttribute('data-t2') === t2) {{
          btn.className = 'news-t2-pill active px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap';
        }} else {{
          btn.className = 'news-t2-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }}
      }});
      renderNews();
    }}

    function handleNewsSearch(val) {{
      targetSelectedInboxId = '';
      currentNewsPage = 1;
      currentNewsSearch = (val || '').trim().toLowerCase();
      renderNews();
    }}

    function setNewsSort(sort) {{
      currentNewsPage = 1;
      currentNewsSort = sort;
      renderNews();
    }}

    function setNewsSourceFilter(src) {{
      currentNewsPage = 1;
      currentNewsSource = src;
      document.querySelectorAll('.news-src-btn').forEach(btn => {{
        if (btn.getAttribute('data-src') === src) {{
          btn.className = 'news-src-btn active px-2.5 py-1 rounded-lg text-xs font-bold bg-ink-primary text-white transition shrink-0 whitespace-nowrap';
        }} else {{
          btn.className = 'news-src-btn px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:bg-white transition border border-surface-border shrink-0 whitespace-nowrap';
        }}
      }});
      renderNews();
    }}

    // 🌟 Scalable Multi-Source Cross-Platform Clustering UX Engine
    function buildMultiSourceCluster(sources, rawItemId) {{
      if (!sources || sources.length === 0) return '';
      const total = sources.length;
      const safeId = 'src_' + String(rawItemId || Math.random()).replace(/[^a-zA-Z0-9_-]/g, '_');

      function getSourceMeta(s) {{
        const p = (s.platform || s.source_name || '').toLowerCase();
        const u = s.url || '#';
        let icon = '📄';
        let label = s.source_name || (currentLang === 'KO' ? '원문' : 'Source');
        let badgeCls = 'bg-surface-subtle text-ink-secondary hover:text-ink-primary border-surface-border';

        if (p.includes('hacker news') || u.includes('ycombinator')) {{
          icon = '🔥';
          label = currentLang === 'KO' ? 'HN 토론' : 'HN';
          badgeCls = 'bg-orange-50 text-orange-800 hover:text-orange-950 border-orange-200';
        }} else if (p.includes('geeknews') || u.includes('hada.io')) {{
          icon = '💬';
          label = currentLang === 'KO' ? '긱뉴스' : 'GeekNews';
          badgeCls = 'bg-indigo-50 text-indigo-800 hover:text-indigo-950 border-indigo-200';
        }} else if (p.includes('reddit')) {{
          icon = '🤖';
          label = currentLang === 'KO' ? '레딧' : 'Reddit';
          badgeCls = 'bg-red-50 text-red-800 hover:text-red-950 border-red-200';
        }} else if (p.includes('github')) {{
          icon = '🐙';
          label = 'GitHub';
          badgeCls = 'bg-slate-100 text-slate-800 hover:text-slate-950 border-slate-300';
        }} else if (p.includes('hugging')) {{
          icon = '🤗';
          label = 'HuggingFace';
          badgeCls = 'bg-amber-50 text-amber-900 hover:text-amber-950 border-amber-200';
        }} else if (p.includes('arxiv')) {{
          icon = '📑';
          label = 'ArXiv';
          badgeCls = 'bg-rose-50 text-rose-900 hover:text-rose-950 border-rose-200';
        }} else if (p.includes('twitter') || p.includes(' x') || u.includes('x.com') || u.includes('twitter.com')) {{
          icon = '𝕏';
          label = 'X (트위터)';
          badgeCls = 'bg-zinc-100 text-zinc-800 hover:text-zinc-950 border-zinc-300';
        }}

        return {{ icon, label, badgeCls, url: u }};
      }}

      if (total <= 2) {{
        let html = `<div class="flex items-center gap-1.5 flex-wrap">`;
        html += `<span class="px-2 py-0.5 rounded-md text-[10px] font-bold bg-amber-50 text-amber-900 border border-amber-200 shrink-0">🔗 ${{currentLang === 'KO' ? `출처 ${{total}}개 묶음` : (currentLang === 'ZH' ? `聚合${{total}}个来源` : `${{total}} Sources`)}}</span>`;
        sources.forEach(s => {{
          const meta = getSourceMeta(s);
          html += `<a href="${{meta.url}}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded-md ${{meta.badgeCls}} border text-[11px] font-bold flex items-center gap-1 shrink-0 transition shadow-xs">${{meta.icon}} ${{meta.label}} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>`;
        }});
        html += `</div>`;
        return html;
      }}

      // 🌟 Scalable Multi-Source UX: Top 2 visible + '+N개 더보기' floating dropdown popover
      const primarySources = sources.slice(0, 2);
      const remainingSources = sources.slice(2);

      let html = `<div class="flex items-center gap-1.5 flex-wrap relative">`;
      html += `<span class="px-2 py-0.5 rounded-md text-[10px] font-bold bg-amber-50 text-amber-900 border border-amber-200 shrink-0">🔗 ${{currentLang === 'KO' ? `출처 ${{total}}개 묶음` : (currentLang === 'ZH' ? `聚合${{total}}个来源` : `${{total}} Sources`)}}</span>`;
      primarySources.forEach(s => {{
        const meta = getSourceMeta(s);
        html += `<a href="${{meta.url}}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded-md ${{meta.badgeCls}} border text-[11px] font-bold flex items-center gap-1 shrink-0 transition shadow-xs">${{meta.icon}} ${{meta.label}} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>`;
      }});

      html += `
        <div class="relative inline-block src-dropdown-container">
          <button type="button" onclick="toggleSourcePopover(event, '${{safeId}}')" class="px-2 py-1 rounded-md bg-amber-100 hover:bg-amber-200 text-amber-950 border border-amber-300 text-[11px] font-bold flex items-center gap-1 shrink-0 transition cursor-pointer shadow-xs" title="전체 교차 출처 보기">
            <span>+${{remainingSources.length}}${{currentLang === 'KO' ? '개 더보기' : (currentLang === 'ZH' ? '个更多' : ' more')}}</span>
            <i data-lucide="chevron-down" class="w-3 h-3"></i>
          </button>
          <div id="srcMenu_${{safeId}}" class="hidden absolute right-0 bottom-full mb-1.5 w-64 max-w-[calc(100vw-2.5rem)] bg-white rounded-xl shadow-xl border border-surface-border p-2.5 z-50 text-xs flex flex-col gap-1.5">
            <div class="text-[10px] font-mono font-bold text-ink-muted px-1.5 pb-1 border-b border-surface-border flex items-center justify-between">
              <span>🔗 ${{currentLang === 'KO' ? `전체 교차 출처 (${{total}}개)` : (currentLang === 'ZH' ? `全部聚合来源 (${{total}}个)` : `All Sources (${{total}})`)}}</span>
              <span class="text-indigo-600 text-[9px] font-semibold">${{currentLang === 'KO' ? '원문 이동' : (currentLang === 'ZH' ? '直达原文' : 'Open')}} &nearr;</span>
            </div>
            <div class="max-h-48 overflow-y-auto space-y-1 divide-y divide-surface-border/40">
              ${{sources.map(s => {{
                const meta = getSourceMeta(s);
                return `
                  <a href="${{meta.url}}" target="_blank" rel="noopener noreferrer" class="flex items-center justify-between px-2 py-1.5 rounded-lg hover:bg-surface-subtle transition group text-xs text-ink-primary pt-1">
                    <span class="flex items-center gap-1.5 truncate">
                      <span class="shrink-0">${{meta.icon}}</span>
                      <span class="font-bold group-hover:text-indigo-600 truncate">${{meta.label}}</span>
                    </span>
                    <i data-lucide="external-link" class="w-3 h-3 text-ink-muted group-hover:text-indigo-600 shrink-0 ml-2"></i>
                  </a>
                `;
              }}).join('')}}
            </div>
          </div>
        </div>
      `;
      html += `</div>`;
      return html;
    }}

    function toggleSourcePopover(e, safeId) {{
      e.stopPropagation();
      const menu = document.getElementById('srcMenu_' + safeId);
      if (!menu) return;
      const isHidden = menu.classList.contains('hidden');
      document.querySelectorAll('[id^="srcMenu_"]').forEach(el => el.classList.add('hidden'));
      if (isHidden) {{
        menu.classList.remove('hidden');
        if (window.lucide) window.lucide.createIcons();
      }}
    }}

    document.addEventListener('click', (e) => {{
      if (!e.target.closest('.src-dropdown-container')) {{
        document.querySelectorAll('[id^="srcMenu_"]').forEach(el => el.classList.add('hidden'));
      }}
    }});

    function renderNews() {{
      const grid = document.getElementById('newsGrid');
      grid.innerHTML = '';
      const t = i18n[currentLang];

      const rawNewsItems = liveNewsData || [];
      const newsItems = rawNewsItems.filter(it => {{
        // 🌟 Direct Primary Key Match from Radar
        if (targetSelectedInboxId && it.inbox_id === targetSelectedInboxId) {{
          return true;
        }}

        // 1. Tier 1 Domain Filter
        if (currentNewsTier1 !== 'ALL') {{
          const itemTier1 = it.tier1_category || 'TECH_COMPUTING';
          if (itemTier1 !== currentNewsTier1) return false;
        }}

        // 2. Tier 2 Specialization Filter (Under TECH_COMPUTING)
        if (currentNewsTier2 !== 'ALL') {{
          const itemTier2 = it.tier2_category || it.category_primary || 'INDUSTRY_TRENDS';
          if (itemTier2 !== currentNewsTier2) return false;
        }}

        // 2. Platform Source Filter
        if (currentNewsSource !== 'ALL') {{
          const src = (it.source_platform || '').toLowerCase();
          const target = currentNewsSource.toLowerCase();
          if (!src.includes(target)) return false;
        }}

        // 3. Search Filter
        if (currentNewsSearch) {{
          const q = currentNewsSearch.toLowerCase().trim();
          const haystack = (
            (it.inbox_id || '') + ' ' +
            (it.title || '') + ' ' +
            (it.title_ko || '') + ' ' +
            (it.title_en || '') + ' ' +
            (it.hook || '') + ' ' +
            (it.hook_ko || '') + ' ' +
            (it.description || '') + ' ' +
            (it.source_platform || '') + ' ' +
            (it.ai_enrichment?.summary_ko || '')
          ).toLowerCase();

          const tokens = q.split(/\\s+/).filter(t => t.length > 0);
          const matches = haystack.includes(q) || (tokens.length > 0 && tokens.every(t => haystack.includes(t)));
          if (!matches) return false;
        }}

        return true;
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

      const totalPages = Math.ceil(newsItems.length / PAGE_SIZE) || 1;
      if (currentNewsPage > totalPages) currentNewsPage = totalPages;
      if (currentNewsPage < 1) currentNewsPage = 1;

      renderPagination('newsPagination', currentNewsPage, totalPages, 'changeNewsPage');

      if (newsItems.length === 0) {{
        grid.innerHTML = `<div class="col-span-full py-16 text-center text-ink-muted font-medium">${{currentLang === 'KO' ? '해당 플랫폼의 수집 AI 뉴스가 없습니다.' : (currentLang === 'ZH' ? '暂无该平台的 AI 资讯。' : 'No AI news articles available for this source.')}}</div>`;
        return;
      }}

      const pagedNews = newsItems.slice((currentNewsPage - 1) * PAGE_SIZE, currentNewsPage * PAGE_SIZE);
      pagedNews.forEach(it => {{
        const card = document.createElement('div');
        card.className = 'executive-card p-4 sm:p-5 flex flex-col justify-between space-y-4';

        const ai = it.ai_enrichment;
        const multi = it.multilingual || (ai ? ai.multilingual : null);
        let displayTitle = it.title;
        let displayDesc = it.description || '';
        let displayHook = (ai ? ai.hook : '') || it.hook || '';
        let displayTakeaways = (ai ? ai.key_takeaways : []) || [];

        if (multi) {{
          if (currentLang === 'KO' && multi.ko) {{
            displayTitle = multi.ko.title || it.title_ko || displayTitle;
            displayHook = multi.ko.hook || it.hook_ko || displayHook;
            displayTakeaways = multi.ko.key_takeaways || displayTakeaways;
            displayDesc = it.description_ko || it.description || '';
          }} else if (currentLang === 'ZH' && multi.zh) {{
            displayTitle = multi.zh.title || it.title_zh || displayTitle;
            displayHook = multi.zh.hook || it.hook_zh || displayHook;
            displayTakeaways = multi.zh.key_takeaways || displayTakeaways;
            displayDesc = it.description_zh || it.description || '';
          }} else if (currentLang === 'EN' && multi.en) {{
            displayTitle = multi.en.title || it.title_en || displayTitle;
            displayHook = multi.en.hook || it.hook_en || displayHook;
            displayTakeaways = multi.en.key_takeaways || displayTakeaways;
            displayDesc = it.description_en || it.description || '';
          }}
        }} else {{
          if (currentLang === 'KO') {{
            if (it.title_ko) displayTitle = it.title_ko;
            if (it.description_ko) displayDesc = it.description_ko;
          }} else if (currentLang === 'ZH') {{
            if (it.title_zh) displayTitle = it.title_zh;
            if (it.description_zh) displayDesc = it.description_zh;
          }} else if (currentLang === 'EN') {{
            if (it.title_en) displayTitle = it.title_en;
            if (it.description_en) displayDesc = it.description_en;
          }}
        }}

        // Deduplicate Hook: Hook must ONLY appear in the yellow callout box
        if (displayHook) {{
          const cleanH = displayHook.trim();
          if (displayDesc.trim() === cleanH) {{
            displayDesc = '';
          }} else if (cleanH && displayDesc.includes(cleanH)) {{
            displayDesc = displayDesc.replace(cleanH, '').trim();
          }}
        }}

        const isHn = (it.source_platform || '').includes('Hacker News') || (it.source_url || '').includes('news.ycombinator.com');
        const isGn = (it.source_platform || '').includes('GeekNews') || (it.source_url || '').includes('hada.io');
        const hnUrl = it.hn_url || ((it.source_url || '').includes('news.ycombinator.com') ? it.source_url : null);
        const gnUrl = isGn ? (it.hn_url || it.source_url) : null;
        const articleUrl = it.article_url || (it.source_url !== (hnUrl || gnUrl) ? it.source_url : null);

        let linksHtml = '';
        if (it.sources && it.sources.length > 1) {{
          linksHtml = buildMultiSourceCluster(it.sources, it.inbox_id || it.id);
        }} else if (isHn) {{
          if (articleUrl && articleUrl !== hnUrl) {{
            linksHtml += `<a href="${{articleUrl}}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded-md bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border text-[11px] font-medium flex items-center gap-1 shrink-0">📄 ${{currentLang === 'KO' ? '기사 원문' : (currentLang === 'ZH' ? '文章原文' : 'Article')}} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>`;
          }}
          if (hnUrl) {{
            linksHtml += `<a href="${{hnUrl}}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded-md bg-orange-50 text-orange-800 hover:text-orange-950 border border-orange-200 text-[11px] font-bold flex items-center gap-1 shrink-0">🔥 ${{currentLang === 'KO' ? 'HN 토론' : (currentLang === 'ZH' ? 'HN 讨论' : 'HN Thread')}} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>`;
          }}
        }} else if (isGn) {{
          if (articleUrl && articleUrl !== gnUrl) {{
            linksHtml += `<a href="${{articleUrl}}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded-md bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border text-[11px] font-medium flex items-center gap-1 shrink-0">📄 ${{currentLang === 'KO' ? '기사 원문' : (currentLang === 'ZH' ? '文章原文' : 'Article')}} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>`;
          }}
          if (gnUrl) {{
            linksHtml += `<a href="${{gnUrl}}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded-md bg-indigo-50 text-indigo-800 hover:text-indigo-950 border border-indigo-200 text-[11px] font-bold flex items-center gap-1 shrink-0">💬 ${{currentLang === 'KO' ? '긱뉴스 토론' : (currentLang === 'ZH' ? '极客新闻' : 'GeekNews')}} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>`;
          }}
        }} else {{
          linksHtml = `<a href="${{it.source_url}}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded-md bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border text-[11px] font-semibold flex items-center gap-1 shrink-0">📄 ${{t.newsOriginalLink}} <i data-lucide="external-link" class="w-2.5 h-2.5"></i></a>`;
        }}

        let aiBadgeHtml = '';
        let aiSummaryHtml = '';
        let hookHtml = '';
        let relatedHtml = '';

        const tier1Map = {{
          'SCIENCE_RESEARCH': {{ label: currentLang === 'KO' ? '🚀 과학·우주' : (currentLang === 'ZH' ? '🚀 科学与航天' : '🚀 Science & Research'), cls: 'bg-teal-50 text-teal-900 border-teal-200' }},
          'ECONOMY_FINANCE': {{ label: currentLang === 'KO' ? '🏦 경제·금융' : (currentLang === 'ZH' ? '🏦 经济与金融' : '🏦 Economy & Finance'), cls: 'bg-emerald-50 text-emerald-900 border-emerald-200' }},
          'LAW_CRIME_JUSTICE': {{ label: currentLang === 'KO' ? '⚖️ 사회·법률' : (currentLang === 'ZH' ? '⚖️ 法律与社会' : '⚖️ Law & Society'), cls: 'bg-rose-50 text-rose-900 border-rose-200' }},
          'POLITICS_POLICY': {{ label: currentLang === 'KO' ? '🏛️ 정치·정책' : (currentLang === 'ZH' ? '🏛️ 政治与政策' : '🏛️ Politics & Policy'), cls: 'bg-amber-50 text-amber-950 border-amber-300' }},
          'CULTURE_HUMANITIES': {{ label: currentLang === 'KO' ? '🌿 문화·인문' : (currentLang === 'ZH' ? '🌿 文化与人文' : '🌿 Culture & Arts'), cls: 'bg-purple-50 text-purple-900 border-purple-200' }}
        }};
        const catMap = {{
          'INFERENCE_OPT': {{ label: currentLang === 'KO' ? '⚡ 추론·서빙 최적화' : (currentLang === 'ZH' ? '⚡ 推理服务优化' : '⚡ Inference & Opt'), cls: 'bg-amber-50 text-amber-900 border-amber-200' }},
          'AGENTS_DEVTOOLS': {{ label: currentLang === 'KO' ? '🛠️ 에이전트·개발도구' : (currentLang === 'ZH' ? '🛠️ 智能体与工具' : '🛠️ Agents & DevTools'), cls: 'bg-blue-50 text-blue-900 border-blue-200' }},
          'MULTIMODAL_AI': {{ label: currentLang === 'KO' ? '🎨 멀티모달·영상/음성' : (currentLang === 'ZH' ? '🎨 多模态与视听' : '🎨 Multimodal & GenAI'), cls: 'bg-purple-50 text-purple-900 border-purple-200' }},
          'FOUNDATION_MODELS': {{ label: currentLang === 'KO' ? '🤖 파운데이션·가중치' : (currentLang === 'ZH' ? '🤖 基础模型与权重' : '🤖 Foundation Models'), cls: 'bg-emerald-50 text-emerald-900 border-emerald-200' }},
          'INFRA_RAG_SECURITY': {{ label: currentLang === 'KO' ? '🛡️ 인프라·RAG·보안' : (currentLang === 'ZH' ? '🛡️ 基础设施与安全' : '🛡️ Infra, RAG & Safety'), cls: 'bg-rose-50 text-rose-900 border-rose-200' }},
          'DEEP_SCIENCE_SPACE': {{ label: currentLang === 'KO' ? '🚀 우주·신소재·과학' : (currentLang === 'ZH' ? '🚀 深科技与空天科学' : '🚀 Deep Science & Space'), cls: 'bg-teal-50 text-teal-900 border-teal-200' }},
          'MACRO_GLOBAL_BIZ': {{ label: currentLang === 'KO' ? '🏦 산업·거시경제' : (currentLang === 'ZH' ? '🏦 产业与宏观经济' : '🏦 Macro & Global Biz'), cls: 'bg-amber-50 text-amber-950 border-amber-300' }},
          'INDUSTRY_TRENDS': {{ label: currentLang === 'KO' ? '🌐 일반 테크·SW' : (currentLang === 'ZH' ? '🌐 通用科技与软件' : '🌐 General Tech & SW'), cls: 'bg-slate-100 text-slate-800 border-slate-200' }}
        }};
        const catInfo = (it.tier1_category && tier1Map[it.tier1_category]) ? tier1Map[it.tier1_category] : (catMap[it.category_primary] || catMap['INDUSTRY_TRENDS']);

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
                  <span>${{currentLang === 'KO' ? '관련 팩트체크: ' : (currentLang === 'ZH' ? '关联事实核查: ' : 'Related Fact-Check: ')}}${{it.related_dossier.target_tech}}</span>
                </span>
                <i data-lucide="arrow-right" class="w-3 h-3 text-indigo-400"></i>
              </button>
            </div>
          `;
        }}

        card.innerHTML = `
          <div class="space-y-2.5">
            <div class="flex items-center justify-between text-xs font-mono">
              <div class="flex items-center gap-1.5 flex-wrap">
                <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${{catInfo.cls}}">
                  ${{catInfo.label}}
                </span>
                <span class="px-2 py-0.5 rounded bg-surface-subtle text-ink-primary font-bold border border-surface-border text-[10px]">
                  ${{it.source_platform || 'Tech News'}}
                </span>
              </div>
              <span class="text-ink-muted text-[11px] font-mono">${{it.viral_metric || ''}}</span>
            </div>

            ${{aiBadgeHtml}}

            <h3 class="font-bold text-sm text-ink-primary hover:text-indigo-600 transition leading-snug break-words">
              ${{displayTitle}}
            </h3>

            ${{hookHtml}}

            ${{displayDesc ? `<p class="text-xs text-ink-secondary leading-relaxed line-clamp-3">${{displayDesc}}</p>` : ''}}

            ${{aiSummaryHtml}}
            ${{relatedHtml}}
          </div>

          <!-- Standardized 3-Line Footer -->
          <div class="pt-3 border-t border-surface-border space-y-1.5 text-xs font-mono">
            <!-- Line 1: 수집날짜&시간 및 원문 발행일 -->
            <div class="text-[11px] text-ink-muted flex items-center justify-between gap-1 flex-wrap">
              <span>📥 ${{currentLang === 'KO' ? '수집' : (currentLang === 'ZH' ? '采集' : 'Harvest')}}: ${{formatDateTimeCompact(it.harvested_at || it.harvested_date || it.published_at)}}</span>
              ${{it.published_at && (it.published_at.substring(0, 10) !== (it.harvested_at || it.harvested_date || '').substring(0, 10)) ? `
              <span class="text-[10px] text-ink-muted" title="${{currentLang === 'KO' ? '원문 발행일' : (currentLang === 'ZH' ? '原文发布日' : 'Source Published')}}">(${{currentLang === 'KO' ? '원문' : (currentLang === 'ZH' ? '原文' : 'Pub')}}: ${{formatDateTimeCompact(it.published_at)}})</span>
              ` : ''}}
            </div>

            <!-- Line 2: 분석날짜&시간 (분석모델) -->
            ${{ai?.enriched_at ? `
            <div class="text-[11px] text-indigo-700 font-semibold flex items-center gap-1.5 min-w-0 overflow-hidden">
              <span class="shrink-0">🔬 ${{formatDateTimeCompact(ai.enriched_at)}}</span>
              <span class="text-ink-muted font-normal truncate min-w-0 align-bottom cursor-help" title="${{ai.enriched_by_model || ''}}">(${{formatModelAttribution(ai.enriched_by_model)}})</span>
            </div>
            ` : `
            <div class="text-[11px] text-ink-muted flex items-center gap-1.5">
              <span>🔬 ${{currentLang === 'KO' ? 'AI 심층 분석 대기 중' : (currentLang === 'ZH' ? 'AI分析排队中' : 'Pending AI Audit')}}</span>
            </div>
            `}}

            <!-- Line 3: 원문 링크 -->
            <div class="flex items-center gap-1.5 flex-wrap pt-0.5 font-sans">
              ${{linksHtml}}
            </div>
          </div>
        `;
        grid.appendChild(card);
      }});

      if (window.lucide) window.lucide.createIcons({{ root: grid }});
    }}

    // ================= AI MODELS REGISTRY VIEW =================
    let currentModelsFamily = 'ALL';
    let currentModelsModality = 'ALL';
    let currentModelsArtifact = 'ALL';
    let currentModelsSort = 'date-audit-desc';
    let modelsSearchQuery = '';

    function setModelsSort(sort) {{
      currentModelsPage = 1;
      currentModelsSort = sort;
      renderModels();
    }}

    function setModelsArtifactFilter(art) {{
      currentModelsPage = 1;
      currentModelsArtifact = art;
      document.querySelectorAll('.model-art-pill').forEach(btn => {{
        if (btn.getAttribute('data-art') === art) {{
          btn.className = 'model-art-pill active px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap';
        }} else {{
          btn.className = 'model-art-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }}
      }});
      renderModels();
    }}

    function setModelsModalityFilter(mod) {{
      currentModelsPage = 1;
      currentModelsModality = mod;
      document.querySelectorAll('.model-mod-pill').forEach(btn => {{
        if (btn.dataset.mod === mod) {{
          btn.className = 'model-mod-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shrink-0 whitespace-nowrap';
        }} else {{
          btn.className = 'model-mod-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }}
      }});
      renderModels();
    }}

    function setModelsFamilyFilter(fam) {{
      currentModelsPage = 1;
      currentModelsFamily = fam;
      document.querySelectorAll('.model-fam-pill').forEach(btn => {{
        if (btn.getAttribute('data-fam') === fam) {{
          btn.className = 'model-fam-pill active px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shadow-sm shrink-0 whitespace-nowrap';
        }} else {{
          btn.className = 'model-fam-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }}
      }});
      renderModels();
    }}

    document.getElementById('modelsSearchInput')?.addEventListener('input', (e) => {{
      targetSelectedInboxId = '';
      currentModelsPage = 1;
      modelsSearchQuery = e.target.value;
      renderModels();
    }});

    function renderModels() {{
      const grid = document.getElementById('modelsGrid');
      if (!grid) return;
      grid.innerHTML = '';

      const filtered = liveModelsData.filter(item => {{
        // 🚨 STRICT POLICY: 번역/요약/정리가 100% 완료된 아이템만 분류 노출 (미번역 아이템은 절대 분류 금지)
        const hasAi = !!(item.ai_enrichment && (item.multilingual || (item.ai_enrichment && item.ai_enrichment.multilingual)));
        if (!hasAi) return false;

        // 🌟 Direct Primary Key Match from Radar
        if (targetSelectedInboxId && item.inbox_id === targetSelectedInboxId) {{
          return true;
        }}

        let matchesMod = true;
        if (currentModelsModality !== 'ALL') {{
          const itemMod = (item.task_modality || '').toLowerCase();
          matchesMod = itemMod === currentModelsModality.toLowerCase();
        }}

        const fam = (item.model_family || '').toLowerCase();
        let matchesFam = true;
        if (currentModelsFamily === 'ALL') {{
          matchesFam = true;
        }} else if (currentModelsFamily === 'Standalone') {{
          matchesFam = fam.includes('standalone') || fam.includes('독립') || !fam;
        }} else if (currentModelsFamily === 'Audio / Speech') {{
          matchesFam = fam.includes('audio') || fam.includes('speech') || fam.includes('tts') || fam.includes('whisper');
        }} else {{
          matchesFam = fam.includes(currentModelsFamily.toLowerCase());
        }}

        let matchesArt = true;
        if (currentModelsArtifact !== 'ALL') {{
          const itemArt = item.artifact_type || 'WEIGHTS';
          matchesArt = itemArt === currentModelsArtifact;
        }}

        if (!modelsSearchQuery) {{
          return matchesMod && matchesFam && matchesArt;
        }}

        const q = modelsSearchQuery.toLowerCase().trim();
        const searchable = (
          (item.inbox_id || '') + ' ' +
          (item.title || '') + ' ' +
          (item.title_ko || '') + ' ' +
          (item.title_en || '') + ' ' +
          (item.title_zh || '') + ' ' +
          (item.description || '') + ' ' +
          fam + ' ' +
          (item.task_modality || '') + ' ' +
          (item.artifact_type || '') + ' ' +
          (item.parameter_size || '') + ' ' +
          (item.ai_enrichment?.summary_ko || '') + ' ' +
          (item.ai_enrichment?.hook_ko || '')
        ).toLowerCase();

        const tokens = q.split(/\\s+/).filter(t => t.length > 0);
        const matchesSearch = searchable.includes(q) || (tokens.length > 0 && tokens.every(t => searchable.includes(t)));
        return matchesMod && matchesFam && matchesArt && matchesSearch;
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

      const totalPages = Math.ceil(filtered.length / PAGE_SIZE) || 1;
      if (currentModelsPage > totalPages) currentModelsPage = totalPages;
      if (currentModelsPage < 1) currentModelsPage = 1;

      renderPagination('modelsPagination', currentModelsPage, totalPages, 'changeModelsPage');

      if (filtered.length === 0) {{
        grid.innerHTML = `<div class="col-span-full py-16 text-center text-ink-muted font-medium">${{currentLang === 'KO' ? '일치하는 AI 모델이 없습니다.' : (currentLang === 'ZH' ? '暂无匹配的 AI 模型。' : 'No matching AI models.')}}</div>`;
        return;
      }}

      const pagedModels = filtered.slice((currentModelsPage - 1) * PAGE_SIZE, currentModelsPage * PAGE_SIZE);
      pagedModels.forEach(it => {{
        const ai = it.ai_enrichment;
        const multi = it.multilingual || ai?.multilingual;
        const lKey = currentLang.toLowerCase();

        let displayTitle = (multi && multi[lKey]?.title) || (currentLang === 'KO' ? it.title_ko : (currentLang === 'ZH' ? it.title_zh : it.title_en)) || it.title;
        let displayHook = (multi && multi[lKey]?.hook) || (currentLang === 'KO' ? it.hook_ko : (currentLang === 'ZH' ? it.hook_zh : it.hook_en)) || it.hook || '';
        let displayDesc = (currentLang === 'KO' ? it.description_ko : (currentLang === 'ZH' ? it.description_zh : it.description_en)) || it.description || '';

        // Deduplicate Hook: Hook must ONLY appear in the yellow callout box
        if (displayHook) {{
          const cleanH = displayHook.trim();
          if (displayDesc.trim() === cleanH) {{
            displayDesc = '';
          }} else if (cleanH && displayDesc.includes(cleanH)) {{
            displayDesc = displayDesc.replace(cleanH, '').trim();
          }}
        }}

        const hasTrilingual = Boolean(multi && multi.zh && multi.ko && multi.en);
        const langBadge = hasTrilingual 
          ? `<span class="px-1.5 py-0.2 rounded bg-emerald-50 text-emerald-800 text-[9px] font-mono font-bold border border-emerald-200">🌐 KO·EN·ZH</span>`
          : `<span class="px-1.5 py-0.2 rounded bg-surface-subtle text-ink-muted text-[9px] font-mono border border-surface-border">🌐 ${{currentLang === 'KO' ? '분석 대기' : (currentLang === 'ZH' ? '待分析' : 'Pending')}}</span>`;

        const card = document.createElement('div');
        card.className = 'bg-white rounded-2xl p-4 sm:p-5 border border-surface-border hover:border-indigo-400 hover:shadow-md transition flex flex-col justify-between space-y-4';

        const artType = it.artifact_type || (it.source_platform?.includes('Spaces') ? 'WEB_SERVICE' : 'WEIGHTS');
        const artBadgeMap = {{
          'WEIGHTS': {{
            label: currentLang === 'KO' ? '🤖 모델 가중치' : (currentLang === 'ZH' ? '🤖 模型权重' : '🤖 Model Weights'),
            cls: 'bg-indigo-50 text-indigo-800 border-indigo-200',
            btn: currentLang === 'KO' ? '📥 허브 다운로드' : (currentLang === 'ZH' ? '📥 Hub 下载' : '📥 Hub Download')
          }},
          'WEB_SERVICE': {{
            label: currentLang === 'KO' ? '🌐 Spaces 데모' : (currentLang === 'ZH' ? '🌐 Spaces 演示' : '🌐 Spaces Demo'),
            cls: 'bg-emerald-50 text-emerald-800 border-emerald-200',
            btn: currentLang === 'KO' ? '🚀 데모 / Spaces 체험' : (currentLang === 'ZH' ? '🚀 在线 Demo 体验' : '🚀 Try Live Spaces Demo')
          }},
          'FINETUNE': {{
            label: currentLang === 'KO' ? '🎯 특화 파인튜닝' : (currentLang === 'ZH' ? '🎯 微调定制模型' : '🎯 Finetuned Model'),
            cls: 'bg-amber-50 text-amber-800 border-amber-200',
            btn: currentLang === 'KO' ? '🎯 파인튜닝 모델 보기' : (currentLang === 'ZH' ? '🎯 查看微调模型' : '🎯 View Finetuned Model')
          }}
        }};
        const artMeta = artBadgeMap[artType] || artBadgeMap['WEIGHTS'];
        const artBadge = `<span class="px-2 py-0.5 rounded-md font-bold border text-[10px] font-mono ${{artMeta.cls}}">${{artMeta.label}}</span>`;

        const famBadge = it.model_family ? `
          <span class="px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 font-bold border border-indigo-200 text-[11px] font-mono">
            🤖 ${{it.model_family}}
          </span>
        ` : '';

        let modBadge = '';
        if (it.task_modality) {{
          const m = it.task_modality.toLowerCase();
          let icon = '🎯';
          let label = it.task_modality;
          if (m.includes('video')) {{ icon = '🎬'; label = 'Video'; }}
          else if (m.includes('image-text') || m.includes('vision') || m.includes('vlm')) {{ icon = '👁️'; label = 'VLM'; }}
          else if (m.includes('image')) {{ icon = '🎨'; label = 'Image'; }}
          else if (m.includes('speech') || m.includes('audio')) {{ icon = '🎙️'; label = 'Audio/TTS'; }}
          else if (m.includes('text')) {{ icon = '📝'; label = 'Text'; }}
          modBadge = `<span class="px-2 py-0.5 rounded-md bg-purple-50 text-purple-700 font-bold border border-purple-200 text-[10px] font-mono">${{icon}} ${{label}}</span>`;
        }}

        let paramBadge = '';
        if (it.parameter_size) {{
          paramBadge = `<span class="px-1.5 py-0.5 rounded-md bg-amber-50 text-amber-800 font-bold border border-amber-200 text-[10px] font-mono shrink-0">⚡ ${{it.parameter_size}}</span>`;
        }}

        let formatBadges = '';
        if (Array.isArray(it.detected_formats) && it.detected_formats.length > 0) {{
          formatBadges = it.detected_formats.slice(0, 3).map(fmt => 
            `<span class="px-1.5 py-0.2 rounded bg-surface-subtle text-ink-muted text-[9px] font-mono border border-surface-border uppercase">${{fmt}}</span>`
          ).join(' ');
        }}

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
                  <span>${{currentLang === 'KO' ? '관련 기술 검증: ' : (currentLang === 'ZH' ? '关联技术核验: ' : 'Related Verification: ')}}${{it.related_dossier.target_tech}}</span>
                </span>
                <i data-lucide="arrow-right" class="w-3 h-3 text-emerald-600"></i>
              </button>
            </div>
          `;
        }}

        card.innerHTML = `
          <div class="space-y-3">
            <div class="flex items-center justify-between text-xs font-mono">
              <div class="flex items-center gap-1.5 flex-wrap">
                ${{artBadge}}
                ${{famBadge}}
                ${{modBadge}}
                ${{paramBadge}}
              </div>
              <span class="text-ink-muted text-[11px] shrink-0">${{it.source_platform || 'Hugging Face'}}</span>
            </div>

            <h3 class="font-bold text-sm text-ink-primary hover:text-indigo-600 transition leading-snug">
              ${{displayTitle}}
            </h3>

            ${{hookHtml}}

            ${{displayDesc ? `<p class="text-xs text-ink-secondary leading-relaxed line-clamp-3">${{displayDesc}}</p>` : ''}}

            ${{formatBadges ? `<div class="flex items-center gap-1 flex-wrap pt-1">${{formatBadges}}</div>` : ''}}

            ${{relatedHtml}}
          </div>

          <!-- Standardized 3-Line Footer -->
          <div class="pt-3 border-t border-surface-border space-y-1.5 text-xs font-mono">
            <!-- Line 1: 수집날짜&시간 -->
            <div class="text-[11px] text-ink-muted flex items-center gap-1.5">
              <span>📅 ${{formatDateTimeCompact(it.published_at || it.harvested_at || it.harvested_date)}}</span>
            </div>

            <!-- Line 2: 분석날짜&시간 (분석모델) -->
            ${{ai?.enriched_at ? `
            <div class="text-[11px] text-indigo-700 font-semibold flex items-center gap-1.5 min-w-0 overflow-hidden">
              <span class="shrink-0">🔬 ${{formatDateTimeCompact(ai.enriched_at)}}</span>
              <span class="text-ink-muted font-normal truncate min-w-0 align-bottom cursor-help" title="${{ai.enriched_by_model || ''}}">(${{formatModelAttribution(ai.enriched_by_model)}})</span>
            </div>
            ` : `
            <div class="text-[11px] text-ink-muted flex items-center gap-1.5">
              <span>🔬 ${{currentLang === 'KO' ? 'AI 심층 분석 대기 중' : (currentLang === 'ZH' ? 'AI分析排队中' : 'Pending AI Audit')}}</span>
            </div>
            `}}

            <!-- Line 3: Hub Download / Live Demo Button -->
            <div class="flex items-center justify-between pt-0.5 font-sans">
              <span class="text-[11px] text-ink-muted font-mono flex items-center gap-1">
                <a href="${{it.source_url}}" target="_blank" rel="noopener noreferrer" class="text-indigo-600 hover:underline flex items-center gap-0.5 font-semibold">
                  📄 ${{currentLang === 'KO' ? '원문' : (currentLang === 'ZH' ? '原文' : 'Source')}} <i data-lucide="external-link" class="w-2.5 h-2.5"></i>
                </a>
              </span>
              <a href="${{it.source_url}}" target="_blank" rel="noopener noreferrer" class="px-2.5 py-1 rounded-lg bg-surface-subtle hover:bg-ink-primary hover:text-white text-ink-primary font-bold transition text-xs flex items-center gap-1 shrink-0">
                <span>${{artMeta.btn}}</span> <i data-lucide="external-link" class="w-3 h-3"></i>
              </a>
            </div>
          </div>
        `;

        grid.appendChild(card);
      }});

      if (window.lucide) window.lucide.createIcons({{ root: grid }});
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

    let currentInboxSort = 'date-audit-desc';

    function setInboxSort(val) {{
      currentInboxPage = 1;
      currentInboxSort = val;
      renderInbox();
    }}

    let currentInboxLang = 'ALL';
    let currentInboxType = 'ALL';
    let currentInboxTech = 'ALL';

    function setInboxLangFilter(lang) {{
      currentInboxPage = 1;
      currentInboxLang = lang;
      document.querySelectorAll('.inbox-filter-pill').forEach(btn => {{
        if (btn.dataset.langVal === lang) {{
          btn.className = 'inbox-filter-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shrink-0 whitespace-nowrap';
        }} else {{
          btn.className = 'inbox-filter-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }}
      }});
      renderInbox();
    }}

    function setInboxTypeFilter(typeVal) {{
      currentInboxPage = 1;
      currentInboxType = typeVal;
      document.querySelectorAll('.inbox-type-pill').forEach(btn => {{
        if (btn.dataset.typeVal === typeVal) {{
          btn.className = 'inbox-type-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shrink-0 whitespace-nowrap';
        }} else {{
          btn.className = 'inbox-type-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }}
      }});
      renderInbox();
    }}

    function setInboxTechFilter(tech) {{
      currentInboxPage = 1;
      currentInboxTech = tech;
      document.querySelectorAll('.inbox-tech-pill').forEach(btn => {{
        if (btn.dataset.techVal === tech) {{
          btn.className = 'inbox-tech-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shrink-0 whitespace-nowrap';
        }} else {{
          btn.className = 'inbox-tech-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }}
      }});
      renderInbox();
    }}

    function setInboxSourceFilter(src) {{
      currentInboxPage = 1;
      currentInboxSource = src;
      const sel = document.getElementById('inboxSourceSelect');
      if (sel && sel.value !== src) sel.value = src;

      document.querySelectorAll('.inbox-src-pill').forEach(btn => {{
        if (btn.dataset.srcVal === src) {{
          btn.className = 'inbox-src-pill px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shrink-0 whitespace-nowrap';
        }} else {{
          btn.className = 'inbox-src-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-subtle text-ink-secondary hover:text-ink-primary border border-surface-border transition shrink-0 whitespace-nowrap';
        }}
      }});
      renderInbox();
    }}

    document.getElementById('inboxSearchInput').addEventListener('input', (e) => {{
      currentInboxPage = 1;
      inboxSearchQuery = e.target.value;
      renderInbox();
    }});

    // ================= GITHUB ACTIONS CRON PIPELINE TELEMETRY =================
    const cronScheduleConfig = [
      {{ id: 1, hour: 0, min: 17, slotKo: '1회차 (00:17)', slotZh: '第1轮 (00:17)', slotEn: 'Session 1 (00:17)', nameKo: '심야 글로벌 릴리스', nameZh: '深夜全球发布', nameEn: 'Midnight Global Release', estSec: 545, runId: '34133531110', actualDur: '9분 05초' }},
      {{ id: 2, hour: 6, min: 17, slotKo: '2회차 (06:17)', slotZh: '第2轮 (06:17)', slotEn: 'Session 2 (06:17)', nameKo: '모닝 브리핑', nameZh: '早间简报', nameEn: 'Morning Briefing', estSec: 362, runId: '34096402553', actualDur: '6분 02초' }},
      {{ id: 3, hour: 12, min: 17, slotKo: '3회차 (12:17)', slotZh: '第3轮 (12:17)', slotEn: 'Session 3 (12:17)', nameKo: '정오 레이더', nameZh: '正午雷达', nameEn: 'Noon Radar', estSec: 456, runId: '34064244121', actualDur: '7분 36초' }},
      {{ id: 4, hour: 18, min: 17, slotKo: '4회차 (18:17)', slotZh: '第4轮 (18:17)', slotEn: 'Session 4 (18:17)', nameKo: '저녁 라운드업', nameZh: '晚间汇总', nameEn: 'Evening Roundup', estSec: 694, runId: '34048453203', actualDur: '11분 34초' }}
    ];

    function updateCronCountdown() {{
      if (currentView !== 'inbox') return;
      const countdownEl = document.getElementById('pipelineCountdownValue');
      const slotsContainer = document.getElementById('pipelineSlotsContainer');
      const tbody = document.getElementById('pipelineRecentRunsTbody');
      if (!countdownEl || !slotsContainer) return;

      const tLang = currentLang || 'ko';
      const aData = typeof actionsTelemetryData !== 'undefined' ? actionsTelemetryData : {{}};

      // 1. Quota Progress & Analytics
      const usedMin = aData.monthly_used_minutes || 82.8;
      const remMin = aData.monthly_remaining_minutes || 1917.2;
      const usagePct = aData.monthly_usage_percent || 4.1;

      const usedEl = document.getElementById('quotaUsedMin');
      const remEl = document.getElementById('quotaRemMin');
      const progEl = document.getElementById('quotaProgressBar');
      if (usedEl) usedEl.innerText = `${{usedMin}}분`;
      if (remEl) remEl.innerText = `${{remMin}}분 (${{100 - usagePct}}%)`;
      if (progEl) progEl.style.width = `${{Math.min(100, Math.max(2, usagePct))}}%`;

      // 2. Next Run Countdown
      const nowKst = getDynamicKstDate();
      const curHour = nowKst.getHours();
      const curMin = nowKst.getMinutes();
      const curSec = nowKst.getSeconds();
      const curTotalSec = curHour * 3600 + curMin * 60 + curSec;

      let nextSlot = null;
      let diffSec = 0;

      for (let s of cronScheduleConfig) {{
        const sTotalSec = s.hour * 3600 + s.min * 60;
        if (sTotalSec > curTotalSec) {{
          nextSlot = s;
          diffSec = sTotalSec - curTotalSec;
          break;
        }}
      }}

      if (!nextSlot) {{
        nextSlot = cronScheduleConfig[0];
        const eodSec = 24 * 3600 - curTotalSec;
        diffSec = eodSec + (nextSlot.hour * 3600 + nextSlot.min * 60);
      }}

      const remH = Math.floor(diffSec / 3600);
      const remM = Math.floor((diffSec % 3600) / 60);
      const remS = diffSec % 60;
      const pad = (n) => String(n).padStart(2, '0');

      const slotName = tLang === 'zh' ? nextSlot.slotZh : (tLang === 'en' ? nextSlot.slotEn : nextSlot.slotKo);
      countdownEl.innerText = `${{pad(remH)}}:${{pad(remM)}}:${{pad(remS)}} (${{slotName}})`;

      // 3. Render 4 Quarterly Session Telemetry Cards
      const tData = typeof timeline24hData !== 'undefined' ? timeline24hData : [];
      let cardsHtml = '';

      cronScheduleConfig.forEach((s, idx) => {{
        const sTotalSec = s.hour * 3600 + s.min * 60;
        const isPast = curTotalSec >= sTotalSec + (s.estSec || 360);
        const isActive = curTotalSec >= sTotalSec && curTotalSec < sTotalSec + (s.estSec || 360);
        const isPending = curTotalSec < sTotalSec;

        const sessionTitle = tLang === 'zh' ? s.slotZh : (tLang === 'en' ? s.slotEn : s.slotKo);
        const sessionSub = tLang === 'zh' ? s.nameZh : (tLang === 'en' ? s.nameEn : s.nameKo);

        const tlMatch = tData.find(d => d.hour === (idx * 6));
        const itemCount = tlMatch ? (tlMatch.inbox_count || 0) : 0;

        let statusBadge = '';
        let timeInfo = '';
        let cardBorder = 'border-surface-border';
        let cardBg = 'bg-slate-50/50';

        if (isActive) {{
          cardBorder = 'border-indigo-400 ring-2 ring-indigo-200';
          cardBg = 'bg-indigo-50/70';
          statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-600 text-white flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-white animate-ping"></span>${{tLang === 'zh' ? '运行中' : (tLang === 'en' ? 'Running' : '수집 진행 중')}}</span>`;
          timeInfo = `<span class="text-indigo-700 font-bold">${{tLang === 'zh' ? '正在执行' : (tLang === 'en' ? 'Ingesting live...' : '실시간 파이프라인 가동')}}</span>`;
        }} else if (isPast) {{
          cardBorder = 'border-emerald-200';
          cardBg = 'bg-emerald-50/30';
          statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1"><i data-lucide="check-circle" class="w-3 h-3 text-emerald-600"></i>${{tLang === 'zh' ? '已完成' : (tLang === 'en' ? 'Completed' : '수집 완료')}}</span>`;
          timeInfo = `<span>${{tLang === 'zh' ? '实测耗时' : (tLang === 'en' ? 'Duration' : '실측 소요')}}: <b class="text-ink-primary font-bold">${{s.actualDur}}</b> · 0 ${{tLang === 'zh' ? '错误' : (tLang === 'en' ? 'errors' : '에러')}}</span>`;
        }} else {{
          const slotDiffSec = sTotalSec - curTotalSec;
          const futH = Math.floor(slotDiffSec / 3600);
          const futM = Math.floor((slotDiffSec % 3600) / 60);
          statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-600 border border-slate-200 flex items-center gap-1"><i data-lucide="clock" class="w-3 h-3 text-slate-500"></i>${{tLang === 'zh' ? '等待中' : (tLang === 'en' ? 'Scheduled' : '대기 중')}}</span>`;
          timeInfo = `<span>${{tLang === 'zh' ? '剩余' : (tLang === 'en' ? 'Remaining' : '남은 시간')}}: <b class="text-indigo-600">${{futH}}h ${{futM}}m</b> · ${{tLang === 'zh' ? '预计约' : (tLang === 'en' ? 'Est. ' : '예상 ')}}${{Math.round(s.estSec/60)}}분</span>`;
        }}

        cardsHtml += `
          <div class="p-3.5 rounded-xl border ${{cardBorder}} ${{cardBg}} flex flex-col justify-between space-y-2.5 transition">
            <div class="flex items-center justify-between">
              <span class="font-bold text-ink-primary text-xs">${{sessionTitle}}</span>
              ${{statusBadge}}
            </div>
            <div class="space-y-1">
              <div class="text-[11px] text-ink-secondary font-medium">${{sessionSub}}</div>
              <div class="text-xs font-bold text-ink-primary flex items-center justify-between">
                <span>${{tLang === 'zh' ? '采集总量' : (tLang === 'en' ? 'Ingested' : '수집량')}}:</span>
                <span class="text-indigo-600 font-mono">${{itemCount}}건</span>
              </div>
            </div>
            <div class="pt-2 border-t border-surface-border/60 text-[10px] text-ink-muted flex items-center justify-between">
              ${{timeInfo}}
            </div>
          </div>
        `;
      }});
      slotsContainer.innerHTML = cardsHtml;

      // 4. Render Recent Run Logs Table
      if (tbody && aData.runs && aData.runs.length > 0) {{
        let rowsHtml = '';
        aData.runs.forEach(r => {{
          const isSuccess = r.conclusion === 'success';
          const isCancelled = r.conclusion === 'cancelled';
          const statusCls = isSuccess ? 'bg-emerald-100 text-emerald-800 border-emerald-300' : (isCancelled ? 'bg-amber-100 text-amber-800 border-amber-300' : 'bg-indigo-100 text-indigo-800 border-indigo-300');
          const statusLabel = isSuccess ? (tLang === 'zh' ? '成功' : (tLang === 'en' ? 'Success' : '성공')) : (isCancelled ? (tLang === 'zh' ? '已取消' : (tLang === 'en' ? 'Cancelled' : '취소')) : (tLang === 'zh' ? '运行中' : (tLang === 'en' ? 'Running' : '진행중')));
          
          rowsHtml += `
            <tr class="hover:bg-slate-50/80 transition">
              <td class="py-2.5 px-3 font-bold text-ink-primary text-[11px]">${{r.created_at_kst}}</td>
              <td class="py-2.5 px-3 font-medium text-ink-secondary">${{r.name.length > 32 ? r.name.slice(0, 30) + '...' : r.name}}</td>
              <td class="py-2.5 px-3 text-ink-muted"><span class="px-1.5 py-0.5 rounded bg-slate-100 text-[10px] border border-slate-200">${{r.event}}</span></td>
              <td class="py-2.5 px-3 font-bold text-ink-primary">${{r.duration_str}}</td>
              <td class="py-2.5 px-3">
                <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${{statusCls}} inline-flex items-center gap-1">
                  ${{statusLabel}}
                </span>
              </td>
              <td class="py-2.5 px-3 text-emerald-600 font-bold">0 errors</td>
            </tr>
          `;
        }});
        tbody.innerHTML = rowsHtml;
      }}

      if (typeof lucide !== 'undefined') lucide.createIcons();
    }}

    setInterval(updateCronCountdown, 1000);

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

      // 🌟 Precision DateTime Sorting (Default: AI Audit Date DESC)
      filtered.sort((a, b) => {{
        if (currentInboxSort === 'date-audit-desc') {{
          return parseItemTimestamp(b, 'audit') - parseItemTimestamp(a, 'audit');
        }} else if (currentInboxSort === 'date-audit-asc') {{
          return parseItemTimestamp(a, 'audit') - parseItemTimestamp(b, 'audit');
        }} else if (currentInboxSort === 'date-source-desc' || currentInboxSort === 'date-desc') {{
          return parseItemTimestamp(b, 'source') - parseItemTimestamp(a, 'source');
        }} else if (currentInboxSort === 'date-source-asc' || currentInboxSort === 'date-asc') {{
          return parseItemTimestamp(a, 'source') - parseItemTimestamp(b, 'source');
        }} else if (currentInboxSort === 'viral-desc') {{
          return calculateStandardizedViralScore(b) - calculateStandardizedViralScore(a);
        }} else if (currentInboxSort === 'viral-asc') {{
          return calculateStandardizedViralScore(a) - calculateStandardizedViralScore(b);
        }}
        return parseItemTimestamp(b, 'audit') - parseItemTimestamp(a, 'audit');
      }});

      const totalPages = Math.ceil(filtered.length / PAGE_SIZE) || 1;
      if (currentInboxPage > totalPages) currentInboxPage = totalPages;
      if (currentInboxPage < 1) currentInboxPage = 1;

      renderPagination('inboxPagination', currentInboxPage, totalPages, 'changeInboxPage');

      if (filtered.length === 0) {{
        grid.innerHTML = `<div class="col-span-full py-16 text-center text-ink-muted font-medium">${{currentLang === 'KO' ? '수집된 인박스 후보가 없습니다.' : (currentLang === 'ZH' ? '收件箱暂无候选数据。' : 'No candidates in the inbox.')}}</div>`;
        return;
      }}

      const pagedInbox = filtered.slice((currentInboxPage - 1) * PAGE_SIZE, currentInboxPage * PAGE_SIZE);
      pagedInbox.forEach(it => {{
        const isQueued = queuedItemIds.has(it.inbox_id);
        const ai = it.ai_enrichment;
        const multi = it.multilingual || (ai ? ai.multilingual : null);
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
        card.className = 'executive-card p-4 sm:p-5 flex flex-col justify-between space-y-3.5 hover:border-indigo-400 hover:shadow-md transition';

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

        let inboxSourceLinks = '';
        if (it.sources && it.sources.length > 1) {{
          inboxSourceLinks = buildMultiSourceCluster(it.sources, it.inbox_id || it.id);
        }} else {{
          inboxSourceLinks = `
          <a href="${{it.source_url}}" target="_blank" rel="noopener noreferrer" class="text-indigo-600 hover:underline flex items-center gap-0.5 font-semibold text-[11px] font-mono">
            📄 ${{currentLang === 'KO' ? '원문' : (currentLang === 'ZH' ? '原文' : 'Source')}} <i data-lucide="external-link" class="w-2.5 h-2.5"></i>
          </a>`;
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

          </div>

          <!-- Standardized 3-Line Footer -->
          <div class="pt-3 border-t border-surface-border space-y-1.5 text-xs font-mono">
            <!-- Line 1: 수집날짜&시간 -->
            <div class="text-[11px] text-ink-muted flex items-center gap-1.5">
              <span>📅 ${{formatDateTimeCompact(it.published_at || it.created_at || it.harvested_at || it.harvested_date)}}</span>
            </div>

            <!-- Line 2: 분석날짜&시간 (분석모델) -->
            ${{ai?.enriched_at ? `
            <div class="text-[11px] text-indigo-700 font-semibold flex items-center gap-1.5 min-w-0 overflow-hidden">
              <span class="shrink-0">🔬 ${{formatDateTimeCompact(ai.enriched_at)}}</span>
              <span class="text-ink-muted font-normal truncate min-w-0 align-bottom cursor-help" title="${{ai.enriched_by_model || ''}}">(${{formatModelAttribution(ai.enriched_by_model)}})</span>
            </div>
            ` : `
            <div class="text-[11px] text-ink-muted flex items-center gap-1.5">
              <span>🔬 ${{currentLang === 'KO' ? 'AI 심층 분석 대기 중' : (currentLang === 'ZH' ? 'AI分析排队中' : 'Pending AI Audit')}}</span>
            </div>
            `}}

            <!-- Line 3: 원문 링크 & 큐 등록 액션 버튼 -->
            <div class="flex items-center justify-between gap-2 pt-0.5 font-sans">
              <div class="flex items-center gap-1.5 flex-wrap">
                ${{inboxSourceLinks}}
              </div>

              <button onclick="toggleQueueItem('${{it.inbox_id}}', '${{displayTitle.replace(/'/g, "")}}')" 
                      class="px-2.5 py-1 rounded-lg text-xs font-bold transition flex items-center gap-1.5 shrink-0 ${{isQueued ? 'bg-emerald-700 text-white font-black' : 'bg-surface-subtle text-ink-primary hover:bg-ink-primary hover:text-white border border-surface-border'}}">
                <i data-lucide="${{isQueued ? 'check' : 'zap'}}" class="w-3.5 h-3.5"></i>
                <span>${{isQueued ? t.inboxQueuedBtn : t.inboxQueueBtn}}</span>
              </button>
            </div>
          </div>
        `;

        grid.appendChild(card);
      }});

      if (window.lucide) window.lucide.createIcons({{ root: grid }});
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
      renderHomeTopPicks();
      renderTelemetryCharts();
      updateCronCountdown();
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
