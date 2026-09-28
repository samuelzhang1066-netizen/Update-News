"""News Tracker - a tiny local server that stores your articles on your own computer.

No installs needed beyond Python 3. Run via Start.bat / Start.command / start.sh.
"""
import json
import os
import re
import shutil
import socket
import sys
import threading
import urllib.request
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8765
APP_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(APP_DIR)
DATA_DIR = os.path.join(ROOT_DIR, "data")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
DATA_FILE = os.path.join(DATA_DIR, "news.json")
FILES_DIR = os.path.join(ROOT_DIR, "My News Files")
INDEX_FILE = os.path.join(APP_DIR, "index.html")

DEFAULT_DATA = {
    "categories": [
        {"id": "c-markets", "name": "Markets & Stocks", "color": "#2f6fed"},
        {"id": "c-economy", "name": "Economy & Central Banks", "color": "#16a34a"},
        {"id": "c-geo", "name": "Geopolitics", "color": "#dc2626"},
        {"id": "c-tech", "name": "Technology", "color": "#9333ea"},
        {"id": "c-energy", "name": "Energy & Commodities", "color": "#ea580c"},
    ],
    "articles": [],
}

save_lock = threading.Lock()


def load_data():
    if not os.path.exists(DATA_FILE):
        return json.loads(json.dumps(DEFAULT_DATA))
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def safe_name(name):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", name).strip().rstrip(".")
    return name or "Untitled"


def bullets(text):
    lines = [l.strip().lstrip("-•*").strip() for l in (text or "").splitlines()]
    return [l for l in lines if l]


def article_markdown(a):
    out = [f"## {a.get('title') or 'Untitled'}", ""]
    meta = []
    if a.get("source"):
        meta.append(f"**Source:** {a['source']}")
    if a.get("date"):
        meta.append(f"**Date:** {a['date']}")
    if a.get("outlook"):
        meta.append(f"**Outlook:** {a['outlook']}")
    if meta:
        out += [" | ".join(meta), ""]
    if a.get("url"):
        out += [f"**Link:** {a['url']}", ""]
    for label, key in (
        ("Key points", "keyPoints"),
        ("What this could mean for the market", "marketImpact"),
        ("What this could mean for the global market", "globalImpact"),
        ("My notes", "notes"),
    ):
        items = bullets(a.get(key))
        if items:
            out.append(f"**{label}:**")
            out += [f"- {i}" for i in items]
            out.append("")
    out += ["---", ""]
    return "\n".join(out)


def write_category_files(data):
    """Write one readable Markdown file per section into 'My News Files'."""
    os.makedirs(FILES_DIR, exist_ok=True)
    expected = set()
    for cat in data.get("categories", []):
        fname = safe_name(cat.get("name", "")) + ".md"
        expected.add(fname)
        arts = [a for a in data.get("articles", []) if a.get("categoryId") == cat.get("id")]
        arts.sort(key=lambda a: (a.get("date") or "", a.get("createdAt") or ""), reverse=True)
        body = [f"# {cat.get('name')}", "", f"_{len(arts)} article(s) - updated {datetime.now():%d %b %Y %H:%M}_", ""]
        body += [article_markdown(a) for a in arts] or ["_No articles yet._"]
        with open(os.path.join(FILES_DIR, fname), "w", encoding="utf-8") as f:
            f.write("\n".join(body))
    # Remove files for sections that were deleted or renamed
    for fname in os.listdir(FILES_DIR):
        if fname.endswith(".md") and fname not in expected:
            try:
                os.remove(os.path.join(FILES_DIR, fname))
            except OSError:
                pass


def save_data(data):
    with save_lock:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        tmp = DATA_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, DATA_FILE)
        # One backup per day, keep the last 30
        daily = os.path.join(BACKUP_DIR, f"news-{datetime.now():%Y-%m-%d}.json")
        shutil.copyfile(DATA_FILE, daily)
        backups = sorted(f for f in os.listdir(BACKUP_DIR) if f.endswith(".json"))
        for old in backups[:-30]:
            os.remove(os.path.join(BACKUP_DIR, old))
        try:
            write_category_files(data)
        except OSError as e:
            print("Could not write category files:", e)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send_json(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            with open(INDEX_FILE, "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/data":
            try:
                self.send_json(load_data())
            except Exception as e:
                self.send_json({"error": f"Could not read saved data: {e}"}, 500)
        elif self.path == "/api/ping":
            self.send_json({"app": "news-tracker"})
        elif self.path == "/api/open-folder":
            os.makedirs(FILES_DIR, exist_ok=True)
            open_folder(FILES_DIR)
            self.send_json({"ok": True})
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path != "/api/data":
            return self.send_error(404)
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(data.get("categories"), list) or not isinstance(data.get("articles"), list):
                raise ValueError("bad data shape")
            save_data(data)
            self.send_json({"ok": True, "savedAt": datetime.now().strftime("%H:%M:%S")})
        except Exception as e:
            self.send_json({"ok": False, "error": str(e)}, 500)


def open_folder(path):
    if sys.platform.startswith("win"):
        os.startfile(path)  # noqa
    elif sys.platform == "darwin":
        os.system(f'open "{path}"')
    else:
        os.system(f'xdg-open "{path}" >/dev/null 2>&1 &')


def already_running():
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/ping", timeout=1) as r:
            return json.load(r).get("app") == "news-tracker"
    except Exception:
        return False


def main():
    url = f"http://127.0.0.1:{PORT}/"
    if already_running():
        print("News Tracker is already running - opening it in your browser.")
        webbrowser.open(url)
        return
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DATA_FILE):
        save_data(load_data())
    try:
        server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    except OSError:
        print(f"Port {PORT} is being used by another program. Close it and try again.")
        input("Press Enter to close...")
        return
    print("=" * 56)
    print("  News Tracker is running!")
    print(f"  Open in your browser:  {url}")
    print(f"  Your data is saved in: {DATA_FILE}")
    print(f"  Readable files:        {FILES_DIR}")
    print("  Keep this window open while you use it.")
    print("  Close this window (or press Ctrl+C) to stop.")
    print("=" * 56)
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped. Your data is saved.")


if __name__ == "__main__":
    main()
