import re;import argparse;import html;import json;import os;import shutil;import subprocess;import sys;from html.parser import HTMLParser;from pathlib import Path;from typing import Any,Dict,List,Optional,Tuple;sys.path.insert(0,str(Path(__file__).resolve().parent));import client_common;import ensure_report;import os_compat;from markdown_document import MarkdownDocument,is_horizontal_rule,is_table_separator_line,list_item_prefix,parse_heading_line,split_table_row;import report_with_charts as charts;import research_state as rs;E=Path(__file__).resolve().parent.parent;_SECTIONS_PATH=E/'report_sections.json';aw=E/'nl-echarts'/'render-echarts.mjs';T=(E/'node_modules'/'echarts'/'dist'/'echarts.min.js',E/'node_modules'/'echarts'/'dist'/'echarts.js');aL=('cdn.jsdelivr','unpkg.com','cdnjs.cloudflare','bootcdn.net');ae=('echarts.min.js','./echarts.min.js')
class _ReportHTMLParser(HTMLParser):
 def __init__(self):
  super().__init__(convert_charrefs=True);self.script_sources=[];self.script_contents=[];self.element_ids=set();self.has_iframe=False;self._script_parts=None
 def handle_starttag(self,cz,ck):
  bo=cz.casefold()
  for(name,M)in ck:
   if name.casefold()=='id' and M:self.element_ids.add(M)
  if bo=='iframe':
   self.has_iframe=True;return
  if bo!='script':return
  O=''
  for(name,M)in ck:
   if name.casefold()=='src':
    O=str(M or '').strip();break
  if O:self.script_sources.append(O)
  self._script_parts=[]
 def handle_endtag(self,cz):
  if cz.casefold()=='script' and self._script_parts is not None:
   self.script_contents.append(''.join(self._script_parts));self._script_parts=None
 def handle_data(self,data):
  if self._script_parts is not None:self._script_parts.append(data)
def bm(text):
 y=_ReportHTMLParser();y.feed(text);y.close();return y
def az(O):
 bo=O.strip().casefold();return bo.startswith(('http://','https://','//'))or any((bD in bo for bD in aL))
def aW():
 data=json.loads(_SECTIONS_PATH.read_text(encoding='utf-8'))
 if not isinstance(data,dict)or not data.get('required_h2'):raise ValueError(f'invalid report structure definition: {_SECTIONS_PATH}')
 return data
N=aW();t=dict(N.get('chart_section_map')or{});r=dict(N.get('chart_subsection_map')or{})
if not t:t={k:v[0]for(k,v)in charts.CHART_DATA_ANCHOR.items()}
if not r:r={k:v[1]for(k,v)in charts.CHART_DATA_ANCHOR.items()}
for(ce,(cH,cI))in charts.CHART_DATA_ANCHOR.items():
 t.setdefault(ce,cH);r.setdefault(ce,cI)
aM=('market_change_gauge','market_snapshot');bj=tuple(N.get('required_h2')or());a6=tuple((f.get('subsection')for f in N.get('required_h3')or[]if isinstance(f,dict)and f.get('subsection')))
def b5(a1,title):
 if MarkdownDocument(a1).find_section(2,title)is None:raise ValueError(f'missing the standard section: ## {title}')
def _assert_writer_structure(a1):ensure_report._assert_writer_structure(a1)
def bJ(a1,G):return charts.canonicalize_floats_in_text(a1,2)
def b2(a1):
 cn=Path(__file__).resolve().parent/'finalize_report.py';bx=subprocess.run([os_compat.python_exe(),str(cn)],input=a1,capture_output=True,text=True)
 if bx.returncode!=0:raise RuntimeError(bx.stderr.strip()or 'finalize_report failed')
 cf=bx.stdout.strip()
 if not cf:raise RuntimeError('finalize_report returned an empty body')
 return cf
def P(session,h):
 if h:a=Path(h).resolve()
 else:
  a3=str(session.get('charts_dir')or '').strip();a=Path(a3).resolve()if a3 else(client_common.ensure_artifacts_dir()/f"{session['session_id']}.charts").resolve()
 a.mkdir(parents=True,exist_ok=True);return a
def an():
 client_common.load_skill_env();session=client_common.load_session();bE=str(session.get('trace_file')or '').strip()
 if not bE:raise ValueError('this research trace is missing; text and chart data consistency cannot be guaranteed.')
 G=charts._load_traces(Path(bE))
 if not G:raise ValueError('this research trace is empty; same-source charts cannot be generated.')
 return(session,G)
def ag(charts_dir):
 Y=charts_dir/'chart-payloads.json'
 if not Y.is_file():return[]
 try:
  data=json.loads(Y.read_text(encoding='utf-8'))
 except json.JSONDecodeError:
  return[]
 bk=data.get('suggested_chart_slugs')
 if isinstance(bk,list)and bk:return[str(s)for s in bk]
 aT=[]
 for f in data.get('charts')or[]:
  if not isinstance(f,dict)or not f.get('available'):continue
  for sc in f.get('suggested_charts')or[]:
   if isinstance(sc,dict)and sc.get('slug'):aT.append(str(sc['slug']))
 return aT
