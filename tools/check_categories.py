import os
import json

inv_dir = "investigations"
cases = os.listdir(inv_dir)
print(f"Total investigation directories: {len(cases)}")
for c in sorted(cases):
    p = os.path.join(inv_dir, c, "metadata.json")
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            m = json.load(f)
            title = m.get("title", "")
            cat = m.get("category", "")
            cluster = m.get("clustering", {}).get("cluster_id", "")
            print(f"[{c}] -> Cat: '{cat}' | Cluster: '{cluster}' | Title: '{title[:35]}...'")
    else:
        print(f"[!] MISSING metadata: {c}")
