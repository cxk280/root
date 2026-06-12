"use strict";
const C = {bg:'#0b0e14',panel:'#141925',panel2:'#1b2030',line:'#26304a',text:'#e6e9ef',
  muted:'#8b93a7',code:'#5b8def',membrane:'#f2c94c',data:'#5a6373',zero:'#1b2030',
  decay:'#ef5350',repair:'#66bb6a',fuel:'#2dd4bf',nutrient:'#ffb74d',accent:'#5b8def'};
const $ = s => document.querySelector(s);

let meta = {}, activeView = 'arena';
let prevBytes = null;                       // for repair-flash detection
const heart = [];                           // [{integ,turn}]
const ftrail = [];                          // [{pos,food}]

// ---------- control ----------
function control(action, extra) {
  fetch('/control', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({action, ...extra})});
}
function startActive() {
  prevBytes = null; heart.length = 0; ftrail.length = 0;
  hideDeath();
  if (activeView === 'arena') control('start', {spec: arenaSpec()});
  else if (activeView === 'forager') control('start', {spec: foragerSpec()});
}
function arenaSpec() {
  const org = $('#a-org').value;
  const decay = $('#a-decay .on').dataset.d;
  const v = parseFloat($('#a-slider').value);
  if (org === 'colony') return {scenario:'colony', organism:'protocell2', heads:2, lam: decay==='bitrot'?v:0.08};
  const s = {scenario:'arena', organism:org, decay};
  if (decay === 'solvent') s.T = Math.round(v); else s.lam = v;
  return s;
}
function foragerSpec() {
  return {scenario:'forager', organism: $('#f-org .on').dataset.o,
          food_speed: parseFloat($('#f-slider').value)};
}

// slider reconfig for arena decay law
function syncArenaSlider() {
  const decay = $('#a-decay .on').dataset.d, sl = $('#a-slider');
  if (decay === 'solvent') {
    sl.min=100; sl.max=2000; sl.step=50; if(sl.value<100||sl.value>2000) sl.value=600;
    $('#a-sliderlbl').textContent = 'T — sweep period (instructions)';
  } else {
    sl.min=0; sl.max=0.4; sl.step=0.01; if(sl.value>0.4) sl.value=0.08;
    $('#a-sliderlbl').textContent = 'λ — mean flips / window';
  }
  arenaHint();
}
function arenaHint() {
  const decay = $('#a-decay .on').dataset.d, v = parseFloat($('#a-slider').value);
  if (decay==='solvent') $('#a-sliderhint').innerHTML = `T = ${Math.round(v)} · <b>T* ≈ 500</b> (dies below)`;
  else $('#a-sliderhint').innerHTML = `λ = ${v.toFixed(2)} · <b>λ* ≈ 0.04</b> (error catastrophe)`;
}
function foragerHint() {
  const v = parseFloat($('#f-slider').value);
  $('#f-sliderhint').innerHTML = `v = ${v.toFixed(1)} · <b>v* ≈ 1.2</b> (foraging bandwidth)`;
}

// ---------- SSE ----------
let booted = false;
function connect() {
  const es = new EventSource('/stream');
  es.onopen = () => { if(!booted){ booted=true; showView(location.hash.slice(1)||'arena'); } };
  es.addEventListener('meta', e => { meta = JSON.parse(e.data); prevBytes=null; heart.length=0; ftrail.length=0; });
  es.addEventListener('frame', e => render(JSON.parse(e.data)));
  es.addEventListener('done', e => { const d=JSON.parse(e.data); if(d.cause) showDeath(d.cause);
    // life → death → rebirth: restart the scenario so the demo keeps breathing
    if(activeView==='arena'||activeView==='forager')
      setTimeout(()=>{ if(activeView==='arena'||activeView==='forager') startActive(); }, 2600); });
}
function render(f) {
  $('#dot').classList.toggle('dead', f.alive === false);
  if (meta.kind === 'forager') renderForager(f);
  else renderArena(f);
  if (f.alive === false && f.cause) showDeath(f.cause);
}
function showDeath(cause){ const id = activeView==='forager'?'#f-death':'#a-death';
  const el=$(id); if(!el) return; el.classList.add('show');
  const b = el.querySelector('b'); if(b && activeView!=='forager') b.textContent = causeLabel(cause); }
