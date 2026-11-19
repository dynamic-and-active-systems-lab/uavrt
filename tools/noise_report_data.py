#!/usr/bin/env python3
"""Build the derived data for the noise-reduction report from the raw recordings.

Reads the raw IQ recordings (OneDrive FLIGHT_TESTING_DATA) and the NanoVNA files, and writes small
CSV/JSON files to hardware/noise-reduction/data/. Re-run after adding a test, then rebuild the
report. Usage: noise_report_data.py <FLIGHT_TESTING_DATA dir> <hub dir>
"""
import sys, os, json, csv, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from noise_floor import floor_timeline
from bench_calibration import psd_blocks, analyse

FTD, HUB = sys.argv[1], sys.argv[2]
OUT = os.path.join(HUB, "hardware/noise-reduction/data"); os.makedirs(OUT, exist_ok=True)
PATH_LOSS_DB = 0.6       # generator to receiver, 2026-11-17 NanoVNA (0.47 dB read + 0.15 dB thru correction)
KT0 = -173.93            # dBm/Hz at 295 K (bench termination temperature)

# ---------- bench calibration ----------
B = os.path.join(FTD, "2026-11-18-Office_HF_v_Mini_Testing/DRONE_LOGS")
runs = [("Mini_1", "Logs-Detectors-2026-11-18_15-24-11", 3750, "mini"),
        ("HF", "Logs-Detectors-2026-11-18_15-32-46", 3840, "hf"),
        ("Mini_2", "Logs-Detectors-2026-11-18_15-40-45", 3750, "mini")]
cal = {"path_loss_db": PATH_LOSS_DB, "runs": {}}
bench_rows = []; bench_spec = []
for name, d, fs, rx in runs:
    p = os.path.join(B, d, "data_record.4.1.bin")
    o = analyse(p, fs, name)
    ks = [o["res"][str(l)][2] - (l - PATH_LOSS_DB) for l in (-120, -110, -100, -90)]
    o["k_per_level"] = ks; o["k"] = float(np.mean(ks[:2])); o["rx"] = rx
    o["X_flightmetric_load"] = float(np.median(floor_timeline(p, fs)[3:o["glitch_s"] - 2]))
    cal["runs"][name] = o
    # per-second timeline
    P, f = psd_blocks(p, fs); df = f[1] - f[0]
    inner = abs(f) < 0.4 * fs; kt = np.argmin(abs(f - o["tone_hz"]))
    excl = np.zeros_like(f, bool); excl[max(0, kt - 6):kt + 7] = True
    local = (abs(f - o["tone_hz"]) < 600) & ~excl & inner
    for t in range(len(P)):
        Nl = np.median(P[t, local]); tone = (P[t, kt - 5:kt + 6] - Nl).sum() * df
        bench_rows.append([name, rx, t, 10 * np.log10(np.median(P[t, inner])), 10 * np.log10(Nl),
                           10 * np.log10(tone) if tone > 0 else "", ])
    # spectra near tone: load segment and each tone step
    segs = {"load": (3, o["glitch_s"] - 2)}
    for l, (a, b) in zip((-120, -110, -100, -90), o["tone_segments"]): segs[str(l)] = (a + 3, b - 2)
    for sname, (a, b) in segs.items():
        Pm = P[a:b].mean(axis=0)
        for fi, v in zip(f, Pm): bench_spec.append([name, rx, sname, round(float(fi), 2), 10 * np.log10(v)])
kM = np.mean([cal["runs"][n]["k"] for n in ("Mini_1", "Mini_2")]); kH = cal["runs"]["HF"]["k"]
NM = np.mean([cal["runs"][n]["res"]["load"][0] for n in ("Mini_1", "Mini_2")]) - kM
NH = cal["runs"]["HF"]["res"]["load"][0] - kH
XM = np.mean([cal["runs"][n]["X_flightmetric_load"] for n in ("Mini_1", "Mini_2")]); XH = cal["runs"]["HF"]["X_flightmetric_load"]
cal.update(k_mini=kM, k_hf=kH, floor_mini_dBmHz=NM, floor_hf_dBmHz=NH, nf_mini_db=NM - KT0, nf_hf_db=NH - KT0,
           metric_load_mini=XM, metric_load_hf=XH, unit_offset_mini_minus_hf_db=kM - kH, kT0_dBmHz=KT0)
