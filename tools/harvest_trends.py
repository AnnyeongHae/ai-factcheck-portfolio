#!/usr/bin/env python3
"""
Multi-Source Enterprise Trend Harvester & Health Monitor (2026 SOTA Framework - v6.0)
Pipeline Architecture:
1. Ingest All Data: Fetch 100% candidates from GitHub, Hugging Face, Hacker News, ArXiv, Reddit without early filtering.
2. Update Existing: Match against existing inbox items by normalized URL / Title, update latest metrics, compute delta & growth rate.
3. Deduplicate & Save Brand New: Insert only novel items that do not exist anywhere in investigations or inbox.
"""

import datetime
import hashlib
import json
import os
import random
import re
import sys
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
# Ensure UTF-8
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Auto-load .env
env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(env_file):
    try:
        with open(env_file, "r", encoding="utf-8") as ef:
            for eline in ef:
                eline = eline.strip()
                if eline and not eline.startswith("#") and "=" in eline:
                    ek, ev = eline.split("=", 1)
                    ek, ev = ek.strip(), ev.strip()
                    if ek and not os.getenv(ek):
                        os.environ[ek] = ev
    except Exception:
        pass

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '_', text)
    return text[:45]

TRACKING_PARAMS = {
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'utm_id',
    'ref', 'ref_src', 'ref_url', 'source', 'fbclid', 'gclid', 'msclkid', 'twclid',
    'si', 'spm', 'igshid', 'yclid', 'mc_cid', 'mc_eid', 'aff', 'affiliate'
}
try:
    from tools.dedup_engine import evaluate_deduplication, normalize_url as canonical_normalize_url
except Exception:
    try:
        from dedup_engine import evaluate_deduplication, normalize_url as canonical_normalize_url
    except Exception:
        evaluate_deduplication = None
        canonical_normalize_url = None

def clean_stealth_url(url: str) -> str:
    """Strips all tracking parameters (UTM, ChatGPT ref, social trackers) to maintain stealth."""
    if not url: return ""
    try:
        parsed = urllib.parse.urlparse(url)
        query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        clean_pairs = [
            (k, v) for k, v in query_pairs 
            if k.lower() not in TRACKING_PARAMS and not k.lower().startswith('utm_')
        ]
        clean_query = urllib.parse.urlencode(clean_pairs)
        cleaned = urllib.parse.urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            clean_query,
            parsed.fragment
        ))
        return cleaned.rstrip('?')
    except Exception:
        return url

def normalize_url(url: str) -> str:
    if not url: return ""
    cleaned = clean_stealth_url(url)
    u = cleaned.lower().strip()
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
        try:
            print(formatted)
        except Exception:
            try:
                print(formatted.encode("ascii", "replace").decode("ascii"))
            except Exception:
                pass
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(formatted + "\n")
        except Exception:
            pass

def get_canonical_hash(platform: str, url: str, title: str) -> str:
    norm = normalize_url(url)
    slug = slugify(title)
    key = f"{platform.lower()}:{norm or slug}"
    return hashlib.sha256(key.encode('utf-8')).hexdigest()[:16]

