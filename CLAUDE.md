# UAV-RT — project hub

Single entry point for the UAV-RT wildlife radio-telemetry system (NSF awards 1556417, 2104570).
PI: Dr. Michael W. Shafer, Northern Arizona University, Dynamic and Active Systems Lab.

**This directory is itself a git repository** — the hub. It tracks `README.md`, `CLAUDE.md`, `docs/`,
`tools/`, `versions.yaml` and `bootstrap.sh`. The component repositories sitting beside them are
**gitignored**: each keeps its own history and pushes to its own remote. `bootstrap.sh` clones them
from `versions.yaml`. Do not add them as submodules; that was considered and rejected.

**Read `docs/SOFTWARE_CONTEXT.md` before making changes.** It is the authoritative map of the
system: both SDR signal chains, the tunnel protocol, the UDP frame format, build and deploy for every
component, and known issues. This file is the index; that file is the reference.

---

## What is here

| Directory | What it is |
|---|---|
| `MavlinkTagController2` | Companion-computer monorepo (Don Gagne). MAVLink controller, decimator, ZMQ publisher, Python detector, IQ simulator. **Most actively developed.** |
| `TagTracker` | Ground control station — a QGroundControl custom build (Don Gagne). |
| `uavrt_detection` | Primary detector. MATLAB → MATLAB Coder → C++. Michael's algorithm. |
| `uavrt_postflight` | Post-flight analysis: pulse-log reader, plotting, bearing estimate, KMZ export. Has its own `CLAUDE.md` — read it before touching that repo. |
| `airspy_channelize` | Mini path: 375 kSPS → 100 channels @ 3750 SPS. MATLAB Coder. |
| `airspyhf_channelize` | **Incomplete.** An unfinished attempt to support the Airspy HF+; never fully tested. See "Open questions". |
| `airspy_decimate` | **Abandoned.** MATLAB-Coder ÷8 decimator, superseded by `csdr-uavrt`. Not referenced anywhere in `MavlinkTagController2`. Possibly useful for bench work. |
| `csdr-uavrt` | Fork of csdr providing `fir_decimate_cc` in the Mini pipeline. |
| `uavrt_bearing` | PCA bearing estimation (Shafer 2019 method). Branch `pulse_tables`, frozen 2023. **Not reachable from the flight system.** |
| `uavrt_localize` | Triangulation from bearings (Lenth 1981). Branch `main`, frozen 2023. **Not reachable from the flight system.** |
| `uavrt_localization_utils` | Shared MATLAB utilities; a **submodule of `uavrt_localize`**, but `uavrt_bearing` carries diverged copies. Branch `euler_angs`, frozen 2023. |
| `uavrt_interfaces` | ROS2 message definitions. **Archived on GitHub**; reference only. |
| `PRIVATE/` | Source documents and the context files. Not code. |
| `_baseline/` | Regression-test scratch: warm threshold cache, detector config, baseline logs. Not a repo. |

Everything above is under version control. `dynamic-and-active-systems-lab/*` is Michael's org;
`DonLakeFlyer/*` is Don Gagne, an **unpaid volunteer collaborator** — his repos take pull requests,
not direct pushes.

---

## Rules

1. **Both SDR chains are supported.** Airspy Mini (what Michael flies) and Airspy HF+ (what Don
   develops on). Never propose removing the Mini path.
2. **Both antenna types are supported.** Directional (Telonics RA-23K/RA-2AK, mounted close, better
   gain and directionality, mature triangulation) and omnidirectional (hanging monopole 5 m below,
   ~10 dB quieter, better close-in pinpointing). They are a deliberate trade-off, each with its own
   localization methods. Never propose consolidating to one antenna or one method family.
3. **Never hand-edit `codegen/`.** It is MATLAB Coder output. Change the `.m` source; codegen is
   Michael's step (see below).
4. **`OLD_CODE/` is an archive, never live code.** It is gitignored and local-only. Do not treat
   anything in it as current, and do not delete it — it is deliberately kept as a record of how the
   current design was reached.
5. **Check tunnel-protocol submodule SHA parity** across `TagTracker/custom/tunnel-protocol` and
   `MavlinkTagController2/tunnel-protocol` before debugging any comms problem. If they diverge, the
   GCS and the aircraft silently disagree about the wire format.
