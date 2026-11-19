import json, csv, numpy as np, matplotlib, collections, os, sys
matplotlib.use("Agg"); import matplotlib.pyplot as plt
D=sys.argv[1]; OUT=sys.argv[2]
C=dict(blue="#2a78d6",orange="#eb6834",aqua="#1baf7a",yellow="#eda100",magenta="#e87ba4",green="#008300",violet="#6250d6",red="#e34948")
INK="#0b0b0b"; INK2="#52514e"; GRID="#e4e3df"; NEUT="#8a8984"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":9,"axes.edgecolor":NEUT,"axes.labelcolor":INK2,"xtick.color":INK2,"ytick.color":INK2,
  "axes.grid":True,"grid.color":GRID,"grid.linewidth":0.6,"axes.spines.top":False,"axes.spines.right":False,"lines.linewidth":1.6,
  "legend.frameon":False,"figure.dpi":150,"savefig.bbox":"tight","axes.titlesize":10,"axes.titleweight":"bold","axes.titlecolor":INK})
cal=json.load(open(f"{D}/bench_calibration.json")); NM,NH=cal["floor_mini_dBmHz"],cal["floor_hf_dBmHz"]; kM,kH=cal["k_mini"],cal["k_hf"]
def rd(fn): return list(csv.DictReader(open(f"{D}/{fn}")))
S={r["flight"]:r for r in rd("flight_summary.csv")}
TL=collections.defaultdict(list)
for r in rd("flight_timelines.csv"): TL[r["flight"]].append(float(r["floor_dBm_per_Hz"]))
SP=collections.defaultdict(lambda: ([],[]))
for r in rd("flight_spectra.csv"):
    k=(r["flight"],r["segment"]); SP[k][0].append(float(r["freq_offset_hz"])); SP[k][1].append(float(r["psd_dBm_per_Hz"]))
def save(fig,name): fig.savefig(f"{OUT}/{name}.pdf"); fig.savefig(f"{OUT}/{name}.png",dpi=160); plt.close(fig)
def floorline(ax,y,txt,x=1.0,ha="right"):
    ax.axhline(y,color=NEUT,lw=1,ls=(0,(4,3))); ax.text(x,y-0.5,txt,transform=ax.get_yaxis_transform(),ha=ha,va="top",fontsize=7.5,color=INK2)

# --- Fig 1: dumbbell, ground vs in flight (dBm/Hz)
rows=[("P2","Ponui 2025, old setup (Mini)"),("P3","Ponui 2025, old setup (Mini)"),("F6","No choke, no extension"),("F5","No choke, 15 ft coax"),("F7","Choke, no extension"),("F3","Choke + 15 ft coax"),("F2","Choke + 15 ft coax")]
fig,ax=plt.subplots(figsize=(6.6,3.3))
for i,(fid,lab) in enumerate(rows):
    g=float(S[fid]["ground_dBm_per_Hz"]); s=float(S[fid]["steady_dBm_per_Hz"])
    ax.plot([g,s],[i,i],color=GRID,lw=3,zorder=1,solid_capstyle="round")
    ax.scatter([g],[i],s=46,color=C["blue"],zorder=3,edgecolor="white",linewidth=1.2,label="On the ground, motors off" if i==0 else None)
    ax.scatter([s],[i],s=46,color=C["orange"],zorder=3,edgecolor="white",linewidth=1.2,label="In steady flight" if i==0 else None)
ax.set_yticks(range(len(rows))); ax.set_yticklabels([f"{lab}  [{fid}]" for fid,lab in rows],fontsize=8)
for x,t in ((NH,"HF+ own noise"),(NM,"Mini own noise")):
    ax.axvline(x,color=NEUT,lw=1,ls=(0,(4,3)))
ax.text(NH+0.3,len(rows)-0.45,"HF+ own noise\n−166.8",fontsize=7,color=INK2,va="top"); ax.text(NM-0.3,len(rows)-0.45,"Mini own noise\n−167.6",fontsize=7,color=INK2,va="top",ha="right")
ax.set_xlabel("Noise at the receiver input (dBm/Hz)"); ax.grid(axis="y",visible=False); ax.set_xlim(-170,-142)
ax.legend(loc="lower left",bbox_to_anchor=(0,1.0),ncol=2,fontsize=8,handletextpad=0.3)
save(fig,"fig1_dumbbell")

