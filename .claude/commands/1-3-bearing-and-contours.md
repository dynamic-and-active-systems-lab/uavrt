---
description: "Task 1-3 — field review C++ core: the bearing estimate and contour lines"
model: sonnet
effort: medium
---

Read these first, in this order:

1. `docs/WRITING_RULES.md` — how to write anything a person will read.
2. `docs/TASK_COMMS.md`, "Decisions already made".
3. `uavrt_postflight/python/analysis.py`, and the "Bearing estimate" section of
   `uavrt_postflight/CLAUDE.md`, which explains what the three numbers mean and records a
   claim about the method that turned out to be false.

## What this task is

Two smaller pieces of the field review, both working on a grid of signal strengths that
already exists. Do not build the grid; a later task does that. Use the same plain grid
structure task 1-2 defined.

Work in `custom/src/FieldReview/` on branch `field-review` in `TagTracker/`. Plain C++17,
no Qt types, no QGroundControl types.

## What to build

**The bearing.** Port `estimate_bearing`. The slope of the interpolated signal surface
points uphill, which is roughly toward the transmitter, and the estimate is the
magnitude-weighted circular mean of the slope directions across every cell inside the
flown area. It returns three numbers: a bearing in compass degrees where zero is north
and angles increase clockwise, a confidence between zero and one which is the length of
the resultant vector, and a spread in degrees which is the circular standard deviation.

Read `uavrt_postflight/CLAUDE.md` on this before porting. The weighting does not change
the direction, and an earlier version of that file claimed it did. What the circular form
adds is the confidence number.

**Contour lines.** Port `contour_levels` and `contour_polylines`. These produce the
contour lines as plain lists of coordinates for a map to draw, not a plot. Lines must
stop at the edge of the flown area rather than being drawn across it. The Python uses the
`contourpy` library; in C++ write marching squares directly, which is about a hundred
lines for this case.

## How you know it worked

The Python test file `uavrt_postflight/python/test_fieldreview.py` has the cases that
were thought worth testing for both. Port them.

The bearing has exact answers on synthetic fields: a clean linear slope at each of eight
compass bearings, and a point-source field whose true bearing is 45 degrees, where the
estimate should read 45.00. Confidence should collapse toward zero as noise rises.

On the Cumbria log `2025-11-21-Cumbria-Day5-Fri/HERELINK_LOGS/Pulse-2025-11-21-11-08-41-149.csv`,
tag 42, confirmed only, default trimming, the Python reports a bearing of **174 degrees**
with confidence **0.43** and spread **75 degrees**. As in task 1-2, get the grid by
exporting it from the Python rather than rebuilding it, so both sides see the same
surface.

For the contours, compare the number of lines per level and the total length of each
level's lines against the Python, rather than point-by-point equality: marching squares
and `contourpy` may order and split lines differently while tracing the same curve. Say
in your report which comparison you used.

## Rules

Nothing in `custom/src/FieldReview/` may include a Qt or QGroundControl header.

`TagTracker/custom/tunnel-protocol/` is a separate clone sitting untracked inside the
working tree. Never let it into a commit. Stage files by name, never `git add -A`.

Do not push. Add your files to `CUSTOM_SOURCES` in `custom/CMakeLists.txt` and your tests
to the test target task 1-1 created.

## When you finish

Append an entry to the top of "Open" in `docs/TASK_COMMS.md` with your commit hash. Then
report to Michael in chat, ending with what he needs to do.
