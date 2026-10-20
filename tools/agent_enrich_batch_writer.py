import os
import json
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def apply_batch(input_json_path):
    with open(input_json_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL not found in .env")

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    updated = 0
    for item in items:
        db_id = item.get("db_id")
        if not db_id:
            print(f"[!] Skipping invalid item (no db_id): {item}")
            continue

        category_primary = item.get("category_primary") or item.get("category") or "FOUNDATION_MODELS"
        ai_enrichment = item.get("ai_enrichment")

        if not ai_enrichment:
            # Flattened format support
            t_ko = item.get("title_ko", "")
            t_en = item.get("title_en", "")
            t_zh = item.get("title_zh", "")
            h_ko = item.get("hook_ko", "")
            h_en = item.get("hook_en", "")
            h_zh = item.get("hook_zh", "")
            model = item.get("enriched_by_model", "google/gemini-3.6-flash")

            ai_enrichment = {
                "category_primary": category_primary,
                "enriched_by_model": model,
                "korean_title": t_ko,
                "hook": h_ko,
                "multilingual": {
                    "ko": {"title": t_ko, "hook": h_ko},
                    "en": {"title": t_en, "hook": h_en},
                    "zh": {"title": t_zh, "hook": h_zh}
                }
            }
        else:
            multi = ai_enrichment.get("multilingual", {})
            t_ko = multi.get("ko", {}).get("title") or ai_enrichment.get("korean_title", "")
            t_en = multi.get("en", {}).get("title", "")
            t_zh = multi.get("zh", {}).get("title", "")

            h_ko = multi.get("ko", {}).get("hook") or ai_enrichment.get("hook", "")
            h_en = multi.get("en", {}).get("hook", "")
            h_zh = multi.get("zh", {}).get("hook", "")

        query = """
            UPDATE raw_trends_inbox
            SET is_classified = TRUE,
                category_primary = %s,
                raw_payload = COALESCE(raw_payload, '{}'::jsonb) || jsonb_build_object(
                    'title_ko', %s::text,
                    'title_en', %s::text,
                    'title_zh', %s::text,
                    'hook', %s::text,
                    'hook_ko', %s::text,
                    'hook_en', %s::text,
                    'hook_zh', %s::text,
                    'source_lang', %s::text,
                    'ai_enrichment', %s::jsonb
                ),
                updated_at = NOW()
            WHERE id = %s;
        """
        src_lang = ai_enrichment.get("source_lang", "EN")
        cur.execute(query, (
            category_primary,
            t_ko, t_en, t_zh,
            h_ko, h_ko, h_en, h_zh,
            src_lang,
            json.dumps(ai_enrichment, ensure_ascii=False),
            db_id
        ))
        updated += 1

    conn.commit()
    conn.close()
    print(f"[SUCCESS] Successfully committed {updated} rows into PostgreSQL SSOT.")
    return updated

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "temp_batch_output.json"
    apply_batch(path)