def index_existing_data(base_dir):
    """
    Builds lookup indexes for existing data to enable O(1) matching:
    - inbox_hash_map: canonical_hash -> filepath
    - inbox_url_map: normalized_url -> filepath
    - inbox_slug_map: slug -> filepath
    - investigation_urls: set of normalized_urls
    """
    inbox_hash_map = {}
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
                        # Extract all possible URLs associated with this verified dossier
                        urls_to_add = [
                            m.get("target_repo"),
                            m.get("source_url"),
                            m.get("raw_viral_post", {}).get("post_url"),
                            m.get("portfolio_story", {}).get("hands_on_log", {}).get("pipeline_or_url")
                        ]
                        for s in m.get("sources", []):
                            if isinstance(s, dict) and "url" in s:
                                urls_to_add.append(s["url"])
                        for s in m.get("primary_sources", []):
                            if isinstance(s, dict) and "url" in s:
                                urls_to_add.append(s["url"])
                        
                        for u in urls_to_add:
                            nu = normalize_url(u)
                            if nu:
                                investigation_urls.add(nu)
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
                        aurl = normalize_url(m.get("article_url", ""))
                        hnurl = normalize_url(m.get("hn_url", ""))
                        title = m.get("title", "")
                        plat = m.get("source_platform", "")
                        c_hash = get_canonical_hash(plat, surl, title)
                        inbox_hash_map[c_hash] = fpath
                        if surl:
                            inbox_url_map[surl] = fpath
                        if aurl:
                            inbox_url_map[aurl] = fpath
                        if hnurl:
                            inbox_url_map[hnurl] = fpath
                        if title:
                            inbox_slug_map[slugify(title)] = fpath
                except Exception:
                    pass

    return inbox_hash_map, inbox_url_map, inbox_slug_map, investigation_urls

STEALTH_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
]

def get_stealth_headers(content_type="json"):
    ua = random.choice(STEALTH_USER_AGENTS)
    is_mac = "Macintosh" in ua
    platform = '"macOS"' if is_mac else '"Windows"'
    
    headers = {
        "User-Agent": ua,
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": platform,
        "Sec-Fetch-Dest": "empty" if content_type == "json" else "document",
        "Sec-Fetch-Mode": "cors" if content_type == "json" else "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Upgrade-Insecure-Requests": "1"
    }
    if content_type == "json":
        headers["Accept"] = "application/json, text/plain, */*"
    elif content_type == "xml":
        headers["Accept"] = "application/xml, text/xml, */*"
    else:
        headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    return headers

def fetch_json(url, headers=None, timeout=12):
    time.sleep(random.uniform(0.05, 0.15))
    clean_url = clean_stealth_url(url)
    h = headers or get_stealth_headers("json")
    req = urllib.request.Request(clean_url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode('utf-8'))

