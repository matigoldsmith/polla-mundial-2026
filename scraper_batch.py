#!/usr/bin/env python3
"""
Scraper por batch — ejecutar con: python3 scraper_batch.py BATCH_NUM
BATCH_NUM: 0, 1, 2 o 3
Cada batch corre ~18 partidos. Después mergear con: python3 scraper_batch.py merge
"""
import json, re, time, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import cloudscraper

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE = "https://www.oddschecker.com"

MATCHES = [
    {"slug":"mexico-v-south-africa",               "fecha":"Jun 11","j":1,"grp":"A","local":"México","visita":"Sudáfrica"},
    {"slug":"south-korea-v-czech-republic",        "fecha":"Jun 11","j":1,"grp":"A","local":"Corea del Sur","visita":"Rep. Checa"},
    {"slug":"canada-v-bosnia-and-herzegovina",     "fecha":"Jun 12","j":1,"grp":"B","local":"Canadá","visita":"Bosnia"},
    {"slug":"usa-v-paraguay",                      "fecha":"Jun 12","j":1,"grp":"D","local":"USA","visita":"Paraguay"},
    {"slug":"qatar-v-switzerland",                 "fecha":"Jun 13","j":1,"grp":"B","local":"Qatar","visita":"Suiza"},
    {"slug":"brazil-v-morocco",                    "fecha":"Jun 13","j":1,"grp":"C","local":"Brasil","visita":"Marruecos"},
    {"slug":"haiti-v-scotland",                    "fecha":"Jun 14","j":1,"grp":"C","local":"Haití","visita":"Escocia"},
    {"slug":"australia-v-turkey",                  "fecha":"Jun 14","j":1,"grp":"D","local":"Australia","visita":"Turquía"},
    {"slug":"germany-v-curacao",                   "fecha":"Jun 14","j":1,"grp":"E","local":"Alemania","visita":"Curazao"},
    {"slug":"ivory-coast-v-ecuador",               "fecha":"Jun 14","j":1,"grp":"E","local":"C. de Marfil","visita":"Ecuador"},
    {"slug":"netherlands-v-japan",                 "fecha":"Jun 14","j":1,"grp":"F","local":"Países Bajos","visita":"Japón"},
    {"slug":"sweden-v-tunisia",                    "fecha":"Jun 15","j":1,"grp":"F","local":"Suecia","visita":"Túnez"},
    {"slug":"belgium-v-egypt",                     "fecha":"Jun 15","j":1,"grp":"G","local":"Bélgica","visita":"Egipto"},
    {"slug":"spain-v-cape-verde",                  "fecha":"Jun 15","j":1,"grp":"H","local":"España","visita":"Cabo Verde"},
    {"slug":"saudi-arabia-v-uruguay",              "fecha":"Jun 15","j":1,"grp":"H","local":"Arabia Saudita","visita":"Uruguay"},
    {"slug":"iran-v-new-zealand",                  "fecha":"Jun 16","j":1,"grp":"G","local":"Irán","visita":"Nueva Zelanda"},
    {"slug":"france-v-senegal",                    "fecha":"Jun 16","j":1,"grp":"I","local":"Francia","visita":"Senegal"},
    {"slug":"iraq-v-norway",                       "fecha":"Jun 16","j":1,"grp":"I","local":"Irak","visita":"Noruega"},
    {"slug":"argentina-v-algeria",                 "fecha":"Jun 17","j":1,"grp":"J","local":"Argentina","visita":"Argelia"},
    {"slug":"austria-v-jordan",                    "fecha":"Jun 17","j":1,"grp":"J","local":"Austria","visita":"Jordania"},
    {"slug":"portugal-v-dr-congo",                 "fecha":"Jun 17","j":1,"grp":"K","local":"Portugal","visita":"RD Congo"},
    {"slug":"england-v-croatia",                   "fecha":"Jun 17","j":1,"grp":"L","local":"Inglaterra","visita":"Croacia"},
    {"slug":"ghana-v-panama",                      "fecha":"Jun 17","j":1,"grp":"L","local":"Ghana","visita":"Panamá"},
    {"slug":"uzbekistan-v-colombia",               "fecha":"Jun 18","j":1,"grp":"K","local":"Uzbekistán","visita":"Colombia"},
    {"slug":"mexico-v-south-korea",                "fecha":"Jun 18","j":2,"grp":"A","local":"México","visita":"Corea del Sur"},
    {"slug":"czech-republic-v-south-africa",       "fecha":"Jun 18","j":2,"grp":"A","local":"Rep. Checa","visita":"Sudáfrica"},
    {"slug":"canada-v-qatar",                      "fecha":"Jun 18","j":2,"grp":"B","local":"Canadá","visita":"Qatar"},
    {"slug":"switzerland-v-bosnia-and-herzegovina","fecha":"Jun 18","j":2,"grp":"B","local":"Suiza","visita":"Bosnia"},
    {"slug":"brazil-v-haiti",                      "fecha":"Jun 19","j":2,"grp":"C","local":"Brasil","visita":"Haití"},
    {"slug":"scotland-v-morocco",                  "fecha":"Jun 19","j":2,"grp":"C","local":"Escocia","visita":"Marruecos"},
    {"slug":"usa-v-australia",                     "fecha":"Jun 19","j":2,"grp":"D","local":"USA","visita":"Australia"},
    {"slug":"turkey-v-paraguay",                   "fecha":"Jun 19","j":2,"grp":"D","local":"Turquía","visita":"Paraguay"},
    {"slug":"germany-v-ivory-coast",               "fecha":"Jun 20","j":2,"grp":"E","local":"Alemania","visita":"C. de Marfil"},
    {"slug":"ecuador-v-curacao",                   "fecha":"Jun 20","j":2,"grp":"E","local":"Ecuador","visita":"Curazao"},
    {"slug":"netherlands-v-sweden",                "fecha":"Jun 20","j":2,"grp":"F","local":"Países Bajos","visita":"Suecia"},
    {"slug":"tunisia-v-japan",                     "fecha":"Jun 21","j":2,"grp":"F","local":"Túnez","visita":"Japón"},
    {"slug":"belgium-v-iran",                      "fecha":"Jun 21","j":2,"grp":"G","local":"Bélgica","visita":"Irán"},
    {"slug":"new-zealand-v-egypt",                 "fecha":"Jun 21","j":2,"grp":"G","local":"Nueva Zelanda","visita":"Egipto"},
    {"slug":"spain-v-saudi-arabia",                "fecha":"Jun 21","j":2,"grp":"H","local":"España","visita":"Arabia Saudita"},
    {"slug":"uruguay-v-cape-verde",                "fecha":"Jun 21","j":2,"grp":"H","local":"Uruguay","visita":"Cabo Verde"},
    {"slug":"france-v-iraq",                       "fecha":"Jun 22","j":2,"grp":"I","local":"Francia","visita":"Irak"},
    {"slug":"norway-v-senegal",                    "fecha":"Jun 22","j":2,"grp":"I","local":"Noruega","visita":"Senegal"},
    {"slug":"argentina-v-austria",                 "fecha":"Jun 22","j":2,"grp":"J","local":"Argentina","visita":"Austria"},
    {"slug":"jordan-v-algeria",                    "fecha":"Jun 22","j":2,"grp":"J","local":"Jordania","visita":"Argelia"},
    {"slug":"portugal-v-uzbekistan",               "fecha":"Jun 23","j":2,"grp":"K","local":"Portugal","visita":"Uzbekistán"},
    {"slug":"colombia-v-dr-congo",                 "fecha":"Jun 23","j":2,"grp":"K","local":"Colombia","visita":"RD Congo"},
    {"slug":"england-v-ghana",                     "fecha":"Jun 23","j":2,"grp":"L","local":"Inglaterra","visita":"Ghana"},
    {"slug":"panama-v-croatia",                    "fecha":"Jun 23","j":2,"grp":"L","local":"Panamá","visita":"Croacia"},
    {"slug":"bosnia-and-herzegovina-v-qatar",      "fecha":"Jun 24","j":3,"grp":"B","local":"Bosnia","visita":"Qatar"},
    {"slug":"switzerland-v-canada",                "fecha":"Jun 24","j":3,"grp":"B","local":"Suiza","visita":"Canadá"},
    {"slug":"morocco-v-haiti",                     "fecha":"Jun 24","j":3,"grp":"C","local":"Marruecos","visita":"Haití"},
    {"slug":"scotland-v-brazil",                   "fecha":"Jun 24","j":3,"grp":"C","local":"Escocia","visita":"Brasil"},
    {"slug":"czech-republic-v-mexico",             "fecha":"Jun 25","j":3,"grp":"A","local":"Rep. Checa","visita":"México"},
    {"slug":"south-africa-v-south-korea",          "fecha":"Jun 25","j":3,"grp":"A","local":"Sudáfrica","visita":"Corea del Sur"},
    {"slug":"curacao-v-ivory-coast",               "fecha":"Jun 25","j":3,"grp":"E","local":"Curazao","visita":"C. de Marfil"},
    {"slug":"ecuador-v-germany",                   "fecha":"Jun 25","j":3,"grp":"E","local":"Ecuador","visita":"Alemania"},
    {"slug":"japan-v-sweden",                      "fecha":"Jun 25","j":3,"grp":"F","local":"Japón","visita":"Suecia"},
    {"slug":"tunisia-v-netherlands",               "fecha":"Jun 25","j":3,"grp":"F","local":"Túnez","visita":"Países Bajos"},
    {"slug":"paraguay-v-australia",                "fecha":"Jun 26","j":3,"grp":"D","local":"Paraguay","visita":"Australia"},
    {"slug":"turkey-v-usa",                        "fecha":"Jun 26","j":3,"grp":"D","local":"Turquía","visita":"USA"},
    {"slug":"norway-v-france",                     "fecha":"Jun 26","j":3,"grp":"I","local":"Noruega","visita":"Francia"},
    {"slug":"senegal-v-iraq",                      "fecha":"Jun 26","j":3,"grp":"I","local":"Senegal","visita":"Irak"},
    {"slug":"egypt-v-iran",                        "fecha":"Jun 27","j":3,"grp":"G","local":"Egipto","visita":"Irán"},
    {"slug":"new-zealand-v-belgium",               "fecha":"Jun 27","j":3,"grp":"G","local":"Nueva Zelanda","visita":"Bélgica"},
    {"slug":"cape-verde-v-saudi-arabia",           "fecha":"Jun 27","j":3,"grp":"H","local":"Cabo Verde","visita":"Arabia Saudita"},
    {"slug":"uruguay-v-spain",                     "fecha":"Jun 27","j":3,"grp":"H","local":"Uruguay","visita":"España"},
    {"slug":"colombia-v-portugal",                 "fecha":"Jun 27","j":3,"grp":"K","local":"Colombia","visita":"Portugal"},
    {"slug":"dr-congo-v-uzbekistan",               "fecha":"Jun 27","j":3,"grp":"K","local":"RD Congo","visita":"Uzbekistán"},
    {"slug":"croatia-v-ghana",                     "fecha":"Jun 27","j":3,"grp":"L","local":"Croacia","visita":"Ghana"},
    {"slug":"panama-v-england",                    "fecha":"Jun 27","j":3,"grp":"L","local":"Panamá","visita":"Inglaterra"},
    {"slug":"algeria-v-austria",                   "fecha":"Jun 28","j":3,"grp":"J","local":"Argelia","visita":"Austria"},
    {"slug":"jordan-v-argentina",                  "fecha":"Jun 28","j":3,"grp":"J","local":"Jordania","visita":"Argentina"},
]

