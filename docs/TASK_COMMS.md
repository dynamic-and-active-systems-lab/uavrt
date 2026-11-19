# Task comms

The file the two Claude sessions use to talk to each other.

## Who is who

There are two sessions working on this project and they cannot see each other's
conversation.

The **planning session** is the one Michael talks to. It runs in Cowork, it writes the
plans and the task briefs, and it keeps the documents in `docs/`. It cannot build the
app, cannot push to GitHub, and works on the repository through a network mount that
makes large git commands slow.

A **task** is a single Claude Code run on Michael's Mac, started by a slash command such
as `/1-1`. Tasks do the code, the builds and the device work. Each one starts with no
memory of any other conversation, including this one.

Michael runs the tasks. He is not a message bus. Before this file existed, anything a
task wanted the planning session to know had to be read out of one window and retyped
into another, which is a copy a person should not be making.

## How to use it

**A task appends one entry to the top of "Open" at the end of every run.** Including a
task that has nothing to ask. Write "For the planning session: nothing" in those words,
because a missing entry looks exactly like a task that had nothing to say, and the
planning session will treat a missing entry as a finding rather than assume.

Entry format:

```
### Task 1-1 — 2026-09-21 — commit a1b2c3d — Done
**For the planning session**
1. ...
**For Michael**
1. ...
```

Status is `Done`, `Partial` or `Blocked`. `Partial` says which line it stopped at. The
commit hash matters: it is what lets the planning session read the change rather than a
description of the change.

**Tasks append only.** Never edit or delete an existing entry, and never write into
"Resolved". Both sessions share one working tree and one of them is usually mid-task.
Reading "Resolved" for context is fine.

**The planning session** moves an entry to "Resolved" once it has acted, adding a line
saying what it did and the date. It does not rewrite a task's words.

**Everything here is written in the plain English `docs/WRITING_RULES.md` requires.**
Never an identifier alone. Say what breaks for a person. Define any word this project
coined. Say the action you want, not the observation that prompted it: not "the infinite
signal values are a problem" but "add a guard for infinite signal values to task 1-2's
brief".

---

## Decisions already made

A fresh task knows none of this. Read it before writing code.

**The reported strongest-signal position is always the position of a real pulse.**
Michael decided on 2026-09-21 that the field review will not fit a curve to the pulse
data. The surface is interpolated linearly between pulses, and a linear surface has its
maximum at one of the data points, so the reported position steps from pulse to pulse as
the selection changes rather than sliding smoothly. That is accepted. Do not add a local
quadratic fit or any other curve. The reasoning is in `docs/FIELD_REVIEW.md` section 3.

**The signal floor is a mask, never a modified surface.** The floor is the control that
hides weak signal on the map: it sets a cutoff a chosen number of decibels below the
strongest reading in the current selection, and anything below it draws as background.
The routine that computes it returns a set of flags saying which cells pass, and the
caller keeps handing the untouched surface to the peak finder and the bearing. If the
floor were applied to the surface itself, the reported position would move whenever the
operator dragged the slider, and the one number the whole feature exists to produce
would stop being a property of the flight. A test in the Python prototype asserts the
position and the bearing are bit-identical from 3 to 30 dB. The C++ port must carry the
same test.

**`FIELD_REVIEW.md` section 7 is wrong about where the analyze page list comes from.**
It says `CustomPlugin` or `CustomOptions` in `custom/` supplies it. Neither does.
`analyzePages` is a virtual function on `QGCCorePlugin`, and the list is built in
`src/API/QGCCorePlugin.cc`. Adding the field review page means adding an override in
`CustomPlugin` that calls the base and appends to what it returns. The placement
conclusion in that section still holds: the page belongs in the analyze view, and the
analyze view is reachable on Android, because `src/Toolbar/SelectViewDropdown.qml` calls
`showAnalyzeTool()` on every platform.

**Some pulse logs carry infinite signal strength.** The 2023 NAVHDA log has 70 such rows
out of 1154. Both the Python reader and the C++ reader pass them through unchanged. An
infinite peak would make the floor's cutoff infinite too, and the peak finder would
report infinity as the strongest signal. Nothing guards this yet in either language.
Whichever task writes the peak finder fixes it in the C++ and files an entry here asking
the planning session to fix the Python to match.

**Work split.** The Python prototype in `uavrt_postflight/python/` belongs to the
planning session, which has the flight logs and a working Python environment. The
TagTracker C++, the QML and the build belong to tasks. Neither side edits the other's
files without an entry here saying so.

**A port is not finished until it has been checked against the Python.** The whole
justification for the C++ is that it produces the same answers as the Python prototype
that was validated against flights with known tag positions. Every porting task names
the specific logs and the specific numbers it must reproduce, and a task that cannot run
that comparison reports `Partial` rather than `Done`.

**13 tests fail on this Mac for reasons unrelated to any of our work.** Bluetooth timeouts,
serial, GPS and UDP socket tests, two interface view tests and two CMake coverage checks, mostly
tripping on a missing "Sans Serif" font in strict mode or on socket timing. The full suite is 374
of 387. They fail identically at the first commit of the `telemetry-pairing` branch, so nothing
we wrote causes them. Nobody has checked `master`, so the honest claim is "unchanged by this
branch", not "pre-existing". **Do not write "all tests pass" in a brief or a report.**

**PX4's clock inside the Parallels VM runs slow against the Mac's**, by about 16% over a
twenty-minute run. Lining PX4 flight log times up with TagTracker's requires calibrating against
a known shared event, such as a start-detection command, rather than trusting either clock.

**Quitting TagTracker while detection is running leaves the controller detecting.** The next Start
Detection after relaunch fails with "Start Tag Send failed. Controller in incorrect state" until a
Stop Detection is sent. Seen by task 0-3. Nothing we have written touches that code and nobody has
checked whether `master` behaves the same. It is Don Gagne's to fix, it matters to an operator who
restarts the app mid-flight, and it is not in scope for the telemetry pairing pull request.
Since task 0-5 the pulses from that still-running detection are logged (see the next entry), but
the next Start Detection still fails until a Stop Detection is sent.

**TagTracker starts a pulse log by itself when the controller is detecting and none is open.**
Built by task 0-5 for pull request #133, in response to Don's review. On every controller
heartbeat, in Survey Detection mode, with a vehicle connected, if the controller says it is
detecting and no pulse log is open, TagTracker opens one in the current connection's folder and
tells the operator. It covers three cases that used to lose every pulse without a word: a
disconnect and reconnect mid-detection, a lost reply to Start Detection, and TagTracker restarted
while the controller kept detecting. It stands aside while a Start Detection is in progress and
after a Stop Detection until the controller leaves detecting. Python (rotation) modes are not
affected.

**There is a simulated aircraft; use it before reaching for hardware.** Built by task 0-2 and
run from the Mac with `tools/sim_rig.sh start`, `status`, `stop` and `logs`. It brings up PX4
SITL and `MavlinkTagController2 --simulator` in the Parallels VM at 10.211.55.3, each in its
own tmux session so they outlive the ssh command. TagTracker on the Mac finds the vehicle through
its default UDP auto-connect on port 14550; no link needs configuring. The rig has its own
checkout and Python environment under `~/uavrt-rig` in the VM, deliberately separate from
Michael's `~/repos`.

Two things that will bite. The vehicle must arm at some point or QGroundControl saves no
telemetry file at all, because "save logs even if vehicle was not armed" is off; take off from
TagTracker or type `commander takeoff` in the PX4 shell. And macOS may re-ask whether TagTracker
can accept incoming connections after a rebuild; if the vehicle appears before you click Allow,
its startup requests are lost and TagTracker needs restarting.

Since 2026-10-05 the VM is on Parallels' shared network at 10.211.55.3 rather than bridged onto
the home network at 192.168.0.136. That address stays the same whichever network the Mac is on.
The VM's firewall allows ssh from `10.211.55.0/24`, and the Mac's `~/.ssh/config` entry
`uavrt-vm` points there. The rig's controller checkout in the VM is at `1f80697`, built against
tunnel protocol version 7.

Stop the rig when you are done with it. PX4 writes about 700 MB of flight log an hour even when
nothing is happening; overnight it filled the VM's disk to 96%. The rig keeps only the newest ten
PX4 logs each time it starts, but ten long runs can still be several gigabytes. To clear them:
`ssh uavrt-vm 'find ~/uavrt-rig/px4/log -name "*.ulg" -delete'`.

The controller once crashed as the rig started, with `std::system_error: Invalid argument` before
it opened its socket. Starting the rig again worked. Not investigated; if it recurs, note it here.

