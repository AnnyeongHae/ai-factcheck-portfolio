#!/usr/bin/env python3
"""
Multi-Source Enterprise Trend Harvester & Health Monitor (2026 SOTA Framework - v6.0)
Pipeline Architecture:
1. Ingest All Data: Fetch 100% candidates from GitHub, Hugging Face, Hacker News, ArXiv, Reddit without early filtering.
2. Update Existing: Match against existing inbox items by normalized URL / Title, update latest metrics, compute delta & growth rate.
3. Deduplicate & Save Brand New: Insert only novel items that do not exist anywhere in investigations or inbox.
"""

import datetime
import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

# Ensure UTF-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '_', text)
    return text[:45]

def normalize_url(url: str) -> str:
    if not url: return ""
    u = url.lower().strip()
    u = re.sub(r'^https?://', '', u)
    u = re.sub(r'^www\.', '', u)
    u = u.rstrip('/')
    return u

def extract_metric_number(text: str) -> int:
    if not text: return 0
    m_k = re.search(r'([\d\.]+)\s*[kK]', str(text))
    if m_k:
        try:
            return int(float(m_k.group(1)) * 1000)
        except Exception:
            pass
    m_num = re.search(r'([\d,]+)', str(text))
    if m_num:
        try:
            return int(m_num.group(1).replace(',', ''))
        except Exception:
            pass
    return 0

class Logger:
    def __init__(self, log_file):
        self.log_file = log_file

    def log(self, msg, level="INFO"):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{timestamp}] [{level}] {msg}"
        print(formatted)
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(formatted + "\n")
        except Exception:
            pass

def index_existing_data(base_dir):
    """
    Builds lookup indexes for existing data to enable O(1) matching:
    - inbox_url_map: normalized_url -> filepath
    - inbox_slug_map: slug -> filepath
    - investigation_urls: set of normalized_urls
    """
    inbox_url_map = {}
    inbox_slug_map = {}
    investigation_urls = set()

    # 1. Investigations (Verified Portfolios)
    inv_dir = os.path.join(base_dir, "investigations")
    if os.path.exists(inv_dir):
        for d in os.listdir(inv_dir):
            meta_path = os.path.join(inv_dir, d, "metadata.json")
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        m = json.load(f)
                        if "target_repo" in m:
                            investigation_urls.add(normalize_url(m["target_repo"]))
                        if "source_url" in m:
                            investigation_urls.add(normalize_url(m["source_url"]))
                        for s in m.get("sources", []):
                            if "url" in s:
                                investigation_urls.add(normalize_url(s["url"]))
                except Exception:
                    pass

    # 2. Inbox Items
    inbox_dir = os.path.join(base_dir, "inbox")
    if os.path.exists(inbox_dir):
        for f in os.listdir(inbox_dir):
            if f.endswith(".json") and not f.startswith("_"):
                fpath = os.path.join(inbox_dir, f)
                try:
                    with open(fpath, "r", encoding="utf-8") as fp:
                        m = json.load(fp)
                        surl = normalize_url(m.get("source_url", ""))
                        if surl:
                            inbox_url_map[surl] = fpath
                        title = m.get("title", "")
                        if title:
                            inbox_slug_map[slugify(title)] = fpath
                except Exception:
                    pass

    return inbox_url_map, inbox_slug_map, investigation_urls

def fetch_json(url, headers=None, timeout=12):
    if headers is None:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode('utf-8'))

def fetch_xml(url, headers=None, timeout=12):
    if headers is None:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) FactCheck/1.0"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode('utf-8')

def match_persona_domain(title, desc, persona_config):
    text = (title + " " + desc).lower()
    domains = persona_config.get("user_profile", {}).get("proven_experience_domains", {})
    matched = []
    for d_key, d_val in domains.items():
        for kw in d_val.get("relevance_keywords", []):
            if kw.lower() in text:
                matched.append(d_val.get("name"))
                break
    return matched if matched else ["일반 최신 기술 (Tech General)"]

