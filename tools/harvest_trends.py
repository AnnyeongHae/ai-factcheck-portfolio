#!/usr/bin/env python3
"""
Multi-Source Enterprise Trend Harvester & Health Monitor (2026 SOTA Framework - v4.0)
GitHub, Hugging Face, Hacker News, ArXiv, Reddit 등에서 대량의 최신 AI 트렌드를 수집하고,
모든 수집 시도/성공/실패/에러 내역을 logs/에 정밀 기록하여 시스템 상태를 실시간 감시합니다.
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

def get_existing_ids(base_dir):
    existing = set()
    
    # 1. Investigations
    inv_dir = os.path.join(base_dir, "investigations")
    if os.path.exists(inv_dir):
        for d in os.listdir(inv_dir):
            existing.add(d.lower())
            meta_path = os.path.join(inv_dir, d, "metadata.json")
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        m = json.load(f)
                        if "target_repo" in m: existing.add(m["target_repo"].lower())
                        if "source_url" in m: existing.add(m["source_url"].lower())
                except Exception:
                    pass

    # 2. Inbox
    inbox_dir = os.path.join(base_dir, "inbox")
    if os.path.exists(inbox_dir):
        for f in os.listdir(inbox_dir):
            if f.endswith(".json"):
                existing.add(f.replace(".json", "").lower())
                try:
                    with open(os.path.join(inbox_dir, f), "r", encoding="utf-8") as fp:
                        m = json.load(fp)
                        if "source_url" in m: existing.add(m["source_url"].lower())
                except Exception:
                    pass

    # 3. Promoted Archive
    p_dir = os.path.join(base_dir, "inbox", "_promoted")
    if os.path.exists(p_dir):
        for f in os.listdir(p_dir):
            if f.endswith(".json"):
                existing.add(f.replace(".json", "").lower())

    # 4. Rejected Archive
    rej_dir = os.path.join(base_dir, "inbox", "_rejected")
    if os.path.exists(rej_dir):
        for f in os.listdir(rej_dir):
            if f.endswith(".json"):
                existing.add(f.replace(".json", "").lower())

    return existing

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
    logger.log("🚀 Multi-Source Trend Harvester Job Started")
    logger.log("=======================================================")

    # Load Persona
    persona_path = os.path.join(base_dir, "configs", "user_persona_alignment.json")
    persona_config = {}
    if os.path.exists(persona_path):
        with open(persona_path, "r", encoding="utf-8") as f:
            persona_config = json.load(f)

    existing_set = get_existing_ids(base_dir)
    logger.log(f"[*] Loaded {len(existing_set)} existing IDs to guarantee 100% deduplication.")

    harvest_report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "date": today_str,
        "sources": {},
        "summary": {"total_fetched": 0, "new_saved": 0, "duplicates_skipped": 0, "errors": 0}
    }

    all_candidates = []

    # 1. Hugging Face Trending
    hf_start = time.time()
    try:
        logger.log("[*] Fetching Hugging Face Trending Models (limit=30)...")
        hf_data = fetch_json("https://huggingface.co/api/models?sort=trendingScore&direction=-1&limit=30")
        count = 0
        if hf_data and isinstance(hf_data, list):
            for item in hf_data:
                mid = item.get("id", "")
                url = f"https://huggingface.co/{mid}"
                if mid and url.lower() not in existing_set:
                    all_candidates.append({
                        "title": f"HuggingFace: {mid}",
                        "source_platform": "Hugging Face Hub",
                        "source_url": url,
                        "type": "repo",
                        "description": f"Trending Score: {item.get('trendingScore', 0)}, Downloads: {item.get('downloads', 0)}, Pipeline: {item.get('pipeline_tag', 'N/A')}",
                        "viral_metric": f"Trending {item.get('trendingScore', 0)} pts"
                    })
                    count += 1
        harvest_report["sources"]["huggingface"] = {"status": "SUCCESS", "items_found": count, "duration_sec": round(time.time() - hf_start, 2)}
        logger.log(f"[+] Hugging Face: {count} new items extracted in {time.time() - hf_start:.2f}s")
    except Exception as e:
        harvest_report["sources"]["huggingface"] = {"status": "ERROR", "error": str(e), "duration_sec": round(time.time() - hf_start, 2)}
        logger.log(f"[!] Hugging Face Failed: {e}", level="ERROR")
        harvest_report["summary"]["errors"] += 1

    # 2. GitHub Search API (High Velocity Repos)
    gh_start = time.time()
    try:
        logger.log("[*] Fetching GitHub High-Velocity Repositories (Stars > 50, Recent 14 days)...")
        # 14 days ago
        fourteen_days_ago = (datetime.date.today() - datetime.timedelta(days=14)).strftime("%Y-%m-%d")
        gh_url = f"https://api.github.com/search/repositories?q=created:>{fourteen_days_ago}+stars:>30&sort=stars&order=desc&per_page=30"
        gh_data = fetch_json(gh_url, headers={"User-Agent": "FactCheck-Harvester/1.0", "Accept": "application/vnd.github.v3+json"})
        count = 0
        if gh_data and "items" in gh_data:
            for item in gh_data["items"]:
                rname = item.get("full_name", "")
                url = item.get("html_url", "")
                desc = item.get("description", "") or "No description"
                if rname and url.lower() not in existing_set:
                    all_candidates.append({
                        "title": f"GitHub: {rname}",
                        "source_platform": "GitHub Official",
                        "source_url": url,
                        "type": "repo",
                        "description": f"Stars: {item.get('stargazers_count', 0)}, Forks: {item.get('forks_count', 0)} | {desc}",
                        "viral_metric": f"★ {item.get('stargazers_count', 0)} Stars"
                    })
                    count += 1
        harvest_report["sources"]["github"] = {"status": "SUCCESS", "items_found": count, "duration_sec": round(time.time() - gh_start, 2)}
        logger.log(f"[+] GitHub Search: {count} new items extracted in {time.time() - gh_start:.2f}s")
    except Exception as e:
        harvest_report["sources"]["github"] = {"status": "ERROR", "error": str(e), "duration_sec": round(time.time() - gh_start, 2)}
        logger.log(f"[!] GitHub Search Failed: {e}", level="ERROR")
        harvest_report["summary"]["errors"] += 1

    # 3. Hacker News API
    hn_start = time.time()
    try:
        logger.log("[*] Fetching Hacker News Top Stories (limit=30)...")
        hn_top_ids = fetch_json("https://hacker-news.firebaseio.com/v0/topstories.json")
        count = 0
        if hn_top_ids and isinstance(hn_top_ids, list):
            for sid in hn_top_ids[:30]:
                story = fetch_json(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
                if story and "title" in story:
                    title = story.get("title", "")
                    url = story.get("url", f"https://news.ycombinator.com/item?id={sid}")
                    if any(kw in title.lower() for kw in ["ai", "llm", "agent", "rust", "python", "model", "rag", "open-source", "show hn", "bench", "eval"]):
                        if url.lower() not in existing_set:
                            all_candidates.append({
                                "title": f"Hacker News: {title}",
                                "source_platform": "Hacker News",
                                "source_url": url,
                                "type": "repo" if "github.com" in url else "sns",
                                "description": f"HN Score: {story.get('score', 0)} pts, Comments: {story.get('descendants', 0)}",
                                "viral_metric": f"{story.get('score', 0)} HN Points"
                            })
                            count += 1
        harvest_report["sources"]["hacker_news"] = {"status": "SUCCESS", "items_found": count, "duration_sec": round(time.time() - hn_start, 2)}
        logger.log(f"[+] Hacker News: {count} new items extracted in {time.time() - hn_start:.2f}s")
    except Exception as e:
        harvest_report["sources"]["hacker_news"] = {"status": "ERROR", "error": str(e), "duration_sec": round(time.time() - hn_start, 2)}
        logger.log(f"[!] Hacker News Failed: {e}", level="ERROR")
        harvest_report["summary"]["errors"] += 1

    # 4. ArXiv API (cs.AI & cs.CL)
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
                if url.lower() not in existing_set:
                    all_candidates.append({
                        "title": f"ArXiv: {title}",
                        "source_platform": "ArXiv Preprint",
                        "source_url": url,
                        "type": "repo",
                        "description": f"Abstract: {summary}...",
                        "viral_metric": "ArXiv Primary Paper"
                    })
                    count += 1
        harvest_report["sources"]["arxiv"] = {"status": "SUCCESS", "items_found": count, "duration_sec": round(time.time() - arxiv_start, 2)}
        logger.log(f"[+] ArXiv: {count} new items extracted in {time.time() - arxiv_start:.2f}s")
    except Exception as e:
        harvest_report["sources"]["arxiv"] = {"status": "ERROR", "error": str(e), "duration_sec": round(time.time() - arxiv_start, 2)}
        logger.log(f"[!] ArXiv Failed: {e}", level="ERROR")
        harvest_report["summary"]["errors"] += 1

    # 5. Reddit r/LocalLLaMA
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
                if not pdata.get("stickied", False) and url.lower() not in existing_set:
                    all_candidates.append({
                        "title": f"Reddit: {title}",
                        "source_platform": "Reddit r/LocalLLaMA",
                        "source_url": url,
                        "type": "sns",
                        "description": f"Upvotes: {pdata.get('score', 0)}, Comments: {pdata.get('num_comments', 0)}",
                        "viral_metric": f"{pdata.get('score', 0)} Upvotes"
                    })
                    count += 1
        harvest_report["sources"]["reddit"] = {"status": "SUCCESS", "items_found": count, "duration_sec": round(time.time() - reddit_start, 2)}
        logger.log(f"[+] Reddit: {count} new items extracted in {time.time() - reddit_start:.2f}s")
    except Exception as e:
        harvest_report["sources"]["reddit"] = {"status": "ERROR", "error": str(e), "duration_sec": round(time.time() - reddit_start, 2)}
        logger.log(f"[!] Reddit Note (403/Blocked handled gracefully): {e}", level="WARNING")

    # Deduplicate and save into inbox/
    new_saved = 0
    dup_skipped = 0
    for cand in all_candidates:
        slug = slugify(cand["title"])
        case_id = f"{today_str}_{cand['type']}_{slug}"
        if case_id.lower() in existing_set:
            dup_skipped += 1
            continue

        matched_domains = match_persona_domain(cand["title"], cand["description"], persona_config)

        inbox_item = {
            "inbox_id": case_id,
            "harvested_date": today_str,
            "title": cand["title"],
            "source_platform": cand["source_platform"],
            "source_url": cand["source_url"],
            "type": cand["type"],
            "description": cand["description"],
            "viral_metric": cand["viral_metric"],
            "matched_user_domains": matched_domains,
            "status": "PENDING_REVIEW"
        }

        save_path = os.path.join(inbox_dir, f"{case_id}.json")
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(inbox_item, f, indent=2, ensure_ascii=False)
        existing_set.add(case_id.lower())
        new_saved += 1

    harvest_report["summary"]["total_fetched"] = len(all_candidates)
    harvest_report["summary"]["new_saved"] = new_saved
    harvest_report["summary"]["duplicates_skipped"] = dup_skipped

    logger.log(f"=======================================================")
    logger.log(f"🎯 Harvester Finished: {new_saved} new items saved, {dup_skipped} duplicates skipped.")
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
    history = history[:30] # Keep last 30 runs

    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    logger.log(f"[+] Harvest history and health log saved to {history_file}")

if __name__ == "__main__":
    harvest_all()
