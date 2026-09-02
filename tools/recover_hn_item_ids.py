#!/usr/bin/env python3
"""
Recovers exact Hacker News Story IDs using HN Algolia Search API.
Fixes all generic 'https://news.ycombinator.com' links in inbox/
to point to the exact 'https://news.ycombinator.com/item?id={sid}' thread.
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

# Ensure UTF-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "FactCheck-Recovery/1.0"})
    with urllib.request.urlopen(req, timeout=10) as res:
        return json.loads(res.read().decode('utf-8'))

def recover_all_hn_ids():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    inbox_dir = os.path.join(base_dir, "inbox")
    if not os.path.exists(inbox_dir): return

    files = [f for f in os.listdir(inbox_dir) if f.endswith(".json") and not f.startswith("_")]
    print(f"[*] Scanning {len(files)} inbox files for Hacker News items...")

    recovered_count = 0

    for f in files:
        path = os.path.join(inbox_dir, f)
        try:
            with open(path, "r", encoding="utf-8") as fp:
                item = json.load(fp)

            is_hn = "Hacker News" in item.get("source_platform", "") or "hacker_news" in f
            if not is_hn: continue

            hn_url = item.get("hn_url", "")
            # Check if it lacks a valid item?id=\d+
            has_valid_id = bool(re.search(r'item\?id=\d+', hn_url))

            if not has_valid_id:
                # Need recovery! Extract title
                raw_title = item.get("title", "").replace("Hacker News:", "").strip()
                print(f"[*] Searching Algolia for: '{raw_title}'...")

                query_url = f"https://hn.algolia.com/api/v1/search?query={urllib.parse.quote(raw_title)}&tags=story"
                data = fetch_json(query_url)
                hits = data.get("hits", [])

                if hits:
                    best_hit = None
                    # Find exact title match or first hit
                    for h in hits:
                        if h.get("title", "").strip().lower() == raw_title.lower():
                            best_hit = h
                            break
                    if not best_hit:
                        best_hit = hits[0]

                    real_id = best_hit.get("objectID")
                    real_hn_url = f"https://news.ycombinator.com/item?id={real_id}"
                    real_article_url = best_hit.get("url") or real_hn_url

                    item["hn_id"] = str(real_id)
                    item["hn_url"] = real_hn_url
                    item["source_url"] = real_hn_url
                    if not item.get("article_url") or item.get("article_url") == "https://news.ycombinator.com":
                        item["article_url"] = real_article_url

                    with open(path, "w", encoding="utf-8") as fp:
                        json.dump(item, fp, indent=2, ensure_ascii=False)

                    recovered_count += 1
                    print(f"    [+] Recovered {f} -> ID: {real_id} ({real_hn_url})")
                    time.sleep(0.3)
                else:
                    print(f"    [-] No hit for '{raw_title}'")

        except Exception as e:
            print(f"[!] Error on {f}: {e}")

    print(f"\n=======================================================")
    print(f"🎯 Recovery Finished: {recovered_count} HN items linked to exact discussion threads!")
    print(f"=======================================================\n")

if __name__ == "__main__":
    recover_all_hn_ids()