def w(charts_dir):
 co=[]
 for path in sorted(charts_dir.iterdir())if charts_dir.is_dir()else[]:
  if not path.is_file():continue
  name=path.name;stem=path.stem.replace('.option','')if name.endswith('.option.json')else path.stem
  if any((stem==al or stem.startswith(al+'.')for al in aM)):
   co.append(name);continue
  if name.endswith('.show-widget.svg')or name.endswith('.show-widget.html'):co.append(name)
 if co:raise ValueError('found deprecated or conflicting chart artifacts: '+', '.join(co)+'. Delete the forbidden artifacts market_snapshot / market_change_gauge / show_widget and re-run; prefer price_technical (candlestick) for the valuation chart.')
def ab(path):
 if not path.is_file():return None
 try:
  data=json.loads(path.read_text(encoding='utf-8'))
 except(OSError,json.JSONDecodeError):
  return None
 return data if isinstance(data,dict)else None
def ay(l):
 by=l.get('yAxis');cC=by if isinstance(by,list)else[by]
 for f in cC:
  if isinstance(f,dict)and f.get('min')==0:return True
 return False
def a4(l):
 dz=l.get('dataZoom')
 if not isinstance(dz,list)or not dz:return False
 cg={str(f.get('type')or '').strip()for f in dz if isinstance(f,dict)};return 'inside' in cg and 'slider' in cg
def u(charts_dir,e=None):
 b6=set(e or[])
 if 'market_snapshot' in b6:
  bN=ab(charts_dir/'market_snapshot.option.json')
  if bN is not None and ay(bN):raise ValueError('market_snapshot forbids absolute price yAxis.min=0; switch to yAxis.scale:true and re-render.')
 if 'price_technical' in b6:
  bS=ab(charts_dir/'price_technical.option.json')
  if bS is not None and ay(bS):raise ValueError('price_technical forbids the price axis yAxis.min=0; switch to yAxis.scale:true and re-render.')
  if bS is not None and(not a4(bS)):raise ValueError('price_technical must include dataZoom (type=inside + type=slider) to support the bottom slider and wheel zoom; fill it in per the visual-theme.md candlestick template and re-render.')
def ad():
 for path in T:
  if path.is_file():return path
 raise FileNotFoundError(f'the local echarts.min.js was not found. Run npm install in the skill root (expected {T[0]})')
def W(charts_dir):
 cD=ad();bh=charts_dir/'echarts.min.js';charts_dir.mkdir(parents=True,exist_ok=True)
 if not bh.is_file()or bh.stat().st_size!=cD.stat().st_size:shutil.copy2(cD,bh)
 return bh
def bd(charts_dir,slug):
 p=charts_dir/f'{slug}.option.json'
 if p.is_file():
  d=ab(p)
  if d:return B(d)
  raise ValueError(f'{slug}.option.json is invalid or empty')
 hp=charts_dir/f'{slug}.html'
 if not hp.is_file():raise ValueError(f'missing chart option: {slug}')
 cM=hp.read_text(encoding='utf-8',errors='ignore');m=re.search('var\\s+option\\s*=\\s*(\\{.*?\\});\\s*var\\s+chart',cM,re.S)
 if not m:raise ValueError(f'{slug}.html is missing var option')
 return B(json.loads(m.group(1)))
def o(f):
 if f is None:return False
 if isinstance(f,bool):return True
 if isinstance(f,(int,float)):return f==f and float(f)!=0.0
 if isinstance(f,str):return bool(f.strip())
 if isinstance(f,dict):
  if 'value' in f:return o(f.get('value'))
  return any((o(v)for v in f.values()))
 if isinstance(f,(list,tuple)):
  cv=[float(x)for x in f if isinstance(x,(int,float))and(not isinstance(x,bool))and(x==x)]
  if cv and any((n!=0.0 for n in cv)):return True
  return any((o(x)for x in f if not isinstance(x,(int,float))or isinstance(x,bool)))
 return False
def ah(by):
 if isinstance(by,dict):
  data=by.get('data');return list(data)if isinstance(data,list)else[]
 if isinstance(by,list):
  am=[]
  for f in by:
   if isinstance(f,dict)and isinstance(f.get('data'),list):am.extend(f['data'])
  return am
 return[]
def a7(data):
 bF=0.0
 for f in data:
  if isinstance(f,bool):continue
  if isinstance(f,(int,float))and f==f:bF+=abs(float(f))
  elif isinstance(f,dict)and 'value' in f:
   v=f.get('value')
   if isinstance(v,(int,float))and v==v:bF+=abs(float(v))
   elif isinstance(v,(list,tuple)):
    for x in v:
     if isinstance(x,(int,float))and x==x:bF+=abs(float(x))
  elif isinstance(f,(list,tuple)):
   for x in f:
    if isinstance(x,(int,float))and x==x:bF+=abs(float(x))
 return bF
def Q(l):
 if not isinstance(l,dict)or not l:return False
 V=l.get('series')
 if isinstance(V,dict):V=[V]
 if not isinstance(V,list)or not V:return False
 cp=ah(l.get('xAxis'));cq=ah(l.get('yAxis'));bb=False
 for s in V:
  if not isinstance(s,dict):continue
  cl=str(s.get('type')or '').lower();data=s.get('data')
  if not isinstance(data,list)or not data:continue
  if cl=='pie':
   cc=sum((1 for f in data if o(f)))
   if cc>=2:bb=True
   continue
  if cl in('bar','pictorialbar'):
   if not cp and(not cq):continue
   if a7(data)<=0:continue
   bb=True;continue
  if any((o(f)for f in data)):bb=True
 return bb
