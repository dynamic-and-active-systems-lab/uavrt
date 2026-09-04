# UAV-RT Software System Context

**Maintainer:** Dr. Michael W. Shafer, Northern Arizona University (DASL)
**Companion doc:** `PROJECT_CONTEXT.md` (program/proposal history)
**Created:** 2026-08-31
**Working directory:** `/Users/mws22/Developer/uavrt`

---

## 0. Scope and How To Use This Document

This document describes the **operational UAV-RT software system** — the code that runs on a flight, plus the ground tooling that turns a flight into a bearing. It is written for Claude sessions doing development work in this directory.

**Deliberately excluded:** the legacy ROS2 architecture (`uavrt_supervisor`, `uavrt_connection`, `uavrt_source`, `uavrt_ws` deployment) and the original MATLAB `UAV-RT` system. That material belongs to proposal history, not to current engineering.

**ROS2 was removed from `uavrt_detection` on 2026-09-01** (branch `remove-ros2`; see `CLEANUP_TASK_PLAN.md` for the full record). The detector no longer has a ROS2 code path at any build. `uavrt_interfaces` is archived on GitHub.

**Both SDR signal chains are current and supported.** Don Gagne has moved to the Airspy HF+; Michael still flies the Airspy Mini. Backward compatibility to the Mini is a requirement, not a legacy concern. Do not propose removing the Mini path.

---

## 1. Repository Map

All repos live side by side under `/Users/mws22/Developer/uavrt/`.

| Repo | Owner | Lang | Build | Last commit | Role |
|---|---|---|---|---|---|
| `MavlinkTagController2` | DonLakeFlyer | C++20 / Python | CMake ≥3.20 + CPM | 2026-04-13 | Companion-computer monorepo: MAVLink controller, decimator, ZMQ publisher, Python detector, IQ simulator |
| `TagTracker` | DonLakeFlyer | C++ / QML | CMake + Qt 6 | 2026-08-27 | Ground control station — QGroundControl custom build |
| `uavrt_detection` | DASL | MATLAB → C++ | `make` via matlab-coder-utils | 2025-03-18 | Primary detector: near-optimal pulse detection |
| `airspy_channelize` | DASL | MATLAB → C++ | Coder + `make` | 2023-04-01 | Mini path: 375 kSPS → 100 channels @ 3750 SPS |
| `airspy_decimate` | DASL | MATLAB → C++ | Coder + `make` | 2024-09-06 | Mini path: 3 MSPS → 375 kSPS (÷8) |
| `airspyhf_channelize` | DASL | MATLAB → C++ | Coder + `make` | 2022-09-20 | Ancestor of `airspy_channelize`; HF+ era |
| `csdr-uavrt` | DonLakeFlyer | C | `make` | 2024-09-11 | Fork of csdr; provides `fir_decimate_cc` in the Mini pipe |
| `uavrt_interfaces` | DASL | C++ (ROS2 msgs) | colcon | 2025-01-15 | ROS2 message definitions — **archived on GitHub**, retained locally for reference only |
| `uavrt_postflight` | DASL | MATLAB | none (base MATLAB) | 2026-09-01 | Post-flight analysis: pulse-log reader, signal-strength plotting, bearing estimate, KMZ export |

Ground post-processing was moved into this directory and onto GitHub on 2026-09-01 as `uavrt_postflight` (formerly the unversioned `uavrt_kml` working directory in OneDrive). Every part of the operational chain is now under version control.

### Ownership note

The two most actively developed repos (`MavlinkTagController2`, `TagTracker`) are under Don Gagne's personal GitHub account. He is an **unpaid volunteer collaborator** who works on this as a hobby. This is the single largest sustainability risk in the software system and must be addressed explicitly in any proposal's Sustainability section.

---

## 2. System Architecture

Three tiers, connected by two well-defined interfaces.

```
┌─────────────────────────────────────────────────────────┐
│ TIER 1 — GROUND CONTROL STATION                          │
│ TagTracker (QGroundControl custom build)                 │
│ Runs on: laptop, or Herelink controller (Android)        │
│ Qt state machines drive takeoff → rotate → detect → RTL  │
└───────────────────────┬─────────────────────────────────┘
                        │ MAVLink TUNNEL messages
                        │ (TunnelProtocol.h — shared submodule)
┌───────────────────────▼─────────────────────────────────┐
│ TIER 2 — COMPANION COMPUTER (Raspberry Pi 5, /home/pi)   │
│ MavlinkTagController2 spawns + monitors child processes: │
│   SDR source → decimate → channelize → detector(s)       │
│ Pulses relayed back to GCS over the same tunnel          │
└───────────────────────┬─────────────────────────────────┘
                        │ CSV files (Pulse-*.csv, Rotation-N.csv)
                        │ written by the GCS, not the Pi
┌───────────────────────▼─────────────────────────────────┐
│ TIER 3 — GROUND POST-PROCESSING (MATLAB, offline)        │
│ uavrt_kml / pulseplotter2 → bearings, surfaces, KMZ      │
└─────────────────────────────────────────────────────────┘
```

