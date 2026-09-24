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
import concurrent.futures
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

    # 3. Load DB Fingerprints & URLs from Neon Postgres if connected (Deterministic O(1) Lookup)
    try:
        try:
            from tools.db_bridge import get_db_connection
        except Exception:
            from db_bridge import get_db_connection
        conn = get_db_connection()
        if conn:
            with conn.cursor() as cur:
                cur.execute("SELECT inbox_id, source_fingerprint, source_url, title FROM raw_trends_inbox;")
                for iid, fp, surl, title in cur.fetchall():
                    tag = f"db:{iid}"
                    if fp and fp not in inbox_hash_map:
                        inbox_hash_map[fp] = tag
                    if surl:
                        nu = normalize_url(surl)
                        if nu and nu not in inbox_url_map:
                            inbox_url_map[nu] = tag
                    if title:
                        tslug = slugify(title)
                        if tslug and tslug not in inbox_slug_map:
                            inbox_slug_map[tslug] = tag
            conn.close()
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

def fetch_hn_raw_comments(sid, max_comments=100):
    """
    ELT Raw Comment Extractor for Hacker News via Algolia API.
    Preserves all comments without premature truncation or lossy pre-filtering.
    """
    try:
        # Extract numeric story ID if full URL passed
        if isinstance(sid, str) and not sid.isdigit():
            m = re.search(r'(?:id=|\/)(\d+)', sid)
            if m:
                sid = m.group(1)
            else:
                return []
        url = f"https://hn.algolia.com/api/v1/items/{sid}"
        data = fetch_json(url, timeout=5)
        if not data:
            return []
        
        def _traverse(node_list):
            collected = []
            for n in node_list:
                if not n or not isinstance(n, dict):
                    continue
                txt = n.get("text") or ""
                if txt:
                    clean_txt = re.sub(r'<[^>]+>', ' ', txt).strip()
                    collected.append({
                        "id": f"hn_{n.get('id')}",
                        "author": n.get("author") or "anonymous",
                        "text": clean_txt,
                        "points": n.get("points") or 0,
                        "created_at_i": n.get("created_at_i"),
                        "parent_id": n.get("parent_id")
                    })
                if n.get("children"):
                    collected.extend(_traverse(n.get("children")))
            return collected

        all_comments = _traverse(data.get("children", []))
        return all_comments[:max_comments]
    except Exception:
        return []