function hideDeath(){ document.querySelectorAll('.death').forEach(d=>d.classList.remove('show')); }
function causeLabel(c){
  if(c.includes('forbidden')) return 'died: trapped instruction';
  if(c.includes('READ')||c.includes('FETCH')||c.includes('fault')) return 'died: dissolved / fault';
  if(c==='no_turnover') return 'died: stopped metabolizing';
  if(c==='all_heads_down') return 'colony collapsed';
  return 'died: ' + c;
}

// ---------- Arena render ----------
function renderArena(f) {
  const cv=$('#a-canvas'), ctx=cv.getContext('2d');
  const cols=meta.cols, rows=meta.rows, roles=meta.roles||[], birth=meta.birth||[];
  const pitch=Math.floor(Math.min(cv.width/cols, cv.height/rows)), cell=pitch-2;
  const ox=(cv.width-cols*pitch)/2, oy=(cv.height-rows*pitch)/2;
  ctx.clearRect(0,0,cv.width,cv.height);
  const rips = f.rips!==undefined ? f.rips : (f.rip!==undefined?[f.rip]:[]);
  const headSet = new Set(rips.map(r=>Math.max(0,Math.min(f.bytes.length-1,r))));
  for(let o=0;o<f.bytes.length;o++){
    const col=o%cols, row=(o/cols)|0, x=ox+col*pitch, y=oy+row*pitch;
    let color;
    const healthy = birth.length ? f.bytes[o]===birth[o] : true;
    if(!healthy) color = C.decay;                                  // currently corrupted
    else if(prevBytes && birth.length && prevBytes[o]!==birth[o]) color = C.repair; // just healed
    else { const r=roles[o]||'code'; color = f.bytes[o]===0 ? C.zero : C[r]||C.data; }
    ctx.fillStyle=color; rr(ctx,x,y,cell,cell,2); ctx.fill();
    if(headSet.has(o)){ ctx.strokeStyle='#fff'; ctx.lineWidth=2; rr(ctx,x+1,y+1,cell-2,cell-2,2); ctx.stroke(); }
  }
  prevBytes = f.bytes.slice();
  // vital signs
  const ip=Math.round(f.integrity*100);
  $('#a-integ').textContent=ip; $('#a-integ2').textContent=ip+'%';
  $('#a-integbar').style.width=ip+'%';
  $('#a-win').textContent=(f.w+1).toLocaleString();
  $('#a-turn').textContent=(f.turnover!==undefined?f.turnover+' B':'—');
  $('#a-heads').textContent = meta.kind==='colony' ? String(rips.length) : '—';
  heart.push({integ:f.integrity, turn:f.turnover||0}); if(heart.length>120) heart.shift();
  drawHeart();
}
function drawHeart() {
  const cv=$('#a-heart'), ctx=cv.getContext('2d'); ctx.clearRect(0,0,cv.width,cv.height);
  const n=heart.length; if(!n) return; const step=cv.width/Math.max(120,n);
  const maxT=Math.max(1,...heart.map(h=>h.turn));
  line(ctx, i=>i*step, i=>cv.height-4-heart[i].integ*(cv.height-8), n, C.repair, 1.6);
  line(ctx, i=>i*step, i=>cv.height-4-(heart[i].turn/maxT)*(cv.height-8)*0.5, n, C.fuel, 1.2, 0.6);
}

