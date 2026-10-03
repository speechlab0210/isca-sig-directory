"""Fetch known public primary sources into a private review queue; never publish scraped text."""
import concurrent.futures, datetime as dt, hashlib, ipaddress, json, re, socket, ssl, sys, urllib.request, urllib.parse
try:
    import certifi
    # urllib on Windows does not trust some current CA chains by default; use certifi when present
    CTX=ssl.create_default_context(cafile=certifi.where())
except ImportError:
    CTX=ssl.create_default_context()
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
class Text(HTMLParser):
    def __init__(self): super().__init__(); self.skip=0; self.parts=[]; self.links=[]
    def handle_starttag(self,t,a):
        if t in ('script','style','noscript','svg'): self.skip+=1
        if t=='a':
            u=dict(a).get('href','')
            if u: self.links.append(u)
    def handle_endtag(self,t):
        if t in ('script','style','noscript','svg'): self.skip=max(0,self.skip-1)
    def handle_data(self,s):
        if not self.skip and s.strip(): self.parts.append(s.strip())
def public_url(url):
    p=urllib.parse.urlparse(url)
    if p.scheme not in ('http','https') or not p.hostname or p.username or p.password: raise ValueError('Invalid public URL')
    if p.hostname=='synsig.org' or p.hostname.endswith('.synsig.org'): raise ValueError('Blocked obsolete domain')
    for info in socket.getaddrinfo(p.hostname,p.port or (443 if p.scheme=='https' else 80),type=socket.SOCK_STREAM):
        if not ipaddress.ip_address(info[4][0]).is_global: raise ValueError('Non-public destination')
class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        public_url(newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)
def main():
    now=dt.datetime.now(dt.timezone.utc).isoformat(); day=dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).date().isoformat()
    run=ROOT/'ops'/'crawl'/day; run.mkdir(parents=True,exist_ok=True)
    base=json.loads((ROOT/'data/sigs.json').read_text(encoding='utf-8-sig')); ed=json.loads((ROOT/'data/editorial.json').read_text(encoding='utf-8-sig'))
    urls={'https://isca-speech.org/Special-Interest-Groups':{'ISCA roster'}}
    def add(u,label):
        # skipped: video hosts, login-only or app-only pages, PDFs and sites that block automated fetches — they can never be read as text
        if u and u.startswith(('http://','https://')) and not any(h in urllib.parse.urlparse(u).netloc for h in ('youtube.com','youtu.be','superlectures.com','bsky.app','slack.com','groups.google.com','mdpi.com','underline.io')) and not urllib.parse.urlparse(u).path.lower().endswith('.pdf'):
            urls.setdefault(u,set()).add(label)
    for s in base['sigs']:
        add(s['website'],s['acronym']);add(s['iscaUrl'],s['acronym'])
        for series in s['series']: add(series['pageUrl'],s['acronym'])
        for a in s['activities']: add(a.get('url'),s['acronym'])
        for v in s['videos']: add(v.get('url'),s['acronym'])
    for s in ed['series']:
        for link in s['links']: add(link['href'],s['sig'])
    for item in ed['central']: add(item.get('url'),'ISCA resources')
    if (ROOT/'data/events.json').exists():
        for e in json.loads((ROOT/'data/events.json').read_text(encoding='utf-8')): add(e.get('url'),e['sig'])
    previous={s['url']:s for s in json.loads((ROOT/'data/checks.json').read_text(encoding='utf-8')).get('sources',[])} if (ROOT/'data/checks.json').exists() else {}
    def fetch(item):
        url,groups=item; key=hashlib.sha256(url.encode()).hexdigest()[:20]
        result={'url':url,'groups':sorted(groups),'checkedAt':now}
        try:
            public_url(url)
            req=urllib.request.Request(url,headers={'User-Agent':'ISCA-SIG-Atlas/1.0 (+mailto:speechlab0210@gmail.com)','Accept':'text/html,application/xhtml+xml,text/plain'})
            with urllib.request.build_opener(SafeRedirect,urllib.request.HTTPSHandler(context=CTX)).open(req,timeout=25) as resp:
                raw=resp.read(2_000_001)
                if len(raw)>2_000_000: raise ValueError('Page exceeds collection limit')
                if not any(c in resp.headers.get('Content-Type','') for c in ('html','text/plain')): raise ValueError('Not a text source')
                html=raw.decode(resp.headers.get_content_charset() or 'utf-8',errors='replace')
                parser=Text();parser.feed(html); content='\n'.join(parser.parts)
                if len(content)<180 or re.search(r'^(Just a moment|Access Denied|Attention Required|403 Forbidden)',content,re.I): raise ValueError('Page content unavailable or challenge')
                digest=hashlib.sha256(content.encode()).hexdigest()
                (run/f'{key}.txt').write_text(content,encoding='utf-8')
                links=sorted(set(urllib.parse.urljoin(resp.url,u) for u in parser.links if not u.startswith(('javascript:','mailto:','#'))))
                (run/f'{key}.json').write_text(json.dumps({'url':url,'resolved':resp.url,'links':links,'textFile':f'{key}.txt'},ensure_ascii=False,indent=2),encoding='utf-8')
                old=previous.get(url,{})
                result.update(status='retrieved',httpStatus=resp.status,sha256=digest,changed=old.get('sha256')!=digest,snapshot=f'{key}.txt')
        except Exception as e:
            result.update(status='unavailable',error=type(e).__name__,changed=False)
            if previous.get(url,{}).get('sha256'): result['lastSuccessfulHash']=previous[url]['sha256']
        return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: results=list(pool.map(fetch,sorted(urls.items())))
    out={'checkedAt':now,'sources':results,'scope':'Official roster, every SIG profile/homepage, seminar indexes, event sources and association resources. A successful fetch is not a factual review.'}
    # Publication is a separate, reviewed step. Keep this stage private.
    (run/'checks.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'ops/latest-crawl.json').write_text(json.dumps({'directory':str(run),'checkedAt':now},indent=2),encoding='utf-8')
    print(json.dumps({'directory':str(run),'sources':len(results),'retrieved':sum(r['status']=='retrieved' for r in results),'changed':sum(r['changed'] for r in results),'unavailable':[{'url':r['url'],'error':r['error']} for r in results if r['status']!='retrieved']}))
if __name__=='__main__': main()
