from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.parse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        res = {
            "status": "ONLINE",
            "service": "AI Tech-Lineage Fact-Check Intelligence Hub (Vercel Serverless)",
            "version": "v14.0",
            "endpoints": ["/api/health", "/api/queue"]
        }
        self.wfile.write(json.dumps(res, ensure_ascii=False, indent=2).encode('utf-8'))