**ssh keys on this Mac must be ECDSA P-256.** Its managed ssh policy, from Apple's security
compliance baseline in `/etc/ssh/crypto.conf`, accepts nothing else. An ed25519 key is loaded and
then never offered, which looks exactly like a wrong key. Task 0-2 lost time to this.

**Pulse logs now live one folder per vehicle connection.** Built by task 0-1 on branch
`telemetry-pairing`. The folder is `Logs/<first pulse log's timestamp>/` and holds every pulse
and rotation log from that connection, a `Pulse-<timestamp>.json` sidecar beside each pulse log,
and a copy of the flight telemetry file added when the vehicle disconnects. The sidecar carries
`sidecar_version`, `pulse_log`, `start_utc`, `stop_utc`, `vehicle_id`, `app_version` and
`telemetry_file`. Rotation numbering restarts per folder and rotation logs are no longer deleted
at app start. **Nothing will find pulse logs at the top of `Logs/` any more**, so the field
review's file picker has to look inside these folders. The Python prototype is unaffected because
it takes explicit paths.

**Don Gagne approved the telemetry pairing plan on 2026-09-23**, including Claude writing it.
Task 0-1 is cleared to run and to become its own pull request from branch `telemetry-pairing`.

**Don Gagne will not accept changes outside `custom/`.** Said on 2026-09-23, when Michael
proposed the telemetry pairing work. He has removed almost every patch TagTracker carried against
upstream QGroundControl, because they make it painful to follow new QGC releases, and he has one
left that he wants gone. Any task that finds itself wanting to edit `src/` should stop and report
`Blocked` instead. He is happy with anything in the custom plugin.

**Two words that were being used loosely, now fixed.** A *flight telemetry recording* is the
`.tlog` QGroundControl writes, from the first heartbeat after a vehicle connects until the last
vehicle disappears. A *pulse detection run* is one press of start detection to one press of stop,
producing one `Pulse-*.csv`. One recording can contain several runs. Do not write "session".

**A telemetry file's start time is its first eight bytes.** A `.tlog` is a sequence of records
each beginning with a 64-bit big-endian microsecond timestamp; `src/Comms/LogReplayLink.cc` line
319 reads exactly that. The file's name is its *stop* time, which is why pairing by filename
fails. Reading the start from the file is what lets custom code pair logs without asking
QGroundControl anything.

**The telemetry file is written continuously, but saved only at the end.** Every message is
appended to a temp file with a random name as it arrives. The named file in `Telemetry/` does not
exist until the last vehicle disconnects, so nothing can copy it before then.

**The field review does not need the telemetry file.** Every pulse row carries its own latitude,
longitude and altitude, so the map, the surface and the reported position come from the pulse log
alone. The telemetry file only adds the parts of the flight where no pulses were heard. A flight
review works with the vehicle still connected and the telemetry file not yet saved.

**Building and running TagTracker on the Mac.** Established 2026-09-22, and the project's
older build notes are wrong, so use this instead.

```
cd ~/Developer/uavrt/TagTracker
export QT_ROOT_DIR=~/Qt/6.11.1/macos
cmake --preset macOS-debug
cmake --build --preset macOS-debug
ctest --preset macOS-debug            # unit tests, debug builds only
open build/macOS-debug/Debug/TagTracker.app
```

Four things that cost time to find. The build needs Qt 6.11.1 exactly: 6.11.0 is the
minimum and 6.11.1 the maximum, checked as a hard error. It needs Homebrew's pkgconf,
ccache, nasm, mold, just and create-dmg. It needs Python 3.10 or newer on the path, which
macOS does not supply, and it needs `uv` to build its own virtual environment under
`tools/.venv`; once that exists the Python path no longer matters. And there are two
bundles in the build directory: the runnable one is under `Debug/`, while the one at the
top level holds only QML files and will not launch.

GStreamer must stay enabled. Turning it off compiles out the body of the GStreamer test
but not its declarations, so the link fails on missing test symbols. CMake downloads
GStreamer itself and no separate install is needed.

`docs/FIELD_REVIEW.md` section 7 and `docs/SOFTWARE_CONTEXT.md` section 8 both describe an
older build: Qt 6.6.3, Android minimum SDK 25, a `herelink-linux.yml` workflow, and two git
submodules. None of that is true now. Android minimum SDK is 28, which is Android 9, so
whether the Herelink can run a current build is an open question. Correct those documents
when you touch them.

**Bench testing on the real controller and drone, learned 2026-09-30 to 2026-10-01.** The
paragraphs below come from the first test of the `telemetry-pairing` build on the SIYI UniRC 7 Pro
handheld with the drone's Raspberry Pi 5 on the bench, unarmed.

**Installing an APK on the SIYI: use a thumb drive.** The SIYI's USB-C port is in video mode, so a
Mac sees no Android device over USB and `adb` finds nothing. Wireless debugging works only with the
SIYI and the Mac on the same Wi-Fi, and joining any Wi-Fi other than the SIYI's own drops its link
to the drone (192.168.144.x). What works: copy `TagTracker.apk` from
`TagTracker/build/Android/android-build/` to a thumb drive, plug it into the SIYI, open Files, tap
the APK and choose Update. If Android says "App not installed" or warns of a conflict, stop: never
uninstall, because that deletes the logs on the controller.

**Where TagTracker saves on Android depends on what is plugged in when it starts.** If a removable
drive (a USB thumb drive counts) is present at app start, everything goes to that drive.
Otherwise it goes to the app's own storage, `Android/data/com.thegagnes.tagtracker/files/TagTracker/`,
which the SIYI's Files app can open. If the drive is plugged in for one start and not the next,
a flight's files end up in two places and its folder is never paired, because pairing only looks in
the current location. In the field: keep a drive out of the SIYI, or turn on QGroundControl's
"don't save to SD card" setting. This is QGroundControl's behaviour, not ours.

**A bench test needs three settings.** Detection Flight Mode must be Survey Detection, or the
Start and Stop Detection actions do not appear and no pulse log is written (the default is Auto
Rotation). "Save logs even if vehicle was not armed" must be on to get a telemetry file without
arming. And wait about a minute after the controller bar turns green before Start Detection: a Pi
that is still starting may miss the reply, which before task 0-5 meant detection ran with nothing
logged.

**End a bench connection with `sudo poweroff` on the Pi, never by cutting its power.** Wait for
the Pi's green light to stop blinking, then power off the drone. Once, after its power was cut
while running, the next boot stopped in emergency mode with the root account locked. The cause was
never determined: a damaged file system is one possibility, but Don has never seen one in years of
testing, and a Pi repairs minor damage itself at boot. Pressing Enter at that screen let it carry
on booting, and it came up normally. If it recurs, run `journalctl -b -1 -p err` on the next good
boot to see what failed. If that ever fails,
add `fsck.mode=force fsck.repair=yes` to the end of the single line in `cmdline.txt` on the SD
card's boot partition, boot once, then take it out again.

**The Pi's clock cannot be trusted on the bench.** The Pi has no battery-backed clock, and without
internet it starts each boot from the last time it saved. Against the SIYI it was 2.5 minutes
ahead on one boot and 24 minutes behind on the next, after a hard power-off. The pulse logs'
`start_time_seconds` come from the Pi's clock. Telemetry pairing is unaffected, because it uses
only the SIYI's clock. The field review mostly is too, because each pulse row carries its own
position, but anything that lines pulse times up with the telemetry file must not trust the Pi's
clock. Don knows. A fix without a battery would be for the controller to set the Pi's clock from
the flight controller's GPS time.

**The SIYI's clock is set to UTC+8**, so folder and telemetry file names read about 15 hours ahead
of local Arizona time. The sidecars' times are UTC and correct.

**A Raspberry Pi 5 needs one extra line for the serial link to the flight controller.**
`setup/full_setup.sh` in MavlinkTagController2 leaves `/dev/serial0` pointing at the Pi 5's debug
connector (`ttyAMA10`) rather than the GPIO pins (`ttyAMA0`), so the controller never hears the
flight controller and TagTracker's controller bar stays red. Adding `dtparam=uart0_console` to
`/boot/firmware/config.txt` fixes it; Michael's Pi has it, with a backup at
`config.txt.bak-serial0`. Don builds on a compute module, which does not hit this. Michael emailed
him on 2026-09-30.