def harvest_all():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    inbox_dir = os.path.join(base_dir, "inbox")
    logs_dir = os.path.join(base_dir, "logs")
    os.makedirs(inbox_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    log_file = os.path.join(logs_dir, f"harvest_{today_str}.log")
    logger = Logger(log_file)

    logger.log("=======================================================")
    logger.log("🚀 Multi-Source Trend Harvester Job (v6.0 - 3-Step Pipeline) Started")
    logger.log("=======================================================")

    # Load Persona Config
    persona_path = os.path.join(base_dir, "configs", "user_persona_alignment.json")
    persona_config = {}
    if os.path.exists(persona_path):
        with open(persona_path, "r", encoding="utf-8") as f:
            persona_config = json.load(f)

    # Index Existing Data (O(1) lookups)
    inbox_url_map, inbox_slug_map, investigation_urls = index_existing_data(base_dir)
    logger.log(f"[*] Indexed {len(inbox_url_map)} existing inbox items & {len(investigation_urls)} verified portfolio URLs.")

    harvest_report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "date": today_str,
        "sources": {},
        "summary": {"total_fetched": 0, "updated_count": 0, "new_saved": 0, "duplicates_skipped": 0, "errors": 0}
    }

    # =========================================================================
    # STEP 1: INGEST ALL DATA (NO PREMATURE FILTERING)
    # =========================================================================
    def validate_candidate(cand):
        url = cand.get("source_url", "").strip()
        if not url or not url.startswith("http"):
            return False
        # Reject generic root domains
        if url.rstrip('/') in ["https://news.ycombinator.com", "https://github.com", "https://huggingface.co"]:
            return False
        # Reject invalid HN IDs
        if "news.ycombinator.com/item?id=" in url:
            if not re.search(r'item\?id=\d+', url):
                return False
        # Reject invalid GitHub repo paths
        if "github.com" in url:
            if not re.search(r'github\.com/[\w\.-]+/[\w\.-]+', url):
                return False
        return True

    def add_candidate(cand):
        if not validate_candidate(cand):
            return False
        nurl = normalize_url(cand.get("source_url", ""))
        if nurl and nurl not in seen_urls_this_run:
            seen_urls_this_run.add(nurl)
            all_candidates.append(cand)
            return True
        return False

    # 1. Hugging Face Models Trending
    hf_start = time.time()
    try:
        logger.log("[*] Fetching Hugging Face Trending Models (limit=30)...")
        hf_data = fetch_json("https://huggingface.co/api/models?sort=trendingScore&direction=-1&limit=30")
        count = 0
        if hf_data and isinstance(hf_data, list):
            for item in hf_data:
                mid = item.get("id", "")
                url = f"https://huggingface.co/{mid}"
                score = round(item.get('trendingScore', 0), 1)
                downloads = item.get('downloads', 0)
                likes = item.get('likes', 0)
                if mid:
                    added = add_candidate({
                        "title": f"HuggingFace Model: {mid}",
                        "source_platform": "Hugging Face Models",
                        "source_url": url,
                        "type": "repo",
                        "description": f"Trending Score: {score}, Downloads: {downloads}, Likes: {likes}, Pipeline: {item.get('pipeline_tag', 'N/A')}",
                        "viral_metric": f"Trending {score} pts (❤️ {likes})"
                    })
                    if added: count += 1
        harvest_report["sources"]["hf_models"] = {"status": "SUCCESS", "items_found": count, "duration_sec": round(time.time() - hf_start, 2)}
        logger.log(f"[+] Hugging Face Models: {count} candidates ingested in {time.time() - hf_start:.2f}s")
    except Exception as e:
        harvest_report["sources"]["hf_models"] = {"status": "ERROR", "error": str(e), "duration_sec": round(time.time() - hf_start, 2)}
        logger.log(f"[!] Hugging Face Models Failed: {e}", level="ERROR")
        harvest_report["summary"]["errors"] += 1

    # 2. Hugging Face Spaces (Interactive Demos)
    spaces_start = time.time()
    try:
        logger.log("[*] Fetching Hugging Face Trending Spaces (limit=25)...")
        sp_data = fetch_json("https://huggingface.co/api/spaces?sort=trendingScore&direction=-1&limit=25")
        count = 0
        if sp_data and isinstance(sp_data, list):
            for item in sp_data:
                sid = item.get("id", "")
                url = f"https://huggingface.co/spaces/{sid}"
                sdk = item.get("sdk", "gradio")
                likes = item.get("likes", 0)
                if sid:
                    added = add_candidate({
                        "title": f"HF Space: {sid}",
                        "source_platform": "Hugging Face Spaces (Demo)",
                        "source_url": url,
                        "type": "repo",
                        "description": f"Interactive AI Demo (SDK: {sdk}) | Likes: {likes} | Live URL: {url}",
                        "viral_metric": f"❤️ {likes} Likes (Trending Demo)"
                    })
                    if added: count += 1
        harvest_report["sources"]["hf_spaces"] = {"status": "SUCCESS", "items_found": count, "duration_sec": round(time.time() - spaces_start, 2)}
        logger.log(f"[+] Hugging Face Spaces: {count} interactive demo candidates ingested in {time.time() - spaces_start:.2f}s")
    except Exception as e:
        harvest_report["sources"]["hf_spaces"] = {"status": "ERROR", "error": str(e), "duration_sec": round(time.time() - spaces_start, 2)}
        logger.log(f"[!] Hugging Face Spaces Failed: {e}", level="ERROR")
        harvest_report["summary"]["errors"] += 1

    # 3. GitHub Search API (High Velocity Repos)
    gh_start = time.time()
    try:
        logger.log("[*] Fetching GitHub High-Velocity Repositories (Recent 14 days, Stars > 30)...")
        fourteen_days_ago = (datetime.date.today() - datetime.timedelta(days=14)).strftime("%Y-%m-%d")
        gh_url = f"https://api.github.com/search/repositories?q=created:>{fourteen_days_ago}+stars:>30&sort=stars&order=desc&per_page=30"
        gh_data = fetch_json(gh_url, headers={"User-Agent": "FactCheck-Harvester/1.0", "Accept": "application/vnd.github.v3+json"})
        count = 0
        if gh_data and "items" in gh_data:
            for item in gh_data["items"]:
                rname = item.get("full_name", "")
                url = item.get("html_url", "")
                desc = item.get("description", "") or "No description"
                stars = item.get('stargazers_count', 0)
                forks = item.get('forks_count', 0)
                if rname:
                    added = add_candidate({
                        "title": f"GitHub: {rname}",
                        "source_platform": "GitHub Official",
                        "source_url": url,
                        "type": "repo",
                        "description": f"Stars: {stars}, Forks: {forks} | {desc}",
                        "viral_metric": f"★ {stars} Stars"
                    })
                    if added: count += 1
        harvest_report["sources"]["github"] = {"status": "SUCCESS", "items_found": count, "duration_sec": round(time.time() - gh_start, 2)}
        logger.log(f"[+] GitHub Search: {count} repo candidates ingested in {time.time() - gh_start:.2f}s")
    except Exception as e:
        harvest_report["sources"]["github"] = {"status": "ERROR", "error": str(e), "duration_sec": round(time.time() - gh_start, 2)}
        logger.log(f"[!] GitHub Search Failed: {e}", level="ERROR")
        harvest_report["summary"]["errors"] += 1

    # 4. Hacker News API (Top & Best Stories Combined)
    hn_start = time.time()
    try:
        logger.log("[*] Fetching Hacker News Top & Best Stories (limit=80)...")
        hn_top_ids = fetch_json("https://hacker-news.firebaseio.com/v0/topstories.json") or []
        hn_best_ids = fetch_json("https://hacker-news.firebaseio.com/v0/beststories.json") or []
        
        combined_ids = []
        seen_sids = set()
        for sid in list(hn_top_ids[:40]) + list(hn_best_ids[:40]):
            if sid not in seen_sids:
                seen_sids.add(sid)
                combined_ids.append(sid)

        count = 0
        hn_keywords = [
            "ai", "llm", "agent", "rust", "python", "model", "rag", "open-source", 
            "show hn", "bench", "eval", "gpt", "claude", "deepseek", "llama", 
            "transformer", "diffusion", "gpu", "cuda", "browser", "vision", 
            "neural", "inference", "compiler", "linux", "database", "postgres"
        ]

        for sid in combined_ids[:60]:
            try:
                story = fetch_json(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json", timeout=6)
                if story and "title" in story and story.get("type") == "story":
                    if story.get("dead") or story.get("deleted"):
                        continue
                    title = story.get("title", "")
                    hn_discussion_url = f"https://news.ycombinator.com/item?id={sid}"
                    article_url = story.get("url") or hn_discussion_url
                    title_lower = title.lower()
                    
                    if any(kw in title_lower for kw in hn_keywords):
                        score = story.get("score", 0)
                        descendants = story.get("descendants", 0)
                        added = add_candidate({
                            "title": f"Hacker News: {title}",
                            "source_platform": "Hacker News",
                            "source_url": hn_discussion_url,
                            "hn_url": hn_discussion_url,
                            "article_url": article_url,
                            "type": "repo" if "github.com" in article_url else "sns",
                            "category_type": "NEWS" if not "github.com" in article_url else "REPO",
                            "description": f"HN Score: {score} pts | Comments: {descendants} | {title}",
                            "viral_metric": f"🔥 {score} HN Points"
                        })
                        if added: count += 1
            except Exception:
                continue

        harvest_report["sources"]["hacker_news"] = {"status": "SUCCESS", "items_found": count, "duration_sec": round(time.time() - hn_start, 2)}
        logger.log(f"[+] Hacker News: {count} verified AI/Tech items ingested in {time.time() - hn_start:.2f}s")
    except Exception as e:
        harvest_report["sources"]["hacker_news"] = {"status": "ERROR", "error": str(e), "duration_sec": round(time.time() - hn_start, 2)}
        logger.log(f"[!] Hacker News Failed: {e}", level="ERROR")
        harvest_report["summary"]["errors"] += 1

    # 5. ArXiv API (cs.AI & cs.CL)
    arxiv_start = time.time()
    try:
        logger.log("[*] Fetching ArXiv AI/CL Recent Papers (limit=20)...")
        xml_data = fetch_xml("http://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.CL&sortBy=submittedDate&sortOrder=descending&max_results=20")
        root = ET.fromstring(xml_data)
        count = 0
        for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
            title_elem = entry.find('{http://www.w3.org/2005/Atom}title')
            id_elem = entry.find('{http://www.w3.org/2005/Atom}id')
            summary_elem = entry.find('{http://www.w3.org/2005/Atom}summary')
            if title_elem is not None and id_elem is not None:
                title = title_elem.text.strip().replace("\n", " ")
                url = id_elem.text.strip()
                summary = summary_elem.text.strip().replace("\n", " ")[:200] if summary_elem is not None else ""
                added = add_candidate({
                    "title": f"ArXiv: {title}",
                    "source_platform": "ArXiv Preprint",
                    "source_url": url,
                    "type": "repo",
                    "description": f"Abstract: {summary}...",
                    "viral_metric": "ArXiv Primary Paper"
                })
                if added: count += 1
        harvest_report["sources"]["arxiv"] = {"status": "SUCCESS", "items_found": count, "duration_sec": round(time.time() - arxiv_start, 2)}
        logger.log(f"[+] ArXiv: {count} papers ingested in {time.time() - arxiv_start:.2f}s")
    except Exception as e:
        harvest_report["sources"]["arxiv"] = {"status": "ERROR", "error": str(e), "duration_sec": round(time.time() - arxiv_start, 2)}
        logger.log(f"[!] ArXiv Failed: {e}", level="ERROR")
        harvest_report["summary"]["errors"] += 1

    # 6. Reddit r/LocalLLaMA
    reddit_start = time.time()
    try:
        logger.log("[*] Fetching Reddit r/LocalLLaMA Hot (limit=15)...")
        r_url = "https://www.reddit.com/r/LocalLLaMA/hot.json?limit=15"
        r_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r_data = fetch_json(r_url, headers=r_headers)
        count = 0
        if r_data and "data" in r_data and "children" in r_data["data"]:
            for post in r_data["data"]["children"]:
                pdata = post.get("data", {})
                title = pdata.get("title", "")
                url = f"https://reddit.com{pdata.get('permalink', '')}"
                if not pdata.get("stickied", False):
                    added = add_candidate({
                        "title": f"Reddit: {title}",
                        "source_platform": "Reddit r/LocalLLaMA",
                        "source_url": url,
                        "type": "sns",
                        "description": f"Upvotes: {pdata.get('score', 0)}, Comments: {pdata.get('num_comments', 0)}",
                        "viral_metric": f"{pdata.get('score', 0)} Upvotes"
                    })
                    if added: count += 1
        harvest_report["sources"]["reddit"] = {"status": "SUCCESS", "items_found": count, "duration_sec": round(time.time() - reddit_start, 2)}
        logger.log(f"[+] Reddit: {count} items ingested in {time.time() - reddit_start:.2f}s")
    except Exception as e:
        harvest_report["sources"]["reddit"] = {"status": "ERROR", "error": str(e), "duration_sec": round(time.time() - reddit_start, 2)}
        logger.log(f"[!] Reddit Note: {e}", level="WARNING")

    logger.log(f"[*] Step 1 Complete: Total {len(all_candidates)} candidates fetched from all channels.")

    # =========================================================================
    # STEP 2: UPDATE EXISTING ITEMS (METRIC 갱신 & DELTA 계산)
    # =========================================================================
    updated_count = 0
    new_saved = 0
    dup_skipped = 0

    for cand in all_candidates:
        norm_url = normalize_url(cand["source_url"])
        slug = slugify(cand["title"])
        current_val = extract_metric_number(cand.get("viral_metric", ""))

        # Check if exists in inbox by URL or Slug
        target_inbox_file = inbox_url_map.get(norm_url) or inbox_slug_map.get(slug)

        if target_inbox_file and os.path.exists(target_inbox_file):
            # UPDATE EXISTING ITEM
            try:
                with open(target_inbox_file, "r", encoding="utf-8") as fp:
                    old_item = json.load(fp)

                old_tracking = old_item.get("metric_tracking")
                if not old_tracking:
                    old_init_val = extract_metric_number(old_item.get("viral_metric", ""))
                    old_tracking = {
                        "initial": {
                            "value": old_init_val,
                            "display": old_item.get("viral_metric", ""),
                            "recorded_at": old_item.get("created_at", old_item.get("harvested_date", today_str))
                        }
                    }

                init_val = old_tracking.get("initial", {}).get("value", current_val)
                delta = current_val - init_val
                delta_pct = round(((current_val - init_val) / max(1, init_val)) * 100, 1) if init_val > 0 else 0.0

                old_tracking["latest"] = {
                    "value": current_val,
                    "display": cand["viral_metric"],
                    "updated_at": today_str
                }
                old_tracking["delta"] = delta
                old_tracking["delta_display"] = f"+{delta:,}" if delta > 0 else (f"{delta:,}" if delta < 0 else "0")
                old_tracking["growth_rate_pct"] = delta_pct
                old_tracking["is_spiking"] = delta >= 50 or delta_pct >= 30.0

                old_item["metric_tracking"] = old_tracking
                old_item["description"] = cand["description"]
                old_item["viral_metric"] = cand["viral_metric"]
                old_item["updated_at"] = today_str

                with open(target_inbox_file, "w", encoding="utf-8") as fp:
                    json.dump(old_item, fp, indent=2, ensure_ascii=False)

                updated_count += 1
            except Exception as e:
                logger.log(f"[!] Failed to update {target_inbox_file}: {e}", level="ERROR")
            continue

        # Check if already verified in investigations (Do not duplicate verified portfolios)
        if norm_url in investigation_urls:
            dup_skipped += 1
            continue

        # =========================================================================
        # STEP 3: DEDUPLICATE & SAVE BRAND NEW ITEMS
        # =========================================================================
        case_id = f"{today_str}_{cand['type']}_{slug}"
        save_path = os.path.join(inbox_dir, f"{case_id}.json")
        if os.path.exists(save_path):
            dup_skipped += 1
            continue

        matched_domains = match_persona_domain(cand["title"], cand["description"], persona_config)

        metric_tracking = {
            "initial": {
                "value": current_val,
                "display": cand["viral_metric"],
                "recorded_at": today_str
            },
            "latest": {
                "value": current_val,
                "display": cand["viral_metric"],
                "updated_at": today_str
            },
            "delta": 0,
            "delta_display": "+0",
            "growth_rate_pct": 0.0,
            "is_spiking": False
        }

        inbox_item = {
            "inbox_id": case_id,
            "harvested_date": today_str,
            "created_at": today_str,
            "updated_at": today_str,
            "title": cand["title"],
            "source_platform": cand["source_platform"],
            "source_url": cand["source_url"],
            "type": cand["type"],
            "category_type": cand.get("category_type", "TECH"),
            "description": cand["description"],
            "viral_metric": cand["viral_metric"],
            "metric_tracking": metric_tracking,
            "matched_user_domains": matched_domains,
            "status": "PENDING_REVIEW"
        }

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(inbox_item, f, indent=2, ensure_ascii=False)

        # Update in-memory index
        inbox_url_map[norm_url] = save_path
        inbox_slug_map[slug] = save_path
        new_saved += 1

    harvest_report["summary"]["total_fetched"] = len(all_candidates)
    harvest_report["summary"]["updated_count"] = updated_count
    harvest_report["summary"]["new_saved"] = new_saved
    harvest_report["summary"]["duplicates_skipped"] = dup_skipped

    logger.log(f"=======================================================")
    logger.log(f"🎯 Harvester Finished Successfully:")
    logger.log(f"    - Total Candidates Ingested: {len(all_candidates)}")
    logger.log(f"    - Existing Items Updated (Upsert): {updated_count}")
    logger.log(f"    - Novel Items Saved: {new_saved}")
    logger.log(f"    - Duplicates / Verified Skipped: {dup_skipped}")
    logger.log(f"=======================================================")

    # Update logs/harvest_history.json
    history_file = os.path.join(logs_dir, "harvest_history.json")
    history = []
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []
    history.insert(0, harvest_report)
    history = history[:30]

    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    logger.log(f"[+] Harvest history saved to {history_file}")

if __name__ == "__main__":
    harvest_all()