// ---------- Forager render ----------
function renderForager(f) {
  const cv=$('#f-canvas'), ctx=cv.getContext('2d'); ctx.clearRect(0,0,cv.width,cv.height);
  const N=meta.world_n||64, sw=cv.width, cw=sw/N, sy=20, sh=46;
  for(let i=0;i<N;i++){ const s=Math.max(0,1-Math.abs(i-f.food)/14);
    ctx.fillStyle=`rgba(255,183,77,${0.08+0.5*s})`; rr(ctx,i*cw+0.5,sy,cw-1,sh,2); ctx.fill(); }
  ctx.fillStyle=C.nutrient; rr(ctx,f.food*cw,sy-4,cw,sh+8,2); ctx.fill();
  ctx.fillStyle=C.fuel; rr(ctx,f.pos*cw,sy+sh+8,cw,12,2); ctx.fill();
  ctx.fillStyle=C.nutrient; ctx.font='11px sans-serif'; ctx.textAlign='center';
  ctx.fillText('food', f.food*cw+cw/2, sy-8);
  ctx.fillStyle=C.fuel; ctx.fillText('forager', f.pos*cw+cw/2, sy+sh+38);
  // timeline
  ftrail.push({pos:f.pos, food:f.food}); if(ftrail.length>60) ftrail.shift();
  const T0=140,T1=280,xl=24,xr=cv.width-8;
  ctx.strokeStyle=C.line; ctx.lineWidth=1; ctx.beginPath();
  ctx.moveTo(xl,T1); ctx.lineTo(xr,T1); ctx.moveTo(xl,T0); ctx.lineTo(xl,T1); ctx.stroke();
  ctx.fillStyle=C.muted; ctx.textAlign='left'; ctx.fillText('pos', 2, T0+9);
  ctx.textAlign='right'; ctx.fillText('time →', xr, T1+14); ctx.textAlign='left';
  const m=ftrail.length, sx=(xr-xl)/Math.max(59,m-1);
  line(ctx, i=>xl+i*sx, i=>T1-(T1-T0)*(ftrail[i].food/N), m, C.nutrient, 2);
  line(ctx, i=>xl+i*sx, i=>T1-(T1-T0)*(ftrail[i].pos/N), m, C.fuel, 1.8);
  if(f.harvest){ ctx.fillStyle='rgba(255,183,77,0.5)'; rr(ctx,f.food*cw-2,sy-6,cw+4,sh+12,3); ctx.fill(); }
  // fuel panel
  const fp=Math.max(0,Math.min(100, f.fuel/800*100));
  $('#f-fuel').textContent=f.fuel; $('#f-fuelbar').style.height=fp+'%';
  $('#f-win').textContent=(f.w+1).toLocaleString();
  $('#f-harv').textContent=f.harvests;
  $('#f-track').textContent=f.track_error;
}

// ---------- canvas helpers ----------
function rr(ctx,x,y,w,h,r){ctx.beginPath();ctx.moveTo(x+r,y);ctx.arcTo(x+w,y,x+w,y+h,r);
  ctx.arcTo(x+w,y+h,x,y+h,r);ctx.arcTo(x,y+h,x,y,r);ctx.arcTo(x,y,x+w,y,r);ctx.closePath();}
function line(ctx,fx,fy,n,color,w,alpha){ if(n<2)return; ctx.globalAlpha=alpha||1;
  ctx.strokeStyle=color; ctx.lineWidth=w; ctx.beginPath();
  for(let i=0;i<n;i++){ i?ctx.lineTo(fx(i),fy(i)):ctx.moveTo(fx(i),fy(i)); } ctx.stroke(); ctx.globalAlpha=1; }

// ---------- tabs / transport ----------
function showView(v){ activeView=v;
  document.querySelectorAll('.tab').forEach(t=>t.classList.toggle('active',t.dataset.view===v));
  document.querySelectorAll('.view').forEach(s=>s.classList.toggle('active',s.id==='view-'+v));
  $('#transport').style.visibility = (v==='arena'||v==='forager')?'visible':'hidden';
  if(v==='arena'||v==='forager') startActive();
}
document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>showView(t.dataset.view));
$('#playpause').onclick=function(){ const p=this.textContent==='⏸';
  this.textContent=p?'▶':'⏸'; control(p?'pause':'resume',{}); };
