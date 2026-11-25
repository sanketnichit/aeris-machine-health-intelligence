# Paderborn stored timebase findings

[Protocol](PADERBORN_TIMEBASE_PROTOCOL.md) | [Execution](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45617208442) | [Evidence](evidence/paderborn_timebase_summary.json)

The exact 12 pilot recording hashes and sample counts reproduced, and all 17 targeted tests passed. Each MAT record has three X structures (Mech_4kHz, HostService, Temp_1Hz). For speed and vibration, a unique same-raster same-count candidate is present, and the stored XIndex agrees with a one-based interpretation in all 12 recordings. This is internally consistent structural association, not verification of the exporter schema or physical synchronization. The stored Unit fields are empty.

| Recording | Vibration samples | Stored span | Median stored step | Maximum relative step deviation | Native speed median |
|---|---:|---:|---:|---:|---:|
| N15_M07_F10_K001_1.mat | 256001 | 3.99999872 | 1.582578e-5 | 8.11% | 1499.610 |
| N09_M07_F10_K001_1.mat | 256823 | 4.00000342 | 1.539805e-5 | 72.22% | 899.724 |
| N15_M01_F10_K001_1.mat | 256070 | 4.00000214 | 1.582578e-5 | 345.95% | 1499.675 |
| N15_M07_F04_K001_1.mat | 258669 | 3.99999230 | 1.582578e-5 | 75.68% | 1499.532 |
| N15_M07_F10_KA04_1.mat | 256004 | 3.99999530 | 1.582590e-5 | 86.49% | 1499.774 |
| N09_M07_F10_KA04_1.mat | 256001 | 4.00000000 | 1.582590e-5 | 5.41% | 899.439 |
| N15_M01_F10_KA04_1.mat | 256332 | 3.99998845 | 1.582590e-5 | 94.59% | 1499.672 |
| N15_M07_F04_KA04_1.mat | 256475 | 4.00000000 | 1.582590e-5 | 72.97% | 1499.692 |
| N15_M07_F10_KI04_1.mat | 256001 | 3.99999957 | 1.582584e-5 | 5.41% | 1499.731 |
| N09_M07_F10_KI04_1.mat | 256087 | 4.00000128 | 1.582584e-5 | 113.51% | 899.817 |
| N15_M01_F10_KI04_1.mat | 256732 | 3.99999316 | 1.539831e-5 | 97.22% | 1499.992 |
| N15_M07_F04_KI04_1.mat | 256004 | 3.99999401 | 1.582584e-5 | 72.97% | 1499.723 |

All matched vibration time vectors are strictly increasing but nonuniform; the maximum relative step deviation ranges from 5.41% to 345.95%. Stored spans are approximately four time units despite varying counts. Native speed values are compatible with nominal 900/1500 rpm, but no per-file unit or calibration is established. The original paper reports nominal 64 kHz digitization and lower-rate auxiliary acquisition; the export timestamp semantics are unresolved. Do not assert these are the actual physical ADC sample instants, or repair them using interpolation without a documented assumption. No spectral score was computed.

The primary cohort inventory is separately frozen, including 17 specimens. Individual geometry and acquisition-time semantics must be established before applying the frozen spectral decision rule. A nominal FFT can be an explicitly labeled research sensitivity comparison, not a calibrated measurement.
