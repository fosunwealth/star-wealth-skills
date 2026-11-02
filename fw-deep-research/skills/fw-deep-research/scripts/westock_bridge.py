import shutil;import subprocess;import sys;from pathlib import Path;from typing import Any,Dict,List,Optional,Sequence,Tuple;sys.path.insert(0,str(Path(__file__).resolve().parent));import os_compat;from markdown_document import split_table_row;from symbol_utils import is_standard_symbol,normalize_westock_symbol;W=tuple(os_compat.builtin_westock_roots());K=('股份有限公司','有限责任公司','有限公司','控股集团','集团股份','集团公司','Corporation','Limited','集团','控股','公司','Inc.','Corp.','Ltd.','Co.','Inc','Corp','Ltd','Co');X=frozenset(('OQ','N','NYSE','NASDAQ','HK','SH','SZ'))
def _all_ascii_letters(a):return bool(a)and all(('A'<=I<='Z' or 'a'<=I<='z' for I in a))
def _all_ascii_digits(a):return bool(a)and all(('0'<=I<='9' for I in a))
def l(a):
 lower=a.lower()
 for H in K:
  if lower.endswith(H.lower()):return a[:-len(H)]
 return a
def n(a):
 w=[];b=0
 while b<len(a):
  if a[b]not in('(','（'):
   w.append(a[b]);b+=1;continue
  end=b+1
  while end<len(a)and a[end]not in(')','）'):
   end+=1
  if end==len(a):
   w.append(a[b:]);break
  w.append(' ');b=end+1
 return ''.join(w)
def Z(a):
 ak=frozenset((',','/','|','，','、'));p=[];start=None
 for(index,I)in enumerate(a):
  if I.isspace()or I in ak:
   if start is not None:
    p.append(a[start:index]);start=None
  elif start is None:start=index
 if start is not None:p.append(a[start:])
 return p
def m(I):return I=='_' or I.isalnum()
def V(a):
 p=[];b=0
 while b<len(a):
  if b>0 and m(a[b- 1]):
   b+=1;continue
  if _all_ascii_letters(a[b]):
   end=b+1
   while end<len(a)and _all_ascii_letters(a[end]):
    end+=1
   ag=a[b:end];lower=ag.lower();au=('usa','us','hk','sh','sz','bj');M=any((lower.startswith(ar)and 1<=len(ag)-len(ar)<=5 for ar in au))
   if(1<=len(ag)<=5 or M)and(end==len(a)or not m(a[end])):p.append(ag)
   b=end;continue
  if _all_ascii_digits(a[b]):
   end=b+1
   while end<len(a)and _all_ascii_digits(a[end]):
    end+=1
   ah=end-b
   if 4<=ah<=6 and(end==len(a)or not m(a[end])):
    G=end
    if end+3<=len(a)and a[end:end+1]=='.':
     H=a[end+1:end+3].lower()
     if H in('hk','sh','sz','bj','us'):
      u=end+3
      if u==len(a)or not m(a[u]):G=u
    p.append(a[b:G]);b=G;continue
   b=end;continue
  b+=1
 return p
def d(aD):
 raw=aD.strip()
 if not raw.startswith('|'):return False
 b=1
 while b<len(raw)and raw[b].isspace():
  b+=1
 if b<len(raw)and raw[b]==':':b+=1
 start=b
 while b<len(raw)and raw[b]=='-':
  b+=1
 return b-start>=2
def af():
 L=shutil.which('westock-data')
 if L:return[L]
 aa=os_compat.westock_shim_basename()
 for ay in W:
  ad=ay/'scripts'/'index.js'
  if ad.is_file():
   aI=shutil.which('node')or 'node';return[aI,str(ad)]
  for aM in(f'scripts/{aa}',f'bin/{aa}','scripts/westock-data','bin/westock-data'):
   path=ay/aM
   if os_compat.is_runnable_file(path):return[str(path)]
 return None
