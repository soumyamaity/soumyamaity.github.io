#!/usr/bin/env python3
"""
serve.py — preview the site locally, exactly as GitHub Pages will serve it.

    python local-server/serve.py          (or double-click start-server.bat)

Rebuilds the content manifests, then serves the repo at
http://localhost:8000 and opens your browser.
"""
import http.server
import os
import socketserver
import subprocess
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def end_headers(self):
        # match GitHub Pages behaviour closely enough; avoid stale previews
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def main() -> int:
    print("Rebuilding manifests…")
    subprocess.run([sys.executable, str(ROOT / "tools" / "build.py")], check=False)

    url = f"http://localhost:{PORT}/"
    print(f"\nServing {ROOT}")
    print(f"Preview: {url}   (Ctrl+C to stop)\n")
    webbrowser.open(url)
    with socketserver.ThreadingTCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
