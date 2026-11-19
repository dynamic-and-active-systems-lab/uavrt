# Receiver noise reduction

The record of how the noise reaching the tracking drone's receiver was measured and reduced, from
the Ponui fieldwork in March 2025 to now. Started 2026-11-19.

**Where it stands (draft 0.1, 2026-11-19):** in steady flight the noise at the receiver input fell
from about −145 dBm/Hz at Ponui to −163.5 dBm/Hz on 2026-11-14, about 18 dB. It now sits 3.3 dB above
the receiver's own internal noise, against 22 dB at Ponui. Details, methods and caveats are in the
report.

## Contents

| Path | What it is |
|---|---|
| `report/noise_report.pdf` | The report. Source `noise_report.tex`; figures from `make_figures.py`. |
| `report/uavrt-noise-reduction.html` | The same report as an interactive page. Self-contained; open in a browser. |
| `tests/<date>-<name>/` | One folder per test: what was done, the results, and notes written at the time. |
| `data/` | Small derived data the report is built from: noise floors per second, spectra, calibration, VNA traces. |

Tests so far:

| Folder | Test |
|---|---|
| `tests/2026-11-14-flights-rail-x-ranch/` | Seven flights, five with radio data: choke and coax-extension configurations, no tag out. |
| `tests/2026-11-17-vna-cables/` | NanoVNA loss and match of the 15 ft RG-316, the choke, and the bench cable. Includes the S2P files. |
| `tests/2026-11-18-bench-mini-vs-hf/` | Signal-generator calibration of the Airspy Mini and HF+: noise figure, units, strong-signal behaviour. |
| `tests/2025-11-24-cumbria-mini-choke/` | Cumbria fieldwork, last two flights: Mini inside the shield with the choke. Not yet in the report. |
| `tests/2025-03-ponui-trip-pulse-logs/` | Every Ponui-trip flight with detections, from the detector's noise estimate in the pulse logs; the USB-cable ferrites; the cabin captures. Not yet in the report. |

The Ponui reference flights in the report (2025-03-22 UTC) are read directly from their recordings.

## Configuration history

From Michael, 2026-11-19. Each change below happened between field trips, so no single step has a
same-day A/B comparison yet.

| When | Receiver and where it sits | Antenna side | Aircraft | In flight, dBm/Hz |
|---|---|---|---|---|
| Mar 2025, first flights (Wellington test flights in the Day 1 folder) | Airspy Mini outside the shield, on a USB extension from a USB bulkhead not deliberately bonded to the shield (it may have touched it); no ferrites on the extension | 15 ft RG-316, no choke | Castle BEC; no ferrites | about −137 |
| Mar 2025, Ponui, by Day 8 | The same, with two snap-on ferrites on the USB extension (two passes and three passes) | The same | The same | −145.4 |
| Nov 2025, Cumbria | Mini inside the shield on the Pi; SMA bulkhead with the back shell bonded to the shield | Choke at the bulkhead (from the second day), 15 ft RG-316, PHW150C | Castle BEC; no ferrites | about −158 |
| Since Cumbria; measured Nov 2026 | Airspy HF+ outside the shield, through a bonded USB bulkhead | Choke, 15 ft RG-316, PHW150C | PM12S-4A in place of the Castle BEC; ferrites F1–F9 and the rest of `../emi-design.md` | −163.5 |

Not recorded: the antenna at Ponui, and exactly when the USB-extension ferrites went on.

## Raw data

Recordings stay in OneDrive `FLIGHT_TESTING_DATA/`, too large for git:
`2025-03-16-Ponui-Day1-Sun`, `2025-03-23-Ponui-Day8-Sun`, `2025-11-24-Cumbria-Day8-Mon`,
`2026-11-14-Rail-X_Ranch_Road`, `2026-11-18-Office_HF_v_Mini_Testing`.

## Rebuilding

From the hub root:

```bash
python3 tools/noise_report_data.py <folder containing the FLIGHT_TESTING_DATA test folders> .
cd hardware/noise-reduction/report
python3 make_figures.py ../data figures
latexmk -pdf noise_report.tex
python3 build_page.py
```

`tools/noise_floor.py` and `tools/bench_calibration.py` are the measurement routines. `tools/pulse_log_noise.py`
reads the in-flight noise of any past flight from TagTracker's pulse logs, no IQ recording needed;
`tools/raw_capture_floor.py` reads airspy_rx raw captures.

## Related

- `../emi-design.md`: the ferrite and shielding design, with the reasoning for each change.
- `../NAU_VHF_DRONE.md`: the aircraft, including the ferrite table, which records measured effects as they arrive.
