"""Figure for tests/2025-03-ponui-usb-ferrites. Usage: fig_trip.py <this test folder> <noise-reduction/data> <out dir>"""
import csv, json, sys, collections, datetime as dt, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
D, DATA, OUT = sys.argv[1:4]
C=dict(blue="#2a78d6",orange="#eb6834",red="#e34948")
INK="#0b0b0b"; INK2="#52514e"; GRID="#e4e3df"; NEUT="#8a8984"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":9,"axes.edgecolor":NEUT,"axes.labelcolor":INK2,"xtick.color":INK2,"ytick.color":INK2,
  "axes.grid":True,"grid.color":GRID,"grid.linewidth":0.6,"axes.spines.top":False,"axes.spines.right":False,"lines.linewidth":1.4,
  "legend.frameon":False,"figure.dpi":150,"savefig.bbox":"tight","axes.titlesize":10,"axes.titleweight":"bold","axes.titlecolor":INK})
OWN=-167.6
F=collections.defaultdict(list)
for r in csv.DictReader(open(f"{D}/pulse_noise.csv")):
    F[r["file"]].append((float(r["t"]),float(r["z"]),float(r["dbm_hz"]),float(r["lat"])))
d2=json.load(open(f"{D}/day2_floors.json"))
nz=lambda fn: dt.datetime.strptime(fn[6:25],"%Y-%m-%d-%H-%M-%S")+dt.timedelta(hours=13)
pts=[]  # (label, values, colour, filled)
for fn in sorted(F):
    a=np.array(F[fn]); air=a[a[:,1]>10,2]
    if a[0,3]<-40 and len(air)>=4: pts.append((nz(fn).strftime("%a %d %H:%M"),air,C["orange"],True))
for k in ("10-27-47","10-40-21","10-42-26","11-21-50"):
    st=d2[k]["stages"]; key=[s for s in st if s.startswith("flight")][0]; a,b,_=st[key]
    pts.append((f"Mon 17 flight {len([p for p in pts if p[0].startswith('Mon')])+1}",np.array(d2[k]["per_second_dBm_Hz"][a:b]),C["red"],True))
for fn in sorted(F):
    a=np.array(F[fn]); air=a[a[:,1]>10,2]
    if a[0,3]>-40 and fn>"Pulse-2025-03-18" and len(air)>=4: pts.append((nz(fn).strftime("%a %d %H:%M"),air,C["blue"],len(air)>=8))
fig,axs=plt.subplots(2,1,figsize=(7.4,7.6),gridspec_kw=dict(height_ratios=[1.05,1],hspace=0.5))
ax=axs[0]
for i,(lab,v,col,fill) in enumerate(pts):
    m=np.median(v); ax.errorbar(i,m,yerr=[[m-np.percentile(v,10)],[np.percentile(v,90)-m]],fmt="o",color=col,ms=5,lw=1,mfc=col if fill else "white")
ax.set_xticks(range(len(pts)),[p[0] for p in pts],fontsize=6.5,rotation=60,ha="right",rotation_mode="anchor"); ax.set_ylabel("dBm/Hz at receiver input"); ax.set_ylim(-170,-128)
ax.axvline(5.5,color=INK2,lw=0.9); ax.text(5.65,-160,"Tue 18, rain: cabin tests\nshow the USB ferrites help;\nfitted from here on",ha="left",va="center",fontsize=6.8,color=INK2)
ax.axhline(OWN,color=NEUT,lw=0.9,ls=(0,(4,3))); ax.text(len(pts)-0.5,OWN+0.4,"Mini's own noise",ha="right",va="bottom",fontsize=7,color=INK2)
ax.text(0,-130,"No ferrites on the USB cable",color=C["red"],fontsize=7.5); ax.text(len(pts)-0.5,-139.5,"Two snap-on ferrites on the USB cable",color=C["blue"],fontsize=7.5,ha="right")
ax.text(0,-132.6,"orange: Wellington test flights, from pulse logs; red: Ponui Day 2, from IQ recordings",color=INK2,fontsize=6.5)
ax.set_title("A. In-flight noise, every flight with data, March 2025 (median, 10-90% bar; NZDT)",loc="left")
ax=axs[1]
v=np.array(d2["11-21-50"]["per_second_dBm_Hz"]); ax.plot(np.arange(len(v)),v,color=C["red"],label="Mon 17, Day 2: no ferrites on the USB cable")
P=[float(r["floor_dBm_per_Hz"]) for r in csv.DictReader(open(f"{DATA}/flight_timelines.csv")) if r["flight"]=="P3"]
ax.plot(np.arange(len(P)),P,color=C["blue"],label="Sun 23, Day 8 (flight P3): with the ferrites")
ax.axhline(OWN,color=NEUT,lw=0.9,ls=(0,(4,3))); ax.text(1,OWN+0.4,"Mini's own noise",transform=ax.get_yaxis_transform(),ha="right",va="bottom",fontsize=7,color=INK2)
for xy in ((12,-143.5),(10,-162.3)): ax.annotate("",xy=xy,xytext=(70,-153),arrowprops=dict(arrowstyle="-",color=NEUT,lw=0.8))
ax.text(72,-153,"on the ground, motors off",fontsize=7,color=INK2,va="center")
ax.set_xlim(0,max(len(v),len(P))); ax.set_ylim(-170,-128); ax.set_xlabel("seconds from start of recording"); ax.set_ylabel("dBm/Hz")
ax.legend(loc="upper right",fontsize=7.5); ax.set_title("B. Noise through one flight on each day, from the IQ recordings",loc="left")
fig.savefig(f"{OUT}/ponui_trip.png",dpi=160)
