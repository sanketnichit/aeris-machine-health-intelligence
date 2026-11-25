# CWRU measured spectral audit — frozen v1

Question: does envelope demodulation expose the documented seeded race defect order more strongly than raw acceleration spectra on a new laboratory platform? This is a descriptive comparison, not classifier training or an independent safety validation.

Sources:
- https://engineering.case.edu/bearingdatacenter/12k-drive-end-bearing-fault-data
- https://engineering.case.edu/bearingdatacenter/bearing-information
- https://engineering.case.edu/bearingdatacenter/apparatus-and-procedures

Population: all four loads (0–3 HP) for 0.007-inch inner race (105–108) and centered outer race (130–133) drive-end fault recordings, source files named by the CWRU table. Only the DE acceleration channel; no invented horizontal/vertical orientation. Sample rate 12000 Hz. Approximate nominal speeds 1797,1772,1750,1730 rpm from the published table, not estimated from outcomes. Expected orders 5.4152 inner and 3.5848 outer. Source acceleration units are not assumed or converted; scale-invariant spectral fractions only.

Before inspection: first 12 complete nonoverlapping 8192-sample windows per file (98304 samples); reject incomplete or nonfinite data. Demeaned, amplitude-normalized signal; compare periodic Hann one-sided power spectrum against envelope spectrum following a fixed fourth-order Butterworth 2000–5000 Hz bandpass (zero-phase offline filtering within each window) and Hilbert magnitude. Normalize both spectra by total non-DC power. Use AERIS spectral_summary with include_bins=True; input is dimensionless, so ignore its dimensional amplitude labels. Report energy fraction in the first three harmonics of each order, within ±2 FFT bins of nominal frequencies; union of bins, no double counting. Report both expected and alternative order fractions. Per-record medians across 12 windows. Primary descriptive outcome: count of eight recordings with higher median expected-order fraction for envelope vs raw. Secondary: count of records with median expected-order fraction higher than alternative under each representation. No thresholds, learned weights, tuning, confidence intervals or independent-window significance claims. Retain every result, including failures.

Pin file IDs, direct official URLs, SHA-256 and implementation revision in execution output. No raw recordings redistributed. Multiple windows and loads from the same seeded bearing configuration are correlated, not independent assets. Source study deliberately creates defects; results cannot establish natural fault detection, unseen bearing classification, RUL, operational calibration or generalization. Future selection using these results requires a new evaluation population.
