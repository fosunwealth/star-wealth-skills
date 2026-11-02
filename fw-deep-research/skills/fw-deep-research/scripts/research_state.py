import json;import sys;from pathlib import Path;from typing import Any,Dict,List,Optional;import client_common;import os_compat;i=('need_activation','need_start','need_read_prompts','need_phase_a','need_phase_b','need_host_packs','need_web_sources','need_write','need_dump','need_render','need_assemble','need_present','done');MIN_PUBLIC_WEB_REFS=2;SKILL_ROOT=client_common.SKILL_ROOT;q=(SKILL_ROOT/'raw_writer.md',Path.cwd()/'raw_writer.md')
def try_load_session():
 if not client_common.SESSION_FILE.is_file():return None
 try:
  data=json.loads(client_common.SESSION_FILE.read_text(encoding='utf-8'))
 except(OSError,json.JSONDecodeError):
  return None
 return data if isinstance(data,dict)else None
def N(session=None):
 b=session if session is not None else try_load_session()
 if not b:return 'need_activation'
 phase=str(b.get('phase')or '').strip()
 if phase=='need_options':return 'need_render'
 if phase in i:return phase
 return 'need_start'
def set_phase(phase,*,hint='',extra=None):
 if phase not in i:raise ValueError(f'unknown phase: {phase}')
 b=try_load_session()
 if b is None:return{'phase':phase,'phase_hint':hint}
 b['phase']=phase
 if hint:b['phase_hint']=hint
 if extra:
  for(k,v)in extra.items():
   b[k]=v
 client_common.save_session(b);return b
def _charts_dir(session):
 if not session:return None
 raw=str(session.get('charts_dir')or '').strip()
 if not raw:
  ac=str(session.get('session_id')or '').strip()
  if ac:return client_common.ensure_artifacts_dir()/f'{ac}.charts'
  return None
 return Path(raw)
def j():
 for path in q:
  if path.is_file()and path.stat().st_size>20:return path.resolve()
 return None
def r(session,charts):
 H={}
 for(key,name)in(('writer_system_path','writer_system.md'),('writer_input_path','writer_input.md'),('playbook_path','playbook.md'),('capabilities_path','capabilities.json')):
  raw=str(session.get(key)or '').strip()
  if raw:H[key]=Path(raw)
  elif charts is not None:H[key]=charts/'prompts'/name
 return H
def y(charts):
 l=charts/'chart-payloads.json'
 if not l.is_file():return[]
 try:
  data=json.loads(l.read_text(encoding='utf-8'))
 except(OSError,json.JSONDecodeError):
  return[]
 e=data.get('suggested_chart_slugs')
 if isinstance(e,list)and e:return[str(s)for s in e]
 return[]
def t(charts,e):
 if not e:return False
 path=charts/'chart_contracts.json'
 if not path.is_file():return False
 try:
  data=json.loads(path.read_text(encoding='utf-8'))
 except(OSError,json.JSONDecodeError):
  return False
 B=data.get('contracts')if isinstance(data,dict)else None
 if not isinstance(B,dict):return False
 return all((s in B for s in e))
def z(charts,e):
 if not e:return False
 return all(((charts/f'{s}.html').is_file()for s in e))
def host_packs_ready(charts):
 for name in('host_institutional_views.json','host_fundamentals_pack.json'):
  path=charts/name
  if path.is_file()and path.stat().st_size>20:return True
 return False
def o(ad):
 u=(ad or '').strip().rstrip('.,;，。；')
 if not u.startswith(('http://','https://'))or len(u)<12:return False
 ae=u.lower()
 if any((m in ae for m in('...','example.com','example.org','localhost','占位'))):return False
 return True
def collect_public_web_urls(charts):
 X=set();I=[]
 def R(raw):
  if isinstance(raw,dict):u=str(raw.get('url')or '').strip()
  else:u=str(raw or '').strip()
  if not o(u)or u in X:return
  X.add(u);I.append(u)
 n=charts/'host_web_sources.json'
 if n.is_file():
  try:
   data=json.loads(n.read_text(encoding='utf-8'))
  except(OSError,json.JSONDecodeError):
   data=None
  if isinstance(data,list):
   for L in data:
    R(L)
  elif isinstance(data,dict):
   for key in('sources','items','urls'):
    V=data.get(key)
    if isinstance(V,list):
     for L in V:
      R(L)
 for path in sorted(charts.glob('host_*.json')):
  if path.name=='host_web_sources.json':continue
  try:
   Y=json.loads(path.read_text(encoding='utf-8'))
  except(OSError,json.JSONDecodeError):
   continue
  if not isinstance(Y,dict):continue
  raw=Y.get('sources')
  if isinstance(raw,list):
   for L in raw:
    R(L)
 return I
