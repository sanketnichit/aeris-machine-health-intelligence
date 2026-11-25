# AERIS v0.2.0 — Expanded Research Release

Research software, not an operationally certified maintenance system.

Accepted source revision: `5e6aba8f01f0a35347698c4c45661b09db7a92ca`. [Final acceptance](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45621480240) and [versioned package validation](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45621480466) both passed. 434 tests passed in checkout and fresh extraction; 30 registered evidence reports; integrated Docker, browser, authenticated review, concurrency and database recovery passed.

## Research additions

- All four official legacy NASA C-MAPSS subsets, including negative direct cross-regime transfer results and training-only regime applicability research.
- MFPT physical bearing transfer and measurement uncertainty, abstention and common-mode investigations.
- Local capture advisory, monitoring and review journal; expanded evidence-linked dashboards.
- Paderborn pinned specimen acquisition and paired conditional timing study: 17 specimens, 68 recordings; per timing hypothesis 6/44 correct fault suggestions, 38/44 fault abstentions and 3/24 healthy false suggestions. All 68 decisions agreed; reliable transfer was not established.

## Limits and attribution

No verified physical clock calibration, visual geometry verification, independent prospective field validation, operational authorization or production safety certification. Negative and inconclusive results are retained.

MIT applies to AERIS code. Third-party datasets retain their terms: MFPT redistribution by MathWorks is CC BY-NC-SA 4.0; Paderborn KAt-DataCenter (Christian Lessmeier et al., Chair of Design and Drive Technology, Paderborn University) is CC BY-NC 4.0. The package contains derived research summaries and structural metadata, not raw dataset archives or specimen PDFs. To the extent third-party rights apply to those derived materials, the original attribution, noncommercial and applicable share-alike conditions remain in effect. See [DATA_LICENSE.md](https://github.com/sanketnichit/aeris-machine-health-intelligence/blob/5e6aba8f01f0a35347698c4c45661b09db7a92ca/DATA_LICENSE.md), [MFPT source](https://github.com/mathworks/RollingElementBearingFaultDiagnosis-Data) and [Paderborn source](https://mb.uni-paderborn.de/en/kat/research/bearing-datacenter). No commercial dataset rights are granted.

The original v0.1.0 archive DOI 10.5281/zenodo.24522637 is preserved and does not identify this version. A separate Zenodo version remains pending.
