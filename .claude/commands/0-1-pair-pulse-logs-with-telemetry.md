---
description: "Task 0-1 — TagTracker: pair each pulse log with its telemetry file. Own branch, own PR to Don."
model: opus
effort: high
---

Read first: `docs/WRITING_RULES.md`, then `docs/TASK_COMMS.md` including "Decisions already made".

## What this task is

After a flight there is no way to tell which telemetry file belongs to which pulse log. This
closes that. It is foundational for the field review work but independent of it, and Michael
has asked Don Gagne about it separately.

**Do not build on the field review branch.** Start a new branch from `master`:

```
cd TagTracker
git checkout master
git checkout -b telemetry-pairing
```

`master` and `field-review` must stay independent so Don can take either pull request without
the other. Nothing in this task may touch `custom/src/FieldReview/`.

## What is true today

Established by reading the code on 2026-09-22. Confirm it still holds before you change anything.

- `MAVLinkProtocol::_startLogging()` opens a temp file with a random name on the first heartbeat
  or high-latency message. Recording is not tied to arming or to a flight.
- `MAVLinkProtocol::_stopLogging()` runs when the last vehicle disappears
  (`_vehicleCountChanged`) or on a write error.
- `_saveTelemetryLog()` then copies the temp file into `telemetrySavePath()` under a name built
  from `QDateTime::currentDateTime()`, which is the moment it stopped, not started.
- Saving is skipped unless the vehicle armed at some point or `telemetrySaveNotArmed` is set,
  and unless `telemetrySave` is set. On Android that setting also gates starting.
- `checkForLostLogFiles()` recovers temp files stranded by a crash on the next app start.
- `CSVLogManager::csvStartFullPulseLog()` is called from `StartDetectionState`, and writes
  `Pulse-<now>.csv` into `logSavePath()`. `csvStopFullPulseLog()` is called from
  `StopDetectionState` and from `CustomPlugin`.
- Rotation logs are `Rotation-<N>.csv`, numbered from one, and `CustomPlugin::init()` deletes
  every one of them at app start.

## What to build

1. Expose the recording start time from `MAVLinkProtocol`, and emit a signal when a telemetry
   file is saved carrying the temp path and the final path.
2. Name the saved telemetry file for the recording start time instead of the stop time.
3. Have `CSVLogManager` write pulse and rotation logs into `Logs/Session-<recording start>/`.
4. Copy the saved telemetry file into that session folder.
5. Write a JSON sidecar beside each pulse log holding its own start and stop times in UTC, the
   telemetry file name, the vehicle id and the app version.

Do not change the pulse CSV format. There are four header variants in the wild and every reader
parses positionally around them, so the sidecar is a separate file.

## Cases it must handle

Detection started after takeoff, stopped and restarted in flight, or stopped before landing:
each run is its own pulse log in the same session folder with its own window. Telemetry saving
disabled or the vehicle never armed: no telemetry file exists and the pulse logs still land in
the folder. A crash before disconnect: the recovered file must still be identifiable. Two
flights on one connection: one folder, which is honest, because there was one recording.

Decide what happens when pulse logging starts with no vehicle connected, so no recording session
exists. Say what you chose and why.

## How you know it worked

Add tests to `custom/test/`, registered with `add_qgc_test` the way `OperationProgressTest` is.
The build recipe is in `docs/TASK_COMMS.md`. Then run TagTracker against the simulator, start
and stop detection twice in one session, disconnect, and confirm one session folder holds two
pulse logs, two sidecars and one telemetry file with a start-time name.

## Rules

`TagTracker/custom/tunnel-protocol/` is an untracked separate clone inside the working tree.
Never let it into a commit. Stage files by name, never `git add -A`.

Do not push and do not open the pull request. Michael is talking to Don first.

Keep the changes to `MAVLinkProtocol` as small as you can and in their own commit, separate from
the `CSVLogManager` work, because upstream QGroundControl code is the part Don will look at
hardest.

## When you finish

Append an entry to the top of "Open" in `docs/TASK_COMMS.md` with your commit hashes, then
report to Michael in chat ending with what he needs to do.
