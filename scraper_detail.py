#!/usr/bin/env python3
"""
Scraper de cuotas COMPLETAS por casa de apuesta (7 casas top)
Guarda tabla 1X2 + top 8 marcadores exactos por partido
"""
import json, re, time, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import cloudscraper

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE = "https://www.oddschecker.com"
BATCH_SIZE = 18

# Solo las 7 casas más confiables disponibles en OddsChecker
TRUSTED = {'BF', 'B3', 'UN', 'OE', 'MA', 'VC', 'WA'}
BK_NAMES = {
    'BF': 'Betfair', 'B3': 'bet365', 'UN': 'Unibet',
    'OE': '10bet', 'MA': 'Matchbook', 'VC': 'BetVictor', 'WA': 'Betway'
}

MATCHES = [
    {"slug":"mexico-v-south-africa",               "fecha":"Jun 11","hora":"15:00","ciudad":"Ciudad de México","j":1,"grp":"A","local":"México","visita":"Sudáfrica"},
    {"slug":"south-korea-v-czech-republic",        "fecha":"Jun 11","hora":"22:00","ciudad":"Guadalajara","j":1,"grp":"A","local":"Corea del Sur","visita":"Rep. Checa"},
    {"slug":"canada-v-bosnia-and-herzegovina",     "fecha":"Jun 12","hora":"15:00","ciudad":"Toronto","j":1,"grp":"B","local":"Canadá","visita":"Bosnia"},
    {"slug":"usa-v-paraguay",                      "fecha":"Jun 12","hora":"21:00","ciudad":"Los Ángeles","j":1,"grp":"D","local":"USA","visita":"Paraguay"},
    {"slug":"australia-v-turkey",                  "fecha":"Jun 13","hora":"00:00","ciudad":"Vancouver","j":1,"grp":"D","local":"Australia","visita":"Turquía"},
    {"slug":"qatar-v-switzerland",                 "fecha":"Jun 13","hora":"15:00","ciudad":"San Francisco","j":1,"grp":"B","local":"Qatar","visita":"Suiza"},
    {"slug":"brazil-v-morocco",                    "fecha":"Jun 13","hora":"18:00","ciudad":"Nueva York","j":1,"grp":"C","local":"Brasil","visita":"Marruecos"},
    {"slug":"haiti-v-scotland",                    "fecha":"Jun 13","hora":"21:00","ciudad":"Boston","j":1,"grp":"C","local":"Haití","visita":"Escocia"},
    {"slug":"germany-v-curacao",                   "fecha":"Jun 14","hora":"13:00","ciudad":"Houston","j":1,"grp":"E","local":"Alemania","visita":"Curazao"},
    {"slug":"netherlands-v-japan",                 "fecha":"Jun 14","hora":"16:00","ciudad":"Dallas","j":1,"grp":"F","local":"Países Bajos","visita":"Japón"},
    {"slug":"ivory-coast-v-ecuador",               "fecha":"Jun 14","hora":"19:00","ciudad":"Philadelphia","j":1,"grp":"E","local":"C. de Marfil","visita":"Ecuador"},
    {"slug":"sweden-v-tunisia",                    "fecha":"Jun 14","hora":"22:00","ciudad":"Monterrey","j":1,"grp":"F","local":"Suecia","visita":"Túnez"},
    {"slug":"spain-v-cape-verde",                  "fecha":"Jun 15","hora":"12:00","ciudad":"Atlanta","j":1,"grp":"H","local":"España","visita":"Cabo Verde"},
    {"slug":"belgium-v-egypt",                     "fecha":"Jun 15","hora":"15:00","ciudad":"Seattle","j":1,"grp":"G","local":"Bélgica","visita":"Egipto"},
    {"slug":"saudi-arabia-v-uruguay",              "fecha":"Jun 15","hora":"18:00","ciudad":"Miami","j":1,"grp":"H","local":"Arabia Saudita","visita":"Uruguay"},
    {"slug":"iran-v-new-zealand",                  "fecha":"Jun 15","hora":"21:00","ciudad":"Los Ángeles","j":1,"grp":"G","local":"Irán","visita":"Nueva Zelanda"},
    {"slug":"austria-v-jordan",                    "fecha":"Jun 16","hora":"00:00","ciudad":"San Francisco","j":1,"grp":"J","local":"Austria","visita":"Jordania"},
    {"slug":"france-v-senegal",                    "fecha":"Jun 16","hora":"15:00","ciudad":"Nueva York","j":1,"grp":"I","local":"Francia","visita":"Senegal"},
    {"slug":"iraq-v-norway",                       "fecha":"Jun 16","hora":"18:00","ciudad":"Boston","j":1,"grp":"I","local":"Irak","visita":"Noruega"},
    {"slug":"argentina-v-algeria",                 "fecha":"Jun 16","hora":"21:00","ciudad":"Kansas City","j":1,"grp":"J","local":"Argentina","visita":"Argelia"},
    {"slug":"portugal-v-dr-congo",                 "fecha":"Jun 17","hora":"13:00","ciudad":"Houston","j":1,"grp":"K","local":"Portugal","visita":"RD Congo"},
    {"slug":"england-v-croatia",                   "fecha":"Jun 17","hora":"16:00","ciudad":"Dallas","j":1,"grp":"L","local":"Inglaterra","visita":"Croacia"},
    {"slug":"ghana-v-panama",                      "fecha":"Jun 17","hora":"19:00","ciudad":"Toronto","j":1,"grp":"L","local":"Ghana","visita":"Panamá"},
    {"slug":"uzbekistan-v-colombia",               "fecha":"Jun 17","hora":"22:00","ciudad":"Ciudad de México","j":1,"grp":"K","local":"Uzbekistán","visita":"Colombia"},
    {"slug":"mexico-v-south-korea",                "fecha":"Jun 18","hora":"21:00","ciudad":"Guadalajara","j":2,"grp":"A","local":"México","visita":"Corea del Sur"},
    {"slug":"czech-republic-v-south-africa",       "fecha":"Jun 18","hora":"12:00","ciudad":"Atlanta","j":2,"grp":"A","local":"Rep. Checa","visita":"Sudáfrica"},
    {"slug":"canada-v-qatar",                      "fecha":"Jun 18","hora":"18:00","ciudad":"Vancouver","j":2,"grp":"B","local":"Canadá","visita":"Qatar"},
    {"slug":"switzerland-v-bosnia-and-herzegovina","fecha":"Jun 18","hora":"15:00","ciudad":"Los Ángeles","j":2,"grp":"B","local":"Suiza","visita":"Bosnia"},
    {"slug":"brazil-v-haiti",                      "fecha":"Jun 19","hora":"21:00","ciudad":"Philadelphia","j":2,"grp":"C","local":"Brasil","visita":"Haití"},
    {"slug":"scotland-v-morocco",                  "fecha":"Jun 19","hora":"18:00","ciudad":"Boston","j":2,"grp":"C","local":"Escocia","visita":"Marruecos"},
    {"slug":"usa-v-australia",                     "fecha":"Jun 19","hora":"15:00","ciudad":"Seattle","j":2,"grp":"D","local":"USA","visita":"Australia"},
    {"slug":"turkey-v-paraguay",                   "fecha":"Jun 19","hora":"00:00","ciudad":"San Francisco","j":2,"grp":"D","local":"Turquía","visita":"Paraguay"},
    {"slug":"germany-v-ivory-coast",               "fecha":"Jun 20","hora":"16:00","ciudad":"Toronto","j":2,"grp":"E","local":"Alemania","visita":"C. de Marfil"},
    {"slug":"ecuador-v-curacao",                   "fecha":"Jun 20","hora":"20:00","ciudad":"Kansas City","j":2,"grp":"E","local":"Ecuador","visita":"Curazao"},
    {"slug":"netherlands-v-sweden",                "fecha":"Jun 20","hora":"13:00","ciudad":"Houston","j":2,"grp":"F","local":"Países Bajos","visita":"Suecia"},
    {"slug":"tunisia-v-japan",                     "fecha":"Jun 20","hora":"00:00","ciudad":"Monterrey","j":2,"grp":"F","local":"Túnez","visita":"Japón"},
    {"slug":"belgium-v-iran",                      "fecha":"Jun 21","hora":"15:00","ciudad":"Los Ángeles","j":2,"grp":"G","local":"Bélgica","visita":"Irán"},
    {"slug":"new-zealand-v-egypt",                 "fecha":"Jun 21","hora":"21:00","ciudad":"Vancouver","j":2,"grp":"G","local":"Nueva Zelanda","visita":"Egipto"},
    {"slug":"spain-v-saudi-arabia",                "fecha":"Jun 21","hora":"12:00","ciudad":"Atlanta","j":2,"grp":"H","local":"España","visita":"Arabia Saudita"},
    {"slug":"uruguay-v-cape-verde",                "fecha":"Jun 21","hora":"18:00","ciudad":"Miami","j":2,"grp":"H","local":"Uruguay","visita":"Cabo Verde"},
    {"slug":"france-v-iraq",                       "fecha":"Jun 22","hora":"17:00","ciudad":"Philadelphia","j":2,"grp":"I","local":"Francia","visita":"Irak"},
    {"slug":"norway-v-senegal",                    "fecha":"Jun 22","hora":"20:00","ciudad":"Nueva York","j":2,"grp":"I","local":"Noruega","visita":"Senegal"},
    {"slug":"argentina-v-austria",                 "fecha":"Jun 22","hora":"13:00","ciudad":"Dallas","j":2,"grp":"J","local":"Argentina","visita":"Austria"},
    {"slug":"jordan-v-algeria",                    "fecha":"Jun 22","hora":"23:00","ciudad":"San Francisco","j":2,"grp":"J","local":"Jordania","visita":"Argelia"},
    {"slug":"portugal-v-uzbekistan",               "fecha":"Jun 23","hora":"13:00","ciudad":"Houston","j":2,"grp":"K","local":"Portugal","visita":"Uzbekistán"},
    {"slug":"colombia-v-dr-congo",                 "fecha":"Jun 23","hora":"22:00","ciudad":"Guadalajara","j":2,"grp":"K","local":"Colombia","visita":"RD Congo"},
    {"slug":"england-v-ghana",                     "fecha":"Jun 23","hora":"16:00","ciudad":"Boston","j":2,"grp":"L","local":"Inglaterra","visita":"Ghana"},
    {"slug":"panama-v-croatia",                    "fecha":"Jun 23","hora":"19:00","ciudad":"Toronto","j":2,"grp":"L","local":"Panamá","visita":"Croacia"},
    {"slug":"bosnia-and-herzegovina-v-qatar",      "fecha":"Jun 24","hora":"15:00","ciudad":"Seattle","j":3,"grp":"B","local":"Bosnia","visita":"Qatar"},
    {"slug":"switzerland-v-canada",                "fecha":"Jun 24","hora":"15:00","ciudad":"Vancouver","j":3,"grp":"B","local":"Suiza","visita":"Canadá"},
    {"slug":"morocco-v-haiti",                     "fecha":"Jun 24","hora":"18:00","ciudad":"Atlanta","j":3,"grp":"C","local":"Marruecos","visita":"Haití"},
    {"slug":"scotland-v-brazil",                   "fecha":"Jun 24","hora":"18:00","ciudad":"Miami","j":3,"grp":"C","local":"Escocia","visita":"Brasil"},
    {"slug":"czech-republic-v-mexico",             "fecha":"Jun 24","hora":"21:00","ciudad":"Ciudad de México","j":3,"grp":"A","local":"Rep. Checa","visita":"México"},
    {"slug":"south-africa-v-south-korea",          "fecha":"Jun 24","hora":"21:00","ciudad":"Monterrey","j":3,"grp":"A","local":"Sudáfrica","visita":"Corea del Sur"},
    {"slug":"curacao-v-ivory-coast",               "fecha":"Jun 25","hora":"16:00","ciudad":"Philadelphia","j":3,"grp":"E","local":"Curazao","visita":"C. de Marfil"},
    {"slug":"ecuador-v-germany",                   "fecha":"Jun 25","hora":"16:00","ciudad":"Nueva York","j":3,"grp":"E","local":"Ecuador","visita":"Alemania"},
    {"slug":"japan-v-sweden",                      "fecha":"Jun 25","hora":"19:00","ciudad":"Dallas","j":3,"grp":"F","local":"Japón","visita":"Suecia"},
    {"slug":"tunisia-v-netherlands",               "fecha":"Jun 25","hora":"19:00","ciudad":"Kansas City","j":3,"grp":"F","local":"Túnez","visita":"Países Bajos"},
    {"slug":"paraguay-v-australia",                "fecha":"Jun 25","hora":"22:00","ciudad":"San Francisco","j":3,"grp":"D","local":"Paraguay","visita":"Australia"},
    {"slug":"turkey-v-usa",                        "fecha":"Jun 25","hora":"22:00","ciudad":"Los Ángeles","j":3,"grp":"D","local":"Turquía","visita":"USA"},
    {"slug":"norway-v-france",                     "fecha":"Jun 26","hora":"15:00","ciudad":"Boston","j":3,"grp":"I","local":"Noruega","visita":"Francia"},
    {"slug":"senegal-v-iraq",                      "fecha":"Jun 26","hora":"15:00","ciudad":"Toronto","j":3,"grp":"I","local":"Senegal","visita":"Irak"},
    {"slug":"cape-verde-v-saudi-arabia",           "fecha":"Jun 26","hora":"20:00","ciudad":"Houston","j":3,"grp":"H","local":"Cabo Verde","visita":"Arabia Saudita"},
    {"slug":"uruguay-v-spain",                     "fecha":"Jun 26","hora":"20:00","ciudad":"Guadalajara","j":3,"grp":"H","local":"Uruguay","visita":"España"},
    {"slug":"egypt-v-iran",                        "fecha":"Jun 26","hora":"23:00","ciudad":"Seattle","j":3,"grp":"G","local":"Egipto","visita":"Irán"},
    {"slug":"new-zealand-v-belgium",               "fecha":"Jun 26","hora":"23:00","ciudad":"Vancouver","j":3,"grp":"G","local":"Nueva Zelanda","visita":"Bélgica"},
    {"slug":"panama-v-england",                    "fecha":"Jun 27","hora":"17:00","ciudad":"Nueva York","j":3,"grp":"L","local":"Panamá","visita":"Inglaterra"},
    {"slug":"croatia-v-ghana",                     "fecha":"Jun 27","hora":"17:00","ciudad":"Philadelphia","j":3,"grp":"L","local":"Croacia","visita":"Ghana"},
    {"slug":"colombia-v-portugal",                 "fecha":"Jun 27","hora":"19:30","ciudad":"Miami","j":3,"grp":"K","local":"Colombia","visita":"Portugal"},
    {"slug":"dr-congo-v-uzbekistan",               "fecha":"Jun 27","hora":"19:30","ciudad":"Atlanta","j":3,"grp":"K","local":"RD Congo","visita":"Uzbekistán"},
    {"slug":"algeria-v-austria",                   "fecha":"Jun 27","hora":"22:00","ciudad":"Kansas City","j":3,"grp":"J","local":"Argelia","visita":"Austria"},
    {"slug":"jordan-v-argentina",                  "fecha":"Jun 27","hora":"22:00","ciudad":"Dallas","j":3,"grp":"J","local":"Jordania","visita":"Argentina"},
]

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
    if not ids: return []
    r = sc.get(f"{BASE}/api/markets/v2/all-odds?market-ids={ids}&repub=OC", timeout=15)
    return r.json()