def public_web_sources_ready(charts,*,Z=MIN_PUBLIC_WEB_REFS):return len(collect_public_web_urls(charts))>=Z
def d(session,tool):
 h=str(session.get('trace_file')or '').strip()
 if not h:return False
 path=Path(h)
 if not path.is_file():return False
 try:
  for J in path.read_text(encoding='utf-8').splitlines():
   if not J.strip():continue
   try:
    M=json.loads(J)
   except json.JSONDecodeError:
    continue
   if isinstance(M,dict)and M.get('tool')==tool:
    if M.get('ok')is False:continue
    result=M.get('result')
    if result:return True
 except OSError:
  return False
 return False
def f(session):
 h=str(session.get('trace_file')or '').strip()
 if not h:return None
 path=Path(h)
 if not path.is_file():return None
 try:
  aa=path.read_text(encoding='utf-8').splitlines()
 except OSError:
  return None
 for J in reversed(aa):
  if not J.strip():continue
  try:
   M=json.loads(J)
  except json.JSONDecodeError:
   continue
  if not isinstance(M,dict)or M.get('tool')!='resolve_symbol':continue
  result=M.get('result')
  if isinstance(result,str):
   try:
    result=json.loads(result)
   except json.JSONDecodeError:
    continue
  if not isinstance(result,dict):continue
  code=str(result.get('preferred_code')or '').strip()
  if code:return code
  G=result.get('candidates')
  if isinstance(G,list)and G and isinstance(G[0],dict):
   c=str(G[0].get('code')or '').strip()
   if c:return c
 return str(session.get('preferred_code')or '').strip()or None
def g(phase,session=None,*,preferred_code='',charts_dir='',report_file='',present_path=''):
 py=os_compat.py_cmd();b=session if session is not None else try_load_session()or{};charts=Path(charts_dir)if charts_dir else _charts_dir(b);a=str(charts)if charts else '';code=preferred_code or f(b)or '';T=code or '<ticker>';D=report_file or str(j()or 'raw_writer.md')
 if phase=='need_activation':return{'id':'activate','do':'run','command':f'{py} fintrust_gate/activation_gate.py','done_when':'exit_code==0'}
 if phase=='need_start':return{'id':'start_research','do':'run','command':f"{py} scripts/start_research.py --query '<latest user question>'",'done_when':'session.json and prompts exist'}
 if phase=='need_read_prompts':
  w=r(b,charts);ab=[str(w[k])for k in('writer_system_path','playbook_path','writer_input_path')if w.get(k)];return{'id':'read_prompts','do':'Read','paths':ab,'done_when':'Read writer_system.md and playbook.md in full','then_mark':f'{py} scripts/research_progress.py --mark-read-prompts'}
 if phase=='need_phase_a':return{'id':'resolve_symbol','do':'run','command':f"""{py} scripts/run_tool.py resolve_symbol '{{"query":"<name>"}}'""",'done_when':'stdout has preferred_code or candidates'}
 if phase=='need_phase_b':return{'id':'run_phase_b','do':'run','command':f"{py} scripts/run_phase_b.py --code '{T}'",'done_when':'stdout ok=true and price_technical available'}
 if phase=='need_host_packs':return{'id':'host_packs','do':'run','command':f'westock-data rating {T} && fill host_deep_profile.json / host_fundamentals_pack.json / host_institutional_views.json then {py} scripts/research_progress.py --mark-host-packs','paths':[a]if a else[],'done_when':'host_*.json written and --mark-host-packs run'}
 if phase=='need_web_sources':
  n=str(Path(a)/'host_web_sources.json')if a else '';wp=n or 'charts_dir/host_web_sources.json';return{'id':'write_web_sources','do':'Write','command':f'Write {wp} with >={MIN_PUBLIC_WEB_REFS} openable http(s) URLs, then {py} scripts/research_progress.py --mark-web-sources','paths':[p for p in(n,a)if p],'min_urls':MIN_PUBLIC_WEB_REFS,'done_when':f'host_web_sources.json has >={MIN_PUBLIC_WEB_REFS} URLs'}
 if phase=='need_write':return{'id':'write_report','do':'Write','path':D,'command':'Write raw_writer.md in English per SKILL.md (Key takeaways + In-depth analysis + six modules, ### Relative strength, ### Revenue mix + host_revenue_mix.json, ### Peer comparison + host_peer_radar.json, inline (Source: ...) citations).','done_when':'raw_writer.md and host JSON files are written'}
 if phase=='need_dump':return{'id':'dump_payloads','do':'run','command':f'{py} scripts/prepare_report.py --report-file {D} --dump-payloads'+(f' --charts-dir {a}' if a else ''),'done_when':'stdout ok=true'}
 if phase=='need_render':
  cp=str(Path(a)/'chart_contracts.json')if a else '';return{'id':'render_all','do':'run','command':f'{py} scripts/prepare_report.py --render-all'+(f' --charts-dir {a}' if a else ''),'paths':[p for p in(cp,a)if p],'done_when':'stdout ok=true'}
 if phase=='need_assemble':return{'id':'assemble_html','do':'run','command':f"{os_compat.assemble_env_prefix('<skill root>')}{py} scripts/prepare_report.py --report-file {D} --assemble-html"+(f' --charts-dir {a}' if a else ''),'done_when':'stdout has present_path'}
 if phase=='need_present':return{'id':'deliver_file','do':'deliver_file','present_path':present_path or str(b.get('present_path')or ''),'command':'give present_path to the user (attach the file when the host supports it), then give the full absolute path and one or two sentences','done_when':'delivered'}
 return{'id':'done','do':'none','command':'','done_when':'delivered'}
