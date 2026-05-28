#!/usr/bin/env python3
"""
Scraper de cuotas Mundial 2026 desde OddsChecker
Usa cloudscraper para bypassear Cloudflare.
Estrategia:
  1. GET HTML de cada partido → extraer JSON inline con market IDs
  2. GET /api/markets/v2/all-odds?market-ids=ID&repub=OC → cuotas
  3. Guarda resultados parciales cada 10 partidos
"""

import json
import time
import re
import os
import warnings
from datetime import datetime
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

try:
    import cloudscraper
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'darwin', 'mobile': False}
    )
    print("cloudscraper OK")
except ImportError:
    import requests as scraper
    print("WARNING: usando requests (sin bypass Cloudflare)")

BASE = "https://www.oddschecker.com"
BASE_PATH = os.path.dirname(os.path.abspath(__file__))

HEADERS = {
    "Referer": "https://www.oddschecker.com/football/world-cup",
    "Accept-Language": "es-US,es;q=0.9,en;q=0.8",
}

MATCHES = [
    # Jornada 1
    {"slug": "mexico-v-south-africa",              "fecha": "Jun 11", "j": 1, "grp": "A", "local": "México",          "visita": "Sudáfrica"},
    {"slug": "south-korea-v-czech-republic",       "fecha": "Jun 11", "j": 1, "grp": "A", "local": "Corea del Sur",   "visita": "Rep. Checa"},
    {"slug": "canada-v-bosnia-and-herzegovina",    "fecha": "Jun 12", "j": 1, "grp": "B", "local": "Canadá",          "visita": "Bosnia"},
    {"slug": "usa-v-paraguay",                     "fecha": "Jun 12", "j": 1, "grp": "D", "local": "USA",             "visita": "Paraguay"},
    {"slug": "qatar-v-switzerland",                "fecha": "Jun 13", "j": 1, "grp": "B", "local": "Qatar",           "visita": "Suiza"},
    {"slug": "brazil-v-morocco",                   "fecha": "Jun 13", "j": 1, "grp": "C", "local": "Brasil",          "visita": "Marruecos"},
    {"slug": "haiti-v-scotland",                   "fecha": "Jun 14", "j": 1, "grp": "C", "local": "Haití",           "visita": "Escocia"},
    {"slug": "australia-v-turkey",                 "fecha": "Jun 14", "j": 1, "grp": "D", "local": "Australia",       "visita": "Turquía"},
    {"slug": "germany-v-curacao",                  "fecha": "Jun 14", "j": 1, "grp": "E", "local": "Alemania",        "visita": "Curazao"},
    {"slug": "ivory-coast-v-ecuador",              "fecha": "Jun 14", "j": 1, "grp": "E", "local": "C. de Marfil",   "visita": "Ecuador"},
    {"slug": "netherlands-v-japan",                "fecha": "Jun 14", "j": 1, "grp": "F", "local": "Países Bajos",   "visita": "Japón"},
    {"slug": "sweden-v-tunisia",                   "fecha": "Jun 15", "j": 1, "grp": "F", "local": "Suecia",          "visita": "Túnez"},
    {"slug": "belgium-v-egypt",                    "fecha": "Jun 15", "j": 1, "grp": "G", "local": "Bélgica",         "visita": "Egipto"},
    {"slug": "spain-v-cape-verde",                 "fecha": "Jun 15", "j": 1, "grp": "H", "local": "España",          "visita": "Cabo Verde"},
    {"slug": "saudi-arabia-v-uruguay",             "fecha": "Jun 15", "j": 1, "grp": "H", "local": "Arabia Saudita", "visita": "Uruguay"},
    {"slug": "iran-v-new-zealand",                 "fecha": "Jun 16", "j": 1, "grp": "G", "local": "Irán",            "visita": "Nueva Zelanda"},
    {"slug": "france-v-senegal",                   "fecha": "Jun 16", "j": 1, "grp": "I", "local": "Francia",         "visita": "Senegal"},
    {"slug": "iraq-v-norway",                      "fecha": "Jun 16", "j": 1, "grp": "I", "local": "Irak",            "visita": "Noruega"},
    {"slug": "argentina-v-algeria",                "fecha": "Jun 17", "j": 1, "grp": "J", "local": "Argentina",       "visita": "Argelia"},
    {"slug": "austria-v-jordan",                   "fecha": "Jun 17", "j": 1, "grp": "J", "local": "Austria",         "visita": "Jordania"},
    {"slug": "portugal-v-dr-congo",                "fecha": "Jun 17", "j": 1, "grp": "K", "local": "Portugal",        "visita": "RD Congo"},
    {"slug": "england-v-croatia",                  "fecha": "Jun 17", "j": 1, "grp": "L", "local": "Inglaterra",      "visita": "Croacia"},
    {"slug": "ghana-v-panama",                     "fecha": "Jun 17", "j": 1, "grp": "L", "local": "Ghana",           "visita": "Panamá"},
    {"slug": "uzbekistan-v-colombia",              "fecha": "Jun 18", "j": 1, "grp": "K", "local": "Uzbekistán",      "visita": "Colombia"},
    # Jornada 2
    {"slug": "mexico-v-south-korea",               "fecha": "Jun 18", "j": 2, "grp": "A", "local": "México",          "visita": "Corea del Sur"},
    {"slug": "czech-republic-v-south-africa",      "fecha": "Jun 18", "j": 2, "grp": "A", "local": "Rep. Checa",      "visita": "Sudáfrica"},
    {"slug": "canada-v-qatar",                     "fecha": "Jun 18", "j": 2, "grp": "B", "local": "Canadá",          "visita": "Qatar"},
    {"slug": "switzerland-v-bosnia-and-herzegovina","fecha": "Jun 18", "j": 2, "grp": "B", "local": "Suiza",           "visita": "Bosnia"},
    {"slug": "brazil-v-haiti",                     "fecha": "Jun 19", "j": 2, "grp": "C", "local": "Brasil",          "visita": "Haití"},
    {"slug": "scotland-v-morocco",                 "fecha": "Jun 19", "j": 2, "grp": "C", "local": "Escocia",         "visita": "Marruecos"},
    {"slug": "usa-v-australia",                    "fecha": "Jun 19", "j": 2, "grp": "D", "local": "USA",             "visita": "Australia"},
    {"slug": "turkey-v-paraguay",                  "fecha": "Jun 19", "j": 2, "grp": "D", "local": "Turquía",         "visita": "Paraguay"},
    {"slug": "germany-v-ivory-coast",              "fecha": "Jun 20", "j": 2, "grp": "E", "local": "Alemania",        "visita": "C. de Marfil"},
    {"slug": "ecuador-v-curacao",                  "fecha": "Jun 20", "j": 2, "grp": "E", "local": "Ecuador",         "visita": "Curazao"},
    {"slug": "netherlands-v-sweden",               "fecha": "Jun 20", "j": 2, "grp": "F", "local": "Países Bajos",   "visita": "Suecia"},
    {"slug": "tunisia-v-japan",                    "fecha": "Jun 21", "j": 2, "grp": "F", "local": "Túnez",           "visita": "Japón"},
    {"slug": "belgium-v-iran",                     "fecha": "Jun 21", "j": 2, "grp": "G", "local": "Bélgica",         "visita": "Irán"},
    {"slug": "new-zealand-v-egypt",                "fecha": "Jun 21", "j": 2, "grp": "G", "local": "Nueva Zelanda",   "visita": "Egipto"},
    {"slug": "spain-v-saudi-arabia",               "fecha": "Jun 21", "j": 2, "grp": "H", "local": "España",          "visita": "Arabia Saudita"},
    {"slug": "uruguay-v-cape-verde",               "fecha": "Jun 21", "j": 2, "grp": "H", "local": "Uruguay",         "visita": "Cabo Verde"},
    {"slug": "france-v-iraq",                      "fecha": "Jun 22", "j": 2, "grp": "I", "local": "Francia",         "visita": "Irak"},
    {"slug": "norway-v-senegal",                   "fecha": "Jun 22", "j": 2, "grp": "I", "local": "Noruega",         "visita": "Senegal"},
    {"slug": "argentina-v-austria",                "fecha": "Jun 22", "j": 2, "grp": "J", "local": "Argentina",       "visita": "Austria"},
    {"slug": "jordan-v-algeria",                   "fecha": "Jun 22", "j": 2, "grp": "J", "local": "Jordania",        "visita": "Argelia"},
    {"slug": "portugal-v-uzbekistan",              "fecha": "Jun 23", "j": 2, "grp": "K", "local": "Portugal",        "visita": "Uzbekistán"},
    {"slug": "colombia-v-dr-congo",                "fecha": "Jun 23", "j": 2, "grp": "K", "local": "Colombia",        "visita": "RD Congo"},
    {"slug": "england-v-ghana",                    "fecha": "Jun 23", "j": 2, "grp": "L", "local": "Inglaterra",      "visita": "Ghana"},
    {"slug": "panama-v-croatia",                   "fecha": "Jun 23", "j": 2, "grp": "L", "local": "Panamá",          "visita": "Croacia"},
    # Jornada 3
    {"slug": "bosnia-and-herzegovina-v-qatar",     "fecha": "Jun 24", "j": 3, "grp": "B", "local": "Bosnia",          "visita": "Qatar"},
    {"slug": "switzerland-v-canada",               "fecha": "Jun 24", "j": 3, "grp": "B", "local": "Suiza",           "visita": "Canadá"},
    {"slug": "morocco-v-haiti",                    "fecha": "Jun 24", "j": 3, "grp": "C", "local": "Marruecos",       "visita": "Haití"},
    {"slug": "scotland-v-brazil",                  "fecha": "Jun 24", "j": 3, "grp": "C", "local": "Escocia",         "visita": "Brasil"},
    {"slug": "czech-republic-v-mexico",            "fecha": "Jun 25", "j": 3, "grp": "A", "local": "Rep. Checa",      "visita": "México"},
    {"slug": "south-africa-v-south-korea",         "fecha": "Jun 25", "j": 3, "grp": "A", "local": "Sudáfrica",       "visita": "Corea del Sur"},
    {"slug": "curacao-v-ivory-coast",              "fecha": "Jun 25", "j": 3, "grp": "E", "local": "Curazao",         "visita": "C. de Marfil"},
    {"slug": "ecuador-v-germany",                  "fecha": "Jun 25", "j": 3, "grp": "E", "local": "Ecuador",         "visita": "Alemania"},
    {"slug": "japan-v-sweden",                     "fecha": "Jun 25", "j": 3, "grp": "F", "local": "Japón",           "visita": "Suecia"},
    {"slug": "tunisia-v-netherlands",              "fecha": "Jun 25", "j": 3, "grp": "F", "local": "Túnez",           "visita": "Países Bajos"},
    {"slug": "paraguay-v-australia",               "fecha": "Jun 26", "j": 3, "grp": "D", "local": "Paraguay",        "visita": "Australia"},
    {"slug": "turkey-v-usa",                       "fecha": "Jun 26", "j": 3, "grp": "D", "local": "Turquía",         "visita": "USA"},
    {"slug": "norway-v-france",                    "fecha": "Jun 26", "j": 3, "grp": "I", "local": "Noruega",         "visita": "Francia"},
    {"slug": "senegal-v-iraq",                     "fecha": "Jun 26", "j": 3, "grp": "I", "local": "Senegal",         "visita": "Irak"},
    {"slug": "egypt-v-iran",                       "fecha": "Jun 27", "j": 3, "grp": "G", "local": "Egipto",          "visita": "Irán"},
    {"slug": "new-zealand-v-belgium",              "fecha": "Jun 27", "j": 3, "grp": "G", "local": "Nueva Zelanda",   "visita": "Bélgica"},
    {"slug": "cape-verde-v-saudi-arabia",          "fecha": "Jun 27", "j": 3, "grp": "H", "local": "Cabo Verde",      "visita": "Arabia Saudita"},
    {"slug": "uruguay-v-spain",                    "fecha": "Jun 27", "j": 3, "grp": "H", "local": "Uruguay",         "visita": "España"},
    {"slug": "colombia-v-portugal",                "fecha": "Jun 27", "j": 3, "grp": "K", "local": "Colombia",        "visita": "Portugal"},
    {"slug": "dr-congo-v-uzbekistan",              "fecha": "Jun 27", "j": 3, "grp": "K", "local": "RD Congo",        "visita": "Uzbekistán"},
    {"slug": "croatia-v-ghana",                    "fecha": "Jun 27", "j": 3, "grp": "L", "local": "Croacia",         "visita": "Ghana"},
    {"slug": "panama-v-england",                   "fecha": "Jun 27", "j": 3, "grp": "L", "local": "Panamá",          "visita": "Inglaterra"},
    {"slug": "algeria-v-austria",                  "fecha": "Jun 28", "j": 3, "grp": "J", "local": "Argelia",         "visita": "Austria"},
    {"slug": "jordan-v-argentina",                 "fecha": "Jun 28", "j": 3, "grp": "J", "local": "Jordania",        "visita": "Argentina"},
]


