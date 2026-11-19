#!/usr/bin/env python3
"""Derived data for the history section of the report (Ponui 2025, Cumbria 2025, now).

Reads the per-test files under ../tests/ and ../data/flight_summary.csv and writes:
  ../data/history_summary.csv    ground (motors off) and steady-flight floor per field configuration
  ../data/history_steps.csv      the four in-flight stages, March 2025 to November 2026
  ../data/trip_flights.csv       every Ponui-trip flight with data: in-flight median, 10th and 90th percentile
  ../data/history_timelines.csv  per-second floors of Ponui Day 2 flight 4 and the two Cumbria flights
Usage (from this folder): python3 make_history_data.py
"""
import csv, json, os, collections, datetime as dt
import numpy as np
from decimal import Decimal, ROUND_HALF_UP

H = os.path.dirname(os.path.abspath(__file__)); NR = os.path.join(H, "..")
T_P = os.path.join(NR, "tests", "2025-03-ponui-usb-ferrites"); T_C = os.path.join(NR, "tests", "2025-11-24-cumbria-mini-choke")
D = os.path.join(NR, "data")
cal = json.load(open(os.path.join(D, "bench_calibration.json"))); NM, NH = cal["floor_mini_dBmHz"], cal["floor_hf_dBmHz"]
S = {r["flight"]: r for r in csv.DictReader(open(os.path.join(D, "flight_summary.csv")))}
med = lambda v: float(np.median(v))

# ---- Ponui Day 2 (IQ), no ferrites on the USB cable
d2 = json.load(open(os.path.join(T_P, "day2_floors.json")))
d2_flight = [st[k][2] for st in (v["stages"] for v in d2.values()) for k in st if k.startswith("flight")]
d2_ground = [st[k][2] for st in (v["stages"] for v in d2.values()) for k in st if k.startswith("ground")]

# ---- Pulse logs, every flight of the trip
F = collections.defaultdict(list)
for r in csv.DictReader(open(os.path.join(T_P, "pulse_noise.csv"))):
    F[r["file"]].append((float(r["z"]), float(r["dbm_hz"]), float(r["lat"])))
nz = lambda fn: dt.datetime.strptime(fn[6:25], "%Y-%m-%d-%H-%M-%S") + dt.timedelta(hours=13)
trip = []
for fn in sorted(F):
    a = np.array(F[fn]); air = a[a[:, 0] > 10, 1]
    if len(air) < 4 or a[0, 2] == 0: continue
    wg = a[0, 2] < -40
    if not wg and fn < "Pulse-2025-03-18": continue          # Day 2 comes from the IQ recordings instead
    trip.append(dict(when_nzdt=nz(fn).strftime("%Y-%m-%d %H:%M"), site="Wellington" if wg else "Ponui", source="pulse log " + fn,
                     usb_ferrites="no" if wg else "yes", n=len(air), median=round(med(air), 2),
                     p10=round(float(np.percentile(air, 10)), 2), p90=round(float(np.percentile(air, 90)), 2)))
for i, (k, v) in enumerate(sorted(d2.items())):
    st = v["stages"]; a, b, _ = st[[s for s in st if s.startswith("flight")][0]]; x = np.array(v["per_second_dBm_Hz"][a:b])
    trip.append(dict(when_nzdt=f"2025-03-17 flight {i + 1}", site="Ponui", source=f"IQ, Pi session {k}", usb_ferrites="no", n=len(x),
                     median=round(med(x), 2), p10=round(float(np.percentile(x, 10)), 2), p90=round(float(np.percentile(x, 90)), 2)))
trip.sort(key=lambda r: r["when_nzdt"])
pt_flight = med([r["median"] for r in trip if r["site"] == "Ponui" and r["usb_ferrites"] == "yes"])
wg_flight = [r["median"] for r in trip if r["site"] == "Wellington"]

# ---- Cumbria (IQ), Mini inside the shield, choke. Floor = mean of the two channels' readings in dB.
cu = json.load(open(os.path.join(T_C, "cumbria_floors.json")))
CW = {"2025-11-20_02-40-07": dict(id="C1", ground=(0, 8), steady=(60, 420), after=(558, 564)),
      "2025-11-20_03-24-27": dict(id="C2", ground=(0, 5), steady=(60, 525), after=(640, 661), landed=(605, 635))}
cum = {}
for k, w in CW.items():
    x = (np.array(cu[k]["ch1"]) + np.array(cu[k]["ch8"])) / 2
    cum[w["id"]] = {s: round(med(x[a:b]), 2) for s, (a, b) in w.items() if s != "id"}
    cum[w["id"]]["series"] = x; cum[w["id"]]["alt"] = cu[k]["alt"]