json.dump(cal, open(os.path.join(OUT, "bench_calibration.json"), "w"), indent=1, default=float)
with open(os.path.join(OUT, "bench_timelines.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["run", "receiver", "second", "band_floor_db_units_per_hz", "local_noise_db_units_per_hz", "tone_power_db_units"]); w.writerows(bench_rows)
with open(os.path.join(OUT, "bench_spectra.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["run", "receiver", "segment", "freq_offset_hz", "psd_db_units_per_hz"]); w.writerows(bench_spec)

# ---------- flights ----------
conv = lambda m, rx: (NM + (m - XM)) if rx == "mini" else (NH + (m - XH))
T = os.path.join(FTD, "2026-11-14-Rail-X_Ranch_Road/DRONE LOGS"); P0 = os.path.join(FTD, "2025-03-23-Ponui-Day8-Sun/DRONE_LOGS")
flights = [  # id, path, fs, rx, config, ground(s), steady(s)
 ("F2", f"{T}/Logs-Detectors-2026-11-14_17-31-39/data_record.4.1.bin", 3840, "hf", "Choke + 15 ft coax, ~170 ft, 30 s hover", (0, 9), (20, 135)),
 ("F3", f"{T}/Logs-Detectors-2026-11-14_17-40-15/data_record.4.1.bin", 3840, "hf", "Choke + 15 ft coax, ~170 ft", (0, 8), (18, 85)),
 ("F5", f"{T}/Logs-Detectors-2026-11-14_17-46-24/data_record.4.1.bin", 3840, "hf", "No choke + 15 ft coax, 50 ft", (0, 7), (18, 80)),
 ("F6", f"{T}/Logs-Detectors-2026-11-14_17-50-16/data_record.4.1.bin", 3840, "hf", "No choke, no extension, 50 ft", (0, 8), (16, 80)),
 ("F7", f"{T}/Logs-Detectors-2026-11-14_17-53-16/data_record.4.1.bin", 3840, "hf", "Choke, no extension, 50 ft", (0, 8), (20, 70)),
 ("P1", f"{P0}/Logs-Detectors-2025-03-22_04-17-55/data_record.24.1.bin", 3750, "mini", "Ponui flight 1 (old setup, Mini gain 20)", None, (30, 450)),
 ("P2", f"{P0}/Logs-Detectors-2025-03-22_04-34-33/data_record.24.1.bin", 3750, "mini", "Ponui flight 2 (old setup, Mini gain 20)", (0, 18), (30, 1050)),
 ("P3", f"{P0}/Logs-Detectors-2025-03-22_05-02-04/data_record.24.1.bin", 3750, "mini", "Ponui flight 3 (old setup, Mini gain 20)", (0, 18), (30, 600)),
]
own = {"mini": NM, "hf": NH}
summ = []; tl = []; sp = []
for fid, p, fs, rx, cfg, g, st in flights:
    fl = floor_timeline(p, fs); flc = [conv(v, rx) for v in fl]
    for t, (m, c) in enumerate(zip(fl, flc)): tl.append([fid, rx, t, round(float(m), 3), round(float(c), 3)])
    gm = float(np.median(flc[g[0]:g[1]])) if g else None; sm = float(np.median(flc[st[0]:st[1]]))
    summ.append([fid, rx, cfg, g, st, gm, sm, (gm - own[rx]) if g else None, sm - own[rx], (sm - gm) if g else None])
    # spectra (per-bin median over 1-s blocks of median-over-segments), converted with the same offset
    x = np.fromfile(p, dtype=np.complex64).astype(np.complex128); nfft = 256; nseg = int(fs) // nfft
    w = np.hanning(nfft); wn = (w ** 2).sum(); nb = len(x) // (nseg * nfft)
    X = np.abs(np.fft.fftshift(np.fft.fft(x[:nb * nseg * nfft].reshape(nb, nseg, nfft) * w, axis=2), axes=2)) ** 2 / (wn * fs)
    Pm = np.median(X, axis=1); f = np.fft.fftshift(np.fft.fftfreq(nfft, 1 / fs)); band = slice(int(0.1 * nfft), int(0.9 * nfft))
    off = (NM - XM) if rx == "mini" else (NH - XH)
    for segname, seg in (("ground", g), ("steady", st)):
        if not seg: continue
        s = 10 * np.log10(np.median(Pm[seg[0]:seg[1], band], axis=0)) + off
        for fi, v in zip(f[band], s): sp.append([fid, rx, segname, round(float(fi), 2), round(float(v), 3)])
with open(os.path.join(OUT, "flight_summary.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["flight", "receiver", "configuration", "ground_seconds", "steady_seconds", "ground_dBm_per_Hz", "steady_dBm_per_Hz", "ground_above_own_floor_db", "steady_above_own_floor_db", "rise_db"])
    for r in summ: w.writerow([r[0], r[1], r[2], "" if not r[3] else f"{r[3][0]}-{r[3][1]}", f"{r[4][0]}-{r[4][1]}"] + ["" if v is None else round(v, 2) for v in r[5:]])
with open(os.path.join(OUT, "flight_timelines.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["flight", "receiver", "second", "floor_metric_db_units", "floor_dBm_per_Hz"]); w.writerows(tl)
with open(os.path.join(OUT, "flight_spectra.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["flight", "receiver", "segment", "freq_offset_hz", "psd_dBm_per_Hz"]); w.writerows(sp)

# ---------- VNA ----------
V = os.path.join(HUB, "hardware/noise-reduction/tests/2026-11-17-vna-cables")
vna = [("thru", "thru_calibration_result_2026-11-17.s2p"), ("rg316_15ft", "rg316_15foot_extension_2026-11-17.s2p"),
       ("choke", "common_mode_choke_2026-11-17.s2p"), ("rg316_15ft+choke", "common_mode_choke_and_rg316_15foot_extension_2026-11-17.s2p"),
       ("rg316_88cm", "rg316_short_extension_2026-11-17.s2p"), ("rg316_88cm+choke", "common_mode_choke_and_rg316_short_extension_2026-11-17.s2p")]
with open(os.path.join(OUT, "vna.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["component", "freq_hz", "s21_db", "s11_db"])
    for name, fn in vna:
        d = np.loadtxt(os.path.join(V, fn), comments=["#", "!"])
        for r in d: w.writerow([name, int(r[0]), round(20 * np.log10(abs(r[3] + 1j * r[4])), 4), round(20 * np.log10(abs(r[1] + 1j * r[2])), 3)])
for r in summ: print(r[0], r[2], "ground", None if r[5] is None else round(r[5], 1), "steady", round(r[6], 1), "above own", round(r[8], 1))
print("NM", round(NM, 2), "NH", round(NH, 2), "NF", round(NM - KT0, 2), round(NH - KT0, 2), "kM-kH", round(kM - kH, 2))
