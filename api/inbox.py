#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
api/inbox.py - Vercel Serverless Function
Returns paginated, filterable real-time inbox items from Neon PostgreSQL DB.
"""

import os
import sys
import json
import math
import datetime
from decimal import Decimal
from http.server import BaseHTTPRequestHandler
import urllib.parse

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def get_db_url():
    url = os.environ.get("DATABASE_URL") or os.environ.get("NEON_KEY") or os.environ.get("NEON_DATABASE_URL")
    if not url:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(base_dir, ".env")
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("DATABASE_URL=") or line.startswith("NEON_KEY="):
                            val = line.split("=", 1)[1].strip().strip('"').strip("'")
                            if val:
                                return val
            except Exception:
                pass
    return url

def fetch_inbox_items(page=1, limit=30, category=None, platform=None, search=None):
    db_url = get_db_url()
    if not db_url:
        return {
            "status": "error",
            "message": "DATABASE_URL not configured",
            "items": [],
            "pagination": {"page": page, "limit": limit, "total_count": 0, "total_pages": 0}
        }

    try:
        import psycopg2
        conn = psycopg2.connect(db_url, connect_timeout=5)
        cur = conn.cursor()

        where_clauses = ["raw_payload IS NOT NULL"]
        params = []

        if category:
            where_clauses.append("(category_primary = %s OR raw_payload->>'tier1_category' = %s)")
            params.extend([category, category])

        if platform:
            where_clauses.append("source_platform ILIKE %s")
            params.append(f"%{platform}%")

        if search:
            where_clauses.append("(title ILIKE %s OR raw_payload->>'title_ko' ILIKE %s OR description ILIKE %s)")
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

        where_sql = " AND ".join(where_clauses)

        # Count total matching
        cur.execute(f"SELECT count(*) FROM raw_trends_inbox WHERE {where_sql};", tuple(params))
        total_count = cur.fetchone()[0]
        total_pages = math.ceil(total_count / max(1, limit))

        # Fetch page items
        offset = (page - 1) * limit
        query_sql = f"""
            SELECT id, inbox_id, source_platform, title, item_type, harvested_date, raw_payload
            FROM raw_trends_inbox
            WHERE {where_sql}
            ORDER BY id DESC
            LIMIT %s OFFSET %s;
        """
        cur.execute(query_sql, tuple(params + [limit, offset]))
        rows = cur.fetchall()

        items = []
        for r in rows:
            payload = r[6]
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except Exception:
                    payload = {}
            if not isinstance(payload, dict):
                payload = {}

            # Ensure minimal required fields
            if "inbox_id" not in payload:
                payload["inbox_id"] = r[1]
            if "title" not in payload:
                payload["title"] = r[3]
            if "source_platform" not in payload:
                payload["source_platform"] = r[2]
            if "harvested_date" not in payload:
                payload["harvested_date"] = str(r[5])

            items.append(payload)

        conn.close()

        return {
            "status": "success",
            "pagination": {
                "page": page,
                "limit": limit,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            },
            "items": items
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "items": [],
            "pagination": {"page": page, "limit": limit, "total_count": 0, "total_pages": 0}
        }

def app(environ, start_response):
    method = environ.get('REQUEST_METHOD', 'GET')
    if method == 'OPTIONS':
        start_response('204 No Content', [
            ('Access-Control-Allow-Origin', '*'),
            ('Access-Control-Allow-Methods', 'GET, OPTIONS'),
            ('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        ])
        return [b'']

    query_str = environ.get('QUERY_STRING', '')
    query_params = urllib.parse.parse_qs(query_str)

    try:
        page = int(query_params.get("page", ["1"])[0])
    except ValueError:
        page = 1

    try:
        limit = min(100, max(1, int(query_params.get("limit", ["30"])[0])))
    except ValueError:
        limit = 30

    category = query_params.get("category", [None])[0]
    platform = query_params.get("platform", [None])[0]
    search = query_params.get("search", [None])[0]

    data = fetch_inbox_items(page=page, limit=limit, category=category, platform=platform, search=search)
    body = json.dumps(data, default=decimal_default, ensure_ascii=False).encode('utf-8')
    status = '200 OK' if data.get("status") == "success" else '500 Internal Server Error'

    start_response(status, [
        ('Content-Type', 'application/json; charset=utf-8'),
        ('Access-Control-Allow-Origin', '*'),
        ('Cache-Control', 'public, s-maxage=30, stale-while-revalidate=60'),
        ('Content-Length', str(len(body)))
    ])
    return [body]

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)

        try:
            page = int(query_params.get("page", ["1"])[0])
        except ValueError:
            page = 1

        try:
            limit = min(100, max(1, int(query_params.get("limit", ["30"])[0])))
        except ValueError:
            limit = 30

        category = query_params.get("category", [None])[0]
        platform = query_params.get("platform", [None])[0]
        search = query_params.get("search", [None])[0]

        data = fetch_inbox_items(page=page, limit=limit, category=category, platform=platform, search=search)
        body = json.dumps(data, default=decimal_default, ensure_ascii=False).encode('utf-8')

        self.send_response(200 if data.get("status") == "success" else 500)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'public, s-maxage=30, stale-while-revalidate=60')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

if __name__ == '__main__':
    res = fetch_inbox_items(page=1, limit=5)
    print(f"Status: {res.get('status')}, Total: {res.get('pagination', {}).get('total_count')}, Items fetched: {len(res.get('items', []))}")
    if res.get('items'):
        sample = res['items'][0]
        print("Sample item:", sample.get("inbox_id"), sample.get("title_ko") or sample.get("title"))