# ---- Summary rows
rows = [
    dict(id="W", label="Wellington test flights, no USB ferrites", date="2025-03-15", site="Wellington, NZ", freq_mhz="160.40", receiver="mini", gain=20,
         configuration="Mini outside the shield on a USB extension, no ferrites on it; 15 ft coax, no choke", ground_dBm_per_Hz="",
         steady_dBm_per_Hz=round(med(wg_flight), 2), source="pulse logs, 2 flights"),
    dict(id="D2", label="Ponui Day 2, no USB ferrites", date="2025-03-17", site="Ponui Island, NZ", freq_mhz="161.09", receiver="mini", gain=20,
         configuration="Mini outside the shield on a USB extension, no ferrites on it; 15 ft coax, no choke", ground_dBm_per_Hz=round(med(d2_ground), 2),
         steady_dBm_per_Hz=round(med(d2_flight), 2), source="IQ, 4 flights"),
    dict(id="PT", label="Ponui Days 3-8, USB ferrites", date="2025-03-18 to 23", site="Ponui Island, NZ", freq_mhz="160.17-161.09", receiver="mini", gain=20,
         configuration="As Day 2 plus two snap-on ferrites on the USB extension", ground_dBm_per_Hz=round((float(S["P2"]["ground_dBm_per_Hz"]) + float(S["P3"]["ground_dBm_per_Hz"])) / 2, 2),
         steady_dBm_per_Hz=round(pt_flight, 2), source="pulse logs, 15 flights; ground from the Day 8 IQ (P2, P3)"),
    dict(id="C1", label="Cumbria flight 1", date="2025-11-24", site="Ambleside, UK", freq_mhz="173.29-173.31", receiver="mini", gain=21,
         configuration="Mini inside the shield, bonded SMA bulkhead, choke, 15 ft coax, PHW150C; Castle BEC, no aircraft ferrites",
         ground_dBm_per_Hz=cum["C1"]["ground"], steady_dBm_per_Hz=cum["C1"]["steady"], source="IQ"),
    dict(id="C2", label="Cumbria flight 2", date="2025-11-24", site="Ambleside, UK", freq_mhz="173.29-173.31", receiver="mini", gain=21,
         configuration="As C1", ground_dBm_per_Hz=cum["C2"]["ground"], steady_dBm_per_Hz=cum["C2"]["steady"], source="IQ"),
]
for r in rows:
    own = NM if r["receiver"] == "mini" else NH
    r["ground_above_own_floor_db"] = "" if r["ground_dBm_per_Hz"] == "" else round(r["ground_dBm_per_Hz"] - own, 2)
    r["steady_above_own_floor_db"] = round(r["steady_dBm_per_Hz"] - own, 2)
with open(os.path.join(D, "history_summary.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

R = {r["id"]: r for r in rows}
now_f = (float(S["F2"]["steady_dBm_per_Hz"]) + float(S["F3"]["steady_dBm_per_Hz"])) / 2
now_g = (float(S["F2"]["ground_dBm_per_Hz"]) + float(S["F3"]["ground_dBm_per_Hz"])) / 2
steps = [
    ("1", "Ponui Day 2, Mar 2025", "Mini on a USB extension outside the shield; no ferrites; no choke", "mini", R["D2"]["steady_dBm_per_Hz"], R["D2"]["ground_dBm_per_Hz"], ""),
    ("2", "Ponui Days 3-8, Mar 2025", "Two snap-on ferrites on the USB extension", "mini", R["PT"]["steady_dBm_per_Hz"], R["PT"]["ground_dBm_per_Hz"], "one change, same site, receiver and gain"),
    ("3", "Cumbria, Nov 2025", "Mini moved inside the shield on a bonded SMA bulkhead; common-mode choke on the coax", "mini",
     round((R["C1"]["steady_dBm_per_Hz"] + R["C2"]["steady_dBm_per_Hz"]) / 2, 2), round((R["C1"]["ground_dBm_per_Hz"] + R["C2"]["ground_dBm_per_Hz"]) / 2, 2), "also new site and frequency (173 MHz), gain 21"),
    ("4", "Arizona, Nov 2026", "Airspy HF+ outside the shield via a bonded USB bulkhead; aircraft ferrites F1-F9; PM12S-4A regulator", "hf", round(now_f, 2), round(now_g, 2), "also new site, frequency and receiver"),
]
with open(os.path.join(D, "history_steps.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["stage", "label", "change", "receiver", "steady_dBm_per_Hz", "ground_dBm_per_Hz", "own_dBm_per_Hz", "notes"])
    r1 = lambda v: float(Decimal(str(v)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))   # stage values to 0.1 dB, as quoted in the text
    for s in steps: w.writerow(list(s[:4]) + [r1(s[4]), r1(s[5]), round(NM if s[3] == "mini" else NH, 2), s[6]])
with open(os.path.join(D, "trip_flights.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(trip[0].keys())); w.writeheader(); w.writerows(trip)
with open(os.path.join(D, "history_timelines.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["flight", "second", "floor_dBm_per_Hz", "alt_m"])
    v = d2["11-21-50"]["per_second_dBm_Hz"]
    for i, x in enumerate(v): w.writerow(["D2", i, round(x, 2), ""])
    for cid in ("C1", "C2"):
        for i, (x, a) in enumerate(zip(cum[cid]["series"], cum[cid]["alt"])): w.writerow([cid, i, round(float(x), 2), "" if a is None else a])
print(json.dumps({"steps": [(s[1], s[4], s[5]) for s in steps], "wellington": wg_flight, "d2": d2_flight, "d2_ground": d2_ground,
                  "cumbria": {k: {s: v for s, v in c.items() if s not in ("series", "alt")} for k, c in cum.items()}}, indent=1))