**Critical invariant:** `TunnelProtocol.h` is a git submodule in *both* TagTracker (`custom/tunnel-protocol`) and MavlinkTagController2 (`tunnel-protocol`), pointing at `DonLakeFlyer/TagTrackerTunnelProtocol`. Both are currently at `af114d8`. **If these two SHAs diverge, the GCS and the aircraft will silently disagree about the wire format.** Check this first when debugging inexplicable comms behavior.

---

## 3. The Tunnel Protocol

MAVLink `TUNNEL` messages carrying a custom binary payload. Every message begins with `HeaderInfo_t { uint32_t command; }`.

| ID | Command | Direction | Purpose |
|---|---|---|---|
| 1 | `ACK` | Pi → GCS | Acknowledge, with result + message |
| 2 | `START_TAGS` | GCS → Pi | Clear tag DB, begin upload |
| 3 | `END_TAGS` | GCS → Pi | Upload complete |
| 4 | `TAG` | GCS → Pi | One tag definition (`TagInfo_t`) |
| 5 | `START_DETECTION` | GCS → Pi | Spawn SDR chain + detectors |
| 6 | `STOP_DETECTION` | GCS → Pi | Tear down all child processes |
| 7 | `PULSE` | Pi → GCS | One detected pulse |
| 8 | `RAW_CAPTURE` | GCS → Pi | Capture raw SDR data to disk |
| 9 | `HEARTBEAT` | Pi → GCS | Status + CPU temperature |
| 10/11 | `START/STOP_ROTATION` | (log only) | Never sent; marks rotation bounds in CSV |
| 12/13 | `SAVE_LOGS` / `CLEAN_LOGS` | GCS → Pi | Log management to USB/SD |
| 14 | `AIRSPY_STATUS` | GCS → Pi | Query which Airspy is attached |
| 15–18 | `START_ROTATION_DETECTION`, `START_DETECTION_AT_HEADING`, `STOP_ROTATION_DETECTION`, `BEARING_RESULT` | both | **Python-detector-only** rotation sequence with onboard bearing calculation |

### `TagInfo_t` — the core data structure

```
id, frequency_hz, pulse_width_msecs,
intra_pulse1_msecs, intra_pulse2_msecs,
intra_pulse_uncertainty_msecs, intra_pulse_jitter_msecs,
k, false_alarm_probability,
channelizer_channel_number, channelizer_channel_center_frequency_hz,
ip1_mu, ip1_sigma, ip2_mu, ip2_sigma
```

`intra_pulse2_msecs != 0` signals a **rate-switching tag**, which drives secondary-channel allocation throughout the system (a second detector on port+1).

Timing semantics, which the detector depends on and which are easy to conflate:

- **`tip`** — nominal inter-pulse interval (PRI).
- **`tipu`** — *systematic* uncertainty in the mean PRI. **Accumulates linearly**: by pulse *n* the window is `n·tip ± n·tipu`. Arises from manufacturer tolerance and oscillator drift.
- **`tipj`** — *stochastic* per-pulse jitter, independent pulse to pulse, does not accumulate.

---

## 4. Signal Chain A — Airspy Mini (Michael's current flight configuration)

```
airspy_rx -f <MHz> -a 3000000 -r /dev/stdout -h <gain> -t 0
    │  3 MSPS complex IQ, via stdout pipe
    ▼
csdr-uavrt fir_decimate_cc 8 0.05 HAMMING
    │  375 kSPS, via stdin pipe
    ▼
~/repos/airspy_channelize/airspy_channelize <channel list>
    │  100 channels × 3750 SPS, UDP
    ▼
detector(s) on UDP 20000 + (channel-1)*2   [secondary: +1]
```

- Spawned by `CommandHandler::_handleStartDetection` in the `else` branch (`deviceType` is neither `HF` nor `SIMULATOR`).
- `airspy_channelize` channel→port mapping: positive channel *n* → port `20000 + (n-1)*2`; a **negative** channel number additionally emits on the odd secondary port (rate-switching tags).
- `TagDatabase::channelizerCommandLine()` builds the channel argument list, negating the channel number when `intra_pulse2_msecs != 0`.
- `channelizerTuner.cpp` assigns tags to channels.
- `airspy_decimate` (÷8, 3 MSPS → 375 kSPS) is the MATLAB-Coder equivalent of the `csdr-uavrt` stage. The flight system uses `csdr-uavrt`; `airspy_decimate` exists as the pure-MATLAB alternative and for bench work.

**Provisioning gap — known issue.** Commit `c45b047` (2026-03-03, "remove stale repos") deleted `csdr-uavrt`, `airspy_channelize`, and `uavrt_detection` from `setup/full_setup.sh`, while `CommandHandler.cpp` on `main` still spawns all three by absolute path. **A Pi provisioned with the current setup script cannot run the Mini path.** The pre-`c45b047` version of that script (recoverable at `git show 6f173f8:setup/full_setup.sh`) documents the correct build steps. This needs resolving with Don.

---

## 5. Signal Chain B — Airspy HF+ (Don's current configuration)

