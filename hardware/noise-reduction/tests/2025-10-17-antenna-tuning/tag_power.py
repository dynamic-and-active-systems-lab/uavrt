# Tag pulse power per second from a Mini data_record (dBm at the receiver input, gain-21 calibration).
# Usage: tag_power.py data_record.36.1.bin ...   Written 2026-11-20 for the 2025-10-17 antenna A/B.
import sys, numpy as np
NM=-167.58; XM=-109.36   # Mini gain 21: dBm/Hz = NM + (reading - XM); reading = 10log10(P per Hz)
fs=3750.0
def run(path, f0=-33.0):
    x=np.fromfile(path,dtype=np.complex64).astype(np.complex128)
    N=64; w=np.hanning(N); nb=len(x)//3750
    out=[]
    for b in range(nb):
        s=x[b*3750:(b+1)*3750]; segs=s[:len(s)//N*N].reshape(-1,N)
        # pulse power: total power in a +-90 Hz band around the tag, per 17 ms segment, minus floor estimate
        X=np.fft.fftshift(np.fft.fft(segs*w,axis=1),axes=1); f=np.fft.fftshift(np.fft.fftfreq(N,1/fs))
        P=np.abs(X)**2/(fs*(w**2).sum())          # per Hz
        band=np.abs(f-f0)<=90; df=fs/N
        floor=np.median(P[:,np.abs(f-f0)>300])     # per-Hz floor in this second
        sig=(P[:,band]-floor).sum(axis=1)*df       # W-equivalent per segment
        k=np.argmax(sig); pk=sig[k]
        out.append((b, 10*np.log10(max(pk,1e-30)) - XM + NM, NM+(10*np.log10(floor)-XM)))
    return out
for p in sys.argv[1:]:
    o=run(p); print('==',p)
    print(' '.join(f"{int(s) if s>-150 else '.'}" for _,s,_ in o))