def A(charts_dir,slug):
 try:
  l=bd(charts_dir,slug)
 except ValueError:
  return None
 if not Q(l):return None
 return charts.canonicalize_option_decimals(l,2)
def a2(M):
 C=charts.canonicalize_json_floats(M,2);return json.dumps(C,ensure_ascii=False).replace('</','<\\/')
def L(j):
 text=j.read_text(encoding='utf-8',errors='ignore');y=bm(text)
 if y.has_iframe:raise ValueError(f'{j.name} still contains an iframe; nested chart pages are forbidden.')
 if any((az(O)for O in y.script_sources)):raise ValueError(f'{j.name} still references CDN/external ECharts and will be blank offline. Re-render with --render-all or render-echarts.mjs (the local ./echarts.min.js is enforced).')
 bA=[O.casefold()for O in y.script_sources]
 if not any((O in ae for O in bA)):raise ValueError(f'{j.name} does not reference the local ./echarts.min.js; chart rendering cannot be guaranteed.')
 bW=[O for O in y.script_sources if O.casefold()not in ae]
 if bW:raise ValueError(f'{j.name} contains extra relative scripts; single-file assembly safety cannot be guaranteed.')
 if 'echarts.init' not in text and 'setOption' not in text:raise ValueError(f'{j.name} is missing ECharts init logic; probably an empty shell HTML.')
def J(charts_dir,e):
 W(charts_dir);U=charts_dir/'echarts.min.js'
 if not U.is_file()or U.stat().st_size<100000:raise ValueError(f'the local echarts runtime is invalid: {U}')
 for slug in e:
  j=charts_dir/f'{slug}.html'
  if not j.is_file():raise ValueError(f'interactive charts missing: {slug}.html')
  L(j)
def bi(aj,j,cw=900,height=520):
 if not aw.is_file():raise FileNotFoundError(f'the render script does not exist: {aw}')
 bx=subprocess.run([os_compat.resolve_exe('node'),str(aw),'--input',str(aj),'--out',str(j),'--format','html','--width',str(cw),'--height',str(height)],capture_output=True,text=True,cwd=str(E))
 if bx.returncode!=0:
  cs=(bx.stderr or bx.stdout or '').strip();raise RuntimeError(f"render failed {aj.name}: {cs or f'exit {bx.returncode}'}")
 L(j)
def av(charts_dir,e=None):
 aG={};bk=list(e)if e else list(r.keys())
 if len(bk)>charts.MAX_SUGGESTED_CHARTS:raise ValueError(f'suggested chart count {len(bk)} exceeds the limit {charts.MAX_SUGGESTED_CHARTS}; please re-run --dump-payloads')
 cE={s:i for(i,s)in enumerate(charts.CHART_PRIORITY)};bK=sorted(bk,key=lambda s:(cE.get(s,999),s))
 for slug in bK:
  section=t.get(slug);subsection=r.get(slug)
  if not section or not subsection:raise ValueError(f'Chart {slug} is missing its module/section anchor and cannot be inserted right after the data paragraph')
  if section not in bj:raise ValueError(f'Chart {slug} maps to module "{section}" is not one of the six core modules')
  if subsection not in a6:raise ValueError(f'Chart {slug} anchor "### {subsection}" is not among the unlocked sub-points')
  if subsection in aG:continue
  j=charts_dir/f'{slug}.html'
  if not j.is_file():continue
  text=j.read_text(encoding='utf-8',errors='ignore')
  if '<html' not in text.lower()and 'echarts' not in text.lower():continue
  if A(charts_dir,slug)is None:continue
  aG[subsection]=(slug,j)
 return aG
def R(text):
 am=[];ak=0;q=0
 def aB(end):
  nonlocal ak
  if end>ak:am.append(html.escape(text[ak:end]))
 while q<len(text):
  if text[q]=='`':
   end=text.find('`',q+1)
   if end>q+1:
    aB(q);am.append(f'<code>{html.escape(text[q + 1:end])}</code>');q=end+1;ak=q;continue
  if text.startswith('**',q):
   end=text.find('**',q+2)
   if end>q+2:
    aB(q);am.append(f'<strong>{R(text[q + 2:end])}</strong>');q=end+2;ak=q;continue
  if text[q]=='[':
   aK=text.find('](',q+1)
   if aK>q+1:
    bI=text.find(')',aK+2)
    if bI>aK+2:
     cL=text[aK+2:bI];b1=cL.casefold()
     if b1.startswith(('http://','https://')):
      aB(q);am.append(f'<a href="{html.escape(cL, quote=True)}" target="_blank" rel="noopener">{R(text[q + 1:aK])}</a>');q=bI+1;ak=q;continue
  q+=1
 aB(len(text));return ''.join(am)
