#!/usr/bin/env python3
"""
rebuild_html.py — Regenera el HTML desde polla_data_final.json existente.
Incluye sección visual "cómo se eligió el marcador" en cada panel de detalle.
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

    # The JS is written as a plain Python string — no escaping needed
    js = r"""
const DATA=__DATA__;
const FLAGS=__FLAGS__;
const BK_NAMES={BF:'Betfair',B3:'bet365',UN:'Unibet',OE:'10bet',MA:'Matchbook',VC:'BetVictor',WA:'Betway'};
const BK_ORDER=['BF','B3','UN','OE','MA','VC','WA'];
const BK_URLS={BF:'https://www.betfair.com',B3:'https://www.bet365.com',UN:'https://www.unibet.com',OE:'https://www.10bet.com',MA:'https://www.matchbook.com',VC:'https://www.betvictor.com',WA:'https://www.betway.com'};
const BASE='https://www.oddschecker.com/football/world-cup';
const DOW=__DOW__;

function getLEV(m){const w=m.win_pred;if(!w||w==='Empate')return'E';if(w===m.local)return'L';return'V';}

function buildWinTable(m){
  const wt=m.win_table||{};const bks=BK_ORDER.filter(bk=>bk in wt);
  if(!bks.length)return'<p class="no-data">Sin datos</p>';
  const outcomes=[m.local,'Empate',m.visita];
  // Best price per outcome (column min) — for "best odds" highlight
  const best={};outcomes.forEach(o=>{let mn=Infinity;bks.forEach(bk=>{const v=(wt[bk]||{})[o];if(v&&v<mn)mn=v;});best[o]=mn;});
  // Each bookmaker's favorite outcome (row min = most likely according to them)
  const bkFave={};bks.forEach(bk=>{let mn=Infinity,mo=null;outcomes.forEach(o=>{const v=(wt[bk]||{})[o];if(v&&v<mn){mn=v;mo=o;}});bkFave[bk]=mo;});
  let h=`<table class="odds-table"><thead><tr><th>Casa</th><th>${FLAGS[m.local]||''} ${m.local}</th><th>Empate</th><th>${FLAGS[m.visita]||''} ${m.visita}</th></tr></thead><tbody>`;
  bks.forEach(bk=>{const row=wt[bk]||{};h+=`<tr><td class="bk-name"><a href="${BK_URLS[bk]}" target="_blank" style="color:#3b71c8;text-decoration:none">${BK_NAMES[bk]}</a></td>`;outcomes.forEach(o=>{const v=row[o];const isFave=bkFave[bk]===o;h+=`<td${isFave?' style="background:#eaf3de;font-weight:700;color:#2a6a2a"':''}>${v?v.toFixed(2):'—'}</td>`;});h+='</tr>';});
  return h+'</tbody></table>';
}

function buildCSTable(m){
  const cs=m.cs_top||{};const scores=Object.keys(cs);
  if(!scores.length)return'<p class="no-data">Sin datos</p>';
  const bks=BK_ORDER.filter(bk=>scores.some(s=>bk in(cs[s]||{})));
  // Per-bookmaker: find their favorite score (lowest odds = most likely)
  const bkMin={};
  bks.forEach(bk=>{let mn=Infinity,ms=null;scores.forEach(s=>{const v=(cs[s]||{})[bk];if(v&&v>=2.0&&v<mn){mn=v;ms=s;}});bkMin[bk]=ms;});
  let h=`<table class="odds-table"><thead><tr><th>Score</th>${bks.map(bk=>`<th>${BK_NAMES[bk]}</th>`).join('')}</tr></thead><tbody>`;
  scores.forEach(s=>{const isBest=s===m.cs_refined;h+=`<tr><td class="score-col"${isBest?' style="color:#c08010"':''}>${s}${isBest?' ★':''}</td>`;bks.forEach(bk=>{const raw=(cs[s]||{})[bk];const v=raw&&raw>=2.0?raw:null;const isFave=bkMin[bk]===s;h+=`<td${isFave?' style="background:#eaf3de;font-weight:700;color:#2a6a2a"':''}>${v?v.toFixed(2):'—'}</td>`;});h+='</tr>';});
  return h+'</tbody></table>';
}

