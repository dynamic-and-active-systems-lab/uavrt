# Cleanup Task Plan — Removing ROS2 and Vestigial Code from `uavrt_detection`

**Created:** 2026-08-31
**Target repo:** `/Users/mws22/Developer/uavrt/uavrt_detection`
**Companion doc:** `SOFTWARE_CONTEXT.md`

---

## Progress — updated 2026-09-01

| Task | State |
|---|---|
| 0 — Baseline | **DONE.** 51 pulses, 18 segments, 0 thresholds generated, 0 peel anomalies. `_baseline/baseline_before.txt` |
| 1 — Remove ROS2 pulse-send indirection | **DONE, VERIFIED.** `after_task1.txt` → `RESULT: MATCH`, detection list identical; 49 `Skipping ROS2 Pulse send` lines → 0 |
| 2 — Delete ROS2 codegen path | **DONE.** `uavrt_detection_codegenerator.m` removed, README rewritten |
| 3b — `detectorsetting2configstr` | **DONE (option b: repaired for bench use).** Signature realigned to 17 params, all 5 defects fixed, write/read symmetry restored. Needs `test_config_roundtrip.m` run to confirm |
| 3c — `ros2enable` in `TagDatabase.cpp` | **PR SUBMITTED** to DonLakeFlyer/MavlinkTagController2 from mwshafer fork, branch `remove-ros2enable`. Also corrects 4 stale ROS2 references in UAVRT_DETECTION_ANALYSIS.md |
| 4 — Vestigial sweep | **DONE.** 85 lines of dead comments removed, `msgdef/` archived, `nargin` guard fixed |
| 5 — Regenerate codegen | **DONE.** 275 files regenerated, no ROS2 symbols in generated C++, clean link on Ubuntu x86_64. Two commits pushed on branch `remove-ros2` |
| 6 — Peel-loop `fprintf` | Deferred pending flight data |
| Remaining | Pi build, flight test, merge `remove-ros2` to `main`. Email to Don re: Mini provisioning not yet sent |

Everything removed was archived to `OLD_CODE/` first: `ros-pulse-send/`, `msgdef/`, `removed_comment_blocks/`, `uavrt_detection_codegenerator.m`, `README_pre_ros2_removal.md`.

### Task 3b finding — `detectorsetting2configstr` is already broken

While preparing to remove the `ros2enable` argument, the caller and callee turned out not to match at all.

`detectorsetting2configstr.m` declares **20 parameters**. `DetectorConfig.writeToFile` (line 225) passes **17 arguments**, and they misalign from position 5 onward:

| Caller passes | Lands in parameter |
|---|---|
| `obj.Fs` | `ipCntrl` |
| `obj.tagFreqMHz` | `portCntrl` |
| `obj.tp` | `Fs` |
| `obj.tip` | `tagFreqMHz` |
| … | … (shifted by two throughout) |
| `obj.startIndex` | `dataRecordPath` |
| *(never passed)* | `processedOuputPath`, `ros2enable`, `startInRunState` |

So `writeToFile` cannot execute — it errors with "Not enough input arguments", the same failure mode as the `nargin` guard bug. There is a second defect in the same file: the `sprintf` format string at line 31 contains `\channelCenterFreqMHZ` — `\c` is not a valid escape, so the `ID` and `channelCenterFreqMHZ` fields would run together on one line and the resulting file would not parse.

**This path is dead.** `MavlinkTagController2` writes detector config files in C++ (`TagDatabase.cpp`); nothing in the flight system calls `DetectorConfig.writeToFile`.

**DECIDED 2026-09-01: option (b) — repaired for bench use.**

Five defects were present, not two. In addition to the 17-vs-20 signature mismatch:

3. The `sprintf` arguments were **rotated** relative to their specifiers — `uint32(ID)` fed `timeStamp`'s `%0.3f`, `channelCenterFreqMHZ` fed `ID`'s `%d`, `currTime` fed `channelCenterFreqMHZ`'s `%f`.
4. The key was spelled `channelCenterFreqMHZ` (capital Z); the reader matches `channelCenterFreqMHz`, so that field would never have loaded.
5. That key was emitted with no tab after the colon. The reader locates values via `tabLocs(1)+1`, so a tabless line does not merely mis-parse — it errors on an empty index.

