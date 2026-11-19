(function(){
const D = JSON.parse(document.getElementById('report-data').textContent);
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const NS = 'http://www.w3.org/2000/svg';
const el = (tag, attrs={}, parent) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; };
const fmt = (v, d=1) => (v>0?'+':'') + v.toFixed(d);
const NM = D.cal.floor_mini_dBmHz, NH = D.cal.floor_hf_dBmHz;

// Fixed colour per flight (identity follows the flight, never its rank)
const FL = {
  F2:{c:'--s1',lab:'F2 choke + 15 ft'}, F3:{c:'--s2',lab:'F3 choke + 15 ft'}, F5:{c:'--s3',lab:'F5 no choke, 15 ft'},
  F6:{c:'--s4',lab:'F6 no choke, no ext.'}, F7:{c:'--s5',lab:'F7 choke, no ext.'}, P1:{c:'--s6',lab:'Ponui 1 (Mini)'},
  P2:{c:'--s7',lab:'Ponui 2 (Mini)'}, P3:{c:'--s8',lab:'Ponui 3 (Mini)'},
  D2:{c:'--s2',lab:'Ponui Day 2, no USB ferrites'}, C1:{c:'--s3',lab:'Cumbria 1 (173 MHz)'}, C2:{c:'--s4',lab:'Cumbria 2 (173 MHz)'}
};
const isMini = k => k[0]==='P'||k[0]==='D'||k[0]==='C';

function makeTip(host){ let t = host.querySelector('.tip'); if(!t){ t = document.createElement('div'); t.className='tip'; t.hidden=true; host.appendChild(t);} return t; }
function placeTip(host, tip, x, y){ const w = host.clientWidth; tip.hidden=false; const tw = tip.offsetWidth; let left = x + 14; if (left + tw > w) left = x - tw - 14; tip.style.left = Math.max(0,left)+'px'; tip.style.top = Math.max(0, y - 10)+'px'; }

// Generic line chart with one y-axis, crosshair + tooltip
function lineChart(host, o){
  host.innerHTML=''; if(o.legend){ const lg=document.createElement('div'); lg.className='controls'; lg.style.marginBottom='6px'; lg.innerHTML=o.series.map(s=>`<span style="font-size:13px;color:var(--ink2);display:inline-flex;align-items:center;gap:6px"><span style="width:14px;height:3px;border-radius:2px;background:${s.color}"></span>${s.name}</span>`).join(''); host.appendChild(lg); } const W = Math.max(300, host.clientWidth), H = o.height || Math.round(Math.min(380, Math.max(240, W*0.42)));
  const m = {l:52, r:16, t:12, b:40};
  const svg = el('svg',{viewBox:`0 0 ${W} ${H}`, role:'img', 'aria-label':o.aria||''}, host);
  const xs = o.series.flatMap(s=>s.x), xmin = o.xmin ?? Math.min(...xs), xmax = o.xmax ?? Math.max(...xs);
  const X = v => m.l + (v - xmin)/(xmax - xmin) * (W - m.l - m.r);
  const Y = v => m.t + (o.ymax - v)/(o.ymax - o.ymin) * (H - m.t - m.b);
  for (let v = o.ymin; v <= o.ymax + 1e-9; v += o.ystep){ el('line',{x1:m.l,x2:W-m.r,y1:Y(v),y2:Y(v),class:'gridl'},svg); const t=el('text',{x:m.l-8,y:Y(v)+4,'text-anchor':'end'},svg); t.textContent=v; }
  const xt = o.xticks || niceTicks(xmin,xmax,6);
  xt.forEach(v=>{ const t=el('text',{x:X(v),y:H-m.b+16,'text-anchor':'middle'},svg); t.textContent=o.xfmt?o.xfmt(v):v; });
  el('line',{x1:m.l,x2:W-m.r,y1:H-m.b,y2:H-m.b,stroke:css('--neutral')},svg);
  const xl=el('text',{x:(m.l+W-m.r)/2,y:H-4,'text-anchor':'middle'},svg); xl.textContent=o.xlabel;
  const yl=el('text',{x:12,y:(m.t+H-m.b)/2,'text-anchor':'middle',transform:`rotate(-90 12 ${(m.t+H-m.b)/2})`},svg); yl.textContent=o.ylabel;
  (o.refs||[]).slice().sort((a,b)=>b.y-a.y).forEach((r,i)=>{ el('line',{x1:m.l,x2:W-m.r,y1:Y(r.y),y2:Y(r.y),stroke:css('--neutral'),'stroke-dasharray':'4 3'},svg); const t=el('text',{x:W-m.r-4,y:Y(r.y)+(i===0?-5:13),'text-anchor':'end'},svg); t.textContent=r.label; });
  o.series.forEach(s=>{ let d=''; s.x.forEach((xv,i)=>{ const yv=Math.max(o.ymin,Math.min(o.ymax,s.y[i])); d += (i?'L':'M')+X(xv).toFixed(1)+','+Y(yv).toFixed(1); });
    el('path',{d, fill:'none', stroke:s.color, 'stroke-width':s.width||1.6, 'stroke-linejoin':'round'},svg); });
  const cross = el('line',{y1:m.t,y2:H-m.b,stroke:css('--ink3'),'stroke-width':1,visibility:'hidden'},svg);
  const tip = makeTip(host);
  const hit = el('rect',{x:m.l,y:m.t,width:W-m.l-m.r,height:H-m.t-m.b,fill:'transparent'},svg);
  const move = ev => { const r = svg.getBoundingClientRect(); const sx = (ev.clientX - r.left) * W / r.width; const xv = xmin + (sx - m.l)/(W-m.l-m.r)*(xmax-xmin);
    cross.setAttribute('x1',sx); cross.setAttribute('x2',sx); cross.setAttribute('visibility','visible');
    let html = `<div style="color:var(--ink2);margin-bottom:3px">${o.xname}: ${o.xfmt?o.xfmt(Math.round(xv)):Math.round(xv)}</div>`;
    o.series.forEach(s=>{ let bi=0,bd=1e9; s.x.forEach((v,i)=>{ const dd=Math.abs(v-xv); if(dd<bd){bd=dd;bi=i;} }); if (bd <= (o.snap||Infinity)) html += `<div><span class="k" style="background:${s.color}"></span>${s.name}: <b class="num">${s.y[bi].toFixed(1)}</b> ${o.unit||''}</div>`; });
    tip.innerHTML = html; placeTip(host, tip, (ev.clientX - r.left), (ev.clientY - r.top)); };
  hit.addEventListener('pointermove', move); hit.addEventListener('pointerleave', ()=>{ tip.hidden=true; cross.setAttribute('visibility','hidden'); });
}
function niceTicks(a,b,n){ const span=b-a, step0=span/n, p=Math.pow(10,Math.floor(Math.log10(step0))), f=step0/p; const step=(f<1.5?1:f<3?2:f<7?5:10)*p; const out=[]; for(let v=Math.ceil(a/step)*step; v<=b+1e-9; v+=step) out.push(+v.toFixed(6)); return out; }

function chips(host, keys, state, onChange){ host.innerHTML=''; keys.forEach(k=>{ const b=document.createElement('button'); b.className='chip'; b.type='button'; b.id='chip-'+host.id+'-'+k; b.style.setProperty('--c', `var(${FL[k].c})`); b.setAttribute('aria-pressed', state.has(k)?'true':'false'); b.innerHTML=`<span class="sw"></span>${FL[k].lab}`; b.onclick=()=>{ state.has(k)?state.delete(k):state.add(k); b.setAttribute('aria-pressed', state.has(k)?'true':'false'); onChange(); }; host.appendChild(b); }); }
function seg(host, onChange){ host.querySelectorAll('button').forEach(b=> b.onclick=()=>{ host.querySelectorAll('button').forEach(x=>x.setAttribute('aria-pressed','false')); b.setAttribute('aria-pressed','true'); onChange(b.dataset.v); }); return host.querySelector('[aria-pressed="true"]').dataset.v; }

// ---- Dumbbell
const DL={F2:'Choke + 15 ft coax',F3:'Choke + 15 ft coax',F7:'Choke, no extension',F5:'No choke, 15 ft coax',F6:'No choke, no extension',C2:'Cumbria, Mini in shield + choke',C1:'Cumbria, Mini in shield + choke',P3:'Ponui Day 8, USB ferrites (Mini)',P2:'Ponui Day 8, USB ferrites (Mini)',D2:'Ponui Day 2, no USB ferrites (Mini)'};
function dumbbell(){
  const host=document.getElementById('dumbbell'); host.innerHTML='';
  const rows=['F2','F3','F7','F5','F6','C2','C1','P3','P2','D2']; const S=D.summary;
  const W=Math.max(320,host.clientWidth), narrow=W<560, rh=34, m={l:narrow?70:200,r:18,t:52,b:40}, H=m.t+m.b+rh*rows.length;
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,role:'img','aria-label':'Ground and flight noise per configuration'},host);
  const xmin=-170,xmax=-132, X=v=>m.l+(v-xmin)/(xmax-xmin)*(W-m.l-m.r);
  for(let v=xmin; v<=xmax; v+=5){ el('line',{x1:X(v),x2:X(v),y1:m.t-6,y2:H-m.b,class:'gridl'},svg); const t=el('text',{x:X(v),y:H-m.b+16,'text-anchor':'middle'},svg); t.textContent=v; }
  const xl=el('text',{x:(m.l+W-m.r)/2,y:H-4,'text-anchor':'middle'},svg); xl.textContent='Noise at the receiver input (dBm/Hz)';
  [[NM,'Mini own',-1],[NH,'HF+ own',1]].forEach(([v,lab,dir])=>{ el('line',{x1:X(v),x2:X(v),y1:m.t-6,y2:H-m.b,stroke:css('--neutral'),'stroke-dasharray':'4 3'},svg); const t=el('text',{x:X(v)+dir*4,y:m.t-10,'text-anchor':dir<0?'end':'start'},svg); t.textContent=lab; });
  const tip=makeTip(host);
  const cg=css('--s1'), cf=css('--s2');
  // legend
  [[cg,'Ground, motors off'],[cf,'Steady flight']].forEach(([c,t],i)=>{ const x=m.l+ i*150; el('circle',{cx:x+5,cy:10,r:5,fill:c},svg); const tx=el('text',{x:x+15,y:14},svg); tx.textContent=t; });
  rows.forEach((k,i)=>{ const y=m.t+rh*i+rh/2; const g=parseFloat(S[k].ground_dBm_per_Hz), s=parseFloat(S[k].steady_dBm_per_Hz);
    const lab=el('text',{x:m.l-10,y:y+4,'text-anchor':'end',style:'fill:var(--ink)'},svg); lab.textContent=narrow?k:`${DL[k]} [${k}]`;
    el('line',{x1:X(g),x2:X(s),y1:y,y2:y,stroke:css('--rule'),'stroke-width':4,'stroke-linecap':'round'},svg);
    [[g,cg,'Ground, motors off'],[s,cf,'Steady flight']].forEach(([v,c,t])=>{ const own=S[k].receiver==='hf'?NH:NM;
      const dot=el('circle',{cx:X(v),cy:y,r:6,fill:c,stroke:css('--panel'),'stroke-width':2},svg);
      const hz=el('circle',{cx:X(v),cy:y,r:14,fill:'transparent'},svg);
      hz.addEventListener('pointerenter',ev=>{ tip.innerHTML=`<b>${DL[k]} [${k}]</b><div>${t}: <b class="num">${v.toFixed(1)}</b> dBm/Hz</div><div style="color:var(--ink2)">${fmt(v-own)} dB above the receiver's own noise</div><div style="color:var(--ink2)">${S[k].configuration}</div>`; const r=host.getBoundingClientRect(); placeTip(host,tip,ev.clientX-r.left,ev.clientY-r.top); });
      hz.addEventListener('pointerleave',()=>tip.hidden=true); });
  });
}

