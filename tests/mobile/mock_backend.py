"""Local synthetic backend for Android transport tests; never contacts Goofish."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CANDIDATE = dict(item_id="12345", title="SHARP LJ64HB34 TFEL screen", listed_price=180,
                 rule_interest_score=92, price_confidence=90, price_type="NEGOTIABLE_REAL_PRICE",
                 detected_models=[{"model":"LJ64HB34"}], risk_flags=["UNTESTED"],
                 evaluation_reason="Worth opening, not a purchase recommendation.", image_urls=[],
                 url="https://www.goofish.com/item?id=12345", evaluated_at="2026-10-04")
class Handler(BaseHTTPRequestHandler):
    def reply(self, data, status=200):
        content=json.dumps(data).encode(); self.send_response(status)
        self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(content)))
        self.end_headers();self.wfile.write(content)
    def do_GET(self):
        if self.path == "/health": self.reply({"status":"healthy"})
        elif self.path == "/api/radar/summary": self.reply({"items_today":1,"candidates":1})
        elif self.path.startswith("/api/radar/candidates"): self.reply({"total":1,"items":[CANDIDATE]})
        elif self.path.startswith("/api/tasks"): self.reply([])
        else: self.reply({})
    def do_POST(self):
        content=json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
        if self.path=="/auth/status" and content=={"username":"test","password":"test-only"}: self.reply({"authenticated":True,"username":"test"})
        else: self.reply({"detail":"test authentication failed"},401)
if __name__=="__main__": ThreadingHTTPServer(("0.0.0.0",8765), Handler).serve_forever()