BATCH_SIZE = 18

def make_scraper():
    return cloudscraper.create_scraper(browser={'browser':'chrome','platform':'darwin','mobile':False})

def get_market_ids(sc, slug):
    url = f"{BASE}/football/world-cup/{slug}/winner"
    r = sc.get(url, timeout=20)
    soup = BeautifulSoup(r.text, 'html.parser')
    markets = {}
    for sec in soup.find_all('section', id=re.compile(r'^market_')):
        mid = sec['id'].replace('market_','')
        h2 = sec.find('h2')
        name = h2.get_text(strip=True) if h2 else ''
        markets[name] = mid
    return markets

def get_odds(sc, win_id, cs_id):
    ids = ','.join(filter(None, [win_id, cs_id]))
    if not ids:
        return []
    r = sc.get(f"{BASE}/api/markets/v2/all-odds?market-ids={ids}&repub=OC", timeout=15)
    return r.json()

def best_per_bk(market_data, field='line'):
    bets = {b['betId']: b for b in market_data.get('bets', [])}
    by_bk = {}
    for o in market_data.get('odds', []):
        bk = o.get('bookmakerCode','?')
        bid = o['betId']
        dec = o.get('oddsDecimal') or 99
        frac = o.get('oddsFractional','')
        val = bets.get(bid, {}).get(field) or bets.get(bid, {}).get('betName','?')
        if bk not in by_bk or dec < by_bk[bk]['dec']:
            by_bk[bk] = {'val': val, 'dec': dec, 'frac': frac}
    return by_bk