// ---- Timelines
const tlState=new Set(['D2','P3','F2']); const TLK=['F2','F3','F5','F6','F7','C1','C2','P1','P2','P3','D2'];
function timelines(){ const keys=TLK.filter(k=>tlState.has(k));
  const series=keys.map(k=>({name:FL[k].lab,color:css(FL[k].c),x:D.timelines[k].map((_,i)=>i),y:D.timelines[k],width:1.3}));
  if(!series.length){ document.getElementById('tl-chart').innerHTML='<p style="color:var(--ink2);padding:20px">Choose at least one flight above.</p>'; return; }
  const refs=[]; if(keys.some(k=>k[0]==='F')) refs.push({y:NH,label:'HF+ own noise'}); if(keys.some(isMini)) refs.push({y:NM,label:'Mini own noise'});
  lineChart(document.getElementById('tl-chart'),{series,ymin:-172,ymax:keys.includes('D2')?-128:-140,ystep:4,xmin:0,xlabel:'Seconds from Start Detection',ylabel:'dBm/Hz',xname:'Second',unit:'dBm/Hz',refs,snap:2,aria:'Noise floor over time'}); }

// ---- Spectra
const spState=new Set(['P3','F6','F2']); let spStage='steady';
function spectra(){ const keys=['F2','F3','F5','F6','F7','P1','P2','P3'].filter(k=>spState.has(k)&&D.spectra[k+'|'+spStage]);
  const series=keys.map(k=>{ const rx=D.summary[k].receiver; return {name:FL[k].lab,color:css(FL[k].c),x:D.spectra_f[rx],y:D.spectra[k+'|'+spStage],width:1.3}; });
  const host=document.getElementById('sp-chart'); if(!series.length){ host.innerHTML='<p style="color:var(--ink2);padding:20px">No data for that choice. Ponui flight 1 has no motors-off stage.</p>'; return; }
  const refs=[]; if(keys.some(k=>k[0]==='F')) refs.push({y:NH,label:'HF+ own noise'}); if(keys.some(k=>k[0]==='P')) refs.push({y:NM,label:'Mini own noise'});
  lineChart(host,{series,ymin:-172,ymax:-140,ystep:4,xmin:-1550,xmax:1550,xticks:[-1500,-1000,-500,0,500,1000,1500],xlabel:'Offset from 160.172 MHz (Hz)',ylabel:'dBm/Hz',xname:'Offset (Hz)',unit:'dBm/Hz',refs,snap:30,aria:'Noise spectrum across the channel'}); }

