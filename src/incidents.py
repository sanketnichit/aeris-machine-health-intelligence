"""Local review workflow; freshness is not a diagnosis of communication failure."""
from datetime import datetime, timezone
import json
from src.telemetry_store import connection, canonical, UnknownAsset, Conflict
from src.telemetry_contract import ASSET


def stamp(now=None):
    now=now if now is not None else datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Timezone required")
    return now.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00","Z")


def initialize_incidents(db):
    db.execute("""CREATE TABLE IF NOT EXISTS freshness (
        asset_id TEXT PRIMARY KEY REFERENCES assets(asset_id),
        max_age_seconds INTEGER NOT NULL
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS incidents (
        incident_id INTEGER PRIMARY KEY, asset_id TEXT NOT NULL REFERENCES assets(asset_id),
        kind TEXT NOT NULL, opened_at TEXT NOT NULL, status TEXT NOT NULL,
        detail TEXT NOT NULL, updated_at TEXT NOT NULL
    )""")
    db.execute("""CREATE UNIQUE INDEX IF NOT EXISTS incident_active
        ON incidents(asset_id,kind) WHERE status!='resolved'""")
    db.execute("""CREATE TABLE IF NOT EXISTS incident_history (
        action_id INTEGER PRIMARY KEY, incident_id INTEGER NOT NULL REFERENCES incidents(incident_id),
        timestamp TEXT NOT NULL, action TEXT NOT NULL, note TEXT NOT NULL
    )""")


def configure_freshness(path,asset,seconds):
    if not isinstance(asset,str) or not ASSET.fullmatch(asset):
        raise ValueError("Invalid asset identifier")
    if type(seconds) is not int or not 1<=seconds<=604800:
        raise ValueError("Freshness seconds must be 1 to 604800")
    with connection(path) as db:
        db.execute("BEGIN IMMEDIATE")
        if not db.execute("SELECT 1 FROM assets WHERE asset_id=?",(asset,)).fetchone():
            raise UnknownAsset("Unknown asset")
        db.execute("INSERT INTO freshness VALUES (?,?) ON CONFLICT(asset_id) DO UPDATE SET max_age_seconds=excluded.max_age_seconds",(asset,seconds))
    return {"asset_id":asset,"max_age_seconds":seconds}


def open_incident(db,asset,kind,detail,now):
    row=db.execute("SELECT incident_id FROM incidents WHERE asset_id=? AND kind=? AND status!='resolved'",(asset,kind)).fetchone()
    if row:
        db.execute("UPDATE incidents SET detail=?,updated_at=? WHERE incident_id=?",(canonical(detail),now,row[0]))
        return False
    cursor=db.execute("INSERT INTO incidents(asset_id,kind,opened_at,status,detail,updated_at) VALUES (?,?,?,?,?,?)",
                      (asset,kind,now,"open",canonical(detail),now))
    db.execute("INSERT INTO incident_history(incident_id,timestamp,action,note) VALUES (?,?,?,?)",(cursor.lastrowid,now,"opened","Automatic observation review"))
    return True


def scan_freshness(path,now=None):
    current=stamp(now)
    dt=datetime.fromisoformat(current.replace("Z","+00:00"))
    opened=0
    with connection(path) as db:
        db.execute("BEGIN IMMEDIATE")
        rows=db.execute("""SELECT f.asset_id,f.max_age_seconds,
            (SELECT max(timestamp) FROM observations o WHERE o.asset_id=f.asset_id) AS latest
            FROM freshness f ORDER BY f.asset_id""").fetchall()
        for row in rows:
            latest=row["latest"]
            age=(dt-datetime.fromisoformat(latest.replace("Z","+00:00"))).total_seconds() if latest else None
            if age is None or age>row["max_age_seconds"] or age<0:
                kind="telemetry_freshness"
                reason="no_data" if age is None else ("future_timestamp" if age<0 else "stale_data")
                opened+=open_incident(db,row["asset_id"],kind,{"reason":reason,"latest":latest,"age_seconds":age,"max_age_seconds":row["max_age_seconds"]},current)
    return {"scanned_assets":len(rows),"opened":opened,"scan_time":current,"scope":"Explicit scan; manual review required, no automatic resolution."}


def transition(path,incident_id,action,note):
    if type(incident_id) is not int or incident_id<1 or action not in ("acknowledge","resolve"):
        raise ValueError("Invalid incident transition")
    if not isinstance(note,str) or not 1<=len(note.strip())<=500 or not note.isprintable():
        raise ValueError("Provide a printable review note")
    now=stamp()
    with connection(path) as db:
        db.execute("BEGIN IMMEDIATE")
        row=db.execute("SELECT status FROM incidents WHERE incident_id=?",(incident_id,)).fetchone()
        if not row:
            raise UnknownAsset("Unknown incident")
        expected="open" if action=="acknowledge" else "acknowledged"
        target="acknowledged" if action=="acknowledge" else "resolved"
        if row["status"]!=expected:
            raise Conflict("Invalid incident state transition")
        db.execute("UPDATE incidents SET status=?,updated_at=? WHERE incident_id=?",(target,now,incident_id))
        db.execute("INSERT INTO incident_history(incident_id,timestamp,action,note) VALUES (?,?,?,?)",(incident_id,now,target,note.strip()))
    return {"incident_id":incident_id,"status":target}


def list_incidents(path,limit=100):
    if type(limit) is not int or not 1<=limit<=1000:
        raise ValueError("Limit must be 1 to 1000")
    with connection(path) as db:
        rows=db.execute("SELECT * FROM incidents ORDER BY incident_id DESC LIMIT ?",(limit,)).fetchall()
        result=[]
        for row in rows:
            actions=db.execute("SELECT timestamp,action,note FROM incident_history WHERE incident_id=? ORDER BY action_id",(row["incident_id"],)).fetchall()
            result.append({**dict(row),"detail":json.loads(row["detail"]),"history":[dict(a) for a in actions]})
    return {"incidents":result,"scope":"Local review incidents, not diagnosed equipment failures."}