def consensus(by_bk):
    if not by_bk:
        return None, 'sin datos', {}
    votes = {}
    for bk, d in by_bk.items():
        v = d['val']
        votes[v] = votes.get(v, 0) + 1
    winner = max(votes, key=votes.get)
    pct = votes[winner] / sum(votes.values())
    nivel = '🟢' if pct >= 0.75 else ('🟡' if pct >= 0.55 else '🔴')
    return winner, nivel, votes

def process_match(match):
    sc = make_scraper()
    slug = match['slug']
    try:
        markets = get_market_ids(sc, slug)
        win_id = markets.get('Win Market') or markets.get('Match Betting')
        cs_id  = markets.get('Correct Score')

        if not win_id and not cs_id:
            return {**match, 'error': 'no markets found', 'win': None, 'cs': None}

        odds_data = get_odds(sc, win_id, cs_id)

        win_data, cs_data = None, None
        for mkt in odds_data:
            mid = str(mkt.get('marketId',''))
            if mid == win_id:
                win_data = mkt
            elif mid == cs_id:
                cs_data = mkt

        win_by_bk = best_per_bk(win_data, field='betName') if win_data else {}
        cs_by_bk  = best_per_bk(cs_data,  field='line')    if cs_data  else {}

        win_pred, win_nivel, win_votes = consensus(win_by_bk)
        cs_pred,  cs_nivel,  cs_votes  = consensus(cs_by_bk)

        print(f"  ✅ [{match['grp']} J{match['j']}] {match['local']} vs {match['visita']}: "
              f"1X2={win_pred} {win_nivel} | CS={cs_pred} {cs_nivel}")

        return {
            **match,
            'error': None,
            'win_pred': win_pred, 'win_nivel': win_nivel, 'win_votes': win_votes,
            'cs_pred':  cs_pred,  'cs_nivel':  cs_nivel,  'cs_votes':  cs_votes,
            'win_by_bk': win_by_bk,
            'cs_by_bk':  cs_by_bk,
        }
    except Exception as e:
        print(f"  ❌ {slug}: {e}")
        return {**match, 'error': str(e), 'win': None, 'cs': None}

