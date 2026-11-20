#!/usr/bin/env python3
"""PX4 flight-log series aligned to the noise recordings, for the report.

Reads ../tests/<test>/px4_per_second.csv (one row per second of each PX4 log, written from the .ulg
files with pyulog; see the test READMEs) and writes ../data/px4_timelines.csv, indexed by the second of
each noise recording:
  2026-11-14 flights: the recording starts at the Pi session time (UTC, the log folder's name) and
  PX4 seconds are UTC from GPS, so the alignment is exact to the second. Checked: the noise rises
  within 1-2 s of the motors spinning up on every flight.
  Cumbria 2025-11-24: the Pi clock was wrong, so the offset is the one that best matches the PX4
  height to the height logged with the detected pulses (median difference 0.03-0.04 m).
Height is relative to the point where the motors spun up. Usage: python3 make_px4_data.py
"""
import csv, os, collections, datetime as dt
import numpy as np

H = os.path.dirname(os.path.abspath(__file__)); NR = os.path.join(H, ".."); D = os.path.join(NR, "data")
REC = {  # flight: (test folder, recording length source, offset rule)
    "F2": ("2026-11-14-flights-rail-x-ranch", "17:31:39"), "F3": ("2026-11-14-flights-rail-x-ranch", "17:40:15"),
    "F5": ("2026-11-14-flights-rail-x-ranch", "17:46:24"), "F6": ("2026-11-14-flights-rail-x-ranch", "17:50:16"),
    "F7": ("2026-11-14-flights-rail-x-ranch", "17:53:16"),
    "C1": ("2025-11-24-cumbria-mini-choke", -14), "C2": ("2025-11-24-cumbria-mini-choke", -18)}
LEN = collections.Counter(r["flight"] for r in csv.DictReader(open(os.path.join(D, "flight_timelines.csv"))))
LEN.update(collections.Counter(r["flight"] for r in csv.DictReader(open(os.path.join(D, "history_timelines.csv"))) if r["flight"] in ("C1", "C2")))
f = lambda x: float(x) if x != "" else np.nan
out = []
for fid, (test, rule) in REC.items():
    rows = [r for r in csv.DictReader(open(os.path.join(NR, "tests", test, "px4_per_second.csv"))) if r["flight"] == fid]
    t = np.array([int(r["unix"]) for r in rows]); mot = np.array([f(r["motor_mean"]) for r in rows])
    alt = np.array([f(r["alt_m"]) for r in rows]); alt = alt - alt[np.argmax(mot > 0.05)]
    if isinstance(rule, str):
        t0 = int(dt.datetime(2026, 11, 14, *map(int, rule.split(":")), tzinfo=dt.timezone.utc).timestamp()); j0 = t0 - t[0]
    else:
        j0 = rule
    for i in range(LEN[fid]):
        j = i + j0
        if 0 <= j < len(rows):
            r = rows[j]; out.append([fid, i, round(float(alt[j]), 2) if alt[j] == alt[j] else "", r["motor_mean"], r["lidar_m"], r["current_a"]])
        else:
            out.append([fid, i, "", "", "", ""])
with open(os.path.join(D, "px4_timelines.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["flight", "second", "height_m", "motor_mean", "lidar_m", "current_a"]); w.writerows(out)
print(len(out), "rows")