/* --- Recommendation logic --- */
function getBkFave(m){
  const cs=m.cs_top||{};const scores=Object.keys(cs);
  const bkFave={};
  BK_ORDER.forEach(bk=>{
    let best=null,bestO=Infinity;
    scores.forEach(s=>{const v=(cs[s]||{})[bk];if(v&&v>=2.0&&v<bestO){bestO=v;best=s;}});
    if(best)bkFave[bk]={score:best,odds:bestO};
  });
  return bkFave;
}

function buildRecommendation(m){
  const bkFave=getBkFave(m);
  const bks=Object.keys(bkFave);
  if(!bks.length)return'';

  const votes={};
  bks.forEach(bk=>{const s=bkFave[bk].score;votes[s]=(votes[s]||0)+1;});
  const total=bks.length;
  const sorted=Object.entries(votes).sort((a,b)=>b[1]-a[1]);
  const winner=sorted[0][0],wCount=sorted[0][1];
  const pct=wCount/total;
  const nivelTxt=pct>=0.75?'Mayoría clara':pct>=0.55?'Mayoría débil':'Sin mayoría clara';
  const nc=pct>=0.75?'#3b6d11':pct>=0.55?'#854f0b':'#993c1d';
  const nb=pct>=0.75?'#eaf3de':pct>=0.55?'#faeeda':'#faece7';

  const bars=sorted.map(([s,c])=>{
    const iw=s===winner,bp=Math.round(c/total*100);
    return`<div style="display:flex;align-items:center;gap:8px;margin:3px 0">
      <span style="font-variant-numeric:tabular-nums;font-weight:${iw?700:500};color:${iw?'#2a6a2a':'#666'};min-width:36px;font-size:12px">${s}</span>
      <div style="flex:1;background:#f0f0ec;border-radius:3px;height:12px">
        <div style="width:${bp}%;background:${iw?'#5a9a3a':'#ccc'};height:100%;border-radius:3px"></div>
      </div>
      <span style="font-size:11px;color:${iw?'#2a6a2a':'#999'};min-width:62px">${c}/${total} (${bp}%)</span>
    </div>`;
  }).join('');

  const pills=BK_ORDER.filter(bk=>bk in bkFave).map(bk=>{
    const s=bkFave[bk].score,iw=s===winner;
    return`<span style="font-size:10px;display:inline-block;background:${iw?'#eaf3de':'#f0f0ec'};color:${iw?'#3b6d11':'#888'};border-radius:3px;padding:2px 6px;margin:2px;white-space:nowrap">${BK_NAMES[bk]}: ${s}</span>`;
  }).join('');

  const ovrHTML=m.cs_overridden
    ?`<div style="margin-top:8px;padding:6px 10px;background:#fff8e7;border-left:3px solid #c08010;border-radius:0 4px 4px 0;font-size:11px;line-height:1.5">⚠️ Las casas preferían <strong>${winner}</strong> como score, pero también dicen que <strong>${m.win_pred}</strong> gana — no puede ser empate. Se usó <strong style="color:#c08010">${m.cs_refined}</strong></div>`
    :'';

  return`<div class="det-section" style="border-bottom:.5px solid #f0f0ec;padding-bottom:12px;margin-bottom:12px">
    <div class="det-title">Cómo se eligió el marcador</div>
    <div style="margin-bottom:8px">${bars}</div>
    <div style="margin-bottom:6px;line-height:1.8">${pills}</div>
    <div style="font-size:11px;padding:3px 8px;background:${nb};color:${nc};border-radius:4px;display:inline-block">${m.cs_nivel} ${nivelTxt} · ${Math.round(pct*100)}% de acuerdo</div>
    ${ovrHTML}
  </div>`;
}

