import argparse;import copy;import json;import sys;from datetime import datetime;from pathlib import Path;from typing import Any,Dict,List,Optional,Tuple;sys.path.insert(0,str(Path(__file__).resolve().parent));import client_common;from markdown_document import MarkdownDocument,_fence_marker;from symbol_utils import normalize_westock_symbol;from text_scanner import iter_http_url_spans,iter_http_urls,iter_json_objects,parse_inline_sources,parse_labeled_values,strip_parenthetical_label
def a8(text):
 if isinstance(text,(dict,list)):return text
 if not isinstance(text,str):return None
 raw=text.strip()
 if not raw:return None
 try:
  return json.loads(raw)
 except Exception:
  return None
def aT(B):
 aY=B
 for _ in range(3):
  eb=a8(aY)
  if eb is None:break
  aY=eb
 return aY
def c5(B):
 af=aT(B)
 if isinstance(af,list):return[f for f in af if isinstance(f,dict)]
 if not isinstance(B,str):return[]
 return list(iter_json_objects(B))
def _load_traces(cd):
 y=[]
 if not cd.is_file():return y
 for aF in cd.read_text(encoding='utf-8').splitlines():
  aF=aF.strip()
  if not aF:continue
  ec=a8(aF)
  if isinstance(ec,dict):y.append(ec)
 return y
def ag(F,tool):
 for G in reversed(F):
  if G.get('tool')!=tool:continue
  af=aT(G.get('result'))
  if af is not None:return af
 return None
def _to_float(B):
 if B is None:return None
 if isinstance(B,(int,float)):return float(B)
 s=str(B).strip()
 if not s:return None
 s=s.replace(',','')
 try:
  return float(s)
 except Exception:
  return None
def contract_decimals(l):
 B=l.get('decimals');return 2 if B is None else int(B)
def bH(cs):
 data=aT(cs)
 if isinstance(data,dict):
  if isinstance(data.get('result'),list)and data['result']:
   bP=data['result'][0]
   if isinstance(bP,dict):return bP
  if isinstance(data.get('data'),list)and data['data']:
   bP=data['data'][0]
   if isinstance(bP,dict):return bP
  dj=data.get('data')
  if isinstance(dj,dict):
   for cM in('盘中','盘前','盘后','夜盘'):
    do=dj.get(cM)
    if not isinstance(do,dict):continue
    bP=next((f for f in do.values()if isinstance(f,dict)),None)
    if bP:return bP
 if isinstance(data,list)and data and isinstance(data[0],dict):return data[0]
 return None
def bV(f,key,c6='power'):
 raw=_to_float(f.get(key))
 if raw is None:return None
 d1=int(_to_float(f.get(c6))or 0);return raw/float(10**d1)
def bR(B,de=2):
 if B is None:return 'n/a'
 bL=z(B,de)
 if bL is None:return 'n/a'
 text=f'{bL:.{de}f}'.rstrip('0').rstrip('.');return text if text else '0'
def a7(code):
 c=str(code or '').strip().lower()
 if c.startswith('us'):return 'USD'
 if c.startswith('hk'):return 'HKD'
 if c.startswith(('sh','sz','bj')):return 'CNY'
 return ''
def W(bM):
 y=[]
 for aF in bM.splitlines():
  aF=aF.strip()
  if not aF.startswith('|'):continue
  if '---' in aF:continue
  parts=[dO.strip()for dO in aF.strip('|').split('|')]
  if len(parts)<7:continue
  if parts[0]=='code':continue
  G={'trade_date':parts[1],'open':_to_float(parts[2]),'close':_to_float(parts[3]),'high':_to_float(parts[4]),'low':_to_float(parts[5]),'volume':_to_float(parts[6])}
  if G['open']is None or G['close']is None or G['high']is None or(G['low']is None):continue
  y.append(G)
 return y
def ab(bM):
 y=[]
 for aF in bM.splitlines():
  aF=aF.strip()
  if not aF.startswith('|'):continue
  if '---' in aF:continue
  parts=[dO.strip()for dO in aF.strip('|').split('|')]
  if len(parts)<6:continue
  if parts[0].lower()in{'date','日期'}:continue
  G={'trade_date':parts[0],'open':_to_float(parts[1]),'close':_to_float(parts[2]),'high':_to_float(parts[3]),'low':_to_float(parts[4]),'volume':_to_float(parts[5])}
  if G['open']is None or G['close']is None or G['high']is None or(G['low']is None):continue
  y.append(G)
 return y
def V(B):
 text=str(B or '').strip().split(' ')[0]
 if not text:return None
 for ei in('%Y-%m-%d','%Y/%m/%d'):
  try:
   return datetime.strptime(text,ei)
  except ValueError:
   continue
 return None
def Q(y):
 c7=[]
 for G in y:
  dt=V(G.get('trade_date'))
  if dt is None:continue
  c7.append((dt,G))
 c7.sort(key=lambda item:f[0]);return[G for(_,G)in c7]
def aK(y):
 b7=[]
 for G in y:
  dt=V(G.get('trade_date'))
  if dt is not None:b7.append(dt)
 if len(b7)<2:return 0
 b7.sort();return max(((b7[i]-b7[i- 1]).days for i in range(1,len(b7))))
def bW(code):
 c=str(code or '').strip()
 if not c:return ''
 return normalize_westock_symbol(c)or c
def a1(code,*,limit=60):
 import westock_bridge;df=westock_bridge.normalize_symbol(code)or bW(code)
 if not df:return[]
 (rc,text)=westock_bridge.run_westock(['kline',df,'--period','day','--limit',str(limit)],timeout=45)
 if rc!=0 and '数据为空' in text:return[]
 y=Q(ab(text));return y
def au(charts_dir):
 if charts_dir is None:return[]
 path=charts_dir/'host_price_technical.json'
 if not path.is_file():return[]
 try:
  data=json.loads(path.read_text(encoding='utf-8'))
 except(OSError,json.JSONDecodeError):
  return[]
 if isinstance(data,list):bk=data
 elif isinstance(data,dict):
  bk=data.get('rows')or data.get('daily_series')or[]
  if isinstance(bk,str):
   af=W(bk)
   if not af:af=ab(bk)
   return Q(af)
 else:return[]
 y=[]
 for f in bk:
  if not isinstance(f,dict):continue
  G={'trade_date':str(f.get('trade_date')or f.get('date')or '').split(' ')[0],'open':_to_float(f.get('open')),'close':_to_float(f.get('close')if f.get('close')is not None else f.get('last')),'high':_to_float(f.get('high')),'low':_to_float(f.get('low')),'volume':_to_float(f.get('volume'))}
  if G['open']is None or G['close']is None or G['high']is None or(G['low']is None):continue
  y.append(G)
 return Q(y)