def H(md):
 ch=md.replace('\r\n','\n').split('\n');am=[];i=0;aU='';bc=False
 def af():
  nonlocal aU
  if aU:
   am.append(f'</{aU}>');aU=''
 def ai():
  nonlocal bc
  if bc:
   am.append('</tbody></table>');bc=False
 while i<len(ch):
  b9=ch[i];ap=b9.strip()
  if not ap:
   af();ai();i+=1;continue
  if is_horizontal_rule(ap):
   i+=1;continue
  heading=parse_heading_line(b9)
  if heading is not None:
   af();ai();(level,title)=heading;am.append(f'<h{level}>{R(title)}</h{level}>');i+=1;continue
  if ap.startswith('|')and '|' in ap[1:]:
   af();cm=split_table_row(ap)
   if is_table_separator_line(ap):
    i+=1;continue
   if not bc:
    am.append('<table><thead><tr>')
    for c in cm:
     am.append(f'<th>{R(c)}</th>')
    am.append('</tr></thead><tbody>');bc=True
   else:
    am.append('<tr>')
    for c in cm:
     am.append(f'<td>{R(c)}</td>')
    am.append('</tr>')
   i+=1;continue
  al=list_item_prefix(b9)
  if al is not None:
   ai();bD=al.lstrip();ba='ol' if bD and bD[0].isdigit()else 'ul'
   if aU!=ba:
    af();am.append(f'<{ba}>');aU=ba
   f=b9[len(al):].strip();am.append(f'<li>{R(f)}</li>');i+=1;continue
  af();ai();am.append(f'<p>{R(ap)}</p>');i+=1
 af();ai();return '\n'.join(am)
def I(M):
 if isinstance(M,str):
  if '\\n' in M or '\\t' in M or '\\r' in M:return M.replace('\\r\\n','\n').replace('\\n','\n').replace('\\t','\t').replace('\\r','\r')
  return M
 if isinstance(M,list):return[I(v)for v in M]
 if isinstance(M,dict):return{k:I(v)for(k,v)in M.items()}
 return M
def aA(l):
 V=l.get('series')
 if isinstance(V,dict):
  V=[V];l['series']=V
 if not isinstance(V,list):return l
 for s in V:
  if isinstance(s,dict)and str(s.get('type')or '').lower()=='pie':
   s['label']={'show':True,'formatter':'{b} {c}%'}
   for f in s.get('data')or[]:
    if isinstance(f,dict):
     f.pop('label',None);f['name']=re.sub('\\s+\\d+(?:\\.\\d+)?%$','',str(f.get('name')or '').strip()).strip()
   l['legend']={'show':False}
 return l
def B(l):
 aS=I(l)
 if not isinstance(aS,dict):return l
 return aA(aS)
def bn(slug,section='',subsection='',height=520):
 title=html.escape(slug.replace('_',' '));cu=html.escape(slug);ci=html.escape(section)if section else '';sub=html.escape(subsection)if subsection else ''
 if sub:br=f'This chart matches the "{sub}" key data'
 elif ci:br=f'This chart matches the "{ci}" key data'
 else:br=title
 return f'<figure class="chart" id="figure-{cu}" data-section="{ci}" data-subsection="{sub}" data-chart-height="{height}"><figcaption>{br}</figcaption><div class="chart-box" id="chart-{cu}" role="img" aria-label="{br}" style="width:100%;"></div></figure>'
def aX(md):
 sections=MarkdownDocument(md).split_sections(2);bp=[]
 if not sections:return[('',md)]if md.strip()else[]
 if md[:sections[0].start].strip():bp.append(('',md[:sections[0].start]))
 for section in sections:
  bp.append((section.heading.title,section.text(md)))
 return bp
def aP(ao):
 sections=MarkdownDocument(ao).split_sections(3)
 if not sections:return(ao,[])
 bq=ao[:sections[0].start];cF=[(section.heading.title,section.text(ao))for section in sections];return(bq,cF)