function buildDetail(m){
  const ocW=`${BASE}/${m.slug}/winner`,ocC=`${BASE}/${m.slug}/correct-score`;
  return`<div class="detail-links">
    <a class="det-link" href="${ocW}" target="_blank">OddsChecker 1X2 ↗</a>
    <a class="det-link" href="${ocC}" target="_blank">OddsChecker Marcador Exacto ↗</a>
    ${BK_ORDER.filter(bk=>bk in(m.win_table||{})).map(bk=>`<a class="det-link" href="${BK_URLS[bk]}" target="_blank">${BK_NAMES[bk]} ↗</a>`).join('')}
  </div>
  ${buildRecommendation(m)}
  <div class="det-section"><div class="det-title">Cuotas 1X2</div>${buildWinTable(m)}</div>
  <div class="det-section"><div class="det-title">Top marcadores · Recomendado: <strong style="color:#2a6a2a">${m.cs_refined}</strong>${m.cs_overridden?' <span style="color:#c08010;font-size:10px">(corregido por 1X2)</span>':''}</div>${buildCSTable(m)}</div>`;
}

const byDate={};DATA.forEach(m=>{if(!byDate[m.fecha])byDate[m.fecha]=[];byDate[m.fecha].push(m);});
const root=document.getElementById('root');
Object.keys(byDate).forEach(fecha=>{
  const block=document.createElement('div');
  block.innerHTML=`<div class="day-title">${DOW[fecha]||fecha}</div>`;
  byDate[fecha].forEach(m=>{
    const ovr=m.cs_overridden,lev=getLEV(m),lf=FLAGS[m.local]||'🏳',vf=FLAGS[m.visita]||'🏳';
    const levCls=lev==='L'?'L':lev==='V'?'V':'E',levTxt=lev==='E'?'Empate':m.win_pred;
    const id='m_'+m.slug.replace(/-/g,'_');
    const wrap=document.createElement('div');wrap.className='match-wrap';
    wrap.innerHTML=`<div class="match${ovr?' ovr':''}" id="${id}" onclick="toggle('${id}')">
      <div class="meta"><div class="hora">${m.hora}</div><div class="ciudad">${m.ciudad}</div><div><span class="grp-badge">G${m.grp} · J${m.j}</span></div></div>
      <div class="teams">
        <div class="team-row"><span class="flag">${lf}</span><span class="tname${lev==='L'?' bold':''}">${m.local}</span></div>
        <div class="team-row"><span class="flag">${vf}</span><span class="tname${lev==='V'?' bold':''}">${m.visita}</span></div>
      </div>
      <div class="right">
        <div style="display:flex;align-items:center;gap:6px"><span class="result ${levCls}">${levTxt}</span><span class="score${ovr?' ovr':''}">${m.cs_refined||'—'}</span></div>
        <div class="bottom-row"><span class="cons">${m.cs_nivel||''}</span><span class="chevron" id="chv_${id}">▾</span></div>
      </div>
    </div>
    <div class="detail" id="det_${id}">${buildDetail(m)}</div>`;
    block.appendChild(wrap);
  });
  root.appendChild(block);
});
function toggle(id){const d=document.getElementById('det_'+id),c=document.getElementById('chv_'+id),card=document.getElementById(id),o=d.classList.contains('open');d.classList.toggle('open',!o);card.classList.toggle('open',!o);c.classList.toggle('open',!o);}
"""

    js = js.replace('__DATA__', data_js)
    js = js.replace('__FLAGS__', flags_js)
    js = js.replace('__DOW__', dow_js)

    html = f"""<!DOCTYPE html>