$('#step').onclick=()=>{ $('#playpause').textContent='▶'; control('step',{}); };
$('#speed').oninput=function(){ $('#speedlbl').textContent=parseFloat(this.value)+'×'; control('speed',{speed:parseFloat(this.value)}); };
// arena controls
$('#a-org').onchange=startActive;
$('#a-decay').querySelectorAll('button').forEach(b=>b.onclick=()=>{
  $('#a-decay').querySelectorAll('button').forEach(x=>x.classList.remove('on'));
  b.classList.add('on'); syncArenaSlider(); startActive(); });
$('#a-slider').oninput=arenaHint;
$('#a-slider').onchange=startActive;
// forager controls
$('#f-org').querySelectorAll('button').forEach(b=>b.onclick=()=>{
  $('#f-org').querySelectorAll('button').forEach(x=>x.classList.remove('on'));
  b.classList.add('on'); startActive(); });
$('#f-slider').oninput=foragerHint;
$('#f-slider').onchange=startActive;

// ---------- static views ----------
function buildThresholds(){
  const charts=[
    {t:'T*  ·  solvent — survival vs sweep period',crit:'T* = 500',cf:.5,
     s:[{c:C.repair,p:[[0,0],[.45,0],[.5,1],[.7,1],[1,1]]}]},
    {t:'λ*  ·  bit-rot — survival vs flip rate',crit:'λ* ≈ 0.04 → colony lifts',cf:.3,
     s:[{c:C.decay,p:[[0,1],[.15,.4],[.3,0],[1,0]]},{c:C.membrane,p:[[0,1],[.3,.6],[.5,.4],[.7,.1],[1,0]]},
        {c:C.repair,p:[[0,1],[.4,.7],[.6,.5],[.8,.25],[1,.1]]}]},
    {t:'v*  ·  foraging — survival vs drift speed',crit:'v* ≈ 1.2',cf:.6,
     s:[{c:C.fuel,p:[[0,1],[.55,1],[.6,.9],[.72,0],[1,0]]},{c:C.data,p:[[0,0],[1,0]]}]}];
  const W=380,H=190,x0=40,x1=364,y0=46,y1=170;
  $('#t-charts').innerHTML = charts.map(ch=>{
    let g=`<rect x="0" y="0" width="${W}" height="${H+30}" fill="${C.panel}" rx="12" stroke="${C.line}"/>`;
    g+=`<text x="16" y="26" fill="#cdd3df" font-size="13" font-family="sans-serif">${ch.t}</text>`;
    g+=`<line x1="${x0}" y1="${y1}" x2="${x1}" y2="${y1}" stroke="${C.line}"/><line x1="${x0}" y1="${y0}" x2="${x0}" y2="${y1}" stroke="${C.line}"/>`;
    g+=`<text x="6" y="${y0+12}" fill="${C.muted}" font-size="10" font-family="sans-serif">survival</text>`;
    const cx=x0+(x1-x0)*ch.cf;
    g+=`<line x1="${cx}" y1="${y0}" x2="${cx}" y2="${y1}" stroke="${C.membrane}" stroke-dasharray="4 3"/>`;
    g+=`<text x="${cx+4}" y="${y0+12}" fill="${C.membrane}" font-size="11" font-family="sans-serif">${ch.crit}</text>`;
    ch.s.forEach(se=>{const pts=se.p.map(([x,y])=>`${x0+(x1-x0)*x},${y0+(y1-y0)*(1-y)}`).join(' ');
      g+=`<polyline points="${pts}" fill="none" stroke="${se.c}" stroke-width="2"/>`;});
    return `<svg viewBox="0 0 ${W} ${H+30}" style="width:100%">${g}</svg>`;}).join('');
  // scorecard
  const rows=[['rock',[0,0,1,0,0,0],'1/6','dead'],['blind',[0,0,1,0,0,1],'2/6','alive · no boundary'],
    ['protocell0',[1,1,1,1,1,1],'6/6','autopoietic'],['protocell1',[1,1,1,1,1,1],'6/6','autopoietic · TMR'],
    ['protocell2',[1,1,1,1,1,1],'6/6','autopoietic · TMR']];
  let tb='<table><tr><th style="text-align:left">organism</th><th>1</th><th>2</th><th>3</th><th>4</th><th>5</th><th>6</th><th>closure</th><th>verdict</th></tr>';
  rows.forEach(r=>{tb+=`<tr><td class="org">${r[0]}</td>`+r[1].map(v=>`<td class="${v?'yes':'no'}">${v?'✓':'✗'}</td>`).join('')
    +`<td style="font-weight:700">${r[2]}</td><td style="color:var(--muted);font-size:11px">${r[3]}</td></tr>`;});
  $('#t-score').innerHTML=tb+'</table>';
  // benchmark
  const K=[['popcount',276,252],['clamp',108,72],['bitrev',288,264],['crc32',349,626],['utf8',6.1,6.2],
    ['sort16',3.9,7.1],['memchr',6.2,2.3],['isqrt',5.9,5.2],['rle',64,44],['b64',104,133]];
  const cv=$('#t-bench'),ctx=cv.getContext('2d'),bw=cv.width/10,bh=140;
  const mx=Math.max(...K.flatMap(k=>[Math.log10(k[1]+2),Math.log10(k[2]+2)]));
  ctx.clearRect(0,0,cv.width,cv.height); ctx.font='10px sans-serif'; ctx.textAlign='center';
  K.forEach((k,i)=>{const cx=i*bw,h1=Math.log10(k[1]+2)/mx*bh,h2=Math.log10(k[2]+2)/mx*bh,w=(bw-16)/2;
    ctx.fillStyle=C.code; rr(ctx,cx+6,bh-h1,w,h1,3); ctx.fill();
    ctx.fillStyle=C.repair; rr(ctx,cx+6+w+3,bh-h2,w,h2,3); ctx.fill();
    ctx.fillStyle=C.muted; ctx.fillText(k[0],cx+bw/2,bh+16);});
}
function buildOverview(){
  const rungs=[['SYNTHESIS TEST','Can an AI write competent machine code?','One-shot assembly: 10/10 correct, beat -O3 on 6/10 speed & 8/10 size → the gate to a metabolism.',1,'thresholds'],
    ['RUNG 1 · SOLVENT · T* = 500','protocell0 — the first living organism','Identity-copy refresh holds against neglect — but it cannot fix corruption → grow error correction.',1,{org:'protocell0',decay:'solvent'}],
    ['RUNG 2 · BIT-ROT · λ* ≈ 0.04','protocell1 — triple modular redundancy','Majority-vote repair lifts λ* ~4–5×, capped by the executing copy itself → redundant execution.',1,{org:'protocell1',decay:'bitrot'}],
    ['RUNG 2.5 · COLONY','two heads over one genome — division of labor','A corrupted head is repaired by another before it runs. Two heads beat three — a reference copy emerges.',1,{org:'colony',decay:'bitrot'}],
    ['RUNG 2.7 · FORAGING · v* ≈ 1.2','forager0 — chemotaxis to a moving nutrient','It must sense and steer to eat. Sensing, not motion, is foraging → layer all under one fuel budget.',1,'forager'],
    ['RUNG 3 · LAYERED · planned','one organism: self-produce + repair + forage','Continuous metabolism, world-triggered foraging, fuel gating repair. The full autopoietic + cognitive unity.',0,null]];
  $('#o-ladder').innerHTML = rungs.map((r,i)=>`<div class="rung${r[3]?'':' planned'}">
    ${r[3]?`<button class="open" data-i="${i}">open ▸</button>`:''}
    <div class="meta">${r[0]}</div><h4>${r[1]}</h4><div class="lesson">${r[2]}</div></div>`).join('');
  $('#o-ladder').querySelectorAll('.open').forEach(b=>b.onclick=()=>{
    const t=rungs[+b.dataset.i][4];
    if(typeof t==='string') showView(t);
    else if(t){ $('#a-org').value=t.org;
      $('#a-decay').querySelectorAll('button').forEach(x=>x.classList.toggle('on',x.dataset.d===t.decay));
      syncArenaSlider(); showView('arena'); }
  });
}

// ---------- boot ----------
syncArenaSlider(); foragerHint(); buildThresholds(); buildOverview();
connect();   // showView(initial) fires on stream open