**Pulse logs from before tunnel protocol version 7 contain heartbeat rows.** Older controllers
sent their keep-alive as a pulse message with `frequency_hz` of 0, and TagTracker logged those rows
like any other. `readpulsetable.py` in the Python prototype does not filter them out, so a field
review of an older flight would include them. The Python is the planning session's to fix. Logs
written since version 7 have none; the bench test confirmed it.

**Pull request #133 was bench-tested on the SIYI on 2026-10-12**, at TagTracker `3e70b266f`, by
Michael with the planning session checking the files. Results are posted on the pull request.
A normal run paired correctly. Force-closing TagTracker mid-detection and reopening it started a
new pulse log 12 seconds later, with the "pulse logging had stopped" message, and pulses kept
being written. The recording left unsaved by the force-close was recovered by QGroundControl at
the next start and paired by the startup pass in `linkConfigurationsLoaded`. Restarting and
pairing again copied nothing twice. The lost Start Detection reply was not reproduced: pressing
Start the moment the bar went green timed out, but the controller never started detecting.

**The Pair Telemetry Logs action was removed** on 2026-10-12, in `a99ff0aac`, at Michael's
request. Its name did not say what it did, and the same pass already runs at every disconnect and
every startup. Pairing is now automatic only. The two fly view QML files match Don's master again.

**On the SIYI, a log folder lasts one TagTracker session, not one battery.** The SIYI's link is
UDP, and QGroundControl keeps a UDP vehicle after its link drops, so powering the drone off and on
does not end the connection. Two runs on separate power-ups land in one folder, paired with one
telemetry file covering both. The folder only closes when TagTracker restarts.

**After TagTracker restarts mid-detection, the detection bars stay blank** until Start Detection
is pressed again, because Start Detection is what sets them up. Pulses are logged. Raised with Don
on pull request #133 as outside its scope.

**The Pi now keeps its system log across reboots** (set up 2026-10-12, `/var/log/journal`). If it
ever stops in emergency mode again, `journalctl -b -1 -p err` on the next good boot shows why.

**Copilot reviews of pull request #133 happen only when Don requests them.** Pushing a commit does
not trigger one, and nothing merges without Don. If the pull request goes quiet, ask him.

**Open question, not yet decided: how the triangulation gets into the build.** The
interpolated surface needs a Delaunay triangulation, which is the standard way of
joining scattered points into triangles so a value can be interpolated inside each one.
QGroundControl has none. The three options are fetching `delaunator-cpp` through CPM the
way the build already fetches its test libraries, vendoring that single header into
`custom/src/FieldReview/`, or writing the triangulation by hand. The planning session
recommends the first. Until Michael answers, no task should implement the surface.

---

## Open — waiting on the planning session

### From the hub session — 2026-11-03 — no commit — Done

The hub session is the Cowork conversation that set up this hub repository in early September
and did the first consolidation work. It is neither a task nor the planning session. Michael
asked it today whether its conversation was archived well enough for a fresh session to pick up.
Most of what it settled is already in these documents. Below are the pieces that are not, or
that have gone stale since.

**For the planning session**

1. Correct the tunnel protocol pin in the system reference. The tunnel protocol is the shared
   header, `TunnelProtocol.h`, that defines every message between TagTracker and the controller
   on the Pi. `docs/SOFTWARE_CONTEXT.md` says both builds pin it at `81ed30ac`, which is
   protocol version 5. That is several versions old. Michael's Pi notes of 2026-10-30
   (`pi5-troubleshooting.md`, untracked at the hub root) say both sides must now be on
   **version 9**, from 2026-10-24. The local git refs here have not been fetched since early
   October and still show version 7, so read the two pins from a fresh fetch, not from this
   entry.
2. Add to "Decisions already made" what a protocol version mismatch looks like, because it cost
   a day on 2026-09-30. TagTracker's controller box on the toolbar stays red, exactly as if no
   heartbeat were arriving, and TagTracker shows a one-line mismatch message once per app start.
   That day's cause was an Android build of TagTracker made just before Don's version 7 change,
   talking to a controller that had just been updated to version 7. The quick check is that one
   message, or comparing the two pinned commits.
3. Also add: the controller sends TagTracker nothing until it has heard a ground station's own
   heartbeat, and it accepts only ground station system ID 255
   (`MavlinkTagController2/controller/Connection.cpp`). A ground station whose heartbeat never
   reaches the Pi, or that uses another ID, gives the same red box as a mismatch. Worth knowing
   before the next radio change.
4. Correct the build section of the field review specification. `docs/FIELD_REVIEW.md`
   section 7 still says Qt 6.6.3 is required and that moving off it may break the Herelink.
   "Decisions already made" already records Qt 6.11.1 and asks for the older documents to be
   corrected; this one has not been.
5. Decide whether tasks may run MATLAB, and say which in `CLAUDE.md`. It lists running MATLAB as
   something the agent cannot do. That holds for the Cowork sessions but not for a task: MATLAB
   R2025a runs from the command line on Michael's Mac with `matlab -batch`, given the full path
   to MATLAB's `bin` folder. Michael ran it that way on 2026-09-01 and 2026-09-02 to check the
   bearing estimate. A task allowed to run MATLAB would no longer need to verify MATLAB maths by
   rewriting it in Python, which the current rule requires.
6. Nothing to act on in the hub session's handoff note of 2026-09-30,
   `_baseline/HANDOFF_protocol_v7_telemetry_pairing.md`. Tasks 0-2 to 0-5 and the bench-test
   notes in "Decisions already made" cover all of it.

7. Add the new `hardware/` folder at the hub root to the context documents table in `CLAUDE.md`.
   The folder itself was committed by the hub session on 2026-11-19, at Michael's request. Michael asked for it on
   2026-11-03 because hardware knowledge had lived only in individual sessions. It holds a page
   for his drone (`NAU_VHF_DRONE.md`, sections matching Don's page for his own aircraft, mostly
   blank so far), diagnosis guides (`field-notes.md`, starting with the four causes of a red
   controller bar), and Michael's Raspberry Pi 5 notes of 2026-10-30 to 11-02
   (`pi5-troubleshooting.md`). That last file replaces the older copy that was untracked at the
   hub root, which is now in `_baseline/`.
8. Decide which file is the home for facts about the Pi on the aircraft. Several are now in both
   "Decisions already made" and `hardware/`: the extra serial line a Pi 5 needs, ending a bench
   connection with `sudo poweroff`, and the Pi's system log being kept across reboots. Michael's
   newer notes say that last one should be switched off again after debugging, to cut writes to
   the card. Suggested split: `hardware/` holds the facts about the aircraft, and "Decisions
   already made" points to it.

9. *Added 2026-11-19, no action needed.* The hub session committed `hardware/noise-reduction/`
   (the noise measurements, derived data and the draft report, PDF and interactive HTML), the three
   scripts it uses in `tools/` (`noise_floor.py`, `bench_calibration.py`, `noise_report_data.py`), and
   a `__pycache__/` line in `.gitignore`, at Michael's request. Michael asked for the noise work to be archived in one place;
   `hardware/noise-reduction/README.md` is its index. The older `hardware/measurements/` folder is
   empty and was replaced by it.

**For Michael**

1. The documents now have one owner. That handoff note told the field review session that the
   hub session keeps the hub documents; the planning session has kept them ever since. From
   today the hub session does not edit `docs/` or `CLAUDE.md`. If it finds something, it writes
   an entry here, the way a task does. Say so if you want a different split.

### Task 0-5 — answered 2026-10-06 by the planning session

Read all six commits, and item 1's logic in detail, including that a failed Start Detection clears
its "start in progress" flag so the lost-reply case is covered too. Michael force-pushed to
`lab/telemetry-pairing` and posted both replies on pull request #133.

Your notes for the planning session:
1. The protocol version in the hub `CLAUDE.md` rule 5 now says `8f39f958`, version 7.
2. The VM network: Michael chose to keep the shared network. The VM's firewall now allows ssh from
   `10.211.55.0/24`, `tools/sim_rig.sh` uses 10.211.55.3 (hub commit f9d91d5), and `~/.ssh/config`
   was updated. `tools/sim_rig.sh status` works again. No `prlctl exec` fallback was added.
3. PX4's flight logs were deleted, 5.5 GB; the VM has 13 GB free. Recorded in the rig notes above.
4. The controller crash at rig start is recorded in the rig notes above.
5. Open: whether `README.md` should say a pulse log can now start at a reconnect. Not decided.
6. Open: disarming no longer stops detection after a reconnect, on master too. Michael will decide
   whether to raise it with Don once this review round settles.
7. Recorded in "Decisions already made", with a sentence added to the note about quitting
   mid-detection.

