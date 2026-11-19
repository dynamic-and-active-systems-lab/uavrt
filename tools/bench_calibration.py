#!/usr/bin/env python3
"""Signal-generator calibration of a uavrt_detection IQ recording (data_record.<id>.1.bin).

Finds the tone steps and the termination/RF-off swap automatically, then reports per segment the
noise PSD near the tone (receiver units/Hz) and the tone power (receiver units). Written 2026-11-18
for the Mini vs HF+ office test; see hardware/measurements/2026-11-18/.
Usage: bench_calibration.py "name|path|sample_rate" [...]
"""
import numpy as np, sys, json, os
def psd_blocks(path, fs, nfft=256, block_s=1.0):
    x=np.fromfile(path,dtype=np.complex64).astype(np.complex128)
    nseg=int(fs*block_s)//nfft; w=np.hanning(nfft); wn=(w**2).sum()
    nb=len(x)//(nseg*nfft); x=x[:nb*nseg*nfft].reshape(nb,nseg,nfft)
    P=np.abs(np.fft.fftshift(np.fft.fft(x*w,axis=2),axes=2))**2/(wn*fs)
    f=np.fft.fftshift(np.fft.fftfreq(nfft,1/fs))
    return P.mean(axis=1), f   # mean PSD per 1-s block, units^2/Hz
def analyse(path, fs, name):
    P,f=psd_blocks(path,fs); df=f[1]-f[0]; nb=len(P)
    inner=abs(f)<0.4*fs
    fl=10*np.log10(np.median(P[:,inner],axis=1))
    tb=(f>150)&(f<850)
    pk=10*np.log10(P[:,tb].max(axis=1))
    tone=pk>fl+20
    # tone segments: split at jumps >5 dB
    segs=[]; t=0
    while t<nb:
        if tone[t]:
            s=t
            while t+1<nb and tone[t+1] and abs(pk[t+1]-pk[t])<5: t+=1
            segs.append((s,t))
        t+=1
    # keep segments longer than 20 s
    segs=[s for s in segs if s[1]-s[0]>20]
    first_tone=segs[0][0]
    # no-tone portion before first tone; find swap glitch: largest |floor-median| in it
    pre=np.arange(0,first_tone)
    med=np.median(fl[pre]); dev=abs(fl[pre]-med)
    cand=pre[(pre>10)&(pre<first_tone-10)]
    g=cand[np.argmax(dev[cand])] if len(cand) else None
    out={"name":name,"fs":fs,"n_s":nb,"glitch_s":int(g) if g is not None else None,"dev_db":float(dev[g]) if g is not None else None,
         "tone_segments":[(int(a),int(b)) for a,b in segs]}
    # tone frequency from strongest segment
    a,b=segs[-1]; Pm=P[a+3:b-2].mean(axis=0); ftone=f[tb][Pm[tb].argmax()]; out["tone_hz"]=float(ftone)
    k_t=np.argmin(abs(f-ftone))
    excl=np.zeros_like(f,bool); excl[max(0,k_t-6):k_t+7]=True
    local=(abs(f-ftone)<600)&~excl&inner
    band=inner&~excl
    def seg_stats(a,b):
        Pm=P[a:b].mean(axis=0)
        Nl=np.median(Pm[local]); Nb=np.median(Pm[band])
        S=((Pm[k_t-5:k_t+6]-Nl).sum())*df
        # also my flight-style metric: median over bins of per-block median-over-segments is not available here; use median-over-blocks per bin then median over inner
        return Nl,Nb,S
    res={}
    names=["load","rf_off"]
    if g is not None:
        res["load"]=seg_stats(3,g-2); res["rf_off"]=seg_stats(g+3,first_tone-2)
    for lvl,(a,b) in zip([-120,-110,-100,-90],segs):
        res[str(lvl)]=seg_stats(a+3,b-2)
    out["res"]={k:[float(10*np.log10(v[0])),float(10*np.log10(v[1])),(float(10*np.log10(v[2])) if v[2]>0 else None)] for k,v in res.items()}
    return out
if __name__=="__main__":
    allo=[]
    for spec in sys.argv[1:]:
        name,path,fs=spec.split("|"); o=analyse(path,float(fs),name); allo.append(o)
        print(f"== {name}: {o['n_s']} s, swap glitch at {o['glitch_s']} s ({o['dev_db']:.1f} dB), tone segs {o['tone_segments']}, tone at {o['tone_hz']:.0f} Hz")
        for k,(nl,nb,s) in o["res"].items(): print(f"   {k:7s} local noise {nl:7.2f} dB/Hz  band noise {nb:7.2f}  tone {s if s is None else round(s,2)}")
    json.dump(allo,open(__import__("os").path.expanduser("~/scr/bench_results.json"),"w"),indent=1)
