# NAU VHF tag-tracking drone — hardware

Michael Shafer's tracking drone at Northern Arizona University. The sections match Don Gagne's page
for his own aircraft (`MavlinkTagController2/docs/hardware/PDC_VHF_DRONE.md`) so the two can be
compared side by side.

**This page was started on 2026-11-03 from what had come up in conversation, and filled further
on 2026-11-10 from the ferrite design record (`emi-design.md`).** Anything marked *not recorded* is unknown here, not absent from the aircraft.
Anything marked *unverified* is an estimate or an inference; replace it with a measurement or the
part's label when you have one.

## Airframe

| Item | Part | Notes |
| --- | --- | --- |
| Frame | *Not recorded* | |
| Motors | MAD 5008 300 KV | ×4. MAD lists 25.5 A maximum current, 602 W maximum power and 3.8 kg maximum thrust per motor for the 300 KV version, which it specifies for 6S. Manufacturer's figures, not measured on this aircraft. |
| ESCs | Hobbywing XRotor PRO 50A | ×4, at the motors on the arm tips. 50 A continuous, 100 A peak, 4–6S, no BEC (Hobbywing). Driven by PWM, not DShot; Don measured DShot raising his in-flight floor about 3 dB. The signal ground wires are cut at both ends to break a ground loop, so the signal returns on DC−. Each has two input capacitors; values *not recorded*. Inputs are 12 AWG. |
| Props | 18×6.1 | One of MAD's recommended sizes for the 300 KV version. Material and folding or fixed: *not recorded*. |
| Battery | 6S LiPo: one 16000 mAh pack, or 2–4 × 4500 mAh packs in parallel | The 4500 mAh packs are for trips where the batteries fly as luggage: each is 99.9 Wh (4.5 Ah × 22.2 V nominal). Confirmed by Michael 2026-11-03. Pack makes: *not recorded*. |

## Flight controller