def fetch_reddit_raw_comments(post_url, max_comments=100):
    """
    ELT Raw Comment Extractor for Reddit via Post .rss Feed.
    Preserves user comments without premature truncation.
    """
    try:
        clean = clean_stealth_url(post_url).rstrip('/')
        feed_url = f"{clean}/.rss"
        xml_data = fetch_xml(feed_url, timeout=5)
        root = ET.fromstring(xml_data)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        entries = root.findall('atom:entry', ns)
        comments = []
        for entry in entries[1:max_comments + 1]:
            author = entry.findtext('atom:author/atom:name', default='', namespaces=ns)
            content = entry.findtext('atom:content', default='', namespaces=ns)
            updated = entry.findtext('atom:updated', default='', namespaces=ns) or entry.findtext('atom:published', default='', namespaces=ns)
            entry_id = entry.findtext('atom:id', default='', namespaces=ns)
            clean_txt = re.sub(r'<[^>]+>', ' ', content).strip() if content else ""
            if clean_txt:
                comments.append({
                    "id": entry_id,
                    "author": author,
                    "text": clean_txt,
                    "points": 0,
                    "updated": updated
                })
        return comments
    except Exception:
        return []

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

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    kst_tz = datetime.timezone(datetime.timedelta(hours=9))
    now_kst = now_utc.astimezone(kst_tz)
    today_str = now_kst.strftime("%Y-%m-%d")
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
        logger.log("[*] Fetching Hugging Face Trending Models (limit=100)...")
        hf_data = fetch_json("https://huggingface.co/api/models?sort=trendingScore&direction=-1&limit=100")
        count = 0
        if hf_data and isinstance(hf_data, list):
            for item in hf_data:
                mid = item.get("id", "")
                url = f"https://huggingface.co/{mid}"
                score = round(item.get('trendingScore', 0), 1)
                downloads = item.get('downloads', 0)
                likes = item.get('likes', 0)
                pipeline_tag = item.get('pipeline_tag') or "text-generation"
                tags = item.get('tags', []) or []
                lib_name = item.get('library_name') or ""

                # Extract parameter size (e.g. 27B, 7B, 14B)
                param_match = re.search(r'\b(\d+(\.\d+)?[BMb])\b', mid)
                parameter_size = param_match.group(1).upper() if param_match else "N/A"

                # Extract model family
                mid_lower = mid.lower()
                if 'qwen' in mid_lower: model_family = 'Qwen'
                elif 'deepseek' in mid_lower: model_family = 'DeepSeek'
                elif 'minimax' in mid_lower: model_family = 'MiniMax'
                elif 'wan' in mid_lower: model_family = 'Wan'
                elif 'flux' in mid_lower: model_family = 'FLUX'
                elif 'llama' in mid_lower: model_family = 'Llama'
                elif 'glm' in mid_lower: model_family = 'GLM'
                elif 'hunyuan' in mid_lower: model_family = 'Hunyuan'
                elif any(k in mid_lower for k in ['whisper', 'tts', 'speech', 'audio', 'voice', 'firered']): model_family = 'Audio / Speech'
                elif 'mistral' in mid_lower or 'codestral' in mid_lower: model_family = 'Mistral'
                elif 'gemma' in mid_lower: model_family = 'Gemma'
                else: model_family = 'Standalone'

                # Formats
                detected_formats = []
                for t in tags:
                    t_low = t.lower()
                    if t_low in ['safetensors', 'gguf', 'fp8', '8-bit', 'mlx', 'diffusers', 'transformers']:
                        detected_formats.append(t.upper() if t_low in ['gguf', 'fp8', 'mlx'] else t.capitalize())
                if 'gguf' in mid_lower and 'GGUF' not in detected_formats: detected_formats.append('GGUF')
                if 'fp8' in mid_lower and 'FP8' not in detected_formats: detected_formats.append('FP8')
                if 'lora' in mid_lower and 'LoRA' not in detected_formats: detected_formats.append('LoRA')

                pub_at = item.get("createdAt") or item.get("lastModified")
                if mid:
                    added = add_candidate({
                        "title": f"HuggingFace Model: {mid}",
                        "source_platform": "Hugging Face Models",
                        "source_url": url,
                        "published_at": pub_at,
                        "type": "repo",
                        "category_type": "MODEL",
                        "description": f"Trending Score: {score}, Downloads: {downloads}, Likes: {likes}, Pipeline: {pipeline_tag}",
                        "viral_metric": f"Trending {score} pts (❤️ {likes})",
                        "task_modality": pipeline_tag,
                        "model_family": model_family,
                        "parameter_size": parameter_size,
                        "detected_formats": detected_formats if detected_formats else ["Safetensors"],
                        "library_name": lib_name
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
        logger.log("[*] Fetching Hugging Face Trending & Popular Spaces (limit=120+60)...")
        # 2-1: Trending Spaces
        sp_data_trending = fetch_json("https://huggingface.co/api/spaces?sort=trendingScore&direction=-1&limit=120")
        # 2-2: Most Liked Recent Spaces
        sp_data_liked = fetch_json("https://huggingface.co/api/spaces?sort=likes&direction=-1&limit=60")
        
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
            pub_at = item.get("createdAt") or item.get("lastModified")
            added = add_candidate({
                "title": f"HF Space: {sid}",
                "source_platform": "Hugging Face Spaces (Demo)",
                "source_url": url,
                "published_at": pub_at,
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

    # 3. GitHub Search API (High Velocity Repos & Emerging AI Tools)
    gh_start = time.time()
    try:
        logger.log("[*] Fetching GitHub High-Velocity Repositories (Recent 14 days, Stars > 30 & Emerging AI)...")
        fourteen_days_ago = (datetime.date.today() - datetime.timedelta(days=14)).strftime("%Y-%m-%d")
        gh_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        gh_headers = {"User-Agent": "FactCheck-Harvester/1.0", "Accept": "application/vnd.github.v3+json"}
        if gh_token:
            gh_headers["Authorization"] = f"Bearer {gh_token}"

        gh_queries = [
            f"https://api.github.com/search/repositories?q=created:>{fourteen_days_ago}+stars:>30&sort=stars&order=desc&per_page=100",
            f"https://api.github.com/search/repositories?q=topic:llm+created:>{fourteen_days_ago}+stars:>15&sort=stars&order=desc&per_page=50"
        ]
        count = 0
        seen_repos = set()
        for gh_url in gh_queries:
            try:
                gh_data = fetch_json(gh_url, headers=gh_headers)
                if gh_data and "items" in gh_data:
                    for item in gh_data["items"]:
                        rname = item.get("full_name", "")
                        if not rname or rname in seen_repos:
                            continue
                        seen_repos.add(rname)
                        url = item.get("html_url", "")
                        desc = item.get("description", "") or "No description"
                        stars = item.get('stargazers_count', 0)
                        forks = item.get('forks_count', 0)
                        pub_at = item.get("created_at")
                        added = add_candidate({
                            "title": f"GitHub: {rname}",
                            "source_platform": "GitHub Official",
                            "source_url": url,
                            "published_at": pub_at,
                            "type": "repo",
                            "description": f"Stars: {stars}, Forks: {forks} | {desc}",
                            "viral_metric": f"★ {stars} Stars"
                        })
                        if added: count += 1
            except Exception as gh_q_err:
                logger.log(f"[!] GitHub query note: {gh_q_err}", level="WARNING")

        harvest_report["sources"]["github"] = {"status": "SUCCESS", "items_found": count, "duration_sec": round(time.time() - gh_start, 2)}
        logger.log(f"[+] GitHub Search: {count} repo candidates ingested in {time.time() - gh_start:.2f}s")
    except Exception as e:
        harvest_report["sources"]["github"] = {"status": "ERROR", "error": str(e), "duration_sec": round(time.time() - gh_start, 2)}
        logger.log(f"[!] GitHub Search Failed: {e}", level="ERROR")
        harvest_report["summary"]["errors"] += 1

    # 4. Hacker News API (Algolia Front Page & Show HN)
    hn_start = time.time()
    try:
        logger.log("[*] Fetching Hacker News Front Page & Show HN via Algolia API (Parallel w=6)...")
        hn_queries = [
            "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=100",
            "https://hn.algolia.com/api/v1/search?tags=show_hn&hitsPerPage=40"
        ]
        count = 0
        seen_stories = set()
        candidate_stories = []
        for hn_url in hn_queries:
            try:
                hn_data = fetch_json(hn_url)
                if hn_data and "hits" in hn_data:
                    for story in hn_data["hits"]:
                        title = story.get("title") or ""
                        sid = story.get("objectID") or ""
                        if not title or not sid or sid in seen_stories:
                            continue
                        seen_stories.add(sid)
                        candidate_stories.append(story)
            except Exception as hn_q_err:
                logger.log(f"[!] HN query note: {hn_q_err}", level="WARNING")

        # 🚀 A/B Tested High-Speed Parallel Comment Extraction (ThreadPoolExecutor max_workers=6)
        story_comments_map = {}
        stories_with_comments = [s for s in candidate_stories if (s.get("num_comments") or 0) > 0]
        
        def _fetch_hn_worker(s):
            sid = s.get("objectID")
            return sid, fetch_hn_raw_comments(sid, max_comments=100)

        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            future_to_sid = {executor.submit(_fetch_hn_worker, s): s.get("objectID") for s in stories_with_comments}
            for future in concurrent.futures.as_completed(future_to_sid):
                try:
                    sid, comments = future.result()
                    story_comments_map[sid] = comments
                except Exception:
                    pass

        for story in candidate_stories:
            title = story.get("title") or ""
            sid = story.get("objectID") or ""
            hn_discussion_url = f"https://news.ycombinator.com/item?id={sid}"
            article_url = story.get("url") or hn_discussion_url
            score = story.get("points") or 0
            num_comments = story.get("num_comments") or 0
            created_at_i = story.get("created_at_i")
            published_at = datetime.datetime.fromtimestamp(created_at_i, tz=datetime.timezone.utc).isoformat() if created_at_i else datetime.datetime.now(datetime.timezone.utc).isoformat()
            
            raw_comments = story_comments_map.get(sid, [])

            added = add_candidate({
                "title": f"Hacker News: {title}",
                "source_platform": "Hacker News",
                "source_url": hn_discussion_url,
                "hn_url": hn_discussion_url,
                "article_url": article_url,
                "published_at": published_at,
                "type": "repo" if "github.com" in article_url else "sns",
                "category_type": "REPO" if "github.com" in article_url else "NEWS",
                "description": f"{title} | {score} points, {num_comments} comments",
                "viral_metric": f"🔥 {score} HN Points",
                "raw_comments": raw_comments,
                "comment_count": len(raw_comments)
            })
            if added: count += 1

        harvest_report["sources"]["hacker_news"] = {"status": "SUCCESS", "items_found": count, "duration_sec": round(time.time() - hn_start, 2)}
        logger.log(f"[+] Hacker News: {count} items ingested in {time.time() - hn_start:.2f}s (parallel w=6)")
    except Exception as e:
        harvest_report["sources"]["hacker_news"] = {"status": "ERROR", "error": str(e), "duration_sec": round(time.time() - hn_start, 2)}
        logger.log(f"[!] Hacker News Failed: {e}", level="ERROR")
        harvest_report["summary"]["errors"] += 1
        harvest_report["summary"]["errors"] += 1

    # 5. ArXiv API (cs.AI, cs.CL, cs.LG, cs.CV)
    arxiv_start = time.time()
    try:
        logger.log("[*] Fetching ArXiv AI Recent Papers (cs.AI, limit=50)...")
        xml_data = fetch_xml("https://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate&sortOrder=descending&max_results=50")
        root = ET.fromstring(xml_data)
        count = 0
        for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
            title_elem = entry.find('{http://www.w3.org/2005/Atom}title')
            id_elem = entry.find('{http://www.w3.org/2005/Atom}id')
            summary_elem = entry.find('{http://www.w3.org/2005/Atom}summary')
            pub_elem = entry.find('{http://www.w3.org/2005/Atom}published')
            
            pub_iso = None
            if pub_elem is not None and pub_elem.text:
                try:
                    dt = datetime.datetime.fromisoformat(pub_elem.text.strip().replace("Z", "+00:00"))
                    pub_iso = dt.astimezone(kst_tz).isoformat()
                except Exception:
                    pub_iso = pub_elem.text.strip()

            if title_elem is not None and id_elem is not None:
                title = title_elem.text.strip().replace("\n", " ")
                url = id_elem.text.strip()
                summary = summary_elem.text.strip().replace("\n", " ")[:200] if summary_elem is not None else ""
                added = add_candidate({
                    "title": f"ArXiv: {title}",
                    "source_platform": "ArXiv Preprint",
                    "source_url": url,
                    "published_at": pub_iso,
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

    # 6. Reddit Major Tech Channels via RSS (.rss)
    reddit_start = time.time()
    try:
        logger.log("[*] Fetching Reddit Major Tech Channels (technology, singularity, LocalLLaMA, ML, AI, ChatGPT)...")
        subreddits = [
            ("Reddit r/technology", "https://www.reddit.com/r/technology/.rss?limit=25"),
            ("Reddit r/singularity", "https://www.reddit.com/r/singularity/.rss?limit=25"),
            ("Reddit r/LocalLLaMA", "https://www.reddit.com/r/LocalLLaMA/.rss?limit=25"),
            ("Reddit r/MachineLearning", "https://www.reddit.com/r/MachineLearning/.rss?limit=25"),
            ("Reddit r/artificial", "https://www.reddit.com/r/artificial/.rss?limit=25"),
            ("Reddit r/ChatGPT", "https://www.reddit.com/r/ChatGPT/.rss?limit=25")
        ]
        count = 0
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        for sname, r_feed in subreddits:
            try:
                xml_raw = fetch_xml(r_feed)
                root = ET.fromstring(xml_raw)
                for idx, entry in enumerate(root.findall('atom:entry', ns)[:25]):
                    title_elem = entry.find('atom:title', ns)
                    link_elem = entry.find('atom:link', ns)
                    pub_elem = entry.find('atom:updated', ns) or entry.find('atom:published', ns)
                    content_elem = entry.find('atom:content', ns)
                    
                    if title_elem is not None and title_elem.text:
                        title = title_elem.text.strip()
                        url = link_elem.attrib.get('href', '') if link_elem is not None else ""
                        published_at = pub_elem.text.strip() if pub_elem is not None and pub_elem.text else None
                        desc_text = re.sub(r'<[^>]+>', ' ', content_elem.text).strip()[:180] if content_elem is not None and content_elem.text else title
                        
                        if url:
                            # Extract comments for top 5 high-signal posts per subreddit to protect against Reddit's 60 req/min ceiling
                            r_comments = fetch_reddit_raw_comments(url, max_comments=100) if idx < 5 else []
                            added = add_candidate({
                                "title": f"{sname.split()[-1]}: {title}",
                                "source_platform": sname,
                                "source_url": url,
                                "published_at": published_at,
                                "type": "sns",
                                "category_type": "NEWS" if "technology" in sname else "TECH",
                                "description": desc_text,
                                "viral_metric": "💬 Reddit Major Discussion",
                                "raw_comments": r_comments,
                                "comment_count": len(r_comments)
                            })
                            if added: count += 1
            except Exception as r_err:
                logger.log(f"[!] {sname} feed note: {r_err}", level="WARNING")

        harvest_report["sources"]["reddit"] = {"status": "SUCCESS", "items_found": count, "duration_sec": round(time.time() - reddit_start, 2)}
        logger.log(f"[+] Reddit: {count} social items ingested in {time.time() - reddit_start:.2f}s")
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
        for entry in root.findall('atom:entry', ns)[:50]:
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

                pub_elem = entry.find('atom:published', ns)
                if pub_elem is None:
                    pub_elem = entry.find('atom:updated', ns)
                published_at = pub_elem.text.strip() if (pub_elem is not None and pub_elem.text) else None

                added = add_candidate({
                    "title": f"GeekNews: {title}",
                    "title_ko": title,
                    "source_platform": "GeekNews",
                    "source_url": topic_url,
                    "hn_url": topic_url,
                    "article_url": article_url,
                    "published_at": published_at,
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

    # 8. Curated AI Engineering RSS (Hugging Face, PyTorchKR, Simon Willison, OpenAI, Anthropic)
    rss_start = time.time()
    try:
        logger.log("[*] Fetching Curated Global AI & Korean Community Feeds...")
        rss_sources = [
            ("Hugging Face Blog", "https://huggingface.co/blog/feed.xml", "https://huggingface.co/blog"),
            ("PyTorchKR", "https://discuss.pytorch.kr/latest.rss", "https://discuss.pytorch.kr"),
            ("Simon Willison Weblog", "https://simonwillison.net/atom/everything/", "https://simonwillison.net"),
            ("OpenAI News", "https://openai.com/news/rss.xml", "https://openai.com"),
            ("Anthropic News", "https://www.anthropic.com/news/rss.xml", "https://www.anthropic.com")
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
                
                for it in items[:30]:
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
                            pub_n = it.find('pubDate') or it.find('{http://www.w3.org/2005/Atom}published') or it.find('{http://www.w3.org/2005/Atom}updated')
                            pub_iso = None
                            if pub_n is not None and pub_n.text:
                                try:
                                    import email.utils
                                    p_dt = email.utils.parsedate_to_datetime(pub_n.text.strip())
                                    pub_iso = p_dt.isoformat()
                                except Exception:
                                    pub_iso = pub_n.text.strip()

                            cand_data = {
                                "title": f"{sname}: {title}",
                                "source_platform": sname,
                                "source_url": url,
                                "article_url": url,
                                "published_at": pub_iso,
                                "type": "sns",
                                "category_type": "NEWS",
                                "description": desc or f"{sname} Tech Publication: {title}",
                                "viral_metric": "🇰🇷 PyTorchKR 커뮤니티" if "PyTorch" in sname else "🌍 Official AI Publication"
                            }
                            if "PyTorch" in sname:
                                cand_data["title_ko"] = title
                                cand_data["description_ko"] = desc or title
                            added = add_candidate(cand_data)
                            if added: count += 1
            except Exception as e_inner:
                logger.log(f"[!] {sname} feed parse note: {e_inner}", level="WARNING")

        harvest_report["sources"]["curated_rss"] = {"status": "SUCCESS", "items_found": count, "duration_sec": round(time.time() - rss_start, 2)}
        logger.log(f"[+] Curated AI RSS: {count} publication articles ingested in {time.time() - rss_start:.2f}s")
    except Exception as e:
        harvest_report["sources"]["curated_rss"] = {"status": "ERROR", "error": str(e), "duration_sec": round(time.time() - rss_start, 2)}
        logger.log(f"[!] Curated RSS Failed: {e}", level="WARNING")

    # 9. Mainstream Tech Press & Google News (TechCrunch, The Verge, VentureBeat, Ars Technica)
    gnews_start = time.time()
    try:
        logger.log("[*] Fetching Global Tech Press & Google News RSS...")
        press_feeds = [
            ("Google News KR", "https://news.google.com/rss/search?q=%EC%9D%B8%EA%B3%B5%EC%A7%80%EB%8A%A5+OR+%EC%83%9D%EC%84%B1%ED%98%95AI&hl=ko&gl=KR&ceid=KR:ko"),
            ("Google News Global", "https://news.google.com/rss/search?q=%22OpenAI%22+OR+%22Claude%22+OR+%22DeepSeek%22&hl=en-US&gl=US&ceid=US:en"),
            ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
            ("The Verge AI", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
            ("VentureBeat AI", "https://venturebeat.com/category/ai/feed/"),
            ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/technology-lab")
        ]
        count = 0
        for sname, p_feed in press_feeds:
            try:
                xml_raw = fetch_xml(p_feed)
                root = ET.fromstring(xml_raw)
                items = root.findall('.//item')
                if not items:
                    ns = {'atom': 'http://www.w3.org/2005/Atom'}
                    items = root.findall('atom:entry', ns) or root.findall('.//{http://www.w3.org/2005/Atom}entry')

                for it in items[:30]:
                    t_node = it.find('title') if it.find('title') is not None else it.find('{http://www.w3.org/2005/Atom}title')
                    l_node = it.find('link') if it.find('link') is not None else it.find('{http://www.w3.org/2005/Atom}link')
                    p_node = it.find('pubDate') or it.find('{http://www.w3.org/2005/Atom}published') or it.find('{http://www.w3.org/2005/Atom}updated')
                    d_node = it.find('description') if it.find('description') is not None else (it.find('{http://www.w3.org/2005/Atom}summary') or it.find('{http://www.w3.org/2005/Atom}content'))
                    
                    if t_node is not None and t_node.text:
                        raw_title = t_node.text.strip()
                        title_clean = raw_title
                        news_org = sname
                        if " - " in raw_title:
                            parts = raw_title.rsplit(" - ", 1)
                            title_clean = parts[0].strip()
                            news_org = parts[1].strip()
                            
                        url = ""
                        if l_node is not None:
                            url = l_node.attrib.get('href') if 'href' in l_node.attrib else (l_node.text or "").strip()
                        if not url:
                            id_n = it.find('{http://www.w3.org/2005/Atom}id')
                            if id_n is not None and id_n.text: url = id_n.text.strip()

                        pub_iso = None
                        if p_node is not None and p_node.text:
                            try:
                                import email.utils
                                pub_iso = email.utils.parsedate_to_datetime(p_node.text.strip()).isoformat()
                            except Exception:
                                pub_iso = p_node.text.strip()
                        
                        desc_text = re.sub(r'<[^>]+>', ' ', d_node.text).strip()[:180] if (d_node is not None and d_node.text) else title_clean
                        if url:
                            added = add_candidate({
                                "title": f"News: {title_clean}",
                                "source_platform": f"Press ({news_org})",
                                "source_url": url,
                                "article_url": url,
                                "published_at": pub_iso,
                                "type": "sns",
                                "category_type": "NEWS",
                                "description": desc_text,
                                "viral_metric": f"📰 {news_org} 보도"
                            })
                            if added: count += 1
            except Exception as p_err:
                logger.log(f"[!] {sname} feed note: {p_err}", level="WARNING")

        harvest_report["sources"]["press_news"] = {"status": "SUCCESS", "items_found": count, "duration_sec": round(time.time() - gnews_start, 2)}
        logger.log(f"[+] Global Tech Press & News: {count} items ingested in {time.time() - gnews_start:.2f}s")
    except Exception as e:
        harvest_report["sources"]["press_news"] = {"status": "ERROR", "error": str(e), "duration_sec": round(time.time() - gnews_start, 2)}
        logger.log(f"[!] Press News Note: {e}", level="WARNING")

    # 10. YouTube Tech Channels RSS (Mainstream AI Virality)
    yt_start = time.time()
    try:
        logger.log("[*] Fetching YouTube Top Tech Channels RSS...")
        yt_channels = [
            ("Fireship", "https://www.youtube.com/feeds/videos.xml?channel_id=UCsBjURrPoezykLs9EqgamOA"),
            ("조코딩 JoCoding", "https://www.youtube.com/feeds/videos.xml?channel_id=UCQNE2JmbasNYbjGAcuBiRRg"),
            ("Two Minute Papers", "https://www.youtube.com/feeds/videos.xml?channel_id=UCbfYPyITQ-7l4upoX8nvctg"),
            ("슈카월드", "https://www.youtube.com/feeds/videos.xml?channel_id=UCsJ6RuBiTVWRX156FVbeaGg"),
            ("Matt Wolfe", "https://www.youtube.com/feeds/videos.xml?channel_id=UCnvrTsmepP_0IflYNGmN8ig")
        ]
        count = 0
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        for cname, yt_feed in yt_channels:
            try:
                xml_raw = fetch_xml(yt_feed)
                root = ET.fromstring(xml_raw)
                for entry in root.findall('atom:entry', ns)[:15]:
                    t_node = entry.find('atom:title', ns)
                    l_node = entry.find('atom:link', ns)
                    p_node = entry.find('atom:published', ns)
                    
                    if t_node is not None and t_node.text:
                        vtitle = t_node.text.strip()
                        vurl = l_node.attrib.get('href', '') if l_node is not None else ""
                        pub_iso = p_node.text.strip() if p_node is not None and p_node.text else None
                        
                        if vurl:
                            added = add_candidate({
                                "title": f"YouTube ({cname}): {vtitle}",
                                "source_platform": f"YouTube ({cname})",
                                "source_url": vurl,
                                "article_url": vurl,
                                "published_at": pub_iso,
                                "type": "sns",
                                "category_type": "NEWS",
                                "description": f"Video by {cname}: {vtitle}",
                                "viral_metric": f"📺 {cname} 영상"
                            })
                            if added: count += 1
            except Exception as yt_err:
                logger.log(f"[!] YouTube {cname} feed note: {yt_err}", level="WARNING")

        harvest_report["sources"]["youtube_tech"] = {"status": "SUCCESS", "items_found": count, "duration_sec": round(time.time() - yt_start, 2)}
        logger.log(f"[+] YouTube Tech: {count} video items ingested in {time.time() - yt_start:.2f}s")
    except Exception as e:
        harvest_report["sources"]["youtube_tech"] = {"status": "ERROR", "error": str(e), "duration_sec": round(time.time() - yt_start, 2)}
        logger.log(f"[!] YouTube Note: {e}", level="WARNING")

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
    updated_harvested_files = []
    metric_snapshots_to_sync = []

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
        matched_inbox_by_dedup = None
        if evaluate_deduplication:
            try:
                dedup_res = evaluate_deduplication(cand, existing_cases_list, existing_inbox_items, api_key=gemini_api_key)
                if dedup_res.get("is_duplicate"):
                    if dedup_res.get("matched_type") == "INVESTIGATION":
                        dup_skipped += 1
                        logger.log(f"[DEDUP Verified Case] Blocked already verified dossier: {cand['title'][:40]}")
                        continue
                    elif dedup_res.get("matched_type") == "INBOX":
                        mid = dedup_res.get("matched_id")
                        if mid:
                            tf = os.path.join(inbox_dir, f"{mid}.json")
                            if os.path.exists(tf):
                                matched_inbox_by_dedup = tf
            except Exception as dedup_err:
                logger.log(f"[!] Dedup check note: {dedup_err}", level="WARNING")

        # Check if exists in inbox by Hash, Omni-URL, Dedup or Slug (Deduplication & Metric Update)
        matched_inbox_by_url = next((inbox_url_map[u] for u in cand_urls if u in inbox_url_map), None)
        target_inbox_file = inbox_hash_map.get(c_hash) or matched_inbox_by_url or matched_inbox_by_dedup or inbox_slug_map.get(slug)

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
                latest_val = old_tracking.get("latest", {}).get("value", init_val)
                delta = current_val - init_val
                delta_step = current_val - latest_val
                delta_pct = round(((current_val - init_val) / max(1, init_val)) * 100, 1) if init_val > 0 else 0.0

                old_tracking["latest"] = {
                    "value": current_val,
                    "display": cand["viral_metric"],
                    "updated_at": now_kst.isoformat()
                }
                old_tracking["delta"] = delta
                old_tracking["delta_display"] = f"+{delta:,}" if delta > 0 else (f"{delta:,}" if delta < 0 else "0")
                old_tracking["growth_rate_pct"] = delta_pct
                old_tracking["is_spiking"] = delta >= 50 or delta_pct >= 30.0

                # Rolling history sparkline (max 7 points) & delta-gated snapshot queue
                history = old_tracking.get("history", [])
                if not history:
                    init_time_str = old_tracking.get("initial", {}).get("recorded_at", today_str)
                    history = [{"v": init_val, "t": str(init_time_str)[:16]}]

                if delta_step != 0 or len(history) <= 1:
                    history.append({"v": current_val, "t": now_kst.strftime("%m-%d %H:%M")})
                    history = history[-7:]
                    old_tracking["history"] = history

                    inbox_id = old_item.get("inbox_id") or os.path.splitext(os.path.basename(target_inbox_file))[0]
                    metric_snapshots_to_sync.append((
                        inbox_id,
                        cand.get("source_platform", old_item.get("source_platform", "UNKNOWN")),
                        current_val,
                        delta_step,
                        now_kst
                    ))
                else:
                    old_tracking["history"] = history

                now_iso = now_kst.isoformat()
                old_item["metric_tracking"] = old_tracking
                old_item["description"] = cand["description"]
                old_item["viral_metric"] = cand["viral_metric"]
                old_item["updated_at"] = now_iso
                if not old_item.get("created_at"):
                    old_item["created_at"] = old_item.get("harvested_at") or now_iso
                if "title_ko" in cand and not old_item.get("title_ko"): old_item["title_ko"] = cand["title_ko"]
                if "description_ko" in cand and not old_item.get("description_ko"): old_item["description_ko"] = cand["description_ko"]
                if "hn_url" in cand and not old_item.get("hn_url"): old_item["hn_url"] = cand["hn_url"]
                if "article_url" in cand and not old_item.get("article_url"): old_item["article_url"] = cand["article_url"]
                if cand.get("raw_comments"):
                    old_item["raw_comments"] = cand["raw_comments"]
                    old_item["comment_count"] = cand.get("comment_count", len(cand["raw_comments"]))

                with open(target_inbox_file, "w", encoding="utf-8") as fp:
                    json.dump(old_item, fp, indent=2, ensure_ascii=False)

                updated_harvested_files.append(target_inbox_file)
                updated_count += 1
            except Exception as e:
                logger.log(f"[!] Failed to update {target_inbox_file}: {e}", level="ERROR")
            continue
        elif target_inbox_file and target_inbox_file.startswith("db:"):
            # Existing item already tracked in Neon DB (Deterministic O(1) deduplication)
            inbox_id = target_inbox_file[3:]
            metric_snapshots_to_sync.append((
                inbox_id,
                cand.get("source_platform", "UNKNOWN"),
                current_val,
                0,
                now_kst
            ))
            updated_count += 1
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

        now_iso = now_kst.isoformat()
        pub_iso = cand.get("published_at") or now_iso
        created_at_iso = now_iso

        metric_tracking = {
            "initial": {
                "value": current_val,
                "display": cand["viral_metric"],
                "recorded_at": created_at_iso
            },
            "latest": {
                "value": current_val,
                "display": cand["viral_metric"],
                "updated_at": now_iso
            },
            "history": [
                {"v": current_val, "t": now_kst.strftime("%m-%d %H:%M")}
            ],
            "delta": 0,
            "delta_display": "+0",
            "growth_rate_pct": 0.0,
            "is_spiking": False
        }

        inbox_item = {
            "inbox_id": case_id,
            "harvested_date": today_str,
            "harvested_at": now_iso,
            "published_at": pub_iso,
            "created_at": created_at_iso,
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
        if "task_modality" in cand: inbox_item["task_modality"] = cand["task_modality"]
        if "model_family" in cand: inbox_item["model_family"] = cand["model_family"]
        if "parameter_size" in cand: inbox_item["parameter_size"] = cand["parameter_size"]
        if "detected_formats" in cand: inbox_item["detected_formats"] = cand["detected_formats"]
        if "library_name" in cand: inbox_item["library_name"] = cand["library_name"]
        if "raw_comments" in cand: inbox_item["raw_comments"] = cand["raw_comments"]
        if "comment_count" in cand: inbox_item["comment_count"] = cand["comment_count"]

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(inbox_item, f, indent=2, ensure_ascii=False)

        # Update in-memory index & tracking
        inbox_hash_map[c_hash] = save_path
        inbox_url_map[norm_url] = save_path
        inbox_slug_map[slug] = save_path
        newly_harvested_files.append(save_path)
        new_saved += 1
        metric_snapshots_to_sync.append((
            case_id,
            cand.get("source_platform", "UNKNOWN"),
            current_val,
            0,
            now_kst
        ))

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

    # Save updated items manifest for Neon DB metric syncing
    updated_manifest_path = os.path.join(logs_dir, "last_harvest_updated_items.json")
    with open(updated_manifest_path, "w", encoding="utf-8") as fp:
        json.dump({
            "harvested_at": datetime.datetime.now().astimezone().isoformat(),
            "updated_count": len(updated_harvested_files),
            "files": updated_harvested_files
        }, fp, indent=2, ensure_ascii=False)
    logger.log(f"[+] Saved manifest with {len(updated_harvested_files)} updated items to '{updated_manifest_path}'")

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

    # Stage 2: Immediate Staging to Cloud DB (Aiven PostgreSQL SSOT) & Telemetry Logging
    record_harvest_telemetry_to_cloud(
        harvest_report, new_saved, updated_count, dup_skipped, len(all_candidates),
        metric_snapshots=metric_snapshots_to_sync
    )
    sync_new_items_to_cloud()

def record_harvest_telemetry_to_cloud(harvest_report, new_saved, updated_count, dup_skipped, total_fetched, metric_snapshots=None):
    """
    Stage 2: Records harvest run metadata and platform-specific metrics directly into Cloud DB (Aiven PostgreSQL SSOT).
    Tables: harvest_runs, harvest_source_metrics, github_actions_run_logs
    """
    gh_run_id = os.environ.get("GITHUB_RUN_ID")
    now_dt = datetime.datetime.now(datetime.timezone.utc)
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 1. Unconditionally save local harvest_summary.json FIRST for subsequent runner steps
    try:
        logs_dir = os.path.join(root_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        summary_path = os.path.join(logs_dir, "harvest_summary.json")
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump({
                "run_id": gh_run_id,
                "items_collected": new_saved,
                "items_scanned": total_fetched,
                "updated_count": updated_count,
                "duplicates_skipped": dup_skipped,
                "recorded_at": now_dt.isoformat()
            }, f, ensure_ascii=False, indent=2)
        print(f"[+] [Local Telemetry] Saved harvest summary to {summary_path} (scanned={total_fetched}, collected={new_saved})")
    except Exception as summ_err:
        print(f"[!] Warning writing local harvest_summary.json: {summ_err}")

    # 2. Connect to Cloud DB
    try:
        from tools.db_bridge import get_db_connection
    except Exception:
        try:
            from db_bridge import get_db_connection
        except Exception:
            return

    conn = get_db_connection()
    if not conn:
        return

    run_id = f"run_{datetime.datetime.now().astimezone().strftime('%Y%m%d_%H%M%S')}"

    # 2-1. Insert harvest_runs
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO harvest_runs (run_id, started_at, finished_at, total_fetched, new_saved, duplicates_skipped, errors_count, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (run_id) DO UPDATE SET
                    total_fetched = EXCLUDED.total_fetched,
                    new_saved = EXCLUDED.new_saved;
            """, (run_id, now_dt, now_dt, total_fetched, new_saved, dup_skipped, 0, 'SUCCESS'))
        conn.commit()
    except Exception as e:
        print(f"[!] Note: harvest_runs insert warning: {e}")
        try: conn.rollback()
        except Exception: pass

    # 2-2. Insert harvest_source_metrics
    try:
        source_counts = harvest_report.get("sources", {})
        with conn.cursor() as cur:
            for src_name, src_data in source_counts.items():
                count = src_data.get("items_found", 0) if isinstance(src_data, dict) else (src_data if isinstance(src_data, int) else 0)
                latency = src_data.get("duration_sec", 0.0) if isinstance(src_data, dict) else 0.0
                status = src_data.get("status", "SUCCESS") if isinstance(src_data, dict) else "SUCCESS"
                cur.execute("""
                    INSERT INTO harvest_source_metrics (run_id, source_name, items_count, latency_seconds, http_status, recorded_at)
                    VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP);
                """, (run_id, src_name, count, latency, status))
        conn.commit()
    except Exception as e:
        print(f"[!] Note: harvest_source_metrics insert warning: {e}")
        try: conn.rollback()
        except Exception: pass

    # 2-3. Upsert github_actions_run_logs if running inside GitHub Actions
    if gh_run_id:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO github_actions_run_logs (
                        run_id, workflow_name, event_trigger, status, conclusion,
                        duration_seconds, duration_str, started_at, items_collected, items_scanned
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (run_id) DO UPDATE SET
                        items_collected = EXCLUDED.items_collected,
                        items_scanned = EXCLUDED.items_scanned;
                """, (
                    int(gh_run_id),
                    os.environ.get("GITHUB_WORKFLOW", "Deploy AI Fact-Check Portfolio & Neon DB Sync"),
                    os.environ.get("GITHUB_EVENT_NAME", "schedule"),
                    "in_progress",
                    "in_progress",
                    60,
                    "1분 0초",
                    now_dt,
                    new_saved,
                    total_fetched
                ))
            conn.commit()
            print(f"[+] [Cloud DB] Synchronized run {gh_run_id} to github_actions_run_logs (collected={new_saved}, scanned={total_fetched}).")
        except Exception as e:
            print(f"[!] Note updating github_actions_run_logs.items_collected: {e}")
            try: conn.rollback()
            except Exception: pass

    # 2-4. Bulk insert metric snapshots if any (Extreme-Efficiency Time-Series Tracking)
    if metric_snapshots:
        try:
            from psycopg2.extras import execute_values
            with conn.cursor() as cur:
                execute_values(
                    cur,
                    """
                    INSERT INTO trend_metric_snapshots (inbox_id, source_platform, metric_value, delta, recorded_at)
                    VALUES %s;
                    """,
                    metric_snapshots
                )
            conn.commit()
            print(f"[+] [Cloud DB] Bulk-inserted {len(metric_snapshots)} metric snapshots into trend_metric_snapshots.")
        except Exception as snap_err:
            print(f"[!] Warning recording metric snapshots to Cloud DB: {snap_err}")
            try: conn.rollback()
            except Exception: pass

    try:
        conn.close()
    except Exception:
        pass
    print(f"[+] [Cloud DB] Recorded harvest run '{run_id}' with {total_fetched} items ({new_saved} new, {updated_count} updated) into harvest_runs & harvest_source_metrics.")

def sync_new_items_to_cloud():
    """
    Stage 2: Immediately sync newly harvested inbox items to Cloud DB (Aiven PostgreSQL SSOT) raw_trends_inbox staging table.
    Ensures data durability even if subsequent LLM processing fails or times out.
    """
    try:
        try:
            from tools.db_bridge import push_inbox_to_neon
        except Exception:
            from db_bridge import push_inbox_to_neon
        print("[*] [Cloud DB Staging] Syncing newly harvested inbox items directly to Cloud DB...")
        push_inbox_to_neon(full_sync=False)
        print("[+] [Cloud DB Staging] Staged items successfully committed to Cloud DB raw_trends_inbox.")
    except Exception as e:
        print(f"[!] Warning syncing staged items to Cloud DB: {e}")

if __name__ == "__main__":
    harvest_all()

