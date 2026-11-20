# Background noise flights, 2026-11-14, Rail-X Ranch Road

**Superseded in part, 2026-11-18:** the signal-generator calibration in `../2026-11-18-bench-mini-vs-hf/` puts these
floors in dBm/Hz. The improvement over Ponui is about 18 dB, not 13, and the remaining in-flight
noise is only 3.3 dB above the HF+'s own floor. Read that note for the corrected comparison.

Seven flights, no tag out, receiver tuned to 160.172 MHz, the frequency of the last Ponui flight. PHW150C whip trimmed to 160.45 MHz (Michael's notes).
Five recorded radio data. Data and Michael's notes:
`OneDrive-NorthernArizonaUniversity/FLIGHT_TESTING_DATA/2026-11-14-Rail-X_Ranch_Road/`.
Analysed 2026-11-14 with `tools/noise_floor.py`. Figures: `timelines.png`, `spectra.png`.

**Method.** The floor is the median power in the inner 80 % of the 3.84 kHz band, per second,
from the detector's raw IQ recording, with brief pulses removed by a median over each second. Units
are the receiver's own, so values compare within one receiver only. Across receivers, compare the
*rise*: the in-flight floor minus the same recording's floor in its first seconds, on the ground
with the receiver running and the motors not yet spinning (called the pre-arm floor below).

**Phases.** Originally read from the noise and the notes; checked 2026-11-20 against the PX4 logs
(section below), which confirm the ground and steady windows used.

| Flight | Session (Pi, UTC) | Configuration | Height | Pre-arm floor | In-flight floor | Rise |
|---|---|---|---|---|---|---|
| 2 | 17-31-39 | Choke + 15 ft coax | ~170 ft, 30 s hover | −144.9 | −141.1 | +3.8 dB |
| 3 | 17-40-15 | Choke + 15 ft coax | ~170 ft, no hover | −144.3 | −141.0 | +3.3 dB |
| 5 | 17-46-24 | No choke + 15 ft coax | 50 ft | −143.5 | −139.3 | +4.2 dB |
| 6 | 17-50-16 | No choke, no coax extension | 50 ft | −132.8 | −134.2 | −1.4 dB |
| 7 | 17-53-16 | Choke, no coax extension | 50 ft | −142.9 | −139.1 | +3.8 dB |
| Ponui 2 | 2025-03-22 04-34-33 | Old setup, Airspy Mini | — | −103.3 | −87.3 | +16.0 dB |
| Ponui 3 | 2025-03-22 05-02-04 | Old setup, Airspy Mini | — | −104.2 | −86.9 | +17.4 dB |

Ponui and today's absolute values are in different receivers' units and must not be compared.

## Findings

1. **Flight now adds about 3.5 dB to the background; at Ponui it added 16–17 dB.** About 13 dB
   less noise from flying, over and above whatever the powered-but-grounded aircraft makes. Not
   separable from the change of site, receiver and every ferrite at once. **The 13 dB is not a
   calibrated figure:** neither receiver reports absolute power, and a rise depends on how quiet
   the receiver itself is. If the motors-off floor is set by each receiver's own noise, a receiver
   that is X dB noisier hides X dB of drone noise. Receivers of this class usually differ by a few
   dB, so the improvement is very likely real and large, but its exact size is unknown until the
   two are calibrated against each other or the Mini is flown on the current aircraft. (An earlier
   version of this note called the HF+ the more sensitive receiver. Nothing measured here shows
   that: the 10,000-fold difference in reported noise power in Don's April comparison is a
   difference in digital scaling, not in sensitivity.)
2. **Best configuration: choke + 15 ft coax** (flights 2 and 3), lowest in every phase.
3. **The coax choke (F10) matters most when the antenna is close.** Without the extension, adding
   it (flight 6 → 7) lowered the pre-arm floor about 10 dB and the in-flight floor about 5 dB. With
   the 15 ft coax (flight 5 → 2/3) it was worth about 1–2 dB, though those flights also differ in
   height.
4. **The 15 ft coax matters most without the choke.** Without the choke, the extension (flight
   6 → 5) bought about 10.7 dB on the ground and 5 dB in flight. With the choke it bought about
   1.5–2 dB.
5. **Flight 6's noise is there before the motors turn.** With no choke and the antenna close, the
   floor was 10–12 dB up on the ground and did not rise in flight: the avionics, not the propulsion,
   set it.
6. **What remains:** a broadband rise of about 3.5 dB in flight, short bursts 3–8 dB above that at
   what looks like takeoff and landing, and several narrow tones up to 6–10 dB above the floor
   (strongest in flights 5 and 7, and on the ground in flight 6), at roughly −1450, −1200, −1050,
   −730, −380, +250, +960 and +1270 Hz from 160.172 MHz. Ponui's in-flight rise was flat across
   the band with no tones.
7. **Three false detections in flight 3,** at 17:41:49–52 UTC, all at 160.17392 MHz, the very edge
   of the detector's band (+1920 Hz), during a 5 dB rise in the floor about 94 s into the session.

## PX4 logs (added 2026-11-20)

`FLIGHT_TESTING_DATA/2026-11-20-PX4_LOG_ARCHIVE/`. File names are the disarm time in Arizona time
(UTC − 7); PX4 time is UTC from GPS.

| Flight | Log | Armed (UTC) | Steady height | Max height | Radio |
|---|---|---|---|---|---|
| 1 | `log_198` | 17:16:48 | — | 45 m | none |
| 2 | `log_199` | 17:31:48 | 53 m (175 ft) | 55 m | session 17-31-39 |
| 3 | `log_200` | 17:40:19 | 45 m (150 ft) | 54 m | 17-40-15 |
| 4 | `log_201` | 17:44:05 | — | 45 m | none (detection not started) |
| 5 | `log_202` | 17:46:30 | 28 m (90 ft) | 34 m | 17-46-24 |
| 6 | `log_204` | 17:50:22 | 19 m (60 ft) | 19 m | 17-50-16 |
| 7 | `log_206` | 17:53:25 | 18 m (60 ft) | 18 m | 17-53-16 |

`log_197`, `203` and `205` are brief arm/disarm cycles. Flights 1–4 lost RC and telemetry together
for 1–7 s beyond about 40 m and switched to Return; the cause was the SIYI air unit's missing 5.8 GHz
antennas (`../../../siyi-link-debug-2026-11-20.md`). That explains the "lost signals" in the notes and
the unplanned maneuvering in flights 2 and 3. The radio recordings are unaffected. Heights are above the takeoff point. The
notes' 50 ft for flights 4–7 was the planned height. Per-second extract: `px4_per_second.csv`
(height, mean motor command, TFMini range, battery current, landed flag); extracted with `pyulog`.

**Alignment.** The recording starts at the Pi session time, which is UTC; on every flight the noise
rose within 1–2 s of the motors spinning up, so no offset is needed.

**Findings.**

1. **Choke + 15 ft coax: motors at hover power with the antenna on the ground leave the noise at the
   receiver's own level.** Flight 3 ended with about 15 s hovering 0.9 m up (TFMini), motors at hover
   thrust, antenna on the ground: −166.5 to −166.9 dBm/Hz. Flight 2's last seconds below 1.5 m: −166.4.
   At height both read −163.5. The in-flight rise appears only with the antenna in the air.
2. **The noise peaks with the drone 5–12 m up**, on the way up and down, with the antenna dangling near
   the ground: up to −158 in flights 2 and 3, about 5 dB over the steady level.
3. **Without the choke or the extension the drone is noisier near the ground than at height:** final
   descent with motors on against steady flight, flight 5 −156.5 / −161.8, flight 6 −153.6 / −156.6,
   flight 7 −158.7 / −161.5.
4. **No link to motor current:** correlation of noise with battery current in steady flight between
   −0.26 and +0.23 on every flight.
5. **The TFMini reads correctly up to about 10–15 m**, then drops out or reads about 1 m, so it is not
   a height source above that.

## Open

- How far below the aircraft the antenna hung in flights 6 and 7.
- The receiver's own floor on a 50 Ω load, to tell how much of the remaining 3.5 dB is the drone
  and how much is simply the antenna seeing more of its surroundings from height.
