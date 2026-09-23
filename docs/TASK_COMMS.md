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

Nothing yet. The first task has not run.

---

## Resolved

Nothing yet.
