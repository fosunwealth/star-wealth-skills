import argparse;import json;import sys;import time;from concurrent.futures import ThreadPoolExecutor,as_completed;from pathlib import Path;from typing import Any;sys.path.insert(0,str(Path(__file__).resolve().parent));import client_common;import research_state as rs;_TOOL_TIMEOUT=120;a=('market_snapshot','price_technical','deep_profile','fundamentals_pack','institutional_views','news_catalysts','public_web_context')
def p(name,code,query):
 if name=='public_web_context':return{'query':query}
 return{'code':code}
def c(name,b):
 try:
  data=client_common.mcp_tool_json(name,b,timeout=_TOOL_TIMEOUT);return(data,'',0)
 except SystemExit as e:
  code=e.code if isinstance(e.code,int)else 1;return(None,f'call interrupted (exit {code})',code)
 except Exception as e:
  return(None,(str(e)or e.__class__.__name__)[:300],1)
def q(name,b):
 l=time.time();(data,o,g)=c(name,b)
 if data is None and g not in(4,5):
  time.sleep(0.6);(data,o,g)=c(name,b)
 if data is None:
  client_common.append_tool_trace({'ts':int(time.time()),'tool':name,'arguments':b,'result':'','error':o,'ok':False,'transport':'mcp'});return{'name':name,'ok':False,'error':o,'exit_code':g,'result_chars':0,'elapsed_ms':int((time.time()-l)*1000)}
 if 'ok' in data:
  ok=bool(data.get('ok'));result=data.get('result','');o='' if ok else str(data.get('error')or 'capability execution failed')
 else:
  ok=True;result=data;o=''
 if not isinstance(result,str):result=json.dumps(result,ensure_ascii=False,default=str)
 client_common.append_tool_trace({'ts':int(time.time()),'tool':name,'arguments':b,'result':result if ok else '','error':o or None,'ok':ok,'transport':'mcp'});return{'name':name,'ok':ok,'error':o[:300]if o else '','exit_code':0 if ok else 1,'result_chars':len(result)if ok else 0,'elapsed_ms':int((time.time()-l)*1000)}
def main():
 h=argparse.ArgumentParser(description='Phase B MCP batch (in-process concurrent)');h.add_argument('--code',required=True,help='standard code, e.g. usAAPL / hk00700 / sh600519');h.add_argument('--query',default='',help='query for public_web_context; defaults to --code');h.add_argument('--workers',type=int,default=len(a),help='concurrency (default = number of capabilities)');args=h.parse_args();code=args.code.strip()
 if not code:
  print('--code must not be empty',file=sys.stderr);return 2
 query=(args.query or '').strip()or code;client_common.load_skill_env();session=client_common.load_session();i={(t.get('function')or{}).get('name')for t in session.get('capabilities')or session.get('tools')or[]if isinstance(t,dict)};j=[n for n in a if not i or n in i]
 if not j:
  print('the session has no Phase B research capabilities; re-run start_research.py',file=sys.stderr);return 2
 workers=max(1,min(args.workers,len(j)));f=[];d=None
 with ThreadPoolExecutor(max_workers=workers)as x:
  s={x.submit(q,name,p(name,code,query)):name for name in j}
  for y in as_completed(s):
   v=y.result();f.append(v);ec=v.get('exit_code')
   if ec in(4,5):d=int(ec)
 f.sort(key=lambda r:j.index(r['name'])if r['name']in j else 99);m=sum((1 for r in f if r.get('ok')));u=len(f)-m;k={'ok':m>0,'code':code,'query':query,'total':len(f),'succeeded':m,'failed':u,'capabilities':f,'hint':'results have been written to session traces; fill any failed summary item with a single run_tool.py call as needed; do not exceed mcp_*.json'}
 if m>0 and d is None:
  rs.set_phase('need_host_packs',hint='phase_b_ok',extra={'preferred_code':code});k=rs.attach_next_action(k,'need_host_packs',preferred_code=code)
 print(json.dumps(k,ensure_ascii=False,indent=2))
 if d is not None:return d
 if m==0:return 1
 return 0
if __name__=='__main__':sys.exit(main())
