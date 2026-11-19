# Ponui, March 2025: the ferrites on the Mini's USB cable

Read 2026-11-19. **The two snap-on ferrites on the Mini's USB extension cut the in-flight noise by
about 10.5 dB, and the noise on the ground with the motors off by 17–20 dB.** Same receiver, same gain
setting, same island, same aircraft, one change. That makes it the cleanest before/after of the whole
noise record.

**Configuration (Michael, 2026-11-19).** Airspy Mini hanging outside the drone's RF shield on a USB
extension, plugged into a USB bulkhead on the fuselage that was not deliberately bonded to the
shield. 15 ft RG-316 to the antenna, no common-mode choke, no ferrites on the aircraft's own wiring,
Castle BEC. Mini gain 20 throughout. Day 2 (Mon 17 March) flew with no ferrites on the USB
extension. Tue 18 it rained; debugging in the cabin showed that ferrites on the USB cable helped a
lot. Every flight after the 17th had two snap-on ferrites on the extension, one with two passes and
one with three.

## Data

- **Day 2, Mon 17 March, no ferrites:** `FLIGHT_TESTING_DATA/2025-03-17-Ponui-Day2-Mon/`, four
  flights with IQ recordings (Pi sessions `2025-03-15_10-27-47`, `10-40-21`, `10-42-26`, `11-21-50`; the
  Pi's clock was two days behind). 161.0891 MHz. Flight notes in `FLIGHT NOTES.xlsx`.
- **Day 8, Sun 23 March, with ferrites:** flights P2 and P3 of the report, IQ recordings.
- **Every flight of the trip with detections:** TagTracker's pulse logs. Every reported pulse carries
  the detector's noise estimate (`noise_psd`), in the same units as the IQ recording, with the
  aircraft's position. `tools/pulse_log_noise.py` converts it: dBm/Hz = 10 log10(noise_psd) − 59.81
  (Mini bench calibration; `noise_psd` is a mean, so it sits 1.59 dB above the median-based reading of
  `tools/noise_floor.py`). Checked against the Day 8 IQ recordings: within 0.4 dB. Pulse logs for the
  whole trip are in the Day 8 folder under `HERELINK_LOGS/TagTracker Daily/Logs/`, in per-day archive
  folders; file names are in UTC, NZDT is 13 h later.

Files here: `day2_floors.json` (Day 2 per-second floors and stage medians, from `day2_stages.py`),
`pulse_noise.csv` (every pulse of the trip with height, SNR and floor), `cabin_capture_*.json`,
`ponui_trip.png` (from `fig_trip.py`).

## Results, dBm/Hz at the receiver input

| | No USB ferrites (Day 2, Mon 17) | With USB ferrites (Tue 18 to Sun 23) | Change |
|---|---|---|---|
| In flight | **−135.0** (four flights: −135.2, −135.1, −134.8, −134.8) | **−145.4** (median of 15 flights, pulse logs); Day 8 IQ −145.5, −145.1 | **about −10.5 dB** |
| On the ground, motors off | **−143 to −149** (before takeoff −144.6, −149.4, −143.2; after landing −145.2, −146.1) | **−161.5, −162.4** (Day 8 IQ, before takeoff); −168 to −169 after landing (pulse logs) | **about −17 to −20 dB** |
| Above the Mini's own noise (−167.6), in flight | +32.6 dB | +22.2 dB | |

Both columns are at gain 20, so the gain caveat on the conversion cancels in the change.

1. **Without the ferrites, the aircraft was loud even with the motors off.** On the ground before
   takeoff it read −143 to −149 dBm/Hz, 18–24 dB above the receiver's own noise and about as loud as the
   later flights were in the air. That noise is the Pi and avionics reaching the antenna through the
   USB cable, the Mini and the outside of the coax, the path described in `../../../emi-design.md`
   appendix A.3.
2. **The motors added another 9–14 dB on top**, to −135 in flight. With the ferrites, motors-off
   dropped to −162 or lower and flight to −145.4: the ferrites removed most of the electronics' share,
   and the motors' share then dominated.
3. **The step is at the right place.** All four Day 2 flights sit at −135, the Wellington test flights
   before them at −137 (pulse logs), and every flight from Tue 18 on between −144 and −148.
4. **The two Wellington flights** (Sat 15 March, logged at −41.286, 174.771) agree: no ferrites, about
   −137 in flight. Their motors-off ground readings were at the receiver's own level, unlike Day 2;
   the setup on the ground may have differed.
5. **Gain-20 offset.** After landing, motors off, the ferrite flights read −168 to −169.5, 1–2 dB below
   the receiver's own noise at gain 21. So all Ponui values in dBm/Hz probably read 1–2 dB low, as the
   report's caveat says. Differences between Ponui values are unaffected.

## Other captures in the Day 1 and Day 2 folders

- **Cabin captures, Day 1 folder** (`DRONE LOGS/Logs-RawCapture-2025-03-15_*`, 8 s each, 160.401 MHz,
  gain 20, motors off, antenna on the railing 3–5 m from the drone, tag in Michael's bag): −138.6 and
  −144.1 dBm/Hz, flat across ±1 MHz, with a comb of lines about 92 kHz apart, a switching power supply.
  Read with `tools/raw_capture_floor.py`, which emulates the decimate-and-channelize chain. These were
  taken before the ferrites, so the drone may be part of it; they are not a clean background reference.
- **Mac captures, Day 2 folder** (`DRONE LOGS/0800-Mac-Raw_Captures/`): the old and a new Mini, and a
  wire antenna, at 149 and 160.401 MHz. Old and new Mini agree within about 1 dB, so the receiver was not
  at fault. The gain setting used on the Mac is not recorded, so these are not converted to dBm/Hz.

## The sequence so far, in flight

| When | Configuration | In flight, dBm/Hz |
|---|---|---|
| Mar 2025, Ponui Day 2 | Mini on a USB extension outside the shield, no ferrites on it, no choke | −135.0 |
| Mar 2025, Ponui from Day 3 | the same with two snap-on ferrites on the USB extension | −145.4 |
| Nov 2025, Cumbria | Mini inside the shield, bonded SMA bulkhead, choke | about −158 (`../2025-11-24-cumbria-mini-choke/`) |
| Nov 2026 | HF+ outside the shield, bonded USB bulkhead, choke, aircraft ferrites F1–F9, PM12S-4A | −163.5 |

From the start of the Ponui trip to now, about 28 dB. Only the first step is a single change on one
site; see the configuration history in `../../README.md`.