```
airspyhf_zeromq_rx -Z -f <MHz + 0.010> -a 768000 -g off -m on
    │  768 kSPS, ZeroMQ PUB on tcp://127.0.0.1:5555
    │  40-byte packed LE header + interleaved float32 IQ
    ▼
airspyhf_decimator --input-rate 768000 --shift-khz 10 --ports 10000,10001
    │  three-stage FIR: 8 × 5 × 5 = 200×  →  3840 SPS
    ▼
detector(s) on UDP 10000 (primary) / 10001 (secondary)
```

- The receiver is tuned **+10 kHz above** the requested center to move the target off the HF+ DC bin; the decimator applies a compensating `--shift-khz 10` digital shift, re-centering the signal while parking the hardware DC spur at +10 kHz. **These two offsets must stay matched.**
- Both binaries are built from the `MavlinkTagController2` monorepo — no external repos on this path, which is why Don could prune the setup script.
- The ZMQ packet header is defined once in `shared/tagtracker_wireformat/zmq_iq_packet.h`: magic `0x5a514941`, version 1, 40 bytes, `sequence`, `timestamp_us`, `sample_rate`, `sample_count`, `payload_bytes`, `flags` (`0x1` = final chunk).

### Simulator path

`--simulator [preset]` replaces the SDR with `simulator/iq_simulator.py`, publishing wire-compatible IQ on the same ZMQ port; the decimator runs with `--shift-khz 0` (no hardware spur to dodge). Presets: `strong`, `weak`, `noise-only`, `two-tags`, `distant`, `dropout`, `gap`. Tag parameters from the MAVLink tag database map to `--freq-offset-hz`, `--tp`, `--tip`. **This is the fastest way to exercise the full pipeline without hardware and should be the default for development work.**

---

## 6. The Two Detectors

Selected by `StartDetectionInfo_t.detection_mode`, surfaced in the GCS as a setting.

### `DETECTION_MODE_UAVRT` (0) — `uavrt_detection`

MATLAB source → MATLAB Coder → C++ executable. Michael's algorithm; the scientifically authoritative implementation.

- Entry point `uavrt_detection.m(configPath, thresholdCachePath)`.
- Reads `config/detectorConfig.txt` via the `DetectorConfig` class; the controller writes one config file per tag per channel.
- Builds a *priori* `pulsestats` object, then STFT → spectral weighting (`weightingmatrix.m`, sub-bin matched filter) → incoherent summation over K pulses (`incohsumtoeplitz.m`, `buildtimecorrelatormatrix.m`) → threshold test → `confirmpulses.m` → `repetitionrejector.m`.
- Thresholds from an extreme-value distribution (`evthresh.m`), cached to `thresholdCachePath`.
- Spawned as `~/repos/uavrt_detection/uavrt_detection <configFile> <thresholdCachePath>`.
- Detection runs **continuously** during rotation; the GCS uses rate-detector heartbeat gating to decide when a slice has enough data.

### `DETECTION_MODE_PYTHON` (1) — `pulse_detector.py`

Lives in the monorepo at `detector/pulse_detector.py`. A Python reimplementation tracking the MATLAB algorithm closely — `detector/PYTHON_VS_UAVRT_COMPARISON.md` is a source-level comparison of the two and is the best single document for understanding either.

- Args: `--tp --tip --fs --port --pf --center-freq --tag-id --freq --pulse-port --threshold-cache-dir --detection-margin --confidence-ratio --k --tip-secondary --warmup-seconds`.
- Defaults: `fs=3840` (HF+ rate), `k=5`, `detection-margin=0.90`, `confidence-ratio=1.3`.
- Runs from `MavlinkTagController2/.venv/bin/python3`, falling back to system `python3`.
- Detection is started and stopped **per slice**; the GCS waits for a confirmed pulse-or-no-pulse verdict from every detector before advancing. Bearing is computed onboard (`BearingCalculator.cpp`) and returned via `BEARING_RESULT`.

Sample rates differ by path: **3840 SPS** (HF+/simulator) vs **3750 SPS** (Mini). `isHFMode` selects both the rate and the port base throughout `CommandHandler.cpp`.

---

### Channelizer → detector UDP frame format

Undocumented anywhere in the repos until now, and easy to get wrong. Each datagram is exactly **1024 complex float32 samples (8192 bytes)**, and **the first sample is a timestamp, not signal**:

```
[ sec:uint32 | nsec:uint32 ]  +  1023 × ( I:float32, Q:float32 )
```

`uavrt_detection.m` recovers it with `typecast(real(dataReceived(1)),'uint32')` — a **bit reinterpretation**, not a numeric conversion. The remaining 1023 samples are the IQ payload. `channelizerSampleFrameSize = 1024` and `dataWriterPacketsPerInterval = ceil(interval/((packetLength-1)/Fs))` both confirm the 1023 payload length. The HF+ decimator's `--frame` option describes the same convention ("timestamp + payload").

Two consequences:

- The detector's staleness check (`uavrt_detection.m:252`) compares packet timestamps against its own expectations. Feeding it old timestamps causes a permanent stale/flush loop with no detections.
- `data_record.*.bin` recordings contain **only the IQ payload** — `asyncWriteBuff` is fed post-strip `iqData`. Replaying a recording therefore requires synthesising fresh timestamps. `tools/replay_iq_udp.py` does this.

## 7. Port Map

