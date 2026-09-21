---
description: "Task 1-2 — field review C++ core: strongest-signal position, other lobes, and the signal floor"
model: opus
---

Read these first, in this order:

1. `docs/WRITING_RULES.md` — how to write anything a person will read.
2. `docs/TASK_COMMS.md`, especially "Decisions already made". Two of them are about this
   task and getting either wrong wastes the work.
3. `docs/FIELD_REVIEW.md` sections 3 and 6b — what the strongest-signal position and the
   signal floor are for, and what the floor measured on real flights.
4. `uavrt_postflight/python/analysis.py` — the code you are porting.

## What this task is

The field review reports where a tagged animal's signal was strongest during a flight,
and lets the operator hide weak signal so the strong area stands out on the map. This
task ports both of those from the validated Python prototype into C++ inside TagTracker.

Everything here works on a surface that already exists: a rectangular grid of signal
strengths in decibels, with cells outside the flown area marked as missing. The code that
builds that grid from the pulses is a separate, later task, so define a small plain
structure for a grid (values, width, height, cell size in meters, and the east and north
coordinate of each row and column) and write against it. Do not build the grid here.

Work in `custom/src/FieldReview/`, alongside `PulseLog` and `Geodesy` on branch
`field-review` in `TagTracker/`. Read those two files first for the house style: plain
C++17, no Qt types, no QGroundControl types.

## What to build

`custom/src/FieldReview/SurfaceAnalysis.{h,cc}`, porting from `analysis.py`:

- `peak_prominence` — every local maximum on the surface, with how far each one stands
  above the saddle joining it to higher ground.
- `edge_distance` and the `on_edge` flag — how close a maximum is to the edge of the
  flown area. A strongest signal within two cells of the edge means the survey ran out
  while the signal was still rising, and the operator should be told to fly further that
  way.
- `find_peaks` — the strongest position plus any other lobes worth reporting. The rule is
  a 10 dB window, 2 dB of prominence, at most three. Those numbers were chosen by a sweep
  against real flights and are not to be re-tuned here.
- `signal_floor` and `apply_floor` — the floor. Read the decision about it in
  `docs/TASK_COMMS.md` before writing a line. It returns a set of flags saying which
  cells pass, and it must never modify the surface.

## The bug you are being asked to fix on the way

Some pulse logs carry infinite signal strength: the 2023 NAVHDA log has 70 such rows out
of 1154, and the reader passes them through unchanged. If the strongest value on a
surface is infinite, the floor's cutoff is infinity minus ten, which is still infinity,
and the peak finder reports infinity as the strongest signal. Neither language guards
this today.

Decide what the right behavior is, implement it in the C++, and say in your report what
you chose and why. Then file an entry in `docs/TASK_COMMS.md` asking the planning session
to make the Python match, because the two must not diverge.

## How you know it worked

Port the synthetic surfaces from `uavrt_postflight/python/test_fieldreview.py` — the
two-lobe surface built by `two_lobes()` and the cases in `test_peaks` and `test_floor` —
and assert the same results in C++. On Michael's Mac the Python virtual environment in
`uavrt_postflight/python/.venv` works, so you can run the Python side directly to
generate expected values rather than copying them from the file.

Then check against a real flight. On the Cumbria log
`2025-11-21-Cumbria-Day5-Fri/HERELINK_LOGS/Pulse-2025-11-21-11-08-41-149.csv`, tag 42,
confirmed only, default trimming, the Python reports:

- strongest signal at **54.32736, -2.96657**, at **66.3 dB**
- surface median **35.2 dB**, so a contrast of **31.0 dB**
- one lobe only, not on the edge, not flagged weak
- at a 10 dB floor: cutoff **56.3 dB**, **4%** of the flown surface passes, **8507 m²**

Building that surface needs the grid code this task does not write. Get the grid by
running the Python and exporting the grid values to a file your test reads, so the
comparison is against the same surface rather than one you reconstructed. If you cannot
make that work, say so and report `Partial`; do not skip the real-flight check silently.

The test that matters most: the strongest position and the value must be identical at
floors of 3, 6, 10, 20 and 30 dB and with the floor off. If they are not, the floor is
touching the surface and the implementation is wrong.

## Rules

Nothing in `custom/src/FieldReview/` may include a Qt or QGroundControl header.

`TagTracker/custom/tunnel-protocol/` is a separate clone sitting untracked inside the
working tree. Never let it into a commit. Stage files by name, never `git add -A`.

Do not push. Add your files to `CUSTOM_SOURCES` in `custom/CMakeLists.txt` and your tests
to the test target task 1-1 created.

## When you finish

Append an entry to the top of "Open" in `docs/TASK_COMMS.md` with your commit hash,
including the ask about the infinite signal values. Then report to Michael in chat,
ending with what he needs to do.
