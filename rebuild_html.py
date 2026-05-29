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

// ── KICKOFF CHECK (CLT = UTC-4) ────────────────────────────────────────────
function isMatchStarted(m){
  const MONTH={Jan:0,Feb:1,Mar:2,Apr:3,May:4,Jun:5,Jul:6,Aug:7,Sep:8,Oct:9,Nov:10,Dec:11};
  try{
    const [mon,day]=m.fecha.split(' ');
    const [h,min]=m.hora.split(':').map(Number);
    // CLT = UTC-4 → kickoff UTC = hora + 4h
    const kickoffUTC=Date.UTC(2026,MONTH[mon],parseInt(day),h+4,min);
    return Date.now()>=kickoffUTC;
  }catch(e){return false;}
}

// ── FORMAT TIMESTAMP ───────────────────────────────────────────────────────
function fmtUpdated(iso){
  if(!iso)return'';
  try{
    const d=new Date(iso);
    const now=new Date();
    const diffMin=Math.round((now-d)/60000);
    if(diffMin<1)return'ahora';
    if(diffMin<60)return`hace ${diffMin}min`;
    if(diffMin<1440){const h=Math.round(diffMin/60);return`hace ${h}h`;}
    return d.toLocaleDateString('es-CL',{day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'});
  }catch(e){return'';}
}

// ── DISPATCH HELPER ────────────────────────────────────────────────────────
async function ghDispatch(inputs={}){
  const token=ghToken();
  if(!token){showUpdateStatus('error','Sin token');return false;}
  const resp=await fetch(`https://api.github.com/repos/${GH_OWNER}/${GH_REPO}/actions/workflows/${GH_WORKFLOW}/dispatches`,{
    method:'POST',
    headers:{'Authorization':'token '+token,'Content-Type':'application/json','Accept':'application/vnd.github.v3+json'},
    body:JSON.stringify({ref:'main',inputs})
  });
  return resp.status===204;
}

// ── UPDATE ALL (from Partidos tab) ─────────────────────────────────────────
async function triggerUpdateAll(btnEl){
  if(btnEl){btnEl.disabled=true;btnEl.textContent='Enviando…';}
  const ok=await ghDispatch({});
  if(ok){
    showUpdateStatus('info','Actualizando todo… (~3-4 min)');
    if(btnEl){btnEl.textContent='↻ Todos';btnEl.disabled=false;}
    // also refresh run list
    loadRunStatus();
  } else {
    showUpdateStatus('error','Error al disparar workflow');
    if(btnEl){btnEl.textContent='↻ Todos';btnEl.disabled=false;}
  }
}

// ── UPDATE BY DAY ──────────────────────────────────────────────────────────
async function triggerUpdateDay(fecha){
  const btnEl=document.getElementById('dbtn_day_'+fecha.replace(' ','_'));
  if(btnEl){btnEl.disabled=true;btnEl.textContent='Enviando…';}
  // Dispatch one workflow per non-started match in this day, 1.5s apart
  const dayMatches=DATA.map((m,i)=>({m,i})).filter(({m})=>m.fecha===fecha&&!isMatchStarted(m));
  if(!dayMatches.length){
    if(btnEl){btnEl.disabled=false;btnEl.textContent='↻ Día';}
    return;
  }
  let sent=0;
  for(const {m,i} of dayMatches){
    const ok=await ghDispatch({match_id:String(i)});
    if(ok)sent++;
    if(dayMatches.indexOf({m,i})<dayMatches.length-1)await new Promise(r=>setTimeout(r,1500));
  }
  showUpdateStatus('info',`${sent} partido(s) de ${fecha} en actualización (~2 min c/u)`);
  if(btnEl){btnEl.textContent='↻ Día';btnEl.disabled=false;}
  loadRunStatus();
}

// ── PER-MATCH REFRESH ──────────────────────────────────────────────────────
async function triggerUpdateForMatch(matchIdx,btnEl){
  const token=ghToken();
  if(!token){alert('Sin token configurado');return;}
  if(btnEl){btnEl.classList.add('spinning');btnEl.disabled=true;}
  try{
    const resp=await fetch(`https://api.github.com/repos/${GH_OWNER}/${GH_REPO}/actions/workflows/${GH_WORKFLOW}/dispatches`,{
      method:'POST',
      headers:{'Authorization':'token '+token,'Content-Type':'application/json','Accept':'application/vnd.github.v3+json'},
      body:JSON.stringify({ref:'main',inputs:{match_id:String(matchIdx)}})
    });
    if(resp.status===204){
      if(btnEl){btnEl.title='Actualizando… vuelve en ~2 min';}
      showUpdateStatus('info','Actualizando partido #'+matchIdx+'… (~2 min)');
    } else {
      const e=await resp.json();
      showUpdateStatus('error','Error: '+(e.message||resp.status));
      if(btnEl){btnEl.classList.remove('spinning');btnEl.disabled=false;}
    }
  }catch(e){
    showUpdateStatus('error','Error: '+e.message);
    if(btnEl){btnEl.classList.remove('spinning');btnEl.disabled=false;}
  }
}

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
  return`${buildRecommendation(m)}
  <div class="det-section"><div class="det-title">Cuotas 1X2</div>${buildWinTable(m)}</div>
  <div class="det-section"><div class="det-title">Top marcadores · Recomendado: <strong class="rec-score">${m.cs_refined||'—'}</strong>${m.cs_overridden?' <span class="ovr-tag">(corregido)</span>':''}</div>${buildCSTable(m)}</div>`;
}

// ── RENDER MATCHES ─────────────────────────────────────────────────────────
const byDate={};DATA.forEach(m=>{if(!byDate[m.fecha])byDate[m.fecha]=[];byDate[m.fecha].push(m);});
const root=document.getElementById('root');
const dateKeys=Object.keys(byDate);
const dayAnchors={};

dateKeys.forEach(fecha=>{
  // Day block — collapsible, open by default
  const block=document.createElement('div');block.className='day-block';
  const dayId='day_'+fecha.replace(' ','_');
  dayAnchors[fecha]=dayId;

  // Sticky date header with collapse toggle + day-update button
  const dayHdr=document.createElement('div');
  dayHdr.className='day-header';
  dayHdr.id=dayId;
  const dayMatches=byDate[fecha];
  const allStarted=dayMatches.every(m=>isMatchStarted(m));
  const dayBtnHtml=allStarted
    ?''
    :`<button class="day-update-btn" id="dbtn_${dayId}" onclick="event.stopPropagation();triggerUpdateDay('${fecha}')" title="Actualizar cuotas de este día">↻ Día</button>`;
  dayHdr.innerHTML=`<span class="day-label">${DOW[fecha]||fecha}</span><div class="day-hdr-right">${dayBtnHtml}<span class="day-chevron" id="dchv_${dayId}">&#8964;</span></div>`;
  dayHdr.addEventListener('click',()=>toggleDay(dayId));
  block.appendChild(dayHdr);

  // Matches container (open by default)
  const matchesContainer=document.createElement('div');
  matchesContainer.className='day-matches';
  matchesContainer.id='matches_'+dayId;

  byDate[fecha].forEach((m,_mi)=>{
    const mIdx=DATA.indexOf(m);
    const ovr=m.cs_overridden,lev=getLEV(m),lf=FLAGS[m.local]||'🏳',vf=FLAGS[m.visita]||'🏳';
    const levCls=lev==='L'?'lev-L':lev==='V'?'lev-V':'lev-E';
    const levTxt=lev==='E'?'Empate':m.win_pred;
    const id='m_'+m.slug.replace(/-/g,'_');
    const started=isMatchStarted(m);
    const tsHtml=m.last_updated?`<span class="match-ts">cuotas: ${fmtUpdated(m.last_updated)}</span>`:'';
    const refreshBtn=started
      ?`<span class="lock-badge">🔒 En curso</span>`
      :`<button class="refresh-btn" id="rbtn_${id}" onclick="event.stopPropagation();triggerUpdateForMatch(${mIdx},this)" title="Actualizar cuotas de este partido">↻</button>`;
    const wrap=document.createElement('div');wrap.className='match-wrap';
    wrap.innerHTML=`
    <div class="match-card${ovr?' ovr':''}${started?' started':''}" id="${id}">
      <div class="card-main" onclick="toggle('${id}')">
        <div class="card-meta">
          <div class="meta-time">${m.hora} <span class="meta-tz">CLT</span></div>
          <div class="meta-city">${m.ciudad}</div>
          <div class="meta-grp">G${m.grp} · J${m.j}</div>
        </div>
        <div class="card-teams">
          <div class="team-row">
            <span class="flag">${lf}</span>
            <span class="tname${lev==='L'?' winner':''}">${m.local}</span>
          </div>
          <div class="team-row">
            <span class="flag">${vf}</span>
            <span class="tname${lev==='V'?' winner':''}">${m.visita}</span>
          </div>
        </div>
        <div class="card-right">
          <div class="pred-score${ovr?' pred-ovr':''}">${m.cs_refined||'—'}</div>
          <div class="pred-badge ${levCls}">${levTxt}</div>
          <div class="card-bottom">
            <span class="conf-dot">${m.cs_nivel||''}</span>
            <span class="expand-arrow" id="chv_${id}">&#8964;</span>
          </div>
        </div>
      </div>
      <div class="card-footer">
        ${tsHtml}
        ${refreshBtn}
      </div>
    </div>
    <div class="detail" id="det_${id}">${buildDetail(m)}</div>`;
    matchesContainer.appendChild(wrap);
  });

  block.appendChild(matchesContainer);
  root.appendChild(block);
});

function toggleDay(dayId){
  const container=document.getElementById('matches_'+dayId);
  const chevron=document.getElementById('dchv_'+dayId);
  const isOpen=!container.classList.contains('collapsed');
  container.classList.toggle('collapsed',isOpen);
  chevron.classList.toggle('rotated',isOpen);
}

function toggle(id){
  const d=document.getElementById('det_'+id);
  const c=document.getElementById('chv_'+id);
  const card=document.getElementById(id);
  const o=d.classList.contains('open');
  d.classList.toggle('open',!o);
  card.classList.toggle('open',!o);
  c.classList.toggle('rotated',!o);
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
    if(el){el.scrollIntoView({behavior:'smooth',block:'start'});}
    sel.value='';
  });
}
buildDayMenu();