| Port | Protocol | Use |
|---|---|---|
| 5555 | ZMQ PUB | `airspyhf_zeromq_rx` / `iq_simulator.py` → decimator |
| 10000 / 10001 | UDP | HF+/simulator channel data → detector (primary/secondary) |
| 20000 + (n-1)*2 | UDP | Mini channel *n* → detector (primary) |
| 20001 + (n-1)*2 | UDP | Mini channel *n* → detector (secondary, rate-switching tags) |
| pulse-port | UDP | Detector → `UDPPulseReceiver` in the controller |
| 14540 | UDP | Default MAVLink (PX4 SITL) |
| `/dev/serial0:921600` | serial | MAVLink to Pixhawk in flight |

---

## 8. Build and Deploy

### Companion computer (Raspberry Pi 5, user `pi`, repos under `/home/pi/repos`)

System packages: `build-essential git cmake pkg-config libboost-all-dev libzmq3-dev libusb-1.0-0-dev libairspyhf-dev python3 python3-venv`

`MavlinkTagController2` checks all of these at configure time and fails with an actionable message. MAVLink C headers are **not** a submodule — CPM downloads `mavlink/c_library_v2` pinned at `ae473c3a` during CMake configure.

```bash
cd ~/repos/MavlinkTagController2
git submodule update --init --recursive     # tunnel-protocol
make                                        # controller + decimator + airspyhf_zeromq
./setup_venv.sh                             # .venv: numpy>=2.0, pyzmq>=25.0, scipy>=1.12
```

Autostart: `crontab -e` → `@reboot /bin/bash /home/pi/repos/MavlinkTagController2/setup/crontab-start-controller.sh`, which sources `.venv` and runs the controller against `serial:///dev/serial0:921600`, logging to `/home/pi/MavlinkTagController.log`.

Pixhawk config: `MAV_1_CONFIG`=TELEM2, `MAV_1_MODE`=Onboard, `MAV_1_FORWARD`=On, `SER_TEL2_BAUD`=921600 8N1. Pi timezone must be **UTC**; serial console disabled, hardware serial enabled.

### GCS

Standard QGroundControl custom build: Qt 6, CMake, Ninja. All third-party deps (SDL2, exiv2, GeographicLib, shapelib, ulog_cpp, libevents, zlib, expat, …) are fetched by CPM at configure time — **do not clone them.** Submodules needed: `custom/tunnel-protocol` and `src/FirmwarePlugin/APM/ArduPilot-Parameter-Repository`. Android/Herelink builds define `TAG_TRACKER_HERELINK_BUILD`.

### MATLAB Coder repos — the standard pattern

`uavrt_detection`, `airspy_channelize`, `airspy_decimate`, `airspyhf_channelize` all share one workflow, and **generated C++ is committed to git**:

1. Edit `.m` sources on a Mac with MATLAB + Coder.
2. Run the repo's codegen script (for `uavrt_detection`: `uavrt_detection_codegen_no_ros_script.m`).
3. `git add .` — the regenerated `codegen/` tree is part of the commit.
4. `make` on the target builds the executable via `matlab-coder-utils/Makefile`.

`matlab-coder-utils` (DonLakeFlyer, submodule) supplies the Makefile, the `c-udp` UDP system objects (`ComplexSingleSamplesUDPReceiver`, `PulseInfoStruct`), and vendored Coder headers.

**Implication for AI-assisted work: Claude can edit `.m` sources but cannot run MATLAB Coder.** The loop is: Claude edits sources → Michael runs codegen in MATLAB → Michael commits. Source edits and regenerated codegen should be separate, individually reviewable commits.

For `uavrt_detection`, add `matlab-coder-utils/c-udp` to the MATLAB path before codegen. (The former `no-ros-pulse-send` path entry was deleted with ROS2 support.)

### Testing without hardware

`uavrt_detection` reads channelized IQ from a UDP port, so a recorded `data_record.*.bin` can be replayed into it with no SDR, no Pi and no channelizer. Tooling lives in `tools/`:

| Tool | Purpose |
|---|---|
| `replay_iq_udp.py` | Replays a recording over UDP, synthesising the per-datagram timestamp sample and pacing at the configured rate |
| `summarize_detections.py` | Extracts run-invariant detection results from a diary log and diffs two runs |
| `test_config_roundtrip.m` | Verifies `DetectorConfig` write/read symmetry |

Reference baseline: `_baseline/` holds a warm threshold cache, a repointed config, and `baseline_before.txt` — **51 pulses over 18 segments** from `data_record.2.5.bin`. Threshold generation is stochastic on a cache miss, so always run against the warm cache or comparisons are meaningless.

---

## 9. Ground Post-Processing (`uavrt_postflight`)

The GCS writes two CSV families to its log directory:

- **`Pulse-<timestamp>.csv`** — every confirmed pulse for the session, with rotation start/stop markers (command IDs 10/11) carrying GPS coordinates.
- **`Rotation-<N>.csv`** — one file per rotation.

Columns (20, after a leading command-id field):
`tag_id, frequency_hz, start_time_seconds, predict_next_start_seconds, snr, stft_score, group_seq_counter, group_ind, group_snr, noise_psd, detection_status, confirmed_status, latitude, longitude, altitude_rel, roll_deg, pitch_deg, yaw_deg, antenna_offset`

