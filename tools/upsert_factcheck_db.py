#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/upsert_factcheck_db.py
Direct DB-First factcheck upsert tool for Neon PostgreSQL.
No local investigations/ folder or metadata.json required.
"""

import os
import sys
import json

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tools_dir = os.path.join(base_dir, 'tools')
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

from db_bridge import get_db_connection

def upsert_case(c):
    conn = get_db_connection()
    if not conn:
        print('[!] Database connection failed.')
        return False

    case_id = c['case_id']
    curation = c.get('curation', {})
    clustering = c.get('clustering', {})
    portfolio_story = c.get('portfolio_story', {})
    hands_on = portfolio_story.get('hands_on_log', {})
    raw_post = c.get('raw_viral_post', {})

    try:
        cur = conn.cursor()
        # 1. verified_factchecks
        cur.execute("""
            INSERT INTO verified_factchecks (
                case_id, title, category, verdict, confidence_score, discovery_mode,
                curator_name, personal_motivation, target_workflow, cluster_id,
                cluster_name, hands_on_status, hands_on_pipeline, hands_on_env,
                hands_on_metrics, hands_on_details, the_hook, marketing_hype_anatomy,
                engineering_takeaways, future_applications, sources, created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s
            )
            ON CONFLICT (case_id) DO UPDATE SET
                title = EXCLUDED.title,
                category = EXCLUDED.category,
                verdict = EXCLUDED.verdict,
                confidence_score = EXCLUDED.confidence_score,
                discovery_mode = EXCLUDED.discovery_mode,
                curator_name = EXCLUDED.curator_name,
                personal_motivation = EXCLUDED.personal_motivation,
                target_workflow = EXCLUDED.target_workflow,
                cluster_id = EXCLUDED.cluster_id,
                cluster_name = EXCLUDED.cluster_name,
                hands_on_status = EXCLUDED.hands_on_status,
                hands_on_pipeline = EXCLUDED.hands_on_pipeline,
                hands_on_env = EXCLUDED.hands_on_env,
                hands_on_metrics = EXCLUDED.hands_on_metrics,
                hands_on_details = EXCLUDED.hands_on_details,
                the_hook = EXCLUDED.the_hook,
                marketing_hype_anatomy = EXCLUDED.marketing_hype_anatomy,
                engineering_takeaways = EXCLUDED.engineering_takeaways,
                future_applications = EXCLUDED.future_applications,
                sources = EXCLUDED.sources;
        """, (
            case_id,
            c.get('title', ''),
            c.get('category', 'general_ai'),
            c.get('verdict', 'VERIFIED_TRUE'),
            float(c.get('confidence_score', 95.0)),
            curation.get('discovery_mode', 'USER_CURATED'),
            curation.get('curator', 'FactCheck AI Lab'),
            curation.get('personal_motivation', ''),
            curation.get('target_workflow', ''),
            clustering.get('cluster_id', 'general'),
            clustering.get('cluster_name', 'General AI'),
            hands_on.get('status', 'verified'),
            hands_on.get('pipeline_or_url', ''),
            hands_on.get('test_environment', ''),
            hands_on.get('measured_results', ''),
            hands_on.get('details', ''),
            portfolio_story.get('the_hook', ''),
            portfolio_story.get('marketing_hype_anatomy', ''),
            portfolio_story.get('engineering_takeaways', ''),
            portfolio_story.get('future_applications', ''),
            json.dumps(c.get('sources', []), ensure_ascii=False),
            f"{c.get('investigation_date', '2026-09-20')} 12:00:00"
        ))

        # 2. factcheck_atomic_claims
        cur.execute('DELETE FROM factcheck_atomic_claims WHERE case_id = %s;', (case_id,))
        for idx, clm in enumerate(c.get('claims_assessment', []), 1):
            cur.execute("""
                INSERT INTO factcheck_atomic_claims (
                    case_id, claim_number, claim_title, claim_text, claim_verdict, verification_evidence
                ) VALUES (%s, %s, %s, %s, %s, %s);
            """, (
                case_id,
                clm.get('claim_number', idx),
                clm.get('claim_title', f'Claim {idx}'),
                clm.get('claim', clm.get('statement', '')),
                clm.get('verdict', clm.get('status', 'CONFIRMED')),
                clm.get('reality', clm.get('verification_evidence', ''))
            ))

        # 3. factcheck_alternatives
        cur.execute('DELETE FROM factcheck_alternatives WHERE case_id = %s;', (case_id,))
        for alt in clustering.get('alternatives', []) or c.get('alternatives', []):
            cur.execute("""
                INSERT INTO factcheck_alternatives (
                    case_id, tool_name, tech_stack, pros, cons, best_for
                ) VALUES (%s, %s, %s, %s, %s, %s);
            """, (
                case_id,
                alt.get('name', ''),
                alt.get('tech_stack', ''),
                alt.get('pros', ''),
                alt.get('cons', ''),
                alt.get('best_for', '')
            ))

        # 4. factcheck_community_signals
        cur.execute('DELETE FROM factcheck_community_signals WHERE case_id = %s;', (case_id,))
        if raw_post:
            cur.execute("""
                INSERT INTO factcheck_community_signals (
                    case_id, platform, author_type, quote, source_url, signal_type
                ) VALUES (%s, %s, %s, %s, %s, %s);
            """, (
                case_id,
                raw_post.get('platform', 'Web'),
                raw_post.get('author', ''),
                raw_post.get('quote', ''),
                raw_post.get('post_url', ''),
                'viral_origin'
            ))

        conn.commit()
        print(f'[+] Successfully upserted {case_id} directly to Neon DB (SSOT).')
        return True
    except Exception as e:
        conn.rollback()
        print(f'[!] Upsert failed for {case_id}: {e}')
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                for item in data: upsert_case(item)
            else:
                upsert_case(data)
