"""Live visualizer server — stdlib only (ThreadingHTTPServer + Server-Sent Events).

    python -m viz.server [--port 8808]

Runs a chosen scenario of the contained medium in a worker thread and streams
one frame per window to the browser over SSE (`GET /stream`). The browser sends
play/pause/step/speed/scenario via `POST /control`. The server paces and pauses
the medium by *blocking inside the on_frame callback* it hands the scenario — so
the medium needs no knowledge of the UI.

Containment (SECURITY.md C7): emulation runs in this process with the C1
instruction traps active — safe for the curated demo organisms. For untrusted or
evolved organisms, run this server inside the C4 container
(`containment/run.sh python3 -m viz.server`).
"""

import argparse
import json
import queue
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import scenes

STATIC = Path(__file__).resolve().parent / "static"
BASE_INTERVAL = 0.12              # seconds per frame at speed 1×
MIME = {".html": "text/html", ".js": "text/javascript", ".css": "text/css"}


class _Stop(Exception):
    """Raised inside on_frame to abort a superseded/stopped run."""


class Session:
    def __init__(self):
        self.clients = []                 # list[queue.Queue]
        self.lock = threading.Lock()
        self.meta = {}
        self.last_frame = None
        self.token = 0                    # bumped on each (re)start
        self.paused = False
        self.step = False
        self.speed = 1.0

    # --- client registry / broadcast ---
    def add_client(self):
        q = queue.Queue(maxsize=64)
        with self.lock:
            self.clients.append(q)
        return q

    def drop_client(self, q):
        with self.lock:
            if q in self.clients:
                self.clients.remove(q)

    def broadcast(self, event, data):
        msg = (event, data)
        with self.lock:
            for q in list(self.clients):
                try:
                    q.put_nowait(msg)
                except queue.Full:
                    pass

    # --- run control ---
    def start(self, spec):
        meta, run = scenes.build(spec)
        with self.lock:
            self.token += 1
            token = self.token
            self.meta = {**meta, "spec": spec}
            self.last_frame = None
            self.paused = False
            self.speed = float(spec.get("speed", self.speed))
        self.broadcast("meta", self.meta)
        threading.Thread(target=self._worker, args=(token, run), daemon=True).start()

    def _worker(self, token, run):
        def on_frame(fr):
            if token != self.token:
                raise _Stop
            self.last_frame = fr
            self.broadcast("frame", fr)
            interval = BASE_INTERVAL / max(self.speed, 0.05)
            deadline = time.time() + interval
            while True:
                if token != self.token:
                    raise _Stop
                if self.paused:
                    if self.step:
                        self.step = False
                        return
                    time.sleep(0.03)
                    deadline = time.time() + interval
                elif time.time() >= deadline:
                    return
                else:
                    time.sleep(0.01)
        try:
            run(on_frame)
        except _Stop:
            return
        except Exception as e:                      # surface medium errors to UI
            self.broadcast("done", {"cause": f"error: {e}"})
            return
        if token == self.token:
            lf = self.last_frame or {}
            self.broadcast("done", {"cause": lf.get("cause", ""),
                                    "alive": lf.get("alive", True)})


SESSION = Session()


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def handle(self):                     # swallow client-disconnect noise (SSE)
        try:
            super().handle()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass

    def log_message(self, *a):            # quiet
        pass

    def _send(self, code, body=b"", ctype="text/plain"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/stream":
            return self._stream()
        if path == "/":
            path = "/index.html"
        f = (STATIC / path.lstrip("/")).resolve()
        if STATIC in f.parents and f.is_file():
            return self._send(200, f.read_bytes(),
                              MIME.get(f.suffix, "application/octet-stream"))
        self._send(404, b"not found")

    def do_POST(self):
        if self.path != "/control":
            return self._send(404, b"not found")
        n = int(self.headers.get("Content-Length", 0))
        try:
            msg = json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            return self._send(400, b"bad json")
        action = msg.get("action")
        if action == "start":
            SESSION.start(msg.get("spec", {}))
        elif action == "pause":
            SESSION.paused = True
        elif action == "resume":
            SESSION.paused = False
        elif action == "step":
            SESSION.paused = True
            SESSION.step = True
        elif action == "speed":
            SESSION.speed = float(msg.get("speed", 1.0))
        self._send(200, b'{"ok":true}', "application/json")

    def _stream(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        q = SESSION.add_client()

        def write(event, data):
            self.wfile.write(f"event: {event}\ndata: {json.dumps(data)}\n\n".encode())

        try:
            if SESSION.meta:
                write("meta", SESSION.meta)
            if SESSION.last_frame:
                write("frame", SESSION.last_frame)
            while True:
                try:
                    event, data = q.get(timeout=15)
                    write(event, data)
                except queue.Empty:
                    self.wfile.write(b": keepalive\n\n")   # comment ping
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            SESSION.drop_client(q)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8808)
    a = ap.parse_args()
    SESSION.start({"scenario": "arena", "organism": "protocell1",
                   "decay": "bitrot", "lam": 0.08})
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    print(f"Living Software visualizer → http://127.0.0.1:{a.port}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