`pulseplotter2.m` (a MATLAB App; `pulseplotter.mlapp` is the App Designer twin — identical apart from the class name) reads these, plots SNR/score by time, heading or position, interpolates a surface, estimates a bearing, and exports KMZ.

### Format hazard — four header variants

TagTracker has shipped **four** header variants of the same file, including a 2023 build with **no header at all**. In every variant the first 16 fields are in the same order and columns 14/15/16 are lat/lon/alt, so `readpulsetable.m` parses **positionally** and ignores header names. It also strips the leading `#` and rejects the 4-field rotation start/stop records interleaved among pulse records — `readtable` turns those into bogus "pulses" carrying a latitude in the `tag_id` column, which corrupts the tag list and any local frame anchored on the first row.

### Toolbox independence

The repo is base-MATLAB only. Automated Driving (`latlon2local`/`local2latlon`), Mapping (`wrapTo360`), Statistics (`nanmean`) and a third-party KML toolbox were all removed — partly so it runs on a bare install, partly because a mobile port is the stated next step and the numeric core is now plain arithmetic. Geodesy is a flat-earth WGS84 approximation agreeing with a rigorous ECEF ENU transform to under 5 cm over a 1 km box.

### Bearing estimate — **not validated against ground truth**

Magnitude-weighted circular mean of the interpolated SNR surface's gradient directions, reporting bearing (compass degrees), confidence (resultant length 0–1) and spread (circular standard deviation). Verified numerically only. **The Cumbria Tag 42 flight has a known tag position and is the obvious validation case; until that is done, treat bearings as indicative.**

## 9b. Antenna Configurations and Localization Methods

*Written 2026-09-01, corrected the same day after PI input. **Both antenna types are supported deliberately and permanently.** An earlier draft of this section wrongly treated the directional/omnidirectional split as an unresolved inconsistency. It is not — it is a designed trade-off, and each antenna has its own matched localization method.*

### The two configurations are complementary, not competing

| | **Directional** (Telonics RA-23K / RA-2AK) | **Omnidirectional** (hanging monopole) |
|---|---|---|
| Mounting | Near the airframe, ~0.5 m below | Suspended ~5 m below on coax |
| Gain / directionality | **Better** — real gain and a usable beam pattern | Lower gain; toroidal pattern with the null pointed at the drone |
| Susceptibility to drone RF noise | **Higher** — it has to be mounted close in | **~10 dB better SNR** in testing; distance plus null orientation both help |
| Close-in precision pinpointing | **Weaker** | **Better** |
| Localization methods | Rotation-slice pattern fit; PCA bearing (`doapca`); **well-established triangulation** from multiple bearings | Signal-strength surface mapping; gradient bearing (**experimental**) |
| Maturity | Established, trusted | Mapping is proven in the field; the gradient bearing estimator is **not** |

**Neither replaces the other.** The directional antenna gives gain, directionality and mature triangulation methods; the omnidirectional gives a much quieter receive path and better close-in pinpointing. Operators choose per mission. Any consolidation must preserve both families of method.

### Known limitation of the gradient method

**The gradient bearing estimator fails when there is significant topography near the drone.** The method assumes the interpolated SNR surface slopes monotonically toward the transmitter; terrain near the aircraft breaks that assumption. This is known from field experience, is not captured in the `uavrt_postflight` code or docs, and is separate from the fact that the estimator has never been checked against ground truth. Treat it as experimental.

This is consistent with what Mohammadi 2026 reports independently: received signal strength peaks when the UAV is slightly *downhill* of the tag rather than above it, because of the interaction between the monopole's toroidal pattern and terrain-dependent propagation. Terrain is the common factor.

### The four implementations

### The four implementations

| Where | Method | Antenna assumed | When it runs | Reachable from flight system? |
|---|---|---|---|---|
| `MavlinkTagController2/controller/BearingCalculator.cpp` | Least-squares fit of measured SNR across rotation slices against a hardcoded antenna pattern | **Directional Telonics RA-2AK** (19-point pattern, 0–180° in 10° steps, "eyeballed from the RA-2A polar plot") | In flight, Python-detector rotation mode | **Yes** |
| `uavrt_postflight` | Magnitude-weighted circular mean of the interpolated SNR surface's gradient | **Omnidirectional monopole** | Post-flight, MATLAB app | N/A — offline |
| `uavrt_bearing` | PCA of SNR vs. heading (`doapca.m`), the Shafer 2019 method | Directional, with antenna offset applied | Intended in-flight | **No** — not referenced anywhere in `MavlinkTagController2` |
| `uavrt_localize` | Triangulation from multiple bearings — Lenth (1981) MLE, repeated median regression, and M-estimation | n/a, consumes bearings | Intended in-flight | **No** |

Repo status: `uavrt_bearing` on branch `pulse_tables` (2023-12-20), `uavrt_localization_utils` on branch `euler_angs` (2023-08-17), `uavrt_localize` on `main` (2023-07-03). **All three frozen since 2023**, and two are on side branches rather than `main`.

