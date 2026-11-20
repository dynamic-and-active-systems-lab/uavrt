# Field notes

Diagnosis guides for problems where one symptom has several causes. Each entry lists the causes
in the order to check them: cheapest check first.

## Red controller bar on TagTracker

The controller bar is the box on TagTracker's top toolbar that names the selected tag. It is
green while TagTracker is receiving heartbeats from the controller program on the Pi
(MavlinkTagController2), red when it is not, and orange when heartbeats arrive but the Pi reports
under-voltage or thermal throttling. "No Tag" inside the box only means no tag is selected; it has
nothing to do with the colour.

Red has had four different causes so far.

| Order | Cause | How to tell | Fix | First seen |
|---|---|---|---|---|
| 1 | **The controller is not running.** In October the controller's automatic start moved from a crontab entry to a system service, and rebuilding does not switch it over. | On the Pi: `systemctl status mavlink-tag-controller` is not running, or `pgrep -a MavlinkTag` shows nothing. | Rerun the setup script and reboot. See problem 1 in `pi5-troubleshooting.md`. | 2026-10-30 |
| 2 | **The Pi cannot hear the flight controller.** On a fresh Pi 5 install, the serial port name the controller opens points at the debug connector instead of the pins wired to the Pixhawk. | The controller log (`~/MavlinkTagController.log`) stops at `Waiting for autopilot heartbeat...`. | Add `dtparam=uart0_console` to the Pi's boot configuration. See problem 3 in `pi5-troubleshooting.md`, and MavlinkTagController2 issue #187. | 2026-11-02 |
| 3 | **The controller has not heard the ground station.** It sends TagTracker nothing at all until it has received a heartbeat from a ground station, and it only accepts ground station system ID 255. | The log shows `Found autopilot` but never `Found gcs - sysid: 255`. | Check that the radio forwards the ground station's messages to the Pi: in PX4, forwarding must be on for the SIYI air unit's port (TELEM1, `MAV_0_FORWARD`), not just for the Pi's (TELEM2, `MAV_1_FORWARD`). Both were 1 in the 2026-11-14 PX4 log. Check that TagTracker's ground station system ID is 255. | Not yet seen. Read from the controller source (`controller/Connection.cpp`) in September 2026; recheck it against the current code. |
| 4 | **TagTracker and the controller speak different protocol versions.** The tunnel protocol is the shared definition of every message between them; both programs pin a version, and they must match exactly. A heartbeat with the wrong version is ignored, so the bar stays red even though heartbeats arrive. | TagTracker shows a "Controller protocol mismatch" message once per app start, naming both version numbers. | Rebuild whichever side is older so both pin the same protocol commit. | 2026-09-30, when a TagTracker build from 2026-09-24 (version 5) met a controller just updated to version 7. |

On 2026-09-30 the version check came first in the investigation because the controller had just
been updated. When nothing has changed on either side, start at row 1.

## RC and telemetry drop out together, then the drone returns home

Both links go at once for 1–7 s and recover on their own; PX4 waits for the RC-loss timeout and
switches to Return. Full write-up: `siyi-link-debug-2026-11-20.md`.

| Order | Cause | How to tell | Fix | First seen |
|---|---|---|---|---|
| 1 | **An air unit antenna is missing.** The SIYI link picks its band automatically between 2.4 and 5.8 GHz. With the 5.8 GHz ports empty it works at close range and fades at about 40–60 m. The band switching is inferred; the PX4 logs cannot show which band was in use. | Dropouts start beyond about 40 m and never happen close in. In the PX4 log, RC loss and the ground station heartbeat loss fall within about a second of each other. Check the air unit: four antennas, two 5.8 GHz (MMCX quick-release) and two 2.4 GHz (IPEX). | Fit all four antennas. Never power the air unit with an antenna port empty. Confirmed by a walk-away test with and without the 5.8 GHz antennas, 2026-11-20. | 2026-11-14 flights 1–4 (PX4 logs 198–201), at 41–97 m |

**Do not use QGroundControl's RSSI to judge the link.** With S.Bus it reads a constant 41 %, even
during dropouts. Use UniGCS → Link Status (packet loss, signal strength and quality, channel), and
screen-record it during tests.

**Settings in play** (from the PX4 log of 2026-11-14): Return on RC loss (`NAV_RCL_ACT` = 2) after
0.5 s (`COM_RC_LOSS_T`); data-link loss action off (`NAV_DLL_ACT` = 0). Raising `COM_RC_LOSS_T` to
1–1.5 s would ride out a brief band switch, at the cost of a slower reaction to a real loss. Not
changed yet.

## UniGCS keeps restarting its parameter download

Open, low priority. UniGCS on the handheld restarts the parameter download about every 10 s;
QGroundControl and TagTracker load parameters normally. Seen 2026-11-20. Tried so far: the air
unit's port (TELEM1) and UniGCS's datalink both raised from 57600 to 115200 baud, which helped but
did not fix it. Next: set `MAV_0_RATE` to 0 (it was capped at 1200 bytes/s) and reboot; run UniGCS
with QGroundControl closed; update UniGCS and the handheld's firmware. Failing that, configure PX4
from QGroundControl. Details in `siyi-link-debug-2026-11-20.md`.

## "Waiting..." on the detection bar that never clears

The detection bar is the strength bar TagTracker shows for each tag once detection starts.
"Waiting..." means TagTracker has received nothing from that tag's detector yet: no pulse, and no
"no pulse" report either.

**With Survey Detection selected, this is normal whenever no tag is heard.** Survey Detection uses
the MATLAB detector (`uavrt_detection`), which reports only confirmed pulses and sends nothing when
it hears nothing. The bar stays on "Waiting..." until the first confirmed pulse, however long that
takes. The rotation modes use the Python detector, which reports every cycle and shows
"No Pulse ×N" instead. Seen 2026-11-09 during an in-flight noise-floor test with no tag out.

To confirm the detector is running rather than stuck, look at its log on the Pi:
`tail -n 30 "$(find ~/Logs -name 'detector_*' -mmin -30 | head -1)"`. A working detector ends each
segment with "No pulses detected" and a processing time well under a second. On the HF+ its
threshold and score values print as 0.000000; that is expected, because the HF+ noise floor is about
10,000 times lower than the Airspy Mini's and the values are too small for six decimal places.
