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

**There is a simulated aircraft; use it before reaching for hardware.** Built by task 0-2 and
run from the Mac with `tools/sim_rig.sh start`, `status`, `stop` and `logs`. It brings up PX4
SITL and `MavlinkTagController2 --simulator` in the Parallels VM at 192.168.0.136, each in its
own tmux session so they outlive the ssh command. TagTracker on the Mac finds the vehicle through
its default UDP auto-connect on port 14550; no link needs configuring. The rig has its own
checkout and Python environment under `~/uavrt-rig` in the VM, deliberately separate from
Michael's `~/repos`.

Two things that will bite. The vehicle must arm at some point or QGroundControl saves no
telemetry file at all, because "save logs even if vehicle was not armed" is off; take off from
TagTracker or type `commander takeoff` in the PX4 shell. And macOS may re-ask whether TagTracker
can accept incoming connections after a rebuild; if the vehicle appears before you click Allow,
its startup requests are lost and TagTracker needs restarting.

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

**Open question, not yet decided: how the triangulation gets into the build.** The
interpolated surface needs a Delaunay triangulation, which is the standard way of
joining scattered points into triangles so a value can be interpolated inside each one.
QGroundControl has none. The three options are fetching `delaunator-cpp` through CPM the
way the build already fetches its test libraries, vendoring that single header into
`custom/src/FieldReview/`, or writing the triangulation by hand. The planning session
recommends the first. Until Michael answers, no task should implement the surface.

---

## Open — waiting on the planning session

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
