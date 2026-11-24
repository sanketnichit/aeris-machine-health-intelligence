"""Local research HTTP service. Not an internet-facing production server."""
import argparse
import hmac
import os
import json
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

from research.verify_evidence import verify, ROOT
from src.telemetry_contract import validate_batch, SCHEMA_VERSION, UNITS

from src.telemetry_store import DEFAULT_DB, initialize, register, ingest, fleet, history, Conflict, UnknownAsset, configure_policy, list_events

from src.incidents import configure_freshness, scan_freshness, transition, list_incidents

from src.decision_engine import assess_asset, benchmark_context

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

    def authorized(self, path):
        if path in ("/health","/v1/schema","/v1/evidence") or self.server.token is None:
            return True
        supplied=self.headers.get("Authorization","").encode("utf-8")
        if not hmac.compare_digest(supplied,("Bearer "+self.server.token).encode("utf-8")):
            self.reply(401,{"error":"Bearer token required"})
            return False
        return True

    def do_GET(self):
        path = urlsplit(self.path).path
        if not self.authorized(path):
            return
        if path == "/health":
            self.reply(200, {"status":"ok","service":"aeris-research-api"})
        elif path == "/v1/schema":
            self.reply(200, {"schema_version":SCHEMA_VERSION,"units":UNITS,
                             "scope":"Unit contract; ingestion is opt-in via storage routes, no inference"})
        elif path == "/v1/evidence":
            try:
                entries = verify(ROOT)
                version = VERSION_PATH.read_text(encoding="utf-8").strip()
            except (OSError,ValueError,KeyError,TypeError):
                self.reply(503, {"error":"Evidence integrity unavailable"})
                return
            self.reply(200, {"version":version,"evidence":entries,
                             "scope":"Research benchmark evidence, not industrial certification"})
        elif path in ("/v1/assets", "/v1/telemetry/history", "/v1/events", "/v1/incidents", "/v1/advisory"):
            if self.server.database is None:
                self.reply(503, {"error":"Telemetry storage disabled"})
                return
            try:
                query=parse_qs(urlsplit(self.path).query,strict_parsing=True,max_num_fields=4)
                limit=int(query.get("limit",["100" if path.endswith("history") else "200"])[0])
                if path=="/v1/assets":
                    result=fleet(self.server.database,limit)
                elif path=="/v1/advisory":
                    result=assess_asset(self.server.database,query["asset_id"][0])
                    try:
                        result["benchmark_context"]=benchmark_context()
                    except (OSError,ValueError,KeyError,TypeError):
                        self.reply(503,{"error":"Benchmark evidence integrity unavailable"})
                        return
                elif path=="/v1/incidents":
                    result=list_incidents(self.server.database,limit)
                elif path=="/v1/events":
                    result=list_events(self.server.database,query.get("asset_id",[None])[0],limit)
                else:
                    result={"asset_id":query["asset_id"][0],"records":history(self.server.database,query["asset_id"][0],limit)}
            except UnknownAsset as exc:
                self.reply(404,{"error":str(exc)})
                return
            except (ValueError,KeyError):
                self.reply(400,{"error":"Invalid query"})
                return
            except sqlite3.Error:
                self.reply(503,{"error":"Telemetry storage unavailable"})
                return
            self.reply(200,result)
        else:
            self.reply(404, {"error":"Route not found"})

    def do_POST(self):
        path=urlsplit(self.path).path
        if not self.authorized(path):
            return
        if path not in ("/v1/telemetry/validate","/v1/assets","/v1/telemetry/ingest","/v1/policies","/v1/freshness","/v1/freshness/scan","/v1/incidents/transition"):
            self.reply(404, {"error":"Route not found"})
            return
        if path!="/v1/telemetry/validate" and self.server.database is None:
            self.reply(503, {"error":"Telemetry storage disabled"})
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
            payload=decode(raw)
            if path=="/v1/telemetry/validate":
                result=validate_batch(payload)
            elif path=="/v1/assets":
                result=register(self.server.database,payload)
            elif path=="/v1/policies":
                if not isinstance(payload,dict) or set(payload)!={"asset_id","bounds"}:
                    raise ValueError("Expected asset_id and bounds")
                result=configure_policy(self.server.database,payload["asset_id"],{"bounds":payload["bounds"]})
            elif path=="/v1/freshness":
                if not isinstance(payload,dict) or set(payload)!={"asset_id","max_age_seconds"}:
                    raise ValueError("Expected asset_id and max_age_seconds")
                result=configure_freshness(self.server.database,payload["asset_id"],payload["max_age_seconds"])
            elif path=="/v1/freshness/scan":
                if payload!={}:
                    raise ValueError("Expected empty JSON object")
                result=scan_freshness(self.server.database)
            elif path=="/v1/incidents/transition":
                if not isinstance(payload,dict) or set(payload)!={"incident_id","action","note"}:
                    raise ValueError("Expected incident_id, action and note")
                result=transition(self.server.database,**payload)
            else:
                result=ingest(self.server.database,payload)
        except Conflict as exc:
            self.reply(409,{"error":str(exc)})
            return
        except UnknownAsset as exc:
            self.reply(404,{"error":str(exc)})
            return
        except sqlite3.Error:
            self.reply(503,{"error":"Telemetry storage unavailable"})
            return
        except (ValueError,UnicodeError,RecursionError) as exc:
            self.reply(400, {"error":str(exc) if isinstance(exc,ValueError) else "Invalid JSON"})
            return
        self.reply(200,result)


def make_server(host="127.0.0.1", port=8080, database=None, token=None):
    if token is not None and (not isinstance(token,str) or len(token)<32 or not token.isascii() or not token.isprintable() or any(c.isspace() for c in token)):
        raise ValueError("API token must be at least 32 printable non-space ASCII characters")
    if database is not None:
        initialize(database)
    server=ThreadingHTTPServer((host,port),Handler)
    server.database=database
    server.token=token
    return server


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--host",default="127.0.0.1")
    parser.add_argument("--port",type=int,default=8080)
    parser.add_argument("--database",type=Path,default=DEFAULT_DB)
    parser.add_argument("--validation-only",action="store_true")
    args=parser.parse_args()
    with make_server(args.host,args.port,None if args.validation_only else args.database,token=os.environ.get("AERIS_API_TOKEN") or None) as server:
        print(f"AERIS research API listening on {args.host}:{args.port}",flush=True)
        server.serve_forever()
