# Day 2 stage medians. Usage: day2_stages.py <hub>/tools <2025-03-17-Ponui-Day2-Mon/DRONE LOGS/2025-03-17-Ponui-Monday> day2_floors.json
import sys, json, numpy as np
sys.path.insert(0, sys.argv[1]); from noise_floor import floor_timeline
NM=-167.58; XM=-109.36
B=sys.argv[2]
S={"10-27-47":[("ground before",0,40),("flight",47,150),("ground after",170,216)],
   "10-40-21":[("ground before",0,20),("flight",26,97)],
   "10-42-26":[("flight (started in the air)",0,330),("descent/landing",330,365),("ground after",368,390)],
   "11-21-50":[("ground before",0,30),("flight",32,368)]}
ch={"10-27-47":4,"10-40-21":4,"10-42-26":4,"11-21-50":5}
out={}
for k,st in S.items():
    d=NM+(floor_timeline(f"{B}/Logs-Detectors-2025-03-15_{k}/data_record.{ch[k]}.1.bin",3750.0)-XM)
    out[k]={"per_second_dBm_Hz":[round(float(v),2) for v in d],"stages":{}}
    for name,a,b in st:
        m=float(np.median(d[a:b])); out[k]["stages"][name]=[a,b,round(m,1)]
        print(f"{k} {name:28s} s{a:3d}-{b:3d}  {m:7.1f} dBm/Hz")
json.dump(out,open(sys.argv[3],"w"))