def be(bu,g,charts_dir,bL):
 ar=W(charts_dir);U=ar.read_text(encoding='utf-8',errors='ignore')
 if len(U)<100000 or 'echarts' not in U[:2000].lower():raise ValueError(f'invalid local echarts: {ar}')
 bu=charts.canonicalize_floats_in_text(bu,2);bp=[b for b in aX(a5(bu))if b[1].strip()];(aI,au,aD)=([],[],set())
 def a9(aO,slug,aF,D):
  l=A(charts_dir,slug)
  if l is None:return False
  ci=t.get(slug,aF);aO.append(f'<div class="charts" data-after-subsection="{html.escape(D)}">\n'+bn(slug,section=ci,subsection=D,height=560 if slug=='price_technical' else 520)+'\n</div>');au.append((slug,l));return True
 for(aF,ao)in bp:
  (bq,bO)=aP(ao);bY='section refs' if aF.strip()=='References' else 'section'
  if not bO:
   aO=[H(ao)]
   for(D,(slug,_))in list(g.items()):
    if D not in aD and t.get(slug)==aF and a9(aO,slug,aF,D):aD.add(D)
   aI.append(f'<section class="{bY}">\n'+'\n'.join(aO)+'\n</section>');continue
  aO=[H(bq)]if bq.strip()else[]
  for(D,ct)in bO:
   aO.append(H(ct))
   if D in g:
    (slug,_)=g[D]
    if a9(aO,slug,aF,D):aD.add(D)
  aI.append(f'<section class="{bY}">\n'+'\n'.join(aO)+'\n</section>')
 if not au:raise ValueError('no drawable chart was embedded')
 if len(au)>charts.MAX_SUGGESTED_CHARTS:raise ValueError(f'embedded charts {len(au)} exceed limit {charts.MAX_SUGGESTED_CHARTS}')
 ca={sub for(sub,(slug,_))in g.items()if A(charts_dir,slug)is not None};b7=ca-aD
 if b7:raise ValueError('Charts could not be attached to their target ### or ## section: '+', '.join(sorted(b7)))
 a_=['(function(){function rm(el){var w=el&&(el.closest(".charts")||el.closest("figure.chart"));if(w&&w.parentNode)w.parentNode.removeChild(w);}function boot(){']
 for(slug,l)in au:
  a_.append(f"(function(){{var el=document.getElementById({a2('chart-' + slug)});if(!el)return;var fig=el.closest('figure.chart');try{{var opt={a2(l)};var h=(fig&&parseInt(fig.getAttribute('data-chart-height'),10))||520;el.style.height=h+'px';if(fig)fig.classList.add('is-ready');var w=el.closest('.charts');if(w)w.classList.add('is-ready');var c=echarts.init(el);c.setOption(opt);c.resize();window.addEventListener('resize',function(){{c.resize();}});}}catch(e){{rm(el);}}}})();")
 a_.append('}if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",boot);else boot();})();');cj='\n'.join(a_);bz=html.escape(bL or 'research note');cN=':root{--bg:#f7f8fa;--card:#fff;--text:#1f2329;--muted:#646a73;--line:#e5e6eb;--accent:#3370ff}body{margin:0;font:15px/1.65 sans-serif;color:var(--text);background:var(--bg)}.wrap{max-width:960px;margin:0 auto;padding:32px 20px 64px}header.hero{margin-bottom:28px}header.hero h1{margin:0 0 8px;font-size:28px}header.hero p{margin:0;color:var(--muted);font-size:14px}.section{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 22px 8px;margin-bottom:18px}.section h1{font-size:24px;margin:.2em 0 .6em}.section h2{font-size:20px;margin:.2em 0 .6em;border-left:3px solid var(--accent);padding-left:10px}.section h3{font-size:16px;margin:1em 0 .4em}.section p,.section li{font-size:15px}table{width:100%;border-collapse:collapse;margin:12px 0 16px;font-size:14px}th,td{border:1px solid var(--line);padding:8px 10px;text-align:left}th{background:#f2f3f5}.charts,figure.chart{display:none}.charts.is-ready{display:block;margin:8px 0 16px}figure.chart.is-ready{display:block}figure.chart{margin:0 0 16px;border:1px solid var(--line);border-radius:10px;overflow:hidden;background:#fff}figure.chart figcaption{padding:8px 12px;font-size:13px;color:var(--muted);border-bottom:1px solid var(--line)}.chart-box{width:100%;background:#fff}code{background:#f2f3f5;padding:0 4px;border-radius:4px}a{color:var(--accent)}.section.refs{background:transparent;border:none;padding:8px 4px 0}.section.refs h2,.section.refs p,.section.refs li{font-size:12px;color:var(--muted);border:none;padding:0}';return f"""<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><title>{bz}</title><style>{cN}</style></head><body><main class="wrap"><header class="hero"><h1>{bz}</h1><p>Illustrated report · self-contained ECharts interactive HTML</p></header>{''.join(aI)}</main><script>{U}</script><script>{cj}</script></body></html>\n"""
def X(z,bB):
 text=z.read_text(encoding='utf-8',errors='ignore');y=bm(text)
 if y.has_iframe:raise ValueError('report.html still contains an iframe; the preview panel will be blank, so it must render inline inside a div')
 if y.script_sources:raise ValueError('report.html still loads ECharts via script src; the full echarts.min.js must be inlined into the single file')
 if 'echarts.init' not in text or 'setOption' not in text:raise ValueError('report.html is missing inline ECharts init logic')
 if len(text)<100000:raise ValueError('report.html is too small; the echarts runtime is probably not inlined')
 for slug in bB:
  if f'chart-{slug}' not in y.element_ids:raise ValueError(f'report.html is missing the chart container chart-{slug}')
def aY(md):
 b8=MarkdownDocument(md).heading_titles(1);return b8[0].strip()if b8 else 'research note'
def a5(md):
 cb=MarkdownDocument(md);body=md
 for heading in reversed([f for f in cb.headings if f.level==1]):
  body=body[:heading.start]+body[heading.end:]
 return body
def ac(code):
 c=str(code or '').strip()
 if not c:return ''
 cx=c.lower()
 if cx.startswith('us')and len(c)>2 and c[2:].replace('.','').isalpha():return c[2:].split('.')[0].upper()
 if '.' in c:return c.split('.',1)[0].upper()
 if len(c)in(6,7)and cx.startswith('hk')and c[2:].isdigit():return c.upper()
 if len(c)==8 and cx[:2]in('sh','sz','bj')and c[2:].isdigit():return c.lower()
 return c.upper()
def at(G):
 for f in G or[]:
  if not isinstance(f,dict):continue
  for key in('result','data','output','content'):
   C=f.get(key)
   if isinstance(C,str):
    try:
     C=json.loads(C)
    except json.JSONDecodeError:
     C=None
   if not isinstance(C,dict):continue
   for cA in('code','symbol','standard_code','ticker'):
    code=ac(str(C.get(cA)or ''))
    if code:return code
   args=C.get('arguments')if isinstance(C.get('arguments'),dict)else None
   if args:
    code=ac(str(args.get('code')or args.get('symbol')or ''))
    if code:return code
  code=ac(str(f.get('code')or f.get('symbol')or ''))
  if code:return code
 return ''
