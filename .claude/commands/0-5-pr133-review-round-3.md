---
description: "Task 0-5 — rebase telemetry-pairing onto Don's new master and fix six items from the third review of pull request #133"
model: opus
effort: high
---

Read first: `docs/WRITING_RULES.md`, then `docs/TASK_COMMS.md` including "Decisions already made".

## What this task is

Pull request #133 to Don Gagne's TagTracker is the `telemetry-pairing` branch: one log folder per
vehicle connection, a JSON sidecar beside each pulse log, and the flight's telemetry file (`.tlog`)
copied into the folder. It has been through two rounds of review already. The branch is at
`71bb49512`, which is also on Michael's fork as `lab/telemetry-pairing`.

Don reviewed it on 2026-10-04 (six numbered findings) and Copilot reviewed it the same day (two
findings). The planning session checked each one against the code. This task does the fixes.

Michael's decisions for this round:

- **Keep the existing commits.** Do not squash. Each fix goes in as a new commit on top.
- **Fix items 1, 2, 3, 5, 7 and 8. Do not fix 4 or 6.** The reasons are below so you can write
  the replies.

Don's rule still holds: **nothing outside `custom/` changes.**

## Step 0. Rebase onto Don's new master

Don's master moved to `093c56c7e` (about 400 files changed, including an upstream QGroundControl
merge). Item 2 needs a hook that only exists there. Don says the branch merges cleanly.

```
git fetch origin
git rebase origin/master
```

Then build `macOS-debug` (expect a long rebuild) and run the custom suites before changing
anything, so you know the starting point:

```
ctest --preset macOS-debug -R 'TelemetryPairing|PulseLogFolder|TunnelProtocolText|OperationProgress|TagTrackerPulseDisplay' --output-on-failure
```

If the rebase conflicts or a suite fails at this point, stop and report. Do not fix master.

## The items to fix

Numbers are the review numbers Michael and the planning session use. Keep them.

### 1. Pulses stop being logged after a disconnect and reconnect (Don, medium)

The last round made closing a connection's folder also close any open pulse and rotation logs.
That was right, but in survey detection mode nothing opens a new pulse log afterwards. The
controller on the Pi keeps detecting, pulses keep arriving, the screen still says Detecting, and
`CSVLogManager::csvLogPulse` drops every pulse because no file is open. Nothing tells the operator.
On master the old log stayed open, so this is a regression this branch introduced.

The same gap causes a separate bug Michael has already emailed Don about: if the reply to Start
Detection is lost (the Pi was slow), TagTracker reports a failure and never opens the pulse log,
but the Pi starts detecting anyway. Pulses show on screen and none are saved. One fix covers both.

**Fix.** In the controller heartbeat handler in `CustomPlugin.cc` (around the
`_controllerStatus != heartbeat.status` block), check on **every** heartbeat, not only when the
status changes, because after a reconnect the status stays Detecting throughout. If the mode is
survey detection (not a Python mode), the controller status is Detecting, a vehicle is connected,
and no full pulse log is open, open one with `csvStartFullPulseLog()` and show one message, for
example: "Detection is running but pulse logging had stopped. A new pulse log has started." Add a
small `CSVLogManager` accessor for whether the full pulse log is open.

**Watch for a race.** During a normal Start Detection, a heartbeat saying Detecting can arrive
before the reply to the start command. The heartbeat check would then open the log first, and the
start state machine's `_startPulseLogging` would hit "Unable to open full pulse csv log file -
csvFile already open". Make that path quietly accept an already-open log, or make the heartbeat
check stand back while a start is in progress. Your choice; say which and why.

**Prove it.** Reproduce the bug on the simulated aircraft first (`tools/sim_rig.sh start`): set
Detection Flight Mode to Survey Detection, start detection, press Disconnect in TagTracker, let it
reconnect, and show that pulses arrive but no new pulse log appears. Then show the fix: a second
folder with its own pulse log and sidecar, and pulses written to it. Add an automated test if one
is practical with the mock link; if it is not, say why in the report.

### 2. Startup pairing depends on timing (Don, low)

