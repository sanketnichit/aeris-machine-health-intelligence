"""Local research HTTP service. Not an internet-facing production server."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from research.verify_evidence import verify, ROOT
from src.telemetry_contract import validate_batch, SCHEMA_VERSION, UNITS

MAX_BODY = 1024 * 1024
VERSION_PATH = Path(__file__).resolve().parents[1] / "VERSION"


def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("Duplicate JSON member")
        obj[key] = value
    return obj


def decode(body):
    def reject(_):
        raise ValueError("Nonfinite JSON constant")
    return json.loads(body.decode("utf-8"), object_pairs_hook=unique_object,
                      parse_constant=reject)


class Handler(BaseHTTPRequestHandler):
    server_version = "AERISResearchAPI/1"
    sys_version = ""

    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def reply(self, status, data):
        raw = json.dumps(data, allow_nan=False, separators=(",",":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/health":
            self.reply(200, {"status":"ok","service":"aeris-research-api"})
        elif path == "/v1/schema":
            self.reply(200, {"schema_version":SCHEMA_VERSION,"units":UNITS,
                             "scope":"validation only, not persistence or inference"})
        elif path == "/v1/evidence":
            try:
                entries = verify(ROOT)
                version = VERSION_PATH.read_text(encoding="utf-8").strip()
            except (OSError,ValueError,KeyError,TypeError):
                self.reply(503, {"error":"Evidence integrity unavailable"})
                return
            self.reply(200, {"version":version,"evidence":entries,
                             "scope":"Research benchmark evidence, not industrial certification"})
        else:
            self.reply(404, {"error":"Route not found"})

    def do_POST(self):
        if urlsplit(self.path).path != "/v1/telemetry/validate":
            self.reply(404, {"error":"Route not found"})
            return
        if self.headers.get("Transfer-Encoding"):
            self.reply(400, {"error":"Transfer encoding unsupported"})
            return
        if self.headers.get_content_type() != "application/json":
            self.reply(415, {"error":"Expected application/json"})
            return
        lengths = self.headers.get_all("Content-Length", [])
        if len(lengths)!=1 or not lengths[0].isascii() or not lengths[0].isdigit() or len(lengths[0])>10:
            self.reply(400, {"error":"Valid Content-Length required"})
            return
        size=int(lengths[0])
        if not 1<=size<=MAX_BODY:
            self.reply(413, {"error":"Body exceeds allowed size or is empty"})
            return
        try:
            raw=self.rfile.read(size)
            if len(raw)!=size:
                raise ValueError("Incomplete body")
            result=validate_batch(decode(raw))
        except (ValueError,UnicodeError,RecursionError) as exc:
            self.reply(400, {"error":str(exc) if isinstance(exc,ValueError) else "Invalid JSON"})
            return
        self.reply(200,result)


def make_server(host="127.0.0.1", port=8080):
    return ThreadingHTTPServer((host,port),Handler)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--host",default="127.0.0.1")
    parser.add_argument("--port",type=int,default=8080)
    args=parser.parse_args()
    with make_server(args.host,args.port) as server:
        print(f"AERIS research API listening on {args.host}:{args.port}",flush=True)
        server.serve_forever()
