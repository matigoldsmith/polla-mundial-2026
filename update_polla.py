#!/usr/bin/env python3
"""
update_polla.py — Actualiza cuotas y regenera el HTML de la polla mundialera.
Uso: python3 update_polla.py
Tiempo estimado: ~3-4 minutos
"""
import json, re, time, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import cloudscraper

try:
    from curl_cffi import requests as cffi_requests
    CURL_CFFI = True
except ImportError:
    CURL_CFFI = False

DIR = os.path.dirname(os.path.abspath(__file__))
BASE = "https://www.oddschecker.com"
TRUSTED = {'BF', 'B3', 'UN', 'OE', 'MA', 'VC', 'WA'}
BK_NAMES = {'BF':'Betfair','B3':'bet365','UN':'Unibet','OE':'10bet','MA':'Matchbook','VC':'BetVictor','WA':'Betway'}
BK_ORDER = ['BF','B3','UN','OE','MA','VC','WA']
BK_URLS  = {'BF':'https://www.betfair.com','B3':'https://www.bet365.com','UN':'https://www.unibet.com',
            'OE':'https://www.10bet.com','MA':'https://www.matchbook.com','VC':'https://www.betvictor.com','WA':'https://www.betway.com'}

EN_ES = {'Mexico':'México','South Africa':'Sudáfrica','South Korea':'Corea del Sur','Czech Republic':'Rep. Checa',
 'Canada':'Canadá','Bosnia and Herzegovina':'Bosnia','USA':'USA','Paraguay':'Paraguay','Qatar':'Qatar',
 'Switzerland':'Suiza','Brazil':'Brasil','Morocco':'Marruecos','Haiti':'Haití','Scotland':'Escocia',
 'Australia':'Australia','Turkey':'Turquía','Germany':'Alemania','Curacao':'Curazao',
 'Ivory Coast':'C. de Marfil','Ecuador':'Ecuador','Netherlands':'Países Bajos','Japan':'Japón',
 'Sweden':'Suecia','Tunisia':'Túnez','Belgium':'Bélgica','Egypt':'Egipto','Spain':'España',
 'Cape Verde':'Cabo Verde','Saudi Arabia':'Arabia Saudita','Uruguay':'Uruguay','Iran':'Irán',
 'New Zealand':'Nueva Zelanda','France':'Francia','Senegal':'Senegal','Iraq':'Irak','Norway':'Noruega',
 'Argentina':'Argentina','Algeria':'Argelia','Austria':'Austria','Jordan':'Jordania','Portugal':'Portugal',
 'DR Congo':'RD Congo','England':'Inglaterra','Croatia':'Croacia','Ghana':'Ghana','Panama':'Panamá',
 'Uzbekistan':'Uzbekistán','Colombia':'Colombia','Draw':'Empate'}

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

