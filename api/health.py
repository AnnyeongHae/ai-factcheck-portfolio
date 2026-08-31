from http.server import BaseHTTPRequestHandler
import json
import os
import psycopg2

NEON_DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_1sXv4iFvJadO@ep-quiet-grass-a1wqqs32-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"
)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        db_status = "UNKNOWN"
        counts = {}
        try:
            conn = psycopg2.connect(NEON_DATABASE_URL)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM verified_portfolios;")
            counts["verified_portfolios"] = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM inbox_candidates;")
            counts["inbox_candidates"] = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM inbox_candidates WHERE status = 'QUEUED_FOR_INVESTIGATION';")
            counts["queued_for_investigation"] = cur.fetchone()[0]
            cur.close()
            conn.close()
            db_status = "CONNECTED_HEALTHY"
        except Exception as e:
            db_status = f"ERROR: {str(e)}"

        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        res = {
            "service": "AI Tech-Lineage Fact-Check Hub (Vercel Serverless Backend)",
            "version": "v14.0",
            "neon_postgres_status": db_status,
            "metrics": counts
        }
        self.wfile.write(json.dumps(res, ensure_ascii=False, indent=2).encode('utf-8'))