<html lang="es"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Polla Mundial 2026</title>
<style>
:root{{color-scheme:light}}*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f5f5f2;color:#1a1a1a;font-size:13px}}
.container{{max-width:800px;margin:0 auto;padding:20px 16px}}
h1{{font-size:16px;font-weight:600;margin-bottom:2px}}.sub{{font-size:11px;color:#999;margin-bottom:4px}}
.day-title{{font-size:11px;font-weight:700;letter-spacing:.4px;color:#888;text-transform:uppercase;margin:20px 0 6px;padding-bottom:4px;border-bottom:1px solid #e0e0da}}
.match-wrap{{margin-bottom:5px}}
.match{{display:grid;grid-template-columns:70px 1fr auto;align-items:center;background:#fff;border:.5px solid #e8e8e4;border-radius:8px;padding:8px 12px;gap:10px;cursor:pointer;transition:background .1s}}
.match:hover{{background:#fafaf8}}.match.ovr{{border-left:3px solid #e0a020}}.match.open{{border-radius:8px 8px 0 0;border-bottom:none}}
.meta{{font-size:10px;color:#aaa;line-height:1.6}}.meta .hora{{font-size:12px;font-weight:600;color:#444}}.meta .ciudad{{color:#aaa}}
.meta .grp-badge{{display:inline-block;font-size:9px;font-weight:700;background:#f0f0ec;color:#888;border-radius:3px;padding:1px 4px;margin-top:1px}}
.teams{{min-width:0}}.team-row{{display:flex;align-items:center;gap:5px;padding:1px 0}}
.flag{{font-size:14px;line-height:1;flex-shrink:0}}.tname{{font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}.tname.bold{{font-weight:600}}
.right{{display:flex;flex-direction:column;align-items:flex-end;gap:4px;flex-shrink:0}}
.result{{font-size:10px;padding:2px 6px;border-radius:4px;font-weight:500;white-space:nowrap}}
.L{{background:#eaf3de;color:#3b6d11}}.E{{background:#faeeda;color:#854f0b}}.V{{background:#faece7;color:#993c1d}}
.score{{font-size:18px;font-weight:700;letter-spacing:2px;font-variant-numeric:tabular-nums}}.score.ovr{{color:#c08010}}
.bottom-row{{display:flex;align-items:center;gap:5px}}.cons{{font-size:12px}}
.chevron{{font-size:10px;color:#ccc;transition:transform .2s}}.chevron.open{{transform:rotate(180deg)}}
.detail{{display:none;background:#fff;border:.5px solid #e8e8e4;border-top:none;border-radius:0 0 8px 8px;padding:12px 14px 14px}}
.detail.open{{display:block}}
.detail-links{{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap}}
.det-link{{font-size:11px;color:#3b71c8;text-decoration:none;background:#f0f4ff;border-radius:4px;padding:3px 8px}}
.det-link:hover{{background:#dde8ff}}
.det-section{{margin-bottom:12px}}.det-title{{font-size:10px;font-weight:700;color:#888;text-transform:uppercase;letter-spacing:.4px;margin-bottom:6px}}
.odds-table{{width:100%;border-collapse:collapse;font-size:11px}}
.odds-table th{{text-align:left;color:#888;font-weight:500;padding:3px 6px;border-bottom:.5px solid #eee;white-space:nowrap}}
.odds-table td{{padding:4px 6px;border-bottom:.5px solid #f5f5f2;white-space:nowrap}}
.odds-table tr:last-child td{{border-bottom:none}}.odds-table .bk-name{{font-weight:500;color:#444}}
.odds-table .best{{font-weight:700;color:#2a6a2a}}.odds-table .score-col{{font-weight:600;color:#1a1a1a;font-variant-numeric:tabular-nums}}
.no-data{{font-size:11px;color:#aaa;font-style:italic;padding:6px 0}}
.updated{{font-size:10px;color:#bbb;margin-top:2px;margin-bottom:20px}}
</style></head><body>
<div class="container">
<h1>Polla Mundial 2026</h1>
<p class="sub">Betfair · bet365 · Unibet · 10bet · Matchbook · BetVictor · Betway · Hora Chile · Score: Local–Visita</p>
<p class="updated">Actualizado: {now}</p>
<div id="root"></div>
</div>
<script>
{js}
</script></body></html>"""
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
