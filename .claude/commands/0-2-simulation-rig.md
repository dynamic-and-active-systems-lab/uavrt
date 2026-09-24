---
description: "Task 0-2 — stand up the flight simulation rig in the Parallels VM and leave one command to start it"
model: opus
effort: high
---

Read first: `docs/WRITING_RULES.md`, then `docs/TASK_COMMS.md` including "Decisions already made".

## What this task is

Testing TagTracker currently means flying, which is a slow way to find out that a button does
not work. Everything needed to avoid that already exists and has never been wired together on
this machine. This task wires it together and leaves behind a way to start it that later tasks
can call without thinking about it.

When it is done, Michael runs one command, gets a simulated aircraft flying with a simulated
radio producing real pulses, and spends his attention on TagTracker rather than on the rig.

## The pieces, and why none of them need writing

- **PX4 SITL** — the flight controller, simulated. Already set up in Michael's Parallels VM.
- **`MavlinkTagController2 --simulator`** — the companion computer software, with the SDR
  replaced. It spawns `simulator/iq_simulator.py` as the IQ source over ZeroMQ, then runs the
  real decimator and the real detector on top of it, so everything downstream of the antenna is
  the actual flight code. Seven presets: `strong`, `weak`, `noise-only`, `two-tags`, `distant`,
  `dropout`, `gap`. Tag parameters from the MAVLink tag database are mapped into the simulator's
  frequency offset and pulse timing.
- **TagTracker** — runs on the Mac, as the ground station, exactly as it does in the field.

The aircraft side belongs in the VM and the ground station on the Mac, which is the real
arrangement rather than a convenient fiction.

## The machine

```
VM:   parallels@192.168.0.136, MavlinkTagController2 in ~/repos
Mac:  the repository at ~/Developer/uavrt, TagTracker built at
      TagTracker/build/macOS-debug/Debug/TagTracker.app
```

## What to build

1. **Passwordless ssh from the Mac to the VM.** Generate a key if there is none, install it, and
   confirm `ssh parallels@192.168.0.136 true` returns with no prompt. An interactive password
   prompt hangs a Claude Code session dead, so this is not optional. If the address has moved,
   stop and ask rather than guessing.

2. **Confirm the VM can run the pieces.** `MavlinkTagController2` built, or build it; its
   dependencies present; the Python environment for `iq_simulator.py` created by `setup_venv.sh`;
   PX4 SITL present and runnable. Report what was missing.

   Find out whether simulator mode uses the Python detector or the C++ `uavrt_detection`, which
   only builds for aarch64 Linux. If it needs the C++ one and the VM is x86_64, say so plainly
   in your report rather than working around it quietly.

3. **Scripts in the hub's `tools/`**, named so their purpose is obvious, that start, stop and
   report on the rig from the Mac over ssh. Requirements:

   - Everything on the VM runs under named `tmux` sessions, so it survives the ssh command
     exiting. Starting the rig and then having it die when the command returns is the failure
     mode to design against.
   - Starting twice does not produce two of anything.
   - The status command says what is actually running and reachable, not what should be.
   - The stop command leaves nothing behind.
   - The simulator preset is an argument, defaulting to `strong`.
   - Logs from both the controller and SITL land somewhere a person can read afterward.

4. **Work out how TagTracker on the Mac connects**, and write it down. The controller talks to
   PX4 on the VM's own loopback. TagTracker has to reach the same vehicle across the network, so
   something has to be listening on an address the Mac can see. Settle it, verify it, and put
   the exact link settings in your report and in `docs/TASK_COMMS.md`.

## How you know it worked

Start the rig. Connect TagTracker on the Mac. Confirm it shows a vehicle and the tag controller
heartbeat. Start detection, wait for pulses to appear, stop detection.

**Then do the click-through that task 0-1 could not.** It is the same rig and it closes an open
item. On branch `telemetry-pairing`, with that build running:

- Start and stop detection twice in one connection.
- Before disconnecting, check `Logs/` holds one new folder with two `Pulse-*.csv` and two
  `Pulse-*.json`, and no telemetry file.
- Disconnect. Check the same folder now holds a `.tlog` and that both sidecars name it.
- Press Pair Telemetry Logs once and record exactly what the message says.

That last one is the only part of task 0-1 no person has ever exercised, and it is the only part
of it a person presses.

## Rules

Nothing in this task changes TagTracker source. The scripts go in the hub repository, under
`tools/`, committed there.

Do not put the ssh private key anywhere in the repository, and do not print it.

If the VM turns out to be missing something large, such as PX4 SITL not really being there, stop
and report `Blocked` with what is needed rather than installing your way through it.

## When you finish

Append an entry to the top of "Open" in `docs/TASK_COMMS.md` with your commit hashes, the exact
command to start the rig, the TagTracker link settings, and the result of the click-through. Then
report to Michael in chat, ending with what he needs to do.
