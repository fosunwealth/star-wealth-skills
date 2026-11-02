import argparse;import sys;from pathlib import Path;sys.path.insert(0,str(Path(__file__).resolve().parent));import client_common;import research_state as rs
def main():
 b=argparse.ArgumentParser(description='Research phase → next_action');b.add_argument('--mark-read-prompts',action='store_true',help='mark writer_system + playbook as Read and enter Phase A');b.add_argument('--mark-host-packs',action='store_true',help='mark host_*.json as written and move on to public web source collection');b.add_argument('--mark-web-sources',action='store_true',help='mark host_web_sources.json as complete and move on to writing');b.add_argument('--mark-presented',action='store_true',help='mark the file delivery as done; phase = done');args=b.parse_args();client_common.load_skill_env()
 if args.mark_read_prompts:
  a=rs.try_load_session()
  if a is None:
   print('no research session in progress; run start_research.py first',file=sys.stderr);return 2
  ws=Path(str(a.get('writer_system_path')or ''));pb=Path(str(a.get('playbook_path')or ''))
  if not ws.is_file()or not pb.is_file():return rs.reject_with_next('the prompts file does not exist; run start_research.py first','need_start')
  rs.set_phase('need_phase_a',hint='prompts_read',extra={'prompts_read':True});rs.emit_progress(rs.progress_payload(phase='need_phase_a'));return 0
 if args.mark_host_packs:
  a=rs.try_load_session()
  if a is None:
   print('no research session in progress',file=sys.stderr);return 2
  charts=rs._charts_dir(a)
  if charts is None or not rs.host_packs_ready(charts):return rs.reject_with_next('step skipped: no non-empty host_*.json under charts_dir yet','need_host_packs',charts_dir=str(charts)if charts else '')
  rs.set_phase('need_web_sources',hint='host_packs',extra={'host_packs_done':True});rs.emit_progress(rs.progress_payload(phase='need_web_sources'));return 0
 if args.mark_web_sources:
  a=rs.try_load_session()
  if a is None:
   print('no research session in progress',file=sys.stderr);return 2
  charts=rs._charts_dir(a)
  if charts is None or not rs.public_web_sources_ready(charts):
   n=len(rs.collect_public_web_urls(charts))if charts else 0;return rs.reject_with_next(f'step skipped: not enough public web URLs (currently {n}; need ≥{rs.MIN_PUBLIC_WEB_REFS}). Write host_web_sources.json first, then --mark-web-sources.','need_web_sources',charts_dir=str(charts)if charts else '')
  rs.set_phase('need_write',hint='web_sources',extra={'host_packs_done':True,'web_sources_done':True});rs.emit_progress(rs.progress_payload(phase='need_write'));return 0
 if args.mark_presented:
  a=rs.try_load_session()
  if a is None:
   print('no research session in progress',file=sys.stderr);return 2
  c=str(a.get('present_path')or '').strip()
  if not c:return rs.reject_with_next('missing present_path; run --assemble-html first','need_assemble')
  rs.set_phase('done',hint='presented',extra={'presented':True});rs.emit_progress(rs.progress_payload(phase='done'));client_common.clear_session();return 0
 if rs.try_load_session()is None:
  try:
   from fintrust_gate import find_api_key;(key,_)=find_api_key()
   if not key:
    rs.emit_progress(rs.progress_payload(phase='need_activation'));return 0
  except Exception:
   rs.emit_progress(rs.progress_payload(phase='need_activation'));return 0
  rs.emit_progress(rs.progress_payload(phase='need_start'));return 0
 (phase,blockers)=rs.infer_phase();rs.set_phase(phase,hint='inferred');rs.emit_progress(rs.progress_payload(phase=phase,blockers=blockers));return 0
if __name__=='__main__':sys.exit(main())