def aZ(title,G):
 raw=str(title or '').strip()or 'research note';Z=raw
 for al in('research note: ','research note: '):
  if Z.startswith(al):
   Z=Z[len(al):].strip();break
 else:return raw if len(raw)<=32 else raw[:31].rstrip()+'…'
 code=at(G);name=''
 if code:
  index=Z.casefold().find(code.casefold())
  if index>=0:name=Z[:index].strip(' ：:，,、-—_（）()')
 if name:
  if len(name)>24:name=name[:24].rstrip()+'…'
  return f'{name} ({code}) research note'
 if code:return f'{code} research note'
 if len(Z)>24:Z=Z[:24].rstrip()+'…'
 return f'{Z}research note' if Z else 'research note'
def a8(title,G):
 cr=frozenset('\\/:*?"<>|：');aT=''.join((b_ for b_ in title if b_ not in cr and ord(b_)>=32 and(not b_.isspace()))).strip()or 'research note'
 if aT.lower().endswith('.html'):aT=aT[:- 5]
 if len(aT)>60:aT=aT[:60]
 code=at(G)
 if code and code.upper()not in aT.upper():aT=f'{aT}_{code}'
 return f'{aT}.html'
def a0(path,cG):
 try:
  path.resolve().relative_to(cG.resolve());return True
 except ValueError:
  return False
def aQ():
 bR=E.resolve();bM=(os.environ.get('FINTRUST_PRESENT_DIR')or '').strip()
 if bM:
  aN=Path(bM).expanduser().resolve()
  if aN.name=='outputs' and aN.parent.is_dir():aN=aN.parent
 else:
  cwd=Path.cwd().resolve();bT=cwd==bR or a0(cwd,bR)
  if bT:
   cJ=(os.environ.get('OLDPWD')or '').strip()
   if not cJ:
    al=os_compat.assemble_env_prefix('<skill root>');raise ValueError(f'cannot resolve the host session workspace: assemble-html ran inside the skill directory and OLDPWD is unset. Use: {al}{os_compat.py_cmd()} scripts/prepare_report.py --assemble-html ...')
   aN=Path(cJ).expanduser().resolve()
  else:aN=cwd
 if not aN.is_dir():raise ValueError(f'host session workspace does not exist: {aN}')
 if aN==bR or a0(aN,bR):raise ValueError(f'present_path must not fall inside the skill directory ({aN}). It must be delivered to the session workspace root, otherwise the WorkBuddy sidebar will not expand the artifact preview.')
 return aN
def aR(z,aH):
 aN=aQ();bh=(aN/aH).resolve()
 if a0(bh,E)or bh.parent==E.resolve():raise ValueError(f'refusing to write into the skill directory: {bh}')
 shutil.copy2(z,bh);return bh
def bf(report_file,h):
 if not report_file.is_file()or report_file.stat().st_size<20:return rs.reject_with_next(f'step skipped: missing the written draft {report_file}; write raw_writer.md per WRITER_SYSTEM first','need_write',report_file=str(report_file))
 try:
  K=report_file.read_text(encoding='utf-8');_assert_writer_structure(K)
 except ValueError as cd:
  return rs.reject_with_next(f'step skipped: {cd}','need_write',report_file=str(report_file))
 a=None
 try:
  (session,G)=an();a=P(session,h);aq=ensure_report.required_public_web_refs(K);bG=len(rs.collect_public_web_urls(a))
  if bG<aq:return rs.reject_with_next(f'step skipped: not enough public web URLs ({bG}/{aq}). At least 2 openable http(s) URLs must be written to host_web_sources.json; writing "(Source: public reporting)" requires a supporting web page.','need_web_sources',charts_dir=str(a),report_file=str(report_file))
  Y=a/'chart-payloads.json';C=charts.write_chart_payloads(G,Y,report_text=K);bs=str(C.get('report_text')or '')
  if bs and bs!=K:
   report_file.write_text(bs,encoding='utf-8');K=bs
 except ValueError as cd:
  bV=str(cd)
  if 'K 线' in bV or 'price_technical' in bV:return rs.reject_with_next(f'step skipped: {bV}','need_phase_b',charts_dir=str(a)if a is not None else h,report_file=str(report_file))
  if 'revenue_mix' in bV or '产品收入' in bV or 'Revenue mix' in bV or('host_revenue_' in bV):return rs.reject_with_next(f'step skipped: {bV}','need_write',charts_dir=str(a)if a is not None else h,report_file=str(report_file))
  return rs.reject_with_next(f'step skipped: {bV}','need_dump',charts_dir=str(a)if a is not None else h,report_file=str(report_file))
 except OSError as cd:
  print(f'dump failed: {cd}',file=sys.stderr);return 3
 e=C.get('suggested_chart_slugs')or[]
 if charts.MANDATORY_KLINE_SLUG not in e:return rs.reject_with_next('step skipped: suggested is missing the mandatory candlestick price_technical. Re-run Phase B to fetch daily candles and re-run --dump-payloads.','need_phase_b',charts_dir=str(a),report_file=str(report_file))
 if charts.MANDATORY_PRODUCT_PIE_SLUG not in e:return rs.reject_with_next('step skipped: suggested is missing the mandatory product revenue pie revenue_mix. Ask the model to read ### Revenue mix, then write charts_dir/host_revenue_mix.json ({"parts":[{"name":"Business name","value":12.34},…]}, ≥2 sectors) and re-run --dump-payloads.','need_write',charts_dir=str(a),report_file=str(report_file))
 if len(e)<2:
  print(f'not enough suggested charts available: only {len(e)} charts; at least 2 are required to keep rendering.',file=sys.stderr);return 3
 b3=C.get('mandatory_pie_slugs')or[s for s in e if s in charts.MANDATORY_PIE_SLUGS];bC=a/'chart_contracts.json';rs.set_phase('need_render',hint='dump_ok');am={'ok':True,'mode':'dump-payloads','payloads':str(Y),'contracts':str(bC),'charts_dir':str(a),'available':C.get('available_slugs')or[],'suggested_charts':e,'mandatory_kline_slug':charts.MANDATORY_KLINE_SLUG,'mandatory_product_pie_slug':charts.MANDATORY_PRODUCT_PIE_SLUG,'mandatory_pie_slugs':b3,'instruction':'execute next_action only: run --render-all directly. chart_contracts.json already holds the values plus title/caption/unit; price_technical + revenue_mix are mandatory; the Agent must not hand-write {slug}.option.json or change any number; the script fills the template from the contract to build the option and render.'};print(json.dumps(rs.attach_next_action(am,'need_render',charts_dir=str(a),report_file=str(report_file)),ensure_ascii=False));return 0