def run_westock(args,*,timeout=45):
 aE=af()
 if not aE:return(127,'westock-data is unavailable')
 av=list(aE);av[0]=os_compat.resolve_exe(av[0])
 try:
  ax=subprocess.run([*av,*args],capture_output=True,text=True,timeout=timeout,check=False)
 except(OSError,subprocess.TimeoutExpired)as e:
  return(1,str(e))
 text=((ax.stdout or '')+'\n'+(ax.stderr or '')).strip();return(ax.returncode,text)
def normalize_symbol(code):
 c=str(code or '').strip()
 if not c:return ''
 if '.' in c:
  (aJ,H)=c.rsplit('.',1)
  if H.upper()in X:c=aJ
 al=c.lower()
 if al.startswith('us')and 1<=len(c[2:])<=5 and _all_ascii_letters(c[2:]):return normalize_westock_symbol(c)
 if 1<=len(c)<=5 and _all_ascii_letters(c):return normalize_westock_symbol(c)
 if al.startswith('hk')and 4<=len(c[2:])<=5 and _all_ascii_digits(c[2:]):return normalize_westock_symbol(c)
 if al[:2]in('sh','sz','bj')and len(c[2:])==6 and _all_ascii_digits(c[2:]):return normalize_westock_symbol(c)
 return c
def query_variants(query):
 raw=str(query or '').strip()
 if not raw:return[]
 w=[];az=set()
 def add(aH):
  s=str(aH or '').strip()
  if not s:return
  key=s.lower()
  if key in az:return
  az.add(key);w.append(s)
 add(raw);add(n(raw).strip());p=Z(raw)
 for t in p:
  add(t);P=l(t).strip();add(P)
  if P!=t:add(P)
 add(l(raw).strip())
 for aF in V(raw):
  add(aF);add(normalize_symbol(aF))
 w.sort(key=lambda s:(len(s),s))
 if raw in w:w.remove(raw)
 return[raw,*w]
def A(text):
 C=[];x=[ln.strip()for ln in(text or '').splitlines()if ln.strip()];D=- 1;R=[]
 for(i,ln)in enumerate(x):
  if ln.startswith('|')and 'code' in ln.lower()and('name' in ln.lower()):
   R=[c.strip().lower()for c in ln.strip('|').split('|')];D=i;break
 if D<0 or not R:return C
 for ln in x[D+1:]:
  if not ln.startswith('|'):continue
  if d(ln):continue
  Q=split_table_row(ln)
  if len(Q)<2:continue
  data={R[j]:Q[j]for j in range(min(len(R),len(Q)))};code=normalize_symbol(data.get('code')or '');name=data.get('name')or ''
  if not code:continue
  C.append({'code':code,'name':name,'type':data.get('type')or 'stock'})
 return C
def J(query,*,limit=8):
 at=query_variants(query);L=[];T=set()
 for q in at[:8]:
  (code,text)=run_westock(['search',q,'--limit',str(limit)],timeout=30)
  if code!=0 and '未找到' not in text:continue
  for ab in A(text):
   c=ab['code']
   if c in T:continue
   T.add(c);L.append({'code':c,'name':ab.get('name')or c,'market':B(c),'source':'westock-data','match_query':q})
   if len(L)>=limit:return L
 return L
def B(code):
 al=code.lower()
 if al.startswith('us'):return 'us'
 if al.startswith('hk'):return 'hk'
 if al.startswith(('sh','sz','bj')):return 'cn'
 return ''
def N(text):
 O=[];x=(text or '').splitlines();i=0
 while i<len(x):
  ln=x[i].strip()
  if ln.startswith('|')and(not d(ln)):
   R=split_table_row(ln)
   if i+1<len(x)and d(x[i+1]):
    C=[];j=i+2
    while j<len(x)and x[j].strip().startswith('|'):
     aq=x[j].strip()
     if d(aq):
      j+=1;continue
     Q=split_table_row(aq)
     if any(Q):C.append(Q)
     j+=1
    O.append((R,C));i=j;continue
  i+=1
 return O
