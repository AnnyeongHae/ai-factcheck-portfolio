#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/verify_hf_spaces.py
Directly verifies and synchronizes live likes for all Hugging Face Spaces in inbox.
"""

import os
import glob
import json
import time
import urllib.request

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
inbox_dir = os.path.join(ROOT_DIR, "inbox")

files = glob.glob(os.path.join(inbox_dir, "*space*.json"))
print(f"[*] Starting live verification for {len(files)} Hugging Face Spaces in inbox...")

updated = 0
results = []

for fp in sorted(files):
    try:
        with open(fp, "r", encoding="utf-8") as f:
            item = json.load(f)
        s_url = item.get("source_url", "")
        if "huggingface.co/spaces/" not in s_url:
            continue
        sid = s_url.split("huggingface.co/spaces/")[1].strip("/")
        api_url = f"https://huggingface.co/api/spaces/{sid}"
        req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        
        live_likes = data.get("likes", 0)
        sdk = data.get("sdk", "gradio")
        old_val = item.get("metric_tracking", {}).get("latest", {}).get("value", 0)
        
        diff = live_likes - old_val
        results.append({
            "sid": sid,
            "old": old_val,
            "live": live_likes,
            "diff": diff
        })

        if old_val != live_likes:
            print(f"[*] Space '{sid}': {old_val} -> {live_likes} ({'+' if diff > 0 else ''}{diff})")
            init_val = item.get("metric_tracking", {}).get("initial", {}).get("value", live_likes)
            delta = live_likes - init_val
            delta_pct = round((delta / max(1, init_val)) * 100, 1) if init_val > 0 else 0.0
            
            item["viral_metric"] = f"❤️ {live_likes} Likes (Trending Demo)"
            item["description"] = f"Interactive AI Demo (SDK: {sdk}) | Likes: {live_likes} | Live URL: {s_url}"
            item["metric_tracking"] = {
                "initial": item.get("metric_tracking", {}).get("initial", {
                    "value": live_likes,
                    "display": f"❤️ {live_likes} Likes (Trending Demo)",
                    "recorded_at": item.get("harvested_date", "2026-09-03")
                }),
                "latest": {
                    "value": live_likes,
                    "display": f"❤️ {live_likes} Likes (Trending Demo)",
                    "updated_at": "2026-09-03"
                },
                "delta": delta,
                "delta_display": f"+{delta:,}" if delta > 0 else f"{delta:,}",
                "growth_rate_pct": delta_pct,
                "is_spiking": delta >= 50 or delta_pct >= 30.0
            }
            with open(fp, "w", encoding="utf-8") as f:
                json.dump(item, f, ensure_ascii=False, indent=2)
            updated += 1
    except Exception as e:
        print(f"[-] Error for {fp}: {e}")
    time.sleep(0.05)

print(f"\n[+] Space Verification Complete! {updated}/{len(files)} items updated with live metrics.")