def get_market_ids(slug):
    url = f"{BASE}/football/world-cup/{slug}/winner"
    try:
        r = scraper.get(url, headers=HEADERS, timeout=20, verify=False)
        if r.status_code == 403:
            print(f"  403 Cloudflare blocked")
            return None, None
        if r.status_code != 200:
            print(f"  HTTP {r.status_code}")
            return None, None
        html = r.text
    except Exception as e:
        print(f"  ERROR HTML: {e}")
        return None, None

    win_id = cs_id = None
    block = re.search(r'"markets":\s*\{"entities":\s*\{([\s\S]*?)\},"ids"', html)
    if block:
        for m in re.finditer(r'"(\d+)":\s*\{[^}]*?"marketTypeName":"([^"]+)"', block.group(1)):
            if m.group(2) == 'Win Market' and not win_id:
                win_id = m.group(1)
            elif m.group(2) == 'Correct Score' and not cs_id:
                cs_id = m.group(1)
    if not win_id or not cs_id:
        for m in re.finditer(r'"ocMarketId":(\d+)', html):
            ctx = html[m.start():m.start()+300]
            if '"Win Market"' in ctx and not win_id:
                win_id = m.group(1)
            elif '"Correct Score"' in ctx and not cs_id:
                cs_id = m.group(1)
    return win_id, cs_id


