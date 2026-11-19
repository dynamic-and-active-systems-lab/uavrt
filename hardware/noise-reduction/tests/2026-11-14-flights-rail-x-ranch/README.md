# Background noise flights, 2026-11-14, Rail-X Ranch Road

**Superseded in part, 2026-11-18:** the signal-generator calibration in `../2026-11-18-bench-mini-vs-hf/` puts these
floors in dBm/Hz. The improvement over Ponui is about 18 dB, not 13, and the remaining in-flight
noise is only 3.3 dB above the HF+'s own floor. Read that note for the corrected comparison.

Seven flights, no tag out, receiver tuned to 160.172 MHz, the frequency of the last Ponui flight.
Five recorded radio data. Data and Michael's notes:
`OneDrive-NorthernArizonaUniversity/FLIGHT_TESTING_DATA/2026-11-14-Rail-X_Ranch_Road/`.
Analysed 2026-11-14 with `tools/noise_floor.py`. Figures: `timelines.png`, `spectra.png`.

**Method.** The floor is the median power in the inner 80 % of the 3.84 kHz band, per second,
from the detector's raw IQ recording, with brief pulses removed by a median over each second. Units
are the receiver's own, so values compare within one receiver only. Across receivers, compare the
*rise*: the in-flight floor minus the same recording's floor in its first seconds, on the ground
with the receiver running and the motors not yet spinning (called the pre-arm floor below).

**Caveat on phases.** No telemetry file covers these flights; the two saved cover 17:10–17:15 UTC
only. Pre-arm, takeoff, steady flight and landing are read from the noise itself and the notes,
not from altitude or throttle.

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

## Open

- PX4 flight logs from the Cube for these flights, to replace the inferred phases with altitude,
  throttle and current.
- How far below the aircraft the antenna hung in flights 6 and 7.
- The receiver's own floor on a 50 Ω load, to tell how much of the remaining 3.5 dB is the drone
  and how much is simply the antenna seeing more of its surroundings from height.