MATCHES = [
    {"slug":"mexico-v-south-africa","fecha":"Jun 11","hora":"15:00","ciudad":"Ciudad de México","j":1,"grp":"A","local":"México","visita":"Sudáfrica"},
    {"slug":"south-korea-v-czech-republic","fecha":"Jun 11","hora":"22:00","ciudad":"Guadalajara","j":1,"grp":"A","local":"Corea del Sur","visita":"Rep. Checa"},
    {"slug":"canada-v-bosnia-and-herzegovina","fecha":"Jun 12","hora":"15:00","ciudad":"Toronto","j":1,"grp":"B","local":"Canadá","visita":"Bosnia"},
    {"slug":"usa-v-paraguay","fecha":"Jun 12","hora":"21:00","ciudad":"Los Ángeles","j":1,"grp":"D","local":"USA","visita":"Paraguay"},
    {"slug":"australia-v-turkey","fecha":"Jun 13","hora":"00:00","ciudad":"Vancouver","j":1,"grp":"D","local":"Australia","visita":"Turquía"},
    {"slug":"qatar-v-switzerland","fecha":"Jun 13","hora":"15:00","ciudad":"San Francisco","j":1,"grp":"B","local":"Qatar","visita":"Suiza"},
    {"slug":"brazil-v-morocco","fecha":"Jun 13","hora":"18:00","ciudad":"Nueva York","j":1,"grp":"C","local":"Brasil","visita":"Marruecos"},
    {"slug":"haiti-v-scotland","fecha":"Jun 13","hora":"21:00","ciudad":"Boston","j":1,"grp":"C","local":"Haití","visita":"Escocia"},
    {"slug":"germany-v-curacao","fecha":"Jun 14","hora":"13:00","ciudad":"Houston","j":1,"grp":"E","local":"Alemania","visita":"Curazao"},
    {"slug":"netherlands-v-japan","fecha":"Jun 14","hora":"16:00","ciudad":"Dallas","j":1,"grp":"F","local":"Países Bajos","visita":"Japón"},
    {"slug":"ivory-coast-v-ecuador","fecha":"Jun 14","hora":"19:00","ciudad":"Philadelphia","j":1,"grp":"E","local":"C. de Marfil","visita":"Ecuador"},
    {"slug":"sweden-v-tunisia","fecha":"Jun 14","hora":"22:00","ciudad":"Monterrey","j":1,"grp":"F","local":"Suecia","visita":"Túnez"},
    {"slug":"spain-v-cape-verde","fecha":"Jun 15","hora":"12:00","ciudad":"Atlanta","j":1,"grp":"H","local":"España","visita":"Cabo Verde"},
    {"slug":"belgium-v-egypt","fecha":"Jun 15","hora":"15:00","ciudad":"Seattle","j":1,"grp":"G","local":"Bélgica","visita":"Egipto"},
    {"slug":"saudi-arabia-v-uruguay","fecha":"Jun 15","hora":"18:00","ciudad":"Miami","j":1,"grp":"H","local":"Arabia Saudita","visita":"Uruguay"},
    {"slug":"iran-v-new-zealand","fecha":"Jun 15","hora":"21:00","ciudad":"Los Ángeles","j":1,"grp":"G","local":"Irán","visita":"Nueva Zelanda"},
    {"slug":"austria-v-jordan","fecha":"Jun 16","hora":"00:00","ciudad":"San Francisco","j":1,"grp":"J","local":"Austria","visita":"Jordania"},
    {"slug":"france-v-senegal","fecha":"Jun 16","hora":"15:00","ciudad":"Nueva York","j":1,"grp":"I","local":"Francia","visita":"Senegal"},
    {"slug":"iraq-v-norway","fecha":"Jun 16","hora":"18:00","ciudad":"Boston","j":1,"grp":"I","local":"Irak","visita":"Noruega"},
    {"slug":"argentina-v-algeria","fecha":"Jun 16","hora":"21:00","ciudad":"Kansas City","j":1,"grp":"J","local":"Argentina","visita":"Argelia"},
    {"slug":"portugal-v-dr-congo","fecha":"Jun 17","hora":"13:00","ciudad":"Houston","j":1,"grp":"K","local":"Portugal","visita":"RD Congo"},
    {"slug":"england-v-croatia","fecha":"Jun 17","hora":"16:00","ciudad":"Dallas","j":1,"grp":"L","local":"Inglaterra","visita":"Croacia"},
    {"slug":"ghana-v-panama","fecha":"Jun 17","hora":"19:00","ciudad":"Toronto","j":1,"grp":"L","local":"Ghana","visita":"Panamá"},
    {"slug":"uzbekistan-v-colombia","fecha":"Jun 17","hora":"22:00","ciudad":"Ciudad de México","j":1,"grp":"K","local":"Uzbekistán","visita":"Colombia"},
    {"slug":"czech-republic-v-south-africa","fecha":"Jun 18","hora":"12:00","ciudad":"Atlanta","j":2,"grp":"A","local":"Rep. Checa","visita":"Sudáfrica"},
    {"slug":"switzerland-v-bosnia-and-herzegovina","fecha":"Jun 18","hora":"15:00","ciudad":"Los Ángeles","j":2,"grp":"B","local":"Suiza","visita":"Bosnia"},
    {"slug":"canada-v-qatar","fecha":"Jun 18","hora":"18:00","ciudad":"Vancouver","j":2,"grp":"B","local":"Canadá","visita":"Qatar"},
    {"slug":"mexico-v-south-korea","fecha":"Jun 18","hora":"21:00","ciudad":"Guadalajara","j":2,"grp":"A","local":"México","visita":"Corea del Sur"},
    {"slug":"turkey-v-paraguay","fecha":"Jun 19","hora":"00:00","ciudad":"San Francisco","j":2,"grp":"D","local":"Turquía","visita":"Paraguay"},
    {"slug":"usa-v-australia","fecha":"Jun 19","hora":"15:00","ciudad":"Seattle","j":2,"grp":"D","local":"USA","visita":"Australia"},
    {"slug":"scotland-v-morocco","fecha":"Jun 19","hora":"18:00","ciudad":"Boston","j":2,"grp":"C","local":"Escocia","visita":"Marruecos"},
    {"slug":"brazil-v-haiti","fecha":"Jun 19","hora":"21:00","ciudad":"Philadelphia","j":2,"grp":"C","local":"Brasil","visita":"Haití"},
    {"slug":"tunisia-v-japan","fecha":"Jun 20","hora":"00:00","ciudad":"Monterrey","j":2,"grp":"F","local":"Túnez","visita":"Japón"},
    {"slug":"netherlands-v-sweden","fecha":"Jun 20","hora":"13:00","ciudad":"Houston","j":2,"grp":"F","local":"Países Bajos","visita":"Suecia"},
    {"slug":"germany-v-ivory-coast","fecha":"Jun 20","hora":"16:00","ciudad":"Toronto","j":2,"grp":"E","local":"Alemania","visita":"C. de Marfil"},
    {"slug":"ecuador-v-curacao","fecha":"Jun 20","hora":"20:00","ciudad":"Kansas City","j":2,"grp":"E","local":"Ecuador","visita":"Curazao"},
    {"slug":"spain-v-saudi-arabia","fecha":"Jun 21","hora":"12:00","ciudad":"Atlanta","j":2,"grp":"H","local":"España","visita":"Arabia Saudita"},
    {"slug":"belgium-v-iran","fecha":"Jun 21","hora":"15:00","ciudad":"Los Ángeles","j":2,"grp":"G","local":"Bélgica","visita":"Irán"},
    {"slug":"uruguay-v-cape-verde","fecha":"Jun 21","hora":"18:00","ciudad":"Miami","j":2,"grp":"H","local":"Uruguay","visita":"Cabo Verde"},
    {"slug":"new-zealand-v-egypt","fecha":"Jun 21","hora":"21:00","ciudad":"Vancouver","j":2,"grp":"G","local":"Nueva Zelanda","visita":"Egipto"},
    {"slug":"argentina-v-austria","fecha":"Jun 22","hora":"13:00","ciudad":"Dallas","j":2,"grp":"J","local":"Argentina","visita":"Austria"},
    {"slug":"france-v-iraq","fecha":"Jun 22","hora":"17:00","ciudad":"Philadelphia","j":2,"grp":"I","local":"Francia","visita":"Irak"},
    {"slug":"norway-v-senegal","fecha":"Jun 22","hora":"20:00","ciudad":"Nueva York","j":2,"grp":"I","local":"Noruega","visita":"Senegal"},
    {"slug":"jordan-v-algeria","fecha":"Jun 22","hora":"23:00","ciudad":"San Francisco","j":2,"grp":"J","local":"Jordania","visita":"Argelia"},
    {"slug":"portugal-v-uzbekistan","fecha":"Jun 23","hora":"13:00","ciudad":"Houston","j":2,"grp":"K","local":"Portugal","visita":"Uzbekistán"},
    {"slug":"colombia-v-dr-congo","fecha":"Jun 23","hora":"22:00","ciudad":"Guadalajara","j":2,"grp":"K","local":"Colombia","visita":"RD Congo"},
    {"slug":"england-v-ghana","fecha":"Jun 23","hora":"16:00","ciudad":"Boston","j":2,"grp":"L","local":"Inglaterra","visita":"Ghana"},
    {"slug":"panama-v-croatia","fecha":"Jun 23","hora":"19:00","ciudad":"Toronto","j":2,"grp":"L","local":"Panamá","visita":"Croacia"},
    {"slug":"switzerland-v-canada","fecha":"Jun 24","hora":"15:00","ciudad":"Vancouver","j":3,"grp":"B","local":"Suiza","visita":"Canadá"},
    {"slug":"bosnia-and-herzegovina-v-qatar","fecha":"Jun 24","hora":"15:00","ciudad":"Seattle","j":3,"grp":"B","local":"Bosnia","visita":"Qatar"},
    {"slug":"scotland-v-brazil","fecha":"Jun 24","hora":"18:00","ciudad":"Miami","j":3,"grp":"C","local":"Escocia","visita":"Brasil"},
    {"slug":"morocco-v-haiti","fecha":"Jun 24","hora":"18:00","ciudad":"Atlanta","j":3,"grp":"C","local":"Marruecos","visita":"Haití"},
    {"slug":"czech-republic-v-mexico","fecha":"Jun 24","hora":"21:00","ciudad":"Ciudad de México","j":3,"grp":"A","local":"Rep. Checa","visita":"México"},
    {"slug":"south-africa-v-south-korea","fecha":"Jun 24","hora":"21:00","ciudad":"Monterrey","j":3,"grp":"A","local":"Sudáfrica","visita":"Corea del Sur"},
    {"slug":"ecuador-v-germany","fecha":"Jun 25","hora":"16:00","ciudad":"Nueva York","j":3,"grp":"E","local":"Ecuador","visita":"Alemania"},
    {"slug":"curacao-v-ivory-coast","fecha":"Jun 25","hora":"16:00","ciudad":"Philadelphia","j":3,"grp":"E","local":"Curazao","visita":"C. de Marfil"},
    {"slug":"japan-v-sweden","fecha":"Jun 25","hora":"19:00","ciudad":"Dallas","j":3,"grp":"F","local":"Japón","visita":"Suecia"},
    {"slug":"tunisia-v-netherlands","fecha":"Jun 25","hora":"19:00","ciudad":"Kansas City","j":3,"grp":"F","local":"Túnez","visita":"Países Bajos"},
    {"slug":"turkey-v-usa","fecha":"Jun 25","hora":"22:00","ciudad":"Los Ángeles","j":3,"grp":"D","local":"Turquía","visita":"USA"},
    {"slug":"paraguay-v-australia","fecha":"Jun 25","hora":"22:00","ciudad":"San Francisco","j":3,"grp":"D","local":"Paraguay","visita":"Australia"},
    {"slug":"norway-v-france","fecha":"Jun 26","hora":"15:00","ciudad":"Boston","j":3,"grp":"I","local":"Noruega","visita":"Francia"},
    {"slug":"senegal-v-iraq","fecha":"Jun 26","hora":"15:00","ciudad":"Toronto","j":3,"grp":"I","local":"Senegal","visita":"Irak"},
    {"slug":"cape-verde-v-saudi-arabia","fecha":"Jun 26","hora":"20:00","ciudad":"Houston","j":3,"grp":"H","local":"Cabo Verde","visita":"Arabia Saudita"},
    {"slug":"uruguay-v-spain","fecha":"Jun 26","hora":"20:00","ciudad":"Guadalajara","j":3,"grp":"H","local":"Uruguay","visita":"España"},
    {"slug":"egypt-v-iran","fecha":"Jun 26","hora":"23:00","ciudad":"Seattle","j":3,"grp":"G","local":"Egipto","visita":"Irán"},
    {"slug":"new-zealand-v-belgium","fecha":"Jun 26","hora":"23:00","ciudad":"Vancouver","j":3,"grp":"G","local":"Nueva Zelanda","visita":"Bélgica"},
    {"slug":"panama-v-england","fecha":"Jun 27","hora":"17:00","ciudad":"Nueva York","j":3,"grp":"L","local":"Panamá","visita":"Inglaterra"},
    {"slug":"croatia-v-ghana","fecha":"Jun 27","hora":"17:00","ciudad":"Philadelphia","j":3,"grp":"L","local":"Croacia","visita":"Ghana"},
    {"slug":"colombia-v-portugal","fecha":"Jun 27","hora":"19:30","ciudad":"Miami","j":3,"grp":"K","local":"Colombia","visita":"Portugal"},
    {"slug":"dr-congo-v-uzbekistan","fecha":"Jun 27","hora":"19:30","ciudad":"Atlanta","j":3,"grp":"K","local":"RD Congo","visita":"Uzbekistán"},
    {"slug":"algeria-v-austria","fecha":"Jun 27","hora":"22:00","ciudad":"Kansas City","j":3,"grp":"J","local":"Argelia","visita":"Austria"},
    {"slug":"jordan-v-argentina","fecha":"Jun 27","hora":"22:00","ciudad":"Dallas","j":3,"grp":"J","local":"Jordania","visita":"Argentina"},
]