### The structural problem: a shared library that was forked instead of shared

`uavrt_localization_utils` is a **git submodule of `uavrt_localize`** — it is the intended shared layer. But `uavrt_bearing` carries its **own copies** of 15 of those files rather than consuming the submodule, and five have since diverged:

| File | Status |
|---|---|
| `doapca.m` | **Diverged — behaviour differs, see below** |
| `PulseStruct.m` | Diverged (78 lines) |
| `readbearingcsv.m` | Diverged (46 lines) |
| `readpulsecsv.m` | Diverged (15 lines) |
| `vincentydistance.m` | Diverged (155 lines) |
| 10 others | Identical |

`uavrt_localize` pins `uavrt_localization_utils` at commit `478805c`.

### The divergence that matters: `doapca.m` ignores antenna offset in one copy

`uavrt_bearing`'s copy is the newer, corrected one. It was reworked to take a pulse **table** rather than a struct array, and critically it applies the antenna mounting offset:

```matlab
% uavrt_bearing (newer, correct)
angs = wrapTo2Pi( (curr_yaws + curr_antennaOffsets)*pi/180 );
DOA  = wrapTo360( 180/pi * DOA_calc );

% uavrt_localization_utils (older, via the submodule uavrt_localize pins)
angs = curr_yaws*pi/180;
DOA  = 180/pi*DOA_calc;
```

**The submodule copy discards `antennaOffset` entirely.** Any bearing computed through `uavrt_localize` → `uavrt_localization_utils` is therefore wrong by the antenna's mounting offset from vehicle heading, and unwrapped. Since `uavrt_localize` pins the submodule, that is the copy its build uses.

Both copies also call `wrapTo2Pi`/`wrapTo360`, which are **Mapping Toolbox** functions — the same dependency deliberately removed from `uavrt_postflight`. Any consolidation should drop them too.

### What this means for consolidation

The four implementations are **not four answers to one question**. They are two families:

- **Directional family:** `BearingCalculator.cpp` (in flight, reachable), `uavrt_bearing`'s `doapca` (PCA bearing), `uavrt_localize` (triangulation from bearings).
- **Omnidirectional family:** `uavrt_postflight` (signal-strength mapping, plus the experimental gradient bearing).

So the goal is **not** to pick a winner. It is to remove the duplication *within* the directional family — where a shared library was forked and has silently diverged — while keeping both families working.

### The two directional bearing methods differ in generality — keep both

They overlap, but they are not equivalent:

| | `BearingCalculator.cpp` | `doapca.m` (`uavrt_bearing`) |
|---|---|---|
| Approach | Least-squares fit of measured SNR to a **hardcoded antenna pattern** | **PCA** of SNR vs. heading |
| Antenna assumption | **Tuned to one specific antenna** — a 19-point RA-2AK pattern, eyeballed from the RA-2A polar plot | **Antenna-agnostic** — no pattern model |
| Consequence | Should do better with the antenna it was built for; degrades with any other | Works with any directional antenna; gives up the prior that a known pattern provides |
| Author | Don Gagne | Shafer (Shafer 2019 method) |

**Decision (PI, 2026-09-01): both are retained.** The pattern-fit method may outperform PCA with its matched antenna, but PCA generalises across antennas, and their **relative robustness to noisy signals has not been tested**. Retiring either before that comparison would be guessing. This overlap is therefore deliberate, not debt.

**Open task worth doing:** compare the two methods against noisy real-world pulse logs. Both consume the same inputs — per-pulse SNR with vehicle heading — so a fair comparison is tractable offline against recorded flight logs, without hardware. See "Suggested consolidation order" below.

### Empirical baseline — measured 2026-09-01

Captured with `tools/localization_regression.m` under MATLAB R2025a, run twice with only one copy of the shared utilities on the path each time. Outputs in `_baseline/localization_bearing.txt` and `_baseline/localization_utils.txt`.

| Fixture | utils from `uavrt_bearing` | utils from `uavrt_localization_utils` |
|---|---|---|
| `rotation_example.csv` | **197.718853°** | **ERROR** `MATLAB:table:LinearSubscript` |
| `rotation_example_2.csv` | **179.806138°** | **ERROR** (same) |
| `rotation_example_2_with_ant_offset.csv` | **269.806138°** | **ERROR** (same) |
| `rotation_example_old.csv` | ERROR `subsassigndimmismatch` | ERROR (same) |
| `localize()` on `bearing_example.csv` | returns 0, positions match `positions_example.csv` | **identical** |

**Three conclusions, all of which simplify the consolidation:**

1. **The `uavrt_localization_utils` copies are not merely older — they are non-functional with the current caller.** `bearing.m` passes a pulse **table**; that copy of `doapca` expects a **struct array** and indexes `pulseList(:)`. Every pulse fixture fails. So there is no contest between the two copies: `uavrt_bearing`'s are the only ones that run. Promoting them is a repair, not a preference.

2. **The antenna offset is applied correctly, and provably.** `rotation_example_2.csv` gives 179.806138° and `rotation_example_2_with_ant_offset.csv` gives 269.806138° — a difference of **exactly 90.000000°**, matching the fixture's offset. This is direct evidence that `uavrt_bearing`'s `doapca` handles the offset the submodule copy discards.

