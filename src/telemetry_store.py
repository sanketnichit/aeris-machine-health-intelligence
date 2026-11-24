"""Local research telemetry storage; no operational forecasts or health diagnosis."""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from src.telemetry_contract import ASSET, UNITS, validate_batch

DEFAULT_DB = Path(__file__).resolve().parents[1]/"data"/"telemetry.sqlite3"


class Conflict(ValueError):
    pass


class UnknownAsset(ValueError):
    pass


@contextmanager
def connection(path):
    db=sqlite3.connect(path,timeout=5)
    db.row_factory=sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    try:
        with db:
            yield db
    finally:
        db.close()


def initialize(path):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    with connection(path) as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("BEGIN IMMEDIATE")
        version=db.execute("PRAGMA user_version").fetchone()[0]
        if version not in (0,1):
            raise ValueError("Unsupported telemetry storage version")
        db.execute("""CREATE TABLE IF NOT EXISTS assets (
            asset_id TEXT PRIMARY KEY, name TEXT NOT NULL, expected TEXT NOT NULL
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS observations (
            asset_id TEXT NOT NULL REFERENCES assets(asset_id),
            timestamp TEXT NOT NULL, measurements TEXT NOT NULL,
            PRIMARY KEY(asset_id,timestamp)
        )""")
        db.execute("PRAGMA user_version=1")


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False)


def register(path,payload):
    if not isinstance(payload,dict) or set(payload)!={"asset_id","name","expected_measurements"}:
        raise ValueError("Expected asset_id, name and expected_measurements")
    asset,name,expected=(payload[k] for k in ("asset_id","name","expected_measurements"))
    if not isinstance(asset,str) or not ASSET.fullmatch(asset):
        raise ValueError("Invalid asset identifier")
    if not isinstance(name,str) or not 1<=len(name.strip())<=100 or not name.isprintable():
        raise ValueError("Invalid asset name")
    if (not isinstance(expected,list) or not expected
        or any(not isinstance(x,str) or x not in UNITS for x in expected)
        or len(set(expected))!=len(expected)):
        raise ValueError("Invalid expected measurements")
    name=name.strip()
    encoded=canonical(sorted(expected))
    with connection(path) as db:
        db.execute("BEGIN IMMEDIATE")
        row=db.execute("SELECT name,expected FROM assets WHERE asset_id=?",(asset,)).fetchone()
        if row is not None:
            if (row["name"],row["expected"])!=(name,encoded):
                raise Conflict("Asset already registered with different metadata")
            created=False
        else:
            db.execute("INSERT INTO assets VALUES (?,?,?)",(asset,name,encoded))
            created=True
    return {"asset_id":asset,"name":name,"expected_measurements":sorted(expected),"created":created}


def ingest(path,payload):
    batch=validate_batch(payload)
    inserted=duplicates=0
    with connection(path) as db:
        db.execute("BEGIN IMMEDIATE")
        for record in batch["records"]:
            asset=record["asset_id"]
            if not db.execute("SELECT 1 FROM assets WHERE asset_id=?",(asset,)).fetchone():
                raise UnknownAsset(f"Unregistered asset: {asset}")
            # Fixed-width UTC timestamp preserves chronological string ordering.
            stamp=datetime.fromisoformat(record["timestamp"].replace("Z","+00:00")).isoformat(timespec="microseconds").replace("+00:00","Z")
            measurements=canonical(record["measurements"])
            row=db.execute("SELECT measurements FROM observations WHERE asset_id=? AND timestamp=?",(asset,stamp)).fetchone()
            if row:
                if row["measurements"]!=measurements:
                    raise Conflict(f"Conflicting observation: {asset} at {stamp}")
                duplicates+=1
            else:
                db.execute("INSERT INTO observations VALUES (?,?,?)",(asset,stamp,measurements))
                inserted+=1
    return {"status":"stored","inserted":inserted,"duplicates":duplicates,"persisted":True,"forecast":None}


def history(path,asset,limit=100):
    if not isinstance(asset,str) or not ASSET.fullmatch(asset):
        raise ValueError("Invalid asset identifier")
    if type(limit) is not int or not 1<=limit<=1000:
        raise ValueError("History limit must be 1 to 1000")
    with connection(path) as db:
        if not db.execute("SELECT 1 FROM assets WHERE asset_id=?",(asset,)).fetchone():
            raise UnknownAsset("Unknown asset")
        rows=db.execute("SELECT timestamp,measurements FROM observations WHERE asset_id=? ORDER BY timestamp DESC LIMIT ?",(asset,limit)).fetchall()
    return [{"timestamp":r["timestamp"],"measurements":json.loads(r["measurements"])} for r in reversed(rows)]


def fleet(path,limit=200):
    if type(limit) is not int or not 1<=limit<=1000:
        raise ValueError("Fleet limit must be 1 to 1000")
    with connection(path) as db:
        db.execute("BEGIN")
        assets=db.execute("SELECT * FROM assets ORDER BY asset_id LIMIT ?",(limit,)).fetchall()
        total=db.execute("SELECT count(*) FROM assets").fetchone()[0]
        result=[]
        for a in assets:
            n=db.execute("SELECT count(*) FROM observations WHERE asset_id=?",(a["asset_id"],)).fetchone()[0]
            latest=db.execute("SELECT timestamp,measurements FROM observations WHERE asset_id=? ORDER BY timestamp DESC LIMIT 1",(a["asset_id"],)).fetchone()
            expected=json.loads(a["expected"])
            observed=json.loads(latest["measurements"]) if latest else {}
            missing=sorted(set(expected)-set(observed))
            result.append({"asset_id":a["asset_id"],"name":a["name"],"observations":n,
                           "latest_timestamp":latest["timestamp"] if latest else None,
                           "expected_measurements":expected,"missing_latest":missing,
                           "quality":"no_data" if latest is None else ("incomplete" if missing else "complete")})
    return {"assets":result,"total_assets":total,"truncated":total>limit,"scope":"Data completeness only; not machine health."}