def get_odds(market_id, slug):
    url = f"{BASE}/api/markets/v2/all-odds?market-ids={market_id}&repub=OC"
    h = {**HEADERS, "Accept": "application/json",
         "Referer": f"{BASE}/football/world-cup/{slug}/winner"}
    try:
        r = scraper.get(url, headers=h, timeout=15, verify=False)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  ERROR API {market_id}: {e}")
        return []


def parse_1x2(market):
    if not market or not market.get('bets'):
        return {}
    bets = market['bets']
    roles = {}
    if len(bets) >= 3:
        roles[bets[0]['betId']] = 'L'
        roles[bets[1]['betId']] = 'E'
        roles[bets[2]['betId']] = 'V'
    by_bk = {}
    for odd in market.get('odds', []):
        bk = odd.get('bookmakerCode', '?')
        role = roles.get(odd.get('betId'), '?')
        dec = odd.get('oddsDecimal')
        if dec:
            if bk not in by_bk:
                by_bk[bk] = {}
            by_bk[bk][role] = dec
    # Fallback: bestOdds
    if not by_bk:
        for b in bets:
            role = roles.get(b['betId'], '?')
            for bk in b.get('bestOddsBookmakerCodes', []):
                if bk not in by_bk:
                    by_bk[bk] = {}
                by_bk[bk][role] = b.get('bestOddsDecimal')
    return by_bk


