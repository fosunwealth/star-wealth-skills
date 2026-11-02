import sys;from pathlib import Path;sys.path.insert(0,str(Path(__file__).resolve().parent));import client_common;import ensure_report
def main():
 client_common.load_skill_env();session=client_common.load_session();raw=sys.stdin.read()
 if not raw.strip():
  print('stdin is empty: pipe the finished text in, e.g. cat raw.md | python3 finalize_report.py',file=sys.stderr);return 2
 query=str(session.get('resolved_query')or session.get('query')or '').strip()
 try:
  c=ensure_report.ensure_markdown_report(raw,query)
 except ValueError as e:
  print(f'local compliance finalization failed: {e}',file=sys.stderr);return 3
 b=ensure_report.adapt_h1_for_server_finalize(c);data=client_common.mcp_tool_json('finalize_report',{'report':b,'resolved_query':query},timeout=60);a=(data.get('report')or b).strip()
 try:
  a=ensure_report.reconcile_after_server_finalize(a,query)
 except ValueError as e:
  print(f'local re-check failed after server-side finalization: {e}',file=sys.stderr);return 3
 sys.stdout.write(a)
 if a and(not a.endswith('\n')):sys.stdout.write('\n')
 sys.stdout.flush();return 0
if __name__=='__main__':sys.exit(main())
