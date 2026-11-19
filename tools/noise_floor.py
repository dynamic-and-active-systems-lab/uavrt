#!/usr/bin/env python3
"""Background noise floor from a uavrt_detection IQ recording (data_record.<id>.1.bin).

The recording is raw complex float32 IQ with no timestamps, at the detector's sample rate
(3840 S/s for the Airspy HF+, 3750 S/s for the Airspy Mini). For each 1 s block this takes
256-point Hann-windowed spectra, the median across the spectra in the block (which drops brief
tag pulses), then the median across the inner 80 % of the band. Output is dB relative to the
receiver's own units: compare values from the same receiver only, or compare rises relative to
each recording's own motors-off reference.

Usage: noise_floor.py <data_record.bin> <sample_rate> [out.csv]
Written 2026-11-14 for the Rail-X Ranch Road noise flights; see hardware/measurements/.
"""
import sys, numpy as np

def floor_timeline(path, fs, nfft=256, block_s=1.0):
    x = np.fromfile(path, dtype=np.complex64).astype(np.complex128)
    nseg = int(fs * block_s) // nfft
    w = np.hanning(nfft); wn = (w ** 2).sum()
    nb = len(x) // (nseg * nfft)
    x = x[: nb * nseg * nfft].reshape(nb, nseg, nfft)
    P = np.abs(np.fft.fftshift(np.fft.fft(x * w, axis=2), axes=2)) ** 2 / (wn * fs)
    band = np.median(P, axis=1)[:, int(0.1 * nfft): int(0.9 * nfft)]
    return 10 * np.log10(np.median(band, axis=1))

if __name__ == "__main__":
    fl = floor_timeline(sys.argv[1], float(sys.argv[2]))
    if len(sys.argv) > 3:
        np.savetxt(sys.argv[3], np.c_[np.arange(len(fl)), fl], delimiter=",", header="second,floor_db", comments="")
    q = np.percentile(fl, [5, 50, 95])
    print(f"{len(fl)} s  floor dB p5={q[0]:.1f} median={q[1]:.1f} p95={q[2]:.1f}")
