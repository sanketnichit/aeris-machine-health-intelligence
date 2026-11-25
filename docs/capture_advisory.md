# Offline capture-to-advisory research workflow

This is a **read-only research interface**, not a production diagnosis, live monitoring rule or equipment-control mechanism. It joins the existing immutable local capture archive to the frozen MFPT envelope recipe, an explicitly pinned measurement context, externally enrolled calibration metadata and the common-mode guard.

1. Archive a two-axis acceleration CSV with explicit unit, sample clock, start time and clipping range. Use 12,000 Hz, four complete 8,192-sample windows and no quality flags for this frozen experiment. Other shapes are withheld rather than silently resampled. See [capture archive](capture_archive.md).
2. An independent measurement authority must establish simultaneous speed indications, applicable geometry (effective inner, outer, and twice-ball defect orders), individual and shared deterministic error bounds, calibration validity covering the observation, and clock/speed stationarity. Do not estimate bounds from fault labels.
3. Create the canonical enrollment JSONs (UTF-8, sorted keys, separators comma/colon, no NaN) containing each record's metadata and certificate SHA-256. The enrollment SHA-256 is not a field in the enrolled JSON itself. The externally trusted pin directory contains the raw certificate and enrollment bytes, each filename exactly its SHA-256. Merely generating these bytes locally does not make them authoritative.
4. Create a pinned context JSON with exactly the following fields: capture_id, capture_sha256, asset_id, axis, observed_from, observed_until, primary_speed_hz, secondary_speed_hz, effective_orders (inner/outer/ball), primary, secondary, common. The latter three include the enrollment SHA-256 in addition to the enrolled fields defined in src/calibration_provenance.py. Observation times are UTC and must cover the complete capture. Pin the context bytes under their SHA-256 in the same separately controlled directory.
5. Run the offline advisory:

```sh
python -m research.capture_advisory --archive archive.sqlite --capture-id <capture-id> --trusted-pins trusted-pins --context-sha256 <context-digest> --output advisory.json
```

The output file must not exist; original capture and evidence are untouched. No network requests or actuation occur. The result includes an advisory next action and explicitly denies operational authorization. Incorrect, missing, expired, unpinned or mismatched metadata withholds a suggestion. Invalid archive/pin-directory integrity fails the command.

Trust boundary: this tool checks bytes and scope, not signature authenticity, instrument identity, actual speed stationarity, sensor placement, certificate issuer, field applicability or clock correctness. The pinned context must be supplied by a genuinely trusted enrollment process; arbitrary operator-generated pins do not establish calibration. The synthetic decision lab demonstrates mechanics only. The existing telemetry API and incident system do not consume this advisory.

## Persistent offline review journal

Use a separate SQLite database to retain computed advisories (including abstentions), deduplicate identical results and record a single manual review without replacing the original result. This is a local review record, not an authenticated workflow or machine command. Review identity is declared, not verified. Advisory fingerprints detect accidental payload mismatch, not hostile modification by someone controlling the database.

```sh
python -m src.advisory_review --journal review.sqlite analyze --archive archive.sqlite --capture-id <capture-id> --context-sha256 <context-digest> --trusted-pins trusted-pins
python -m src.advisory_review --journal review.sqlite list
python -m src.advisory_review --journal review.sqlite review --advisory-id <id> --reviewer engineer --note "Inspect measurement evidence"
```

No advice is injected into fleet incidents, threshold policies or equipment controls. The production-adjacent telemetry API is unchanged. Do not treat the local review status as permission to operate equipment.

For optional read-only dashboard inspection, set `AERIS_ADVISORY_JOURNAL_PATH` to the trusted local journal before launching Streamlit. The calibration decision lab then displays stored records and review notes. It cannot create a journal or change a review. Do not expose this local dashboard to unauthorized users.