def parse_cs(market):
    if not market or not market.get('bets'):
        return {}
    bets = {b['betId']: b.get('line', b.get('betName', '?')) for b in market['bets']}
    by_bk = {}
    for odd in market.get('odds', []):
        bk = odd.get('bookmakerCode', '?')
        score = bets.get(odd.get('betId'), '?')
        dec = odd.get('oddsDecimal')
        if dec and (bk not in by_bk or dec < by_bk[bk]['dec']):
            by_bk[bk] = {'score': score, 'dec': dec}
    if not by_bk:
        for b in market['bets']:
            score = b.get('line', b.get('betName', '?'))
            dec = b.get('bestOddsDecimal')
            for bk in b.get('bestOddsBookmakerCodes', []):
                if dec and (bk not in by_bk or dec < by_bk[bk]['dec']):
                    by_bk[bk] = {'score': score, 'dec': dec}
    return by_bk


def consensus_1x2(by_bk):
    votes = {}
    for odds in by_bk.values():
        valid = {r: d for r, d in odds.items() if d}
        if valid:
            best = min(valid, key=valid.get)
            votes[best] = votes.get(best, 0) + 1
    if not votes:
        return '?', 0.0, {}
    winner = max(votes, key=votes.get)
    total = sum(votes.values())
    return winner, round(votes[winner]/total, 2), votes


