"""Read-only engineering review advisory; no operational model or automatic action."""
from datetime import datetime, timezone
import json

from src.anomaly import deviation_series
from src.monitoring import evaluate
from src.telemetry_contract import ASSET
from src.telemetry_store import connection, UnknownAsset

POLICY_VERSION="review-v1"
DEVIATION_LIMIT=6.0
HISTORY_LIMIT=1000


def assess_asset(path, asset, now=None):
    if not isinstance(asset,str) or not ASSET.fullmatch(asset):
        raise ValueError("Invalid asset identifier")
    now=now if now is not None else datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Timezone required")
    now=now.astimezone(timezone.utc)
    # Consistent read snapshot across telemetry, configuration and incident state.
    with connection(path) as db:
        db.execute("BEGIN")
        metadata=db.execute("SELECT * FROM assets WHERE asset_id=?",(asset,)).fetchone()
        if metadata is None:
            raise UnknownAsset("Unknown asset")
        policy=db.execute("SELECT revision,bounds FROM policies WHERE asset_id=?",(asset,)).fetchone()
        freshness=db.execute("SELECT max_age_seconds FROM freshness WHERE asset_id=?",(asset,)).fetchone()
        rows=db.execute("SELECT timestamp,measurements FROM observations WHERE asset_id=? ORDER BY timestamp DESC LIMIT ?",(asset,HISTORY_LIMIT)).fetchall()
        active=db.execute("SELECT incident_id,kind,status FROM incidents WHERE asset_id=? AND status!='resolved' ORDER BY incident_id",(asset,)).fetchall()
    records=[{"timestamp":r["timestamp"],"measurements":json.loads(r["measurements"])} for r in reversed(rows)]
    expected=json.loads(metadata["expected"])
    bounds=json.loads(policy["bounds"]) if policy else {}
    latest=records[-1] if records else None
    age=None
    data_reasons=[]
    review_reasons=[]
    signals={}
    if freshness is None:
        data_reasons.append({"code":"freshness_not_configured"})
    if not records:
        data_reasons.append({"code":"no_observations"})
    else:
        age=(now-datetime.fromisoformat(latest["timestamp"].replace("Z","+00:00"))).total_seconds()
        if age<0:
            data_reasons.append({"code":"future_timestamp","age_seconds":age})
        elif freshness and age>freshness["max_age_seconds"]:
            data_reasons.append({"code":"stale_observation","age_seconds":age,"limit_seconds":freshness["max_age_seconds"]})
        for kind,detail in evaluate(expected,latest["measurements"],bounds):
            reason={"code":kind,**detail}
            (data_reasons if kind=="missing_measurements" else review_reasons).append(reason)
        for name in expected:
            point=deviation_series(records,name)[-1]
            signals[name]=point
            if point["status"]!="scored":
                data_reasons.append({"code":"deviation_unavailable","measurement":name,"reason":point["status"]})
            elif point["score"]>=DEVIATION_LIMIT:
                review_reasons.append({"code":"exploratory_deviation","measurement":name,"score":point["score"],"threshold":DEVIATION_LIMIT})
    for item in active:
        review_reasons.append({"code":"active_review_incident",**dict(item)})
    status=("review_required" if review_reasons else
            "insufficient_evidence" if data_reasons else "no_current_rule_trigger")
    recommendation={"review_required":"Review the listed observations and open incidents with an engineer.",
                    "insufficient_evidence":"Check telemetry completeness, timing and baseline availability.",
                    "no_current_rule_trigger":"Continue observation; absence of a rule trigger does not establish healthy operation."}[status]
    return {"asset_id":asset,"policy_version":POLICY_VERSION,
            "assessed_at":now.isoformat(),"latest_timestamp":latest["timestamp"] if latest else None,
            "latest_age_seconds":age,"history_records":len(records),
            "configured_policy_revision":policy["revision"] if policy else 0,
            "freshness_limit_seconds":freshness["max_age_seconds"] if freshness else None,
            "status":status,"recommendation":recommendation,
            "data_reasons":data_reasons,"review_reasons":review_reasons,"deviations":signals,
            "forecast":{"status":"withheld","remaining_life":None,"failure_probability":None,
                        "model_disagreement":None,"calibrated_interval":None,
                        "reasons":["no_asset_validated_model","no_asset_specific_calibration",
                                   "no_verified_operational_transfer"]},
            "scope":"Local research review only. No health certification, automatic maintenance action or operational failure forecast."}