def bt(h):
 try:
  client_common.load_skill_env();session=client_common.load_session();a=P(session,h)
  if not(a/'chart-payloads.json').is_file():return rs.reject_with_next('step skipped: --dump-payloads has not run yet','need_dump',charts_dir=str(a))
  w(a);e=ag(a)
  if charts.MANDATORY_KLINE_SLUG not in e:return rs.reject_with_next('step skipped: suggested is missing the mandatory candlestick price_technical; please re-run --dump-payloads.','need_dump',charts_dir=str(a))
  if len(e)>charts.MAX_SUGGESTED_CHARTS:raise ValueError(f'too many suggested charts: {len(e)} charts (limit {charts.MAX_SUGGESTED_CHARTS}). Please re-run --dump-payloads.')
  if len(e)<2:raise ValueError(f'not enough suggested charts available: only {len(e)} charts; at least 2 are required. Please re-run --dump-payloads.')
  bl=charts.load_chart_contracts(a);aJ=[s for s in e if s not in bl]
  if aJ:return rs.reject_with_next('step skipped: missing chart_contracts: '+', '.join(aJ)+'. Please re-run --dump-payloads.','need_dump',charts_dir=str(a))
  for slug in e:
   if slug not in charts.MANDATORY_PIE_SLUGS:continue
   cB=str((bl.get(slug)or{}).get('type')or '')
   if cB!='pie':return rs.reject_with_next(f'step skipped: {slug} must be a pie contract (proportional data); please re-run --dump-payloads.','need_dump',charts_dir=str(a))
  ad();bP=[]
  for slug in e:
   bv=bl.get(slug)or{}
   try:
    aS=charts.build_option_from_contract(bv)
   except ValueError as cd:
    return rs.reject_with_next(f'contract template fill failed: {cd}','need_dump',charts_dir=str(a))
   aS=B(aS);bw=charts.contract_decimals(bv)
   if bw>0:bw=2
   aS=charts.canonicalize_option_decimals(aS,bw)
   try:
    charts.assert_option_matches_contract(aS,bv)
   except ValueError as cd:
    return rs.reject_with_next(f'contract validation failed: {cd}','need_dump',charts_dir=str(a))
   if not Q(aS):raise ValueError(f'{slug} no drawable series after template fill. Check the contract and re-run --dump-payloads.')
   aj=a/f'{slug}.option.json';j=a/f'{slug}.html';aj.write_text(json.dumps(aS,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');bi(aj,j);bP.append(slug)
  u(a,e);ar=W(a);J(a,e)
 except(OSError,ValueError,RuntimeError,FileNotFoundError)as cd:
  print(f'render-all failed: {cd}',file=sys.stderr);return 3
 rs.set_phase('need_assemble',hint='render_ok');am={'ok':True,'mode':'render-all','charts_dir':str(a),'rendered':bP,'echarts':str(ar)};print(json.dumps(rs.attach_next_action(am,'need_assemble',charts_dir=str(a)),ensure_ascii=False));return 0
def bg(report_file,h):
 if not report_file.is_file():return rs.reject_with_next(f'step skipped: missing the written draft {report_file}','need_write',report_file=str(report_file))
 try:
  K=report_file.read_text(encoding='utf-8');_assert_writer_structure(K);(session,G)=an();a=P(session,h);w(a);e=ag(a)
  if charts.MANDATORY_KLINE_SLUG not in e:return rs.reject_with_next('step skipped: suggested is missing the mandatory candlestick price_technical; please re-run --dump-payloads.','need_dump',charts_dir=str(a),report_file=str(report_file))
  if charts.MANDATORY_PRODUCT_PIE_SLUG not in e:return rs.reject_with_next('step skipped: suggested is missing the mandatory product revenue pie revenue_mix; fill in ### Revenue mix and re-run --dump-payloads.','need_write',charts_dir=str(a),report_file=str(report_file))
  u(a,e)
  if len(e)>charts.MAX_SUGGESTED_CHARTS:
   print(f'too many suggested charts: {len(e)} charts (limit {charts.MAX_SUGGESTED_CHARTS}). Please re-run --dump-payloads.',file=sys.stderr);return 3
  if len(e)<1:return rs.reject_with_next('not enough suggested charts available: run --dump-payloads first','need_dump',charts_dir=str(a),report_file=str(report_file))
  bZ=[slug for slug in e if not(a/f'{slug}.html').is_file()]
  if bZ:return rs.reject_with_next(f"step skipped: interactive charts missing {', '.join(bZ)}; run --render-all first",'need_render',charts_dir=str(a),report_file=str(report_file))
  J(a,e);g=av(a,e);aE=len(g)
  if aE>charts.MAX_SUGGESTED_CHARTS:
   print(f'too many embedded charts: {aE} charts (limit {charts.MAX_SUGGESTED_CHARTS}).',file=sys.stderr);return 3
  if aE<1:
   print('not enough interactive charts: nothing drawable to embed (empty or all-zero series removed; no chart beats a blank one).',file=sys.stderr);return 3
  ax=[slug for(slug,_)in g.values()]
  if charts.MANDATORY_KLINE_SLUG not in ax:return rs.reject_with_next('step skipped: the final draft does not embed the mandatory candlestick price_technical (it must follow ### Relative strength). Check option/html then run --render-all.','need_render',charts_dir=str(a),report_file=str(report_file))
  if charts.MANDATORY_PRODUCT_PIE_SLUG not in ax:return rs.reject_with_next('step skipped: the final draft does not embed the mandatory product revenue pie revenue_mix (it must follow ### Revenue mix). Fill in the shares and run --dump-payloads / --render-all.','need_write',charts_dir=str(a),report_file=str(report_file))
  bH=bJ(K,G);F=b2(bH);aa=charts.collect_data_sources(G,charts_dir=a,report_md=F);aq=ensure_report.required_public_web_refs(F);b0=len(rs.collect_public_web_urls(a))
  if len(aa)<aq or b0<aq:return rs.reject_with_next(f'step skipped: not enough public web URLs (assemble entries {len(aa)}, host file URLs {b0}; need ≥{aq}). Only ≥2 counts; complete host_web_sources.json, then --mark-web-sources, then assemble.','need_web_sources',charts_dir=str(a),report_file=str(report_file))
  aV=charts.limit_reference_entries(aa);charts.write_references_artifacts(a,aV);F=charts.inject_references_section(F,aV)
  if '## References' not in F:raise ValueError('assembly failed: the final draft is missing "## References"')
  title=aZ(aY(F),G);bU=be(F,g,a,title);z=(a/'report.html').resolve();z.write_text(bU,encoding='utf-8');X(z,ax);b4=z.read_text(encoding='utf-8')
  if 'References' not in b4:raise ValueError('assembly failed: report.html does not contain "References"')
  aH=a8(title,G);present_path=aR(z,aH)
 except(OSError,ValueError,RuntimeError,FileNotFoundError)as cd:
  print(f'assemble-html failed: {cd}',file=sys.stderr);return 3
 bX=str(z.resolve());aC=str(present_path.resolve());rs.set_phase('need_present',hint='assemble_ok',extra={'present_path':aC});am={'ok':True,'mode':'assemble-html','report':bX,'present_path':aC,'htmlFilePath':aC,'htmlFileName':present_path.name,'charts':aE,'self_contained':True,'references':len(aa),'references_json':str((a/'references.json').resolve()),'instruction':f'execute next_action only: give present_path to the user (attach the file when the host supports it) plus the absolute path in chat; afterwards {os_compat.py_cmd()} scripts/research_progress.py --mark-presented'};print(json.dumps(rs.attach_next_action(am,'need_present',present_path=aC,charts_dir=str(a),report_file=str(report_file)),ensure_ascii=False));return 0
def main():
 y=argparse.ArgumentParser(description='Prepare interactive HTML deep-research report (dump / render-all / assemble-html)');y.add_argument('--report-file',default='',help='Step 3 raw report file (required by --dump-payloads / --assemble-html)');y.add_argument('--dump-payloads',action='store_true',help='Export chart-payloads.json only');y.add_argument('--render-all',action='store_true',help='Build options from chart_contracts and render all suggested slugs to HTML');y.add_argument('--assemble-html',action='store_true',help='Assemble interactive HTML report from rendered chart HTML files');y.add_argument('--charts-dir',default='',help='Charts / payloads directory');args=y.parse_args();cy=sum((1 for cK in(args.dump_payloads,args.render_all,args.assemble_html)if cK))
 if cy!=1:
  print('exactly one of these must be given: --dump-payloads / --render-all / --assemble-html',file=sys.stderr);return 2
 if args.render_all:return bt(args.charts_dir)
 if not args.report_file:
  print('--dump-payloads / --assemble-html requires --report-file',file=sys.stderr);return 2
 report_file=Path(args.report_file).resolve()
 if not report_file.is_file():return rs.reject_with_next(f'step skipped: the report file does not exist {report_file}','need_write',report_file=str(report_file))
 if args.dump_payloads:return bf(report_file,args.charts_dir)
 return bg(report_file,args.charts_dir)
if __name__=='__main__':sys.exit(main())