### Task 0-5 — 2026-10-05 — TagTracker commits 9d62ebd44, cb4e77d42, e6ccd73a7, 7baf11764, 3a1d0ae29, 3e70b266f — Done
The six review items Michael chose for pull request #133 are fixed, one commit each, on top of
`telemetry-pairing` rebased onto Don's master `093c56c7e`. The rebase had no conflicts. Nothing
outside `custom/` changed: 9 files, 232 insertions, 20 deletions. Not pushed.

| Item | Commit | Result |
|---|---|---|
| 1. Pulses stop being logged after disconnect and reconnect | 9d62ebd44 | Fixed, new test, shown on the simulated aircraft |
| 2. Startup pairing depends on timing | cb4e77d42 | Moved into `linkConfigurationsLoaded`; seen running there on the simulated aircraft |
| 3. QSaveFile without direct-write fallback | e6ccd73a7 | Fixed; no test (needs storage that cannot rename) |
| 5. Identical copies paired under the later name | 7baf11764 | Fixed; test renamed to `_duplicateCopiesPairWithShortestName` |
| 7. Empty telemetry or log path scans the working directory | 3a1d0ae29 | Fixed, new test |
| 8. Telemetry paired with runs that had no vehicle | 3e70b266f | Fixed, new test |

Items 4 and 6 are not fixed, as Michael decided; replies below. For item 6 I checked Don's new
master myself: no workflow under `.github/` runs clang-format or pre-commit.

**Item 1, how it works.** On every controller heartbeat, not only on a status change, TagTracker
checks: Survey Detection mode, controller Detecting, a vehicle connected, no full pulse log open.
If all hold, it opens a pulse log in the current connection's folder and shows "Detection is
running but pulse logging had stopped. A new pulse log has started." The same check covers
Michael's emailed bug (a lost reply to Start Detection) and a third case: TagTracker restarted
while the controller is still detecting now logs from the first heartbeat.

The race the brief warned about. I made the heartbeat check stand back rather than make the start
path accept an already-open log. Accepting the open log would avoid the error but still show the
operator "logging had stopped" during an ordinary start. Stop Detection has the mirror-image race:
it closes the log, then waits for the controller's reply, and a heartbeat still saying Detecting
would reopen it. So the check stands back while the Start Detection state machine runs, and after
a stop until the controller reports it has left Detecting. If the log cannot be opened, it does
not retry every heartbeat (one error message, not one every 5 seconds).

**Item 1 on the simulated aircraft**, with Michael clicking. There is no Disconnect button while
the link is healthy: QGroundControl shows it only beside "Comms Lost", and the auto-connected UDP
link is hidden from the Comm Links page. So I blocked PX4's packets to the Mac with a temporary
`iptables` rule in the VM, Michael pressed Disconnect, and the rule was lifted 3 seconds after
TagTracker logged the disconnect, so it reconnected through auto-connect.

- Unfixed build: 65 confirmed pulses before the disconnect, 65 rows in the pulse log. After the
  reconnect 28 confirmed pulses arrived, 0 were written, and no second folder appeared. The
  controller's simulator, decimator and detector were all still running.
- Fixed build, launched while the controller was still detecting: it opened a log 3 seconds after
  start (folder `2026-10-05-07-20-48-041`). After the same disconnect it opened a second folder,
  `2026-10-05-07-21-51-588`, 4 seconds after the vehicle came back, with its own pulse log
  (45 rows) and a sidecar naming vehicle 1. The first folder's sidecar got its stop time.
- A normal Stop then Start in the fixed build: nothing reopened the log in the 25 seconds after
  Stop, and Start opened exactly one log through its own state machine, with no "already open"
  error. Both replies came back within 0.2 s, so no heartbeat fell inside the windows the guards
  protect. The simulator shows the normal path unchanged; the guards themselves are verified by
  reading the code only.

The new automated test, `PulseLogFolderTest::_detectingHeartbeatResumesPulseLog`, feeds controller
heartbeats to the plugin with the mock vehicle: none in a Python mode, one log on a Detecting
heartbeat, no second log on the next, then disconnect, reconnect, and a new folder with its own
pulse log and sidecar. The start and stop guards have no automated test. Exercising them needs a
Stop Detection state machine retrying against a mock link that never answers, and the test
framework's strict warning check would make that brittle.

**Tests.** Ran the five custom suites (TelemetryPairing, PulseLogFolder, TunnelProtocolText,
OperationProgress, TagTrackerPulseDisplay): all five passed after the rebase and before any
change, and all five pass at the tip. Every one of the six commits was built and the five suites
run at it; see "per-commit check" below. Each new test fails without its fix, checked by reverting
the fix locally: `_detectingHeartbeatResumesPulseLog` with the heartbeat check removed,
`_duplicateCopiesPairWithShortestName`, `_emptyPathsDoNotScanWorkingDirectory` (each half
separately) and `_noVehicleRunIsNotPaired` with the old pairing code. The full suite was not run.
The build has no compiler warnings; the linker prints one upstream note about duplicate
libraries, unrelated to this branch.

Per-commit check: each of the six commits, checked out in order, built `macOS-debug` cleanly and
passed all five custom suites, so the history can be bisected.

**For the planning session**
1. Correct rule 5 of the hub `CLAUDE.md`. Both pins are now `8f39f958` (tunnel protocol version 7),
   not `81ed30ac`: TagTracker master in `custom/CMakeLists.txt` and MavlinkTagController2 `main`
   since its commit 6701d10. The rig in the VM was still built against `81ed30ac`, so I moved its
   checkout from d3f7830 to `1f80697` (current `main`, detached head as before) and rebuilt it.
2. The VM's network has changed, and `tools/sim_rig.sh` cannot reach it. It is now on Parallels'
   shared network at 10.211.55.3 (the Mac was on another network, 192.168.205.x), and its firewall
   admits ssh only from 192.168.0.0/24. I drove it with `prlctl exec` as the `parallels` user
   instead and changed no firewall rule. Add to the rig notes, and give Michael the choice: allow
   ssh from 10.211.55.0/24 in the VM, or put the VM back on bridged networking. A `prlctl exec`
   fallback in `sim_rig.sh` would make the rig independent of the network.
3. The VM disk is 96% full, 2.9 GB free. PX4's flight logs grew from 0.5 GB to 5.4 GB overnight
   while the rig sat idle. Add "stop the rig when done" to the rig notes, or have the rig trim
   PX4's logs at start.
4. The controller crashed once at rig start, `std::system_error: Invalid argument`, inside its
   simulator telemetry publisher before the socket bind. The second start worked, and running it by
   hand worked. Not investigated: gdb in the VM cannot produce a backtrace. Note it in the rig notes
   in case it recurs.
5. The branch's README says a full pulse log runs from Start Detection to Stop Detection. A resumed
   log now starts at a reconnect. The README is outside `custom/`, so I left it. Decide whether one
   sentence goes in with this round.
6. A judgement call for Michael and Don, not fixed: after a reconnect, disarming no longer stops
   detection, because Start Detection connected the disarm handler to the old vehicle object, which
   the disconnect destroyed. This is true on master too. The resume path could connect it to the new
   vehicle in one line. Worth asking Don whether he wants it in this pull request.
7. Add to "Decisions already made": TagTracker now resumes pulse logging whenever the controller is
   detecting in Survey Detection and no log is open. That changes what task 0-3's "controller left
   detecting after a quit" means for an operator: the pulses are now logged, but the next Start
   Detection still fails until a Stop is sent.

**For Michael**
1. Read the commits, then push with
   `git push --force-with-lease=telemetry-pairing:71bb49512 lab telemetry-pairing`.
2. Paste the two replies below into pull request #133.
3. Decide on the VM network (item 2 above). Until then `tools/sim_rig.sh` fails with "cannot ssh".

**Reply to Don (one comment):**