// ---- Bench
let bnLevel='-90';
function bench(){ const ramp={load:'--neutral','-120':'--s1','-110':'--s1','-100':'--s1','-90':'--s1'};
  [['Mini_1','bn-mini',NM,'Mini own noise'],['HF','bn-hf',NH,'HF+ own noise']].forEach(([run,id,own,lab])=>{
    const rx=run; const s=[{name:'50 Ω load',color:css('--neutral'),x:D.bench_f[rx],y:D.bench[run+'|load'],width:1.2}];
    if(bnLevel!=='load') s.push({name:bnLevel+' dBm tone',color:css('--s1'),x:D.bench_f[rx],y:D.bench[run+'|'+bnLevel],width:1.5});
    lineChart(document.getElementById(id),{series:s,ymin:-172,ymax:-136,ystep:6,xmin:-1500,xmax:1500,xticks:[-1500,-750,0,750,1500],xlabel:'Offset from 160.172 MHz (Hz)',ylabel:'dBm/Hz at input',xname:'Offset (Hz)',unit:'dBm/Hz',refs:[{y:own,label:lab}],snap:30,height:260,legend:true,aria:'Spectrum around the calibration tone'}); }); }

// ---- Budget calculator
const KT0=-173.93;
function budget(){ const fa=+document.getElementById('b-fa').value, nf=+document.getElementById('b-nf').value, ldb=+document.getElementById('b-l').value;
  document.getElementById('b-fa-v').textContent=fa.toFixed(1)+' dB above kT₀'; document.getElementById('b-nf-v').textContent=nf.toFixed(1)+' dB'; document.getElementById('b-l-v').textContent=ldb.toFixed(1)+' dB';
  const F=10**(nf/10), L=10**(ldb/10), fap=10**(fa/10)/L + (1-1/L), tot=fap+F-1, rise=10*Math.log10(tot/F);
  document.getElementById('b-rise').textContent=fmt(rise)+' dB'; document.getElementById('b-in').textContent=(KT0+10*Math.log10(tot)).toFixed(1)+' dBm/Hz';
  document.getElementById('b-range').textContent=Math.round(100*10**(-rise/20))+' %';
  // strip chart of Fa scale with markers
  const host=document.getElementById('b-chart'); host.innerHTML=''; const W=Math.max(260,host.clientWidth), H=120, m={l:10,r:10,t:18,b:30};
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,role:'img','aria-label':'Outside noise scale with reference levels'},host); const X=v=>m.l+(v+12)/(47)*(W-m.l-m.r);
  el('line',{x1:X(-12),x2:X(35),y1:H-m.b,y2:H-m.b,stroke:css('--neutral')},svg);
  [-10,0,10,20,30].forEach(v=>{ el('line',{x1:X(v),x2:X(v),y1:H-m.b,y2:H-m.b+4,stroke:css('--neutral')},svg); const t=el('text',{x:X(v),y:H-m.b+16,'text-anchor':'middle'},svg); t.textContent=v; });
  const tx=el('text',{x:W/2,y:H-2,'text-anchor':'middle'},svg); tx.textContent='Outside noise at the antenna, dB above kT₀';
  Object.entries(D.budget.itu_fam_160MHz).sort((a,b)=>a[1]-b[1]).forEach(([k,v],i)=>{ el('circle',{cx:X(v),cy:H-m.b,r:4,fill:css('--neutral')},svg); const t=el('text',{x:X(v),y:H-m.b-(i%2?24:10),'text-anchor':'middle',style:'font-size:10px'},svg); t.textContent=k; });
  [[D.budget.external_now_antenna_db,'--s2','Now',1],[D.budget.external_ponui_antenna_db,'--s7','Ponui',-1]].forEach(([v,c,lab,dir])=>{ el('circle',{cx:X(v),cy:m.t,r:5,fill:css(c)},svg); const t=el('text',{x:X(v)+dir*8,y:m.t+4,'text-anchor':dir<0?'end':'start',style:'fill:var(--ink)'},svg); t.textContent=lab+' (measured)'; });
  el('line',{x1:X(fa),x2:X(fa),y1:m.t-10,y2:H-m.b,stroke:css('--accent'),'stroke-width':2},svg);
}
function presets(){ const host=document.getElementById('b-presets'); const P=[
  ['Now: HF+, choke + 15 ft',D.budget.external_now_antenna_db,7.2,1.8],['Ponui: Mini, 15 ft, no choke',D.budget.external_ponui_antenna_db,6.4,1.4],['Rural background, HF+',D.budget.itu_fam_160MHz.Rural,7.2,1.8],['Residential background, HF+',D.budget.itu_fam_160MHz.Residential,7.2,1.8]];
  P.forEach(([lab,fa,nf,l],i)=>{ const b=document.createElement('button'); b.className='chip'; b.type='button'; b.id='preset-'+i; b.textContent=lab; b.onclick=()=>{ document.getElementById('b-fa').value=fa.toFixed(2); document.getElementById('b-nf').value=nf; document.getElementById('b-l').value=l; budget(); }; host.appendChild(b); }); }

