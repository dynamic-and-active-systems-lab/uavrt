# Cumbria fieldwork, Day 8, 2025-11-24: Airspy Mini with the choke

Pine marten tracking near Ambleside. Read 2026-11-19 from
`FLIGHT_TESTING_DATA/2025-11-24-Cumbria-Day8-Mon/`. The Pi's clock was wrong by four days, so its
log folders are named 2025-11-20.

**Configuration (from Michael, 2026-11-19):** Airspy Mini inside the drone's RF shield, plugged into
the Pi, its SMA connector brought out through the shield with the back shell bonded to it. The
common-mode choke at that connector, then the 15 ft RG-316 extension and the PHW150C antenna. The
choke was fitted after the first day of the trip, so it is on every flight from 2025-11-18 to
2025-11-24. Mini gain 21, the same setting as the 2026-11-18 bench calibration. Not yet fitted at
Cumbria: the PM12S-4A (5 V came from the Castle BEC), the USB bulkhead (the Mini was inside, so no
USB cable left the shield), and the aircraft ferrites F1–F9 (`../../../emi-design.md`).

**Flights analysed:** the last two of the day, Pi sessions `02-40-07` and `03-24-27` (Herelink pulse
logs `Pulse-2025-11-24-14-29-46-578.csv` and `-15-42-40-343.csv`). Two channels each: 173.288 MHz
(tag 10, almost silent) and 173.314 MHz (tag 12, on the animal that was found). Tag pulses are removed
by the noise-floor estimate; the two channels agree within a few tenths of a dB, which confirms it.
Height comes from the pulses' logged position.

## Results, dBm/Hz at the receiver input

Converted with the Mini's bench calibration (`../2026-11-18-bench-mini-vs-hf/`). The calibration was at
160 MHz and these flights were at 173 MHz; the Mini's gain may differ slightly between the two.

| Stage | Flight 1 (14:29) | Flight 2 (15:42, tag found) |
|---|---|---|
| On the ground before takeoff | −166.2 | −163.1 / −165.3 |
| Steady flight | −158.8 at 127 m | −157.9 at 95 m |
| Final descent and landing, motors on | −156.8 | **−153.9** |
| First 10–15 s after the motors stopped (disarm) | −157.0 | −153.8 |
| After that | −166.9 | −167.0 |

The Mini's own noise is −167.6 dBm/Hz.

1. **In steady flight the noise sat about 9.5 dB above the Mini's own noise.** That is between Ponui
   (no choke, +22 dB) and the 2026-11-14 HF+ flights (+3.3 dB).
2. **The noise came on with the motors but did not go off with them.** In flight 2 the noise rose as
   soon as the motors spun up, while the drone was still on the ground. It was highest, −153.9, through
   the final descent and landing. *Corrected 2026-11-20 from the PX4 logs:* the motors stopped at
   disarm, right after touchdown, but the noise stayed at about −154 for another ~17 s (flight 1: ~15 s)
   and then fell to the receiver's own level within a second or two. Earlier versions of this note read
   that period as "landed, motors still running". Whatever made the noise ran on after disarm and then
   stopped. Falling to exactly the receiver's own noise is what disconnecting or picking up the antenna
   would give; what happened at that moment is not recorded.
3. **Height made little difference.** Medians stayed within about 3 dB from a few metres up to 127 m.
   Within a steady hover the noise wandered between about −161 and −154, which looks like throttle,
   not height.

## PX4 logs (added 2026-11-20)

`FLIGHT_TESTING_DATA/2026-11-20-PX4_LOG_ARCHIVE/`: `log_189_2025-11-24-07-38-44.ulg` is flight 1
(armed 14:29:59 UTC) and `log_190_2025-11-24-08-52-50.ulg` flight 2 (15:42:56 UTC); the file names are
in Arizona time. Per-second extract: `px4_per_second.csv` (height, mean motor command, TFMini range,
battery current). The Pi clock was wrong, so the recordings were aligned to the logs by matching the
PX4 height to the height logged with the detected pulses: offsets −14 s and −18 s, median height
difference 0.03–0.04 m. Steady heights 124 m and 95 m above the takeoff point. The logged battery
current tops out near 10 A, far below the 2026 logs' 20 A in hover, so the current sensor was probably
not calibrated then.

## What this adds

- **A middle point between Ponui and now:** Mini + choke + shield in November 2025, about −158 dBm/Hz in
  flight; HF+ + choke + ferrites in November 2026, −163.5. Between those two the receiver and where it
  sits (inside the shield, then outside through a bonded USB bulkhead), the regulator, the aircraft
  ferrites, the frequency and the site all changed, so the 5.5 dB cannot yet be split between them. The planned same-day Mini/HF+ flights will separate the receiver's share.
- **A simpler answer to the antenna-height question:** idle on the ground with the motors running for
  about 30 s before takeoff and after landing. If the noise rises with the antenna still on the ground,
  it is the drone.

Figure: `timelines.png`. Per-second data: `cumbria_floors.json`.
