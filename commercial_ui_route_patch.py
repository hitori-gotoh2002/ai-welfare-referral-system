from __future__ import annotations

from urllib.parse import urlparse

import backend_server as b


def apply() -> None:
    if getattr(b, "COMMERCIAL_UI_ROUTE_PATCH_APPLIED", False):
        return

    native_do_get = b.WelfareHandler.do_GET

    def patched_do_get(self):
        parsed = urlparse(self.path)
        if parsed.path == "/commercial-ui-polish.js":
            body = (b.ROOT / "commercial-ui-polish.js").read_bytes()
            self.send_response(b.HTTPStatus.OK)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path == "/commercial-ui-style-fix.js":
            body = (b.ROOT / "commercial-ui-style-fix.js").read_bytes()
            self.send_response(b.HTTPStatus.OK)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return native_do_get(self)

    b.WelfareHandler.do_GET = patched_do_get
    b.COMMERCIAL_UI_ROUTE_PATCH_APPLIED = True