// ---- VNA
let vnMode='il';
const VN=[['rg316_15ft+choke','--s1','15 ft RG-316 + choke'],['rg316_15ft','--s2','15 ft RG-316'],['rg316_88cm+choke','--s3','88 cm RG-316 + choke'],['choke','--s7','Choke']];
function vna(){ const s=VN.map(([k,c,lab])=>({name:lab,color:css(c),x:D.vna_f,y:D.vna[k][vnMode]}));
  lineChart(document.getElementById('vn-chart'),{series:s,ymin:vnMode==='il'?0:15,ymax:vnMode==='il'?2:55,ystep:vnMode==='il'?0.5:10,xmin:100,xmax:220,xticks:[100,120,140,160,180,200,220],xlabel:'Frequency (MHz)',ylabel:vnMode==='il'?'Insertion loss (dB)':'Return loss (dB)',xname:'MHz',unit:'dB',snap:1.5,height:260,legend:true,aria:'Cable and choke measurements'}); }
function vnaTable(){ const rows=[['thru','Thru (calibration check)',null],['rg316_15ft','15 ft RG-316 extension','≈1.4'],['choke','Common-mode choke','≈0.35'],['rg316_15ft+choke','15 ft RG-316 + choke','≈1.8'],['rg316_88cm','88 cm RG-316 (bench cable)','≈0.35'],['rg316_88cm+choke','88 cm RG-316 + choke (bench path)','≈0.6']];
  const i=D.vna_f.findIndex(f=>Math.abs(f-160)<0.01); document.getElementById('vn-table').innerHTML=rows.map(([k,lab,c])=>`<tr><td>${lab}</td><td class="n">${(Math.abs(D.vna[k].il[i])<0.02?0:D.vna[k].il[i]).toFixed(2)} dB</td><td class="n">${c?c+' dB':'—'}</td><td class="n">${D.vna[k].rl[i].toFixed(1)} dB</td></tr>`).join(''); }

