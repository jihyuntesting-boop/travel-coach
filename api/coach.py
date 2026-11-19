"""Vercel Serverless Function (Python): POST /api/coach"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(__file__))
from _core import handle  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def _send(self, status, body):
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 4096:
                return self._send(413, {"error": "요청이 너무 큽니다."})
            payload = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            return self._send(400, {"error": "요청 형식이 올바르지 않습니다."})
        status, body = handle(payload)
        self._send(status, body)

    def do_GET(self):
        self._send(405, {"error": "POST 요청만 지원합니다."})
