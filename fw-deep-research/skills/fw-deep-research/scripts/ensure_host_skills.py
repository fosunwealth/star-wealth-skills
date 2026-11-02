import argparse;import json;import shutil;import subprocess;import sys;from pathlib import Path;from typing import Any,Dict,List,Optional,Tuple;SCRIPT_DIR=Path(__file__).resolve().parent;sys.path.insert(0,str(SCRIPT_DIR));import os_compat;n=Path.home()/'.workbuddy'/'skills';w=Path.home()/'bin';s=Path.home()/'.workbuddy'/'binaries';C='westock-data-skillhub@1.0.5';o=n/'westock-data';q=n/'neodata-financial-search';d=q/'scripts'/'query.py';b='install the westock-data skill from the WorkBuddy skill marketplace';c='install the neodata-financial-search skill from the WorkBuddy skill marketplace';r='call connect_cloud_service for a tempToken, then rerun with --save-token'
def y(x,*,timeout=90):
 u=list(x)
 if u:u[0]=os_compat.resolve_exe(u[0])
 try:
  B=subprocess.run(u,capture_output=True,text=True,timeout=timeout,check=False)
 except(OSError,subprocess.TimeoutExpired)as e:
  return(1,'',str(e))
 return(B.returncode,(B.stdout or '').strip(),(B.stderr or '').strip())
def i():
 z=shutil.which('westock-data')
 if z:return z
 name=os_compat.westock_shim_basename()
 for p in(w/name,s/name,o/'scripts'/name):
  if os_compat.is_runnable_file(p):return str(p)
 return None
def j():
 x=i();result={'cmd':x,'search_ok':False,'rating_ok':False,'detail':''}
 if not x:
  result['detail']=b;return result
 (rc,E,F)=y([x,'search','招商银行'],timeout=90);text=E or F;result['search_ok']=rc==0 and 'hk03968' in text and('code' in text.lower())
 if not result['search_ok']:
  result['detail']=text[:240];return result
 (J,H,I)=y([x,'rating','hk03968'],timeout=90);t=H or I;result['rating_ok']=J==0 and('targetPriceAvg' in t or 'Price target' in t)
 if not result['rating_ok']:result['detail']=t[:240]
 return result
def f(stdout):
 raw=(stdout or '').strip()
 if not raw:return False
 try:
  start=raw.find('{');data=json.loads(raw[start:]if start>=0 else raw)
 except(json.JSONDecodeError,TypeError,ValueError):
  return '"suc": true' in raw.replace(' ','').lower()or '"code":"200"' in raw.replace(' ','')
 if data.get('suc')in(True,'true',1,'1'):return True
 return str(data.get('code'))=='200'
def k():
 result={'skill_present':d.is_file(),'query_ok':False,'detail':''}
 if not result['skill_present']:
  result['detail']=c;return result
 (rc,E,F)=y([sys.executable,str(d),'--query','招商银行最新股价'],timeout=60);result['query_ok']=f(E)
 if not result['query_ok']:result['detail']=(F or E)[:240]or f'exit={rc}'
 return result
def l():
 a=j();ok=bool(a.get('search_ok')and a.get('rating_ok'));return{'ok':ok,'hint':'' if ok else a.get('detail')or b,'probe':a}
def m():
 a=k();ok=bool(a.get('query_ok'))
 if ok:hint=''
 elif not a.get('skill_present'):hint=c
 elif 'TOKEN_MISSING' in str(a.get('detail'))or 'AUTH_ERROR' in str(a.get('detail')):hint=r
 else:hint=a.get('detail')or 'query_failed'
 return{'ok':ok,'hint':hint,'probe':a}
def main():
 v=argparse.ArgumentParser(description='Check the westock-data / neodata host skills (read-only)');v.add_argument('--allow-neodata-degraded',action='store_true',help='exit 0 when westock works and neodata is missing or broken (neodata only fills gaps)');args=v.parse_args();g=l();h=m();D=bool(g.get('ok'))and(bool(h.get('ok'))or args.allow_neodata_degraded);A={'westock':g,'neodata':h,'ok':D};print(json.dumps(A,ensure_ascii=False))
 if not g.get('ok'):
  print(f"westock-data unavailable: {g.get('hint')}",file=sys.stderr);return 1
 if not h.get('ok')and(not args.allow_neodata_degraded):
  print(f"neodata unavailable: {h.get('hint')}",file=sys.stderr);return 1
 return 0
if __name__=='__main__':raise SystemExit(main())
