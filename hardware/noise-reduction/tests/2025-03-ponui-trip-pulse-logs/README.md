# Ponui trip, March 2025: in-flight noise from the pulse logs

Read 2026-11-19 to answer one question: how much did the two snap-on ferrites on the Mini's USB
extension do? Michael: the first flights of the trip had no ferrites on that cable; by Day 8 it had
two, one with two passes and one with three.

## What the Day 1 folder holds

`FLIGHT_TESTING_DATA/2025-03-16-Ponui-Day1-Sun/` has **no flight IQ recordings.** It has:

- **Two 8 s raw captures** (`DRONE LOGS/Logs-RawCapture-2025-03-15_*`): `airspy_rx -f 160.401 -a 3000000
  -h 20 -t 0`, float IQ at 3 MS/s. Michael's note: outside the cabin, antenna hanging from the railing,
  drone on a bench 10–15 ft away, tag transmitting in his bag. Motors off.
- **TagTracker's pulse logs** (`HERELINK LOGS/.../Pulse-*.csv`) for everything flown up to then. The
  same logs, for the whole trip, are in the Day 8 folder under `HERELINK_LOGS/TagTracker Daily/Logs/`,
  sorted into per-day archive folders. Herelink file names are in UTC; NZDT is 13 h later.

## Method: the detector's own noise estimate

Every pulse uavrt_detection reports carries `noise_psd`, its noise estimate for the channel, in the
same digital units as the IQ recording. TagTracker logs it with the aircraft's position. So every
flight with detections has a noise timeline, one point per pulse, even with no IQ recording.

Conversion, Mini bench calibration (`../2026-11-18-bench-mini-vs-hf/`): **dBm/Hz = 10 log10(noise_psd) −
59.81.** `noise_psd` is a mean, so it sits 1.59 dB above the median-based reading of
`tools/noise_floor.py`; the constant includes that.

**Checked against the IQ recordings** of Day 8 flights 2 and 3: above 10 m the pulse logs give −145.7
and −145.5 dBm/Hz; the IQ analysis gave −145.5 and −145.1. Agreement within 0.4 dB.

Tools: `tools/pulse_log_noise.py` (any pulse log) and `tools/raw_capture_floor.py` (airspy_rx raw
captures; emulates the decimate-and-channelize chain, both stages unity gain). Data: `pulse_noise.csv`
(every pulse of the trip with height, SNR and floor), `cabin_capture_*.json`. Figure: `ponui_trip.png`.

## Results, dBm/Hz at the receiver input

| Flights (NZDT) | Where | In flight, >10 m | On the ground, motors off |
|---|---|---|---|
| Sat 15 Mar, 11:23 and 11:41 | Wellington (logged at −41.286, 174.771) | **−138.1, −136.7** | −166 to −169 |
| Mon 17 Mar, 11:26 | Ponui | −132 to −134 (5 weak pulses only) | — |
| Tue 18 to Sun 23 Mar, 15 flights | Ponui | **−144.1 to −148.3, median −145.4** | −168 to −169 after landing |
| Sat 15 Mar evening, cabin, 8 pulses | cabin | — | −146.7 |
| Cabin raw captures, 49 min apart | cabin | — | **−138.6, −144.1** |

The Mini's own noise is −167.6 dBm/Hz (gain 21).

1. **The Day 1 folder cannot answer the ferrite question by itself.** It has no Ponui flights. The only
   flights without the USB-cable ferrites are the two Wellington test flights, at a different site.
2. **The noise is the drone's, at both sites.** On the ground with the motors off it sits at the
   receiver's own noise. When the motors start, still on the ground, it jumps about 30 dB at once, and it
   then stays level from a few metres up to 30 m (Wellington) or 65 m (Ponui). It falls back within
   seconds of the motors stopping. Background noise from a city would show on the ground and would change
   with height. So the site difference is unlikely to explain the gap below.
3. **The Ponui flights from Tue 18 on are about 8 dB quieter than the Wellington flights:** −145.4 against
   −137.4. If the USB-cable ferrites went on between Sat 15 and Tue 18, and nothing else on the aircraft
   changed, about 8 dB is their effect. The Mon 17 flight, at −133, suggests they went on after it, but it
   has only five low-SNR pulses. Not yet confirmed: when the ferrites went on, and whether anything else
   changed then (cable routing, extension length, antenna).
4. **The cabin captures are not the drone.** −138.6 and −144.1 dBm/Hz with the motors off and the antenna
   3–5 m away, where every motors-off reading under the drone sits at the receiver's own noise. The noise
   is flat across ±1 MHz with a comb of lines about 92 kHz apart: a switching power supply, either the
   cabin's or whatever powered the drone on the bench. Treat these captures as the cabin, not as a
   background reference for the island.
5. **Gain-20 offset.** Ponui ran the Mini at gain 20; the calibration is at gain 21. After landing, motors
   off, Ponui reads −168 to −169.5, about 1–2 dB below the receiver's own noise. So the Ponui values in
   dBm/Hz probably read 1–2 dB low, in line with the report's caveat. In-flight Ponui would then be about
   −144 rather than −145.5.

## The sequence so far, in flight

| When | Configuration | In flight, dBm/Hz |
|---|---|---|
| Mar 2025, Wellington | Mini on a USB extension, no ferrites on it, no choke | about −137 |
| Mar 2025, Ponui | the same with two snap-on ferrites on the USB extension | −145.4 |
| Nov 2025, Cumbria | Mini inside the shield, bonded SMA bulkhead, choke | about −158 (`../2025-11-24-cumbria-mini-choke/`) |
| Nov 2026 | HF+ outside the shield, bonded USB bulkhead, choke, aircraft ferrites F1–F9, PM12S-4A | −163.5 |

Each step changes more than one thing, and the sites, frequencies and receivers differ; see the full
configuration history in `../../README.md`.
