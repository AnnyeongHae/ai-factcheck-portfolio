import sys, os, json
sys.path.insert(0, r'd:\2026.06.21_Antigravity\2026-08-31_WEB_Factcheck')
from tools.db_bridge import load_env_db_url
import psycopg2

db_url = load_env_db_url()
conn = psycopg2.connect(db_url)
cur = conn.cursor()

# 1. Update raw_trends_inbox with enriched payload
inbox_file = r'd:\2026.06.21_Antigravity\2026-08-31_WEB_Factcheck\inbox\x-winneravgwin-2097155225207603544.json'
with open(inbox_file, 'r', encoding='utf-8') as fp:
    inbox_payload = json.load(fp)

cur.execute("""
    UPDATE raw_trends_inbox
    SET 
        title = %s,
        item_type = %s,
        category_primary = %s,
        raw_payload = %s,
        created_at = %s,
        harvested_date = %s
    WHERE inbox_id = %s;
""", (
    inbox_payload['title'],
    inbox_payload['type'],
    inbox_payload['category_primary'],
    json.dumps(inbox_payload, ensure_ascii=False),
    '2026-09-08 18:00:00+09',
    '2026-09-08',
    'x-winneravgwin-2097155225207603544'
))
print("Updated raw_trends_inbox rows:", cur.rowcount)

# 2. Insert into verified_factchecks
meta_file = r'd:\2026.06.21_Antigravity\2026-08-31_WEB_Factcheck\investigations\2026-09-08_sns_refero_styles_design_md\metadata.json'
with open(meta_file, 'r', encoding='utf-8') as fp:
    meta = json.load(fp)

cur.execute("""
    INSERT INTO verified_factchecks (
        case_id, title, category, created_at, verdict, confidence_score,
        discovery_mode, curator_name, personal_motivation, target_workflow,
        cluster_id, cluster_name, hands_on_status, hands_on_pipeline,
        hands_on_env, hands_on_metrics, hands_on_details, the_hook,
        marketing_hype_anatomy, engineering_takeaways, future_applications,
        sources, origin_inbox_id, version
    ) VALUES (
        %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s,
        %s, %s, %s, %s,
        %s, %s, %s, %s,
        %s, %s, %s,
        %s, %s, %s
    )
    ON CONFLICT (case_id) DO UPDATE SET
        title = EXCLUDED.title,
        category = EXCLUDED.category,
        verdict = EXCLUDED.verdict,
        confidence_score = EXCLUDED.confidence_score,
        the_hook = EXCLUDED.the_hook,
        engineering_takeaways = EXCLUDED.engineering_takeaways,
        updated_at = NOW();
""", (
    meta['case_id'],
    meta['title'],
    meta['category'],
    '2026-09-08 18:00:00+09',
    meta['verdict'],
    meta['confidence_score'],
    meta['curation']['discovery_mode'],
    meta['curation']['curator'],
    meta['curation']['personal_motivation'],
    meta['curation']['target_workflow'],
    meta['clustering']['cluster_id'],
    meta['clustering']['cluster_name'],
    meta['portfolio_story']['hands_on_log']['status'],
    meta['portfolio_story']['hands_on_log']['pipeline_or_url'],
    meta['portfolio_story']['hands_on_log']['test_environment'],
    meta['portfolio_story']['hands_on_log']['measured_results'],
    meta['portfolio_story']['hands_on_log']['details'],
    meta['portfolio_story']['the_hook'],
    meta['portfolio_story']['marketing_hype_anatomy'],
    meta['portfolio_story']['engineering_takeaways'],
    meta['portfolio_story']['future_applications'],
    json.dumps(meta['sources'], ensure_ascii=False),
    'x-winneravgwin-2097155225207603544',
    1
))
print("Upserted verified_factchecks rows:", cur.rowcount)

# 3. Check total counts in Neon DB
cur.execute("SELECT COUNT(*) FROM verified_factchecks;")
print("Total verified_factchecks:", cur.fetchone()[0])
cur.execute("SELECT COUNT(*) FROM raw_trends_inbox;")
print("Total raw_trends_inbox:", cur.fetchone()[0])

conn.commit()
conn.close()
print("Done sync to Neon DB!")
