# Hardware

What the aircraft and ground equipment are, how they are wired, and what was learned getting
them to work. Software lives in the component repositories and in `docs/`. This folder is for
the physical side: parts, power, wiring, shielding, ferrites, and problems whose cause turned out
to be hardware or setup rather than code.

Started 2026-11-03. Before this, hardware knowledge lived only in individual Claude sessions,
in Michael's notes, and in Don Gagne's page for his own aircraft.

## What is here

| File | What it is |
|---|---|
| `NAU_VHF_DRONE.md` | Michael's tracking drone: airframe, flight controller, power, shielding, ferrites, companion computer, receiver, antenna, ground station. Rename it if the aircraft has a name. |
| `emi-design.md` | The ferrite and shielding design for Michael's drone, 2026-11-09: every decision and the reasoning and source behind it, the options rejected, the likely noise sources ranked, the A/B test plan, and the theory. Nothing in it is measured yet. |
| `field-notes.md` | Diagnosis guides for problems that look the same but have different causes. Starts with the red controller bar on TagTracker. |
| `pi5-troubleshooting.md` | Michael's notes on the Raspberry Pi 5 from 2026-10-30 to 11-02: the auto-start change, the failing microSD card, the wrong serial port on a fresh install, and the fresh-install checklist. |
| `noise-reduction/` | The record of how the receiver noise was measured and reduced: one folder per test under `tests/`, small derived data under `data/`, and the report (PDF and interactive HTML) under `report/`. Raw recordings stay in OneDrive `FLIGHT_TESTING_DATA`. Scripts are `tools/noise_floor.py`, `tools/bench_calibration.py`, `tools/pulse_log_noise.py` and `tools/raw_capture_floor.py` in the hub. |
| `photos/` | Small photos of wiring and ferrite placement. Large photos stay in OneDrive; link to them. |

**Don's aircraft is documented in his repository, not here:**
`MavlinkTagController2/docs/hardware/PDC_VHF_DRONE.md`, the drone he built for the Painted Dog
Conservation team. Link to it; do not copy it. `NAU_VHF_DRONE.md` uses the same sections so the
two aircraft can be compared side by side. His page is also the model for how to record noise
work: every change has a date and a measured result in dB.

## How to write in this folder

**Date every finding, or say which software versions it applies to.** Hardware fixes go stale
when software changes underneath them. The table at the top of `pi5-troubleshooting.md` is the
pattern.

**For anything that changes radio noise, record the measurement, not just the change.** A ferrite,
a shield or a rerouted cable gets: where it is, the exact part, the noise floor or signal-to-noise
ratio before and after, how that was measured, and the date. Measure the same way each time, or
say how the method differed. Noise fixes get undone or doubted later, and the numbers are what
settle it. "Made no difference" is a result worth writing down.

**A design decision with no measurement yet is still worth recording**, as long as it says so.
Write the reasoning and the source of the best practice it follows, mark it *not yet measured*,
and describe the before/after test that would confirm it. That way the test can be run later
without reconstructing why the part is there.

**Mark what is not verified.** An estimate, a recollection or a manufacturer's figure is fine to
record, but say which it is. Do not let a guess read like a measurement.

**Follow `docs/WRITING_RULES.md`.** Plain English, shorthand defined where it first appears, and
never an identifier on its own.
