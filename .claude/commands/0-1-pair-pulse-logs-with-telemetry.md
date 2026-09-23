---
description: "Task 0-1 — TagTracker: put each flight's pulse logs and its telemetry file in one folder. Custom plugin only. Own branch, own PR to Don."
model: opus
effort: high
---

Read first: `docs/WRITING_RULES.md`, then `docs/TASK_COMMS.md` including "Decisions already made".

## Vocabulary, used consistently below

- **Flight telemetry recording** — the `.tlog` QGroundControl writes. Starts at the first
  heartbeat after a vehicle connects, ends when the last vehicle disappears.
- **Pulse detection run** — one press of start detection to one press of stop. Produces one
  `Pulse-*.csv`. A flight telemetry recording can contain several of them.

## What this task is

Today there is no way to tell which telemetry file belongs to which pulse log. This fixes that
by putting them in one folder. Michael has to copy one folder to his computer instead of hunting
through two, and post-flight analysis stops guessing.

Don Gagne agreed to this on 2026-09-23 with one hard condition, and it shapes everything:

**Nothing outside `custom/` may change.** He has spent real effort removing patches to upstream
QGroundControl from TagTracker so it can follow new QGC releases, has one left, and wants it
gone. Do not touch `src/`. Do not add a getter to `MAVLinkProtocol`. Do not change how telemetry
files are named or where QGroundControl puts them. If you believe the task cannot be done under
that rule, stop and report `Blocked` rather than patching upstream.

Start a new branch from `master`, not from `field-review`:

```
cd TagTracker
git checkout master
git checkout -b telemetry-pairing
```

The two branches must stay independent so Don can take either pull request without the other.
Nothing in this task may touch `custom/src/FieldReview/`.

## What is true today

Read from the code on 2026-09-22. Confirm it still holds before changing anything.

- `MAVLinkProtocol::_startLogging()` opens a temp file with a random name in the system temp
  directory on the first heartbeat, and appends every MAVLink message to it as it arrives. The
  data is written continuously through the flight.
- `MAVLinkProtocol::_stopLogging()` runs when the last vehicle disappears
  (`_vehicleCountChanged`) or on a write error. Only then is the temp file copied into
  `telemetrySavePath()`, under a name built from the time it stopped.
- Saving is skipped, and the temp file deleted, unless the vehicle armed at some point or
  `telemetrySaveNotArmed` is set, and unless `telemetrySave` is set.
- `checkForLostLogFiles()` recovers temp files stranded by a crash on the next app start.
- `CSVLogManager::csvStartFullPulseLog()` is called from `StartDetectionState` and writes
  `Pulse-<now>.csv` straight into `logSavePath()`. `csvStopFullPulseLog()` is called from
  `StopDetectionState` and from `CustomPlugin`.
- Rotation logs are `Rotation-<N>.csv`, numbered from one. `CustomPlugin::init()` calls
  `csvClearPrevRotationLogs()`, which deletes every `Rotation-*.csv` in `logSavePath()`.
- A `.tlog` is a sequence of records, each starting with a 64-bit big-endian microsecond
  timestamp. `src/Comms/LogReplayLink.cc` line 319 does exactly this read. So a telemetry file's
  start time is its first eight bytes, which is how custom code can learn it without asking
  QGroundControl anything.

## What to build

All of it in `custom/src/`.

1. **Create the folder at the start, not the end.** When `csvStartFullPulseLog` runs and no
   folder is open for this connection, create `logSavePath()/<that pulse log's timestamp>/` and
   remember it. Every pulse and rotation log until the vehicle disconnects goes in it. Forget it
   on disconnect so the next connection starts a new folder.

   The folder must exist from the first pulse log onward. Someone offloading before disconnecting
   has to find organized files, not loose ones.

2. **Write a JSON sidecar beside each pulse log**, same name with a `.json` extension. It holds
   that pulse detection run's start and stop times in UTC, the vehicle id, the app version, and
   the telemetry filename. Write it when the run starts, complete it when the run stops, and fill
   the telemetry filename later, in step 3.

   Do not change the pulse CSV format. Four header variants are already in the wild and every
   reader parses positionally around them, which is why this is a separate file.

3. **Coalesce when the telemetry file exists.** On vehicle disconnect, find the telemetry file in
   `telemetrySavePath()` that covers this connection, copy it into the folder, and write its name
   into the sidecars there. The original stays where QGroundControl put it; this is a copy.

   Match by content, not by filename. The file's name is its stop time, but its start time is its
   first eight bytes. A telemetry file belongs to this folder when its time span contains the
   pulse detection runs in it.

   Run the same step at app start, so a crash or a force quit leaves a folder that gets completed
   rather than orphaned. Add a manual action that runs it on demand; Don suggested one.

## Decide these, and say what you chose

- `csvClearPrevRotationLogs` deletes `Rotation-*.csv` from `logSavePath()`. With per-connection
  folders that glob no longer matches anything. Decide what it should do now and why. Deleting
  rotation logs from every previous folder is almost certainly wrong.
- What happens when detection starts with no vehicle connected. There is no telemetry recording,
  so the folder is named from the pulse log as usual and no telemetry file will ever arrive.
- What happens when two telemetry files could match one folder.

## Cases it must survive

Detection started after takeoff, stopped and restarted in flight, or stopped before landing:
each run is its own pulse log and sidecar in the same folder. A ground test where the vehicle
never arms: QGroundControl deletes the telemetry file, so the sidecar's telemetry field must stay
empty rather than naming a file that is gone. Two flights on one connection, such as a battery
swap: one folder, one telemetry file, which is honest because there was one recording. Offloading
mid-flight: the folder holds the pulse logs and sidecars, and the telemetry file simply is not
there yet.

## How you know it worked

Add tests to `custom/test/`, registered with `add_qgc_test` the way `OperationProgressTest` is.
The build recipe is in `docs/TASK_COMMS.md`.

Then run TagTracker against the simulator: connect, start and stop detection twice, disconnect,
and confirm one folder holds two pulse logs, two sidecars and one telemetry file, with each
sidecar naming that file and carrying its own window. Check the folder and both pulse logs exist
before the disconnect, not only after.

## Rules

`TagTracker/custom/tunnel-protocol/` is an untracked separate clone inside the working tree.
Never let it into a commit. Stage files by name, never `git add -A`.

Do not push and do not open the pull request.

Keep the sidecar work and the coalescing work in separate commits.

## When you finish

Append an entry to the top of "Open" in `docs/TASK_COMMS.md` with your commit hashes, then report
to Michael in chat ending with what he needs to do.