function cfgTable(){ const R=[['D2','2025-03-17','Ponui Day 2: Mini outside the shield on a USB extension, no ferrites, 15 ft coax, no choke; 161.09 MHz','Mini, gain 20'],['C1','2025-11-24','Cumbria: Mini inside the shield, bonded SMA bulkhead, choke + 15 ft coax; 173.3 MHz','Mini, gain 21'],['C2','2025-11-24','Cumbria, as C1','Mini, gain 21'],['F2','2026-11-14','Choke + 15 ft coax, ~170 ft, 30 s hover','HF+'],['F3','2026-11-14','Choke + 15 ft coax, ~170 ft','HF+'],['F7','2026-11-14','Choke, no extension, 50 ft','HF+'],['F5','2026-11-14','No choke, 15 ft coax, 50 ft','HF+'],['F6','2026-11-14','No choke, no extension, 50 ft','HF+'],['P2','2025-03-22','Ponui: Mini outside the shield on a USB extension with 2 snap-on ferrites, 15 ft coax, no choke','Mini, gain 20'],['P3','2025-03-22','Ponui: Mini outside the shield on a USB extension with 2 snap-on ferrites, 15 ft coax, no choke','Mini, gain 20']];
  document.getElementById('cfg-table').innerHTML=R.map(([k,d,c,r])=>{ const S=D.summary[k]; return `<tr><td>${k}</td><td class="num">${d}</td><td>${c}</td><td>${r}</td><td class="n">${S.ground_dBm_per_Hz===''?'—':(+S.ground_dBm_per_Hz).toFixed(1)}</td><td class="n">${(+S.steady_dBm_per_Hz).toFixed(1)}</td><td class="n">${fmt(+S.steady_above_own_floor_db)} dB</td></tr>`; }).join(''); }