3. **`readbearingcsv`'s 46-line divergence does not change behaviour on this fixture.** `localize()` produced byte-identical positions under both copies, matching `positions_example.csv` exactly. This was the one item flagged as needing a PI decision before refactoring; the risk is lower than assumed, though the fixture is narrow (see below).

**Pre-existing failure, not a regression:** `rotation_example_old.csv` fails under *both* configurations with `subsassigndimmismatch`. It is an obsolete-format fixture; the failure predates any change made here.

**Coverage gap in the localize fixture:** `bearing_example.csv` contains only two bearings per tag, so MLE, repeated-median regression and M-estimation all return the identical intersection — the three methods are degenerate by construction on this input. The fixture therefore verifies that `localize()` runs and is reproducible, but does **not** exercise the differences between Lenth's three estimators. A three-or-more-bearing fixture would be needed for that.

### Committed codegen can silently stop matching its source — a systemic risk

`uavrt_bearing`'s committed `codegen/` was generated **2023-11-07**. Five weeks later, `8064a2d` converted the pulse pipeline from structs to tables and was never regenerated. The repository has therefore shipped C++ that calls a struct-based reader alongside MATLAB that produces tables — **for two years** — and nothing detected it, because nothing rebuilds it and `main` was stuck behind the side branch that held the change.

This is not specific to `uavrt_bearing`. Every MATLAB Coder repo here commits generated code: `uavrt_detection` (284 files), `uavrt_localize` (216), `uavrt_bearing` (148), plus `airspy_channelize` and `airspy_decimate`. All carry the same exposure, and only `uavrt_detection` has been regenerated recently (2026-09-01, during the ROS2 removal).

**Worth building:** a freshness check comparing the newest tracked `.m` mtime against the codegen build timestamp, run before any release or flight. It would have caught this in December 2023.

**Current state of `uavrt_bearing` codegen:** does not complete. Two Coder restrictions found and one fixed; the next is the struct/table type conflict at `readpulsecsvtable.m:22-23` versus `:270`. `tools/probe_table_types.m` measures the column types the fix needs. Restoring it is tracked as separate work — the tail is unknown, and it is not a regression from the consolidation.

### What `uavrt_bearing` and `uavrt_localize` actually contain

*Established 2026-09-02. Both repos are dormant — nothing in `MavlinkTagController2` or elsewhere in the tree references them — but they are **not** superseded, and the PI intends to revisit them. Do not archive, move or delete them without asking.*

`BearingCalculator.cpp` does not replace them. It never touches a file: rotation slices accumulate in memory during flight (`heading_deg`, `snr_db`, `tag_id` per pulse) and are fed to `addSlice()` / `solve()` when the rotation stops, with the answer going straight to the GCS as a `BEARING_RESULT` tunnel message. It writes `bearing_result.log` as a record, never reads it. The MATLAB path is file-driven throughout: `bearing.m` reads a pulse CSV, `localize.m` reads a bearing CSV.

Four things in those repos have no equivalent anywhere else in the project:

| File | What it is |
|---|---|
| `doapca.m` | PCA bearing estimate (Shafer 2019). Antenna-agnostic, and applies the antenna mounting offset — which `BearingCalculator` never receives. |
| `localizefrombearings.m` | **All three Lenth (1981) estimators, fully implemented**, 258 lines: MLE (iterative, convergence guard, NaN on failure), RMR (pairwise ray intersections, median per ray then median of medians), and MEST (Andrews psi at c = 1.5 with von Mises κ from the mean resultant length). The only triangulation in the project. Header documents Lenth's X-East/Y-North compass convention and what to swap for other frames. |
| `vincentydistance.m` / `vincentyendpoint.m` | Proper geodesics — more rigorous than `uavrt_postflight`'s flat-earth approximation. |
| `latlon2eastnorth.m` | The frame conversion the above depend on. |

**A comparison of `BearingCalculator` against `doapca` is not a matter of pointing both at one file** — they have no common input interface. It needs a harness that parses a pulse log and calls `addSlice()`. `controller/tests/test_bearing_calculator.cpp` already does exactly this with synthesised data drawn from the real RA-2AK pattern via `patternLinear()`, so extending it to read a CSV is the short path.

**Watch the reference frames when comparing.** `BearingCalculator` receives only `heading_deg`; `doapca` uses `curr_yaws + curr_antennaOffsets`. If the antenna is not aligned with vehicle heading the two work in different frames, and the constant offset would look like an accuracy disagreement when it is not.

### Suggested consolidation order

Both antenna families stay, and both directional bearing methods stay. Consolidation here means removing **duplication and defects**, not implementations.

