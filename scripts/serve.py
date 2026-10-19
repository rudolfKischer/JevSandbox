import json
import sys
from urllib.parse import parse_qs, urlparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from phonalign.config import SETTINGS
from phonalign.sources import lookup
from scripts.data_bucket import ensure

PORT = SETTINGS["viewer"]["port"]


def listing(folder=""):
    rows = []
    base = ROOT / SETTINGS["alignment"]["results_dir"] / folder
    for path in sorted(base.glob("*.json")):
        data = json.loads(path.read_text())
        rows.append({key: data.get(key) for key in ("experiment", "method", "kind", "live", "created", "summary", "config", "gold", "set", "partial")} | {"file": path.name})
    return rows


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_json(self, payload):
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        route = self.path.split("?")[0]
        if route == "/api/sources":
            query = parse_qs(urlparse(self.path).query)
            word, pron, ours = (query.get(key, [""])[0] for key in ("word", "pron", "ours"))
            return self.send_json(lookup.answers(word, pron, ours) if word and pron and ours else [])
        if route.startswith("/api/results"):
            folder = route[len("/api/results"):].strip("/")
            body = json.dumps(listing(folder) if folder != "regions" else []).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    ensure()
    lookup.preload()
    print(f"viewer at http://127.0.0.1:{PORT}/web/")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
