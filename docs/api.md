# AERIS local research API

This is a versioned, validation-only development interface. It uses Python's standard-library HTTP server and is not intended for public internet exposure. No authentication, durable telemetry storage, live model inference or equipment control is provided. Do not send confidential production telemetry.

## Start

With Docker and Docker Compose installed, from the repository root:

```bash
docker compose up --build --detach --wait
```

Dashboard: http://127.0.0.1:8501

API: http://127.0.0.1:8080

Both host ports bind to loopback. Containers run as an unprivileged user, with capabilities dropped. The API filesystem is read-only. The dashboard can write local benchmark data when the AI4I workspace is selected.

Without Docker, run `python -m src.api` and `python -m streamlit run app.py` in separate terminals using the quickstart environment.

## Endpoints

| Method | Route | Contract |
|---|---|---|
| GET | /health | Process health |
| GET | /v1/schema | Telemetry version and measurement unit registry |
| GET | /v1/evidence | Verified evidence file metadata, revisions and run links; HTTP 503 on integrity failure |
| POST | /v1/telemetry/validate | Validate and normalize a telemetry batch; no persistence or forecast |

Example request body:

```json
{
  "schema_version": 1,
  "records": [
    {
      "asset_id": "demo-bearing",
      "timestamp": "2026-11-24T12:00:00Z",
      "measurements": {
        "horizontal_vibration_rms": {"value": 1.25, "unit": "m/s2"}
      }
    }
  ]
}
```

Save as telemetry.json and submit:

```bash
curl -H "Content-Type: application/json" --data-binary @telemetry.json http://127.0.0.1:8080/v1/telemetry/validate
```

Use curl.exe in Windows PowerShell. Response includes normalized UTC timestamps, record and asset counts, status validated_only, persisted=false and forecast=null. The API does not infer units or silently convert them. It rejects duplicate JSON keys, invalid timestamps, nonfinite numeric measurements, unknown fields and units, and non-increasing per-asset timestamps within the batch. Limits: 1 MiB body and 1000 records. These are contract checks, not calibrated engineering operating limits.

## Limits

No cross-batch deduplication, historical persistence, rate limiting, TLS or access control. Use only locally for research integration. A production service would need a hardened server, authenticated transport, durable ingestion, asset-specific validation, monitoring and independent operational evidence.

Stop containers with `docker compose down`.
