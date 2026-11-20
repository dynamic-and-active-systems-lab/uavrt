<!-- Added to the hub 2026-11-20 from scratch/, written by a separate Claude session the same day.
Body kept as written; PX4 version and parameter values checked against the flight logs are in
NAU_VHF_DRONE.md, and the symptom-to-cause entry is in field-notes.md. -->

# SIYI UniRC 7 Pro Link Debug Summary (2026-11-20)

## System

- Quad, Cube Orange+ running PX4
- SIYI UniRC 7 Pro handheld GCS + air unit, 6S power (22–24.6 V in logs, not a factor)
- RC via SBUS (`input_source` 4), MAVLink telemetry via air unit on TELEM1
- No camera; link used for RC + telemetry only

## Issue 1: Lost link and RTL at \~40–60 m

### Symptom

During Nov 14 test flights, RC and MAVLink dropped together for 1–7 s, then recovered on their own. PX4 held 5 s, then RTL'd.

### Log analysis (logs 197–206, 2026-11-14)

- RC failsafe and GCS heartbeat loss coincided within \~1 s: whole radio link down, not one stream.
- Dropouts at 41–97 m straight-line distance, elevation angles 22°–85°, so not an overhead antenna-null problem.
- Flights with no dropouts (202, 204, 206) never exceeded \~38 m from the pilot.
- QGC RSSI was a constant 41% on every sample, including during dropouts. It's meaningless with SBUS; ignore it.
- Failsafe trigger was RC loss: `NAV_RCL_ACT` = 2 (Return), `COM_RC_LOSS_T` = 0.5 s. `NAV_DLL_ACT` = 0 (disabled).

### Root cause (confirmed by A/B test)

The air unit was flown with only the 2.4 GHz antennas fitted, and the 5.8 GHz ports were empty. The link is dual-band with automatic band/channel selection, and it likely settled on 5.8 GHz at close range, where the bare ports still worked, then faded at \~40–60 m.

**Fix:** install all four air unit antennas (2× 5G MMCX quick-release + 2× 2.4G IPEX). A ground walk-away A/B test with and without the 5.8G antennas confirmed the fix at distance.

### Notes and follow-ups

- The PX4 logs cannot show which band was active. The band-switching explanation is inferred, not proven.
- On this firmware the UniGCS Frequency Band dropdown only offers "2.4G&5.8G" (no single-band lock). Image Transmission Mode (Standard / Bitrate Enhancement / Bitrate Priority) only affects video bitrate, not band; leave it on Standard.
- Never power the air unit with any antenna port empty.
- Use **UniGCS → Link Status** (packet loss, signal strength/quality, wireless channel) as the real link-quality meter, and screen-record it during tests and flights.
- Consider raising `COM_RC_LOSS_T` to \~1–1.5 s so a brief band switchover doesn't trigger RTL (trade-off: slower reaction to real loss).
- Open question for SIYI: are RC and telemetry sent on both bands at once, or switched between them, and what is the switchover time?
- Antenna placement per manual: on multirotors, mount the air unit antennas pointing down along the arms; keep them ≥10 mm from carbon or metal and ≥50 mm apart, with cables uncrossed and away from ESCs. Keep the handheld antennas vertical with the flat side toward the aircraft.
- Add an antenna seating check to the preflight checklist.

## Issue 2: UniGCS "parameter loading" loop (unresolved)

### Symptom

UniGCS on the handheld repeatedly restarts the parameter download (\~every 10 s). QGC loads parameters fine.

### Findings

- The air unit is on **TELEM1** (`MAV_0_CONFIG` = 101), which was at 57600. TELEM2 (921600) is the Onboard link (`MAV_1_MODE` = 2), not the air unit.
- The UniGCS Datalink "sky baud rate" only supports 9600 / 57600 / 115200.
- Changed `SER_TEL1_BAUD` and the UniGCS Datalink 1 baud to **115200**. The download now gets further but still loops.
- `MAV_0_RATE` = 1200 B/s, a low cap that may be throttling the download.
- PX4 logged a \~125% incoming message-loss rate on the air unit's link, consistent with two GCS apps talking at once.

### Next steps to try

1. Set `MAV_0_RATE` = 0 (auto from baud) and reboot.
2. Run UniGCS with QGC fully closed.
3. Update UniGCS and UniRC firmware.
4. If it still loops, use QGC for PX4 configuration. UniGCS is ArduPilot-centric.

## Current status

- Link range issue: **fixed** (all antennas installed, walk test passed).
- UniGCS parameter loop: **open**, low priority. QGC works as the GCS.
