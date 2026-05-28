#!/usr/bin/env python3
"""
rebuild_html.py — Regenera el HTML mobile-first desde polla_data_final.json.
Uso: python3 rebuild_html.py
"""
import json, os, datetime

DIR = os.path.dirname(os.path.abspath(__file__))

FLAGS = {
  'México':'🇲🇽','Sudáfrica':'🇿🇦','Corea del Sur':'🇰🇷','Rep. Checa':'🇨🇿','Canadá':'🇨🇦','Bosnia':'🇧🇦',
  'USA':'🇺🇸','Paraguay':'🇵🇾','Qatar':'🇶🇦','Suiza':'🇨🇭','Brasil':'🇧🇷','Marruecos':'🇲🇦','Haití':'🇭🇹',
  'Escocia':'🏴󠁧󠁢󠁳󠁣󠁴󠁿','Australia':'🇦🇺','Turquía':'🇹🇷','Alemania':'🇩🇪','Curazao':'🇨🇼','C. de Marfil':'🇨🇮',
  'Ecuador':'🇪🇨','Países Bajos':'🇳🇱','Japón':'🇯🇵','Suecia':'🇸🇪','Túnez':'🇹🇳','Bélgica':'🇧🇪',
  'Egipto':'🇪🇬','España':'🇪🇸','Cabo Verde':'🇨🇻','Arabia Saudita':'🇸🇦','Uruguay':'🇺🇾','Irán':'🇮🇷',
  'Nueva Zelanda':'🇳🇿','Francia':'🇫🇷','Senegal':'🇸🇳','Irak':'🇮🇶','Noruega':'🇳🇴','Argentina':'🇦🇷',
  'Argelia':'🇩🇿','Austria':'🇦🇹','Jordania':'🇯🇴','Portugal':'🇵🇹','RD Congo':'🇨🇩','Inglaterra':'🏴󠁧󠁢󠁥󠁮󠁧󠁿',
  'Croacia':'🇭🇷','Ghana':'🇬🇭','Panamá':'🇵🇦','Uzbekistán':'🇺🇿','Colombia':'🇨🇴'
}

DOW = {
  "Jun 11":"Jue 11 Jun","Jun 12":"Vie 12 Jun","Jun 13":"Sáb 13 Jun","Jun 14":"Dom 14 Jun",
  "Jun 15":"Lun 15 Jun","Jun 16":"Mar 16 Jun","Jun 17":"Mié 17 Jun","Jun 18":"Jue 18 Jun",
  "Jun 19":"Vie 19 Jun","Jun 20":"Sáb 20 Jun","Jun 21":"Dom 21 Jun","Jun 22":"Lun 22 Jun",
  "Jun 23":"Mar 23 Jun","Jun 24":"Mié 24 Jun","Jun 25":"Jue 25 Jun","Jun 26":"Vie 26 Jun",
  "Jun 27":"Sáb 27 Jun","Jun 28":"Dom 28 Jun"
}

