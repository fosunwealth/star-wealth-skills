import json;import os;import sys;import threading;import time;from pathlib import Path;from typing import Any,Optional;import requests;SCRIPT_DIR=Path(__file__).resolve().parent;SKILL_ROOT=SCRIPT_DIR.parent;y=Path.home()/'.workbuddy'/'fw-deep-research';SESSION_FILE=y/'.fintrust_session.json';s=SKILL_ROOT/'.fintrust_session.json';u=SKILL_ROOT/'.artifacts'
if str(SKILL_ROOT)not in sys.path:sys.path.insert(0,str(SKILL_ROOT))
if str(SCRIPT_DIR)not in sys.path:sys.path.insert(0,str(SCRIPT_DIR))
from fintrust_gate import find_api_key;from fintrust_gate.activation_gate import service_url;g=30;p=('HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','http_proxy','https_proxy','all_proxy');N={'http':None,'https':None};RESEARCH_CAPABILITY_NAMES=('resolve_symbol','market_snapshot','price_technical','deep_profile','fundamentals_pack','institutional_views','news_catalysts','public_web_context');z=0;A=threading.Lock();w=threading.Lock()
def a():
 for key in p:
  os.environ.pop(key,None)
a()
def load_skill_env():
 a();L=SKILL_ROOT/'.env'
 if not L.is_file():return
 for v in L.read_text(encoding='utf-8').splitlines():
  v=v.strip()
  if not v or v.startswith('#')or '=' not in v:continue
  (key,_,W)=v.partition('=');key=key.strip()
  if key in p:continue
  os.environ.setdefault(key,W.strip().strip('"').strip("'"))
 a()
def d():
 try:
  s.unlink()
 except OSError:
  pass
def save_session(data):
 y.mkdir(parents=True,exist_ok=True);SESSION_FILE.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');d()
def load_session():
 if not SESSION_FILE.is_file():
  print('no research session in progress; run start_research.py to start one.',file=sys.stderr);raise SystemExit(2)
 try:
  return json.loads(SESSION_FILE.read_text(encoding='utf-8'))
 except json.JSONDecodeError:
  print('the session file is corrupted; re-run start_research.py to start a new one.',file=sys.stderr);raise SystemExit(2)
def clear_session():
 try:
  SESSION_FILE.unlink()
 except OSError:
  pass
 d()
def ensure_artifacts_dir():
 u.mkdir(parents=True,exist_ok=True);return u
def append_tool_trace(Y):
 session=load_session();D=session.get('trace_file')
 if not D:return
 E=Path(D);E.parent.mkdir(parents=True,exist_ok=True);v=json.dumps(Y,ensure_ascii=False)+'\n'
 with w:
  with E.open('a',encoding='utf-8')as f:
   f.write(v)
def J(key):return{'X-Api-Key':key}
def mcp_url():
 raw=(os.environ.get('FINTRUST_MCP_URL')or '').strip().strip('"').strip("'")
 if raw:return raw.rstrip('/')
 return f"{service_url().rstrip('/')}/mcp"
def K():
 global z
 with A:
  z+=1;return z
def h(B,k):
 try:
  from fintrust_gate.activation_gate import guide_url;F=f'Get an fsk_ key from the signup page: {guide_url()}'
 except Exception as e:
  F=str(e)
 if B==401:
  print(k or f'API key missing or rejected. {F}',file=sys.stderr);raise SystemExit(4)
 if B==503:
  print(k or 'The API key check is unavailable. Try again later',file=sys.stderr);raise SystemExit(5)
 if B==429:
  print(k or 'The quota is used up. Try again tomorrow.',file=sys.stderr);raise SystemExit(5)
 if B in(404,410):
  clear_session();print(f"{k or 'MCP endpoint unavailable'} (the local session handle has been cleaned up)",file=sys.stderr);raise SystemExit(5)
 print(k or f'service error (HTTP {B}); please retry later.',file=sys.stderr);raise SystemExit(1)
def l(i):
 try:
  data=i.json()
  if isinstance(data,dict):
   if data.get('detail'):return str(data['detail'])
   M=data.get('error')
   if isinstance(M,dict)and M.get('message'):return str(M['message'])
 except(ValueError,AttributeError):
  pass
 return(i.text or '')[:200]
def o(i):
 V=(i.headers.get('content-type')or '').lower();text=i.text or ''
 if 'text/event-stream' in V or text.lstrip().startswith('event:'):
  for v in text.splitlines():
   if v.startswith('data:'):
    R=v[5:].strip()
    if not R:continue
    try:
     O=json.loads(R)
    except json.JSONDecodeError:
     continue
    if isinstance(O,dict)and('result' in O or 'error' in O):return O
  print('unable to parse the MCP SSE response',file=sys.stderr);raise SystemExit(1)
 try:
  O=i.json()
 except ValueError:
  print('MCP response is not valid JSON',file=sys.stderr);raise SystemExit(1)
 if not isinstance(O,dict):
  print('MCP response has an unexpected format',file=sys.stderr);raise SystemExit(1)
 return O