> Thanks, Don. Rebased onto 093c56c7e (no conflicts) and fixed on top, one commit per item.
>
> **1. Survey detection stops logging pulses after a vehicle disconnect and reconnect:** Fixed in
> 9d62ebd44. On every controller heartbeat, if the mode is Survey Detection, the controller says
> Detecting, a vehicle is connected and no pulse log is open, TagTracker opens one in the current
> connection's folder and shows "Detection is running but pulse logging had stopped. A new pulse
> log has started." It checks every heartbeat because the status stays Detecting across the
> reconnect. The same check covers a lost reply to Start Detection, and TagTracker restarted while
> the controller is detecting. It stands back while the Start Detection state machine runs, so an
> early Detecting heartbeat can't open the log ahead of `_startPulseLogging`. It also stands back
> after Stop Detection until the controller leaves Detecting, so a heartbeat sent before the stop
> lands can't reopen the log. New test: `PulseLogFolderTest::_detectingHeartbeatResumesPulseLog`.
> Also reproduced on PX4 SITL with the controller simulator: before the fix, 28 pulses after the
> reconnect and none written; after it, a second folder with its own pulse log and sidecar.
>
> **2. The startup pairing order depends on timing:** Fixed in cb4e77d42. The pass now runs at the
> end of `linkConfigurationsLoaded`, with the same skips for unit tests and disabled persistence.
>
> **3. `QSaveFile` is used without `setDirectWriteFallback(true)`:** Fixed in e6ccd73a7, for both
> the sidecar write and the telemetry copy.
>
> **4. Pairing does blocking file I/O on the UI thread:** Agreed. Moving it to a worker thread is a
> bigger change with its own risks, so I'd like to leave it for a follow-up pull request.
>
> **5. Identical duplicates are paired with the first name in sorted order:** Fixed in 7baf11764.
> Among identical copies it now takes the shortest name, then alphabetical. The test is now
> `_duplicateCopiesPairWithShortestName` and expects `flight.tlog`.
>
> **6. The hand-aligned header additions don't follow clang-format:** Left as they are. No workflow
> in `.github/workflows` runs clang-format; it runs only as a pre-commit hook. The added lines
> match the hand alignment already in `CSVLogManager.h` and `CustomPlugin.h`. Happy to reformat if
> you'd rather.

**Reply to Copilot's two findings (second comment):**

> Copilot's review summary listed two findings with no inline threads; both are fixed.
>
> **Avoid scanning the working directory when telemetry path is empty:** Fixed in 3a1d0ae29. An
> empty telemetry path gives no candidates, and an empty log path makes `pairAll` return an empty
> summary. Test: `_emptyPathsDoNotScanWorkingDirectory`.
>
> **Do not pair telemetry with runs lacking a vehicle:** Fixed in 3e70b266f. A folder whose sidecars
> all have a null `vehicle_id` is `NoTelemetry` without looking at candidates. Test:
> `_noVehicleRunIsNotPaired`.

### Task 0-4 — 2026-09-24 — hub commit 482802d — Done
A signed TagTracker APK for the SIYI UniRC 7 Pro is built and verified, at
`TagTracker/build/Android/android-build/TagTracker.apk`, 88 MB (92,081,770 bytes). It was built
from branch `telemetry-pairing` at 75658c055, so it contains the unmerged log folder work. It ran
on Android 9 and Android 13 emulators, and on both it made a per-connection log folder with a pulse
log, a sidecar and a copy of the flight telemetry file. The real controller was not connected, so
nothing was installed on it.

Checked on the APK itself with `aapt2` and `apksigner` from build tools 36.0.0: package
`com.thegagnes.tagtracker`, minimum SDK 28, target SDK 36, native libraries for `arm64-v8a` only,
and `apksigner verify` passes (APK Signature Scheme v3, one signer, certificate "CN=Don Gagne").
The keystore accepted `android` as its password, so it is signed with the committed debug key,
the same one Don's CI uses.

Versions have not moved: `.github/build-config.json` still pins Java 21, platform android-36,
build tools 36.0.0, NDK 27.2.12479018 and minimum SDK 28, and target SDK follows the platform, so
36. I installed NDK 27.2.12479018 (only 28.2 was present). Two pieces differ from CI in ways that
do not reach the APK: Java is Android Studio's bundled 21.0.10 rather than Temurin 21, and the
SDK command-line tools are version 22.0 rather than CI's pinned build 14742923.

`tools/android_apk.sh build` rebuilds it in one line: it reads the versions from the same config
file CI reads, stops if an installed piece does not match, builds, and runs the checks above.
`verify`, `install` and `path` do the parts separately. The keystore password is kept in the
Mac's login keychain as `uavrt-tagtracker-keystore`, and never in a file.

What the emulators showed. The *rig* is the simulated aircraft from task 0-2 (PX4 SITL and the
tag controller simulator in the Parallels VM). An emulator cannot hear the rig's broadcast, so
`tools/emulator_mav_relay.py` passes MAVLink between them. On each emulator I installed the APK,
connected to the rig, started survey detection, commanded a takeoff so the recording would be
kept, stopped detection, landed and pressed Disconnect.

