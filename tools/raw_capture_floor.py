#!/usr/bin/env python3
"""Noise floor from an airspy_rx raw capture (float32 IQ, `-t 0`), in the detector's units.

Emulates the Mini chain (airspy_rx 3 MS/s -> csdr fir_decimate_cc 8 -> airspy_channelize, 100
channels -> 3750 S/s) with an ideal unity-gain channel cut from a 1 s FFT. Both real stages have
unity passband gain (csdr normalises its taps to sum 1; the channelizer's prototype is
sinc(n/100)*window/100, also summing to 1), so the power density is unchanged and the result is
directly comparable with tools/noise_floor.py on a data_record file. Prints the floor at several
offsets from the tuned frequency, in reading dB and in dBm/Hz (Mini, gain-21 bench calibration).

Usage: raw_capture_floor.py airspy.1.dat [out.json]
Written 2026-11-19 for the Ponui cabin captures (hardware/noise-reduction/tests/).
"""
import sys, json, numpy as np
FS, FC, NFFT = 3_000_000, 3750, 256
NM, XM = -167.58, -109.36
OFFSETS = [-200e3, -100e3, -40e3, -20e3, -10e3, -5e3, 0, 5e3, 10e3, 20e3, 40e3, 100e3, 200e3]

def chan_floor(X, off_hz):
    N = len(X); idx = (np.arange(-FC // 2, FC // 2) + int(round(off_hz))) % N
    y = np.fft.ifft(np.fft.ifftshift(X[idx])) * (FC / N)
    nseg = FC // NFFT; w = np.hanning(NFFT); wn = (w ** 2).sum()
    s = y[: nseg * NFFT].reshape(nseg, NFFT)
    P = np.abs(np.fft.fftshift(np.fft.fft(s * w, axis=1), axes=1)) ** 2 / (wn * FC)
    return float(10 * np.log10(np.median(np.median(P, axis=0)[int(.1 * NFFT): int(.9 * NFFT)])))

def main(path, out=None):
    x = np.fromfile(path, dtype=np.complex64); nb = len(x) // FS
    res = {o: [] for o in OFFSETS}; wide = []
    for b in range(nb):
        X = np.fft.fft(x[b * FS:(b + 1) * FS].astype(np.complex128))
        for o in OFFSETS: res[o].append(chan_floor(X, o))
        P = np.abs(np.fft.fftshift(X)) ** 2 / FS / FS
        wide.append(10 * np.log10(np.median(P.reshape(3000, 1000), axis=1)))
    for o in OFFSETS:
        m = float(np.median(res[o][1:]))
        print(f"offset {o / 1e3:+7.1f} kHz  reading {m:7.2f} dB  {NM + (m - XM):7.2f} dBm/Hz")
    W = NM + (np.median(np.array(wide[1:]), axis=0) - XM)
    if out:
        json.dump({"file": path, "seconds": nb, "offset_hz_floor_dbm_hz": {str(int(o)): NM + (float(np.median(res[o][1:])) - XM) for o in OFFSETS},
                   "wideband_1kHz_dbm_hz": [round(float(v), 2) for v in W]}, open(out, "w"))

if __name__ == "__main__":
    main(*sys.argv[1:3])