def consensus_cs(by_bk):
    votes = {}
    for d in by_bk.values():
        s = d.get('score', '?')
        if s and s != '?':
            votes[s] = votes.get(s, 0) + 1
    if not votes:
        return '?', 0.0, {}
    winner = max(votes, key=votes.get)
    total = sum(votes.values())
    return winner, round(votes[winner]/total, 2), votes


def nivel(pct):
    if pct >= 0.80: return 'ALTO'
    elif pct >= 0.60: return 'PARCIAL'
    return 'BAJO'


def scrape_match(m, delay=2.0):
    slug = m['slug']
    print(f"  [{m['grp']} J{m['j']}] {m['local']} vs {m['visita']}", end=' ')
    r = {**m, 'winId': None, 'csId': None, 'bks': 0,
         'pred1x2': '?', 'pct1x2': 0, 'predCS': '?', 'pctCS': 0,
         'votes1x2': {}, 'votesCS': {}, 'error': None}

    win_id, cs_id = get_market_ids(slug)
    r['winId'] = win_id
    r['csId'] = cs_id

    if not win_id and not cs_id:
        r['error'] = 'no_markets'
        print('-> ERROR: no markets')
        return r

    if win_id:
        data = get_odds(win_id, slug)
        if data:
            by_bk = parse_1x2(data[0])
            r['bks'] = len(by_bk)
            pred, pct, votes = consensus_1x2(by_bk)
            r['pred1x2'] = pred; r['pct1x2'] = pct; r['votes1x2'] = votes
        time.sleep(delay * 0.3)

    if cs_id:
        data = get_odds(cs_id, slug)
        if data:
            by_bk = parse_cs(data[0])
            pred, pct, votes = consensus_cs(by_bk)
            r['predCS'] = pred; r['pctCS'] = pct; r['votesCS'] = votes

    print(f"-> 1X2:{r['pred1x2']}({r['pct1x2']:.0%}) CS:{r['predCS']}({r['pctCS']:.0%}) [{r['bks']} bks]")
    return r