def build_html(data, now):
    flags_js = json.dumps(FLAGS, ensure_ascii=False)
    data_js  = json.dumps(data, ensure_ascii=False, separators=(',',':'))
    dow_js   = json.dumps(DOW, ensure_ascii=False)

    js = r"""
const DATA=__DATA__;
const FLAGS=__FLAGS__;
const BK_NAMES={BF:'Betfair',B3:'bet365',UN:'Unibet',OE:'10bet',MA:'Matchbook',VC:'BetVictor',WA:'Betway'};
const BK_ORDER=['BF','B3','UN','OE','MA','VC','WA'];
const BK_URLS={BF:'https://www.betfair.com',B3:'https://www.bet365.com',UN:'https://www.unibet.com',OE:'https://www.10bet.com',MA:'https://www.matchbook.com',VC:'https://www.betvictor.com',WA:'https://www.betway.com'};
const BASE='https://www.oddschecker.com/football/world-cup';
const DOW=__DOW__;

// ── GITHUB UPDATE CONFIG ───────────────────────────────────────────────────
const GH_OWNER='matigoldsmith';
const GH_REPO='polla-mundial-2026';
const GH_WORKFLOW='update.yml';

function getLEV(m){const w=m.win_pred;if(!w||w==='Empate')return'E';if(w===m.local)return'L';return'V';}

// ── ODDS TABLES ────────────────────────────────────────────────────────────
function buildWinTable(m){
  const wt=m.win_table||{};const bks=BK_ORDER.filter(bk=>bk in wt);
  if(!bks.length)return'<p class="no-data">Sin datos</p>';
  const outcomes=[m.local,'Empate',m.visita];
  const bkFave={};bks.forEach(bk=>{let mn=Infinity,mo=null;outcomes.forEach(o=>{const v=(wt[bk]||{})[o];if(v&&v<mn){mn=v;mo=o;}});bkFave[bk]=mo;});
  let h=`<div class="tbl-scroll"><table class="odds-table"><thead><tr><th>Casa</th><th>${FLAGS[m.local]||''} ${m.local}</th><th>X</th><th>${FLAGS[m.visita]||''} ${m.visita}</th></tr></thead><tbody>`;
  bks.forEach(bk=>{const row=wt[bk]||{};h+=`<tr><td class="bk-name"><a href="${BK_URLS[bk]}" target="_blank">${BK_NAMES[bk]}</a></td>`;outcomes.forEach(o=>{const v=row[o];const isFave=bkFave[bk]===o;h+=`<td${isFave?' class="fave"':''}>${v?v.toFixed(2):'—'}</td>`;});h+='</tr>';});
  return h+'</tbody></table></div>';
}

function buildCSTable(m){
  const cs=m.cs_top||{};const scores=Object.keys(cs);
  if(!scores.length)return'<p class="no-data">Sin datos</p>';
  const bks=BK_ORDER.filter(bk=>scores.some(s=>bk in(cs[s]||{})));
  const bkMin={};bks.forEach(bk=>{let mn=Infinity,ms=null;scores.forEach(s=>{const v=(cs[s]||{})[bk];if(v&&v>=2.0&&v<mn){mn=v;ms=s;}});bkMin[bk]=ms;});
  let h=`<div class="tbl-scroll"><table class="odds-table"><thead><tr><th>Score</th>${bks.map(bk=>`<th>${BK_NAMES[bk]}</th>`).join('')}</tr></thead><tbody>`;
  scores.forEach(s=>{const isBest=s===m.cs_refined;h+=`<tr><td class="score-col${isBest?' best-score':''}">${s}${isBest?' ★':''}</td>`;bks.forEach(bk=>{const raw=(cs[s]||{})[bk];const v=raw&&raw>=2.0?raw:null;const isFave=bkMin[bk]===s;h+=`<td${isFave?' class="fave"':''}>${v?v.toFixed(2):'—'}</td>`;});h+='</tr>';});
  return h+'</tbody></table></div>';
}

// ── RECOMMENDATION ─────────────────────────────────────────────────────────
function buildRecommendation(m){
  const cs=m.cs_top||{};const scores=Object.keys(cs);
  const bkFave={};
  BK_ORDER.forEach(bk=>{let best=null,bestO=Infinity;scores.forEach(s=>{const v=(cs[s]||{})[bk];if(v&&v>=2.0&&v<bestO){bestO=v;best=s;}});if(best)bkFave[bk]={score:best,odds:bestO};});
  const bks=Object.keys(bkFave);if(!bks.length)return'';
  const votes={};bks.forEach(bk=>{const s=bkFave[bk].score;votes[s]=(votes[s]||0)+1;});
  const total=bks.length;
  const sorted=Object.entries(votes).sort((a,b)=>b[1]-a[1]);
  const winner=sorted[0][0],wCount=sorted[0][1],pct=wCount/total;
  const nc=pct>=0.75?'#3b6d11':pct>=0.55?'#854f0b':'#993c1d';
  const nb=pct>=0.75?'#eaf3de':pct>=0.55?'#faeeda':'#faece7';
  const bars=sorted.map(([s,c])=>{const iw=s===winner,bp=Math.round(c/total*100);return`<div class="bar-row"><span class="bar-label${iw?' bar-win':''}">${s}</span><div class="bar-track"><div class="bar-fill${iw?' bar-fill-win':''}" style="width:${bp}%"></div></div><span class="bar-pct${iw?' bar-pct-win':''}">${c}/${total} (${bp}%)</span></div>`;}).join('');
  const pills=BK_ORDER.filter(bk=>bk in bkFave).map(bk=>{const s=bkFave[bk].score,iw=s===winner;return`<span class="pill${iw?' pill-win':''}">${BK_NAMES[bk]}: ${s}</span>`;}).join('');
  const ovrHTML=m.cs_overridden?`<div class="ovr-note">⚠️ Las casas preferían <strong>${winner}</strong> pero <strong>${m.win_pred}</strong> gana — imposible empate. Se usó <strong>${m.cs_refined}</strong></div>`:'';
  return`<div class="det-section"><div class="det-title">Cómo se eligió el marcador</div><div class="bars">${bars}</div><div class="pills">${pills}</div><div class="nivel-badge" style="background:${nb};color:${nc}">${m.cs_nivel} ${pct>=0.75?'Mayoría clara':pct>=0.55?'Mayoría débil':'Sin mayoría'} · ${Math.round(pct*100)}% de acuerdo</div>${ovrHTML}</div>`;
}

// ── DETAIL PANEL ───────────────────────────────────────────────────────────
function buildDetail(m){
  const ocW=`${BASE}/${m.slug}/winner`,ocC=`${BASE}/${m.slug}/correct-score`;
  const links=[
    `<a class="det-link" href="${ocW}" target="_blank">1X2 ↗</a>`,
    `<a class="det-link" href="${ocC}" target="_blank">Marcador ↗</a>`,
    ...BK_ORDER.filter(bk=>bk in(m.win_table||{})).map(bk=>`<a class="det-link" href="${BK_URLS[bk]}" target="_blank">${BK_NAMES[bk]} ↗</a>`)
  ].join('');
  return`<div class="detail-links">${links}</div>
  ${buildRecommendation(m)}
  <div class="det-section"><div class="det-title">Cuotas 1X2</div>${buildWinTable(m)}</div>
  <div class="det-section"><div class="det-title">Top marcadores · Recomendado: <strong class="rec-score">${m.cs_refined||'—'}</strong>${m.cs_overridden?' <span class="ovr-tag">(corregido)</span>':''}</div>${buildCSTable(m)}</div>`;
}

// ── RENDER MATCHES ─────────────────────────────────────────────────────────
const byDate={};DATA.forEach(m=>{if(!byDate[m.fecha])byDate[m.fecha]=[];byDate[m.fecha].push(m);});
const root=document.getElementById('root');
const dateKeys=Object.keys(byDate);
const dayAnchors={};

dateKeys.forEach(fecha=>{
  const block=document.createElement('div');block.className='day-block';
  const anchor=document.createElement('div');anchor.id='day_'+fecha.replace(' ','_');
  dayAnchors[fecha]=anchor.id;
  block.appendChild(anchor);

  const dayHdr=document.createElement('div');dayHdr.className='day-title';
  dayHdr.textContent=DOW[fecha]||fecha;
  block.appendChild(dayHdr);

  byDate[fecha].forEach(m=>{
    const ovr=m.cs_overridden,lev=getLEV(m),lf=FLAGS[m.local]||'🏳',vf=FLAGS[m.visita]||'🏳';
    const levCls=lev==='L'?'L':lev==='V'?'V':'E',levTxt=lev==='E'?'Empate':m.win_pred;
    const id='m_'+m.slug.replace(/-/g,'_');
    const wrap=document.createElement('div');wrap.className='match-wrap';
    wrap.innerHTML=`<div class="match${ovr?' ovr':''}" id="${id}" onclick="toggle('${id}')">
      <div class="meta">
        <div class="hora">${m.hora}</div>
        <div class="ciudad">${m.ciudad}</div>
        <span class="grp-badge">G${m.grp}·J${m.j}</span>
      </div>
      <div class="teams">
        <div class="team-row"><span class="flag">${lf}</span><span class="tname${lev==='L'?' bold':''}">${m.local}</span></div>
        <div class="team-row"><span class="flag">${vf}</span><span class="tname${lev==='V'?' bold':''}">${m.visita}</span></div>
      </div>
      <div class="right">
        <span class="result ${levCls}">${levTxt}</span>
        <span class="score${ovr?' ovr':''}">${m.cs_refined||'—'}</span>
        <div class="bottom-row"><span class="cons">${m.cs_nivel||''}</span><span class="chevron" id="chv_${id}">▾</span></div>
      </div>
    </div>
    <div class="detail" id="det_${id}">${buildDetail(m)}</div>`;
    block.appendChild(wrap);
  });
  root.appendChild(block);
});

function toggle(id){
  const d=document.getElementById('det_'+id),c=document.getElementById('chv_'+id),card=document.getElementById(id),o=d.classList.contains('open');
  d.classList.toggle('open',!o);card.classList.toggle('open',!o);c.classList.toggle('open',!o);
}

// ── TAB NAVIGATION ─────────────────────────────────────────────────────────
function showTab(tab){
  document.getElementById('tab-partidos').style.display=tab==='partidos'?'block':'none';
  document.getElementById('tab-update').style.display=tab==='update'?'block':'none';
  document.getElementById('nav-partidos').classList.toggle('active',tab==='partidos');
  document.getElementById('nav-update').classList.toggle('active',tab==='update');
  if(tab==='update')loadRunStatus();
}

// ── DAY JUMP MENU ──────────────────────────────────────────────────────────
function buildDayMenu(){
  const sel=document.getElementById('day-jump');
  dateKeys.forEach(f=>{
    const o=document.createElement('option');o.value=dayAnchors[f];o.textContent=DOW[f]||f;sel.appendChild(o);
  });
  sel.addEventListener('change',()=>{
    const el=document.getElementById(sel.value);
    if(el)el.scrollIntoView({behavior:'smooth',block:'start'});
    sel.value='';
  });
}
buildDayMenu();

// ── GITHUB ACTIONS UPDATE ──────────────────────────────────────────────────
let pollTimer=null;

function ghToken(){return localStorage.getItem('gh_token')||'';}
function saveToken(t){localStorage.setItem('gh_token',t.trim());}

async function triggerUpdate(){
  const token=ghToken();
  if(!token){showUpdateStatus('error','Ingresa tu token primero');return;}
  const btn=document.getElementById('btn-update');
  btn.disabled=true;btn.textContent='Enviando…';
  setRunState({status:'queued',msg:'Enviando solicitud a GitHub…'});
  try{
    const res=await fetch(`https://api.github.com/repos/${GH_OWNER}/${GH_REPO}/actions/workflows/${GH_WORKFLOW}/dispatches`,{
      method:'POST',
      headers:{'Authorization':`token ${token}`,'Accept':'application/vnd.github.v3+json','Content-Type':'application/json'},
      body:JSON.stringify({ref:'main'})
    });
    if(res.status===204){
      setRunState({status:'queued',msg:'✅ Actualización enviada. Esperando inicio…'});
      setTimeout(()=>startPolling(),3000);
    } else {
      const err=await res.json().catch(()=>({}));
      setRunState({status:'error',msg:'Error: '+(err.message||res.status)});
      btn.disabled=false;btn.textContent='Actualizar todo';
    }
  } catch(e){
    setRunState({status:'error',msg:'Error de red: '+e.message});
    btn.disabled=false;btn.textContent='Actualizar todo';
  }
}

function startPolling(){
  if(pollTimer)clearInterval(pollTimer);
  loadRunStatus();
  pollTimer=setInterval(()=>loadRunStatus(),8000);
}

async function loadRunStatus(){
  try{
    const res=await fetch(`https://api.github.com/repos/${GH_OWNER}/${GH_REPO}/actions/runs?per_page=5`,{
      headers:{'Accept':'application/vnd.github.v3+json'}
    });
    if(!res.ok){if(pollTimer)clearInterval(pollTimer);return;}
    const data=await res.json();
    renderRuns(data.workflow_runs||[]);
  }catch(e){/* silencioso */}
}

function renderRuns(runs){
  const el=document.getElementById('runs-list');
  if(!runs.length){el.innerHTML='<p class="run-empty">Sin ejecuciones recientes</p>';return;}

  // Check if any run is active — keep polling
  const anyActive=runs.some(r=>r.status==='queued'||r.status==='in_progress');
  if(!anyActive&&pollTimer){clearInterval(pollTimer);pollTimer=null;
    // Re-enable button
    const btn=document.getElementById('btn-update');btn.disabled=false;btn.textContent='Actualizar todo';
    // If last run just completed, show reload banner
    if(runs[0]&&runs[0].conclusion==='success'){showReloadBanner();}
  }

  el.innerHTML=runs.slice(0,5).map(r=>{
    const st=r.status,co=r.conclusion;
    let icon,cls,label;
    if(st==='queued'){icon='⏳';cls='run-queued';label='En cola';}
    else if(st==='in_progress'){icon='🔄';cls='run-running';label='Corriendo…';}
    else if(co==='success'){icon='✅';cls='run-ok';label='Completado';}
    else if(co==='failure'){icon='❌';cls='run-fail';label='Falló';}
    else{icon='⬜';cls='run-other';label=co||st;}
    const d=new Date(r.created_at);
    const ago=timeAgo(d);
    return`<div class="run-item ${cls}">
      <div class="run-icon">${icon}</div>
      <div class="run-info">
        <div class="run-label">${label}</div>
        <div class="run-time">${ago}</div>
      </div>
      <a href="${r.html_url}" target="_blank" class="run-link">Ver log ↗</a>
    </div>`;
  }).join('');

  // Also update the last-run indicator in update state
  if(runs[0]){setRunState({status:runs[0].status,conclusion:runs[0].conclusion,created:runs[0].created_at});}
}

function setRunState({status,msg,conclusion,created}){
  const el=document.getElementById('run-state');
  let html='';
  if(msg){html=`<div class="state-msg">${msg}</div>`;}
  el.innerHTML=html;
}

function showReloadBanner(){
  const b=document.getElementById('reload-banner');
  if(b)b.style.display='flex';
}

function timeAgo(d){
  const s=Math.floor((Date.now()-d)/1000);
  if(s<60)return'hace '+s+'s';
  if(s<3600)return'hace '+Math.floor(s/60)+'min';
  if(s<86400)return'hace '+Math.floor(s/3600)+'h';
  return'hace '+Math.floor(s/86400)+'d';
}

function showUpdateStatus(type,msg){
  const el=document.getElementById('run-state');
  el.innerHTML=`<div class="state-msg ${type==='error'?'state-err':''}">${msg}</div>`;
}

// Token setup
document.getElementById('token-save').addEventListener('click',()=>{
  const val=document.getElementById('token-input').value;
  if(!val){return;}
  saveToken(val);
  document.getElementById('token-input').value='';
  document.getElementById('token-status').textContent='Token guardado ✓';
  setTimeout(()=>{document.getElementById('token-status').textContent='';},2000);
});

// Load initial state
if(ghToken()){
  document.getElementById('token-indicator').textContent='Token: guardado ✓';
  document.getElementById('token-indicator').className='token-ok';
} else {
  document.getElementById('token-indicator').textContent='Token: no configurado';
  document.getElementById('token-indicator').className='token-missing';
}

// Pre-load run status silently
loadRunStatus();
"""

    js = js.replace('__DATA__', data_js)
    js = js.replace('__FLAGS__', flags_js)
    js = js.replace('__DOW__', dow_js)

    html = f"""<!DOCTYPE html>
<html lang="es"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<title>Polla Mundial 2026</title>
<style>
/* ── RESET & BASE ─────────────────────────────────────────────────────────── */
:root{{color-scheme:light;--bg:#f5f5f2;--card:#fff;--border:#e8e8e4;--text:#1a1a1a;--sub:#888;--accent:#2563eb;--nav-h:62px}}
*{{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}}
html{{scroll-behavior:smooth}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--text);font-size:14px;padding-bottom:var(--nav-h)}}

/* ── LAYOUT ───────────────────────────────────────────────────────────────── */
.container{{max-width:700px;margin:0 auto;padding:16px 12px 8px}}

/* ── HEADER ───────────────────────────────────────────────────────────────── */
.header{{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;gap:8px}}
.header h1{{font-size:17px;font-weight:700;flex:1}}
.updated{{font-size:11px;color:var(--sub);white-space:nowrap}}

/* ── DAY JUMP ─────────────────────────────────────────────────────────────── */
.day-jump-wrap{{margin-bottom:12px}}
#day-jump{{width:100%;padding:10px 12px;border-radius:10px;border:1px solid var(--border);background:var(--card);font-size:14px;color:var(--text);appearance:none;-webkit-appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%23999' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 12px center;cursor:pointer}}

/* ── DAY HEADERS ──────────────────────────────────────────────────────────── */
.day-block{{margin-bottom:4px}}
.day-title{{font-size:11px;font-weight:700;letter-spacing:.5px;color:var(--sub);text-transform:uppercase;padding:16px 4px 6px;border-bottom:1px solid var(--border)}}

/* ── MATCH CARDS ──────────────────────────────────────────────────────────── */
.match-wrap{{margin-bottom:4px}}
.match{{display:grid;grid-template-columns:60px 1fr auto;align-items:center;background:var(--card);border:.5px solid var(--border);border-radius:12px;padding:10px 12px;gap:10px;cursor:pointer;transition:background .15s;user-select:none;min-height:64px}}
.match:active{{background:#f0f0ec}}
.match.ovr{{border-left:3px solid #e0a020}}
.match.open{{border-radius:12px 12px 0 0;border-bottom-color:transparent}}
.meta{{font-size:10px;color:var(--sub);line-height:1.7}}
.hora{{font-size:13px;font-weight:700;color:#333}}
.ciudad{{font-size:10px;color:#aaa;line-height:1.4}}
.grp-badge{{display:inline-block;font-size:9px;font-weight:600;background:#f0f0ec;color:#999;border-radius:4px;padding:1px 5px;margin-top:2px}}
.teams{{min-width:0}}
.team-row{{display:flex;align-items:center;gap:6px;padding:2px 0}}
.flag{{font-size:16px;line-height:1;flex-shrink:0}}
.tname{{font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#333}}
.tname.bold{{font-weight:700;color:var(--text)}}
.right{{display:flex;flex-direction:column;align-items:flex-end;gap:3px;flex-shrink:0}}
.result{{font-size:10px;padding:2px 7px;border-radius:5px;font-weight:600;white-space:nowrap}}
.L{{background:#eaf3de;color:#3b6d11}}.E{{background:#faeeda;color:#854f0b}}.V{{background:#faece7;color:#993c1d}}
.score{{font-size:20px;font-weight:700;letter-spacing:2px;font-variant-numeric:tabular-nums;color:var(--text)}}
.score.ovr{{color:#c08010}}
.bottom-row{{display:flex;align-items:center;gap:6px}}
.cons{{font-size:13px}}
.chevron{{font-size:11px;color:#ccc;transition:transform .2s}}
.chevron.open{{transform:rotate(180deg)}}

/* ── DETAIL PANEL ─────────────────────────────────────────────────────────── */
.detail{{display:none;background:var(--card);border:.5px solid var(--border);border-top:none;border-radius:0 0 12px 12px;padding:14px 12px 16px}}
.detail.open{{display:block}}
.detail-links{{display:flex;gap:6px;margin-bottom:14px;flex-wrap:wrap}}
.det-link{{font-size:12px;color:var(--accent);text-decoration:none;background:#f0f4ff;border-radius:6px;padding:6px 10px;min-height:32px;display:flex;align-items:center}}
.det-link:active{{background:#dde8ff}}
.det-section{{margin-bottom:14px}}
.det-title{{font-size:10px;font-weight:700;color:var(--sub);text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px}}
.rec-score{{color:#2a6a2a}}
.ovr-tag{{font-size:10px;color:#c08010}}

/* ── ODDS TABLES ──────────────────────────────────────────────────────────── */
.tbl-scroll{{overflow-x:auto;-webkit-overflow-scrolling:touch;border-radius:8px;border:1px solid #f0f0ec}}
.odds-table{{width:100%;border-collapse:collapse;font-size:12px}}
.odds-table th{{text-align:left;color:var(--sub);font-weight:600;padding:6px 8px;background:#fafaf8;white-space:nowrap;border-bottom:1px solid #f0f0ec}}
.odds-table td{{padding:6px 8px;border-bottom:.5px solid #f8f8f5;white-space:nowrap}}
.odds-table tr:last-child td{{border-bottom:none}}
.bk-name a{{color:#3b71c8;text-decoration:none;font-weight:500}}
.fave{{background:#eaf3de;font-weight:700;color:#2a6a2a}}
.score-col{{font-weight:600;font-variant-numeric:tabular-nums}}
.best-score{{color:#c08010}}
.no-data{{font-size:12px;color:#aaa;font-style:italic;padding:8px 0}}

/* ── RECOMMENDATION BARS ──────────────────────────────────────────────────── */
.bars{{margin-bottom:8px}}
.bar-row{{display:flex;align-items:center;gap:8px;margin:4px 0}}
.bar-label{{font-size:12px;font-weight:500;color:#666;min-width:34px;font-variant-numeric:tabular-nums}}
.bar-label.bar-win{{font-weight:700;color:#2a6a2a}}
.bar-track{{flex:1;background:#f0f0ec;border-radius:4px;height:10px}}
.bar-fill{{height:100%;background:#ccc;border-radius:4px}}
.bar-fill.bar-fill-win{{background:#5a9a3a}}
.bar-pct{{font-size:11px;color:#999;min-width:70px;text-align:right}}
.bar-pct.bar-pct-win{{color:#2a6a2a}}
.pills{{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:8px}}
.pill{{font-size:11px;background:#f0f0ec;color:#888;border-radius:4px;padding:3px 7px}}
.pill.pill-win{{background:#eaf3de;color:#3b6d11;font-weight:600}}
.nivel-badge{{display:inline-block;font-size:11px;padding:3px 9px;border-radius:5px;font-weight:500}}
.ovr-note{{margin-top:8px;padding:8px 10px;background:#fff8e7;border-left:3px solid #c08010;border-radius:0 6px 6px 0;font-size:12px;line-height:1.5}}

/* ── BOTTOM NAV ───────────────────────────────────────────────────────────── */
#bottom-nav{{position:fixed;bottom:0;left:0;right:0;height:var(--nav-h);background:rgba(255,255,255,.95);border-top:1px solid var(--border);display:grid;grid-template-columns:1fr 1fr;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);z-index:100;padding-bottom:env(safe-area-inset-bottom,0)}}
.nav-btn{{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;border:none;background:transparent;color:var(--sub);font-size:10px;font-weight:500;cursor:pointer;transition:color .15s;padding:0;padding-bottom:4px}}
.nav-btn .nav-icon{{font-size:22px;line-height:1}}
.nav-btn.active{{color:var(--accent)}}
.nav-btn:active{{opacity:.7}}

/* ── UPDATE TAB ───────────────────────────────────────────────────────────── */
#tab-update{{display:none}}
.update-section{{background:var(--card);border-radius:14px;border:.5px solid var(--border);padding:16px;margin-bottom:12px}}
.update-section h2{{font-size:15px;font-weight:600;margin-bottom:12px}}
.token-indicator{{font-size:12px;margin-bottom:12px;padding:8px 10px;border-radius:8px;font-weight:500}}
.token-ok{{background:#eaf3de;color:#3b6d11}}
.token-missing{{background:#faeeda;color:#854f0b}}
.token-row{{display:flex;gap:8px;margin-bottom:8px}}
#token-input{{flex:1;padding:10px 12px;border-radius:10px;border:1px solid var(--border);font-size:14px;background:#fafaf8;min-width:0}}
#token-input:focus{{outline:none;border-color:var(--accent)}}
#token-save{{padding:10px 16px;background:var(--accent);color:#fff;border:none;border-radius:10px;font-size:14px;font-weight:600;cursor:pointer;white-space:nowrap;flex-shrink:0}}
#token-save:active{{opacity:.8}}
#token-status{{font-size:12px;color:#3b6d11;min-height:18px}}
.token-help{{font-size:11px;color:var(--sub);line-height:1.5;margin-top:6px}}
.token-help a{{color:var(--accent)}}
.update-btn{{width:100%;padding:14px;background:#16a34a;color:#fff;border:none;border-radius:12px;font-size:16px;font-weight:700;cursor:pointer;margin-top:4px;transition:background .15s}}
.update-btn:active{{background:#15803d}}
.update-btn:disabled{{background:#9ca3af;cursor:not-allowed}}
#run-state{{margin-top:10px;min-height:24px}}
.state-msg{{font-size:13px;color:var(--sub);padding:8px 0}}
.state-err{{color:#993c1d}}
.runs-title{{font-size:11px;font-weight:700;color:var(--sub);text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px}}
#runs-list{{display:flex;flex-direction:column;gap:8px}}
.run-item{{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:10px;background:#fafaf8;border:.5px solid var(--border)}}
.run-item.run-running{{background:#eff6ff;border-color:#bfdbfe}}
.run-item.run-queued{{background:#fafaf8}}
.run-item.run-ok{{background:#f0fdf4;border-color:#bbf7d0}}
.run-item.run-fail{{background:#fff1f2;border-color:#fecdd3}}
.run-icon{{font-size:20px;flex-shrink:0}}
.run-info{{flex:1;min-width:0}}
.run-label{{font-size:13px;font-weight:600}}
.run-time{{font-size:11px;color:var(--sub)}}
.run-link{{font-size:11px;color:var(--accent);text-decoration:none;white-space:nowrap;padding:4px 8px;background:#f0f4ff;border-radius:6px}}
.run-empty{{font-size:12px;color:var(--sub);font-style:italic;padding:8px 0}}
#reload-banner{{display:none;align-items:center;justify-content:space-between;gap:10px;padding:12px 14px;background:#dcfce7;border-radius:10px;border:1px solid #86efac;margin-bottom:10px}}
.reload-text{{font-size:13px;color:#166534;font-weight:500}}
.reload-btn{{padding:8px 14px;background:#16a34a;color:#fff;border:none;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer}}
</style>
</head>
<body>

<!-- ── TAB: PARTIDOS ─────────────────────────────────────────────────────── -->
<div id="tab-partidos">
  <div class="container">
    <div class="header">
      <h1>⚽ Polla Mundial 2026</h1>
      <span class="updated">Actualizado: {now}</span>
    </div>
    <div class="day-jump-wrap">
      <select id="day-jump">
        <option value="">Ir a un día…</option>
      </select>
    </div>
    <div id="root"></div>
  </div>
</div>

<!-- ── TAB: ACTUALIZAR ───────────────────────────────────────────────────── -->
<div id="tab-update">
  <div class="container">

    <div id="reload-banner">
      <span class="reload-text">✅ Actualización completada</span>
      <button class="reload-btn" onclick="location.reload()">Recargar página</button>
    </div>

    <div class="update-section">
      <h2>🔄 Actualizar cuotas</h2>
      <div id="token-indicator" class="token-indicator token-missing">Token: no configurado</div>
      <div id="run-state"></div>
      <button class="update-btn" id="btn-update" onclick="triggerUpdate()">Actualizar todo</button>
    </div>

    <div class="update-section">
      <h2>🔑 Token de GitHub</h2>
      <div class="token-row">
        <input id="token-input" type="password" placeholder="ghp_xxxxxxxxxxxx">
        <button id="token-save">Guardar</button>
      </div>
      <div id="token-status"></div>
      <p class="token-help">
        Necesitas un token con scope <strong>repo</strong>.<br>
        Créalo en <a href="https://github.com/settings/tokens/new" target="_blank">github.com/settings/tokens</a>
      </p>
    </div>

    <div class="update-section">
      <div class="runs-title">Últimas ejecuciones</div>
      <div id="runs-list"><p class="run-empty">Cargando…</p></div>
    </div>

  </div>
</div>

<!-- ── BOTTOM NAV ────────────────────────────────────────────────────────── -->
<nav id="bottom-nav">
  <button class="nav-btn active" id="nav-partidos" onclick="showTab('partidos')">
    <span class="nav-icon">📅</span>
    Partidos
  </button>
  <button class="nav-btn" id="nav-update" onclick="showTab('update')">
    <span class="nav-icon">🔄</span>
    Actualizar
  </button>
</nav>

<script>
{js}
</script>
</body>
</html>"""
    return html


def main():
    json_path = os.path.join(DIR, 'polla_data_final.json')
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)

    now = datetime.datetime.now().strftime('%d %b %Y %H:%M')
    html = build_html(data, now)

    out_path = os.path.join(DIR, 'polla_mundial_2026.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ HTML generado: {out_path}")
    print(f"   {len(data)} partidos · {len(html)//1024} KB")


if __name__ == '__main__':
    main()
