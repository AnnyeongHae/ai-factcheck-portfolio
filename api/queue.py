from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.parse
import psycopg2
from psycopg2.extras import RealDictCursor

NEON_DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    if not NEON_DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not configured in Vercel settings.")
    return psycopg2.connect(NEON_DATABASE_URL, cursor_factory=RealDictCursor)

class handler(BaseHTTPRequestHandler):
    def _set_cors_headers(self, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_cors_headers(204)

    def do_GET(self):
        """
        GET /api/queue: Fetch all queued candidates from Neon Postgres DB
        """
        parsed_path = urllib.parse.urlparse(self.path)
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT inbox_id, title, title_ko, source_platform, model_family, variant_role, status, harvested_date 
                FROM inbox_candidates 
                WHERE status = 'QUEUED_FOR_INVESTIGATION' 
                ORDER BY harvested_date DESC, created_at DESC;
            """)
            rows = cur.fetchall()
            cur.close()
            conn.close()

            self._set_cors_headers(200)
            res = {
                "success": True,
                "queued_count": len(rows),
                "queued_items": rows
            }
            self.wfile.write(json.dumps(res, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self._set_cors_headers(500)
            self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))

    def do_POST(self):
        """
        POST /api/queue: Toggle queue status or batch update candidates in Neon DB
        Payload: {"inbox_id": "...", "action": "queue" | "unqueue" | "toggle" | "batch_queue", "inbox_ids": [...]}
        """
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body.decode('utf-8'))
            action = data.get("action", "toggle")
            inbox_id = data.get("inbox_id")
            inbox_ids = data.get("inbox_ids", [inbox_id] if inbox_id else [])

            if not inbox_ids:
                self._set_cors_headers(400)
                self.wfile.write(json.dumps({"success": False, "error": "No inbox_id provided"}).encode('utf-8'))
                return

            conn = get_db_connection()
            cur = conn.cursor()

            updated_status = "QUEUED_FOR_INVESTIGATION"
            if action == "unqueue":
                updated_status = "PENDING_REVIEW"
            elif action == "toggle" and len(inbox_ids) == 1:
                cur.execute("SELECT status FROM inbox_candidates WHERE inbox_id = %s;", (inbox_ids[0],))
                row = cur.fetchone()
                if row and row["status"] == "QUEUED_FOR_INVESTIGATION":
                    updated_status = "PENDING_REVIEW"
                else:
                    updated_status = "QUEUED_FOR_INVESTIGATION"

            for target_id in inbox_ids:
                cur.execute("""
                    UPDATE inbox_candidates 
                    SET status = %s, updated_at = CURRENT_TIMESTAMP 
                    WHERE inbox_id = %s;
                """, (updated_status, target_id))

            conn.commit()
            cur.close()
            conn.close()

            self._set_cors_headers(200)
            res = {
                "success": True,
                "action": action,
                "target_status": updated_status,
                "affected_ids": inbox_ids,
                "message": f"Successfully updated {len(inbox_ids)} candidate(s) in Neon DB to '{updated_status}'"
            }
            self.wfile.write(json.dumps(res, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            self._set_cors_headers(500)
            self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