def save_partial(results, suffix=''):
    path = f"{BASE_PATH}/odds_mundial_2026{suffix}.json"
    clean = [{k: v for k, v in r.items() if 'raw' not in k} for r in results]
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(clean, f, ensure_ascii=False, indent=2)
    return path


def format_table(results):
    lines = [
        f"MUNDIAL 2026 - Cuotas OddsChecker",
        f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "=" * 100,
        f"{'#':<3} {'Fecha':<8} {'Grp':<4} {'J':<2} {'Partido':<35} {'1X2':<5} {'%':<6} {'CS':<8} {'%':<6} {'Casas':<6} {'Nivel'}",
        "-" * 100,
    ]
    for i, r in enumerate(results, 1):
        partido = f"{r['local']} vs {r['visita']}"
        p1 = r.get('pred1x2', '?'); c1 = f"{r.get('pct1x2',0):.0%}" if r.get('pct1x2') else '-'
        pcs = r.get('predCS', '?'); ccs = f"{r.get('pctCS',0):.0%}" if r.get('pctCS') else '-'
        bks = r.get('bks', 0)
        nv = nivel(r.get('pct1x2', 0)) if r.get('pred1x2', '?') != '?' else '-'
        err = f" [ERR:{r['error']}]" if r.get('error') else ''
        lines.append(f"{i:<3} {r['fecha']:<8} {r['grp']:<4} {r['j']:<2} {partido:<35} "
                     f"{str(p1):<5} {c1:<6} {str(pcs):<8} {ccs:<6} {bks:<6} {nv}{err}")
    lines.append("=" * 100)
    return '\n'.join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true', help='Solo primeros 3 partidos')
    parser.add_argument('--from-slug', type=str, help='Empezar desde este slug')
    parser.add_argument('--only-j3', action='store_true', help='Solo Jornada 3')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay entre partidos (seg)')
    args = parser.parse_args()

    matches = MATCHES
    if args.test:
        matches = MATCHES[:3]
    elif args.only_j3:
        matches = [m for m in MATCHES if m['j'] == 3]
    elif args.from_slug:
        idx = next((i for i, m in enumerate(MATCHES) if m['slug'] == args.from_slug), 0)
        matches = MATCHES[idx:]

    print(f"Procesando {len(matches)} partidos | delay={args.delay}s")

    # Cargar resultados existentes si hay
    existing = {}
    json_path = f"{BASE_PATH}/odds_mundial_2026.json"
    if os.path.exists(json_path):
        with open(json_path) as f:
            for r in json.load(f):
                existing[r['slug']] = r
        print(f"  Cargados {len(existing)} resultados previos")

    results = []
    for i, m in enumerate(matches):
        # Saltar si ya tenemos resultado válido
        if m['slug'] in existing and not existing[m['slug']].get('error'):
            print(f"  [{m['grp']} J{m['j']}] {m['local']} vs {m['visita']} -> CACHED")
            results.append(existing[m['slug']])
            continue

        r = scrape_match(m, delay=args.delay)
        results.append(r)
        existing[m['slug']] = r

        # Guardar parcial cada 5 partidos
        if (i + 1) % 5 == 0:
            save_partial(list(existing.values()), '_partial')

        if i < len(matches) - 1:
            time.sleep(args.delay)

    # Guardar final con todos los partidos en orden
    all_results = [existing.get(m['slug'], {**m, 'error': 'not_run'}) for m in MATCHES]
    final_path = save_partial(all_results)
    print(f"\nJSON final: {final_path}")

    table = format_table(all_results)
    txt_path = f"{BASE_PATH}/odds_mundial_2026.txt"
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(table)
    print(f"TXT final: {txt_path}")
    print()
    print(table)

    errors = [r for r in all_results if r.get('error')]
    if errors:
        print(f"\nERRORES ({len(errors)}): {[e['slug'] for e in errors]}")


if __name__ == '__main__':
    main()