`CustomPlugin::init()` runs the startup pairing pass through `QTimer::singleShot(0, ...)`, which
relies on QGroundControl having recovered any stranded telemetry file
(`checkForLostLogFiles()`) before the event loop runs. That holds today but nothing guarantees it.
New master calls `QGCCorePlugin::linkConfigurationsLoaded` right after `checkForLostLogFiles()`,
and `CustomPlugin` already overrides it. **Move the startup pass into that override**, after the
existing body, keeping its two skip conditions (unit tests, persistence disabled).

### 3. QSaveFile without direct-write fallback (Don, low)

Some storage cannot rename files, possibly Android removable media. QSaveFile then fails, so a
sidecar is never written (the folder is never paired) and the telemetry copy fails at every
disconnect. QGroundControl turns the fallback on for its own telemetry save
(`src/Comms/MAVLinkProtocol.cc` around line 450). **Call `setDirectWriteFallback(true)`** on the
QSaveFile in `PulseLogSidecar::write` and in `copyInto` in `TelemetryPairing.cc`.

### 5. Identical copies paired under the later name (Don, nit)

When several byte-identical telemetry files match, the first in sorted order wins, so
`flight.1.tlog` (QGroundControl's name for a second save in the same second) beats `flight.tlog`.
**Prefer the shortest name, then alphabetical.** Update `_duplicateCopiesPairWithFirstName` (and
its name) to expect `flight.tlog`.

### 7. Avoid scanning the working directory when telemetry path is empty (Copilot, medium)

`AppSettings::telemetrySavePath()` returns an empty string when the save location is unavailable,
and `QDir("")` is the process's working directory. Pairing could then pick up unrelated `.tlog`
files. The same applies to the log folder path in `pairAll` (around line 350). **Return no
candidates when the telemetry path is empty, and an empty summary when the log path is empty.**
Add a test.

### 8. Do not pair telemetry with runs lacking a vehicle (Copilot, medium)

A run made with no vehicle connected writes `"vehicle_id": null` in its sidecar, and pairing
ignores that and still matches by time. A telemetry file that ended within the one-second
tolerance could be attached to it. **Treat a folder whose sidecars all have a null vehicle ID as
`NoTelemetry` without looking at candidates.** Add a test.

## Not fixing, with the reason for the reply

- **4. Pairing does file work on the UI thread.** Real, already listed as a known limit in the PR
  description, and moving it to a worker thread is a larger change with its own risks. Reply that
  it is left for a follow-up pull request.
- **6. Header additions don't follow clang-format.** The repository's clang-format check runs as a
  pre-commit hook, not in CI (none of `.github/workflows` runs it), and the added lines match the
  hand alignment already in `CSVLogManager.h` and `CustomPlugin.h`. Reply that they are left
  matching the file.

## How you know it worked

- Build is clean. Warnings are errors in this project.
- The custom suites above pass, plus every test you add.
- Each new test fails without its fix. Check by reverting the fix locally or say how you know.
- Item 1 is shown on the simulated aircraft, before and after.
- Do not write "all tests pass". Say which suites ran.

Before reporting, review your own diff the way Don's `local-review` skill does: correctness,
cleanup of state, threading, failure paths, this repository's rules, tests. Fix what you find, or
list it if it is a judgement call.

## Rules

Nothing outside `custom/` changes. `TagTracker/custom/tunnel-protocol/` is an untracked separate
clone; never let it into a commit. Stage files by name, never `git add -A`.

Commits go on `telemetry-pairing`, one per item or a sensible grouping, each message naming the
item by its review title. End every commit message with:

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

**Do not push.** The rebase rewrote history, so the push needs
`git push --force-with-lease=telemetry-pairing:71bb49512 lab telemetry-pairing`. Michael runs it
after the planning session has read your commits.

## When you finish

Append an entry to the top of "Open" in `docs/TASK_COMMS.md` with your commit hashes and the
result of each item.

Include the PR replies, ready to paste, each starting with the reviewer's own title for the item,
for example "**Survey detection stops logging pulses after a vehicle disconnect and reconnect:**
Fixed in abc1234. ..." Don's six go in one comment answering by number. Copilot's two were listed
only in its review summary, so they have no threads; they go in a second comment.

Then report to Michael in chat, ending with what he needs to do.