# ── Scraper ──────────────────────────────────────────────────────────────────

class CffiSession:
    """Thin wrapper around curl_cffi session that mimics requests API."""
    def __init__(self):
        self._s = cffi_requests.Session(impersonate="chrome120")
        self.cookies = self._s.cookies
        self.headers = self._s.headers
    def get(self, url, **kw):
        kw.setdefault('timeout', 25)
        return self._s.get(url, **kw)
    def cookies_update(self, d):
        self._s.cookies.update(d)

def make_scraper():
    if CURL_CFFI:
        s = CffiSession()
        s.headers.update({
            'Accept-Language': 'en-GB,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        return s
    sc = cloudscraper.create_scraper(browser={'browser':'chrome','platform':'darwin','mobile':False})
    sc.headers.update({
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-GB,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    return sc

def get_market_ids(sc, slug):
    url = f"{BASE}/football/world-cup/{slug}/winner"
    # Retry up to 3 times — first request can get 403 from Cloudflare
    html_text = ''
    for attempt in range(3):
        if attempt > 0:
            wait = 4 * attempt
            print(f"  ↩️  [{slug}] retry {attempt} (wait {wait}s)...")
            time.sleep(wait)
            sc = make_scraper()
        r = sc.get(url, timeout=25)
        if r.status_code == 200 and len(r.text) > 10000:
            html_text = r.text
            break
        print(f"  ⚠️  [{slug}] attempt {attempt+1}: HTTP {r.status_code} / {len(r.text)} chars")
    if not html_text:
        html_text = r.text  # use whatever we got

    soup = BeautifulSoup(html_text, 'html.parser')
    markets = {}

    # Method 1: <section id="market_*"> (works for most matches)
    for sec in soup.find_all('section', id=re.compile(r'^market_')):
        mid = sec['id'].replace('market_','')
        h2 = sec.find('h2')
        markets[h2.get_text(strip=True) if h2 else ''] = mid
    if markets:
        return markets

    # Method 2: any element with id="market_*"
    for el in soup.find_all(id=re.compile(r'^market_')):
        mid = el['id'].replace('market_','')
        h2 = el.find('h2') or el.find('h3')
        label = h2.get_text(strip=True) if h2 else el.get('data-market-name', '')
        if mid and label:
            markets[label] = mid
    if markets:
        return markets

    # Method 3: data-market-id attributes
    for el in soup.find_all(attrs={'data-market-id': True}):
        mid = el['data-market-id']
        label = el.get('data-market-name', '')
        h2 = el.find('h2') or el.find('h3')
        if h2:
            label = h2.get_text(strip=True)
        if mid and label:
            markets[label] = mid
    if markets:
        return markets

    # Method 4: search script tags for JSON market data
    for script in soup.find_all('script'):
        text = script.string or ''
        if not text or 'market' not in text.lower():
            continue
        # Try various patterns for marketName+marketId
        for pattern in [
            r'"marketName"\s*:\s*"([^"]+)"[^}]{0,300}?"marketId"\s*:\s*["\']?(\d+)["\']?',
            r'"name"\s*:\s*"([^"]+)"[^}]{0,300}?"id"\s*:\s*["\']?(\d+)["\']?',
        ]:
            for m in re.finditer(pattern, text, re.DOTALL):
                name, mid = m.group(1), m.group(2)
                if name in ('Win Market', 'Match Betting', 'Correct Score'):
                    markets[name] = mid
        if markets:
            return markets

    # Method 5: find market_ IDs anywhere in raw HTML and probe API
    all_mids = list(dict.fromkeys(re.findall(r'market[_-](\d{5,})', html_text)))[:8]
    if all_mids:
        try:
            odds = sc.get(f"{BASE}/api/markets/v2/all-odds?market-ids={','.join(all_mids)}&repub=OC", timeout=15).json()
            if isinstance(odds, list):
                for mkt in odds:
                    name = mkt.get('marketName', '') or mkt.get('name', '')
                    mid = str(mkt.get('marketId', mkt.get('id', '')))
                    if name in ('Win Market', 'Match Betting'):
                        markets['Win Market'] = mid
                    elif 'Correct Score' in name:
                        markets['Correct Score'] = mid
        except Exception:
            pass
    if markets:
        return markets

    # Debug: print response info to help diagnose
    sections_found = len(soup.find_all('section'))
    print(f"  🔍 [{slug}] HTTP {r.status_code} | html={len(html_text)} chars | sections={sections_found} | snippet: {html_text[200:400]!r}")
    return markets

def get_odds_api(sc, win_id, cs_id):
    ids = ','.join(filter(None,[win_id,cs_id]))
    if not ids: return []
    return sc.get(f"{BASE}/api/markets/v2/all-odds?market-ids={ids}&repub=OC", timeout=15).json()

def process_match(match, cf_cookies=None):
    sc = make_scraper()
    if cf_cookies:
        try:
            sc.cookies.update(cf_cookies)
        except Exception:
            pass
    slug = match['slug']
    try:
        markets = get_market_ids(sc, slug)
        win_id = markets.get('Win Market') or markets.get('Match Betting')
        cs_id  = markets.get('Correct Score')
        if not win_id and not cs_id:
            return {**match, 'error':'no markets','win_table':{},'cs_top':{}}
        odds_data = get_odds_api(sc, win_id, cs_id)
        win_table, cs_raw = {}, {}
        for mkt in odds_data:
            mid = str(mkt.get('marketId',''))
            bets = {b['betId']:b for b in mkt.get('bets',[])}
            if mid == win_id:
                for o in mkt.get('odds',[]):
                    bk = o.get('bookmakerCode','?')
                    if bk not in TRUSTED: continue
                    bid, dec = o['betId'], o.get('oddsDecimal') or 99
                    name = bets.get(bid,{}).get('betName','?')
                    if bk not in win_table: win_table[bk] = {}
                    if name not in win_table[bk] or dec < win_table[bk][name]:
                        win_table[bk][name] = round(dec,2)
            elif mid == cs_id:
                for o in mkt.get('odds',[]):
                    bk = o.get('bookmakerCode','?')
                    if bk not in TRUSTED: continue
                    bid, dec = o['betId'], o.get('oddsDecimal') or 99
                    score = bets.get(bid,{}).get('line','?')
                    if score not in cs_raw: cs_raw[score] = {}
                    if bk not in cs_raw[score] or dec < cs_raw[score][bk]:
                        cs_raw[score][bk] = round(dec,2)
        def avg(d): return sum(d.values())/len(d) if d else 99
        cs_top = dict(sorted(cs_raw.items(), key=lambda x: avg(x[1]))[:8])
        def consensus_win(wt):
            votes = {}
            for bk,outcomes in wt.items():
                best = min(outcomes, key=outcomes.get)
                votes[best] = votes.get(best,0)+1
            if not votes: return None,'❓'
            w = max(votes, key=votes.get)
            pct = votes[w]/sum(votes.values())
            return w, '🟢' if pct>=0.75 else ('🟡' if pct>=0.55 else '🔴')
        def consensus_cs(cs_r):
            bk_fave = {}
            for score,bk_odds in cs_r.items():
                for bk,dec in bk_odds.items():
                    if bk not in TRUSTED: continue
                    if bk not in bk_fave or dec < bk_fave[bk][1]:
                        bk_fave[bk] = (score,dec)
            votes = {}
            for bk,(score,_) in bk_fave.items():
                votes[score] = votes.get(score,0)+1
            if not votes: return None,'❓'
            w = max(votes, key=votes.get)
            pct = votes[w]/sum(votes.values())
            return w, '🟢' if pct>=0.75 else ('🟡' if pct>=0.55 else '🔴')
        wp, wn = consensus_win(win_table)
        cp, cn = consensus_cs(cs_raw)
        print(f"  ✅ [{match['grp']} J{match['j']}] {match['local']} vs {match['visita']}: 1X2={wp}{wn} CS={cp}{cn}")
        return {**match,'error':None,'win_pred':wp,'win_nivel':wn,'cs_pred':cp,'cs_nivel':cn,
                'win_table':win_table,'cs_top':cs_top}
    except Exception as e:
        print(f"  ❌ {slug}: {e}")
        return {**match,'error':str(e),'win_table':{},'cs_top':{}}

# ── Procesamiento ─────────────────────────────────────────────────────────────

def cf_warmup():
    """Solve Cloudflare challenge and return cookies for reuse."""
    sc = make_scraper()
    try:
        r = sc.get(f"{BASE}/football/world-cup", timeout=20)
        print(f"CF warmup: HTTP {r.status_code} ({len(r.text)} chars)")
        time.sleep(3)
        return dict(sc.cookies)
    except Exception as e:
        print(f"CF warmup error: {e}")
        return {}

def scrape_all():
    print(f"Scrapeando {len(MATCHES)} partidos (6 workers en paralelo)...")
    # Warmup CF session first
    print("Calentando sesión Cloudflare...")
    cf_cookies = cf_warmup()
    print(f"CF cookies obtenidas: {list(cf_cookies.keys()) or 'ninguna'}")

    results_map = {}
    batches = [MATCHES[i:i+18] for i in range(0, len(MATCHES), 18)]
    for bi, batch in enumerate(batches):
        print(f"\nBatch {bi+1}/{len(batches)}...")
        with ThreadPoolExecutor(max_workers=6) as ex:
            futures = {ex.submit(process_match, m, cf_cookies): m['slug'] for m in batch}
            for fut in as_completed(futures):
                r = fut.result()
                results_map[r['slug']] = r
        time.sleep(1)

    # Retry failures sequentially with fresh CF session
    failed = [m for m in MATCHES if not results_map.get(m['slug'],{}).get('win_table')]
    if failed:
        print(f"\nReintentando {len(failed)} fallidos (con nueva sesión CF)...")
        cf_cookies2 = cf_warmup()
        for m in failed:
            r = process_match(m, cf_cookies2)
            results_map[m['slug']] = r
            time.sleep(2)

    return [results_map[m['slug']] for m in MATCHES if m['slug'] in results_map]

def build_data(raw_results):
    def lev(m, win_pred):
        local_en = next((en for en,es in EN_ES.items() if es==m['local']), m['local'])
        if win_pred=='Draw': return 'E'
        if win_pred in (local_en, m['local']): return 'L'
        return 'V'
    def refine_cs(m, cs_pred, l):
        if not cs_pred or '-' not in str(cs_pred): return cs_pred, False
        a,b = int(cs_pred.split('-')[0]), int(cs_pred.split('-')[1])
        if a==b and l in ('L','V'): return ('1-0' if l=='L' else '0-1'), True
        if l=='V': return f'{b}-{a}', False
        return cs_pred, False
    out = []
    for r in raw_results:
        wp = r.get('win_pred','')
        l = lev(r, wp)
        cs_refined, ovr = refine_cs(r, r.get('cs_pred',''), l)
        wt = {bk:{EN_ES.get(k,k):v for k,v in r['win_table'][bk].items()}
              for bk in BK_ORDER if bk in r.get('win_table',{})}
        import datetime as _dt
        ts = _dt.datetime.now(_dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') if r.get('win_table') else r.get('last_updated','')
        out.append({
            'slug':r['slug'],'fecha':r['fecha'],'hora':r['hora'],'ciudad':r['ciudad'],
            'j':r['j'],'grp':r['grp'],'local':r['local'],'visita':r['visita'],
            'win_pred':EN_ES.get(wp,wp),'win_nivel':r.get('win_nivel',''),
            'cs_refined':cs_refined,'cs_nivel':r.get('cs_nivel',''),
            'cs_overridden':ovr,'has_data':bool(r.get('win_table')),
            'win_table':wt,'cs_top':r.get('cs_top',{}),
            'last_updated':ts,
        })
    return out

# ── HTML ──────────────────────────────────────────────────────────────────────

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="es"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Polla Mundial 2026</title>
<style>
:root{color-scheme:light}*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f5f5f2;color:#1a1a1a;font-size:13px}
.container{max-width:800px;margin:0 auto;padding:20px 16px}
h1{font-size:16px;font-weight:600;margin-bottom:2px}.sub{font-size:11px;color:#999;margin-bottom:20px}
.day-title{font-size:11px;font-weight:700;letter-spacing:.4px;color:#888;text-transform:uppercase;margin:20px 0 6px;padding-bottom:4px;border-bottom:1px solid #e0e0da}
.match-wrap{margin-bottom:5px}
.match{display:grid;grid-template-columns:70px 1fr auto;align-items:center;background:#fff;border:.5px solid #e8e8e4;border-radius:8px;padding:8px 12px;gap:10px;cursor:pointer;transition:background .1s}
.match:hover{background:#fafaf8}.match.ovr{border-left:3px solid #e0a020}.match.open{border-radius:8px 8px 0 0;border-bottom:none}
.meta{font-size:10px;color:#aaa;line-height:1.6}.meta .hora{font-size:12px;font-weight:600;color:#444}.meta .ciudad{color:#aaa}
.meta .grp-badge{display:inline-block;font-size:9px;font-weight:700;background:#f0f0ec;color:#888;border-radius:3px;padding:1px 4px;margin-top:1px}
.teams{min-width:0}.team-row{display:flex;align-items:center;gap:5px;padding:1px 0}
.flag{font-size:14px;line-height:1;flex-shrink:0}.tname{font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.tname.bold{font-weight:600}
.right{display:flex;flex-direction:column;align-items:flex-end;gap:4px;flex-shrink:0}
.result{font-size:10px;padding:2px 6px;border-radius:4px;font-weight:500;white-space:nowrap}
.L{background:#eaf3de;color:#3b6d11}.E{background:#faeeda;color:#854f0b}.V{background:#faece7;color:#993c1d}
.score{font-size:18px;font-weight:700;letter-spacing:2px;font-variant-numeric:tabular-nums}.score.ovr{color:#c08010}
.bottom-row{display:flex;align-items:center;gap:5px}.cons{font-size:12px}
.chevron{font-size:10px;color:#ccc;transition:transform .2s}.chevron.open{transform:rotate(180deg)}
.detail{display:none;background:#fff;border:.5px solid #e8e8e4;border-top:none;border-radius:0 0 8px 8px;padding:12px 14px 14px}
.detail.open{display:block}
.detail-links{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap}
.det-link{font-size:11px;color:#3b71c8;text-decoration:none;background:#f0f4ff;border-radius:4px;padding:3px 8px}
.det-link:hover{background:#dde8ff}
.det-section{margin-bottom:12px}.det-title{font-size:10px;font-weight:700;color:#888;text-transform:uppercase;letter-spacing:.4px;margin-bottom:6px}
.odds-table{width:100%;border-collapse:collapse;font-size:11px}
.odds-table th{text-align:left;color:#888;font-weight:500;padding:3px 6px;border-bottom:.5px solid #eee;white-space:nowrap}
.odds-table td{padding:4px 6px;border-bottom:.5px solid #f5f5f2;white-space:nowrap}
.odds-table tr:last-child td{border-bottom:none}.odds-table .bk-name{font-weight:500;color:#444}
.odds-table .best{font-weight:700;color:#2a6a2a}.odds-table .score-col{font-weight:600;color:#1a1a1a;font-variant-numeric:tabular-nums}
.no-data{font-size:11px;color:#aaa;font-style:italic;padding:6px 0}
.updated{font-size:10px;color:#bbb;margin-top:4px}
</style></head><body>
<div class="container">
<h1>Polla Mundial 2026</h1>
<p class="sub">Betfair · bet365 · Unibet · 10bet · Matchbook · BetVictor · Betway · Hora Chile · Score: Local–Visita</p>
<p class="updated">Actualizado: {updated}</p>
<div id="root"></div>
</div>
<script>
const DATA={DATA_JSON};
const FLAGS={FLAGS_JSON};
const BK_NAMES={{BF:'Betfair',B3:'bet365',UN:'Unibet',OE:'10bet',MA:'Matchbook',VC:'BetVictor',WA:'Betway'}};
const BK_ORDER=['BF','B3','UN','OE','MA','VC','WA'];
const BK_URLS={{BF:'https://www.betfair.com',B3:'https://www.bet365.com',UN:'https://www.unibet.com',OE:'https://www.10bet.com',MA:'https://www.matchbook.com',VC:'https://www.betvictor.com',WA:'https://www.betway.com'}};
const BASE='https://www.oddschecker.com/football/world-cup';
const DOW={DOW_JSON};
function getLEV(m){{const w=m.win_pred;if(!w||w==='Empate')return'E';if(w===m.local)return'L';return'V';}}
function buildWinTable(m){{
  const wt=m.win_table||{{}};const bks=BK_ORDER.filter(bk=>bk in wt);
  if(!bks.length)return'<p class="no-data">Sin datos</p>';
  const outcomes=[m.local,'Empate',m.visita];
  const best={{}};outcomes.forEach(o=>{{let mn=Infinity;bks.forEach(bk=>{{const v=(wt[bk]||{{}})[o];if(v&&v<mn)mn=v;}});best[o]=mn;}});
  let h=`<table class="odds-table"><thead><tr><th>Casa</th><th>${{FLAGS[m.local]||''}} ${{m.local}}</th><th>Empate</th><th>${{FLAGS[m.visita]||''}} ${{m.visita}}</th></tr></thead><tbody>`;
  bks.forEach(bk=>{{const row=wt[bk]||{{}};h+=`<tr><td class="bk-name"><a href="${{BK_URLS[bk]}}" target="_blank" style="color:#3b71c8;text-decoration:none">${{BK_NAMES[bk]}}</a></td>`;outcomes.forEach(o=>{{const v=row[o];h+=`<td${{v&&v===best[o]?' class="best"':''}}>${{v?v.toFixed(2):'—'}}</td>`;}}); h+='</tr>';}});
  return h+'</tbody></table>';
}}
function buildCSTable(m){{
  const cs=m.cs_top||{{}};const scores=Object.keys(cs);
  if(!scores.length)return'<p class="no-data">Sin datos</p>';
  const bks=BK_ORDER.filter(bk=>scores.some(s=>bk in(cs[s]||{{}})));
  let h=`<table class="odds-table"><thead><tr><th>Score</th>${{bks.map(bk=>`<th>${{BK_NAMES[bk]}}</th>`).join('')}}</tr></thead><tbody>`;
  scores.forEach(s=>{{const isBest=s===m.cs_pred;h+=`<tr><td class="score-col"${{isBest?' style="color:#c08010"':''}}>${{s}}${{isBest?' ★':''}}</td>`;bks.forEach(bk=>{{const v=(cs[s]||{{}})[bk];h+=`<td>${{v?v.toFixed(2):'—'}}</td>`;}});h+='</tr>';}});
  return h+'</tbody></table>';
}}
function buildDetail(m){{
  const ocW=`${{BASE}}/${{m.slug}}/winner`,ocC=`${{BASE}}/${{m.slug}}/correct-score`;
  return`<div class="detail-links"><a class="det-link" href="${{ocW}}" target="_blank">OddsChecker 1X2 ↗</a><a class="det-link" href="${{ocC}}" target="_blank">OddsChecker Marcador Exacto ↗</a>${{BK_ORDER.filter(bk=>bk in(m.win_table||{{}})).map(bk=>`<a class="det-link" href="${{BK_URLS[bk]}}" target="_blank">${{BK_NAMES[bk]}} ↗</a>`).join('')}}</div>
  <div class="det-section"><div class="det-title">Cuotas 1X2</div>${{buildWinTable(m)}}</div>
  <div class="det-section"><div class="det-title">Top marcadores · Recomendado: <strong style="color:#2a6a2a">${{m.cs_refined}}</strong>${{m.cs_overridden?' <span style="color:#c08010;font-size:10px">(corregido por 1X2)</span>':''}}</div>${{buildCSTable(m)}}</div>`;
}}
const byDate={{}};DATA.forEach(m=>{{if(!byDate[m.fecha])byDate[m.fecha]=[];byDate[m.fecha].push(m);}});
const root=document.getElementById('root');
Object.keys(byDate).forEach(fecha=>{{
  const block=document.createElement('div');
  block.innerHTML=`<div class="day-title">${{DOW[fecha]||fecha}}</div>`;
  byDate[fecha].forEach(m=>{{
    const ovr=m.cs_overridden,lev=getLEV(m),lf=FLAGS[m.local]||'🏳',vf=FLAGS[m.visita]||'🏳';
    const levCls=lev==='L'?'L':lev==='V'?'V':'E',levTxt=lev==='E'?'Empate':m.win_pred;
    const id='m_'+m.slug.replace(/-/g,'_');
    const wrap=document.createElement('div');wrap.className='match-wrap';
    wrap.innerHTML=`<div class="match${{ovr?' ovr':''}}" id="${{id}}" onclick="toggle('${{id}}')">
      <div class="meta"><div class="hora">${{m.hora}}</div><div class="ciudad">${{m.ciudad}}</div><div><span class="grp-badge">G${{m.grp}} · J${{m.j}}</span></div></div>
      <div class="teams">
        <div class="team-row"><span class="flag">${{lf}}</span><span class="tname${{lev==='L'?' bold':''}}">${{m.local}}</span></div>
        <div class="team-row"><span class="flag">${{vf}}</span><span class="tname${{lev==='V'?' bold':''}}">${{m.visita}}</span></div>
      </div>
      <div class="right">
        <div style="display:flex;align-items:center;gap:6px"><span class="result ${{levCls}}">${{levTxt}}</span><span class="score${{ovr?' ovr':''}}">${{m.cs_refined||'—'}}</span></div>
        <div class="bottom-row"><span class="cons">${{m.cs_nivel||''}}</span><span class="chevron" id="chv_${{id}}">▾</span></div>
      </div>
    </div>
    <div class="detail" id="det_${{id}}">${{buildDetail(m)}}</div>`;
    block.appendChild(wrap);
  }});
  root.appendChild(block);
}});
function toggle(id){{const d=document.getElementById('det_'+id),c=document.getElementById('chv_'+id),card=document.getElementById(id),o=d.classList.contains('open');d.classList.toggle('open',!o);card.classList.toggle('open',!o);c.classList.toggle('open',!o);}}
</script></body></html>'''

def build_html(data):
    import datetime
    now = datetime.datetime.now().strftime('%d %b %Y %H:%M')
    flags_js  = json.dumps(FLAGS, ensure_ascii=False)
    data_js   = json.dumps(data, ensure_ascii=False, separators=(',',':'))
    dow_js    = json.dumps(DOW, ensure_ascii=False)
    html = HTML_TEMPLATE
    html = html.replace('{updated}', now)
    html = html.replace('{DATA_JSON}', data_js)
    html = html.replace('{FLAGS_JSON}', flags_js)
    html = html.replace('{DOW_JSON}', dow_js[1:-1])  # strip outer {}
    return html

# ── Kickoff check (CLT = UTC-4) ───────────────────────────────────────────────

def match_started(m):
    """Returns True if the match kickoff time (CLT = UTC-4) has already passed."""
    import datetime
    MONTH = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}
    try:
        month_str, day_str = m['fecha'].split()
        month = MONTH[month_str]
        day = int(day_str)
        h, mn = map(int, m['hora'].split(':'))
        # CLT = UTC-4, so kickoff UTC = hora + 4
        kickoff_utc = datetime.datetime(2026, month, day, h, mn, tzinfo=datetime.timezone.utc) + datetime.timedelta(hours=4)
        return datetime.datetime.now(datetime.timezone.utc) >= kickoff_utc
    except Exception:
        return False

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    import datetime, argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--match-id', type=int, default=None,
                        help='Índice del partido a actualizar (0-71). Si se omite, actualiza todos.')
    args = parser.parse_args()

    print("=" * 60)
    print("  POLLA MUNDIAL 2026 — Actualizando cuotas")
    print(f"  {datetime.datetime.now().strftime('%d %b %Y %H:%M')}")
    print("=" * 60)

    json_path = os.path.join(DIR, 'polla_data_final.json')

    if args.match_id is not None:
        # ── Modo partido único ──────────────────────────────────────
        idx = args.match_id
        if idx < 0 or idx >= len(MATCHES):
            print(f"❌ match-id {idx} fuera de rango (0-{len(MATCHES)-1})")
            sys.exit(1)

        m = MATCHES[idx]
        if match_started(m):
            print(f"⏸ Partido ya iniciado: {m['local']} vs {m['visita']} ({m['fecha']} {m['hora']} CLT) — cuotas congeladas.")
            sys.exit(0)

        print(f"Actualizando partido #{idx}: {m['local']} vs {m['visita']}...")

        # Cargar JSON existente
        if os.path.exists(json_path):
            with open(json_path, encoding='utf-8') as f:
                data = json.load(f)
        else:
            print("❌ No existe polla_data_final.json — ejecuta sin --match-id primero.")
            sys.exit(1)

        # Warmup CF session before single-match scrape
        print("Calentando sesión Cloudflare...")
        cf_cookies = cf_warmup()

        # Scrapear solo ese partido
        raw_one = process_match(m, cf_cookies)
        if raw_one.get('win_table'):
            # Preservar last_updated del dato anterior si existe
            raw_one.setdefault('last_updated', data[idx].get('last_updated',''))
            updated = build_data([raw_one])
            if updated:
                data[idx] = updated[0]
                print(f"✅ Datos actualizados para partido #{idx}")
        else:
            print(f"⚠️  Scrape sin datos para partido #{idx} — manteniendo datos anteriores")

        ok = sum(1 for d in data if d.get('has_data'))
        print(f"\nPartidos con datos: {ok}/{len(data)}")

    else:
        # ── Modo completo — skip partidos ya iniciados ──────────────
        to_scrape = [m for m in MATCHES if not match_started(m)]
        skipped   = [m for m in MATCHES if match_started(m)]

        if skipped:
            print(f"⏸ Saltando {len(skipped)} partido(s) ya iniciados (cuotas congeladas):")
            for m in skipped:
                print(f"   {m['local']} vs {m['visita']} ({m['fecha']} {m['hora']} CLT)")

        if not to_scrape:
            print("ℹ️  Todos los partidos ya iniciaron. Nada que actualizar.")
            sys.exit(0)

        print(f"\nActualizando {len(to_scrape)} partido(s)...")

        # Scrapear solo los pendientes
        raw_pending = []
        batches = [to_scrape[i:i+18] for i in range(0, len(to_scrape), 18)]
        from concurrent.futures import ThreadPoolExecutor, as_completed
        for bi, batch in enumerate(batches):
            print(f"\nBatch {bi+1}/{len(batches)}...")
            with ThreadPoolExecutor(max_workers=6) as ex:
                futures = {ex.submit(process_match, m): m['slug'] for m in batch}
                for fut in as_completed(futures):
                    raw_pending.append(fut.result())
            time.sleep(1)

        # Retry failures
        failed = [m for m in to_scrape if not any(r.get('slug') == m['slug'] and r.get('win_table') for r in raw_pending)]
        if failed:
            print(f"\nReintentando {len(failed)} fallidos...")
            for m in failed:
                raw_pending.append(process_match(m))
                time.sleep(1.5)

        # Merge con JSON existente (preservar datos de partidos ya iniciados)
        if os.path.exists(json_path):
            with open(json_path, encoding='utf-8') as f:
                existing = {d['slug']: d for d in json.load(f)}
        else:
            existing = {}

        # Solo usar nuevo dato si tiene win_table válido; si no, preservar el anterior
        raw_map = {r['slug']: r for r in raw_pending if r.get('win_table')}
        failed_slugs = {r['slug'] for r in raw_pending if not r.get('win_table')}
        if failed_slugs:
            print(f"\n⚠️  {len(failed_slugs)} partido(s) sin datos — manteniendo valores anteriores:")
            for s in failed_slugs:
                print(f"   {s}")

        merged_raw = []
        for m in MATCHES:
            if m['slug'] in raw_map:
                # Nuevo dato válido — preservar last_updated previo como fallback
                r = raw_map[m['slug']]
                if m['slug'] in existing:
                    r.setdefault('last_updated', existing[m['slug']].get('last_updated',''))
                merged_raw.append(r)
            elif m['slug'] in existing:
                merged_raw.append(existing[m['slug']])  # mantener dato anterior (started o fallo)
            else:
                merged_raw.append(m)

        data = build_data(merged_raw)
        ok = sum(1 for d in data if d.get('has_data'))
        print(f"\nPartidos con datos: {ok}/{len(data)}")

    # Guardar JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',',':'))
    print(f"JSON: {json_path}")

    print("\n✅ Listo.")

if __name__ == '__main__':
    main()
