#!/usr/bin/env python3
"""
Multi-Source Trend Harvester & Deduplication Gate (2026 SOTA Framework)
Hacker News, Hugging Face, Reddit, GitHub에서 비로그인으로 최신 AI 트렌드를 수집하여 inbox/에 중복 없이 안전 보관합니다.
(사용자가 승인하기 전까지는 절대 공식 포트폴리오로 승격되지 않습니다)
"""

import datetime
import json
import os
import re
import sys
import urllib.request
import urllib.parse

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
    return text[:40]

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

    # 3. Rejected
    rej_dir = os.path.join(base_dir, "inbox", "_rejected")
    if os.path.exists(rej_dir):
        for f in os.listdir(rej_dir):
            existing.add(f.replace(".json", "").lower())

    return existing

def fetch_json(url, headers=None):
    if headers is None:
        headers = {"User-Agent": "FactCheck-Harvester/2026.1 (Academic/Portfolio Research)"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"[!] Warning: Fetch failed for {url}: {e}")
        return None

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

def harvest():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    inbox_dir = os.path.join(base_dir, "inbox")
    os.makedirs(inbox_dir, exist_ok=True)
    
    # Load Persona Config
    persona_path = os.path.join(base_dir, "configs", "user_persona_alignment.json")
    persona_config = {}
    if os.path.exists(persona_path):
        with open(persona_path, "r", encoding="utf-8") as f:
            persona_config = json.load(f)

    existing_set = get_existing_ids(base_dir)
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    
    candidates = []

    print("[*] 1. Harvesting from Hugging Face Trending Models API...")
    hf_data = fetch_json("https://huggingface.co/api/models?sort=trendingScore&direction=-1&limit=10")
    if hf_data and isinstance(hf_data, list):
        for item in hf_data:
            model_id = item.get("id", "")
            url = f"https://huggingface.co/{model_id}"
            if model_id and url.lower() not in existing_set:
                candidates.append({
                    "title": f"HuggingFace Trending: {model_id}",
                    "source_platform": "Hugging Face Hub",
                    "source_url": url,
                    "type": "repo",
                    "description": f"Trending score: {item.get('trendingScore', 0)}, downloads: {item.get('downloads', 0)}",
                    "viral_metric": f"Trending Score {item.get('trendingScore', 0)}"
                })

    print("[*] 2. Harvesting from Hacker News API (Top AI/Dev stories)...")
    hn_top_ids = fetch_json("https://hacker-news.firebaseio.com/v0/topstories.json")
    if hn_top_ids and isinstance(hn_top_ids, list):
        for story_id in hn_top_ids[:15]:
            story = fetch_json(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
            if story and "title" in story:
                title = story.get("title", "")
                url = story.get("url", f"https://news.ycombinator.com/item?id={story_id}")
                # Filter AI/Dev topics
                if any(kw in title.lower() for kw in ["ai", "llm", "agent", "rust", "python", "model", "rag", "open-source", "show hn"]):
                    if url.lower() not in existing_set:
                        candidates.append({
                            "title": f"Hacker News: {title}",
                            "source_platform": "Hacker News",
                            "source_url": url,
                            "type": "repo" if "github.com" in url else "sns",
                            "description": f"HN Score: {story.get('score', 0)} points, {story.get('descendants', 0)} comments",
                            "viral_metric": f"Score {story.get('score', 0)} pts"
                        })

    print("[*] 3. Harvesting from Reddit r/LocalLLaMA Hot API...")
    reddit_data = fetch_json("https://www.reddit.com/r/LocalLLaMA/hot.json?limit=10")
    if reddit_data and "data" in reddit_data and "children" in reddit_data["data"]:
        for post in reddit_data["data"]["children"]:
            pdata = post.get("data", {})
            title = pdata.get("title", "")
            url = f"https://reddit.com{pdata.get('permalink', '')}"
            if not pdata.get("stickied", False) and url.lower() not in existing_set:
                candidates.append({
                    "title": f"Reddit LocalLLaMA: {title}",
                    "source_platform": "Reddit r/LocalLLaMA",
                    "source_url": url,
                    "type": "sns",
                    "description": f"Upvotes: {pdata.get('score', 0)}, Comments: {pdata.get('num_comments', 0)}",
                    "viral_metric": f"{pdata.get('score', 0)} Upvotes"
                })

    # Save unique new candidates to inbox/
    new_saved = 0
    for cand in candidates:
        slug = slugify(cand["title"])
        case_id = f"{today_str}_{cand['type']}_{slug}"
        if case_id.lower() in existing_set:
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
            "status": "PENDING_REVIEW",
            "promotion_guide": f"Run 'python tools/triage.py --promote {case_id}' to elevate to portfolio"
        }

        save_path = os.path.join(inbox_dir, f"{case_id}.json")
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(inbox_item, f, indent=2, ensure_ascii=False)
        existing_set.add(case_id.lower())
        new_saved += 1

    print(f"\n[+] Harvesting Complete! {new_saved} new trending candidates saved to inbox/")
    print(f"[*] View pending candidates: python tools/triage.py --list")

if __name__ == "__main__":
    harvest()
