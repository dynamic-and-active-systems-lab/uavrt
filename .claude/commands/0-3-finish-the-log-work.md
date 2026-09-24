---
description: "Task 0-3 — chase the telemetry-lost-on-quit defect and finish everything else the log reorganization needs before its pull request"
model: opus
effort: high
---

Read first: `docs/WRITING_RULES.md`, then `docs/TASK_COMMS.md` including "Decisions already made"
and the task 0-1 and 0-2 entries.

## What this task is

The log reorganization is built and works, on TagTracker branch `telemetry-pairing`. Three things
stand between it and a pull request to Don Gagne. The first is a defect that would make the whole
feature do nothing in a case that will certainly happen.

Don's condition still governs everything here: **nothing outside `custom/` may change.** If the
only possible fix is upstream, that is a finding to write up, not a licence to patch.

You have a simulated aircraft. `tools/sim_rig.sh start` brings up PX4 SITL and the controller in
the Parallels VM; `status`, `stop` and `logs` do what they say. The vehicle must arm at some point
or QGroundControl saves no telemetry file at all, so take off before testing anything about
telemetry.

## 1. Telemetry lost when the app is quit rather than disconnected

Task 0-2 saw this once and did not find the cause. Quitting TagTracker with the simulated vehicle
armed saved no telemetry file, and none was recovered at the next start.

If that holds, an operator who quits at the end of a flight instead of pressing Disconnect loses
the telemetry file entirely, and the pairing this branch adds has nothing to pair. The feature
would fail silently in the case it exists for.

Reproduce it first and say how reliably. Then find the cause. The pieces to look at, all in
`src/` and therefore read-only to you:

- `MAVLinkProtocol::_stopLogging()` runs from `_vehicleCountChanged` when the last vehicle goes
  away. Quitting may never reach that path.
- `MAVLinkProtocol::_closeLogFile()` deletes the temp file when it is empty, and
  `_stopLogging()` deletes it when the vehicle never armed.
- `checkForLostLogFiles()` is supposed to recover a stranded temp file at the next start.
  `deleteTempLogFiles()` removes them all. Find out which of those runs on a quit and on the next
  launch, and in what order.

Then answer the question that decides what happens next: **can this be fixed from `custom/`?**
TagTracker's custom plugin can observe application shutdown and can see the vehicle list. If it
can force the same orderly path a Disconnect takes, before QGroundControl tears down, that is a
custom-side fix and you should build it. If the only real fix is in `src/`, do not write it.
Write up exactly what goes wrong, with the evidence from your reproduction, in a form Michael can
hand to Don as a separate question.

Either way, say plainly which of the two it turned out to be.

## 2. TagTracker's own README is now wrong

`README.md` lines 97 and 98 describe the pulse and rotation logs without mentioning that they now
live in a per-connection folder, and nothing there describes the sidecar. A reviewer reading that
file will not learn what this branch changed. Update it to match, in the same voice as the
surrounding text.

## 3. The WiFi log download drops folders into the same place

`README.md` line 102: the Download Logs (WiFi) action copies the companion computer's log folders,
named `Logs-<Type>-<timestamp>/`, into the same log save path that now holds the per-connection
folders. Two things to check and report on.

Whether the pairing pass walks into those folders and does anything it should not. It should
ignore anything it did not create.

Whether the two naming schemes can be told apart by a person looking at the directory, and whether
that is good enough or whether it now reads as a mess.

## How you know it worked

For item 1, a reproduction you can run twice with the same result, and either a fix that survives
the same test or a written explanation of why it cannot be fixed under Don's rule.

For items 2 and 3, the README reads correctly and the pairing pass demonstrably ignores a
`Logs-*` folder. Add a test for that if one is cheap.

Run the existing tests. They all passed at the end of task 0-1 and must still.

## Rules

Nothing outside `custom/` changes. `TagTracker/custom/tunnel-protocol/` is an untracked separate
clone in the working tree; never let it into a commit. Stage files by name, never `git add -A`.

Work on the existing `telemetry-pairing` branch. Do not push and do not open the pull request.

## When you finish

Append an entry to the top of "Open" in `docs/TASK_COMMS.md` with your commit hashes, saying
clearly whether the quit defect is fixed, unfixable under Don's rule, or not reproducible. Then
report to Michael in chat ending with what he needs to do.
