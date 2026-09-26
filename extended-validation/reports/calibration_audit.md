# AERIS Calibration Audit

This audit checks how the calibrated risk score behaves across selected subgroups of the primary held-out test set. The global calibration model and 0.50 threshold are unchanged.

A calibration gap is **mean predicted risk minus observed failure rate**. Positive values indicate average overprediction in that subgroup; negative values indicate average underprediction.

## Product-type calibration

| Group | Rows | Failures | Observed rate | Mean predicted | Calibration gap | Brier |
|---|---:|---:|---:|---:|---:|---:|
| Type H | 214 | 5 | 0.0234 | 0.0269 | +0.0036 | 0.0045 |
| Type L | 1170 | 38 | 0.0325 | 0.0344 | +0.0020 | 0.0080 |
| Type M | 616 | 25 | 0.0406 | 0.0385 | -0.0021 | 0.0076 |

## High/low operating-regime checks

The regime boundaries below are fixed from the **training partition quartiles** and then applied to the held-out test set. This avoids deriving the operating bands from the test labels.

| Regime | Rows | Failures | Observed rate | Mean predicted | Calibration gap | Brier |
|---|---:|---:|---:|---:|---:|---:|
| Torque — lower quartile | 501 | 10 | 0.0200 | 0.0166 | -0.0034 | 0.0112 |
| Torque — upper quartile | 473 | 50 | 0.1057 | 0.1054 | -0.0003 | 0.0121 |
| Rotational speed — lower quartile | 481 | 55 | 0.1143 | 0.1107 | -0.0036 | 0.0126 |
| Rotational speed — upper quartile | 483 | 10 | 0.0207 | 0.0170 | -0.0037 | 0.0116 |
| Tool wear — lower quartile | 494 | 6 | 0.0121 | 0.0148 | +0.0027 | 0.0002 |
| Tool wear — upper quartile | 485 | 35 | 0.0722 | 0.0736 | +0.0015 | 0.0270 |
| Air temperature — lower quartile | 490 | 15 | 0.0306 | 0.0284 | -0.0022 | 0.0070 |
| Air temperature — upper quartile | 493 | 34 | 0.0690 | 0.0741 | +0.0051 | 0.0061 |

## Risk-bin calibration

The primary test predictions are partitioned into five equal-count risk bins. This checks whether higher model scores correspond to higher observed failure frequency without treating a single threshold as universally correct.

| Risk bin | Rows | Observed rate | Mean predicted | Gap |
|---|---:|---:|---:|---:|
| 0.000–0.001 | 400 | 0.0000 | 0.0010 | +0.0010 |
| 0.001–0.002 | 400 | 0.0025 | 0.0015 | -0.0010 |
| 0.002–0.003 | 400 | 0.0050 | 0.0022 | -0.0028 |
| 0.003–0.006 | 400 | 0.0000 | 0.0037 | +0.0037 |
| 0.006–0.978 | 400 | 0.1625 | 0.1660 | +0.0035 |

## Interpretation

Calibration is not expected to be identical in every subgroup, especially when the positive class is rare. The useful check is whether the score retains reasonable ordering and whether large subgroup calibration gaps are visible. Any production use would require recalibration and prospective validation on the actual target population.
