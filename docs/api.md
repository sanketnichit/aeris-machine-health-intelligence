# AERIS local research API

This is a versioned local research telemetry interface. It uses Python's standard-library HTTP server and is not intended for public internet exposure. SQLite persistence is local; optional shared-token authentication is available; no live model inference or equipment control is provided. Do not send confidential production telemetry.

## Start

With Docker and Docker Compose installed, from the repository root:

```bash
docker compose up --build --detach --wait
```

Dashboard: http://127.0.0.1:8501

API: http://127.0.0.1:8080

Both host ports bind to loopback. Containers run as an unprivileged user, with capabilities dropped. The API filesystem is read-only except for a named telemetry-data volume. The dashboard can write local benchmark data when the AI4I workspace is selected.

Without Docker, run `python -m src.api` and `python -m streamlit run app.py` in separate terminals using the quickstart environment.

## Endpoints

| Method | Route | Contract |
|---|---|---|
| GET | /health | Process health |
| GET | /v1/schema | Telemetry version and measurement unit registry |
| GET | /v1/evidence | Verified evidence file metadata, revisions and run links; HTTP 503 on integrity failure |
| POST | /v1/telemetry/validate | Validate and normalize a telemetry batch; no persistence or forecast |
| POST | /v1/assets | Register asset metadata and expected measurements |
| GET | /v1/assets | Fleet completeness overview (bounded list) |
| POST | /v1/telemetry/ingest | Store a validated batch atomically |
| GET | /v1/telemetry/history?asset_id=demo-bearing | Retrieve latest records in chronological order |

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

## Persistent telemetry

Register before ingestion:

```json
{"asset_id":"demo-bearing","name":"Demo bearing","expected_measurements":["horizontal_vibration_rms","vertical_vibration_rms"]}
```

POST the asset metadata to /v1/assets, then POST telemetry.json to /v1/telemetry/ingest. Identical registered metadata and identical timestamp/measurement records are idempotent; conflicting records return HTTP 409. Unknown assets return HTTP 404. Invalid batches roll back entirely. Missing expected measurements remain missing and are reported in the fleet view; completeness is not health. Cross-batch historical backfill is accepted. History returns at most 1000 observations. Local CLI storage defaults to data/telemetry.sqlite3; --database selects a different path, --validation-only disables storage.