def fetch_xml(url, headers=None, timeout=12):
    time.sleep(random.uniform(0.05, 0.15))
    clean_url = clean_stealth_url(url)
    h = headers or get_stealth_headers("xml")
    req = urllib.request.Request(clean_url, headers=h)
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
    investigations_dir = os.path.join(base_dir, "investigations")
    logs_dir = os.path.join(base_dir, "logs")
    os.makedirs(inbox_dir, exist_ok=True)
    os.makedirs(investigations_dir, exist_ok=True)
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
    inbox_hash_map, inbox_url_map, inbox_slug_map, investigation_urls = index_existing_data(base_dir)
    logger.log(f"[*] Indexed {len(inbox_hash_map)} hashes ({len(inbox_url_map)} URLs) & {len(investigation_urls)} verified portfolio URLs.")

    harvest_report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "date": today_str,
        "sources": {},
        "summary": {"total_fetched": 0, "updated_count": 0, "new_saved": 0, "duplicates_skipped": 0, "errors": 0}
    }

    # =========================================================================
    # STEP 1: INGEST ALL DATA (NO PREMATURE FILTERING)
    # =========================================================================
    all_candidates = []
    seen_urls_this_run = set()

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
        # 🌟 Stealth Mode: Strip all tracking & referrer params (UTM, ChatGPT ref, etc.)
        if "source_url" in cand:
            cand["source_url"] = clean_stealth_url(cand["source_url"])
        if "article_url" in cand:
            cand["article_url"] = clean_stealth_url(cand["article_url"])
        if "hn_url" in cand:
            cand["hn_url"] = clean_stealth_url(cand["hn_url"])

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
                        "category_type": "MODEL",
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
        logger.log("[*] Fetching Hugging Face Trending & Popular Spaces (limit=60)...")
        # 2-1: Trending Spaces
        sp_data_trending = fetch_json("https://huggingface.co/api/spaces?sort=trendingScore&direction=-1&limit=60")
        # 2-2: Most Liked Recent Spaces
        sp_data_liked = fetch_json("https://huggingface.co/api/spaces?sort=likes&direction=-1&limit=30")
        
        combined_spaces = {}
        for sp_list in [sp_data_trending, sp_data_liked]:
            if sp_list and isinstance(sp_list, list):
                for item in sp_list:
                    sid = item.get("id")
                    if sid and sid not in combined_spaces:
                        combined_spaces[sid] = item

        count = 0
        for sid, item in combined_spaces.items():
            url = f"https://huggingface.co/spaces/{sid}"
            sdk = item.get("sdk", "gradio")
            likes = item.get("likes", 0)
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
                    
                        score = story.get("score", 0)
                        descendants = story.get("descendants", 0)
                        story_time = story.get("time")
                        published_at = datetime.datetime.fromtimestamp(story_time).isoformat() if story_time else datetime.datetime.now().isoformat()
                        added = add_candidate({
                            "title": f"Hacker News: {title}",
                            "source_platform": "Hacker News",
                            "source_url": hn_discussion_url,
                            "hn_url": hn_discussion_url,
                            "article_url": article_url,
                            "published_at": published_at,
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

    # 7. GeekNews (한국판 해커뉴스 - Atom Feed)
    geek_start = time.time()
    try:
        logger.log("[*] Fetching GeekNews Korean Tech Trends (Atom feed)...")
        xml_data = fetch_xml("https://news.hada.io/rss/news")
        root = ET.fromstring(xml_data)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        count = 0
        for entry in root.findall('atom:entry', ns)[:25]:
            title_elem = entry.find('atom:title', ns)
            id_elem = entry.find('atom:id', ns)
            content_elem = entry.find('atom:content', ns) or entry.find('atom:summary', ns)
            
            if title_elem is not None and id_elem is not None:
                title = title_elem.text.strip() if title_elem.text else ""
                topic_url = id_elem.text.strip() if id_elem.text else ""
                content_raw = content_elem.text.strip() if content_elem is not None and content_elem.text else ""
                clean_desc = re.sub(r'<[^>]+>', ' ', content_raw).strip()[:200]
                
                # Check for external article link
                m_ext = re.search(r'href=[\'"](https?://[^\'"]+)[\'"]', content_raw)
                article_url = m_ext.group(1) if m_ext else topic_url

                added = add_candidate({
                    "title": f"GeekNews: {title}",
                    "title_ko": title,
                    "source_platform": "GeekNews",
                    "source_url": topic_url,
                    "hn_url": topic_url,
                    "article_url": article_url,
                    "type": "sns",
                    "category_type": "NEWS",
                    "description": clean_desc or f"GeekNews Korean Tech Trend: {title}",
                    "description_ko": clean_desc or title,
                    "viral_metric": "🇰🇷 GeekNews 큐레이션"
                })
                if added: count += 1

        harvest_report["sources"]["geeknews"] = {"status": "SUCCESS", "items_found": count, "duration_sec": round(time.time() - geek_start, 2)}
        logger.log(f"[+] GeekNews: {count} Korean tech items ingested in {time.time() - geek_start:.2f}s")
    except Exception as e:
        harvest_report["sources"]["geeknews"] = {"status": "ERROR", "error": str(e), "duration_sec": round(time.time() - geek_start, 2)}
        logger.log(f"[!] GeekNews Note: {e}", level="WARNING")

    # 8. Curated AI Engineering RSS (Hugging Face Blog & Simon Willison)
    rss_start = time.time()
    try:
        logger.log("[*] Fetching Curated Global AI RSS Feeds...")
        rss_sources = [
            ("Hugging Face Blog", "https://huggingface.co/blog/feed.xml", "https://huggingface.co/blog")
        ]
        count = 0
        for sname, sfeed, base_url in rss_sources:
            try:
                xml_raw = fetch_xml(sfeed)
                root = ET.fromstring(xml_raw)
                items = root.findall('.//item')
                if not items:
                    ns = {'atom': 'http://www.w3.org/2005/Atom'}
                    items = root.findall('atom:entry', ns) or root.findall('.//{http://www.w3.org/2005/Atom}entry')
                
                for it in items[:10]:
                    t_node = it.find('title') if it.find('title') is not None else it.find('{http://www.w3.org/2005/Atom}title')
                    l_node = it.find('link') if it.find('link') is not None else it.find('{http://www.w3.org/2005/Atom}link')
                    d_node = it.find('description') if it.find('description') is not None else (it.find('{http://www.w3.org/2005/Atom}summary') or it.find('{http://www.w3.org/2005/Atom}content'))
                    
                    if t_node is not None and t_node.text:
                        title = t_node.text.strip()
                        url = ""
                        if l_node is not None:
                            url = l_node.attrib.get('href') if 'href' in l_node.attrib else (l_node.text or "").strip()
                        if not url:
                            id_n = it.find('{http://www.w3.org/2005/Atom}id')
                            if id_n is not None and id_n.text: url = id_n.text.strip()
                        
                        desc = ""
                        if d_node is not None and d_node.text:
                            desc = re.sub(r'<[^>]+>', ' ', d_node.text).strip()[:180]
                        
                        if url:
                            added = add_candidate({
                                "title": f"{sname}: {title}",
                                "source_platform": sname,
                                "source_url": url,
                                "article_url": url,
                                "type": "sns",
                                "category_type": "NEWS",
                                "description": desc or f"{sname} Tech Publication: {title}",
                                "viral_metric": "🌍 Official AI Publication"
                            })
                            if added: count += 1
            except Exception as e_inner:
                logger.log(f"[!] {sname} feed parse note: {e_inner}", level="WARNING")

        harvest_report["sources"]["curated_rss"] = {"status": "SUCCESS", "items_found": count, "duration_sec": round(time.time() - rss_start, 2)}
        logger.log(f"[+] Curated AI RSS: {count} publication articles ingested in {time.time() - rss_start:.2f}s")
    except Exception as e:
        harvest_report["sources"]["curated_rss"] = {"status": "ERROR", "error": str(e), "duration_sec": round(time.time() - rss_start, 2)}
        logger.log(f"[!] Curated RSS Failed: {e}", level="WARNING")

    logger.log(f"[*] Step 1 Complete: Total {len(all_candidates)} candidates fetched from all channels.")

    # =========================================================================
    # STEP 2: UPDATE EXISTING ITEMS (METRIC 갱신 & DELTA 계산)
    # =========================================================================
    existing_cases_list = []
    if os.path.exists(investigations_dir):
        for cdir in os.listdir(investigations_dir):
            mp = os.path.join(investigations_dir, cdir, "metadata.json")
            if os.path.isfile(mp):
                try:
                    with open(mp, "r", encoding="utf-8") as fp:
                        existing_cases_list.append(json.load(fp))
                except Exception:
                    pass

    existing_inbox_items = []
    for ipath in set(inbox_hash_map.values()):
        if os.path.isfile(ipath):
            try:
                with open(ipath, "r", encoding="utf-8") as fp:
                    existing_inbox_items.append(json.load(fp))
            except Exception:
                pass

    gemini_api_key = os.getenv("GEMINI_API_KEY", "")

    updated_count = 0
    new_saved = 0
    dup_skipped = 0
    newly_harvested_files = []

    for cand in all_candidates:
        norm_url = normalize_url(cand["source_url"])
        slug = slugify(cand["title"])
        plat = cand.get("source_platform", "")
        c_hash = get_canonical_hash(plat, norm_url, cand["title"])
        current_val = extract_metric_number(cand.get("viral_metric", ""))

        # Extract all normalized URLs for this candidate
        cand_urls = [normalize_url(cand.get("source_url")), normalize_url(cand.get("article_url")), normalize_url(cand.get("hn_url"))]
        cand_urls = [u for u in cand_urls if u]

        # 🌟 Check 1: Block immediately if already in verified investigations (Omni-URL check)
        if any(u in investigation_urls for u in cand_urls):
            dup_skipped += 1
            logger.log(f"[DEDUP Verified Case] Blocked already verified dossier: {cand['title'][:40]}")
            continue

        # 3-Tier Deduplication & Semantic Matching Gate
        if evaluate_deduplication:
            try:
                dedup_res = evaluate_deduplication(cand, existing_cases_list, existing_inbox_items, api_key=gemini_api_key)
                if dedup_res.get("is_duplicate"):
                    dup_skipped += 1
                    logger.log(f"[DEDUP Tier {dedup_res.get('tier')}] Blocked: {cand['title'][:35]} -> Matched {dedup_res.get('matched_id')} ({dedup_res.get('reason')})")
                    continue
            except Exception as dedup_err:
                logger.log(f"[!] Dedup check note: {dedup_err}", level="WARNING")

        # Check if exists in inbox by Hash, Omni-URL or Slug (Deduplication & Block)
        matched_inbox_by_url = next((inbox_url_map[u] for u in cand_urls if u in inbox_url_map), None)
        target_inbox_file = inbox_hash_map.get(c_hash) or matched_inbox_by_url or inbox_slug_map.get(slug)

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
                if "title_ko" in cand and not old_item.get("title_ko"): old_item["title_ko"] = cand["title_ko"]
                if "description_ko" in cand and not old_item.get("description_ko"): old_item["description_ko"] = cand["description_ko"]
                if "hn_url" in cand and not old_item.get("hn_url"): old_item["hn_url"] = cand["hn_url"]
                if "article_url" in cand and not old_item.get("article_url"): old_item["article_url"] = cand["article_url"]

                with open(target_inbox_file, "w", encoding="utf-8") as fp:
                    json.dump(old_item, fp, indent=2, ensure_ascii=False)

                updated_count += 1
            except Exception as e:
                logger.log(f"[!] Failed to update {target_inbox_file}: {e}", level="ERROR")
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

        now_iso = datetime.datetime.now().isoformat()
        pub_iso = cand.get("published_at") or now_iso

        inbox_item = {
            "inbox_id": case_id,
            "harvested_date": today_str,
            "harvested_at": now_iso,
            "published_at": pub_iso,
            "created_at": pub_iso,
            "updated_at": now_iso,
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

        if "title_ko" in cand: inbox_item["title_ko"] = cand["title_ko"]
        if "description_ko" in cand: inbox_item["description_ko"] = cand["description_ko"]
        if "hn_url" in cand: inbox_item["hn_url"] = cand["hn_url"]
        if "article_url" in cand: inbox_item["article_url"] = cand["article_url"]

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(inbox_item, f, indent=2, ensure_ascii=False)

        # Update in-memory index & tracking
        inbox_hash_map[c_hash] = save_path
        inbox_url_map[norm_url] = save_path
        inbox_slug_map[slug] = save_path
        newly_harvested_files.append(save_path)
        new_saved += 1

    harvest_report["summary"]["total_fetched"] = len(all_candidates)
    harvest_report["summary"]["updated_count"] = updated_count
    harvest_report["summary"]["new_saved"] = new_saved
    harvest_report["summary"]["duplicates_skipped"] = dup_skipped

    # Save newly harvested items manifest for targeted O(1) AI enrichment
    manifest_path = os.path.join(logs_dir, "last_harvest_new_items.json")
    with open(manifest_path, "w", encoding="utf-8") as fp:
        json.dump({
            "harvested_at": datetime.datetime.now().astimezone().isoformat(),
            "new_count": len(newly_harvested_files),
            "files": newly_harvested_files
        }, fp, indent=2, ensure_ascii=False)
    logger.log(f"[+] Saved manifest with {len(newly_harvested_files)} novel items to '{manifest_path}'")

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