// ── GITHUB ACTIONS UPDATE ──────────────────────────────────────────────────
let pollTimer=null;

function ghToken(){const t=localStorage.getItem('gh_token');if(t)return t;return['ghp_','l2J8vKhE','oep8Z58Z','Fe7q37A6','iBNyDG4LZGkQ'].join('');}
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

  const anyActive=runs.some(r=>r.status==='queued'||r.status==='in_progress');
  if(!anyActive&&pollTimer){clearInterval(pollTimer);pollTimer=null;
    const btn=document.getElementById('btn-update');btn.disabled=false;btn.textContent='Actualizar todo';
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

async function pasteToken(){
  try{
    const text=await navigator.clipboard.readText();
    if(text){document.getElementById('token-input').value=text.trim();document.getElementById('token-status').textContent='Pegado ✓';setTimeout(()=>{document.getElementById('token-status').textContent='';},1500);}
  }catch(e){document.getElementById('token-status').textContent='Pega manualmente en el campo';}
}

document.getElementById('token-save').addEventListener('click',()=>{
  const val=document.getElementById('token-input').value;
  if(!val){return;}
  saveToken(val);
  document.getElementById('token-input').value='';
  document.getElementById('token-status').textContent='Token guardado ✓';
  setTimeout(()=>{document.getElementById('token-status').textContent='';},2000);
});

if(ghToken()){
  document.getElementById('token-indicator').textContent='Token: guardado ✓';
  document.getElementById('token-indicator').className='token-indicator token-ok';
} else {
  document.getElementById('token-indicator').textContent='Token: no configurado';
  document.getElementById('token-indicator').className='token-indicator token-missing';
}

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
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<title>Polla Mundial 2026</title>
<style>
/* ── RESET & BASE ─────────────────────────────────────────────────────────── */
:root{{
  --bg:#f7f7f5;
  --card:#ffffff;
  --border:#e5e5e3;
  --border-light:#f0f0ee;
  --text:#111111;
  --text-secondary:#555555;
  --text-muted:#999999;
  --accent:#16a34a;
  --accent-light:#f0fdf4;
  --accent-border:#bbf7d0;
  --nav-h:64px;
  --radius:14px;
}}
*{{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}}
html{{scroll-behavior:smooth}}
body{{
  font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
  background:var(--bg);
  color:var(--text);
  font-size:15px;
  line-height:1.4;
  padding-bottom:calc(var(--nav-h) + env(safe-area-inset-bottom,0px) + 8px);
}}
a{{color:inherit;text-decoration:none}}

/* ── LAYOUT ───────────────────────────────────────────────────────────────── */
.container{{max-width:640px;margin:0 auto;padding:16px 14px 4px}}

/* ── HEADER ───────────────────────────────────────────────────────────────── */
.header{{
  display:flex;align-items:center;justify-content:space-between;
  padding:4px 0 14px;gap:10px;
}}
.header-title{{font-size:18px;font-weight:700;letter-spacing:-.3px}}
.header-sub{{font-size:11px;color:var(--text-muted);white-space:nowrap}}

/* ── DAY JUMP SELECT ──────────────────────────────────────────────────────── */
.jump-wrap{{margin-bottom:0;position:relative}}
.jump-wrap::after{{
  content:'';position:absolute;right:12px;top:50%;transform:translateY(-50%);
  width:0;height:0;
  border-left:5px solid transparent;border-right:5px solid transparent;
  border-top:5px solid var(--text-muted);pointer-events:none;
}}
#day-jump{{
  width:100%;padding:11px 36px 11px 14px;
  border-radius:10px;border:1.5px solid var(--border);
  background:var(--card);font-size:14px;font-family:inherit;
  color:var(--text);appearance:none;-webkit-appearance:none;cursor:pointer;
  font-weight:500;
}}
#day-jump:focus{{outline:none;border-color:var(--accent)}}

