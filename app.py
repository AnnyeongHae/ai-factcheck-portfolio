from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        try:
            with open("public/index.html", "r", encoding="utf-8") as f:
                content = f.read()
            self.wfile.write(content.encode('utf-8'))
        except Exception:
            with open("docs/index.html", "r", encoding="utf-8") as f:
                content = f.read()
            self.wfile.write(content.encode('utf-8'))