def bX(ak,L):
 if len(L)<5:return False
 if len(ak)<5:return True
 ct=aK(ak);cO=aK(L)
 if ct>5 and cO<ct:return True
 bw={dt.date()for dt in(V(r.get('trade_date'))for r in ak)if dt is not None};ce={dt.date()for dt in(V(r.get('trade_date'))for r in L)if dt is not None}
 if not bw or not ce:return False
 (start,end)=(min(bw),max(bw));dP=sum((1 for d in ce if start<=d<=end and d not in bw));return dP>=3 and cO<=ct
def aC(y):
 y=Q(y)[- 30:]
 if len(y)<5:return None
 dB=[G['high']for G in y if G.get('high')is not None];dT=[G['low']for G in y if G.get('low')is not None];bx=[G['close']for G in y if G.get('close')is not None]
 if not dB or not dT or(not bx):return None
 return{'rows':y,'latest_close':bx[- 1],'period_high':max(dB),'period_low':min(dT),'range_start':str(y[0]['trade_date']).split(' ')[0],'range_end':str(y[- 1]['trade_date']).split(' ')[0]}
def ap(F):
 data=ag(F,'market_snapshot')
 if not isinstance(data,dict):return None
 f=bH(data.get('quote'))
 if not isinstance(f,dict):return None
 by=_to_float(f.get('涨跌幅'))
 if by is None:
  cm=_to_float(f.get('chgPct'));by=cm/100.0 if cm is not None else None
 def ai(cX,cY):
  dk=_to_float(f.get(cY));return dk if dk is not None else bV(f,cX)
 aZ=ai('price','Last');a_=ai('pClose','Previous close');cv=by
 if cv is None and aZ is not None and(a_ not in(None,0)):cv=(aZ-a_)/a_*100.0
 w={'code':str(data.get('code')or '').strip(),'name':str(f.get('name')or f.get('名称')or '').strip(),'latest':aZ,'open':ai('open','Open'),'high':ai('high','High'),'low':ai('low','Low'),'prev_close':a_,'chg_pct':cv}
 if not any((w[k]is not None for k in('latest','open','high','low','prev_close','chg_pct'))):return None
 return w