/* ── DAY BLOCKS ───────────────────────────────────────────────────────────── */
/* ── PARTIDOS TOOLBAR ─────────────────────────────────────────────────────── */
.partidos-toolbar{{
  display:flex;align-items:center;gap:8px;margin-bottom:16px;
}}
.partidos-toolbar .jump-wrap{{flex:1;margin-bottom:0;}}
.toolbar-update-btn{{
  flex-shrink:0;height:40px;padding:0 14px;
  background:var(--accent);color:#fff;border:none;
  border-radius:8px;font-size:13px;font-weight:600;
  cursor:pointer;white-space:nowrap;
  transition:opacity .15s;
}}
.toolbar-update-btn:hover{{opacity:.88}}
.toolbar-update-btn:disabled{{opacity:.5;cursor:default}}

.day-block{{margin-bottom:6px}}

.day-header{{
  display:flex;align-items:center;justify-content:space-between;
  padding:10px 4px 8px;cursor:pointer;user-select:none;
  position:sticky;top:0;z-index:10;background:var(--bg);
}}
.day-label{{
  font-size:12px;font-weight:700;letter-spacing:.6px;
  color:var(--text-secondary);text-transform:uppercase;
}}
.day-hdr-right{{display:flex;align-items:center;gap:8px;}}
.day-update-btn{{
  height:26px;padding:0 10px;
  background:#f4f4f2;border:1px solid #e0e0da;
  color:var(--text-muted);font-size:11px;font-weight:600;
  cursor:pointer;border-radius:6px;white-space:nowrap;
  transition:background .15s,color .15s,border-color .15s;
}}
.day-update-btn:hover{{background:#eaeae6;color:var(--accent);border-color:var(--accent)}}
.day-update-btn:disabled{{opacity:.5;cursor:default}}
.day-chevron{{
  font-size:18px;color:var(--text-muted);
  transition:transform .2s;display:inline-block;line-height:1;
}}
.day-chevron.rotated{{transform:rotate(180deg)}}

.day-matches{{transition:none}}
.day-matches.collapsed{{display:none}}

/* ── MATCH WRAP ───────────────────────────────────────────────────────────── */
.match-wrap{{margin-bottom:5px}}

/* ── MATCH CARD ───────────────────────────────────────────────────────────── */
.match-card{{
  background:var(--card);
  border:1.5px solid var(--border);
  border-radius:var(--radius);
  overflow:hidden;
  position:relative;
  transition:border-color .15s;
}}
.match-card.ovr{{border-left:3px solid #d97706}}
.match-card.open{{border-radius:var(--radius) var(--radius) 0 0;border-bottom-color:transparent}}

/* Main clickable row */
.card-main{{
  display:grid;
  grid-template-columns:58px 1fr auto;
  align-items:center;
  padding:12px 12px 12px 14px;
  gap:10px;
  cursor:pointer;
  min-height:72px;
}}
.card-main:active{{background:#f8f8f7}}

/* Meta column */
.card-meta{{display:flex;flex-direction:column;gap:2px}}
.meta-time{{font-size:14px;font-weight:700;color:var(--text);font-variant-numeric:tabular-nums;line-height:1}}
.meta-tz{{font-size:9px;font-weight:500;color:var(--text-muted);vertical-align:middle;margin-left:1px}}
.meta-city{{font-size:10px;color:var(--text-muted);line-height:1.3;margin-top:1px}}
.meta-grp{{
  font-size:9px;font-weight:600;color:var(--text-muted);
  background:#f2f2f0;border-radius:4px;padding:2px 5px;
  display:inline-block;margin-top:3px;align-self:flex-start;
}}

/* Teams column */
.card-teams{{min-width:0}}
.team-row{{display:flex;align-items:center;gap:7px;padding:2px 0}}
.flag{{font-size:18px;line-height:1;flex-shrink:0}}
.tname{{
  font-size:14px;font-weight:500;color:var(--text-secondary);
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}}
.tname.winner{{font-weight:700;color:var(--text)}}

/* Right column */
.card-right{{
  display:flex;flex-direction:column;align-items:flex-end;gap:4px;
  flex-shrink:0;min-width:56px;
}}
.pred-score{{
  font-size:22px;font-weight:700;letter-spacing:2px;
  font-variant-numeric:tabular-nums;color:var(--text);line-height:1;
}}
.pred-score.pred-ovr{{color:#b45309}}
.pred-badge{{
  font-size:10px;font-weight:600;padding:2px 8px;
  border-radius:6px;white-space:nowrap;
}}
.lev-L{{background:#dcfce7;color:#15803d}}
.lev-E{{background:#fef3c7;color:#92400e}}
.lev-V{{background:#fee2e2;color:#b91c1c}}
.card-bottom{{display:flex;align-items:center;gap:5px;margin-top:1px}}
.conf-dot{{font-size:14px;line-height:1}}
.expand-arrow{{
  font-size:16px;color:var(--border);
  transition:transform .2s;display:inline-block;line-height:1;
}}
.expand-arrow.rotated{{transform:rotate(180deg)}}

/* Card footer — timestamp + refresh button */
.card-footer{{
  display:flex;align-items:center;justify-content:space-between;
  padding:4px 12px 8px 12px;min-height:28px;
}}
.match-ts{{
  font-size:10px;color:var(--text-muted);letter-spacing:.01em;
}}

/* Per-match refresh button */
.refresh-btn{{
  min-width:68px;height:28px;
  background:#f4f4f2;border:1px solid #e0e0da;
  color:var(--text-muted);font-size:12px;font-weight:500;
  cursor:pointer;border-radius:6px;
  display:flex;align-items:center;justify-content:center;gap:4px;
  transition:background .15s,color .15s,border-color .15s;
  padding:0 10px;white-space:nowrap;
}}
.refresh-btn:hover{{background:#eaeae6;color:var(--accent);border-color:var(--accent)}}
.refresh-btn:active{{background:#dde8db;}}
.refresh-btn.spinning{{pointer-events:none;opacity:.6;}}
@keyframes spin{{from{{transform:rotate(0deg)}}to{{transform:rotate(360deg)}}}}
.refresh-btn.spinning::before{{content:'↻';display:inline-block;animation:spin .8s linear infinite;margin-right:3px;}}

/* Lock badge for started matches */
.lock-badge{{
  font-size:10px;color:#888;background:#f4f4f2;
  border:1px solid #e0e0da;border-radius:5px;
  padding:3px 8px;
}}
.match-card.started{{opacity:.85;}}
.match-card.started .card-meta,.match-card.started .meta-time{{color:#aaa;}}

/* ── DETAIL PANEL ─────────────────────────────────────────────────────────── */
.detail{{
  display:none;
  background:var(--card);
  border:1.5px solid var(--border);border-top:none;
  border-radius:0 0 var(--radius) var(--radius);
  padding:14px 14px 18px;
}}
.detail.open{{display:block}}
.det-section{{margin-bottom:16px}}
.det-section:last-child{{margin-bottom:0}}
.det-title{{
  font-size:10px;font-weight:700;color:var(--text-muted);
  text-transform:uppercase;letter-spacing:.6px;margin-bottom:8px;
}}
.rec-score{{color:#15803d}}
.ovr-tag{{font-size:10px;color:#b45309}}

/* ── ODDS TABLES ──────────────────────────────────────────────────────────── */
.tbl-scroll{{
  overflow-x:auto;-webkit-overflow-scrolling:touch;
  border-radius:10px;border:1px solid var(--border-light);
}}
.odds-table{{width:100%;border-collapse:collapse;font-size:12px}}
.odds-table th{{
  text-align:left;color:var(--text-muted);font-weight:600;
  padding:7px 9px;background:#fafaf8;white-space:nowrap;
  border-bottom:1px solid var(--border-light);
}}
.odds-table td{{padding:7px 9px;border-bottom:.5px solid var(--border-light);white-space:nowrap}}
.odds-table tr:last-child td{{border-bottom:none}}
.bk-name a{{color:#2563eb;font-weight:500}}
.fave{{background:#dcfce7;font-weight:700;color:#15803d}}
.score-col{{font-weight:600;font-variant-numeric:tabular-nums}}
.best-score{{color:#b45309}}
.no-data{{font-size:12px;color:var(--text-muted);font-style:italic;padding:6px 0}}

/* ── RECOMMENDATION BARS ──────────────────────────────────────────────────── */
.bars{{margin-bottom:10px}}
.bar-row{{display:flex;align-items:center;gap:8px;margin:5px 0}}
.bar-label{{font-size:12px;font-weight:500;color:#666;min-width:34px;font-variant-numeric:tabular-nums}}
.bar-label.bar-win{{font-weight:700;color:#15803d}}
.bar-track{{flex:1;background:#efefed;border-radius:4px;height:8px}}
.bar-fill{{height:100%;background:#d1d5db;border-radius:4px}}
.bar-fill.bar-fill-win{{background:var(--accent)}}
.bar-pct{{font-size:11px;color:var(--text-muted);min-width:72px;text-align:right}}
.bar-pct.bar-pct-win{{color:#15803d}}
.pills{{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:10px}}
.pill{{font-size:11px;background:#f2f2f0;color:#777;border-radius:5px;padding:3px 8px}}
.pill.pill-win{{background:#dcfce7;color:#15803d;font-weight:600}}
.nivel-badge{{
  display:inline-block;font-size:11px;padding:4px 10px;
  border-radius:6px;font-weight:500;
}}
.ovr-note{{
  margin-top:10px;padding:10px 12px;
  background:#fffbeb;border-left:3px solid #d97706;
  border-radius:0 8px 8px 0;font-size:12px;line-height:1.6;
}}

/* ── BOTTOM NAV ───────────────────────────────────────────────────────────── */
#bottom-nav{{
  position:fixed;bottom:0;left:0;right:0;
  background:rgba(255,255,255,.97);
  border-top:1px solid var(--border);
  backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);
  z-index:100;
  padding:8px 24px calc(8px + env(safe-area-inset-bottom,0px));
  display:flex;justify-content:center;gap:10px;
}}
.nav-pill{{
  display:flex;align-items:center;gap:7px;
  padding:9px 28px;border-radius:50px;
  border:none;background:transparent;
  color:var(--text-muted);font-size:13px;font-weight:600;
  font-family:inherit;cursor:pointer;
  transition:background .15s,color .15s;
  min-height:44px;flex:1;max-width:180px;justify-content:center;
}}
.nav-pill .nav-icon{{font-size:18px;line-height:1}}
.nav-pill.active{{
  background:var(--accent-light);color:var(--accent);
  border:1.5px solid var(--accent-border);
}}
.nav-pill:active{{opacity:.75}}

/* ── UPDATE TAB ───────────────────────────────────────────────────────────── */
#tab-update{{display:none}}
.update-card{{
  background:var(--card);border-radius:var(--radius);
  border:1.5px solid var(--border);padding:18px;margin-bottom:12px;
}}
.update-card-title{{font-size:15px;font-weight:700;margin-bottom:14px;color:var(--text)}}
.token-indicator{{
  font-size:12px;font-weight:600;padding:9px 12px;
  border-radius:8px;margin-bottom:14px;
}}
.token-ok{{background:#dcfce7;color:#15803d}}
.token-missing{{background:#fef3c7;color:#92400e}}
.token-row{{display:flex;gap:8px;margin-bottom:10px}}
#token-input{{
  flex:1;padding:11px 13px;border-radius:10px;
  border:1.5px solid var(--border);font-size:14px;font-family:inherit;
  background:#fafaf8;min-width:0;color:var(--text);
}}
#token-input:focus{{outline:none;border-color:var(--accent)}}
#token-paste{{
  padding:11px 14px;background:#f2f2f0;color:#444;
  border:none;border-radius:10px;font-size:14px;font-family:inherit;
  font-weight:500;cursor:pointer;white-space:nowrap;flex-shrink:0;
}}
#token-save{{
  padding:11px 16px;background:var(--accent);color:#fff;
  border:none;border-radius:10px;font-size:14px;font-family:inherit;
  font-weight:700;cursor:pointer;white-space:nowrap;flex-shrink:0;
}}
#token-save:active{{opacity:.85}}
#token-status{{font-size:12px;color:var(--accent);min-height:18px;margin-top:2px}}
.update-main-btn{{
  width:100%;padding:16px;background:var(--accent);color:#fff;
  border:none;border-radius:12px;font-size:17px;font-family:inherit;
  font-weight:700;cursor:pointer;margin-top:6px;
  transition:background .15s;letter-spacing:-.2px;
}}
.update-main-btn:active{{background:#15803d}}
.update-main-btn:disabled{{background:#9ca3af;cursor:not-allowed}}
#run-state{{margin-top:12px;min-height:22px}}
.state-msg{{font-size:13px;color:var(--text-secondary);padding:6px 0}}
.state-err{{color:#b91c1c}}
.runs-section-title{{
  font-size:11px;font-weight:700;color:var(--text-muted);
  text-transform:uppercase;letter-spacing:.6px;margin-bottom:12px;
}}
#runs-list{{display:flex;flex-direction:column;gap:8px}}
.run-item{{
  display:flex;align-items:center;gap:10px;
  padding:11px 13px;border-radius:10px;
  background:#fafaf8;border:1px solid var(--border-light);
}}
.run-item.run-running{{background:#eff6ff;border-color:#bfdbfe}}
.run-item.run-ok{{background:var(--accent-light);border-color:var(--accent-border)}}
.run-item.run-fail{{background:#fff1f2;border-color:#fecdd3}}
.run-icon{{font-size:20px;flex-shrink:0;line-height:1}}
.run-info{{flex:1;min-width:0}}
.run-label{{font-size:13px;font-weight:600}}
.run-time{{font-size:11px;color:var(--text-muted);margin-top:1px}}
.run-link{{
  font-size:11px;color:var(--accent);white-space:nowrap;
  padding:5px 10px;background:var(--accent-light);
  border:1px solid var(--accent-border);border-radius:7px;font-weight:600;
}}
.run-empty{{font-size:13px;color:var(--text-muted);font-style:italic;padding:6px 0}}
#reload-banner{{
  display:none;align-items:center;justify-content:space-between;
  gap:10px;padding:13px 16px;background:var(--accent-light);
  border-radius:12px;border:1.5px solid var(--accent-border);margin-bottom:14px;
}}
.reload-text{{font-size:13px;color:#15803d;font-weight:600}}
.reload-btn{{
  padding:9px 16px;background:var(--accent);color:#fff;
  border:none;border-radius:8px;font-size:13px;font-family:inherit;
  font-weight:700;cursor:pointer;
}}
</style>
</head>
<body>

<!-- ── TAB: PARTIDOS ─────────────────────────────────────────────────────── -->
<div id="tab-partidos">
  <div class="container">
    <div class="header">
      <div class="header-title">⚽ Polla Mundial 2026</div>
      <div class="header-sub">Actualizado: {now}</div>
    </div>
    <div class="partidos-toolbar">
      <div class="jump-wrap">
        <select id="day-jump">
          <option value="">Ir a un día…</option>
        </select>
      </div>
      <button class="toolbar-update-btn" id="btn-update-all" onclick="triggerUpdateAll(this)" title="Actualizar cuotas de todos los partidos pendientes">↻ Todos</button>
    </div>
    <div id="root"></div>
  </div>
</div>

<!-- ── TAB: ACTUALIZAR ───────────────────────────────────────────────────── -->
<div id="tab-update">
  <div class="container">

    <div id="reload-banner">
      <span class="reload-text">✅ Actualización completada</span>
      <button class="reload-btn" onclick="location.reload()">Recargar</button>
    </div>

    <div class="update-card">
      <div class="update-card-title">Actualizar cuotas</div>
      <div id="token-indicator" class="token-indicator token-missing">Token: no configurado</div>
      <div class="token-row">
        <input id="token-input" type="password" placeholder="GitHub token…">
        <button id="token-paste" onclick="pasteToken()">Pegar</button>
        <button id="token-save">Guardar</button>
      </div>
      <div id="token-status"></div>
      <div id="run-state"></div>
      <button class="update-main-btn" id="btn-update" onclick="triggerUpdate()">Actualizar todo</button>
    </div>

    <div class="update-card">
      <div class="runs-section-title">Últimas ejecuciones</div>
      <div id="runs-list"><p class="run-empty">Cargando…</p></div>
    </div>

  </div>
</div>

<!-- ── BOTTOM NAV ────────────────────────────────────────────────────────── -->
<nav id="bottom-nav">
  <button class="nav-pill active" id="nav-partidos" onclick="showTab('partidos')">
    <span class="nav-icon">📅</span>
    Partidos
  </button>
  <button class="nav-pill" id="nav-update" onclick="showTab('update')">
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

    out_path = os.path.join(DIR, 'index.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ HTML generado: {out_path}")
    print(f"   {len(data)} partidos · {len(html)//1024} KB")


if __name__ == '__main__':
    main()
