import csv, json, sys, collections, datetime as dt, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
D=sys.argv[1]; OUT=sys.argv[2]
C=dict(blue="#2a78d6",orange="#eb6834",aqua="#1baf7a",yellow="#eda100",violet="#6250d6",red="#e34948")
INK="#0b0b0b"; INK2="#52514e"; GRID="#e4e3df"; NEUT="#8a8984"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":9,"axes.edgecolor":NEUT,"axes.labelcolor":INK2,"xtick.color":INK2,"ytick.color":INK2,
  "axes.grid":True,"grid.color":GRID,"grid.linewidth":0.6,"axes.spines.top":False,"axes.spines.right":False,"lines.linewidth":1.4,
  "legend.frameon":False,"figure.dpi":150,"savefig.bbox":"tight","axes.titlesize":10,"axes.titleweight":"bold","axes.titlecolor":INK})
F=collections.defaultdict(list)
for r in csv.DictReader(open(f"{D}/pulse_noise.csv")):
    F[r["file"]].append((float(r["t"]),float(r["z"]),float(r["dbm_hz"]),float(r["lat"])))
def nz(fn):
    u=dt.datetime.strptime(fn[6:25],"%Y-%m-%d-%H-%M-%S"); return u+dt.timedelta(hours=13)
fig,axs=plt.subplots(3,1,figsize=(7.2,9.6),gridspec_kw=dict(height_ratios=[1.05,1.1,0.95],hspace=0.45))
# A: in-flight median per flight
ax=axs[0]; xs=[]; labs=[]; i=0
for fn in sorted(F):
    a=np.array(F[fn]); air=a[a[:,1]>10,2]; wg=a[0,3]<-40
    if fn.startswith("Pulse-2025-03-16-22-26"): air=a[:,2]   # in the air (z -39..-36 relative to a higher takeoff point)
    if len(air)<4: continue
    m=np.median(air); col=C["orange"] if wg else (NEUT if len(air)<8 and fn<"Pulse-2025-03-18" else C["blue"])
    ax.errorbar(i,m,yerr=[[m-np.percentile(air,10)],[np.percentile(air,90)-m]],fmt="o",color=col,ms=5,capsize=0,lw=1,mfc=col if len(air)>=8 else "white")
    t=nz(fn); labs.append(t.strftime("%a %d\n%H:%M")); xs.append(i); i+=1
ax.set_xticks(xs,labs,fontsize=6.3); ax.set_ylabel("dBm/Hz at receiver input")
ax.set_ylim(-170,-128)
for y,t in ((-167.6,"Mini's own noise"),(-158.4,"Cumbria Nov 2025, Mini + choke, in shield"),(-163.5,"Nov 2026, HF+ + choke + ferrites")):
    ax.axhline(y,color=NEUT,lw=0.9,ls=(0,(4,3))); ax.text(len(xs)-0.6,y+0.4,t,ha="right",va="bottom",fontsize=7,color=INK2)
ax.text(1.4,-129.5,"Wellington test flights, no ferrites on the USB cable",color=C["orange"],fontsize=7.5,va="top")
ax.text(2.25,-131.6,"Ponui Mon 17: 5 weak pulses only",color=NEUT,fontsize=7,va="top")
ax.text(len(xs)-1,-139.2,"Ponui, Tue 18 to Sun 23; ferrites on the USB cable by Sun 23",color=C["blue"],fontsize=7.5,ha="right")
ax.set_title("A. In-flight noise, every flight with detections, March 2025 (median, 10-90% bar; NZDT)",loc="left")
# B: timelines
ax=axs[1]
for fn,col,lab in (("Pulse-2025-03-14-22-41-44-356.csv",C["orange"],"Wellington, Sat 15, no USB ferrites"),("Pulse-2025-03-19-21-11-08-338.csv",C["blue"],"Ponui, Thu 20")):
    a=np.array(sorted(F[fn])); t=a[:,0]-a[0,0]; ax.plot(t,a[:,2],".",ms=3,color=col,label=lab)
ax.axhline(-167.6,color=NEUT,lw=0.9,ls=(0,(4,3))); ax.text(1,-167.2,"Mini's own noise",transform=ax.get_yaxis_transform(),ha="right",va="bottom",fontsize=7,color=INK2)
ax.annotate("motors start,\nstill on the ground",xy=(70,-147),xytext=(110,-158),fontsize=7,color=INK2,arrowprops=dict(arrowstyle="-",color=NEUT,lw=0.8))
ax.set_xlabel("seconds from first logged pulse"); ax.set_ylabel("dBm/Hz"); ax.set_ylim(-172,-128); ax.legend(loc="upper right",fontsize=7.5)
ax.set_title("B. Noise per detected pulse through two flights",loc="left")
# C: cabin captures
ax=axs[2]; f=np.arange(-1500,1500)+0.5
for k,col,lab in (("08-18-10",C["violet"],"capture 1"),("09-07-36",C["aqua"],"capture 2 (49 min later)")):
    W=np.array(json.load(open(f"{D}/cabin_capture_{k}.json"))["wideband_1kHz_dbm_hz"]); ax.plot(f,W,color=col,lw=0.8,label=lab)
ax.axhline(-167.6,color=NEUT,lw=0.9,ls=(0,(4,3)))
ax.set_xlabel("kHz from 160.401 MHz"); ax.set_ylabel("dBm/Hz (1 kHz median)"); ax.set_xlim(-1500,1500); ax.set_ylim(-170,-125); ax.legend(loc="lower center",fontsize=7.5,ncol=2)
ax.set_title("C. Cabin captures, motors off, antenna on railing 3-5 m from the drone",loc="left")
fig.savefig(f"{OUT}/ponui_trip.png",dpi=160); fig.savefig(f"{OUT}/ponui_trip.pdf")
