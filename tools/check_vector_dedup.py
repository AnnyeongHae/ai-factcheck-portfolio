import os, sys, json
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
tools_dir = os.path.join(ROOT_DIR, "tools")
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)
from dotenv import load_dotenv
load_dotenv('.env')

print('=== 1. VOYAGE API STATUS ===')
voyage_key = os.getenv('VOYAGE_API_KEY')
print('VOYAGE_API_KEY present:', bool(voyage_key))

from voyage_embedder import get_single_embedding, cosine_similarity
try:
    e1 = get_single_embedding('Alibaba Qwen 2.5 release')
    e2 = get_single_embedding('Qwen 2.5 open source weights published by Alibaba')
    e3 = get_single_embedding('Houthi Red Sea shipping attack')
    print('Embedding dimension:', len(e1) if e1 else None)
    print('Sim(Qwen, Qwen):', round(cosine_similarity(e1, e2), 4))
    print('Sim(Qwen, Houthi):', round(cosine_similarity(e1, e3), 4))
except Exception as e:
    print('Voyage test error:', e)

print('\n=== 2. DATABASE VECTOR / EXTENSION STATUS ===')
from tools.db_config import get_db_connection
conn = get_db_connection()
cur = conn.cursor()

try:
    cur.execute("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';")
    ext = cur.fetchall()
    print('pgvector extension in DB:', ext)
except Exception as e:
    print('Extension query error:', e)

try:
    cur.execute("SELECT COUNT(*) FROM raw_trends_inbox WHERE embedding IS NOT NULL;")
    emb_cnt = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM raw_trends_inbox;")
    total_cnt = cur.fetchone()[0]
    print(f'raw_trends_inbox embedding column populated: {emb_cnt} / {total_cnt}')
except Exception as e:
    print('Embedding count error:', e)

print('\n=== 3. DEDUPLICATION METADATA IN RAW_PAYLOAD ===')
cur.execute("""
    SELECT count(*) 
    FROM raw_trends_inbox 
    WHERE raw_payload->>'canonical_story_key' IS NOT NULL;
""")
story_keys = cur.fetchone()[0]
print(f'Items with canonical_story_key: {story_keys} / {total_cnt}')

cur.execute("""
    SELECT count(*) 
    FROM raw_trends_inbox 
    WHERE raw_payload->>'canonical_tech_entity' IS NOT NULL;
""")
tech_keys = cur.fetchone()[0]
print(f'Items with canonical_tech_entity: {tech_keys} / {total_cnt}')

cur.close()
conn.close()
