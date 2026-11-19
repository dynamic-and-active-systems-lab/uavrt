#!/usr/bin/env python3
"""In-flight noise floor from TagTracker pulse logs (Pulse-*.csv), no IQ recording needed.

Every pulse uavrt_detection reports carries its noise estimate for the channel (`noise_psd`, the
11th field), in the same digital units as the IQ recording. TagTracker logs it with the aircraft's
position, so any past flight with detections has a noise timeline at about one point per pulse.

Conversion to dBm/Hz at the receiver input (Airspy Mini, bench calibration of 2026-11-18, gain 21):
    dBm/Hz = 10*log10(noise_psd) - 59.81
-59.81 = (-167.58 dBm/Hz) - (-109.36 + 1.59): the bench floor, the median-based reading of
tools/noise_floor.py on the 50-ohm load, and the 1.59 dB by which a median of exponential power
readings sits below their mean (noise_psd is a mean). Checked against the IQ recordings of Ponui
Day 8 flights 2 and 3: agrees within 0.1 dB. For the Airspy HF+ use -59.81 - 35.7 (unchecked).

Usage: pulse_log_noise.py [--offset DB] [--csv out.csv] Pulse-*.csv ...
Prints one line per log: pulses, position, height range, median floor on the ground (|z|<2 m) and
above 10 m. Written 2026-11-19 for the Ponui trip review (hardware/noise-reduction/tests/).
"""
import sys, os, csv, numpy as np

def read(path, offset):
    rows = [l.split(',') for l in open(path) if l.strip() and not l.startswith('#')]
    out = []
    for r in rows:
        out.append(dict(file=os.path.basename(path), t=float(r[3]), tag=int(r[1]), freq_hz=int(float(r[2])),
                        snr=float(r[5]), noise_psd=float(r[10]), lat=float(r[13]), lon=float(r[14]),
                        z=float(r[15]), dbm_hz=10 * np.log10(float(r[10])) + offset))
    return sorted(out, key=lambda d: d['t'])

def main(argv):
    offset, out_csv, files = -59.81, None, []
    it = iter(argv)
    for a in it:
        if a == '--offset': offset = float(next(it))
        elif a == '--csv': out_csv = next(it)
        else: files.append(a)
    allrows = []
    for f in files:
        d = read(f, offset)
        if not d: continue
        allrows += d
        n = np.array([x['dbm_hz'] for x in d]); z = np.array([x['z'] for x in d])
        g, air = n[np.abs(z) < 2], n[z > 10]
        med = lambda v: f"{np.median(v):7.1f}" if len(v) else "    —  "
        print(f"{os.path.basename(f):38s} n={len(d):4d} ({np.median([x['lat'] for x in d]):.3f},"
              f"{np.median([x['lon'] for x in d]):.3f}) z {z.min():4.0f}..{z.max():4.0f}  "
              f"ground {med(g)} (n={len(g)})  >10 m {med(air)} (n={len(air)})  dBm/Hz")
    if out_csv and allrows:
        with open(out_csv, 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(allrows[0].keys())); w.writeheader(); w.writerows(allrows)

if __name__ == '__main__':
    main(sys.argv[1:])