# --- Fig 2: timelines (dBm/Hz) small multiples
fig,axs=plt.subplots(3,1,figsize=(6.6,6.4),sharey=True)
panels=[("Ponui 2025, old setup, Airspy Mini",[("P2",C["blue"],"Flight 2"),("P3",C["orange"],"Flight 3")],NM,"Mini own noise"),
        ("2026-11-14, choke + 15 ft coax, HF+",[("F2",C["blue"],"Flight 2"),("F3",C["orange"],"Flight 3")],NH,"HF+ own noise"),
        ("2026-11-14, other configurations, HF+",[("F5",C["blue"],"F5 no choke, 15 ft"),("F7",C["orange"],"F7 choke, no ext."),("F6",C["aqua"],"F6 no choke, no ext.")],NH,"HF+ own noise")]
for ax,(title,ser,fl,ftxt) in zip(axs,panels):
    for fid,col,lab in ser: ax.plot(TL[fid],color=col,lw=1.1,label=lab)
    floorline(ax,fl,ftxt); ax.set_title(title,loc="left"); ax.set_ylabel("dBm/Hz"); ax.legend(loc="upper right",fontsize=7.5,ncol=3)
axs[-1].set_xlabel("Seconds from Start Detection"); axs[0].set_ylim(-172,-138)
fig.tight_layout(); save(fig,"fig2_timelines")

# --- Fig 3: spectra in steady flight
fig,ax=plt.subplots(figsize=(6.6,3.2))
for (fid,col,lab) in (("P3",C["blue"],"Ponui flight 3 (Mini)"),("F6",C["aqua"],"F6 no choke, no ext. (HF+)"),("F2",C["orange"],"F2 choke + 15 ft (HF+)")):
    f,v=SP[(fid,"steady")]; ax.plot(f,v,color=col,lw=1.2,label=lab)
    ax.text(-1540,np.median(v)+2.3,lab,fontsize=7.5,color=INK,ha="left")
floorline(ax,NH,"HF+ own noise",x=0.02,ha="left")
ax.set_xlabel("Frequency offset from 160.172 MHz (Hz)"); ax.set_ylabel("dBm/Hz"); ax.set_ylim(-172,-138)
save(fig,"fig3_spectra")

# --- Fig 4: bench linearity residual
fig,ax=plt.subplots(figsize=(4.6,2.6)); lv=np.array([-120,-110,-100,-90])
for name,col,lab,mk in (("Mini_1",C["blue"],"Mini, run 1","o"),("Mini_2",C["blue"],"Mini, run 2","s"),("HF",C["orange"],"HF+","D")):
    r=cal["runs"][name]; k=kM if name!="HF" else kH
    meas=np.array([r["res"][str(l)][2] for l in lv])-k; applied=lv-cal["path_loss_db"]
    ax.plot(lv,meas-applied,marker=mk,ms=5,color=col,lw=1.2,label=lab,mfc="white" if name=="Mini_2" else col)
ax.axhline(0,color=NEUT,lw=1); ax.set_xticks(lv); ax.set_xlabel("Generator setting (dBm)"); ax.set_ylabel("Measured − applied (dB)"); ax.set_ylim(-0.5,0.5)
ax.legend(fontsize=7.5,loc="lower left"); save(fig,"fig4_linearity")

# --- Fig 5: bench spectra near tone, input-referred
BS=collections.defaultdict(lambda: ([],[]))
for r in rd("bench_spectra.csv"):
    k=(r["run"],r["segment"]); BS[k][0].append(float(r["freq_offset_hz"])); BS[k][1].append(float(r["psd_db_units_per_hz"]))
ramp=["#9ec5f4","#5598e7","#256abf","#104281"]
fig,axs=plt.subplots(1,2,figsize=(6.6,2.9),sharey=True)
for ax,(run,k,title) in zip(axs,(("Mini_1",kM,"Airspy Mini (gain 21)"),("HF",kH,"Airspy HF+"))):
    for seg,col,lab in (("load",NEUT,"50 Ω load"),("-110",ramp[1],"−110 dBm tone"),("-100",ramp[2],"−100 dBm tone"),("-90",ramp[3],"−90 dBm tone")):
        f,v=BS[(run,seg)]; ax.plot(f,np.array(v)-k,color=col,lw=1.1,label=lab)
    ax.set_title(title,loc="left"); ax.set_xlim(-1500,1500); ax.set_xlabel("Offset from 160.172 MHz (Hz)")