q=frozenset({502,503,504});b=3
def G(method,P=None,*,timeout=g,x=False):
 (key,_)=find_api_key();aa=mcp_url();headers={**J(key),'Content-Type':'application/json','Accept':'application/json, text/event-stream'};j=None;i=None
 for r in range(b):
  body={'jsonrpc':'2.0','method':method}
  if not x:body['id']=K()
  if P is not None:body['params']=P
  try:
   a()
   with requests.Session()as session:
    session.trust_env=False;session.headers.clear();i=session.post(aa,json=body,headers=headers,timeout=timeout,proxies=N)
  except requests.RequestException as e:
   j=e
   if r+1<b:
    time.sleep(0.8*2**r);continue
   print(f'The service is unreachable. Check the network and retry.({e})',file=sys.stderr);raise SystemExit(5)
  assert i is not None
  if x:
   if i.status_code in(200,202,204):return None
   if i.status_code in q and r+1<b:
    time.sleep(0.8*2**r);continue
   h(i.status_code,l(i))
  if i.status_code in q and r+1<b:
   time.sleep(0.8*2**r);continue
  if i.status_code!=200:h(i.status_code,l(i))
  break
 else:
  if j is not None:
   print(f'The service is unreachable. Check the network and retry.({j})',file=sys.stderr);raise SystemExit(5)
  h(502,'the gateway failed repeatedly')
 assert i is not None;I=o(i)
 if I.get('error'):
  M=I['error'];T=M.get('message')if isinstance(M,dict)else str(M);data=M.get('data')if isinstance(M,dict)else None;k=f'{T}'+(f': {data}' if data else '')
  if '额度' in k or 'quota' in k.lower():
   print(k,file=sys.stderr);raise SystemExit(5)
  print(k or 'MCP call failed',file=sys.stderr);raise SystemExit(1)
 return I.get('result')
def H(name,m=None,*,timeout=g):
 result=G('tools/call',{'name':name,'arguments':m or{}},timeout=timeout)
 if not isinstance(result,dict):
  print(f'MCP tools/call {name} returned an error',file=sys.stderr);raise SystemExit(1)
 if result.get('isError'):
  C=result.get('content')or[];U=[]
  for c in C:
   if isinstance(c,dict)and c.get('text'):U.append(str(c['text']))
  print('; '.join(U)or f'tool error: {name}',file=sys.stderr);raise SystemExit(1)
 C=result.get('content')or[]
 for c in C:
  if isinstance(c,dict)and c.get('type','text')=='text' and('text' in c):return str(c['text'])
 print(f'MCP tools/call {name} has no text content',file=sys.stderr);raise SystemExit(1)
def mcp_tool_json(name,m=None,*,timeout=g):
 text=H(name,m,timeout=timeout)
 try:
  data=json.loads(text)
 except json.JSONDecodeError:
  print(f'MCP tool {name} returned non-JSON: {text[:200]}',file=sys.stderr);raise SystemExit(1)
 if not isinstance(data,dict):
  print(f'MCP tool {name} returned a non-object',file=sys.stderr);raise SystemExit(1)
 return data
def mcp_prompt_text(name,m=None,*,timeout=g):
 result=G('prompts/get',{'name':name,'arguments':m or{}},timeout=timeout)
 if not isinstance(result,dict):
  print(f'MCP prompts/get {name} returned an error',file=sys.stderr);raise SystemExit(1)
 parts=[]
 for T in result.get('messages')or[]:
  if not isinstance(T,dict):continue
  n=T.get('content')
  if isinstance(n,str):parts.append(n)
  elif isinstance(n,dict)and n.get('text'):parts.append(str(n['text']))
  elif isinstance(n,list):
   for c in n:
    if isinstance(c,dict)and c.get('text'):parts.append(str(c['text']))
 text='\n'.join(parts).strip()
 if not text:
  print(f'MCP prompts/get {name} content is empty',file=sys.stderr);raise SystemExit(1)
 return text
def mcp_tools_as_openai_capabilities(*,research_only=True):
 result=G('tools/list',{});Q=(result or{}).get('tools')if isinstance(result,dict)else None
 if not isinstance(Q,list):return[]
 Z=[]
 for t in Q:
  if not isinstance(t,dict):continue
  name=t.get('name')or ''
  if research_only and name not in RESEARCH_CAPABILITY_NAMES:continue
  Z.append({'type':'function','function':{'name':name,'description':t.get('description')or '','parameters':t.get('inputSchema')or{'type':'object','properties':{}}}})
 return Z
def new_session_id_note():return f'session handle saved at {SESSION_FILE} (deleted after delivery is finalized via --mark-presented); research traffic goes over MCP {mcp_url()}'
