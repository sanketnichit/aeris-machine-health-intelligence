# CWRU measured spectral findings — frozen v1

[Protocol](CWRU_SPECTRAL_PROTOCOL.md) · [Successful execution](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45560311529) · [Registered evidence](evidence/cwru_spectral_summary.json)

Eight official 12 kHz drive-end recordings (0.007-inch seeded inner and centered outer race defects, four loads each), first 12 complete windows of 8192 samples each: 96 windows and 786432 analyzed samples. The published protocol was executed without changing the chosen bandpass, harmonic tolerance, nominal speeds or population. Source file fingerprints and implementation revision are in the registered summary; full window-level values and environment are in the execution artifact.

## Results

Median fraction of non-DC power in the first three harmonics of the documented defect order, expressed as percent of the corresponding representation's total non-DC power:

| File | Defect | Load (HP) | Raw FFT (%) | Envelope (%) |
|---|---|---:|---:|---:|
| 105 | Inner | 0.2062 | 41.1638 |
| 106 | Inner | 0.1524 | 44.8028 |
| 107 | Inner | 0.1582 | 41.1603 |
| 108 | Inner | 0.0468 | 39.9244 |
| 130 | Outer | 0.00305 | 66.1819 |
| 131 | Outer | 0.00266 | 63.1213 |
| 132 | Outer | 0.00265 | 66.0393 |
| 133 | Outer | 0.00238 | 66.5347 |

Primary descriptive result: envelope expected-order fraction exceeds raw in 8/8 recordings. Secondary result: expected order exceeds the alternative race order in 4/8 raw recordings and 8/8 envelope recordings. All four raw outer-race recordings have higher alternative-order than expected-order median fraction.

## Interpretation

A fixed high-frequency bandpass and Hilbert envelope concentrate energy around the known seeded defect orders in these recordings. The denominator is representation-specific, so these fractions do not compare absolute vibration energy. The experiment is not a classifier: no normal controls, ball defects, other severities or held-out physical bearing population were evaluated. The repeated windows and loads are correlated, not 96 independent assets. The findings do not imply 100% classification accuracy, a new demodulation method, field fault detection, calibrated acceleration, remaining-life prediction or industrial safety. This is new post-v0.1.0 evidence, not part of the DOI-archived release.

Future confirmatory work should freeze a wider population and compare against normal recordings and competing defects without tuning on the observed eight recordings.