- Android 9 (API 28, arm64, the APK's floor): installed and launched with no fatal error in
  `logcat`. The save folder is `/storage/emulated/0/TagTracker Daily/`, reached after the usual
  storage prompt. The run made `Logs/2026-09-24-21-57-04-616/` holding the pulse log (76 pulse
  rows from the simulated tag, signal-to-noise 36 to 48 dB) and its sidecar with `vehicle_id` 1 and start and
  stop times. At Disconnect the telemetry file was copied in, byte-identical to the one in
  `Telemetry/` (checked with `cmp`), and the sidecar named it.
- Android 13 (API 33, arm64, the controller's version): the first launch opens Android's "All
  files access" screen. I backed out without granting it, which is the harder case. The save
  folder is then `/storage/emulated/0/Android/data/com.thegagnes.tagtracker/files/TagTracker
  Daily/`, the app's own storage, which needs no permission. The same run gave the same result:
  folder, 48 pulse rows (45 to 48 dB), sidecar with start, stop and vehicle id, and a byte-identical telemetry
  copy named in the sidecar.

So scoped storage does not break the log reorganization on Android 13. The files, screenshots
of detection running, and the storage prompt are in `~/Documents/TagTracker task 0-4 emulator
output/`.

**For the planning session**
1. Add to "Decisions already made" where TagTracker saves on the controller: on Android 11 and
   newer, with no removable SD card, the whole `TagTracker Daily` folder lives in the app's own
   storage, `Android/data/com.thegagnes.tagtracker/files/`. Two consequences for Michael, neither
   tested here. Uninstalling the app deletes every log, because Android removes that folder with
   the app; `adb install -r` and upgrades keep it. And Android 13's own Files app usually cannot
   browse `Android/data`, so logs come off by USB file transfer to a computer or `adb pull`.
2. One case is untested and matters if the controller has a microSD card: if "All files access"
   is granted and a removable card is present, QGroundControl saves to the card's root instead.
   The emulator had no removable card. Worth checking on the real controller.
3. Add `tools/android_apk.sh` and `tools/emulator_mav_relay.py` to the "Testing without
   hardware" table in `CLAUDE.md` and wherever `docs/SOFTWARE_CONTEXT.md` lists build tools. I
   did not edit either.
4. Every TagTracker build from this tag gets Android version code 664300999, because the build
   clamps the development counter (3517 commits past v4.3.0) at 999 and warns "Cut a release tag
   to reset the counter". Reinstalling with `adb install -r` works; nothing will ever see a newer
   build as an upgrade by number. Don's concern, not ours, but worth one line to him.
5. Another Claude session, working on TriTrack, installed and launched `edu.nau.tritrack` on my
   Android 13 emulator mid-run, presumably because it was the only device `adb` could see. I left
   its app alone and the emulator (`uavrt_api33`) running. If two sessions will use emulators at
   once, the briefs should name the device with `adb -s`.

**For Michael**
1. To install on the controller once developer options and USB debugging are on and it is
   plugged in: `~/Developer/uavrt/tools/android_apk.sh install`. Without a cable, copy
   `TagTracker/build/Android/android-build/TagTracker.apk` onto it and open it with the
   controller's file manager.
2. At first launch the app opens "All files access". Leaving it off is fine unless you want
   logs on a microSD card (item 2 above).
3. To rebuild after pulling new TagTracker code: `~/Developer/uavrt/tools/android_apk.sh build`.

### Task 0-3 — answered 2026-09-24 by the planning session

The quit defect is not real, and the reasoning for what task 0-2 saw is good enough to act on.
Five tries by four routes all saved the telemetry file, and the mechanism explains why: every
graceful close ends in the same link shutdown the Disconnect button uses, waiting for the vehicle
list to empty before anything is torn down. A crash skips it and the next start recovers the
file, which task 0-1 had already shown.

The explanation for task 0-2's single observation is labelled as fitting the evidence rather than
proven, which is the right way to leave it. The firewall prompt delayed TagTracker's message
handling by roughly two minutes, and QGroundControl deletes a recording whose heartbeats never
showed the vehicle armed. It needs a firewall prompt after a rebuild, which a field machine does
not get. Not worth chasing further.

Items 1 and 3 are recorded above, along with item 2. Item 1 matters most: my own task 0-3 brief
told the task that all tests passed at the end of task 0-1, and that was wrong. The rule is now
written down.

Item 2, the controller left detecting after a quit, is Don's code and out of scope for this pull
request. Recorded above so it is not lost, and Michael can raise it separately.

**Cleared to push.** Four commits, 16 files, 1247 insertions. The only file outside `custom/` is
TagTracker's own `README.md`, which is the fork's documentation rather than upstream
QGroundControl source, so Don's rule is intact. Verified independently.

### Task 0-3 — 2026-09-23 — TagTracker commits d8e86b3e1, 75658c055 — Done
The quit defect is not reproducible, so there is nothing to fix and no question for Don.
Quitting TagTracker with the simulated vehicle armed saved the flight telemetry recording in
all five tries, by four routes: Cmd-Q pressed by Michael, a macOS quit command sent by
script, SIGTERM, and a quit after the simulated aircraft had already been shut down. Each
time the `.tlog` appeared in `Telemetry/` within two seconds of confirming the quit. In the
three tries that had pulse logs, it was also copied into the connection's log folder and
named in every sidecar, including one quit with detection still running. I watched the
temp and telemetry folders ten times a second and ran TagTracker with QGroundControl's
debug logging for the telemetry recorder, the vehicle list and the link manager.

Why a quit is safe. Every graceful way of closing the app ends in the same place. Cmd-Q,
the window's close button, SIGTERM and Ctrl-C all become a close of the main window, which
asks "There are still active connections to vehicles. Are you sure you want to exit?".
Answering Yes runs QGroundControl's link shutdown, which disconnects every link and waits
for the vehicle list to empty before anything is torn down. That is the same end of
recording the Disconnect button causes. A crash or force quit skips it, leaves the
temporary recording file behind, and the next start recovers it, as task 0-1 showed.

What task 0-2 saw is real (nothing from that connection is in `Telemetry/`), and the
likeliest reason is the macOS firewall prompt. Task 0-2's transcript and PX4's flight log
show that TagTracker started before Michael clicked Allow, all of its startup requests to
the vehicle timed out, and at 20:00:17 PX4 measured its round trip at 107 to 149 seconds.
It was handling the vehicle's messages about two minutes late. Takeoff was about 19:57:45
and the quit about 20:02:10. QGroundControl deletes a recording at the end if no
heartbeat in it showed the vehicle armed, which is its "only save armed flights" rule, and
with that backlog it may never have processed one sent after takeoff. That produces
exactly what was seen: no file saved and nothing left to recover. I did not reproduce the
backlog, so this is the explanation that fits the evidence, not a proven one. It needs a
firewall prompt after a rebuild, which a field laptop does not get.

The README now describes the per-connection folders, the sidecar and its fields, when the
telemetry file is copied in (disconnect or quit), the startup and on-demand pairing, and
adds Pair Telemetry Logs to the list of fly view actions. It is TagTracker's own
`README.md` at the repository root, outside `custom/`, which the brief asked for.

The WiFi log download does not confuse the pairing pass. The companion computer's folders
are `Logs-Detectors-`, `Logs-RawCapture-` and `Logs-Rotation-` followed by a timestamp, and
hold controller and detector logs, configs, IQ recordings and spectrogram CSVs. The pairing
pass acts only on a folder with `Pulse-*.json` sidecars at its top level and does not look
inside subfolders, so it passes over them. A new test builds a companion folder from the
same flight, with times inside the telemetry file's span, and checks that the real folder
is paired while every file in the companion folder keeps its name, size and modification
time.

The two naming schemes are easy to tell apart and harder to match up. TagTracker's folders
are a bare local-time stamp such as `2026-09-23-21-08-31-664`; the controller's carry the
`Logs-<type>-` prefix and a UTC stamp, one folder per detection run. So a run started at
21:08:31 local appears as `2026-09-23-21-08-31-664/` and `Logs-Detectors-2026-09-24_04-08-31/`,
seven hours and a date apart. That is good enough for this pull request, and the README now
says which is which. I would not rename TagTracker's folders now: the folder name matching
the first pulse log's name is recorded under "Decisions already made". If the mix bothers
anyone in the field, the cheap fix is on the download side and stays inside `custom/`:
put downloaded folders in a `Companion/` subfolder.

Tests: the two log-folder suites pass, now 5 and 9 cases. The full suite is 374 of 387
passing. The 13 failures are Bluetooth timeouts, serial, GPS and UDP socket tests, two
user-interface view tests and two CMake coverage checks. Most trip on a macOS warning
about a missing "Sans Serif" font in strict mode or on socket timing. The same 13 fail
identically on task 0-1's last commit, so this task did not cause them. I did not check
`master`, so I cannot say whether task 0-1's branch did.

**For the planning session**
1. Correct "all passed at the end of task 0-1" wherever it appears. On this Mac 13
   upstream tests fail at task 0-1's commit too; task 0-1 probably ran only its own suites.
2. Decide whether this deserves a brief: quitting TagTracker while detection is running
   leaves the controller detecting. The next Start Detection after relaunch failed with
   "Start Tag Send failed. Controller in incorrect state" until a Stop Detection was sent.
   This branch does not touch that code, and I did not check `master`. An operator who
   restarts TagTracker mid-flight would hit it.
3. Add to the rig notes under "Decisions already made": the PX4 flight log's clock in the
   VM runs slow against the Mac's, by about 16% over task 0-2's run, so PX4 message times
   must be calibrated against a known event (I used a start detection) before being lined
   up with TagTracker's.

**For Michael**
1. Push `telemetry-pairing` and open the pull request to Don. It now has four commits. Worth
   a line in the description: quitting with a vehicle connected was tested four ways and
   saves and pairs the telemetry file just as Disconnect does.
2. My simulator flights left three log folders and five telemetry files in `TagTracker
   Daily`. I moved them to `~/Documents/TagTracker task 0-3 simulator output/`; delete it
   when you like. Task 0-2's folder `2026-09-23-20-05-07-875` and its `20-12-56.tlog` are
   still in the real folders.
3. The TagTracker you quit at the start of this task had been holding a recording of an
   unarmed connection since 20:26; QGroundControl deleted it on quit, as it should. The rig
   is stopped.

### Task 0-2 — answered 2026-09-24 by the planning session

The rig works, and the click-through it did closes the one thing task 0-1 left open. Pair
Telemetry Logs reported "Telemetry copied into 0 log folder(s)" on a folder already paired at
disconnect, which is the correct message for that state and the only part of task 0-1 no person
had pressed. Task 0-1 is now fully exercised.

Items 1, 3 and 5 are done in this commit. `CLAUDE.md` rule 5 and `docs/SOFTWARE_CONTEXT.md` now
say the tunnel protocol is pinned through CPM in two CMake files rather than carried as a
submodule, and that the parity check is comparing those two `GIT_TAG` lines. The simulator preset
lists are corrected and separated into signal levels and scenarios. `tools/sim_rig.sh` is in the
testing table.

**A finding the report did not make, and it is the same disease as item 2.** Michael's own
`MavlinkTagController2` at `~/Developer/uavrt/MavlinkTagController2` is **47 commits behind
`origin/main`** and still carries the old submodule layout. `versions.yaml` records `verified:
4fb5e85`, which is that stale commit. So there are three copies of the controller in play — his
working clone, the VM's `~/repos` copy, and the rig's own checkout — and only the rig's is
current. Both stale copies would misread today's TagTracker on the wire.

Item 2 and that finding are for Michael to decide, since his uncommitted April simulator work is
in one of them. Asked in chat.

Item 4, telemetry lost on quit, is the one worth chasing and is now its own task. If an operator
quits TagTracker at the end of a flight rather than disconnecting, and no telemetry file is
written or recovered, then task 0-1 has nothing to pair and the feature silently does nothing in
the one case that matters most.

### Task 0-2, ssh verified — 2026-09-23 — Done
Michael installed the ECDSA key and `ssh parallels@192.168.0.136 true` returns with no
prompt, so step 1 is finished and the task is `Done`. I then ran the Mac script over ssh
for the first time. `tools/sim_rig.sh start` returned in 3.6 s. A status from a new ssh
connection 5 s later still showed PX4 SITL and the controller running, with TagTracker
connected from the Mac at 192.168.0.88. A second `start` started nothing new, and `stop`
left no rig processes and no tmux server in the VM.

**For the planning session**: nothing beyond the two entries below.

**For Michael**: nothing. `tools/sim_rig.sh start` is ready to use.

### Task 0-2, correction — 2026-09-23 — Partial
The key install command in the entry below is wrong: it names an ed25519 key, and this Mac
never uses one. Its managed ssh policy (`/etc/ssh/crypto.conf`, from Apple's security
compliance baseline) accepts only ECDSA P-256 keys, so ssh loaded the ed25519 key and never
offered it to the VM. Michael installed that key and still got "Permission denied". The
rig now uses `~/.ssh/id_ecdsa_uavrt_vm`, and `~/.ssh/config` and `tools/sim_rig.sh` point
at it. The correct command is
`ssh-copy-id -o BatchMode=no -i ~/.ssh/id_ecdsa_uavrt_vm.pub parallels@192.168.0.136`.

**For the planning session**
1. Any future brief that has a task make an ssh key on this Mac should say ECDSA P-256.

**For Michael**
1. The unused ed25519 key is still in the VM's `~/.ssh/authorized_keys`, and its key pair
   `~/.ssh/id_ed25519_uavrt_vm` is still on the Mac. Neither does anything; delete them if
   you want them gone.

### Task 0-2 — 2026-09-23 — commit 3d1ddf5 — Partial
Stopped at step 1, passwordless ssh. I made a key without a passphrase
(`~/.ssh/id_ed25519_uavrt_vm`) and added a host entry for the VM to `~/.ssh/config`, but
the Claude Code permission system refused to let me install the key in the VM, so
`ssh parallels@192.168.0.136 true` still fails. Everything else is built and verified.
The rig ran for the whole click-through, driven through Parallels' own command channel
instead of ssh, and the click-through that task 0-1 left open passed. The one piece never
run is the ssh hop in the Mac script.

The *rig* is the simulated aircraft: PX4 SITL (the PX4 autopilot compiled to run as a
normal program, here with its built-in physics model, SIH, so no Gazebo and no display)
plus `MavlinkTagController2 --simulator`, both in the Parallels VM, each in its own named
tmux session so they outlive the ssh command. TagTracker runs on the Mac.

Start command, once the key is installed:

```
cd ~/Developer/uavrt
tools/sim_rig.sh start            # preset defaults to strong
tools/sim_rig.sh status
tools/sim_rig.sh stop
tools/sim_rig.sh logs controller  # or px4
```

TagTracker link settings: none. TagTracker's default UDP auto-connect on port 14550 finds
the vehicle. PX4's ground station link listens on UDP 18570 in the VM and broadcasts to
192.168.0.255:14550 until a ground station answers, then sends to that ground station
directly. The Mac received 1,459 packets in 4 seconds this way, and the VM's firewall
already allowed 18570 in. The Mac's own firewall must allow TagTracker incoming
connections; Michael clicked Allow during this run. On a network that blocks broadcast,
a manual UDP link with server 192.168.0.136:18570 should work, but I did not test it.

Click-through, on TagTracker branch `telemetry-pairing` (build of eb2f50447), with Michael
pressing the buttons and me checking the files:
- Two start/stop detection runs in one connection. The controller logged two starts and
  two stops, each acknowledged. The C++ detector found the simulated tag at about 46 dB.
- Before disconnecting: one new folder, `Logs/2026-09-23-20-05-07-875/`, holding two
  `Pulse-*.csv` (96 and 84 pulse rows) and two `Pulse-*.json` with start and stop times,
  no telemetry file, and `telemetry_file` null in both.
- After Disconnect: the folder also held `2026-09-23 20-12-56.tlog`, 9.2 MB, byte-identical
  to the copy in `Telemetry/` (checked with `cmp`), and both sidecars named it.
- Pair Telemetry Logs, pressed once: "Telemetry copied into 0 log folder(s)." Michael
  picked this from a list of options I offered, not by typing it out. It matches the
  code's message for a folder already paired at disconnect. Nothing in the folder changed.

What the VM needed (step 2):
- The ssh server was listening, but the VM's firewall dropped port 22. I opened it to
  192.168.0.0/24 only.
- tmux was not installed. I installed it (tmux 3.4).
- numpy and scipy crashed on import with "Illegal instruction": numpy's OpenBLAS picks
  kernels for SME, the M4's matrix extension, which the VM advertises but which fault in
  a Parallels guest. `OPENBLAS_CORETYPE=ARMV8` fixes it and the rig sets it.
- `~/repos/MavlinkTagController2` in the VM was 23 commits behind and spoke an older wire
  format than TagTracker (details in item 2 below). Rather than touch it, the rig has its
  own checkout of `origin/main` (d3f7830) in `~/uavrt-rig`, built there with its own
  Python environment. The controller builds every path it spawns from `$HOME/repos`, so
  the rig runs it with `HOME=~/uavrt-rig`; its logs and its log pruning stay there too.
- PX4 SITL was present and built. The rig gives it its own working directory,
  `~/uavrt-rig/px4`, so it does not share parameters with the Gazebo runs.

Which detector simulator mode uses: both, chosen by TagTracker. Start Detection works only
in TagTracker's Survey Detection mode, which runs the C++ `uavrt_detection`; the rotation
modes run the Python detector. The VM is ARM64 Linux, so the C++ detector is already built
there (from `uavrt_detection` commit 766a385) and ran in this test. The x86_64 problem the
brief anticipated does not arise on this Mac.

I used Parallels' command channel (`prlctl exec`), which runs as root in the VM without a
password, to install tmux and add the firewall rule. The key install through the same
channel is what was refused.

**For the planning session**
1. Correct CLAUDE.md rule 5 and `docs/SOFTWARE_CONTEXT.md` sections 2, 7 and 8 on the
   tunnel protocol, the shared header that defines the messages TagTracker and the
   controller exchange. Neither repo has it as a git submodule any more. Both fetch it
   through CPM at a pinned commit, currently `81ed30ac`, set by the `GIT_TAG` for
   `TunnelProtocol` in TagTracker's `custom/CMakeLists.txt` and in the controller's
   `CMakeLists.txt`. The parity check is now "those two lines match". I confirmed both
   builds fetched a byte-identical `TunnelProtocol.h`.
2. Ask Michael what should happen to `~/repos/MavlinkTagController2` in the VM. It sits
   at commit 5419c4d with protocol commit 67f0b32, seven protocol commits older than
   TagTracker's, which change the start-detection and pulse messages. It also carries his
   uncommitted April simulator work: a JSON scenario option in the controller, a GUI for
   the simulator and example scenario files. I left all of it untouched. Anyone who runs
   the controller from that tree against today's TagTracker gets two programs that
   misread each other.
3. Update the simulator presets wherever the documents list them. The controller now
   takes signal levels: `strong`, `moderate`, `marginal`, `below-marginal`, `silent`,
   `competing`, `power-line`. The older names (`weak`, `noise-only`, `two-tags`,
   `distant`, `dropout`, `gap`, `rate-switch`) are simulator scenarios used only when no
   tags are uploaded, and TagTracker always uploads them before detection.
4. Decide whether to chase this: quitting TagTracker (Cmd-Q) with the simulated vehicle
   armed saved no telemetry file at all, and none was recovered at the next start. I saw
   it once and did not find the cause. QGroundControl saves the recording when the last
   vehicle disconnects, and quitting may not go through that path. If it holds, an
   operator who quits instead of disconnecting at the end of a flight loses the telemetry
   file, and task 0-1's pairing has nothing to pair.
5. Add `tools/sim_rig.sh` to the "Testing without hardware" table in CLAUDE.md and to
   `docs/SOFTWARE_CONTEXT.md`. I did not edit either.

**For Michael**
1. Install the key, entering the VM password once:
   `ssh-copy-id -o BatchMode=no -i ~/.ssh/id_ed25519_uavrt_vm.pub parallels@192.168.0.136`.
   Then `ssh parallels@192.168.0.136 true` should return silently, and
   `tools/sim_rig.sh status` is the first run of the Mac script over ssh.
2. The simulated vehicle has to arm at some point or TagTracker saves no telemetry file,
   because "Save logs even if vehicle was not armed" is off. Take off from TagTracker,
   or type `commander takeoff` in PX4's shell
   (`ssh -t parallels@192.168.0.136 tmux attach -t rig-px4`, detach with Ctrl-b d).
3. After a TagTracker rebuild, macOS may ask again whether TagTracker can accept incoming
   connections. If the vehicle appears before you click Allow, its startup requests are
   lost (this run showed a rally point transfer error) and TagTracker needs a restart.
4. Outside the repository I changed: `~/.ssh/config` (backup at `~/.ssh/config.bak3`), a
   new key pair `~/.ssh/id_ed25519_uavrt_vm`, and in the VM the firewall rule, tmux and
   `~/uavrt-rig`. Your `~/.ssh/config` also has an older `parallels-vm` entry pointing at
   192.168.0.102, which is no longer the VM's address. I left it.
5. PX4 SITL logs everything from boot: 225 MB in the 21 minutes of this run, so roughly
   650 MB an hour, and the VM has 7.4 GB free.
   The rig keeps only the newest ten PX4 flight logs.

### Task 0-1 — answered 2026-09-23 by the planning session (the task stays `Partial`)

All six items answered. The status stays `Partial` on purpose: the one thing not covered is the
one a person touches.

1. **The stand-in run is enough for everything except the new button, and Michael should do the
   click-through.** What the stand-in covered is stronger than the brief asked for: a real
   telemetry recording and save, the real ordering at disconnect, a byte-identical copy, the
   never-armed case, and a kill mid-detection where QGroundControl recovered the recording under
   a name 15 seconds off, which matching by filename would have gotten wrong and matching by
   content got right. That last one is worth keeping in the pull request description, because it
   is the argument for reading the file rather than trusting its name. What it did not cover is
   Pair Telemetry Logs, which is new code, new interface, and the only part of this a person
   presses. `qmllint` parsing is not evidence it works. Two minutes of clicking closes it, and
   "I ran it" carries weight with Don that a harness does not.
2. **Done.** `docs/SOFTWARE_CONTEXT.md` section 9 and "Decisions already made" above both now
   carry the folder layout and the sidecar fields, including the sentence that nothing will find
   pulse logs at the top of `Logs/` any more.
3. **Recorded in "Decisions already made" rather than in a brief, because the brief does not
   exist yet.** The file picker belongs to the field review's interface work, which is phase 2
   and unwritten. Tasks 1-1 to 1-3 are the analysis core and take explicit paths, so nothing
   there is affected.
4. **Accepted, with the measurement left open.** Doubling a copy QGroundControl already performs
   on the same thread at the same moment is a fair trade, and 11 ms on 221 KB scales to well
   under a second on a flight-sized file. Say so in the pull request rather than claiming it was
   measured, and note it as the one thing untested at real scale.
5. **Noted.** Deleting the end-of-recording check and watching three tests fail is the right kind
   of evidence, and worth more than the count of cases.
6. **Leave it.** Matching the surrounding hand-aligned style in a header is better than a
   formatted block that reads as foreign, and no workflow in this fork checks it. Mention it in
   the pull request so Don is not surprised.

**One thing the report did not flag as a change of behavior, and the pull request should.**
Rotation logs used to be deleted at every app start. They are not any more. The reasoning is
sound, since numbering now restarts per folder and collisions cannot happen, but it changes what
a user finds on disk after an app restart, and Don should read that in the description rather
than discover it in the diff.

### Task 0-1 — 2026-09-23 — commits f15c5a724, eb2f50447 — Partial
Stopped at "How you know it worked": the simulator run. All the code is written and
committed on TagTracker branch `telemetry-pairing`, which starts from `master` at
743c4bf50. Nothing outside `custom/` changed, and nothing in `custom/src/FieldReview/`.
The simulator run did not happen. This Mac has no PX4 SITL (the simulated autopilot
that TagTracker would see as the vehicle), and this session is refused screen capture,
so it cannot see or click TagTracker's buttons. In its place I ran the real app four
times with a temporary edit, never committed, that drives the same steps from code
against QGroundControl's built-in simulated vehicle (MockLink). What that did and did
not cover is in item 1 below.

What was built. A *log folder* is `Logs/<first pulse log's timestamp>/`. It is created
when the first pulse log after a vehicle connects is opened, and it receives every pulse
and rotation log until the last vehicle disconnects. That is the same moment
QGroundControl ends its telemetry recording. Each `Pulse-*.csv` gets a `Pulse-*.json`
beside it (the *sidecar*) with `sidecar_version`, `pulse_log`, `start_utc`, `stop_utc`,
`vehicle_id` (the MAVLink system id), `app_version` and `telemetry_file`. The pulse CSV
format is unchanged. On disconnect, and once at every app start, the telemetry file
whose span contains the start of every run in a folder is copied in and named in the
sidecars. A new fly view action, Pair Telemetry Logs, runs the same pass on demand.

The three decisions the brief asked for:
- The routine that deleted every `Rotation-*.csv` at app start is gone. It existed only
  because rotation numbering restarted at 1 each app run and would overwrite older
  files. Numbering now restarts per folder, so nothing can collide, and deleting a
  previous flight's rotation logs was losing data. Loose `Rotation-*.csv` files already
  sitting at the top of `Logs` are no longer deleted either.
- Detection started with no vehicle: the folder is named from the pulse log as usual,
  `vehicle_id` and `telemetry_file` stay null, and that run's own stop closes the
  folder, so a later connection does not append to it. Today's UI refuses to start
  detection without a vehicle, so this path cannot currently be reached.
- Two telemetry files match one folder: if they are identical copies, the first by name
  is used. If they differ, neither is named, the sidecars stay null, and the operator
  sees a message. One app never records two overlapping flights, so differing matches
  mean something is wrong, and naming either file could be naming the wrong one.

A decision the brief did not ask for: a match requires every run's start, not its stop,
to fall inside the telemetry file's span. A run left going when the vehicle disconnects
keeps writing to its pulse log (unchanged behavior), and its stop time lands after the
recording ended.

**For the planning session**
1. Decide whether the stand-in run is enough or Michael should do the click-through in
   item 1 under "For Michael". The stand-in covered the real telemetry recording and
   save, the ordering on disconnect, and the real file format. Two pulse logs and two
   sidecars were in the folder before disconnect, with no telemetry file. After
   disconnect the folder also held a byte-identical copy (checked with `cmp`), and each
   sidecar named it with its own start and stop. A second run with the vehicle never
   armed left no telemetry file and null sidecar fields. A third run was killed with
   SIGKILL mid-detection; on restart QGroundControl recovered the stranded recording
   under a name 15 seconds later than the run's start, which matching by filename would
   have gotten wrong, and the startup pass paired it by content. The stand-in did not
   cover the Start and Stop Detection buttons (they call the same unchanged routine),
   the real controller, or the new Pair Telemetry Logs button. Its QML parses under
   `qmllint`, and nothing else has checked it.
2. Add the log folder layout and the sidecar fields to "Decisions already made" and to
   `docs/SOFTWARE_CONTEXT.md`. Anything that looks for pulse logs at the top of `Logs`
   will find none from now on.
3. Add to the field review brief that its file picker must look inside the per-connection
   folders. The field review branch lists no files yet, and the Python prototype takes
   explicit paths, so nothing breaks today.
4. Pairing runs on the UI thread at disconnect: reading the telemetry file and copying
   it. For the 221 KB test recording that took 11 ms. I did not measure a real hour-long
   flight, whose file will be tens of megabytes. QGroundControl already makes a copy of
   the same size on the same thread at the same moment, so I expect the added stall to
   be similar in length, but that is a guess.
5. Tests added, registered with `add_qgc_test`, all passing: `PulseLogFolderTest` (5
   cases, uses a MockLink vehicle and the real disconnect path) and `TelemetryPairingTest`
   (8 cases, synthetic telemetry files). Temporarily removing the end-of-recording check
   made three of them fail, including the ground test, so they catch the mistake that
   matters most.
6. The repo's clang-format check flags my additions to `CSVLogManager.h` and
   `CustomPlugin.h`, because those headers use hand-aligned columns and I matched them.
   No CI workflow in this fork runs that check. New files are fully clang-formatted
   with the pinned version, 23.1.0.

**For Michael**
1. If the planning session wants it: connect to the simulator or the aircraft, start and
   stop detection twice, look in `Logs/` for one new folder with two `Pulse-*.csv` and
   two `Pulse-*.json`, disconnect, and check that a `.tlog` has appeared in the folder and
   both `.json` files name it. Press Pair Telemetry Logs once and read the message.
2. Push `telemetry-pairing` and open the pull request to Don against `master`. I have not
   pushed. `custom/tunnel-protocol/` and `src/FirmwarePlugin/APM/ArduPilot-Parameter-Repository/`
   are untracked and were not committed.
3. The test runs wrote three folders and two telemetry files into
   `~/Documents/TagTracker Daily/`. I moved them out afterward, and those folders now
   match their earlier listings. Nothing of yours was touched.


---

## Resolved

Nothing yet.
