# Airspy Mini vs HF+ calibration with a signal generator, 2026-11-18

Bench test in the office: an Agilent E4432B tone at 160.172500 MHz into each receiver, on the
drone's Pi through the normal processing chains (Survey Detection), motors off. Data and Michael's
notes: `FLIGHT_TESTING_DATA/2026-11-18-Office_HF_v_Mini_Testing/`. The first two log folders are
checkout runs and are not used. Analysed with `tools/bench_calibration.py`.

**Runs:** Mini_1 (`15-24-11`), HF+ (`15-32-46`), Mini_2 (`15-40-45`), in that order. Each: 50 Ω
termination, generator connected with RF off, then −120, −110, −100, −90 dBm. Path from generator
to receiver: N-to-SMA adapter, 88 cm RG-316, choke; **0.6 dB loss** at 160 MHz from the NanoVNA
measurements (`../2026-11-17-vna-cables/results_2026-11-17.md`). Mini gain setting **21**
(`airspy_rx -h 21`); the HF+ runs its fixed settings.

## The measurement is sound

- **Linear:** 10 dB more tone gives 9.9–10.1 dB more reading on both receivers, from −120 to
  −90 dBm. Neither overloads at −90 dBm.
- **Repeatable:** Mini_1 and Mini_2 agree within 0.05 dB on every tone step and within 0.1 dB on
  the floor.
- **No bench pickup:** generator connected with RF off reads within 0.1 dB of the termination on
  both receivers, so nothing came in through the bench grounding.
- **Tone frequency:** both receivers read the tone about 90–95 Hz low, about −0.6 ppm. Harmless.

## Results

| | Airspy Mini (gain 21) | Airspy HF+ |
|---|---|---|
| Floor on 50 Ω, at the receiver input | **−167.6 dBm/Hz** | **−166.8 dBm/Hz** |
| Noise figure, as installed on the drone | **6.3–6.4 dB** | **7.2 dB** |
| Conversion: dBm at input = reading in dB − | 59.9 dB | 24.1 dB |
| Floor near the tone at −110 / −100 / −90 dBm | +0.5 / +4.9 / +14.2 dB | no change |

1. **The Mini is about 0.8 dB more sensitive than the HF+ as installed.** The HF+ is not the more
   sensitive receiver.
2. **The HF+'s advantage is handling strong signals.** A tone at −100 dBm raises the Mini's floor
   near it by 5 dB, and at −90 dBm by 14 dB (8 dB across the whole band). The HF+ is unaffected. A
   close, strong tag would therefore blind the Mini to weaker signals near it in frequency; the HF+
   would not notice. Same generator for both, so the effect is the Mini's, not the generator's.
3. **Converting units:** a Mini reading is 35.7 dB higher than an HF+ reading of the same input.

## The flight floors in dBm/Hz

Converted using each receiver's bench floor, with the same method as the 2026-11-14 analysis so its
bias cancels. "Above own floor" is how far the noise sits above the receiver's own noise.

| Flight | dBm/Hz | Above own floor |
|---|---|---|
| Ponui 2, ground, motors off | −161.5 | +6.1 dB |
| Ponui 2, in flight | −145.5 | +22.1 dB |
| Ponui 3, ground, motors off | −162.4 | +5.2 dB |
| Ponui 3, in flight | −145.1 | +22.5 dB |
| 2026-11-14 flight 2 (choke + 15 ft coax), ground | −167.3 | −0.6 dB |
| 2026-11-14 flight 2, in flight | −163.5 | +3.2 dB |
| 2026-11-14 flight 3 (choke + 15 ft coax), in flight | −163.4 | +3.3 dB |
| 2026-11-14 flight 5 (no choke + 15 ft), in flight | −161.7 | +5.0 dB |
| 2026-11-14 flight 6 (no choke, no extension), ground | −155.2 | +11.5 dB |
| 2026-11-14 flight 7 (choke, no extension), in flight | −161.5 | +5.2 dB |

4. **About 18 dB less noise reaches the receiver in flight than at Ponui:** about −145 dBm/Hz then,
   −163.5 dBm/Hz now. This replaces the rough 13 dB of the 2026-11-14 note, which could not account
   for the two receivers' different sensitivities. The sites still differ.
5. **At Ponui the aircraft was already 5–6 dB above the receiver's floor on the ground, motors
   off.** Now it sits at the receiver's floor: with motors off, nothing the aircraft makes is
   measurable.
6. **In flight the noise is now only 3.3 dB above the receiver's own.** The outside noise, from the
   drone and the surroundings together, is about equal to the receiver's own noise. Removing all
   of the drone's noise could gain at most 3.3 dB, and some of that is the antenna hearing more of
   its surroundings from height. Further ferrite work has little left to win.

## Caveats

- **Gain setting:** Ponui ran the Mini at gain 20; this test used 21. The conversion for the Ponui
  rows is off by the difference between those two settings, likely 1–2 dB. Repeating one Mini run
  at gain 20 would remove this.
- **"As installed":** both noise figures include whatever the drone's electronics add through the
  USB with the motors off. The RF-off check shows nothing came in through the bench, not that
  nothing came in through the USB.
- **Generator level accuracy** and the 0.6 dB path loss are each good to a few tenths of a dB; they
  affect both receivers equally, so the comparison between them is tighter than the absolute
  numbers.
