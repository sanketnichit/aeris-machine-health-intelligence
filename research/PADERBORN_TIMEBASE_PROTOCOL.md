# Paderborn timing metadata protocol

Read only the same 12 previously fingerprinted pilot recordings and reproduce their exact waveform counts. Inspect the actual X structures and the named vibration and speed Y structures. Record bounded metadata and numeric time-vector summaries: count, first/last, interval extrema, median step, monotonicity and relative step variation. Report exact raster-plus-count association candidates separately from count-only candidates. No association is asserted from array length or order alone. Speed values are summarized in native stored units without inferring RPM or synchronization from the filename. Do not compute vibration amplitude distributions or diagnostic scores.

The original paper (Lessmeier et al., PHM Europe 2016, section 4.1, p. 7) specifies nominal 64 kHz housing acceleration and lower-rate auxiliary speed acquisition. Table 1 (p. 3) gives example internal dimensions for **KB24** only: eight rolling elements, pitch diameter 28.55 mm, rolling-element diameter 6.75 mm and zero nominal pressure angle. Do not apply these dimensions automatically to other specimens: manufacturer-specific geometry is explicitly distinguished in section 2. Table 5 (p. 6) identifies KA04 as outer-ring pitting and KI04 as inner-ring pitting with multiple damage; these are not assumed identical fault severities. Obtain specimen fact sheets before freezing geometry and class inclusion.

Source: https://mb.uni-paderborn.de/fileadmin-mb/kat/PDF/Veroeffentlichungen/20160703_PHME16_CM_bearing.pdf
Operating settings: https://mb.uni-paderborn.de/en/kat/research/bearing-datacenter/operating-conditions

No waveform redistribution; no physically calibrated timebase, speed bound, diagnostic performance or deployment claim. All findings are structural.