// ---- History: four stages
function history(){
  const host=document.getElementById('hist-chart'); host.innerHTML=''; const St=D.history.steps;
  const W=Math.max(300,host.clientWidth), narrow=W<600, H=narrow?380:340, m={l:46,r:10,t:30,b:narrow?40:70};
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,role:'img','aria-label':'Noise at each stage from Ponui to now'},host);
  const ymin=-170,ymax=-130, Y=v=>m.t+(ymax-v)/(ymax-ymin)*(H-m.t-m.b), X=i=>m.l+(i+0.5)*(W-m.l-m.r)/St.length, bw=(W-m.l-m.r)/St.length;
  for(let v=ymin; v<=ymax; v+=5){ el('line',{x1:m.l,x2:W-m.r,y1:Y(v),y2:Y(v),class:'gridl'},svg); const t=el('text',{x:m.l-8,y:Y(v)+4,'text-anchor':'end'},svg); t.textContent=v; }
  const yl=el('text',{x:12,y:(m.t+H-m.b)/2,'text-anchor':'middle',transform:`rotate(-90 12 ${(m.t+H-m.b)/2})`},svg); yl.textContent='dBm/Hz at receiver input';
  const cg=css('--s1'), cf=css('--s2'), tip=makeTip(host);
  [[cg,'Ground, motors off'],[cf,'Steady flight']].forEach(([c,t],i)=>{ const x=m.l+i*150; el('circle',{cx:x+5,cy:10,r:5,fill:c},svg); const tx=el('text',{x:x+15,y:14},svg); tx.textContent=t; });
  const SHORT=narrow?['Ponui D2','Ponui D3–8','Cumbria','Arizona']:['Ponui Day 2, Mar 2025','Ponui Days 3–8, Mar 2025','Cumbria, Nov 2025','Arizona, Nov 2026'];
  const SUB=['no ferrites','+ USB ferrites','Mini in shield, choke','HF+, F1–F9'];
  let d='';
  St.forEach((r,i)=>{ const f=+r.steady_dBm_per_Hz, g=+r.ground_dBm_per_Hz, own=+r.own_dBm_per_Hz, x=X(i);
    el('line',{x1:x-bw*0.2,x2:x+bw*0.2,y1:Y(own),y2:Y(own),stroke:css('--neutral'),'stroke-dasharray':'4 3'},svg);
    el('line',{x1:x,x2:x,y1:Y(g),y2:Y(f),stroke:css('--rule'),'stroke-width':4,'stroke-linecap':'round'},svg);
    d+=(i?'L':'M')+x.toFixed(1)+','+Y(f).toFixed(1);
    const t1=el('text',{x,y:H-m.b+18,'text-anchor':'middle',style:'fill:var(--ink)'},svg); t1.textContent=SHORT[i];
    if(!narrow){ const t2=el('text',{x,y:H-m.b+34,'text-anchor':'middle'},svg); t2.textContent=SUB[i]; }
    if(i){ const p=+St[i-1].steady_dBm_per_Hz; const tt=el('text',{x:(X(i-1)+x)/2,y:Y((p+f)/2)-8,'text-anchor':'middle',style:'fill:var(--ink);font-weight:600;font-size:12px'},svg); tt.textContent=(f-p).toFixed(1).replace('-','−')+' dB'; }
    [[g,cg,'Ground, motors off'],[f,cf,'Steady flight']].forEach(([v,c,t])=>{ el('circle',{cx:x,cy:Y(v),r:6,fill:c,stroke:css('--panel'),'stroke-width':2},svg);
      const hz=el('circle',{cx:x,cy:Y(v),r:14,fill:'transparent'},svg);
      hz.addEventListener('pointerenter',ev=>{ tip.innerHTML=`<b>${r.label}</b><div>${t}: <b class="num">${v.toFixed(1)}</b> dBm/Hz</div><div style="color:var(--ink2)">${fmt(v-own)} dB above the receiver's own noise</div><div style="color:var(--ink2);white-space:normal;max-width:260px">${r.change}${r.notes?'; '+r.notes:''}</div>`; const rr=host.getBoundingClientRect(); placeTip(host,tip,ev.clientX-rr.left,ev.clientY-rr.top); });
      hz.addEventListener('pointerleave',()=>tip.hidden=true); }); });
  const path=el('path',{d,fill:'none',stroke:cf,'stroke-width':1.2,'stroke-opacity':0.5},svg); svg.insertBefore(path,svg.querySelector('circle'));
}
function histTable(){ const St=D.history.steps; document.getElementById('hist-table').innerHTML=St.map((r,i)=>`<tr><td>${r.stage}. ${r.label}</td><td>${r.change}${r.notes?' <span style="color:var(--ink3)">('+r.notes+')</span>':''}</td><td class="n">${(+r.ground_dBm_per_Hz).toFixed(1)}</td><td class="n">${(+r.steady_dBm_per_Hz).toFixed(1)}</td><td class="n">${i?((+r.steady_dBm_per_Hz)-(+St[i-1].steady_dBm_per_Hz)).toFixed(1)+' dB':'—'}</td></tr>`).join(''); }