Choose Telemetry fleet in the dashboard sidebar. Compose configures its internal API address. For a non-container deployment use AERIS_API_URL to configure the service address (default http://127.0.0.1:8080).

The named volume survives ordinary container restarts and docker compose down. **docker compose down --volumes deletes stored telemetry.** Back up storage before removal. Do not expose this service publicly or send confidential data.

## Limits

No rate limiting, TLS or per-user access control; no retention policy or production backup management. Use only locally for research integration. A production service would need a hardened server, authenticated transport, durable ingestion, asset-specific validation, monitoring and independent operational evidence.

Stop containers with `docker compose down`.


## Monitoring and synthetic demonstration

POST /v1/policies with {"asset_id":"demo-bearing","bounds":{"horizontal_vibration_rms":{"max":2.0}}} to configure illustrative observation limits in the canonical measurement units. Empty bounds disable numeric limit checks, not missing-measurement checks. Each changed policy receives a new revision; identical submissions preserve the revision. GET /v1/events?limit=100 returns recent persisted observation events; optional asset_id filters the result.

Ingested records and their events commit atomically. Duplicate observations create no extra events. Policy changes do not recompute historical events. Events are ordered by ingestion, including backfills, and are not active incidents. Existing databases migrate automatically to schema version 3; preexisting observations are not retrospectively evaluated.

With the local service running, execute:

```bash
python scripts/demo_fleet.py
```

This inserts 180 deterministic synthetic observations for three explicitly named synthetic assets. Ten observations have an intentionally missing signal; one asset has injected vibration drift. Re-running against unchanged demo policies and data is idempotent. The fixed timestamps and illustrative 2 m/s2 bound are demo choices, not calibrated equipment limits. Use a separate local demonstration database rather than confidential production telemetry.

The fleet workspace exposes recent event history and export. Notification delivery and operational health diagnosis are not provided. Incident review is described below.


## Incident review and freshness

Schema 3 records one active review incident per asset and event kind. New observation-level events update the active incident; all individual events remain in the event table. Ingested historical backfills may also open review incidents. Previous records are not retroactively turned into incidents.

- POST /v1/freshness: {"asset_id":"demo-bearing","max_age_seconds":60} configures an explicit freshness threshold.
- POST /v1/freshness/scan: {} checks configured assets against the service UTC clock. Missing, stale, and future-dated telemetry open or update review incidents. No communication failure is inferred.
- GET /v1/incidents?limit=100 lists incidents and review history.
- POST /v1/incidents/transition: {"incident_id":1,"action":"acknowledge","note":"Review started"} acknowledges an open incident. Use action "resolve" with a review note after acknowledgement.

Resolution is manual and is not evidence of repair. A subsequent scan or new event can open another incident. Freshness scans may be triggered explicitly or by the opt-in local worker below. No external notifications are provided.

## Optional local token

Set AERIS_API_TOKEN to a randomly generated token of at least 32 printable non-space ASCII characters in the local process environment before starting the service. Compose passes this environment variable to both containers. The fleet dashboard and demonstration client read it from their environment. Send Authorization: Bearer TOKEN on protected routes. Health, schema and published evidence remain public. Without a token, the service remains unauthenticated and local-only. This is a shared token, not role-based access control; it does not replace TLS, network isolation or production authentication. Never commit tokens or expose the configured dashboard publicly.

## Backup and recovery

Use the SQLite online backup utility rather than copying a database while its WAL is active:

```bash
python scripts/telemetry_backup.py data/telemetry.sqlite3 backups/telemetry.sqlite3
python scripts/telemetry_backup.py backups/telemetry.sqlite3 data/recovered.sqlite3
python -m src.api --database data/recovered.sqlite3
```

Use a new destination each time; existing files are not overwritten. The utility checks database and foreign-key integrity, then publishes the backup atomically on a filesystem supporting hard links. For Docker storage, run the utility where the volume is mounted with authorized access. Backups may contain sensitive data; protect them. Automated scheduling, encrypted backups and production disaster-recovery guarantees are not provided.


## Periodic monitoring and reviewer UI

Start the optional local worker using:

```bash
docker compose --profile monitoring up --build --detach --wait
```

Or from the same local Python environment, in a separate terminal:

```bash
python -m src.monitor_worker --interval 30
```

Use --database to select the same storage path as the API, and --once for a single scan. Only configured assets are scanned. SQLite transactions serialize updates with ingestion. The worker logs scans and database failures, stops on SIGINT/SIGTERM and retries database failures on the next interval. This is a local process, not an external notification or production availability guarantee.

Set AERIS_ENABLE_REVIEW_ACTIONS=1 for a trusted local dashboard to acknowledge and resolve incidents from the review form. The API still enforces transitions. The default UI is read-only. Do not enable the actions on an exposed dashboard: the shared server token is not user-level authorization.

The fleet signal view includes an exploratory robust deviation score based on the median and scaled median absolute deviation of the preceding 30 available measurements (at least 10). Missing measurements and near-zero scales abstain. The current point is excluded from its own baseline; only the displayed history is used. Scores are not calibrated anomaly probabilities, failure diagnoses, or automatic incident triggers.

For a paced, finite historical synthetic demonstration against an empty demo store:

```bash
python scripts/demo_fleet.py --pace 1
```

Each timestamp group is sent separately. Observation timestamps remain fixed historical demo times, so do not interpret them as current freshness or hardware communication. Refresh the fleet dashboard manually to observe progress. Replay can be repeated without duplicating identical observations.


## Decision intelligence

GET /v1/advisory?asset_id=demo-bearing returns a read-only assessment from a consistent SQLite snapshot of the latest 1000 observations, registered signal expectations, current configured bounds, freshness limits and unresolved review incidents.

Review policy review-v1 uses an exploratory robust deviation threshold of 6 scaled median absolute deviations (30 preceding observed values, minimum 10). This is a fixed illustrative policy, not a validated anomaly alarm. Review-required takes precedence over insufficient-evidence when both apply; both reason lists are retained. No-current-rule-trigger means no rule fired, not healthy operation. Current bounds are evaluated against the latest stored observation even when it was originally ingested under a different policy; historical events retain their original policy revision. Stale or future timestamps are flagged, and their descriptive scores are not validated current-state evidence.

The response separately attaches integrity-verified historical XJTU reliability and independent PRONOSTIA replication summaries. Those summaries describe other populations and are not operational calibration. If evidence verification fails the endpoint returns HTTP 503. Operational remaining life, failure probability, asset model disagreement and calibrated intervals are always null: no asset-validated model or transfer protocol exists. No incident state or equipment action is modified by assessment.

The fleet Decision intelligence panel displays the reasons, provenance context and downloadable JSON assessment. A decision is computed on request, not persisted as a new incident.


## Disposable reliability validation

The reliability-smoke workflow starts the authenticated Compose monitoring profile and runs scripts/reliability_smoke.py against a fresh synthetic database. It checks concurrent idempotent submissions, conflicting-record rejection, unauthorized route access, stale-data detection by the actual periodic worker, and concurrent incident acknowledgement. It then backs up and recovers the live SQLite volume using the runtime backup utility and checks recovered observations and review history.

The browser workflow also exercises opt-in acknowledgement from the trusted local dashboard. It verifies the persisted API state rather than reading rendered table text. These are bounded regression workloads, not throughput, denial-of-service resilience, production security or disaster-recovery certification. Do not run the integration script against existing user data.

Inside an authorized local Compose deployment, the backup utility is included in the API image. For example, use docker compose exec -T api python scripts/telemetry_backup.py data/telemetry.sqlite3 data/backup.sqlite3. Copy the verified backup to protected storage outside the volume before deleting or replacing the volume. Keep recovery destinations separate; the utility never overwrites an existing file.
