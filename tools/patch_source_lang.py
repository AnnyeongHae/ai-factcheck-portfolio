import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def main():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    conn.autocommit = True
    cur = conn.cursor()

    # 1. Update Korean items
    sql_ko = """
    UPDATE raw_trends_inbox
    SET raw_payload = jsonb_set(
        raw_payload,
        '{ai_enrichment,source_lang}',
        '"KO"'
    )
    WHERE (title ~ '[가-힣]' OR source_platform ILIKE '%daum%' OR source_platform ILIKE '%geeknews%')
      AND raw_payload ? 'ai_enrichment'
      AND COALESCE(raw_payload->'ai_enrichment'->>'source_lang', '') != 'KO';
    """
    cur.execute(sql_ko)
    print(f"[*] Updated Korean items: {cur.rowcount}")

    # Also update payload top-level source_lang if present
    sql_ko_top = """
    UPDATE raw_trends_inbox
    SET raw_payload = jsonb_set(
        raw_payload,
        '{source_lang}',
        '"KO"'
    )
    WHERE (title ~ '[가-힣]' OR source_platform ILIKE '%daum%' OR source_platform ILIKE '%geeknews%')
      AND (raw_payload ? 'source_lang')
      AND COALESCE(raw_payload->>'source_lang', '') != 'KO';
    """
    cur.execute(sql_ko_top)
    print(f"[*] Updated Korean top-level source_lang items: {cur.rowcount}")

    # 2. Update Chinese items
    sql_zh = """
    UPDATE raw_trends_inbox
    SET raw_payload = jsonb_set(
        raw_payload,
        '{ai_enrichment,source_lang}',
        '"ZH"'
    )
    WHERE (title ~ '[\\u4e00-\\u9fff]' AND NOT title ~ '[가-힣]')
      AND raw_payload ? 'ai_enrichment'
      AND COALESCE(raw_payload->'ai_enrichment'->>'source_lang', '') != 'ZH';
    """
    cur.execute(sql_zh)
    print(f"[*] Updated Chinese items: {cur.rowcount}")

    # 3. Fix English items mislabeled as KO due to Reddit RSS '[댓글]' footer pollution
    sql_fix_en_top = """
    UPDATE raw_trends_inbox
    SET raw_payload = jsonb_set(
        raw_payload,
        '{source_lang}',
        '"EN"'
    )
    WHERE title !~ '[가-힣]'
      AND title !~ '[\\u4e00-\\u9fff]'
      AND source_platform NOT ILIKE '%daum%'
      AND source_platform NOT ILIKE '%geeknews%'
      AND source_platform NOT ILIKE '%hada.io%'
      AND source_platform NOT ILIKE '%naver%'
      AND COALESCE(raw_payload->>'source_lang', '') = 'KO';
    """
    cur.execute(sql_fix_en_top)
    print(f"[*] Fixed English items with polluted top-level source_lang='KO': {cur.rowcount}")

    sql_fix_en_ai = """
    UPDATE raw_trends_inbox
    SET raw_payload = jsonb_set(
        raw_payload,
        '{ai_enrichment,source_lang}',
        '"EN"'
    )
    WHERE title !~ '[가-힣]'
      AND title !~ '[\\u4e00-\\u9fff]'
      AND source_platform NOT ILIKE '%daum%'
      AND source_platform NOT ILIKE '%geeknews%'
      AND source_platform NOT ILIKE '%hada.io%'
      AND source_platform NOT ILIKE '%naver%'
      AND raw_payload ? 'ai_enrichment'
      AND COALESCE(raw_payload->'ai_enrichment'->>'source_lang', '') = 'KO';
    """
    cur.execute(sql_fix_en_ai)
    print(f"[*] Fixed English items with polluted ai_enrichment.source_lang='KO': {cur.rowcount}")

    # 4. Verify ID 29325 (Michael Burry Reddit post)
    cur.execute("""
        SELECT id, title, source_platform, raw_payload->>'source_lang', raw_payload->'ai_enrichment'->>'source_lang'
        FROM raw_trends_inbox
        WHERE id = 29325;
    """)
    row = cur.fetchone()
    if row:
        print(f"[+] Verification ID 29325: ID={row[0]}, Platform={row[2]}, top_lang={row[3]}, ai_lang={row[4]}")

    conn.close()

if __name__ == "__main__":
    main()
