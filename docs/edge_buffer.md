# Edge telemetry buffer (development add-on)

This module is an opt-in local research integration tool after the immutable v0.1.0 release. It does not connect physical sensors or change the released forecast policy.

## Why

A sensor acquisition process should be able to stage validated observations even when the AERIS ingestion service is unavailable. The SQLite queue persists normalized batches across process restarts; the API already supports idempotent ingestion.

## Try it locally

Register the intended asset with the local API first (see [API documentation](api.md)). Save a schema-version-1 batch as telemetry.json. The queue may be created even when the API is stopped.

```bash
python -m src.edge_buffer --queue edge.sqlite3 enqueue telemetry.json
python -m src.edge_buffer --queue edge.sqlite3 status
python -m src.edge_buffer --queue edge.sqlite3 drain
```

Set AERIS_API_TOKEN in the client environment when the local API requires it. Keep the queue file outside version control and use nonconfidential data.

## Delivery semantics

- Validation and canonical UTC normalization happen before enqueue.
- At most 1000 pending batches, each at most 1 MiB and 1000 records. Capacity exhaustion rejects new batches without deleting old ones.
- A SHA-256 digest deduplicates identical normalized pending batches. This is not a cryptographic authenticity guarantee.
- Replay is FIFO and bounded to 100 batches per invocation by default. A successful stored acknowledgement must account for every submitted record through inserted and duplicate counts.
- Failed HTTP responses, incomplete responses, outages and ambiguous acknowledgements retain the pending batch. A nonzero drain exit code indicates blocked delivery. Register missing assets or investigate conflicts before retrying.
- A crash after the server commits but before local deletion causes a retry; unchanged server records are idempotent. Delivery is at-least-once, not exactly-once. Use one drainer per queue.
- Local queue records are not encrypted; backups, retention, queue compaction and manual conflict resolution are operator responsibilities.

Only explicit loopback HTTP endpoints are allowed; redirects and proxies are disabled. There is no remote connection, automatic background retry, hardware driver, broker, production authentication or field calibration. The buffer does not predict or control machinery.

## Next-generation acceptance

The regression tests exercise offline persistence, capacity, validation, endpoint restrictions, authenticated API rejection and duplicate replay. Subsequent milestones should cover sustained outage/recovery under measured workloads, acquisition adapters with explicit units, independent physical benchmark validation, and improved operator presentation. Each needs separate verified evidence before any production claim.
