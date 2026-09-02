# UAV-RT

Open-source uncrewed aerial radio telemetry for wildlife tracking. A drone carries a software-defined radio and antenna, detects VHF transmitter pulses from tagged animals, and helps a field team find them — faster, more safely, and at greater range than tracking on foot or from a crewed aircraft.

Developed at Northern Arizona University's [Dynamic and Active Systems Lab](https://github.com/dynamic-and-active-systems-lab) under NSF awards [1556417](https://www.nsf.gov/awardsearch/show-award?AWD_ID=1556417) and [2104570](https://www.nsf.gov/awardsearch/show-award?AWD_ID=2104570).

**This repository is the starting point.** It holds the system documentation, shared tooling, and a manifest of every component with the versions known to work together. The components themselves live in their own repositories and are cloned here by `bootstrap.sh`.

---

## Get set up

```bash
git clone https://github.com/dynamic-and-active-systems-lab/uavrt.git
cd uavrt
./bootstrap.sh
```

That clones all twelve component repositories at the branch tips recorded in `versions.yaml`, initialises their submodules, and reports on your environment. Re-run it any time to update; it never discards local work.

```bash
./bootstrap.sh --check      # report what you have, change nothing
./bootstrap.sh --pinned     # check out the last verified combination
```

## Read this next

| Document | What it covers |
|---|---|
| [`docs/SOFTWARE_CONTEXT.md`](docs/SOFTWARE_CONTEXT.md) | **The system reference.** Both SDR signal chains, the tunnel protocol, UDP frame formats, build and deploy for every component, known issues. Read before changing anything. |
| [`docs/CLEANUP_TASK_PLAN.md`](docs/CLEANUP_TASK_PLAN.md) | Consolidation and cleanup work: what is done, what is open, how each step was verified. |
| [`CLAUDE.md`](CLAUDE.md) | Context for AI coding agents working in this directory. |

## What the system is made of

```
  ┌──────────────────────────────────────────────────────┐
  │ GROUND STATION            TagTracker (QGroundControl) │
  └────────────────────────┬─────────────────────────────┘
                           │  MAVLink tunnel messages
  ┌────────────────────────▼─────────────────────────────┐
  │ AIRCRAFT (Raspberry Pi)   MavlinkTagController2       │
  │   SDR → decimate → channelize → uavrt_detection       │
  └────────────────────────┬─────────────────────────────┘
                           │  pulse logs (CSV)
  ┌────────────────────────▼─────────────────────────────┐
  │ AFTER THE FLIGHT   uavrt_postflight, uavrt_bearing,   │
  │                    uavrt_localize                     │
  └──────────────────────────────────────────────────────┘
```

| Component | Role |
|---|---|
| [`MavlinkTagController2`](https://github.com/DonLakeFlyer/MavlinkTagController2) | Onboard controller: spawns the SDR pipeline, relays detections to the ground |
| [`TagTracker`](https://github.com/DonLakeFlyer/TagTracker) | Ground station, a QGroundControl custom build |
| [`uavrt_detection`](https://github.com/dynamic-and-active-systems-lab/uavrt_detection) | Near-optimal pulse detector (MATLAB → C++) |
| [`csdr-uavrt`](https://github.com/DonLakeFlyer/csdr-uavrt) · [`airspy_channelize`](https://github.com/dynamic-and-active-systems-lab/airspy_channelize) | Decimation and channelization for the Airspy Mini path |
| [`uavrt_bearing`](https://github.com/dynamic-and-active-systems-lab/uavrt_bearing) · [`uavrt_localize`](https://github.com/dynamic-and-active-systems-lab/uavrt_localize) · [`uavrt_localization_utils`](https://github.com/dynamic-and-active-systems-lab/uavrt_localization_utils) | Bearing estimation and triangulation |
| [`uavrt_postflight`](https://github.com/dynamic-and-active-systems-lab/uavrt_postflight) | Post-flight plotting, bearing estimate, KMZ export |

`versions.yaml` also lists components that are reference-only: `airspy_decimate` (abandoned), `airspyhf_channelize` (incomplete), `uavrt_interfaces` (archived). They are recorded so their status is documented rather than guessed at.

## Two configurations, both supported

The system supports **two SDR receivers** (Airspy Mini and Airspy HF+) and **two antenna types**, and neither pair is a migration in progress — each is a real trade-off.

|  | Directional (Telonics RA-23K/RA-2AK) | Omnidirectional (hanging monopole) |
|---|---|---|
| Gain and directionality | Better | Lower |
| Susceptibility to drone RF noise | Higher — must mount close in | ~10 dB better SNR |
| Close-in pinpointing | Weaker | Better |
| Localization | Mature triangulation | Signal-strength mapping; gradient bearing is experimental |

Details, including the known failure mode of the gradient method over terrain, are in `docs/SOFTWARE_CONTEXT.md`.

## Testing without hardware

The detector reads channelized IQ from a UDP port, so a recorded flight can be replayed into it with no SDR, no aircraft and no radio.

| Tool | Purpose |
|---|---|
| `tools/replay_iq_udp.py` | Replays a recording over UDP with correct framing and timestamps |
| `tools/summarize_detections.py` | Extracts run-invariant detection results from a log; diffs two runs |
| `tools/localization_regression.m` | Bearing and localization regression against the shipped fixtures |
| `tools/test_config_roundtrip.m` | Detector config write/read symmetry |
| `tools/diagnose_bearing_codegen.m`, `tools/probe_table_types.m` | MATLAB Coder diagnostics |

## Published work

- Shafer, Vega, Rothfus, Flikkema (2019). *UAV wildlife radiotelemetry: System and methods of localization.* Methods in Ecology and Evolution.
- Shafer, Flikkema (2023). *Tracking Small Wildlife With Minimal-Complexity Radio Frequency Transmitters: Near-Optimal Detection.*
- Mohammadi, Shafer (2025). *UAV Path Planning for Precision Multi-Target Localization.* IEEE Access 13, 63715–63728.
- Shafer, Mohammadi, Flikkema (in review). *A Field-Ready UAV Solution for Wildlife Radio Telemetry.*

## Licence

Components are GPL-3.0 unless their repository states otherwise. `TagTracker` follows QGroundControl's licensing.