def _to_float(a):
 if a is None:return None
 if isinstance(a,(int,float)):return float(a)
 s=str(a).strip().replace(',','').replace('%','')
 if not s or s in{'-','—','N/A','null'}:return None
 try:
  return float(s)
 except ValueError:
  return None
def fetch_rating_pack(code):
 Y=normalize_symbol(code)
 if not Y:return None
 (rc,text)=run_westock(['rating',Y],timeout=45)
 if rc!=0 and 'Price target' not in text:return None
 O=N(text)
 if not O:return None
 g=[];y={};E=None
 for(R,C)in O:
  o=[c.lower()for c in R]
  if 'ratingbuycnt' in o or 'forecastinstitutions' in o:
   if not C:continue
   ab=C[0];data={o[k]:ab[k]if k<len(ab)else '' for k in range(len(o))};aN=int(_to_float(data.get('ratingbuycnt'))or 0);aO=int(_to_float(data.get('ratinginccnt'))or 0);aK=int(_to_float(data.get('ratingholdcnt'))or 0);aP=int(_to_float(data.get('ratingdeccnt'))or 0);aL=int(_to_float(data.get('ratingsellcnt'))or 0);E=_to_float(data.get('currentprice'));g.append({'period':'latest','strongBuy':aN,'buy':aO,'hold':aK,'sell':aP,'strongSell':aL});continue
  if 'buyincratio' in o and 'month' in o:
   for ab in C:
    data={o[k]:ab[k]if k<len(ab)else '' for k in range(len(o))};an=str(data.get('month')or '').strip()
    if not an or an=='latest':continue
    ai=int(_to_float(data.get('totalcnt'))or 0)
    if ai<=0:continue
    bi=(_to_float(data.get('buyincratio'))or 0)/100.0;ho=(_to_float(data.get('holdratio'))or 0)/100.0;ac=int(round(ai*bi));ao=int(round(ai*ho));ae=max(0,ai-ac-ao);U=int(round(ac*0.4));aB=ac-U;ap=int(round(ae*0.7));aj=ae-ap;g.append({'period':an,'strongBuy':U,'buy':aB,'hold':ao,'sell':ap,'strongSell':aj})
   continue
  if 'targetpriceavg' in o and 'closeprice' in o:
   z=[]
   for ab in C:
    data={o[k]:ab[k]if k<len(ab)else '' for k in range(len(o))};t=_to_float(data.get('targetpriceavg'))
    if t is not None:z.append(t)
   if z:y={'targetMean':z[- 1],'targetMedian':z[- 1],'targetHigh':max(z),'targetLow':min(z),'numberAnalysts':0,'lastUpdated':''}
 if not g and(not y):return None
 g.sort(key=lambda r:str(r.get('period')));aG={'code':Y,'rating_trends':g,'price_target_consensus':y,'grade_changes':[],'sources':[{'title':f'westock-data rating {Y}','url':'','retrieved_at':''}],'meta':{'current_price':E,'source':'westock-data'}};return aG
def enrich_resolve_payload(aw,query):
 w=dict(aw);F=w.get('candidates')
 if isinstance(F,list)and F:
  if not w.get('preferred_code'):
   am=F[0]
   if isinstance(am,dict)and am.get('code'):w['preferred_code']=normalize_symbol(str(am['code']))
  return w
 f=J(query,limit=8)
 if not f:
  for v in query_variants(query):
   aA=normalize_symbol(v)
   if is_standard_symbol(aA):
    f=[{'code':aA,'name':v,'market':B(aA),'source':'ticker_normalize','match_query':v}];break
 if not f:return w
 w['candidates']=[{'code':h['code'],'name':h.get('name')or h['code'],'market':h.get('market')or B(h['code']),'source':h.get('source')or 'westock-data'}for h in f];w['preferred_code']=f[0]['code'];w['enrichment']='westock-data';raw=w.get('raw')
 if not isinstance(raw,dict):raw={}
 raw=dict(raw);raw['westock_fallback']=f;w['raw']=raw;return w
