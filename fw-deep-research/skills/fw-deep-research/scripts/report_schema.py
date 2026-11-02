import json;from pathlib import Path;_P=Path(__file__).resolve().parent.parent/'report_sections.json';_D=None
def _d():
 global _D
 if _D is None:_D=json.loads(_P.read_text(encoding='utf-8'))
 return _D
def required_h2_titles():return list(_d().get('required_h2')or[m['title']for m in _d().get('modules')or[]])
def required_h3_titles():return[(str(m.get('title')or''),str(s))for m in _d().get('modules')or[]if isinstance(m,dict)for s in m.get('subsections')or[]]
def all_h3_titles():return[s for _,s in required_h3_titles()]
def outer_summary_blocks():return[str(x)for x in _d().get('outer_summary_blocks')or[]if str(x).strip()]