def infer_phase(session=None):
 blockers=[];b=session if session is not None else try_load_session()
 if b is None:return('need_activation',blockers)
 charts=_charts_dir(b);w=r(b,charts);ws=w.get('writer_system_path');pb=w.get('playbook_path')
 if not ws or not ws.is_file()or(not pb)or(not pb.is_file()):return('need_start',['missing prompts/writer_system.md or playbook.md'])
 if not b.get('prompts_read'):return('need_read_prompts',[])
 code=f(b)
 if not code:return('need_phase_a',[])
 C=d(b,'market_snapshot')or d(b,'deep_profile')or d(b,'price_technical')
 if not C:return('need_phase_b',[])
 if charts is None:return('need_phase_b',['missing charts_dir'])
 A=N(b);O=bool(b.get('host_packs_done'))or(A in i and i.index(A)>=i.index('need_web_sources'))
 if not host_packs_ready(charts)and(not O):return('need_host_packs',[])
 Q=bool(b.get('web_sources_done'))or(A in i and i.index(A)>=i.index('need_write'))
 if not public_web_sources_ready(charts)and(not Q):return('need_web_sources',[f'missing ≥{MIN_PUBLIC_WEB_REFS} public web URLs (host_web_sources.json)'])
 W=j()
 if not W:return('need_write',['missing raw_writer.md'])
 l=charts/'chart-payloads.json'
 if not l.is_file():return('need_dump',[])
 e=y(charts)
 if not e:return('need_dump',['chart-payloads has no suggested_chart_slugs'])
 if not t(charts,e):return('need_dump',['chart_contracts is incomplete; please re-run --dump-payloads'])
 if not z(charts,e):return('need_render',[])
 U=str(b.get('present_path')or '').strip();E=charts/'report.html'
 if not E.is_file()or not U:return('need_assemble',[])
 if not b.get('presented'):return('need_present',[])
 return('done',[])
def progress_payload(*,phase=None,preferred_code='',present_path='',report_file='',blockers=None):
 b=try_load_session()
 if phase is None:
  (phase,x)=infer_phase(b);blockers=list(blockers or[])+x
 else:blockers=list(blockers or[])
 action=g(phase,session=b,preferred_code=preferred_code,present_path=present_path,report_file=report_file);return{'ok':True,'phase':phase,'next_action':action,'blockers':blockers,'session_id':(b or{}).get('session_id'),'instruction':'Run only this next_action. Then you may run research_progress.py again. Do not skip steps. Do not show this JSON to the user. All user-facing text is English.'}
def emit_progress(l):print(json.dumps(l,ensure_ascii=False,indent=2))
def attach_next_action(data,phase,**F):
 H=dict(data);H['phase']=phase;H['next_action']=g(phase,**F);H.setdefault('agent_note','execute next_action only; never show this field to the user; run research_progress.py when unsure');return H
def reject_with_next(K,phase,*,P=3,**F):
 print(K,file=sys.stderr);emit_progress(progress_payload(phase=phase,blockers=[K],**F));return P