1. **Promote `uavrt_bearing`'s copies into `uavrt_localization_utils`**, then make `uavrt_bearing` consume the submodule instead of carrying copies. Measured above: the submodule copies do not run at all against the current caller, so this is a repair. Bump the submodule pin in `uavrt_localize` afterwards and re-run the harness — `localize()` must still reproduce `positions_example.csv`.
2. ~~Fix the antenna-offset bug~~ — subsumed by step 1; the fix already exists in `uavrt_bearing`'s copy and is verified by the 90.000000° offset result.
3. **Drop the Mapping Toolbox calls** (`wrapTo2Pi`, `wrapTo360`) as was done in `uavrt_postflight`, so these repos run on a bare MATLAB install.
4. ~~**Merge the side branches**~~ — **DONE 2026-09-01.** Both were clean fast-forwards, performed with `git branch -f` so the working tree was never touched (the baseline above therefore still holds without re-running). `uavrt_bearing` main `1d22eb4` → `8064a2d`; `uavrt_localization_utils` main `2ecd007` → `cf6d5cb`. **Not yet pushed.**

   *Incidental fix:* moving these repos off OneDrive had flipped every tracked file from mode 644 to 755, showing ~420 phantom modifications across the three repos and their submodules. Resolved with `git config core.fileMode false` locally in each — a local config change, nothing committed, no file contents touched.
5. **Reconcile the pulse readers.** `uavrt_bearing`/`uavrt_localization_utils` define `readpulsecsv.m` returning `PulseStruct`/`CommandStruct`; `uavrt_postflight` defines `readpulsetable.m` returning a table. Both parse TagTracker pulse logs, and `uavrt_postflight` handles four header variants plus interleaved rotation records that the older reader may not. The differing names avoided a MATLAB path collision; the underlying duplication is real.
6. **Record the gradient method's topography limitation** in `uavrt_postflight` — done 2026-09-01 in that repo's `CLAUDE.md`.

**Deferred, not part of consolidation:** a comparative evaluation of `BearingCalculator.cpp` versus `doapca` under noisy conditions. Tractable offline against recorded pulse logs; would inform whether either method can eventually be retired, and would be citable.

## 10. Known Issues, Risks, and Open Questions

1. **Mini-path provisioning is broken** in the current `full_setup.sh` (§4). Highest-priority functional issue.
2. **Volunteer dependency.** The two most active repos are on an unpaid collaborator's personal account.
3. **Bearing and localization are fragmented across four implementations, one of which silently drops the antenna offset.** See §9b — the single largest consolidation problem in the codebase.

4. **The `uavrt_postflight` bearing estimator is unvalidated.** `uavrt_postflight` produces a bearing, confidence and spread from every rotation, verified numerically but never checked against a flight with a known tag position. This is the last unquantified link between a detection and a claim about where an animal is. *(Resolved 2026-09-01: the unversioned-code risk previously listed here — `uavrt_kml` is now `uavrt_postflight` on GitHub.)*
5. **Detector divergence risk.** Two independent detector implementations (MATLAB/C++ and Python) must track each other. `PYTHON_VS_UAVRT_COMPARISON.md` is the reconciliation document and should be updated whenever either changes.
6. **`uavrt_detection` was frozen from March 2025 to August 2026** while the monorepo moved fast. `main` now includes the peeling-algorithm bounds guard (`5766874`), previously stranded on `fix_peel_algo_error`, plus the ROS2 removal.
7. **Peeling-algorithm anomaly is guarded, not fixed.** `waveform.m` now catches the case where the peel loop finds at least as many peaks as frequencies (observed in flight: index 151 vs bound 150) and logs loudly instead of crashing. The root cause is unknown. There is also a per-iteration `fprintf('Everything normal, p = %f')` in that loop that costs real time on the Pi and should be removed once the anomaly is understood.
8. **`OLD_CODE/` (90 MB) is gitignored and local-only.** Archived, not live. Never treat it as current. Retained deliberately as a reference for understanding how the current design was reached.
9. **`DetectorConfig.writeToFile` was broken for years and is now repaired.** `detectorsetting2configstr.m` declared 20 parameters against a 17-argument caller, with rotated `sprintf` arguments, an invalid `\c` escape, a mis-capitalised key, and a missing tab. Repaired 2026-09-01; writer and reader key sets are now exactly symmetric, verified by `test_config_roundtrip.m`. The C++ writer in `TagDatabase.cpp` remains the one used in flight.

10. **Large gitignored trees.** `src/` (38 MB), `config/src/` (38 MB), `data_for_testing_detection_code/` are local build output, not repo content. The tracked surface of `uavrt_detection` is only **339 files**.

---

## 11. Conventions for Claude Sessions in This Directory

- **Never propose removing the Airspy Mini path.** Both chains are supported.
- **Never hand-edit `codegen/`.** It is generated output. Change the `.m` source and hand codegen back to Michael.
- **Never treat `OLD_CODE/` as live code.**
- **Check tunnel-protocol submodule SHA parity** across TagTracker and MavlinkTagController2 before debugging comms.
- **Prefer the simulator** (`--simulator`) over hardware assumptions when writing or testing pipeline code.
- Repos on GitHub: `dynamic-and-active-systems-lab/*` (Michael) and `DonLakeFlyer/*` (Don). All local remotes are HTTPS except `uavrt_detection` (SSH).
- Local ssh note: this Mac carries an NAU mSCP security baseline restricting `PubkeyAcceptedAlgorithms` to `ecdsa-sha2-nistp256`. Ed25519 keys will not authenticate. Use `~/.ssh/id_ecdsa_github`.
