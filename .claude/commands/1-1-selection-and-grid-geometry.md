---
description: "Task 1-1 — field review C++ core: selection filters, flight window, grid spacing, build wiring and the test harness"
model: sonnet
---

Read these first, in this order:

1. `docs/WRITING_RULES.md` — how to write anything a person will read. It applies to
   your report, your commit messages and your comments.
2. `docs/TASK_COMMS.md` — in particular "Decisions already made". You know none of them.
3. `docs/FIELD_REVIEW.md` — the specification for the whole feature.
4. `uavrt_postflight/python/analysis.py` — the code you are porting.

## What this task is

The field review is a post-flight screen for the Herelink controller that tells the
operator where the signal from a tagged animal was strongest, so they know where to walk
next without carrying the log to a laptop. A Python prototype of it exists and has been
checked against flights where the tag position was known. This task begins porting that
prototype to C++ inside TagTracker.

Two pieces of the port are already committed, on branch `field-review` in `TagTracker/`,
commit 22cdcb460: `custom/src/FieldReview/PulseLog.{h,cc}` reads a pulse log, and
`Geodesy.{h,cc}` converts latitude and longitude to local east/north/up meters. Read them
before writing anything. They set the house style for this directory: plain C++17, no Qt
types, no QGroundControl types, one thing per file, and a comment at the top saying what
the file is and which Python file it was ported from.

## What to build

A new file pair `custom/src/FieldReview/FieldSelection.{h,cc}`, porting these from
`analysis.py`:

- `select_pulses` — filter by tag, by confirmed-only, by a time range, by an altitude
  range, and by a latitude/longitude box.
- `flight_window` — the rule that picks the flight proper out of a whole log by trimming
  the climb and the descent, using the median altitude. Read the docstring: it falls back
  to the whole log when the altitudes cannot support the judgment.
- `movmean` — the moving mean applied to the signal strengths before interpolation.
- `track_spacing` and `grid_spacing` — the rule that chooses a grid cell size from the
  data: half the median pulse spacing, held between 60 and 300 cells across the longer
  side, with a floor of 1 meter.

Keep the same behavior on the edge cases the Python handles, including empty selections,
all-equal altitudes and single-sample inputs. `uavrt_postflight/python/test_core.py` and
`test_fieldreview.py` show which cases were thought worth testing.

## Build wiring and tests

Add the four existing files and your two new ones to `CUSTOM_SOURCES` in
`custom/CMakeLists.txt`.

Add `custom/test/FieldReviewTest.{h,cc}` and register it with `add_qgc_test` the way
`OperationProgressTest` is registered in the same file. Put your unit tests there.

## How you know it worked

Run the Python prototype on the same inputs and compare. On Michael's Mac the virtual
environment in `uavrt_postflight/python/.venv` works and the flight logs are at the
default path the scripts already use, so no environment variables are needed.

Reproduce these exactly, from the Cumbria log
`2025-11-21-Cumbria-Day5-Fri/HERELINK_LOGS/Pulse-2025-11-21-11-08-41-149.csv`, tag 42,
confirmed pulses only, with the default trimming:

- the selection keeps **434 of 520** pulses for that tag
- the time window runs **0.9 to 11.8 minutes** from the first pulse in the log
- the grid spacing rule gives **5.0 m**, from a median pulse spacing of **10.0 m**
- the flown extent is **570 by 428 meters**, giving a **114 by 86** cell grid

If any of those differ, the port is wrong and the task is `Partial`, not `Done`. Do not
adjust the expected numbers to match your code.

## Rules

Nothing in `custom/src/FieldReview/` may include a Qt or QGroundControl header. That is
what lets this code be compiled and checked outside the app, and it is what makes the
pull request to Don Gagne reviewable as a self-contained unit.

`TagTracker/custom/tunnel-protocol/` is a separate clone sitting untracked inside the
working tree. Never let it into a commit. Stage files by name, never `git add -A`.

Work on branch `field-review` in `TagTracker/`. Do not push. Commit with the source
change and the build wiring in the same commit, and say in the message which comparison
you ran against the Python and what matched.

## When you finish

Append an entry to the top of "Open" in `docs/TASK_COMMS.md`, in the format that file
gives, with your commit hash. Then give Michael your report in chat, ending with what he
needs to do.
