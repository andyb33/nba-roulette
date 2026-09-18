#!/usr/bin/env python3
"""Run the local NBA Roulette browser prototype without external packages."""

from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
import threading
import webbrowser
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

FROZEN = bool(getattr(sys, "frozen", False))
ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(ROOT))

from nba_roulette.data import load_records
from nba_roulette.playtest import PlaytestBatchLogger
from nba_roulette.web import BrowserGame


STATIC = ROOT / "web" / "static"
RECORDS = load_records(data_dir=ROOT / "data" / "game")


def default_log_directory() -> Path:
    """Keep packaged playtest evidence outside PyInstaller's temporary folder."""
    override = os.environ.get("NBA_ROULETTE_LOG_DIR")
    if override:
        return Path(override).expanduser()
    if FROZEN:
        documents = Path(os.environ.get("USERPROFILE", Path.home())) / "Documents"
        return documents / "NBA Roulette" / "playtest_logs"
    return ROOT / "playtest_logs"


PLAYTEST_LOGGER = PlaytestBatchLogger(
    default_log_directory(),
    "playtest_batch_04_v0_4_external_alpha",
    "Playtest Batch 4 — v0.4 External Alpha",
    target=100,
)
SESSIONS: dict[str, BrowserGame] = {}
ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/state":
            game, cookie = self._session()
            self._json(game.state(), cookie=cookie)
            return
        if path in ASSETS:
            filename, content_type = ASSETS[path]
            body = (STATIC / filename).read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        game, cookie = self._session(new=path == "/api/new")
        try:
            payload = self._body()
            if path == "/api/new":
                result = game.state()
            elif path == "/api/spin":
                result = game.spin(payload.get("keeps", []))
            elif path == "/api/score":
                result = game.score(str(payload.get("category", "")))
            else:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self._json(result, cookie=cookie)
        except (ValueError, RuntimeError) as error:
            self._json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST, cookie=cookie)

    def _session(self, new: bool = False) -> tuple[BrowserGame, str | None]:
        cookie = SimpleCookie(self.headers.get("Cookie"))
        session_id = cookie.get("nba_session")
        key = session_id.value if session_id else ""
        created = new or key not in SESSIONS
        if created:
            key = secrets.token_urlsafe(18)
            SESSIONS[key] = BrowserGame(RECORDS, logger=PLAYTEST_LOGGER)
        return SESSIONS[key], f"nba_session={key}; Path=/; SameSite=Lax" if created else None

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _json(
        self,
        payload: dict,
        status: HTTPStatus = HTTPStatus.OK,
        cookie: str | None = None,
    ) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        print(f"[web] {self.address_string()} - {format % args}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0 if FROZEN else 8000)
    parser.add_argument(
        "--open-browser",
        action=argparse.BooleanOptionalAction,
        default=FROZEN,
        help="Open NBA Roulette in the default browser after startup",
    )
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    port = server.server_address[1]
    url = f"http://{args.host}:{port}"
    print(f"NBA Roulette running at {url}")
    print(
        f"Playtest batch: {PLAYTEST_LOGGER.batch_name} "
        f"({PLAYTEST_LOGGER.completed_count()}/{PLAYTEST_LOGGER.target})"
    )
    print(f"Logs: {PLAYTEST_LOGGER.directory}")
    print("Keep this window open while playing. Close it to stop NBA Roulette.")
    if args.open_browser:
        threading.Timer(0.6, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