def aq(F,charts_dir=None):
 data=ag(F,'price_technical');ak=[];code=''
 if isinstance(data,dict):
  cZ=str(data.get('daily_series')or '');ak=Q(W(cZ));code=str(data.get('code')or '').strip()
 if not code:code=am(F)
 if not code:code='Name'
 L=au(charts_dir)
 if len(L)<5 and code!='Name':
  L=a1(code,limit=60)
  if charts_dir is not None and len(L)>=5:
   try:
    charts_dir.mkdir(parents=True,exist_ok=True);(charts_dir/'host_price_technical.json').write_text(json.dumps({'code':code,'rows':L},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
   except OSError:
    pass
 y=L if bX(ak,L)else ak
 if len(y)<5 and L:y=L
 bz=aC(y)
 if bz is None and ak:bz=aC(ak)
 if bz is None:return None
 return{'code':code,**bz}
def bp(text,cw):
 section=MarkdownDocument(text).find_section(2,cw)
 if section is None:return None
 start=section.body_start
 if text[max(0,start- 2):start]=='\r\n':start-=2
 elif start>0 and text[start- 1]=='\n':start-=1
 return(text[start:section.end],start,section.end)
aD={'revenue_mix':('host_revenue_mix.json','Revenue mix'),'revenue_geo':('host_revenue_geo.json','Geographic mix')}
def M(cx,*,b8=True):
 aj=[];cf=set()
 if not isinstance(cx,list):return[]
 for p in cx:
  if not isinstance(p,dict):continue
  name=str(p.get('name')or '').strip()
  if not name or name in cf or len(name)>32:continue
  if any((ch.isdigit()for ch in name))and name.replace('.','').replace('%','').isdigit():continue
  if '%' in name or '％' in name:continue
  da={'占比','比例','收入','营收','合计','总计','分部','地区','产品','业务'}
  if name in da:continue
  rv=z(p.get('value'),2)
  if rv is None or rv<=0 or rv>100:continue
  cf.add(name);aj.append({'name':name,'value':float(rv)})
 if len(aj)<K:return[]
 cy=z(sum((p['value']for p in aj)),2)or 0.0
 if cy>120:return[]
 if abs(cy- 100.0)<=0.009:
  ed=aj[:- 1];dw=z(sum((p['value']for p in ed)),2)or 0.0;dL=z(100.0-dw,2)
  if dL is None or dL<=0:return[]
  aj[- 1]={'name':aj[- 1]['name'],'value':float(dL)};return aj
 if b8 and cy<100.0:
  dl=z(100.0-cy,2)
  if dl is not None and dl>0:
   db=any((p['name']in('其他','其余','其它','Other')for p in aj))
   if not db and dl<=15.0:aj.append({'name':'Other','value':float(dl)})
  return aj
 if cy>100.0:return[]
 return aj
def av(charts_dir,slug):
 dU=aD.get(slug)
 if not dU or charts_dir is None:return[]
 path=Path(charts_dir)/dU[0]
 if not path.is_file():return[]
 try:
  data=json.loads(path.read_text(encoding='utf-8'))
 except(OSError,json.JSONDecodeError):
  return[]
 if isinstance(data,list):raw=data
 elif isinstance(data,dict):raw=data.get('parts')
 else:return[]
 return M(raw)
def aw(*,slug,subsection,parts):
 parts=M(parts);ok=len(parts)>=K;hint=f'Locked pie ({subsection})';return{'available':ok,'slug':slug,'section':'Fundamentals','subsection':subsection,'hint':hint,'suggested_charts':[{'slug':slug,'hint':hint,'section':'Fundamentals','subsection':subsection}]if ok else[],'data':{'parts':parts,'unit':'%','extract_mode':'llm_host_json'}if ok else None}
def aL(charts_dir):
 O=[]
 for(slug,(el,subsection))in aD.items():
  parts=av(charts_dir,slug);O.append(aw(slug=slug,subsection=subsection,parts=parts))
 return O
def cU(raw):
 if not isinstance(raw,list):return[]
 O=[];cf=set()
 for f in raw:
  if isinstance(f,str):(name,dp)=(f.strip(),True)
  elif isinstance(f,dict):
   name=str(f.get('name')or '').strip();dZ=f.get('higherIsBetter');dp=True if dZ is None else bool(dZ)
  else:continue
  if not name or len(name)>16 or name in cf:continue
  cf.add(name);O.append({'name':name,'higherIsBetter':dp})
 return O
def aa(w):
 if not isinstance(w,dict):return None
 cg=cU(w.get('indicators'));y=w.get('companies')
 if not cg or not isinstance(y,list):return None
 aH=[]
 for f in y[:bK]:
  if not isinstance(f,dict):continue
  name=str(f.get('name')or '').strip();values=f.get('values')
  if not name or len(name)>16 or(not isinstance(values,(list,tuple)))or(len(values)<len(cg)):continue
  cP=[_to_float(v)for v in list(values)[:len(cg)]]
  if any((n is None for n in cP)):continue
  aH.append({'name':name,'raw':[float(n)for n in cP if n is not None]})
 if len(aH)<J:return None
 aG=[i for(i,ek)in enumerate(cg)if max((c['raw'][i]for c in aH))-min((c['raw'][i]for c in aH))>1e-12]
 if len(aG)<Y:return None
 cq=[]
 for c in aH:
  a5=[]
  for i in aG:
   eh=[x['raw'][i]for x in aH];(lo,hi)=(min(eh),max(eh));d5=(c['raw'][i]-lo)/(hi-lo)*Z
   if not cg[i]['higherIsBetter']:d5=Z-d5
   a5.append(z(d5,1)or 0.0)
  cq.append({'name':c['name'],'values':a5})
 d2={c['name']for c in cq};b2=str(w.get('subject')or '').strip();return{'subject':b2 if b2 in d2 else cq[0]['name'],'categories':[cg[i]['name']for i in aG],'companies':cq}
def bD(charts_dir):
 if charts_dir is None:return None
 path=Path(charts_dir)/aE
 if not path.is_file():return None
 try:
  w=json.loads(path.read_text(encoding='utf-8'))
 except(OSError,json.JSONDecodeError):
  return None
 if not isinstance(w,dict)or aa(w)is None:return None
 return w
def bq(w):
 ok=bool(aa(w));hint='Locked peer radar';return{'available':ok,'slug':q,'section':'Valuation','subsection':'Peer comparison','hint':hint,'suggested_charts':[{'slug':q,'hint':hint,'section':'Valuation','subsection':'Peer comparison'}]if ok else[],'data':w if ok else None}
def aU(parts,h3):
 cV=[f"- {p['name']}: {bR(p['value'], 2)}%" for p in parts];return f'### {h3}\n\n'+'\n'.join(cV)+'\n\n(Source: company filings)\n'
def aV(text,parts=None):
 parts=M(parts or[])
 if not(text or '').strip()or len(parts)<K:return text
 a4=aU(parts,'Revenue mix')
 if not a4.endswith('\n'):a4+='\n'
 a0=MarkdownDocument(text);bA=a0.find_section(2,'Fundamentals')
 if bA is None:return text.rstrip()+'\n\n## Fundamentals\n\n'+a4+'\n'
 cz=next((section for section in a0.sections(3)if section.heading.title.strip()=='Revenue mix' and bA.body_start<=section.start<bA.end),None)
 if cz is not None:return text[:cz.start]+a4+text[cz.end:]
 b9=next((section for section in a0.sections(3)if section.heading.title.strip()=='Business model' and bA.body_start<=section.start<bA.end),None)
 if b9 is not None:return text[:b9.end]+'\n'+a4+text[b9.end:]
 return text[:bA.body_start]+'\n'+a4+text[bA.body_start:]
def bg(ai,ba=None):
 cA=ai.get('rows');y=cA if isinstance(cA,list)else[];bx=[_to_float(r.get('close'))for r in y if isinstance(r,dict)and _to_float(r.get('close'))is not None];aZ=_to_float(ai.get('latest_close'))
 if aZ is None and bx:aZ=bx[- 1]
 aS=None
 if isinstance(ba,dict):aS=_to_float(ba.get('prev_close'))
 if aS is None and len(bx)>=2:aS=bx[- 2]
 dC=None
 if isinstance(ba,dict):dC=_to_float(ba.get('chg_pct'))
 if dC is None and aZ is not None and(aS not in(None,0)):dC=(aZ-aS)/aS*100.0
 dq=f'{bR(dC, 2)}%' if dC is not None else 'n/a';return{'prev_close':bR(aS),'chg_pct':dq,'range':f"{ai.get('range_start')} ~ {ai.get('range_end')}",'latest_close':bR(aZ)}
def ar(text,ai,ba=None):
 if not text or not isinstance(ai,dict):return text
 b3=bg(ai,ba);a4=f"### Relative strength\n\n- Previous close: {b3['prev_close']}\n- Day change: {b3['chg_pct']}\n- Sample window: {b3['range']}\n- Latest close: {b3['latest_close']}\n\n(Source: market data)\n";a0=MarkdownDocument(text);b_=a0.find_section(3,'Relative strength')
 if b_ is not None:return text[:b_.start]+a4+text[b_.end:]
 section=bp(text,'Valuation')
 if not section:
  bN=a0.find_section(2,'In-depth analysis')
  if bN is None:return text.rstrip()+'\n\n## Valuation\n\n'+a4+'\n'
  cF=bN.body_start;return text[:cF]+'\n## Valuation\n\n'+a4+text[cF:]
 (body,start,end)=section;dr=body.rstrip()+'\n\n'+a4+'\n';return text[:start]+dr+text[end:]
MAX_SUGGESTED_CHARTS=5;MANDATORY_KLINE_SLUG='price_technical';MANDATORY_PRODUCT_PIE_SLUG='revenue_mix';q='peer_radar';aE='host_peer_radar.json';Y=3;J=2;bK=6;Z=100.0;an=('#3370ff','#00b42a','#ff7d00','#f53f3f','#722ed1','#0fc6c2');MANDATORY_PIE_SLUGS=(MANDATORY_PRODUCT_PIE_SLUG,'revenue_geo');K=2;bv=(MANDATORY_KLINE_SLUG,q)+MANDATORY_PIE_SLUGS;ae=(MANDATORY_KLINE_SLUG,MANDATORY_PRODUCT_PIE_SLUG,q);CHART_PRIORITY=('price_technical','revenue_mix','peer_radar','revenue_geo');bG=frozenset({'price_target','institutional_views','market_snapshot','market_prev_close_compare','price_volume','market_change_gauge'});aX=frozenset({MANDATORY_KLINE_SLUG,'revenue_mix','revenue_geo',q});CHART_DATA_ANCHOR={'price_technical':('Valuation','Relative strength'),'revenue_mix':('Fundamentals','Revenue mix'),'revenue_geo':('Fundamentals','Geographic mix'),'peer_radar':('Valuation','Peer comparison')}
def bZ(w):
 if not w:return{'available':False,'slug':'price_technical','section':'Valuation','data':None}
 y=[{'trade_date':str(r.get('trade_date')or '').split(' ')[0],'open':r.get('open'),'close':r.get('close'),'high':r.get('high'),'low':r.get('low'),'volume':r.get('volume')}for r in w.get('rows')or[]];return{'available':True,'slug':'price_technical','section':'Valuation','hint':'Daily OHLC candlestick','suggested_charts':[{'slug':'price_technical','hint':'candlestick'}],'data':{**w,'rows':y}}
def P(values,*,min_points=2):
 cP=[]
 for raw in values:
  v=_to_float(raw)
  if v is None or v!=v:continue
  cP.append(float(v))
 if len(cP)<min_points:return False
 return any((abs(v)>1e-12 for v in cP))
def cN(w):
 a5=[_to_float(w.get('latest')),_to_float(w.get('targetMean')),_to_float(w.get('targetMedian')),_to_float(w.get('targetHigh')),_to_float(w.get('targetLow'))];return sum((1 for v in a5 if v is not None and v==v and(v>0)))>=2
def bY(report_text):return{title.strip()for title in MarkdownDocument(report_text or '').heading_titles(3)if title.strip()}
def aA(charts,g,report_text):
 d9=set(ae);d_=bY(report_text)
 if not d_:return g
 aG=[]
 for slug in g:
  bd=CHART_DATA_ANCHOR.get(slug)
  if not bd:continue
  (d7,subsection)=bd
  if subsection and subsection not in d_ and(slug not in d9):continue
  aG.append(slug)
 for slug in ae:
  if slug in g and slug not in aG:aG.insert(0 if slug==MANDATORY_KLINE_SLUG else min(1,len(aG)),slug)
 bl=set(aG)
 for f in charts:
  f['suggested_charts']=[sc for sc in f.get('suggested_charts')or[]if isinstance(sc,dict)and str(sc.get('slug')or '')in bl]
 return aG
def bI(charts):
 aO={}
 for f in charts:
  for sc in f.get('suggested_charts')or[]:
   if not isinstance(sc,dict)or not sc.get('slug'):continue
   slug=str(sc['slug'])
   if slug in bG:continue
   bd=CHART_DATA_ANCHOR.get(slug)
   if not bd:continue
   (section,subsection)=bd;aO[slug]=(section,subsection,sc)
 ax=[]
 for slug in bv:
  if slug in aO and slug not in ax:ax.append(slug)
 for slug in CHART_PRIORITY:
  if slug in aO and slug not in ax:ax.append(slug)
 for slug in aO:
  if slug not in ax:ax.append(slug)
 bS=[];bb=set()
 for slug in ax:
  if len(bS)>=MAX_SUGGESTED_CHARTS:break
  (section,subsection,em)=aO[slug]
  if not subsection or subsection in bb:continue
  bS.append(slug);bb.add(subsection)
  for f in charts:
   for sc in f.get('suggested_charts')or[]:
    if isinstance(sc,dict)and str(sc.get('slug')or '')==slug:
     sc['section']=section;sc['subsection']=subsection;f['section']=section;f['subsection']=subsection
 cK=set(bS)
 for f in charts:
  aG=[sc for sc in f.get('suggested_charts')or[]if isinstance(sc,dict)and str(sc.get('slug')or '')in cK];f['suggested_charts']=aG
 return bS
def ac(charts,g):
 aG=[slug for slug in g if slug in aX];bl=set(aG)
 for f in charts:
  f['suggested_charts']=[sc for sc in f.get('suggested_charts')or[]if isinstance(sc,dict)and str(sc.get('slug')or '')in bl]
 return aG
def a9(F,charts_dir):
 dg=list(F);dD=(('host_fundamentals_pack.json','fundamentals_pack'),('host_institutional_views.json','institutional_views'))
 for(dx,tool)in dD:
  path=charts_dir/dx
  if not path.is_file():continue
  try:
   data=json.loads(path.read_text(encoding='utf-8'))
  except(OSError,json.JSONDecodeError):
   continue
  if not isinstance(data,dict)or not data:continue
  ay={k:v for(k,v)in data.items()if k not in{'status','instruction','required_host_tools','write_file','schema','rules','data_status'}}
  if not ay:continue
  dg.append({'tool':tool,'arguments':{},'result':ay,'source':'host_pack'})
 return dg
def am(F):
 for tool in('price_technical','market_snapshot','deep_profile','resolve_symbol'):
  data=ag(F,tool)
  if not isinstance(data,dict):continue
  for key in('code','preferred_code','stock_code'):
   raw=data.get(key)
   if raw:return str(raw).strip()
  cG=data.get('candidates')
  if isinstance(cG,list)and cG and isinstance(cG[0],dict)and cG[0].get('code'):return str(cG[0]['code']).strip()
 return ''
def aB(ay):
 dh=ay.get('rating_trends')
 if isinstance(dh,list)and len(dh)>=1:return True
 di=ay.get('price_target_consensus')
 if isinstance(di,dict)and any((_to_float(di.get(k))is not None for k in('targetMean','targetMedian','targetHigh','targetLow'))):return True
 return False
def aM(F,charts_dir):
 import westock_bridge;charts_dir.mkdir(parents=True,exist_ok=True);code=am(F)
 if not code:
  for name in('host_institutional_views.json','host_fundamentals_pack.json'):
   path=charts_dir/name
   if not path.is_file():continue
   try:
    data=json.loads(path.read_text(encoding='utf-8'))
   except(OSError,json.JSONDecodeError):
    continue
   if isinstance(data,dict)and data.get('code'):
    code=str(data['code']).strip();break
 if not code:return F
 a6=charts_dir/'host_institutional_views.json';cB=True
 if a6.is_file():
  try:
   cc=json.loads(a6.read_text(encoding='utf-8'))
  except(OSError,json.JSONDecodeError):
   cc=None
  if isinstance(cc,dict)and aB(cc):cB=False
 if cB:
  ay=westock_bridge.fetch_rating_pack(code)
  if ay:
   if a6.is_file():
    try:
     aS=json.loads(a6.read_text(encoding='utf-8'))
    except(OSError,json.JSONDecodeError):
     aS=None
    if isinstance(aS,dict):
     if aS.get('sources')and(not ay.get('sources')):ay['sources']=aS['sources']
     if aS.get('grade_changes'):ay['grade_changes']=aS['grade_changes']
   a6.write_text(json.dumps(ay,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 cC=charts_dir/'host_fundamentals_pack.json'
 if cC.is_file():
  try:
   dN=json.loads(cC.read_text(encoding='utf-8'))
  except(OSError,json.JSONDecodeError):
   dN=None
  if isinstance(dN,dict)and(not bQ(dN)):pass
 return a9(F,charts_dir)
def bJ(F,charts_dir=None,report_text=''):
 if charts_dir is not None:F=aM(F,charts_dir)
 ba=ap(F);ai=aq(F,charts_dir=charts_dir)
 if ai is None:raise ValueError('Missing candlestick data (price_technical): rerun Phase B price_technical or write host_price_technical.json.')
 report_text=ar(report_text or '',ai,ba);cD=av(charts_dir,MANDATORY_PRODUCT_PIE_SLUG)
 if len(cD)<K:raise ValueError('Missing product revenue pie data: write host_revenue_mix.json (parts>=2).')
 report_text=aV(report_text or '',cD);ci=bD(charts_dir)
 if ci is None:raise ValueError(f'Missing Peer comparison radar data: write {aE} (indicators >={Y}, companies >={J}).')
 c2=aL(charts_dir);charts=[bZ(ai),bq(ci),*c2]
 for f in charts:
  if not f.get('available'):f.setdefault('suggested_charts',[])
 c8=[c['slug']for c in charts if c.get('available')];g=bI(charts);g=aA(charts,g,report_text or '');g=ac(charts,g);C=bt(charts,g);g=at(charts,g,C);g=ac(charts,g);C={k:v for(k,v)in C.items()if k in set(g)}
 for d3 in(MANDATORY_KLINE_SLUG,MANDATORY_PRODUCT_PIE_SLUG,q):
  if d3 not in g or d3 not in C:raise ValueError(f'No drawable {d3}: check host data and dump again.')
 c9=[s for s in g if s in MANDATORY_PIE_SLUGS];return{'version':12,'source':'traces + host json','max_charts':MAX_SUGGESTED_CHARTS,'instruction':'Run --render-all then --assemble-html.','available_slugs':c8,'suggested_chart_slugs':g,'mandatory_kline_slug':MANDATORY_KLINE_SLUG,'mandatory_product_pie_slug':MANDATORY_PRODUCT_PIE_SLUG,'mandatory_peer_radar_slug':q,'mandatory_pie_slugs':c9,'report_text':report_text,'contracts':C,'charts':charts}
cp=('Adding or removing points is forbidden','Reordering categories is forbidden','Second-round aggregation or summarizing is forbidden','Changing the unit or converting by yourself is forbidden','series values must match the contract')
def z(B,t=2):
 n=_to_float(B)
 if n is None or n!=n:return None
 if t<=0:return float(int(round(n)))
 return float(f'{float(n):.{t}f}')
def br(B,t=2):
 bL=z(B,t)
 if bL is None:return '0'
 text=f'{bL:.{t}f}'.rstrip('0').rstrip('.');return text if text and text!='-' else '0'
def bE(text):
 cj=[False]*len(text)
 for dV in iter_http_url_spans(text):
  for i in range(dV.start,min(dV.end,len(cj))):
   cj[i]=True
 ds=0;bc=None;bf=0
 while ds<len(text):
  nl=text.find('\n',ds);cR=len(text)if nl<0 else nl;aF=text[ds:cR];ca=cR if nl<0 else nl+1;bU=_fence_marker(aF)
  if bc is not None:
   for i in range(ds,ca):
    cj[i]=True
   if bU and bU[0]==bc and(bU[1]>=bf)and bU[2]:
    bc=None;bf=0
  elif bU:
   (bc,bf,_)=bU
   for i in range(ds,ca):
    cj[i]=True
  ds=ca
 return cj
def N(ch):
 if not ch:return True
 return not(ch.isalnum()or ch=='_' or ch=='.')
def canonicalize_floats_in_text(text,t=2):
 if not text or t<0:return text
 cj=bE(text);O=[];i=0;n=len(text)
 while i<n:
  if cj[i]:
   O.append(text[i]);i+=1;continue
  ch=text[i];bo=- 1
  if ch=='-' and i+1<n and text[i+1].isdigit():
   aS=text[i- 1]if i>0 else ''
   if N(aS):
    bo=i;i+=1;ch=text[i]
  if ch.isdigit()and(bo>=0 or N(text[i- 1]if i>0 else '')):
   start=bo if bo>=0 else i;j=i
   while j<n and text[j].isdigit():
    j+=1
   if j<n and text[j]=='.' and(j+1<n)and text[j+1].isdigit():
    j+=1
    while j<n and text[j].isdigit():
     j+=1
    if N(text[j]if j<n else '')and(not any((cj[k]for k in range(start,j)))):
     raw=text[start:j]
     try:
      O.append(br(float(raw),t))
     except ValueError:
      O.append(raw)
     i=j;continue
   O.append(text[start:j]if bo>=0 else text[i:j]);i=j;continue
  if bo>=0:
   O.append('-');continue
  O.append(ch);i+=1
 return ''.join(O)
def co(charts,slug):
 for f in charts:
  if isinstance(f,dict)and str(f.get('slug')or '')==slug:return f
 return None
def bh(slug,ck):
 bd=CHART_DATA_ANCHOR.get(slug)or('','');(section,subsection)=(str(bd[0]or ''),str(bd[1]or ''));title=subsection or slug;u=(ck or '').strip()
 if slug in MANDATORY_PIE_SLUGS:bn=''
 elif slug==MANDATORY_KLINE_SLUG:bn='Daily OHLC'+(f' · {u}' if u else '')
 else:bn=u
 return{'section':section,'subsection':subsection,'title':title,'caption':bn}
def aQ(slug,aR,ck,t):
 O={'slug':slug,'type':aR,'unit':ck,'decimals':t,'categories':[],'series':[],'rules':list(cp)};O.update(bh(slug,ck));return O
def a2(data):
 y=data.get('rows')or[]
 if not isinstance(y,list)or len(y)<5:return None
 t=2;bm=[];dW=[]
 for G in y:
  if not isinstance(G,dict):continue
  d=str(G.get('trade_date')or '').strip();o=z(G.get('open'),t);c=z(G.get('close'),t);h=z(G.get('high'),t);dQ=z(G.get('low'),t)
  if not d or o is None or c is None or(h is None)or(dQ is None):continue
  bm.append(d);dW.append([o,c,dQ,h])
 if len(bm)<5:return None
 ck=a7(str(data.get('code')or ''))or 'CNY';O=aQ('price_technical','candlestick',ck,t);O['categories']=bm;O['ohlc']=dW;O['series']=[{'name':'Price','kind':'ohlc'}];return O
def bs(l):
 if not isinstance(l,dict):return False
 aR=str(l.get('type')or '')
 if aR=='radar':
  bm=l.get('categories')or[];dm=l.get('series')or[]
  if len(bm)<Y or len(dm)<J:return False
  values=[]
  for s in dm:
   if isinstance(s,dict):values.extend(s.get('values')or[])
  return P(values,min_points=1)
 if aR=='candlestick':return len(l.get('ohlc')or[])>=5
 if aR=='pie':
  a5=((l.get('series')or[{}])[0]or{}).get('values')or[];return P(a5,min_points=K)
 bm=l.get('categories')or[]
 if not isinstance(bm,list)or not bm:return False
 values=[]
 for s in l.get('series')or[]:
  if isinstance(s,dict):values.extend(s.get('values')or[])
 return P(values,min_points=1)
def at(charts,g,C):
 aG=[s for s in g if s in C and bs(C[s])];bl=set(aG)
 for f in charts:
  f['suggested_charts']=[sc for sc in f.get('suggested_charts')or[]if isinstance(sc,dict)and str(sc.get('slug')or '')in bl]
 return aG
def aN(slug,data):
 parts=M(data.get('parts')if isinstance(data.get('parts'),list)else[])
 if len(parts)<K:return None
 a5=[float(p['value'])for p in parts]
 if abs((z(sum(a5),2)or 0.0)- 100.0)>0.009:return None
 O=aQ(slug,'pie','%',2);O['categories']=[str(p['name'])for p in parts];O['series']=[{'name':'Share','values':a5}];O['min_parts']=K;return O
def bF(data):
 af=aa(data)
 if not af:return None
 O=aQ(q,'radar','',1);O['categories']=list(af['categories']);O['series']=[{'name':c['name'],'values':list(c['values'])}for c in af['companies']];O['subject']=af['subject'];O['axis_max']=Z;O['caption']=f'Normalized 0-{int(Z)}';return O
def bt(charts,g):
 cQ={'peer_radar':bF,'price_technical':a2,'revenue_mix':lambda d:aN('revenue_mix',d),'revenue_geo':lambda d:aN('revenue_geo',d)};O={}
 for slug in g:
  f=co(charts,slug)
  if f and f.get('available')and isinstance(f.get('data'),dict)and(slug in cQ):
   c=cQ[slug](f['data'])
   if c:O[slug]=c
 return O
def bu(charts_dir,C):
 charts_dir.mkdir(parents=True,exist_ok=True);path=charts_dir/'chart_contracts.json';w={'version':2,'instruction':'This file is the input of the chart tool: title/caption/unit + categories/series/ohlc. The model must not change the numbers; --render-all calls build_option_from_contract to fill the template and render.','contracts':C};path.write_text(json.dumps(w,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return path
def load_chart_contracts(charts_dir):
 path=charts_dir/'chart_contracts.json'
 if not path.is_file():return{}
 try:
  data=json.loads(path.read_text(encoding='utf-8'))
 except(OSError,json.JSONDecodeError):
  return{}
 C=data.get('contracts')if isinstance(data,dict)else None
 if not isinstance(C,dict):return{}
 return{str(k):v for(k,v)in C.items()if isinstance(v,dict)}
def be(aJ):
 dE=aJ.get('xAxis');cg=dE if isinstance(dE,list)else[dE]
 for f in cg:
  if isinstance(f,dict)and isinstance(f.get('data'),list):return[str(x)for x in f['data']]
 return[]
def bi(aJ):
 raw=aJ.get('series')
 if not isinstance(raw,list):return[]
 O=[]
 for s in raw:
  if not isinstance(s,dict):continue
  dM=str(s.get('type')or '');data=s.get('data')
  if dM=='radar' and isinstance(data,list):
   y=[]
   for f in data:
    if not isinstance(f,dict):continue
    a5=f.get('value');y.append({'name':str(f.get('name')or ''),'values':[v for v in a5]if isinstance(a5,(list,tuple))else[]})
   O.append({'name':str(s.get('name')or 'radar'),'kind':'radar','data':y})
  elif dM=='candlestick' and isinstance(data,list):O.append({'name':str(s.get('name')or 'Price'),'kind':'ohlc','data':data})
  elif isinstance(data,list)and data:
   if isinstance(data[0],dict)and 'value' in data[0]:O.append({'name':str(s.get('name')or 'pie'),'kind':'pie','data':data})
   else:O.append({'name':str(s.get('name')or ''),'kind':'values','data':data})
 return O
def canonicalize_json_floats(B,t=2):
 if isinstance(B,bool):return B
 if isinstance(B,int):return B
 if isinstance(B,float):
  r=z(B,t);return r if r is not None else B
 if isinstance(B,list):return[canonicalize_json_floats(x,t)for x in B]
 if isinstance(B,dict):return{k:canonicalize_json_floats(v,t)for(k,v)in B.items()}
 return B
def canonicalize_option_decimals(aJ,t=2):
 dF=canonicalize_json_floats(aJ,t);return dF if isinstance(dF,dict)else aJ
def build_option_from_contract(l):
 if not isinstance(l,dict)or not l:raise ValueError('Empty contract')
 aR=str(l.get('type')or '');title=str(l.get('title')or l.get('subsection')or l.get('slug')or 'Chart');bn=str(l.get('caption')or '').strip();ck=str(l.get('unit')or '').strip();t=contract_decimals(l);bm=[str(x)for x in l.get('categories')or[]];az={'text':title,'left':'center','top':12,'textStyle':{'fontSize':16,'fontWeight':600}}
 if bn and aR!='pie':
  az['subtext']=bn;az['subtextStyle']={'fontSize':12,'color':'#666'}
 if aR=='pie':
  dy=((l.get('series')or[{}])[0]or{}).get('values')or[];data=[{'name':str(n),'value':float(v)}for(n,r)in zip(bm,dy)for v in(z(r,t),)if v is not None]
  if len(data)<K:raise ValueError(f"{l.get('slug')}: not enough pie sectors")
  return{'backgroundColor':'#FFFFFF','title':az,'tooltip':{'trigger':'item'},'series':[{'name':'Share','type':'pie','radius':['35%','65%'],'center':['50%','55%'],'label':{'formatter':'{b} {c}%'},'data':data}]}
 if aR=='radar':
  c4=[str(x)for x in bm]
  if len(c4)<Y:raise ValueError(f"{l.get('slug')}: not enough radar axes (>={Y})")
  dz=float(z(l.get('axis_max'),0)or Z);y=[]
  for(i,d6)in enumerate(l.get('series')or[]):
   if not isinstance(d6,dict):continue
   name=str(d6.get('name')or f's{i}');cJ=[float(z(rv,t))for rv in d6.get('values')or[]if z(rv,t)is not None]
   if len(cJ)!=len(c4):raise ValueError(f"{l.get('slug')}: {name} point count != axis count")
   y.append({'name':name,'value':cJ})
  if len(y)<J:raise ValueError(f"{l.get('slug')}: not enough radar series (>={J})")
  b2=str(l.get('subject')or y[0]['name']);cS=[]
  for(i,G)in enumerate(y):
   dc=an[i%len(an)];c0=G['name']==b2;f={'name':G['name'],'value':G['value'],'itemStyle':{'color':dc},'lineStyle':{'color':dc,'width':2.6 if c0 else 1.6},'symbol':'circle','symbolSize':8 if c0 else 5}
   if c0:f['areaStyle']={'color':dc,'opacity':0.18}
   cS.append(f)
  return{'backgroundColor':'#FFFFFF','title':az,'tooltip':{'trigger':'item'},'color':list(an),'legend':{'bottom':8,'left':'center','itemGap':16,'data':[r['name']for r in y]},'radar':{'indicator':[{'name':n,'max':dz}for n in c4],'center':['50%','55%'],'radius':'62%','splitNumber':4,'axisName':{'color':'#374151','fontSize':12},'splitLine':{'lineStyle':{'color':'#e6e8ec'}},'splitArea':{'areaStyle':{'color':['#ffffff','#fcfcfd']}}},'series':[{'type':'radar','data':cS}]}
 bB=[]
 for G in l.get('ohlc')or[]:
  if isinstance(G,(list,tuple))and len(G)>=4:
   a5=[z(G[j],t)for j in range(4)]
   if not any((v is None for v in a5)):bB.append([float(v)for v in a5])
 if len(bB)<5 or len(bm)!=len(bB):raise ValueError(f"{l.get('slug')}: the candlestick contract is incomplete")
 return{'backgroundColor':'#FFFFFF','title':az,'tooltip':{'trigger':'axis','axisPointer':{'type':'cross'}},'grid':{'left':56,'right':40,'top':64,'bottom':88,'containLabel':True},'dataZoom':[{'type':'inside','xAxisIndex':0,'filterMode':'filter'},{'type':'slider','xAxisIndex':0,'height':22,'bottom':8,'start':0,'end':100,'showDetail':False,'brushSelect':False}],'xAxis':{'type':'category','data':bm,'boundaryGap':True,'axisLabel':{'rotate':45},'splitLine':{'show':False}},'yAxis':{'type':'value','scale':True,'name':ck or 'CNY','nameLocation':'end','nameGap':12,'axisLine':{'show':False},'axisTick':{'show':False}},'series':[{'name':'Price','type':'candlestick','data':bB,'itemStyle':{'color':'#26a69a','color0':'#ef5350','borderColor':'#26a69a','borderColor0':'#ef5350'}}]}
def assert_option_matches_contract(aJ,l):
 slug=str(l.get('slug')or '');aR=str(l.get('type')or '');cW=[str(x)for x in l.get('categories')or[]];du=bi(aJ)
 if aR=='pie':
  ee=next((s for s in du if s.get('kind')=='pie'),None)
  if not ee or[str(x.get('name')or '').strip()for x in ee['data']if isinstance(x,dict)]!=cW:raise ValueError(f'{slug}: pie option does not match contract')
  return
 if aR=='radar':
  c4=[str(x.get('name')or '')for x in(aJ.get('radar')or{}).get('indicator')or[]if isinstance(x,dict)]
  if c4!=cW:raise ValueError(f'{slug}: radar indicator does not match contract')
  return
 if be(aJ)!=cW:raise ValueError(f'{slug}: categories do not match contract')
bj=4;H={'resolve_symbol':'Symbol resolution','market_snapshot':'Live quote snapshot','price_technical':'Price history and daily K series','deep_profile':'Stock deep profile (westock-data profile/finance/fund/score/risk)','fundamentals_pack':'Financial estimates and earnings surprise (westock-data consensus/calendar / neodata)','institutional_views':'Institutional ratings and Price target (westock-data rating/report / neodata)','news_catalysts':'Market news flash and stock news','public_web_context':'Public web search gap filling (WebSearch/WebFetch)'};R='Figures below are computed from public data for information only. This is not a trade instruction or investment advice.';b1=('...','example.com','example.org','localhost','占位')
def A(aI):
 u=(aI or '').strip().rstrip('.,;，。；')
 if not u.startswith(('http://','https://')):return False
 if len(u)<12:return False
 dQ=u.lower()
 if any((m in dQ for m in b1)):return False
 try:
  from urllib.parse import urlparse;dn=(urlparse(u).hostname or '').lower()
 except Exception:
  return False
 if not dn or '.' not in dn:return False
 return True
def b0(ts):
 try:
  from datetime import datetime,timedelta,timezone;ej=timezone(timedelta(hours=8));return datetime.fromtimestamp(int(ts),ej).strftime('%Y-%m-%d %H:%M:%S UTC+8')
 except(TypeError,ValueError,OSError,OverflowError):
  return ''
def b6(result):
 if isinstance(result,str):return result
 if result is None:return ''
 try:
  return json.dumps(result,ensure_ascii=False)
 except(TypeError,ValueError):
  return str(result)
def ah(text,limit=8):
 if not text:return[]
 O=[];cf=set()
 for c_ in iter_http_urls(text):
  aI=c_.rstrip('.,;，。；')
  if not A(aI)or aI in cf:continue
  cf.add(aI);O.append(aI)
  if len(O)>=limit:break
 return O
def al(aI):
 u=(aI or '').strip().rstrip('.,;，。；/')
 try:
  from urllib.parse import urlsplit,urlunsplit;parts=urlsplit(u);dn=(parts.hostname or '').lower();path=parts.path or ''
  if path!='/' and path.endswith('/'):path=path.rstrip('/')
  return urlunsplit((parts.scheme.lower(),dn,path,parts.query,''))
 except Exception:
  return u.lower()
def a3(aY,dv):
 a=(aY or '').strip();b=(dv or '').strip()
 if not b:return a or 'Public web'
 if not a:return b
 ea=('Public web search records','Public web','Host data pack','Inline citation');dG=any((a==x or a.startswith(x)for x in ea))or a in H.values();dH=any((b==x or b.startswith(x)for x in ea))or b in H.values()
 if dG and(not dH):return b
 if dH and(not dG):return a
 return b if len(b)>len(a)else a
def I(U,*,tool,label,code,channel,retrieved_at='',urls=None,notes=''):
 cl=[str(u).strip().rstrip('.,;，。；')for u in urls or[]if A(str(u).strip())]
 if not cl:
  key=(tool or label,code or '-',channel or '-','');aY=U.get(key)
  if aY is None:U[key]={'tool':tool,'label':label,'code':code,'channel':channel,'retrieved_at':retrieved_at,'urls':[],'url':'','notes':notes}
  return
 for aI in cl:
  key=(tool or label,code or '-',channel or '-',al(aI));aY=U.get(key)
  if aY is None:
   U[key]={'tool':tool,'label':label,'code':code,'channel':channel,'retrieved_at':retrieved_at,'urls':[aI],'url':aI,'notes':notes};continue
  if retrieved_at and(not aY.get('retrieved_at')):aY['retrieved_at']=retrieved_at
  if notes and notes not in str(aY.get('notes')or ''):aY['notes']=(str(aY.get('notes')or '')+'; '+notes).strip('; ')
  aY['label']=a3(str(aY.get('label')or ''),label)
def E(U,ay,*,default_label,code,pack_name):
 raw=ay.get('sources')
 if not isinstance(raw,list):return
 for f in raw:
  if not isinstance(f,dict):continue
  title=str(f.get('title')or f.get('name')or default_label).strip();b4=str(f.get('url')or f.get('href')or '').strip();aP=ah(b4,limit=8)
  if not aP and b4 and A(b4):aP=[b4.rstrip('.,;，。；')]
  cH=str(f.get('retrieved_at')or f.get('date')or '').strip();dX=str(f.get('note')or f.get('desc')or f.get('description')or '').strip()
  if not title and(not aP):continue
  if not aP:
   I(U,tool=pack_name,label=title or default_label,code=code,channel='Host data pack (explicit source)',retrieved_at=cH,urls=[],notes=dX);continue
  for aI in aP:
   I(U,tool=pack_name,label=title or default_label,code=code,channel='Host data pack (explicit source)',retrieved_at=cH,urls=[aI],notes=dX)
def collect_data_sources(F,charts_dir=None,report_md=''):
 y=list(F or[])
 if charts_dir is not None:y=a9(y,Path(charts_dir))
 U={}
 for G in y:
  if not isinstance(G,dict):continue
  tool=str(G.get('tool')or '').strip()
  if not tool:continue
  cI=G.get('arguments');args=cI if isinstance(cI,dict)else{};code=str(args.get('code')or args.get('stock_code')or args.get('query')or '').strip();ao=aT(G.get('result'))
  if isinstance(ao,dict)and(not code):code=str(ao.get('code')or '').strip()
  b5=b6(G.get('result'));bO=isinstance(ao,dict)and str(ao.get('status')or '').startswith('use_host')
  if bO:
   urls=[];dd=[];notes='Host data guide (the formal source is host_*.json / sources[])'
  else:
   urls=ah(b5);dd=parse_labeled_values(b5,'媒体来源');notes='Media: '+', '.join(dd[:5])if dd else ''
  label=H.get(tool,tool);channel='Host data pack' if G.get('source')=='host_pack' else 'Deep research tool call';I(U,tool=tool,label=label,code=code,channel=channel,retrieved_at=b0(G.get('ts')),urls=urls,notes=notes)
  if isinstance(ao,dict)and(not bO):E(U,ao,default_label=label,code=code,pack_name=tool)
 if charts_dir is not None:
  dY=Path(charts_dir)
  for path in sorted(dY.glob('host_*.json')):
   try:
    ay=json.loads(path.read_text(encoding='utf-8'))
   except(OSError,json.JSONDecodeError):
    continue
   if not isinstance(ay,dict)or not ay:continue
   code=str(ay.get('code')or '').strip();label={'host_deep_profile.json':H['deep_profile'],'host_fundamentals_pack.json':H['fundamentals_pack'],'host_institutional_views.json':H['institutional_views'],'host_web_sources.json':'Public web search records'}.get(path.name,f'Host data pack ({path.name})')
   if path.name!='host_web_sources.json':
    urls=ah(json.dumps(ay,ensure_ascii=False),limit=12)
    for aI in urls:
     I(U,tool=path.stem,label=label,code=code,channel='Host data pack file',urls=[aI],notes=f'File: {path.name}')
   E(U,ay,default_label=label,code=code,pack_name=path.stem)
  cT=dY/'host_web_sources.json'
  if cT.is_file():
   try:
    dA=json.loads(cT.read_text(encoding='utf-8'))
   except(OSError,json.JSONDecodeError):
    dA=None
   if isinstance(dA,list):
    for f in dA:
     if isinstance(f,dict):E(U,{'sources':[f]},default_label='Public web',code=str(f.get('code')or '').strip(),pack_name='host_web_sources')
   elif isinstance(dA,dict):E(U,dA,default_label='Public web',code=str(dA.get('code')or '').strip(),pack_name='host_web_sources')
 if report_md:
  for dR in parse_inline_sources(report_md):
   c1=dR.label.strip()
   if not c1:continue
   urls=ah(c1,limit=3);I(U,tool='inline_citation',label=f'Inline citation: {c1}',code='',channel='Report body',urls=urls)
 cL={'Deep research tool call':0,'Host data pack':1,'Host data pack file':2,'Host data pack (explicit source)':3,'Report body':4};D=list(U.values());D.sort(key=lambda e:(cL.get(str(e.get('channel')or ''),9),str(e.get('tool')or ''),str(e.get('code')or ''),str(e.get('label')or '')));return aW(D)
def X(D):
 cr={};dI=[]
 for f in D:
  if not isinstance(f,dict):continue
  label=str(f.get('label')or '').strip();notes=str(f.get('notes')or '').strip();T=label
  if notes and(not notes.startswith(('File: ','Media: ','Host'))):
   if T and notes not in T:T=f'{T} ({notes})'
   elif not T:T=notes
  cb=list(f.get('urls')or[]);ef=str(f.get('url')or '').strip()
  if ef:cb=[ef]+cb
  urls=[];cn=set()
  for raw in cb:
   for u in ah(str(raw),limit=8)or([str(raw).strip().rstrip('.,;，。；')]if A(str(raw).strip())else[]):
    cu=al(u)
    if not cu or cu in cn:continue
    cn.add(cu);urls.append(u.strip().rstrip('.,;，。；'))
  for aI in urls:
   if not A(aI):continue
   key=al(aI)
   if key not in cr:
    cr[key]={'tool':f.get('tool')or '','label':T or 'Public web','code':f.get('code')or '','channel':f.get('channel')or '','retrieved_at':f.get('retrieved_at')or '','url':aI,'urls':[aI],'notes':notes};dI.append(key)
   else:
    aY=cr[key];aY['label']=a3(str(aY.get('label')or ''),T or '')
    if notes and notes not in str(aY.get('notes')or ''):aY['notes']=(str(aY.get('notes')or '')+'; '+notes).strip('; ')
    if f.get('retrieved_at')and(not aY.get('retrieved_at')):aY['retrieved_at']=f.get('retrieved_at')
 return[cr[k]for k in dI]
def aW(D):return X(D)
def limit_reference_entries(D,*,dJ=bj):
 D=X(D)
 if not D or dJ<=0:return[]
 def d0(f):
  tool=str(f.get('tool')or '');label=str(f.get('label')or '')
  if 'web_sources' in tool or label.startswith('Public web'):return(0,tool,label)
  if str(f.get('channel')or '')=='Host data pack (explicit source)':return(1,tool,label)
  return(2,tool,label)
 ax=sorted((e for e in D if isinstance(e,dict)),key=d0);return ax[:dJ]
def ad(D):
 D=limit_reference_entries(D)
 if not D:return ''
 cV=['## References',''];n=0
 for f in D:
  label=str(f.get('label')or 'Unnamed source').strip();label=strip_parenthetical_label(label,'westock').strip()or 'Public web';aI=str(f.get('url')or '').strip()
  if not aI:
   urls=[str(u).strip()for u in f.get('urls')or[]if str(u).strip()];aI=urls[0]if urls else ''
  if not aI or not A(aI):continue
  n+=1;cV.append(f'{n}. *{label}* · {aI}')
 if n==0:return ''
 return '\n'.join(cV)
def inject_references_section(md,D):
 body=md or ''
 while MarkdownDocument(body).find_section(2,'References')is not None:
  body=MarkdownDocument(body).remove_section(2,'References')
 body=body.strip();dK=ad(D)
 if not dK:
  if R in body:return body if body.endswith('\n')else body+'\n'
  return f'{body}\n\n{R}\n'
 if R in body:
  eg=body.rfind(R);dS=body[:eg].rstrip();d4=body[eg:].lstrip();return f'{dS}\n\n{dK}\n\n{d4}'.strip()+'\n'
 return f'{body}\n\n{dK}\n\n{R}\n'
def write_references_artifacts(charts_dir,D):
 charts_dir.mkdir(parents=True,exist_ok=True);items=limit_reference_entries(D);cE=charts_dir/'references.json';c3=charts_dir/'references.md';cE.write_text(json.dumps({'count':len(items),'items':items},ensure_ascii=False,indent=2)+'\n',encoding='utf-8');c3.write_text(ad(items)+'\n',encoding='utf-8');return(cE,c3)
def write_chart_payloads(F,bT,report_text=''):
 w=bJ(F,charts_dir=bT.parent,report_text=report_text or '');bT.parent.mkdir(parents=True,exist_ok=True);bT.write_text(json.dumps(w,ensure_ascii=False,indent=2),encoding='utf-8');bC=w.get('contracts');C=bC if isinstance(bC,dict)else{};bu(bT.parent,C);return w
if __name__=='__main__':sys.exit(main())