// ---- Ponui trip, per flight
function trip(){
  const host=document.getElementById('trip-chart'); host.innerHTML=''; const T=D.history.trip;
  const W=Math.max(300,host.clientWidth), nar=W<600, H=nar?360:320, m={l:46,r:10,t:nar?62:30,b:70};
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,role:'img','aria-label':'In-flight noise of every flight of the Ponui trip'},host);
  const ymin=-170,ymax=-128, Y=v=>m.t+(ymax-v)/(ymax-ymin)*(H-m.t-m.b), X=i=>m.l+(i+0.5)*(W-m.l-m.r)/T.length;
  for(let v=-170; v<=ymax; v+=10){ el('line',{x1:m.l,x2:W-m.r,y1:Y(v),y2:Y(v),class:'gridl'},svg); const t=el('text',{x:m.l-8,y:Y(v)+4,'text-anchor':'end'},svg); t.textContent=v; }
  el('line',{x1:m.l,x2:W-m.r,y1:Y(NM),y2:Y(NM),stroke:css('--neutral'),'stroke-dasharray':'4 3'},svg); const ot=el('text',{x:W-m.r-4,y:Y(NM)-5,'text-anchor':'end'},svg); ot.textContent='Mini own noise';
  const yl=el('text',{x:12,y:(m.t+H-m.b)/2,'text-anchor':'middle',transform:`rotate(-90 12 ${(m.t+H-m.b)/2})`},svg); yl.textContent='dBm/Hz in flight';
  const col=r=>r.site==='Wellington'?css('--s2'):(r.usb_ferrites==='no'?css('--s8'):css('--s1'));
  [['--s2','Wellington, no ferrites'],['--s8','Ponui Day 2, no ferrites'],['--s1','Ponui Days 3–8, ferrites']].forEach(([c,t],i)=>{ const x=nar?m.l:m.l+i*175, y=nar?10+i*17:10; el('circle',{cx:x+5,cy:y,r:5,fill:css(c)},svg); const tx=el('text',{x:x+15,y:y+4},svg); tx.textContent=t; });
  const k=T.reduce((a,r,i)=>r.usb_ferrites==='no'?i:a,0); const xk=(X(k)+X(k+1))/2;
  el('line',{x1:xk,x2:xk,y1:m.t,y2:H-m.b,stroke:css('--ink3')},svg); const kt=el('text',{x:xk+6,y:Y(-157),style:'font-size:11px'},svg); kt.textContent='18 Mar: ferrites fitted';
  const tip=makeTip(host), step=Math.ceil(T.length/(W<600?8:20));
  T.forEach((r,i)=>{ const x=X(i), c=col(r), n=+r.n;
    el('line',{x1:x,x2:x,y1:Y(+r.p10),y2:Y(+r.p90),stroke:c,'stroke-width':1.5},svg);
    el('circle',{cx:x,cy:Y(+r.median),r:nar?3.5:5,fill:n>=8?c:css('--panel'),stroke:c,'stroke-width':1.6},svg);
    if(i%step===0){ const t=el('text',{x,y:H-m.b+12,'text-anchor':'end',transform:`rotate(-55 ${x} ${H-m.b+12})`,style:'font-size:10px'},svg); t.textContent=r.when_nzdt.slice(5).replace('2025-',''); }
    const hz=el('rect',{x:x-8,y:m.t,width:16,height:H-m.t-m.b,fill:'transparent'},svg);
    hz.addEventListener('pointerenter',ev=>{ tip.innerHTML=`<b>${r.site}, ${r.when_nzdt} NZDT</b><div>In flight: <b class="num">${(+r.median).toFixed(1)}</b> dBm/Hz (10–90 %: ${(+r.p10).toFixed(1)} to ${(+r.p90).toFixed(1)})</div><div style="color:var(--ink2)">USB ferrites: ${r.usb_ferrites}; ${r.n} ${r.source.startsWith('IQ')?'seconds':'pulses'}; ${r.source.split(' Pulse')[0]}</div>`; const rr=host.getBoundingClientRect(); placeTip(host,tip,ev.clientX-rr.left,ev.clientY-rr.top); });
    hz.addEventListener('pointerleave',()=>tip.hidden=true); });
}