The repair realigns the signature to the 17 parameters the caller already passes, in the order it already passes them (the caller needed no change), and makes the emitted key set **exactly** the set `DetectorConfig.setFromFile` parses — verified programmatically, no key emitted that is not parsed and none parsed that is not emitted. Legacy keys `ipCntrl`, `portCntrl`, `processedOuputPath`, `ros2enable` and `startInRunState` were dropped: none is read, and `ros2enable` is obsolete. **This completes Task 3b's `ros2enable` removal as a side effect.**

The broken original is archived at `OLD_CODE/detectorsetting2configstr_BROKEN.m`.

**Verify with:** `tools/test_config_roundtrip.m` — writes a config through `writeToFile`, reads it back with `setFromFile`, and compares every property. Expect `RESULT: PASS`.

Task 3c (deleting the `ros2enable` line from Don's `TagDatabase.cpp`) is unaffected and still stands on its own.

---

## Ground Rules

1. **Claude edits `.m` sources. Michael runs MATLAB Coder. Michael commits.** Claude cannot run MATLAB, so every task that touches a `.m` file ends with a handoff.
2. **Source edits and regenerated `codegen/` go in separate commits.** A source-only commit is reviewable; a commit mixing 13,000 lines of regenerated C++ with a 5-line source change is not.
3. **Never hand-edit `codegen/`.**
4. **Work on a branch**, not `main`. Suggested: `remove-ros2`.
5. **The simulator is the test harness.** `MavlinkTagController2 --simulator` exercises the full chain without hardware or a Pi.

---

## What Is Actually There

The ROS2 surface in this repo is small — the 90 MB `OLD_CODE/`, 38 MB `src/`, and 38 MB `config/src/` trees are all gitignored build output. **Only 339 files are tracked.** The real footprint:

| Item | Tracked | Status |
|---|---|---|
| `uavrt_detection.m` lines 48, 576 | yes | Calls `ros2Setup()` / `ros2PulseSend(...)` |
| `ros-pulse-send/` | yes | Real ROS2 publisher. `ros2PulseSend` has **no `.m` extension** — already deliberately disabled |
| `no-ros-pulse-send/` | yes | Stub shims with identical signatures that print "disabled" and return 0 |
| `uavrt_detection_codegenerator.m` | yes | ROS2 codegen: `coder.hardware('ROS 2')`, `/opt/ros/galactic`, `~/uavrt_ws`, hardcoded `134.114.16.153` / user `dasl` |
| `detectorsetting2configstr.m` | yes | `ros2enable` argument and format field |
| `README.md` | yes | Dominated by ROS2/colcon/galactic deployment instructions |
| `msgdef/` | no (gitignored) | Coder message definitions for `uavrt_interfaces` |

### The mechanism to understand before touching anything

`ros2Setup` and `ros2PulseSend` are resolved **by MATLAB path order at codegen time**. Putting `no-ros-pulse-send/` on the path selects the stubs; putting `ros-pulse-send/` on the path selects the real ROS2 publisher. The rPi build already uses the stubs — so the shipping detector calls a function whose entire body is `fprintf("(Skipping ROS2 Pulse send)")`, once per detected pulse.

That is the vestigial structure to remove: not just the ROS2 code, but the indirection that exists only to switch it off.

### Cross-repo coupling — do not miss this

`MavlinkTagController2/controller/TagDatabase.cpp:63` writes `ros2enable:\tfalse` into **every** detector config file it generates. `DetectorConfig.m` does not appear to parse that key. Removing `ros2enable` from one side without checking the other is the most likely way to break the system during this cleanup. **Task 3 handles both sides together.**

---

## Task 0 — Baseline

**Owner:** Michael (MATLAB). Claude has prepared the harness.

The baseline does **not** require building `MavlinkTagController2`, a Pi, an SDR, or the channelizer. `uavrt_detection.m` reads channelized IQ from a UDP port, so a recorded `data_record.*.bin` can be replayed straight into it from the same machine. This exercises exactly the code being changed, on real recorded signal, in Michael's own Mini configuration.

**Prepared assets** (already written, nothing tracked by git):

| Path | What |
|---|---|
| `tools/replay_iq_udp.py` | Replays a recording over UDP, paced at the configured sample rate |
| `_baseline/detector.2.baseline.config` | `detector.2.config` with the old `/home/dasl` paths repointed at `_baseline/` |
| `uavrt_detection/data_for_testing_detection_code/data_record.2.5.bin` | The recording: 272,384 complex samples = exactly 266 frames = 72.6 s at 3750 Hz |
| `_baseline/thresholds/` | Copy of the 9 cached `.threshold` files, so runs do not write into the repo's test data |

Recording format confirmed against the source: `fwrite(..., interleaveComplexVector(...), 'single')` → interleaved little-endian float32.

**The datagram format is not raw IQ.** Each UDP packet is 1024 complex float32 (8192 bytes) where **sample 1 is a timestamp** — `sec:uint32` and `nsec:uint32` bit-cast into the two float32 slots — followed by 1023 IQ samples. The recording holds only the IQ payload, so the replay tool synthesises fresh timestamps from the current wall clock, advancing 1023/Fs per datagram. Old timestamps trip the staleness check at `uavrt_detection.m:252` and produce an endless `STALE DATA` / flush loop with zero detections. (This is exactly what the first baseline attempt on 2026-09-01 produced, which is how the format was found.)

**Steps**

- [ ] `cd /Users/mws22/Developer/uavrt/uavrt_detection && git checkout -b remove-ros2`
- [ ] MATLAB path: add `matlab-coder-utils/c-udp` and `no-ros-pulse-send`
- [ ] In MATLAB, from the `uavrt_detection` directory. **Both arguments are required** — the default guard is `if nargin == 0`, not `nargin < 2`, so a one-argument call errors on line 18:
      ```matlab
      diary('/Users/mws22/Developer/uavrt/_baseline/baseline_before.txt')
      uavrt_detection('/Users/mws22/Developer/uavrt/_baseline/detector.2.baseline.config', ...
                      '/Users/mws22/Developer/uavrt/_baseline/thresholds')
      ```
- [ ] In a terminal, once the detector is listening:
      `python3 /Users/mws22/Developer/uavrt/tools/replay_iq_udp.py \
          /Users/mws22/Developer/uavrt/uavrt_detection/data_for_testing_detection_code/data_record.2.5.bin \
          --port 20000 --fs 3750`
- [ ] Let it run the full 72.6 s, stop the detector, `diary off`
- [ ] Record: number of pulses detected, their tag IDs / SNRs / times, and any warnings

### Determinism warning — run the baseline TWICE

Threshold generation is **stochastic**: when a needed threshold is not in the cache, `threshold.m` generates it from 100 random trials (`Trials100` in the cache filenames). Two runs with a cache miss will produce different thresholds, and therefore possibly different detections, for reasons that have nothing to do with any code change.

The cache is keyed `N<...>-M<...>-J<...>-K<...>-Trials<...>.threshold` and currently holds 9 files (N = 63, 64, 66, 129, 131, 178, 258 at K = 1 and 3). If the run needs an N that is not present, it generates and caches it.

So:

1. **First run** — populates any missing thresholds into `_baseline/thresholds/`. Discard this log.
2. **Second run** — now fully cache-hit and deterministic. **This is the baseline.** Save as `baseline_before.txt`.
3. All later verification runs use the same `_baseline/thresholds/` directory, so they are comparable.

Watch the log for `Building thresholds...` — if it appears on the second run, something is still missing and the comparison is not yet trustworthy.

**This log is the regression reference.** Every task below is verified by re-running this identical procedure and diffing against it. Detection output must be **bit-identical** after ROS2 removal — the code being deleted is a pair of no-op stubs, so any change in detections means something else was disturbed.

**Order matters:** start the detector first and wait for `Starting processing...` before launching the replay. MATLAB blocks inside `uavrt_detection`, so the replay runs from a separate Terminal window.

**If the detector does not receive data:** an unbroken run of `STALE DATA FLAG` with a 0-byte `data_record.*.bin` means datagrams are arriving malformed or not at all. Check that `portData` matches `--port`, that `Fs` matches `--fs`, and that nothing else holds the port. `--fast` is for smoke-testing the plumbing only — it drops packets and must not be used for the baseline.

## Task 1 — Collapse the ROS2 pulse-send indirection

**Claude edits. Michael codegens.**

Files: `uavrt_detection.m`, `ros-pulse-send/`, `no-ros-pulse-send/`

- [ ] Delete line 48: `[pulsePub, pulseMsg] = ros2Setup();`
- [ ] Delete line 576: `ros2PulseSend(pulsePub, pulseMsg, pulseInfoStruct, detectorPulse);`
- [ ] Remove `pulsePub` / `pulseMsg` from any remaining signatures or declarations they appear in.
- [ ] **Archive before deleting:** `mkdir -p OLD_CODE/ros-pulse-send && cp ros-pulse-send/* OLD_CODE/ros-pulse-send/`
      (`OLD_CODE/` is gitignored, so this preserves the only surviving example of the ROS2 pulse message mapping locally without carrying it in the repo. Restore the `.m` extension on the archived `ros2PulseSend` so it is readable as MATLAB.)
- [ ] `git rm -r ros-pulse-send/ no-ros-pulse-send/`
- [ ] Remove `no-ros-pulse-send` from the path instructions in `README.md` and from `uavrt_detection_codegen_no_ros_script.m` if referenced there.

**Verification:**
- `grep -rn "ros2Setup\|ros2PulseSend\|pulsePub\|pulseMsg" --include=*.m .` returns nothing outside `OLD_CODE/`.
- Codegen completes without "undefined function" errors — this is the real test, since Coder will catch any missed reference.
- Simulator run matches baseline pulse counts.

**Risk:** low. The stubs are no-ops; removing a no-op cannot change detection behavior.

---

## Task 2 — Delete the ROS2 codegen path

**Claude edits. No codegen needed.**

- [ ] `git rm uavrt_detection_codegenerator.m`
- [ ] Rewrite `README.md`: delete the ROS2 deployment section (ROS2 Galactic, colcon, `~/uavrt_ws`, the MathWorks `ros2node` bug workaround, remote-deploy credentials). Replace with the rPi build path that is actually used:
      add `matlab-coder-utils/c-udp` to the MATLAB path → run `uavrt_detection_codegen_no_ros_script.m` → `git add .` → `make`.
- [ ] Document the runtime contract that survives: config file format, UDP data port in, pulse UDP port out, threshold cache path.
- [ ] Keep the `airspy_rx` / `csdr-uavrt` / `airspy_channelize` prerequisites — **the Mini chain stays.**

**Verification:** `grep -rniE "galactic|colcon|uavrt_ws|ros2node" README.md` returns nothing. No code changed, so no codegen and no behavioral risk.

**Note:** `uavrt_detection_codegenerator.m` contains a hardcoded lab IP and username. Its removal is a small security tidy as well as a cleanup.

---

## Task 3 — Remove `ros2enable` from the config plumbing (cross-repo)

**Two repos, one logical change. Do them in this order.**

**3a — RESOLVED (Claude, read-only, 2026-08-31).**
`DetectorConfig.m` parses config keys with an `if`/`elseif` chain (lines 166–200) that recognises only: `ID`, `channelCenterFreqMHz`, `ipData`, `portData`, `Fs`, `tagFreqMHz`, `tp`, `tip`, `tipu`, `tipj`, `K`, `opMode`, `excldFreqs`, `falseAlarmProb`, `dataRecordPath`, `logPath`, `startIndex`. There is **no trailing `else`** — unrecognised keys are silently ignored. `ros2enable`, `ipCntrl`, `portCntrl`, `processedOuputPath`, `startInRunState` and `timeStamp` are all already inert on the MATLAB side.

**Consequence: 3b and 3c are decoupled and can ship independently, in either order.** A version-skewed Pi is not a risk. This downgrades Task 3 from moderate risk to low.

**3b — `uavrt_detection` (Claude edits, Michael codegens).**
- [ ] Remove the `ros2enable` argument from `detectorsetting2configstr.m`'s signature and from its `sprintf` format string and argument list. Note the format string is long and positional — **count the arguments after editing.**
- [ ] Remove any `ros2enable` handling in `DetectorConfig.m`.

**3c — `MavlinkTagController2` (Claude edits, no codegen).**
- [ ] Delete `TagDatabase.cpp:63` — `fprintf(fp, "ros2enable:\tfalse\n");`
- [ ] Rebuild: `make`

**Verification:**
- Generate a config with the controller, diff against a config generated before the change: the only difference is the absent `ros2enable` line.
- Run a detector against the new config; it must start and detect normally.
- Simulator run matches baseline.

**Risk:** low, following 3a. The change is cosmetic on both sides — the field is written but never read.

**Coordination — DEFERRED ACTION, DO NOT SEND YET.** `MavlinkTagController2` is Don's repo, so the `TagDatabase.cpp` change goes to him rather than being pushed directly. Michael will email Don himself.

> **Trigger:** once Tasks 1, 4 and 5 have landed and `uavrt_detection` is confirmed flying without ROS2, Claude drafts a short note (2–3 sentences) for Michael to email Don, explaining that ROS2 support has been stripped from the detector and asking him to drop the `ros2enable` line from `TagDatabase.cpp`. Do not draft or send this before that point — the field must stay until the detector side is proven.

---

## Task 4 — Vestigial code sweep

**Claude edits. Michael codegens.**

- [ ] `uavrt_detection.m` lines ~696–715: a large commented-out `formatPulseForTunnel` block, superseded by the controller's own tunnel formatting. Delete.
- [ ] Audit `coder.target('MATLAB')` branches (lines 29, 377) — confirm each is still meaningful for the MATLAB-vs-generated split, or remove.
- [ ] `msgdef/` — gitignored, contains `uavrt_interfaces_PulseStruct.m` and `builtin_interfaces_TimeStruct.m`, only meaningful for ROS2 codegen. Delete locally once Task 1 lands.
- [ ] Grep for other dead references: `grep -rniE "ros2|galactic|colcon|uavrt_ws" --include=*.m . | grep -v OLD_CODE`
- [ ] **Argument-guard wart:** `uavrt_detection.m:10` uses `if nargin == 0`, so calling with only `configPath` leaves `thresholdCachePath` undefined and errors at line 18. Change to `if nargin < 2` and default `thresholdCachePath = ""` independently. Harmless for codegen (the codegen script always supplies both args) and makes the function usable interactively — which is exactly how the regression harness calls it.

**Do not touch:** `OLD_CODE/` (deliberate archive, gitignored), `data_for_testing_detection_code/`, `post_processing_functions/`.

---

## Task 5 — Regenerate and commit

**Michael, in MATLAB.**

- [ ] MATLAB path: add `matlab-coder-utils/c-udp`. `no-ros-pulse-send` is no longer needed after Task 1.
- [ ] Delete `codegen/`
- [ ] Run `uavrt_detection_codegen_no_ros_script.m`
- [ ] `make` → confirm a clean `uavrt_detection` executable
- [ ] Commit regenerated `codegen/` as its own commit: `"Regenerate codegen after ROS2 removal"`
- [ ] Deploy to the Pi and fly, or at minimum run the full simulator chain on the Pi.

---

## Task 6 — Separate concern: the peel-loop `fprintf`

**Not part of ROS2 removal. Do not bundle.**

`waveform.m` contains `fprintf('Everything normal, p = %f \n', p)` inside the peeling loop, firing every iteration. On the Pi this is real cost in the detector hot path.

This should come out — **but only once the underlying anomaly is understood.** The guard was added because a flight produced more peaks than frequencies (index 151 vs bound 150) and the cause is still unknown. The right sequence is:

1. Keep the guard permanently. It is correct defensive code.
2. Instrument only the `else` branch, not every iteration.
3. Fly and collect logs to characterize when the anomaly fires.
4. Once understood, fix the root cause and reduce logging to the exception path.

Track this separately from the cleanup.

---

## Suggested Order and Batching

| Batch | Tasks | Cross-repo? | Risk |
|---|---|---|---|
| 1 | Task 0 baseline | no | none |
| 2 | Tasks 1 + 4 (source deletions), then Task 5 codegen | no | low |
| 3 | Task 2 (docs only) | no | none |
| 4 | Task 3 (config plumbing) | **yes — needs Don** | low (see 3a) |
| 5 | Task 6 (peel-loop, after flight data) | no | separate concern |

Batches 2 and 3 can proceed immediately and independently. Batch 4 should wait until Batch 2 is flying cleanly, so that if something breaks there is only one change in flight at a time.

---

## Resolved Decisions

1. **`uavrt_interfaces`** — already archived on GitHub (`dynamic-and-active-systems-lab/uavrt_interfaces`). No further action; the local clone stays for reference.
2. **`ros-pulse-send/`** — archive into `OLD_CODE/` before deleting from the repo (folded into Task 1).
3. **`TagDatabase.cpp` change** — Michael emails Don. Claude drafts the note, but **only once ROS2 removal is confirmed flying**. See the deferred-action box in Task 3.
