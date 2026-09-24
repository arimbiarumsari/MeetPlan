"""Minimal HTTP entrypoint for the MeetPlan scheduler service."""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from service import readiness_report, recommend_payload


class SchedulerHandler(BaseHTTPRequestHandler):
    server_version = "MeetPlanScheduler/0.1"

    def _send_json(self, status: int, payload: object) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        if self.path == "/health":
            self._send_json(200, {"status": "ok", "service": "scheduler"})
            return
        if self.path == "/ready":
            try:
                self._send_json(200, readiness_report())
            except RuntimeError as error:
                self._send_json(503, {"status": "not_ready", "error": str(error)})
            return
        self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        if self.path != "/recommend":
            self._send_json(404, {"error": "not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            response = recommend_payload(payload)
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            self._send_json(400, {"error": str(error)})
            return

        self._send_json(200, response)

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), SchedulerHandler)
    print(f"MeetPlan scheduler listening on port {port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
