# NanoVNA cable/component loss measurements at 160 MHz

Context for anyone (human or Claude session) picking up this folder.

## Goal
Measure the path loss (insertion loss, |S21|) at **160 MHz** of cable assemblies and other components
(RG316 extension, common mode choke, and combinations), using a NanoVNA. Loss in dB is the S21
magnitude without the minus sign (S21 = -0.5 dB means 0.5 dB of loss).

## Equipment and software
- VNA: Zeenko ZN401, NanoVNA-H4, firmware 1.2.43 (per `measurement_notes.csv`).
- Ports: the VNA labels them S11 (= CH0, Port 1, stimulus/reflection) and S21 (= CH1, Port 2, receiver).
- PC capture software: NanoVNA-Saver 0.5.5, installed on a Mac from the GitHub release archive
  (it is NOT on PyPI under that name) into a Python 3.12 virtual environment at `~/nanovna-venv`.
  Launch with `source ~/nanovna-venv/bin/activate` then `NanoVNASaver`. The install lives in that
  venv, not in this folder; this folder only holds the saved measurement data.

## Method
1. Set the sweep to 100-220 MHz, 401 points, then calibrate on the VNA itself
   (OPEN, SHORT, LOAD on S11 port; LOAD on S21 port for isolation; THRU joining the ports) using the
   kit standards and the kit test cables, so the calibration plane is at the far ends of the test cables.
2. Check the calibration: with the thru connected, S21 reads about 0 dB across the band (confirmed by the user).
3. Connect the component between the S11 and S21 ports, sweep, and in NanoVNA-Saver use
   Files -> Export file -> "Save 2-port file (S2P)" to save the calibrated data.
4. Record the setup details for each file in `measurement_notes.csv`.

## Files in this folder
- `measurement_notes.csv`: one row per S2P file with component description, connectors, adapters,
  calibration details, sweep settings, and instrument info. This is the user's own record; treat it as the
  source of truth for setup details and do not rewrite it.
- `thru_calibration_result_2026-11-17.s2p`: the thru measured right after calibration, using the 30.4 cm thru
  cable that came with the VNA. It is a calibration verification, not a device measurement (S21 ~0 dB
  across the band, confirmed by the user). Every component row in the CSV references it in
  `cal_thru_s2p_filename`.
- `rg316_15foot_extension_2026-11-17.s2p`: 15 ft RG316 extension alone.
- `common_mode_choke_2026-11-17.s2p`: common mode choke alone.
- `common_mode_choke_and_rg316_15foot_extension_2026-11-17.s2p`: the RG316 extension (on the S11 side) in series
  with the choke (on the S21 side).

## Notes for analysis
- The S2P files are Touchstone text files; parse with e.g. `scikit-rf` or a short script. The files are exported
  after calibration, so they already contain corrected data; no separate cal file is needed.
- The NanoVNA measures only S11 and S21. S12 and S22 columns are not real measurements; ignore them.
- Loss at 160 MHz = -S21 (dB) interpolated at 160 MHz. S11 gives return loss/match.
- Adapters left in the measurement path (the CSV lists a male-male SMA adapter for some rows) were not part of
  the calibration, so their small loss is included in those readings.
- Sanity checks worth doing: S21 of the thru file near 0 dB; the series combination's loss should be roughly
  the sum of the two individual losses, with differences from mismatch and adapters.
- The VNA treats the THRU step as an ideal, lossless connection, so the 30.4 cm thru cable's own loss and delay
  were absorbed into the calibration. Component S21 values are therefore the component's own loss, measured as a
  replacement for that thru cable. The 30.4 cm is not a component length.