def run_batch(batch_num):
    start = batch_num * BATCH_SIZE
    end   = min(start + BATCH_SIZE, len(MATCHES))
    batch = MATCHES[start:end]
    print(f"Batch {batch_num}: partidos {start+1}–{end} ({len(batch)} partidos)\n")
    t0 = time.time()
    results = [None] * len(batch)
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {ex.submit(process_match, m): i for i, m in enumerate(batch)}
        for fut in as_completed(futures):
            idx = futures[fut]
            results[idx] = fut.result()
    elapsed = time.time() - t0
    print(f"\nBatch {batch_num} listo en {elapsed:.1f}s")
    out = os.path.join(OUT_DIR, f'odds_batch_{batch_num}.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Guardado: {out}")
    return results

def merge_batches():
    total = len(MATCHES)
    num_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
    all_results = []
    for b in range(num_batches):
        path = os.path.join(OUT_DIR, f'odds_batch_{b}.json')
        if not os.path.exists(path):
            print(f"⚠️  Falta batch {b} ({path})")
            continue
        with open(path) as f:
            all_results.extend(json.load(f))
    out_json = os.path.join(OUT_DIR, 'odds_mundial_2026.json')
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"✅ Merge completo: {len(all_results)} partidos → {out_json}")
    # Resumen txt
    lines = [
        "MUNDIAL 2026 — CUOTAS ODDSCHECKER",
        f"Generado: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "="*90,
        f"{'#':<3} {'Fecha':<8} {'Grp':<4} {'J':<2} {'Partido':<35} {'1X2':<18} {'CS':<10} {'🟢1X2':<8} {'🟢CS'}",
        "-"*90,
    ]
    for i, r in enumerate(all_results, 1):
        if r:
            partido = f"{r['local']} vs {r['visita']}"
            lines.append(
                f"{i:<3} {r['fecha']:<8} {r['grp']:<4} {r['j']:<2} "
                f"{partido:<35} {str(r.get('win_pred','?')):<18} {str(r.get('cs_pred','?')):<10} "
                f"{r.get('win_nivel','?'):<8} {r.get('cs_nivel','?')}"
            )
    out_txt = os.path.join(OUT_DIR, 'odds_mundial_2026.txt')
    with open(out_txt, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"TXT: {out_txt}")
    print('\n'.join(lines[:20]))

if __name__ == '__main__':
    arg = sys.argv[1] if len(sys.argv) > 1 else '0'
    if arg == 'merge':
        merge_batches()
    else:
        run_batch(int(arg))