function all(){ history(); trip(); dumbbell(); timelines(); spectra(); bench(); budget(); vna(); }
document.getElementById('t-nm').textContent=NM.toFixed(1)+' dBm/Hz'; document.getElementById('t-nh').textContent=NH.toFixed(1)+' dBm/Hz'; document.getElementById('t-nfh').textContent=D.cal.nf_hf_db.toFixed(1)+' dB';
chips(document.getElementById('tl-chips'),TLK,tlState,timelines);
chips(document.getElementById('sp-chips'),['F2','F3','F5','F6','F7','P1','P2','P3'],spState,spectra);
spStage=seg(document.getElementById('sp-seg'),v=>{spStage=v;spectra();});
bnLevel=seg(document.getElementById('bn-seg'),v=>{bnLevel=v;bench();});
vnMode=seg(document.getElementById('vn-seg'),v=>{vnMode=v;vna();});
['b-fa','b-nf','b-l'].forEach(id=>document.getElementById(id).addEventListener('input',budget));
presets(); vnaTable(); cfgTable(); histTable(); all();
let rt; window.addEventListener('resize',()=>{ clearTimeout(rt); rt=setTimeout(all,150); });
if (window.matchMedia) window.matchMedia('(prefers-color-scheme: dark)').addEventListener?.('change', all);
new MutationObserver(all).observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
})();
