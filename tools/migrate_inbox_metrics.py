#!/usr/bin/env python3
"""
Migrates existing inbox files to support initial vs latest metric tracking.
Tracks:
- initial: value, display, recorded_at (created_at)
- latest: value, display, updated_at
- delta: numeric change
- delta_display: '+N' string
- growth_rate_pct: percentage change
"""

import json
import os
import re
import sys

def extract_metric_number(text):
    if not text: return 0
    # Match patterns like 773, 1,200, 15.4k, 250
    m_k = re.search(r'([\d\.]+)\s*[kK]', text)
    if m_k:
        try:
            return int(float(m_k.group(1)) * 1000)
        except Exception:
            pass
    
    m_num = re.search(r'([\d,]+)', text)
    if m_num:
        try:
            return int(m_num.group(1).replace(',', ''))
        except Exception:
            pass
    return 0

def migrate_inbox():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    inbox_dir = os.path.join(base_dir, "inbox")
    if not os.path.exists(inbox_dir): return

    count = 0
    for f in os.listdir(inbox_dir):
        if f.endswith(".json"):
            path = os.path.join(inbox_dir, f)
            try:
                with open(path, "r", encoding="utf-8") as fp:
                    item = json.load(fp)

                created_at = item.get("harvested_date", "2026-08-31")
                updated_at = item.get("last_synced_at", created_at)
                viral_str = item.get("viral_metric", "")

                num_val = extract_metric_number(viral_str)
                
                # Check if already has metric_tracking
                if "metric_tracking" not in item:
                    item["metric_tracking"] = {
                        "initial": {
                            "value": num_val,
                            "display": viral_str,
                            "recorded_at": created_at
                        },
                        "latest": {
                            "value": num_val,
                            "display": viral_str,
                            "updated_at": updated_at
                        },
                        "delta": 0,
                        "delta_display": "+0",
                        "growth_rate_pct": 0.0,
                        "is_spiking": False
                    }
                    item["created_at"] = created_at
                    item["updated_at"] = updated_at

                    with open(path, "w", encoding="utf-8") as fp:
                        json.dump(item, fp, indent=2, ensure_ascii=False)
                    count += 1
            except Exception as e:
                print(f"[!] Error migrating {f}: {e}")

    print(f"[+] Successfully migrated {count} inbox items with initial vs latest metric tracking.")

if __name__ == "__main__":
    migrate_inbox()
