import os
import gzip
import json
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def fetch_unclassified_batch(batch_size=10, output_path="temp_batch_input.json", mod_rem=None, mod_div=None, order_asc=False):
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL not found in .env")

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    order_dir = "ASC" if order_asc else "DESC"

    if mod_rem is not None and mod_div is not None:
        query = f"""
            SELECT r.id, r.inbox_id, r.title, r.source_platform, r.source_url,
                   r.raw_payload->>'description' as desc,
                   r.raw_payload->'community_feedback' as feedback,
                   v.full_text_gzip
            FROM raw_trends_inbox r
            LEFT JOIN raw_content_vault v ON r.inbox_id = v.inbox_id
            WHERE r.is_classified = FALSE AND (r.id %% %s = %s)
            ORDER BY r.id {order_dir}
            LIMIT %s;
        """
        cur.execute(query, (mod_div, mod_rem, batch_size))
    else:
        query = f"""
            SELECT r.id, r.inbox_id, r.title, r.source_platform, r.source_url,
                   r.raw_payload->>'description' as desc,
                   r.raw_payload->'community_feedback' as feedback,
                   v.full_text_gzip
            FROM raw_trends_inbox r
            LEFT JOIN raw_content_vault v ON r.inbox_id = v.inbox_id
            WHERE r.is_classified = FALSE
            ORDER BY r.id {order_dir}
            LIMIT %s;
        """
        cur.execute(query, (batch_size,))
    rows = cur.fetchall()

    batch = []
    for row in rows:
        r_id, inbox_id, title, platform, url, desc, feedback, vault_gzip = row

        body_text = ""
        if vault_gzip:
            try:
                body_text = gzip.decompress(bytes(vault_gzip)).decode("utf-8", errors="replace")[:1000]
            except Exception as e:
                body_text = ""
        
        if not body_text and desc:
            body_text = desc[:1000]

        batch.append({
            "db_id": r_id,
            "inbox_id": inbox_id,
            "title": title,
            "source_platform": platform,
            "source_url": url,
            "body_excerpt": body_text.strip(),
            "community_feedback": feedback or {}
        })

    conn.close()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(batch, f, indent=2, ensure_ascii=False)

    print(f"[*] Fetched {len(batch)} candidate items into {output_path}")
    return batch

if __name__ == "__main__":
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    out = sys.argv[2] if len(sys.argv) > 2 else "temp_batch_input.json"
    mod_rem = int(sys.argv[3]) if len(sys.argv) > 3 else None
    mod_div = int(sys.argv[4]) if len(sys.argv) > 4 else None
    order_asc = len(sys.argv) > 5 and sys.argv[5].lower() in ("asc", "true", "1")
    fetch_unclassified_batch(limit, out, mod_rem, mod_div, order_asc)