| Item | Part | Notes |
| --- | --- | --- |
| FC | CubePilot Cube Orange+ | Carrier board: *not recorded*. |
| Firmware | PX4 | *Unverified*, inferred from the PX4 parameter names used for the companion link (`MAV_1_CONFIG`, `SER_TEL2_BAUD`). Version: *not recorded*. |
| GPS / compass | CubePilot Here3+ | On CAN 1. Outside the vehicle shield, forward of the fuselage between arms 1 and 3, level with the fuselage top (no mast). Its cable runs inside the shield. |
| Rangefinder | Benewake TFMini-S lidar | Inside the vehicle shield, pointing down through the belly pan; a port is cut in the shield over its optics. Powered from a Cube serial port. |
| RC link | SIYI air unit | Model: *not recorded*. Paired with the SIYI UniRC Pro 7 handheld; see [Ground station](#ground-station). |
| Telemetry | SIYI air unit | Same unit as the RC link. UART and S.Bus to the Cube; powered directly from the power distribution board. Which Cube TELEM port it uses, and that port's PX4 MAVLink instance, are *not recorded*; this matters for cause 3 in `field-notes.md`. |

## Power distribution

```
6S battery → XT90 bulkhead → Matek CAN-L4-BM (battery + only) → PDB → 4× XRotor PRO 50A ESCs
                                                                   ├→ SIYI air unit (direct)
                                                                   └→ Matek PM12S-4A ─┬→ OUT-1 (5 V) → Cube Orange+
                                                                                       └→ OUT-2 (5 V) → Pi 5
```

| Rail | Source | Feeds |
| --- | --- | --- |
| Battery (6S, see [Airframe](#airframe)) | Matek CAN-L4-BM battery monitor | Reports voltage and current to the Cube over CAN; passes battery power to the power distribution board. 150 A continuous, 204.8 A burst (Matek). The same module Don flies. |
| Battery (6S) | Power distribution board | 4× ESCs; SIYI air unit (no regulator); PM12S-4A input |
| 5 V (OUT-1) | Matek PM12S-4A dual regulator | Cube Orange+. *Inferred*: both outputs feed only the Cube and the Pi, and OUT-2 is confirmed as the Pi's. |
| 5 V (OUT-2) | Matek PM12S-4A dual regulator | Pi 5. The Pi reports under-voltage in its heartbeat (the orange bar), so this rail is visible in TagTracker. |

The PM12S-4A replaced a Castle Creations CC BEC 2.0 after the Cumbria fieldwork (November 2025). A colleague reported the Matek UBEC DUO, now
discontinued, was quieter at VHF; Matek lists the PM12S-4A as its successor. It is a different
design and its noise is not yet measured.

**Battery lead, XT90 bulkhead to the battery monitor: 12 AWG since 2026-11-10.** Michael rewired
it from 10 AWG, through the F1 ferrite, because 10 AWG was hard to work with; 12 AWG made the job
much easier. Everything on the aircraft draws through this lead. The sizing, from the discussion
of 2026-10-13:

- Full throttle on all four motors: about 100 A, from MAD's 25.5 A per motor. The Pi, Cube and
  SIYI air unit add about 1 A. *Manufacturer's figure.*
- Hover: about 20–25 A. *Unverified estimate*, for a 4–5 kg quad on 18-inch props. For comparison,
  Don's aircraft measured about 19 A at hover from flight logs, on 15-inch props.
- For a 15 cm lead, 12 AWG loses about 1 W at hover and about 17 W at full throttle. That is fine
  for brief full-throttle bursts; 14 AWG (about 26 W) would not be.
- With 2–4 packs in parallel, each pack's own lead carries only its share, but the lead from the
  parallel join onward carries the full current, so it should be 12 AWG or heavier too.
- The battery monitor (CAN-L4-BM) is rated 150 A continuous, so it is not the limit.
- **Still worth doing:** read the real peak and hover current from a PX4 flight log that includes a
  hard climb, to replace the estimates above. The Cube logs battery current through the monitor.

## Shielding

Designed on 2026-11-09; nothing here is measured yet. The reasoning is in `emi-design.md`.

| What | How | Notes |
| --- | --- | --- |
| Vehicle | Custom-fitted Titan RF fabric cover over the fuselage and motor arms, partly covering the ESCs | Outside it: motors, battery, GPS, SIYI antennas, the HF+. Not yet measured. Don's comparable box wrap gained 7.4 dB. |
| Battery entry | XT90 bulkhead | Battery negative is deliberately not bonded to the shield, so power current stays off it. |
| Lidar window | A port about 20 × 10 mm cut in the shield over the TFMini-S optics, in the belly pan | Size approximate, from Michael 2026-11-10. A slot leaks most when its longest side nears half a wavelength, about 1 m at 150 MHz; 20 mm is about 1/50 of that, so very little gets through *(reasoning, not measured)*. |
| USB entry | USB bulkhead, back shell bonded all the way round to the shield with Titan conductive tape | Continuity checked from the HF+ antenna-port back shell to the shield. Not yet measured. |
| CAN-L4-BM | Kapton, then Titan RF tape; short solder-wick strap to a ground pad on the module (not the dead pad) | Grounded to its own ground, not to the vehicle shield. Not yet measured. |
| PM12S-4A | Kapton, then Titan RF tape; solder-wick strap to the module's ground | Follows Don's treatment of the UBEC DUO, which raised his floor 11 dB bare and 3 dB wrapped. Not yet measured. |

## Ferrites

All Fair-Rite mix 43, the material Fair-Rite recommends for suppression from about 20 to
250 MHz and the one Don uses. Every core carries all the conductors of its cable together, so it
blocks only the noise riding on the cable as a whole. Designed 2026-11-09. **Nothing here is
measured yet**; the test plan is section 5 of `emi-design.md`, and the reasoning for each row is
in its section 2.3 under the same label.

| ID | Location | Part | Turns | Status | Why it is there | Measured effect |
| --- | --- | --- | --- | --- | --- | --- |
| F1 | Battery leads, both together, inside the shield about 1 cm from the XT90 bulkhead | 5943000501 toroid | 2 | Fitted | Keeps noise from inside the shield off the battery leads | Not yet measured |
| F2 | Each ESC input (DC+, DC−, PWM) where it leaves the fuselage, ×4 | 5943000501 toroid | 2 | Fitted | ESC switching noise; Don fits cores at the same place | Not yet measured |
| F3 | Each ESC input at the ESC end, ×4 | 5943000501 toroid | 1 | Fitted; keep only if the test shows a benefit (12 g at each arm tip) | Stops ESC noise before the arm wiring radiates it | Not yet measured |
| F4 | PM12S-4A input pair | 5943000301 toroid | 2, *unverified* | Fitted | Regulator switching noise, as Don treated his UBEC DUO | Not yet measured |
| F5 | PM12S-4A output pairs (to the Cube; to the Pi 5) | 5943000301 toroid | 2 each, *unverified* | Fitted | As F4; Don's output cores took 4 dB off his floor | Not yet measured |
| F6 | SIYI power lead from the distribution board | 5943000301 toroid | 2, *unverified* | Fitted | The SIYI air unit as a source; Don's similar core made no measurable change | Not yet measured |
| F7 | SIYI UART and S.Bus, one shared core | 5943000301 toroid | 3 | Fitted | Same pair of devices, so sharing a core is safe | Not yet measured |
| F8 | CAN-L4-BM CAN lead to the Cube, just outside the module's wrap | 5943000301 toroid | 2 | Fitted | Don measured 12 dB from this lead on the same module | Not yet measured |
| F9 | Here3+ GPS cable at the shield exit, all 4 conductors | 2 × 0443178181 snap-on, stacked | 1 each | Fitted | An unshielded cable crossing the shield | Not yet measured |
| F10 | Coax at the HF+ antenna input | Fair-Rite 5943002701, the FT-140 size, mix 43. 38 g. Identified 2026-11-10: Michael knows it is mix 43 or 44, and the mix-44 part of this diameter is 15 mm tall, against 12.8 mm measured | 12, crossover winding (6 + 6) | Fitted | Keeps the drone's noise off the 15 ft coax. At 12 turns it may resonate below 150 MHz; sweep it | 2026-11-14 flights, HF+, 160.172 MHz: without the coax extension, ~10 dB on the ground and ~5 dB in flight; with the 15 ft coax, ~1–2 dB (height also differed). See `noise-reduction/tests/2026-11-14-flights-rail-x-ranch/` |
| F11 | HF+ USB cable, outside the shield, at the HF+ end | 0443164251 snap-ons, single pass, 2–3 in series | 1 each | **Recommended, not fitted** | Don's strongest result: his cores cut regulator noise reaching his receiver from 9 to about 2 dB. The HF+'s own cable is too thick for 2 passes through this core (found 2026-11-10); see `emi-design.md`, F11. | Not yet measured |
| F12 | USB extension inside the shield, at the Pi end | 1 × 0443164251 snap-on | 2 | **Recommended, not fitted** | Don: removed his last 2 dB | Not yet measured |
| F13 | Coax near the antenna | Not chosen | — | Proposed | The hanging coax runs parallel to the whip; check the antenna's match before fitting | Not yet measured |

Not fitted by decision: the Pi-to-Cube serial link (3–4 cm, too short to radiate), the TFMini-S
(its cable stays inside the shield),
and the motor phase wires (Don measured no difference).

**To record when you can:** whether F4 to F6 really have 2 turns; the outside diameter of the
HF+'s USB cable.

## Companion computer

| Item | Part | Notes |
| --- | --- | --- |
| Computer | Raspberry Pi 5, 8 GB | Raspberry Pi OS 64-bit with desktop, Debian 13 (trixie), freshly installed 2026-11-02. Bootloader 2025-05-08. |
| Storage | SanDisk Extreme PLUS 128 GB microSD | Since 2026-11-02. Replaced a Samsung 128 GB card that was stalling for about 30 s at a time. A spare clone is planned. See `pi5-troubleshooting.md`. |
| FC link | Pi UART0 (GPIO 14 and 15) ↔ Cube TELEM2, 921600 baud | MAVLink. Needs `dtparam=uart0_console` in the Pi's boot configuration on a Pi 5, or the controller opens the wrong port. See problem 3 in `pi5-troubleshooting.md`. |
| Network | Built-in Wi-Fi | Reserved address `192.168.0.100` on the field router, Wi-Fi network `TP-Link_E417`. The reservation is tied to this Pi, not to the card. |
| Enclosure | Inside the vehicle shield | See [Shielding](#shielding). |

## SDR

| Item | Part | Notes |
| --- | --- | --- |
| Receiver | Airspy HF+ Discovery | Noise figure 7.2 dB as installed, against 6.3 dB for the Mini, but unaffected by a −90 dBm signal that raises the Mini's floor 14 dB (bench, 2026-11-18; `noise-reduction/tests/2026-11-18-bench-mini-vs-hf/`). Replaced an Airspy Mini. On the HF+ the controller supports one tag at a time (one decimator channel); the Mini supports several. |
| Mounting | On the aircraft, outside the vehicle shield | Exact position *not recorded*. |
| USB cable | Pi 5 inside the shield → USB-A extension → bonded USB bulkhead → the HF+'s own cable (factory ferrites near both ends) → HF+ | On Don's aircraft this cable was how regulator noise reached the receiver. F11 and F12 in [Ferrites](#ferrites) are the recommended fix, not yet fitted. |

## Antenna

| Item | Part | Notes |
| --- | --- | --- |
| Antenna | Larsen (now Pulse Electronics) PHW150C | The project's omnidirectional antenna. An end-fed half-wave for 144–174 MHz with a base coil and field-tunable whip, and no ground plane; the project's documents call it the monopole. Whip length as tuned, and SWR: *not recorded*. The project also flies directional Telonics antennas; whether this aircraft carries them: *not recorded*. |
| Feed | RG-316 coax, 15 ft (about 4.6 m) | Choked at the HF+ end (F10 in [Ferrites](#ferrites)). |
| Mounting | Hangs below the aircraft on its coax | The hanging coax is vertical, parallel to the whip, which makes it the main path for drone noise into the antenna; see `emi-design.md`, F10 and F13. |

## Ground station

| Item | Part | Notes |
| --- | --- | --- |
| Handheld | SIYI UniRC Pro 7 | Runs TagTracker (Don Gagne's custom build of QGroundControl). Its clock is set to UTC+8, so folder and file names read about 15 hours ahead of Arizona time. Install APKs from a thumb drive: its USB-C port is in video mode. Both from `docs/TASK_COMMS.md`. |
| Field router | TP-Link, Wi-Fi network `TP-Link_E417` | Model: *not recorded*. Used to reach the Pi over ssh in the field. |

## Tags

| Tag | Frequency | Pulse interval / pulse width | Notes |
| --- | --- | --- | --- |
| | | | |
