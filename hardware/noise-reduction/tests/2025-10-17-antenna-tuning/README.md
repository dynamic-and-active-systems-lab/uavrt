# Antenna whip, untrimmed against trimmed, 2025-10-17

Read 2026-11-20. **Trimming the PHW150C's whip to 160 MHz cut the in-flight noise by 9.4 dB, and the
tag came in about 8 dB stronger.** The untrimmed whip, as flown at Ponui, made the noise worse rather
than hiding it.

**Test (Michael, 2026-11-20).** Two flights minutes apart, before Cumbria, to check that the trimmed
whip was an improvement: first the whip as sold (untrimmed, resonant near 144 MHz), then a whip
trimmed to 160 MHz with a NanoVNA. Aircraft: as flown at Ponui, but with several internal avionics
grounds disconnected to break ground loops, and working toward the Cumbria configuration. Choke:
very probably not fitted (Michael, 2026-11-20: he started flying it a day or two into the Cumbria trip).
Whether the Mini was inside the shield or outside, and exactly which grounds: *not recorded*.
Airspy Mini at gain 21 (the bench calibration's setting), 160.170 MHz, a tag transmitting on the
ground near the takeoff point.

**Which recording is which (confirmed by Michael, 2026-11-20):** Pi session `2025-10-03_19-59-56` (the
Pi's clock was wrong) is the untrimmed whip and `20-05-37` the trimmed one. The tag strength agrees:
the second heard it more strongly, as a better-matched antenna should.

Data: `FLIGHT_TESTING_DATA/2025-10-17-Track_and_Field_Range_173MHz_Flights/`. No flight log covers
these flights (the handheld's telemetry log from that day has the drone on the ground, disarmed).

## Results, dBm/Hz at the receiver input

| | Untrimmed (19-59-56) | Trimmed to 160 MHz (20-05-37) | Difference |
|---|---|---|---|
| On the ground before takeoff, motors off | −166.3 | −164.9 | +1.4 |
| In flight | **−143.8** | **−153.2** | **−9.4 dB** |
| After landing | −165.9 | −166.4 | −0.5 |
| Tag pulse power in flight, median / 90th percentile / max (dBm) | −95.9 / −83.0 / −78.0 | −93.7 / −74.6 / −70.4 | about +8 dB at the top |

The Mini's own noise is −167.6 dBm/Hz. Tag pulse power is the strongest 17 ms of each second within
±90 Hz of the tag, after removing the floor (`tag_power.py`). Flight paths were not logged, so the tag
comparison is indicative; the noise comparison does not depend on the path, since the in-flight noise
held level through each flight.

1. **The untrimmed whip let in 9.4 dB more noise in flight.** A mismatch should pass on less of
   everything the antenna receives, so the noise rising instead points at the coax: an end-fed
   half-wave off resonance drives more current onto the outside of its feed line, which then works as
   more of the antenna and couples the drone's noise in. Not measured directly.
2. **On the ground the two read the same**, within 1.4 dB of the receiver's own noise: the difference
   needs the motors running and the antenna in the air.
3. **For the noise record:** at Ponui the untrimmed whip probably inflated the noise, so part of the
   reduction since then is the whip. The whip was trimmed before Cumbria, so the Ponui-to-Cumbria
   step (12.8 dB) includes it. The Ponui USB-ferrite comparison is unaffected (same whip on both sides).

## The untrimmed flight against Ponui's last flight

Same untrimmed whip, same frequency (160.17 MHz). Ponui Day 8 flight P3 (`2025-03-22_05-02-04`, Mini
at gain 20, two snap-on ferrites on the USB extension, Mini outside the shield) against the October
untrimmed flight (gain 21, internal grounds disconnected, Mini placement unknown, choke very probably
not fitted). Figure: `ponui_vs_untrimmed.png`.

| dBm/Hz | Ponui P3 | 17 Oct, untrimmed | Difference |
|---|---|---|---|
| On the ground, motors off | −162.5 | −166.3 | −3.8 |
| Steady flight | −145.1 | −143.8 | +1.3 |
| Steady-flight spectrum across the channel, 10th–90th percentile | −145.3 to −144.9 | −144.8 to −143.5 | both flat |

Ponui's gain of 20 probably reads 1–2 dB low (motors off after landing it reads below the receiver's
own noise), which would make the in-flight values about equal and the ground difference 2–3 dB.

1. **In the air, about no difference.** With the untrimmed whip, the noise in flight was the same as at
   Ponui, despite the ground-loop work and whatever change there was in where the Mini sat.
2. **On the ground, motors off, October was 2–5 dB quieter,** close to the receiver's own noise. So
   the ground-loop work (and any move of the Mini) cleaned up the motors-off noise, but the in-flight
   noise came in through the untrimmed whip and its coax and did not move.
3. **That splits the Ponui-to-Cumbria step (−12.8 dB):** about nothing from Ponui to the October
   untrimmed flight; −9.4 dB from trimming the whip; about −5 dB more to Cumbria from the choke, the
   site, the frequency (173 MHz) and the gain setting together.

The sites differ (Ponui Island against a track-and-field range), so a site difference could hide in
the first row; but the in-flight noise was set by the drone at both, since it appears only with the
motors running.

A third flight that day, `19-42-45` at 173.129 MHz: −164.4 on the ground, −151.3 in flight. Which whip
it carried is not recorded.

Files: `floors.json` (per-second floors and tag power, and the stage medians), `tag_power.py`. The
report's Figure "untrimmed against trimmed" is built from `../../data/antenna_tuning.csv`.