6. **Prefer the simulator** (`MavlinkTagController2 --simulator`) over assuming hardware.

## What the agent cannot do

- **Run MATLAB.** No Coder, no `checkcode`, no runtime verification of `.m` files. Verify instead by
  static inspection or by transliterating numeric logic to Python and running it against real data.
  **Never claim MATLAB code has been tested.** Say which method was used.
- **Build for the Pi.** `make` in `uavrt_detection` targets aarch64 Linux with GCC and OpenMP; it does
  not build on macOS. It links cleanly on x86_64 Linux, which is a useful smoke test.
- **Push to GitHub.** No credentials. Prepare commits and hand the push to Michael.

## The MATLAB Coder loop

Claude edits `.m` sources → **Michael runs codegen in MATLAB** → Michael commits. Source edits and
regenerated `codegen/` go in **separate commits** so the source change stays reviewable.

For `uavrt_detection`: add `matlab-coder-utils/c-udp` to the MATLAB path, delete `codegen/`, run
`uavrt_detection_codegen_no_ros_script.m`, then `make`.

## Testing without hardware

`uavrt_detection` reads channelized IQ from a UDP port, so a recorded flight can be replayed into it
with no SDR, no Pi and no channelizer.

| Tool | Purpose |
|---|---|
| `tools/replay_iq_udp.py` | Replays a `data_record.*.bin` over UDP, synthesising the per-datagram timestamp and pacing at the configured rate |
| `tools/summarize_detections.py` | Extracts run-invariant detection results from a diary log; diffs two runs |
| `tools/test_config_roundtrip.m` | Verifies `DetectorConfig` write/read symmetry |

Reference baseline: **51 pulses over 18 segments** from `data_record.2.5.bin`, in
`_baseline/baseline_before.txt`. Threshold generation is stochastic on a cache miss — always run
against the warm cache in `_baseline/thresholds/`, or comparisons are meaningless.

Procedure is in `docs/CLEANUP_TASK_PLAN.md`, Task 0.

## Context documents

| File | Contents |
|---|---|
| `docs/SOFTWARE_CONTEXT.md` | **The system reference.** Read first. |
| `docs/CLEANUP_TASK_PLAN.md` | Cleanup work: what is done, what is open, and the verification procedure. |
| `PRIVATE/PROJECT_CONTEXT.md` | Program and proposal history. Not needed for code work. |
| `uavrt_postflight/CLAUDE.md` | That repo's own hazards and working notes. |

---

## Open questions — consolidation in progress

These are unresolved and a session should not assume an answer.

1. **HF+ support for `uavrt_detection`.** The detector currently works with the Mini's 3750 SPS.
   Supporting the HF+ needs either `airspy_channelize` extended to handle both sample rates, or
   `airspyhf_channelize` finished and tested. Neither has been done.
2. **Duplication within the directional localization family.** See `SOFTWARE_CONTEXT.md` §9b before
   touching any of it. The four bearing/localization implementations are **two families matched to the
   two antennas**, and both families stay. The real problems are narrower: `uavrt_bearing` forked the
   shared utility library instead of consuming it as a submodule and five files have diverged; the
   `doapca.m` copy that `uavrt_localize` actually builds against **silently discards the antenna
   mounting offset**; and two of the three repos sit on side branches, so a fresh `main` clone gets
   stale code. `BearingCalculator.cpp` and `uavrt_bearing`'s `doapca` do overlap, but **both are
   deliberately retained** — the former is fitted to one specific antenna pattern, the latter is
   antenna-agnostic, and their relative robustness to noise is untested. Do not propose retiring
   either.
3. **`uavrt_bearing` codegen does not complete**, and its committed `codegen/` has not matched its
   MATLAB since December 2023. Separate task; see `SOFTWARE_CONTEXT.md` §9b. Every Coder repo here
   commits generated code and carries the same risk of silent drift.
4. **Legacy ROS2 repos** (`uavrt_supervisor`, `uavrt_connection`, `uavrt_source`) are deliberately not
   cloned. To be archived on GitHub.
