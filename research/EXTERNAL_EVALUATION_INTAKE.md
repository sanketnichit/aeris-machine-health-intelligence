# External evaluation intake — proposed physical bearing population

## Candidate: Paderborn University Bearing DataCenter

Source: https://mb.uni-paderborn.de/kat/forschung/bearing-datacenter/data-sets-and-download
Instrumentation: https://mb.uni-paderborn.de/kat/forschung/bearing-datacenter/test-rig-and-measurement-equipment

The publisher describes 32 physical 6203 bearing states (six healthy, 12 artificially damaged, 14 with damage generated through accelerated lifetime tests), four operating settings, and 20 four-second recordings per setting. Repeated recordings are not independent bearings. This is a diagnostic experiment candidate, not a run-to-failure RUL benchmark or prospective deployment trial. The source pages were reviewed; no waveforms, individual fact sheets or numerical test outcomes have been inspected by this intake.

Before any scoring:
1. Obtain the official damage fact sheets, measurement logs, data license and actual bearing geometry (including contact angle and rolling-element count). Do not assume the geometry of MFPT or CWRU applies.
2. Freeze a specimen-level population and label inclusion/exclusion rules before inspecting waveforms or scoring. Separate artificial versus accelerated damage, isolated ring faults versus mixed/ambiguous faults, and healthy controls. Report both specimen and repeated-recording denominators.
3. Acquire named archives from the publisher, verify structure and fingerprints, document actual vibration channel, sample clock, speed metadata and units. Never silently substitute current channels, infer calibration or use label-dependent preprocessing.
4. Freeze the previously established spectral rule, thresholds and resampling recipe. Any change necessary to accommodate a new acquisition chain is a new development procedure and must be declared before evaluation.
5. Report fault suggestions, incorrect suggestions, abstentions, healthy controls receiving suggestions, and specimen/condition breakdowns. Do not tune on the new evaluation scores. A nominal speed value is not a calibrated reference; absent actual calibration information, the operational provenance gate must remain withheld.

## Separate prognostic candidate

N-CMAPSS uses simulated degradation under real flight-condition profiles and HDF5 data (see https://www.mdpi.com/2306-5729/6/1/5). Its feature contract and dataset identity differ from legacy C-MAPSS. Direct reuse of 26-column model features is unjustified; an independently frozen mapping and held-out population are required. No N-CMAPSS data has been acquired or evaluated.

Both candidates remain intake-stage only. Physical machine calibration and prospective field validation are still outstanding.