def process_match(match):
    sc = make_scraper()
    slug = match['slug']
    try:
        markets = get_market_ids(sc, slug)
        win_id = markets.get('Win Market') or markets.get('Match Betting')
        cs_id  = markets.get('Correct Score')
        if not win_id and not cs_id:
            return {**match, 'error': 'no markets', 'win_table': {}, 'cs_top': {}}

        odds_data = get_odds(sc, win_id, cs_id)

        win_table = {}  # bk -> {outcome: decimal}
        cs_raw = {}     # score -> {bk: decimal}

        for mkt in odds_data:
            mid = str(mkt.get('marketId',''))
            bets = {b['betId']: b for b in mkt.get('bets', [])}

            if mid == win_id:
                for o in mkt.get('odds', []):
                    bk = o.get('bookmakerCode','?')
                    if bk not in TRUSTED: continue
                    bid = o['betId']
                    dec = o.get('oddsDecimal') or 99
                    name = bets.get(bid, {}).get('betName','?')
                    if bk not in win_table: win_table[bk] = {}
                    if name not in win_table[bk] or dec < win_table[bk][name]:
                        win_table[bk][name] = round(dec, 2)

            elif mid == cs_id:
                for o in mkt.get('odds', []):
                    bk = o.get('bookmakerCode','?')
                    if bk not in TRUSTED: continue
                    bid = o['betId']
                    dec = o.get('oddsDecimal') or 99
                    score = bets.get(bid, {}).get('line','?')
                    if score not in cs_raw: cs_raw[score] = {}
                    if bk not in cs_raw[score] or dec < cs_raw[score][bk]:
                        cs_raw[score][bk] = round(dec, 2)

        # Top 8 CS scores by lowest average odds
        def avg(d): return sum(d.values())/len(d) if d else 99
        cs_top = dict(sorted(cs_raw.items(), key=lambda x: avg(x[1]))[:8])

        # Consensus from trusted only
        def consensus(by_bk_val):
            votes = {}
            for bk, outcomes in by_bk_val.items():
                best = min(outcomes, key=outcomes.get)
                votes[best] = votes.get(best, 0) + 1
            if not votes: return None, '❓', {}
            winner = max(votes, key=votes.get)
            pct = votes[winner] / sum(votes.values())
            nivel = '🟢' if pct >= 0.75 else ('🟡' if pct >= 0.55 else '🔴')
            return winner, nivel, votes

        def consensus_cs(cs_top_local):
            votes = {}
            for score, bk_odds in cs_top_local.items():
                for bk in bk_odds:
                    votes[score] = votes.get(score, 0) + 1
            # pick score with most bookmakers agreeing it's the fave (lowest odds)
            # Alternative: for each BK, which score has lowest odds
            bk_fave = {}
            for score, bk_odds in cs_raw.items():
                for bk, dec in bk_odds.items():
                    if bk not in TRUSTED: continue
                    if bk not in bk_fave or dec < bk_fave[bk][1]:
                        bk_fave[bk] = (score, dec)
            cs_votes = {}
            for bk, (score, _) in bk_fave.items():
                cs_votes[score] = cs_votes.get(score, 0) + 1
            if not cs_votes: return None, '❓', {}
            winner = max(cs_votes, key=cs_votes.get)
            pct = cs_votes[winner] / sum(cs_votes.values())
            nivel = '🟢' if pct >= 0.75 else ('🟡' if pct >= 0.55 else '🔴')
            return winner, nivel, cs_votes

        win_pred, win_nivel, win_votes = consensus(win_table)
        cs_pred, cs_nivel, cs_votes = consensus_cs(cs_top)

        print(f"  ✅ [{match['grp']} J{match['j']}] {match['local']} vs {match['visita']}: 1X2={win_pred}{win_nivel} CS={cs_pred}{cs_nivel}")

        return {
            **match,
            'error': None,
            'win_pred': win_pred, 'win_nivel': win_nivel, 'win_votes': win_votes,
            'cs_pred': cs_pred,   'cs_nivel': cs_nivel,   'cs_votes': cs_votes,
            'win_table': win_table,
            'cs_top': cs_top,
        }
    except Exception as e:
        print(f"  ❌ {slug}: {e}")
        return {**match, 'error': str(e), 'win_table': {}, 'cs_top': {}}

def run_batch(batch_num):
    start = batch_num * BATCH_SIZE
    end = min(start + BATCH_SIZE, len(MATCHES))
    batch = MATCHES[start:end]
    print(f"\nBatch {batch_num}: partidos {start+1}–{end}")
    results = [None] * len(batch)
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {ex.submit(process_match, m): i for i, m in enumerate(batch)}
        for fut in as_completed(futures):
            idx = futures[fut]
            results[idx] = fut.result()
    out = os.path.join(OUT_DIR, f'detail_batch_{batch_num}.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"  Guardado: {out}")

def merge_batches():
    num = (len(MATCHES) + BATCH_SIZE - 1) // BATCH_SIZE
    all_results = []
    for b in range(num):
        path = os.path.join(OUT_DIR, f'detail_batch_{b}.json')
        with open(path, encoding='utf-8') as f:
            all_results.extend(json.load(f))
    out = os.path.join(OUT_DIR, 'odds_detail_2026.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"Merge listo: {out} ({len(all_results)} partidos)")

if __name__ == '__main__':
    arg = sys.argv[1] if len(sys.argv) > 1 else '0'
    if arg == 'merge':
        merge_batches()
    else:
        run_batch(int(arg))
