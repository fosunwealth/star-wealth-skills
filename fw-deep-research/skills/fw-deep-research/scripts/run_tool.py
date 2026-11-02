import argparse;import json;import sys;import time;from pathlib import Path;sys.path.insert(0,str(Path(__file__).resolve().parent));import client_common;import research_state as rs;_TOOL_TIMEOUT=120
def g(session):return session.get('capabilities')or session.get('tools')or[]
def h(session,name):
 for tool in g(session):
  fn=tool.get('function',{})
  if fn.get('name')==name:return fn
 return None
def main():
 k=argparse.ArgumentParser(description='Deep-research capability client (MCP)');k.add_argument('tool',nargs='?',default='',help='research capability name');k.add_argument('args',nargs='?',default='',help='JSON argument string, e.g. \'{"code": "usGOOGL"}\'');k.add_argument('--list',action='store_true',help='list all research capabilities');k.add_argument('--schema',default='',help='print the argument JSON Schema of the given capability');args=k.parse_args();client_common.load_skill_env();session=client_common.load_session()
 if args.list:
  for(i,tool)in enumerate(g(session),1):
   fn=tool['function'];required=fn['parameters'].get('required',[]);s=fn['parameters'].get('properties',{});r=', '.join((f"{name}{('*' if name in required else '')}" for name in s));print(f"{i:2d}. {fn['name']}({r})");print(f"    {fn['description']}")
  return 0
 if args.schema:
  fn=h(session,args.schema)
  if fn is None:
   print(f'unknown capability: {args.schema}',file=sys.stderr);return 2
  print(json.dumps({'name':fn['name'],'description':fn['description'],'parameters':fn['parameters']},ensure_ascii=False,indent=2));return 0
 if not args.tool:
  k.print_help();return 2
 if args.tool not in client_common.RESEARCH_CAPABILITY_NAMES:
  print(f'unknown capability: {args.tool}. Use --list to see the research capabilities available this time (use start_research.py / finalize_report.py for orchestration).',file=sys.stderr);return 2
 if h(session,args.tool)is None:
  print(f'unknown capability: {args.tool}. Use --list to see the research capabilities available this time.',file=sys.stderr);return 2
 try:
  d=json.loads(args.args)if args.args.strip()else{}
 except json.JSONDecodeError as e:
  print(f'argument is not valid JSON: {e}',file=sys.stderr);return 2
 if not isinstance(d,dict):
  print('the argument must be a JSON object',file=sys.stderr);return 2
 data=client_common.mcp_tool_json(args.tool,d,timeout=_TOOL_TIMEOUT)
 if 'ok' in data and(not data.get('ok')):
  print(data.get('error','capability execution failed'),file=sys.stderr);return 1
 if 'result' in data and('ok' in data or isinstance(data.get('result'),(str,dict,list))):b=data.get('result','')
 else:b=data
 if args.tool=='resolve_symbol':b=j(b,d)
 if not isinstance(b,str):f=json.dumps(b,ensure_ascii=False,default=str)
 else:f=b
 client_common.append_tool_trace({'ts':int(time.time()),'tool':args.tool,'arguments':d,'result':f,'transport':'mcp'})
 if args.tool=='resolve_symbol':
  c=b
  if isinstance(c,str):
   try:
    c=json.loads(c)
   except json.JSONDecodeError:
    c={}
  code=''
  if isinstance(c,dict):
   code=str(c.get('preferred_code')or '').strip()
   if not code:
    o=c.get('candidates')or[]
    if isinstance(o,list)and o and isinstance(o[0],dict):code=str(o[0].get('code')or '').strip()
  if code:
   rs.set_phase('need_phase_b',hint='resolve_ok',extra={'preferred_code':code});q={'ok':True,'tool':'resolve_symbol','preferred_code':code,'result':c if isinstance(c,dict)else f};print(json.dumps(rs.attach_next_action(q,'need_phase_b',preferred_code=code),ensure_ascii=False,indent=2));return 0
  print(f);return 0
 print(f);return 0
def j(b,d):
 import westock_bridge;query=''
 if isinstance(d,dict):query=str(d.get('query')or '').strip()
 c=b
 if isinstance(b,str):
  try:
   c=json.loads(b)
  except json.JSONDecodeError:
   return b
 if not isinstance(c,dict):return b
 m=c.get('candidates')
 if isinstance(m,list)and m:return westock_bridge.enrich_resolve_payload(c,query)
 for p in westock_bridge.query_variants(query)[1:6]:
  try:
   n=client_common.mcp_tool_json('resolve_symbol',{'query':p},timeout=_TOOL_TIMEOUT)
  except SystemExit:
   continue
  a=n
  if isinstance(n,dict)and 'result' in n and('ok' in n):
   a=n.get('result')
   if isinstance(a,str):
    try:
     a=json.loads(a)
    except json.JSONDecodeError:
     continue
  if not isinstance(a,dict):continue
  l=a.get('candidates')
  if isinstance(l,list)and l:
   a=dict(a);a['enrichment']=f'mcp_variant:{p}';return westock_bridge.enrich_resolve_payload(a,query)
 return westock_bridge.enrich_resolve_payload(c,query)
if __name__=='__main__':sys.exit(main())