axs[0].set_ylabel("dBm/Hz at receiver input"); axs[0].set_ylim(-172,-140); axs[1].legend(fontsize=7,loc="upper right")
fig.tight_layout(); save(fig,"fig5_desense")

# --- Fig 6: VNA insertion loss
V=collections.defaultdict(lambda: ([],[]))
for r in rd("vna.csv"): V[r["component"]][0].append(int(r["freq_hz"])/1e6); V[r["component"]][1].append(-float(r["s21_db"]))
fig,ax=plt.subplots(figsize=(6.0,2.8))
for comp,col,lab in (("rg316_15ft+choke",C["blue"],"15 ft RG-316 + choke"),("rg316_15ft",C["orange"],"15 ft RG-316"),("rg316_88cm+choke",C["aqua"],"88 cm RG-316 + choke (bench path)"),("choke",C["violet"],"Choke")):
    ax.plot(V[comp][0],V[comp][1],color=col,lw=1.4,label=lab)
ax.axvline(160,color=NEUT,lw=1,ls=(0,(4,3))); ax.set_xlabel("Frequency (MHz)"); ax.set_ylabel("Insertion loss as read (dB)"); ax.set_ylim(0,2); ax.legend(fontsize=7.5,loc="upper left")
save(fig,"fig6_vna")

# --- noise budget numbers + Fig 7
def fa_from_rise(nf,rise,loss_db):
    F=10**(nf/10); tot=F*10**(rise/10); ext_in=tot-(F-1); L=10**(loss_db/10)
    return 10*np.log10((ext_in-(1-1/L))*L), 10*np.log10(ext_in)
b={}
b["now"]=fa_from_rise(cal["nf_hf_db"],float(S["F2"]["steady_above_own_floor_db"])/1+0,1.8)  # steady above own floor ~ rise over receiver noise
b["ponui"]=fa_from_rise(cal["nf_mini_db"],float(S["P3"]["steady_above_own_floor_db"]),1.4)
itu={"City":(76.8,27.7),"Residential":(72.5,27.7),"Rural":(67.2,27.7),"Quiet rural":(53.6,28.6),"Galactic":(52.0,23.0)}
fam={k:c-d*np.log10(160.172) for k,(c,d) in itu.items()}
json.dump({"external_now_antenna_db":b["now"][0],"external_ponui_antenna_db":b["ponui"][0],"itu_fam_160MHz":fam},open(f"{OUT}/noise_budget.json","w"),indent=1)
fig,ax=plt.subplots(figsize=(6.0,2.6))
items=sorted(fam.items(),key=lambda x:x[1])
for i,(k,v) in enumerate(items): ax.scatter([v],[0],s=40,color=NEUT,zorder=3); ax.annotate(f"{k}\n{v:.0f} dB",(v,0),xytext=(0,9 if i%2==0 else -24),textcoords="offset points",ha="center",fontsize=7,color=INK2)
for y,(key,col,lab) in zip((1,2),(("now",C["orange"],"2026-11-14, choke + 15 ft (HF+)"),("ponui",C["blue"],"Ponui 2025 (Mini)"))):
    ax.scatter([b[key][0]],[y],s=60,color=col,zorder=3,edgecolor="white",linewidth=1.2); ax.text(b[key][0]+0.8,y,f"{lab}: {b[key][0]:.0f} dB",va="center",fontsize=7.5,color=INK)
ax.axvline(cal["nf_hf_db"],ymin=0.42,color=C["orange"],lw=1,ls=(0,(2,2))); ax.text(cal["nf_hf_db"]+0.3,2.6,"HF+ noise figure, 7.2 dB",fontsize=7,color=INK2)
ax.set_yticks([0,1,2]); ax.set_yticklabels(["ITU-R P.372\nmedians, 160 MHz","Measured","Measured"],fontsize=7.5); ax.set_ylim(-0.8,2.9)
ax.set_xlabel("Outside noise at the antenna, dB above thermal (kT₀)"); ax.grid(axis="y",visible=False); ax.set_xlim(-12,44)
save(fig,"fig7_budget")
print(json.dumps({"external_now":b["now"],"external_ponui":b["ponui"],"fam":fam},default=float,indent=0))
