import argparse;import json;import re;import sys;aj='Figures below are computed from public data for information only. This is not a trade instruction or investment advice.'
try:
 import report_schema as _report_schema
except ImportError:
 from pathlib import Path;import sys;sys.path.insert(0,str(Path(__file__).resolve().parent));import report_schema as _report_schema
try:
 from markdown_document import MarkdownDocument,is_horizontal_rule,is_table_separator_line,parse_heading_line,split_table_row;from text_scanner import PhraseMatcher,cleanup_after_removal,collapse_horizontal_whitespace,iter_json_values,parse_inline_sources,split_sentences
except ImportError:
 from.markdown_document import MarkdownDocument,is_horizontal_rule,is_table_separator_line,parse_heading_line,split_table_row;from.text_scanner import PhraseMatcher,cleanup_after_removal,collapse_horizontal_whitespace,iter_json_values,parse_inline_sources,split_sentences
K=tuple(_report_schema.required_h2_titles());J=tuple(_report_schema.all_h3_titles());L={'不构成任何交易指令','仅供信息参考','分析师推荐','推荐评级','推荐趋势','机构推荐','一致推荐','买方推荐','买方分析师推荐','卖方推荐','卖方分析师推荐','Price target'}
for cr in('','任何'):
 for cm in('','投资','交易','操作'):
  L.add(f'not {cr}{cm}advice')
bw=PhraseMatcher(L);d={'强烈推荐','重点推荐','诚意推荐','现在可以买','现在买','我建议','给你的建议','目标仓位','配置比例','仓位建议','抄底','止盈止损','止盈','止损','保证收益','稳赚','潜力股','要不要买','值不值得买','能不能买','能买吗','建议你'}
for aV in('买入','卖出','持有','加仓','减仓','建仓','清仓','抄底','配置','申购','赎回'):
 d.add('advice'+aV);d.add('recommend'+aV)
for aV in('买入','卖出','加仓','减仓','建仓','清仓'):
 d.add(aV+'advice')
for bx in('值得','不值得'):
 for aV in('买','入手','配置'):
  d.add(bx+aV)
for(bx,ce)in(('可以',('买入','卖出','建仓')),('适合',('建仓','买入','定投','配置','布局')),('应当',('买入','卖出','加仓','减仓')),('建议你',('买入','卖出','加仓','减仓','建仓')),('逢低',('布局','买入','建仓'))):
 for aV in ce:
  d.add(bx+aV)
ay=PhraseMatcher(d)
def l(text):
 e=text.split('\n');aS=[];bR=0
 for b in e:
  if b:
   bR=0;aS.append(b)
  else:
   bR+=1
   if bR<=1:aS.append(b)
 return '\n'.join(aS)
def a4(b):
 raw=b.rstrip('\r\n');indent=0
 while indent<len(raw)and raw[indent]==' ':
  indent+=1
 if indent>3:return None
 a=indent
 while a<len(raw)and raw[a]=='#':
  a+=1
 level=a-indent
 if not 1<=level<=6 or a>=len(raw)or raw[a]not in(' ','\t'):return None
 return(level,raw[a:].strip())
def q(b):
 a=0
 while a<len(b)and b[a]in(' ','\t'):
  a+=1
 if a<len(b)and b[a]in('-','*','+'):a+=1
 else:
  start=a
  while a<len(b)and b[a].isdigit():
   a+=1
  if a==start or a>=len(b)or b[a]!='.':return None
  a+=1
 if a>=len(b)or b[a]not in(' ','\t'):return None
 while a<len(b)and b[a]in(' ','\t'):
  a+=1
 return b[:a]
def a5(text):
 body=text.rstrip()
 if not body:return aj
 if '不构成任何交易指令' in body or '不构成投资建议' in body or '不构成任何投资建议' in body or(aj in body):return body
 return f'{body}\n\n{aj}'
def at(ab):
 (o,a1)=ay.remove(ab);o=cleanup_after_removal(o)
 if a1 and(not any(('一'<=aN<='\u9fff' or(aN.isascii()and aN.isalnum())for aN in o))):return('',a1)
 return(o,a1)
def aT(text):
 b7=('buy','overweight','hold','underweight','sell');a=0
 while True:
  start=text.find('rating',a)
  if start<0:return False
  index=start+2
  if index<len(text)and text[index]in('为','是'):index+=1
  while index<len(text)and text[index].isspace():
   index+=1
  if any((text.startswith(ck,index)for ck in b7)):return True
  a=start+2
def H(text):return bool(bw.spans(text))or aT(text)
def br(ab):
 if not ab.strip():return(ab,0)
 spans=ay.spans(ab)
 if not spans:return(ab,0)
 if not H(ab):return('',len(spans))
 return at(ab)
def aA(text):
 if not text:return(aj,0)
 az=0;w=[]
 for b in text.split('\n'):
  heading=a4(b)
  if heading is not None:
   spans=ay.spans(b)
   if spans and(not H(b)):
    az+=1;indent=len(b)-len(b.lstrip(' '));w.append(' '*indent+'#'*heading[0]+' Objective Data Analysis')
   else:w.append(b)
   continue
  V=q(b);spans=ay.spans(b)
  if V and spans and(not H(b)):
   az+=len(spans);continue
  bK=split_sentences(b);ar=[]
  for bd in bK:
   if not bd:continue
   (o,a1)=br(bd);az+=a1
   if o.strip():ar.append(o)
  p=''.join(ar);a2=q(p)
  if a2 and(not p[len(a2):].strip()):continue
  w.append(p)
 body=l('\n'.join(w)).strip();body=a5(body);return(body,az)
aK=tuple(_report_schema.outer_summary_blocks()or('Snapshot','Highlights','Risks','Catalysts'))
def Q(body):
 bH=set(MarkdownDocument(body).heading_titles(3));return[f'### {name}' for name in aK if name not in bH]
Z=('已完成公开信息整理','详见后文In-depth analysis','详见后文Risk signals','以下为客观数据与事实分析，供读者自行判断','数据暂缺：** 详见后文','数据要点：** 详见后文','风险要点：** 详见后文','暂未形成可展示的摘要','公开数据仍在整理中')
def g(n):return any((bL in(n or '')for bL in Z))
def adapt_h1_for_server_finalize(body):
 text=(body or '').strip()
 if not text:return text
 k=MarkdownDocument(text);b8=[heading for heading in k.headings if heading.level==1]
 if len(b8)!=1:return text
 heading=b8[0];title=heading.title.strip()
 if title.startswith(('research note: ','research note: ')):return text
 if not title.endswith('research note'):return text
 ac=title[:-len('research note')].strip()
 if not ac:return text
 E=f'# research note: {ac}\n';return(text[:heading.start]+E+text[heading.end:]).strip()
def aO(body):
 text=(body or '').strip()
 if not text:return text
 k=MarkdownDocument(text);b8=[heading for heading in k.headings if heading.level==1]
 if len(b8)!=1:return text
 heading=b8[0];title=heading.title.strip();ac=''
 for V in('research note: ','research note: '):
  if title.startswith(V):
   ac=title[len(V):].strip();break
 if not ac:return text
 if ac.endswith('research note'):E=f'# {ac}\n'
 else:E=f'# {ac}research note\n'
 return(text[:heading.start]+E+text[heading.end:]).strip()
def B(body):
 text=(body or '').strip()
 if not text:return text
 k=MarkdownDocument(text);aF=k.find_section(2,'Key takeaways')
 if aF is None or not g(aF.text(text)):return text
 bC=k.find_section(2,'In-depth analysis')
 if bC is None:return text
 bX=text[bC.end:].lstrip('\n')
 if not bX.strip():return text
 b3=MarkdownDocument(bX);a_=b3.find_section(2,'Key takeaways')
 if a_ is not None and g(a_.text(bX)):return text
 return bX.strip()
def reconcile_after_server_finalize(body,query):
 bb=B(body);bb=aO(bb);return ensure_markdown_report(bb,query)
def aU(body):
 k=MarkdownDocument(body);by=k.heading_titles(1)
 if len(by)!=1:raise ValueError('Illegal report structure: the whole document must have exactly one H1, in the form "# <name> (<code>) research note" or "# <name>research note". Scripts/models must not add placeholder titles.')
 h1=by[0]
 if not(h1.startswith(('research note: ','research note: '))or h1.endswith('research note')):raise ValueError('Illegal report structure: the H1 must be a short report name (e.g. "Tesla (TSLA) research note"); do not paste the user\'s full question or keyword list into the title.')
 ao=k.heading_titles(2)
 if ao.count('Key takeaways')!=1:raise ValueError('Illegal report structure: there must be exactly one "## Key takeaways" section, immediately followed by "## In-depth analysis" and the six modules; no duplicate summary, no placeholder summary.')
 if 'In-depth analysis' not in ao:raise ValueError('Incomplete report structure: missing "## In-depth analysis". Correct order: Key takeaways → In-depth analysis → Fundamentals…')
 aF=k.find_section(2,'Key takeaways');bC=k.find_section(2,'In-depth analysis');assert aF is not None and bC is not None
 if g(aF.text(body)):raise ValueError('Illegal report structure: placeholder "conclusion first" detected (e.g. "finished compiling public information", "see below"). Write a factual Snapshot/Highlights/Risks/Catalysts per the prompt; no empty shell.')
 if aF.start>bC.start:raise ValueError('Wrong report structure order: "## Key takeaways" must come first, then "## In-depth analysis" and modules such as "## Fundamentals".')
 ba=next((section for section in k.sections(2)if section.heading.title in K),None)
 if ba is not None and bC.start>ba.start:raise ValueError('Wrong report structure order: "## In-depth analysis" must come before the six modules.')
def au(body):
 bH=set(MarkdownDocument(body).heading_titles(2));return[f'## {name}' for name in K if name not in bH]
a6=frozenset({'数据暂缺/未查得','数据暂缺未查得','暂缺','未查得','n/a','na','本节不展开','该节不展开','暂不展开','不展开','不展开数字罗列'});ak=(('本期未取到',80),('暂无',60),('无公开可核实',60),('无可核实',40),('暂无法核对',40),('无法核对',40));aa=('数据暂缺','未查得','未取到','本节不展开','该节不展开','暂不展开','不展开数字','暂无公开','无公开可核实','暂无相关','无可核实','暂无法核对','无法核对','暂不支持','接口不支持','数据源缺失');bs=PhraseMatcher(aa);bo=PhraseMatcher(aa+('deep research capability','capability call','host data package'));bh=PhraseMatcher(('westock-data','westock-tool','westock','neodata-financial-search','neodata','run_tool'),case_sensitive=False);M=frozenset({'Snapshot','Highlights','Risks','Catalysts'})
def I(n):
 e=[]
 for ln in(n or '').splitlines():
  s=ln.strip()
  if not s:continue
  a=0
  if s and s[0]in('-','*','+'):a=1
  else:
   while a<len(s)and s[a].isdigit():
    a+=1
   if a==0 or a>=len(s)or s[a]not in('.',')','、'):a=0
   else:a+=1
  while a<len(s)and s[a].isspace():
   a+=1
  s=s[a:]
  if s.startswith('**'):
   end=s.find('**',2)
   if end>=0:
    aM=s[end+2:]
    if aM.startswith(('：',':')):aM=aM[1:]
    s=aM.lstrip()
  if s:e.append(s)
 return e
def bg(text):
 spans=[(cl.start,cl.end)for cl in bh.spans(text)];F=text.casefold();a=0
 while a<len(text):
  if F.startswith('host_',a):
   end=a+5
   while end<len(text)and(text[end].isascii()and(text[end].isalpha()or text[end]=='_')):
    end+=1
  elif F.startswith('westock',a):
   end=a+7
   for b2 in('-data','-tool'):
    if F.startswith(b2,end):
     end+=len(b2);break
   ag=end
   while ag<len(text)and text[ag]in(' ','\t'):
    ag+=1
   z=ag
   while z<len(text)and(text[z].isascii()and(text[z].isalpha()or text[z]=='_')):
    z+=1
   if z>ag:end=z
  else:
   a+=1;continue
  spans.append((a,end));a=end
 spans.sort();p=[]
 for(start,end)in spans:
  if p and start<p[- 1][1]:p[- 1]=(p[- 1][0],max(p[- 1][1],end))
  else:p.append((start,end))
 return p
def am(text):
 if not text:return text
 spans=bg(text);parts=[];a=0
 for(start,end)in spans:
  parts.append(text[a:start]);a=end
 parts.append(text[a:]);s=collapse_horizontal_whitespace(''.join(parts))
 for W in reversed(parse_inline_sources(s)):
  label=W.label.strip(' 、，,')
  while any((b0 in label for b0 in('、、','，，',',,','、，','，、',',，','，,'))):
   for b0 in('、、','，，',',,','、，','，、',',，','，,'):
    label=label.replace(b0,b0[- 1])
  E=f'(Source: {label})' if label else '';s=s[:W.start]+E+s[W.end:]
 return s
def D(text):
 if bo.spans(text):return True
 start=text.find('no')
 while start>=0:
  end=text.find('interface',start+1)
  if end<0:break
  bY=text[start+1:end]
  if len(bY)<=24 and(not any((aN in bY for aN in('。','．','\n')))):return True
  start=text.find('no',start+1)
 return False
def ai(text):
 if not text:return text
 w=[]
 for b in text.split('\n'):
  if not b.strip():
   w.append(b);continue
  if b.strip().startswith('|')and '|' in b.strip()[1:]:
   w.append(am(b));continue
  bK=split_sentences(b);b_=[]
  for bd in bK:
   if not bd:continue
   bD=bd.strip()
   if not bD:
    b_.append(bd);continue
   if D(bD):continue
   b_.append(am(bd))
  p=''.join(b_);V=q(p)
  if V and(not p[len(V):].strip()):continue
  if p.strip()or not b.strip():w.append(p.rstrip()if p.strip()else '')
 return l('\n'.join(w)).strip()
def aP(text):
 bD=text.strip().casefold();aD=len(bD)
 for aN in('。','．','.'):
  index=bD.find(aN)
  if index>=0:aD=min(aD,index)
 bS=bD[:aD].strip()
 if bS in a6:return True
 return any((bS.startswith(V)and len(bS)-len(V)<=limit for(V,limit)in ak))
def aQ(text):
 a=0
 while a<len(text):
  if not text[a].isdigit():
   a+=1;continue
  end=a+1
  while end<len(text)and(text[end].isdigit()or text[end]=='.'):
   end+=1
  ah=text[a:end].strip('.')
  if not(len(ah)==4 and ah.startswith('20')and ah.isdigit()):return True
  a=end
 return False
def v(e):
 if not e:return True
 if all((aP(x)or '数据暂缺' in x or '未查得' in x or('未取到' in x)or D(x)for x in e)):return True
 bI='\n'.join(e)
 if not bs.spans(bI)and(not D(bI)):return False
 if any(('|' in x for x in e)):return False
 return not aQ(bI)
def an(body):
 if not body:return body
 text=ai(body);aX=set(J)|M;bE=[]
 for section in MarkdownDocument(text).sections(3):
  name=section.heading.title
  if name in aX and name not in M:
   if v(I(section.body(text))):bE.append((section.start,section.end))
 for(start,end)in reversed(bE):
  text=text[:start]+text[end:]
 return l(text).strip()
def R(body):
 aX=set(J)|M;cs=[]
 for section in MarkdownDocument(body or '').sections(3):
  name=section.heading.title
  if name not in aX or name in M:continue
  e=I(section.body(body))
  if v(e):cs.append(f'### {name} (placeholder only, should be deleted)')
 return cs
def aB(body):
 section=MarkdownDocument(body).find_section(3,'Peer comparison')
 if section is None:raise ValueError('Incomplete report structure: must contain "### Peer comparison" and list this instrument plus at least 3 comparable companies.')
 aG=[]
 for b in section.body(body).splitlines():
  u=b.strip()
  if not u.startswith('|')or '|' not in u[1:]:continue
  if is_table_separator_line(u):continue
  t=split_table_row(u)
  if t:aG.append(t)
 if not aG:raise ValueError('Incomplete report structure: must contain "### Peer comparison" and list this instrument plus at least 3 comparable companies.')
 (y,ap)=(aG[0],aG[1:]);bi=[G(h)for h in y];bT=[];U=set();aY=[]
 for t in ap:
  bk=t[0].strip()if t else ''
  for(j,cc)in enumerate(bi):
   if not cc or j>=len(t):continue
   match=a9.match((t[j]or '').strip())
   if not match:continue
   raw=match.group(2)or match.group(3)or '';bB=aE(raw)
   if bB and bB!=cc:bT.append(f"{bk or '?'}[{(y[j] if j < len(y) else j)}]")
  ca=[aq for aq in t[1:]if aq.strip()and(not C(aq))]
  if not bk:continue
  if len(ca)<2:
   aY.append(bk);continue
  U.add(bk.casefold())
 if bT:raise ValueError('Peer comparison currency mismatch: cell currency differs from the header (convert to the header unit):'+' / '.join(bT[:6]))
 if aY:raise ValueError('Peer comparison data incomplete: each company needs at least 2 comparable metrics:'+' / '.join(aY[:6]))
 if len(U)<4:raise ValueError(f'Peer comparison too few companies: the table must include this instrument + at least 3 well-known comparables, currently only {len(U)} companies. Fetch more data before writing.')
def aI(body):
 run=0
 for ch in body or '':
  if '一'<=ch<='\u9fff':
   run+=1
   if run>=12:raise ValueError('Report body must be English. Rewrite raw_writer.md in English. Keep the required English headings, the ticker, and the official name. Do not leave a Chinese sentence.')
  else:run=0
def _assert_writer_structure(body):
 aI(body);aU(body);F=body.casefold()
 if '<!doctype' in F and 'html' in F[F.find('<!doctype'):F.find('<!doctype')+32]or any((bL in F for bL in('<html>','<html ','<html\t','<html\n'))):raise ValueError('Illegal report structure: do not output an HTML page; it must be writer-public six-module Markdown')
 k=MarkdownDocument(body);b4=frozenset('一二三四五六七八九十')
 for heading in k.headings:
  title=heading.title;a=0
  while a<len(title)and title[a]in b4:
   a+=1
  if a and a<len(title)and(title[a]in('、','.','．')):raise ValueError('Illegal report structure: do not build your own "1, 2, 3" table of contents; use "## Fundamentals" … "## Events and catalysts" and the standard ### subpoints')
 ao=k.heading_titles(2)
 if 'AI综合评估' in ao:raise ValueError('Illegal report structure: a one-shot write must not contain "AI Overall Assessment"; that chapter is abolished, rewrite as the six modules (finalization will not delete it for you).')
 cf=('Market Performance Overview','Price and Technical Analysis','Fundamentals','Industry and Event Drivers','Institutional Views Summary','Risks and Challenges','Key Points for Investors','Summary and Outlook')
 for name in cf:
  cb=False
  for title in ao:
   normalized=title.strip();a=0
   while a<len(normalized)and normalized[a].isdigit():
    a+=1
   if a and a<len(normalized)and(normalized[a]=='.'):normalized=normalized[a+1:].strip()
   if normalized==name:
    cb=True;break
  if cb:raise ValueError(f'Illegal report structure: legacy eight-chapter heading detected "{name}"; use the six modules instead (Fundamentals…Events and catalysts).')
 aH=Q(body)
 if aH:raise ValueError('Incomplete report structure: conclusion-first section missing '+' / '.join(aH)+'. Rewrite the summary as Snapshot/Highlights/Risks/Catalysts.')
 if 'Bottom line' not in body:raise ValueError('Incomplete report structure: Snapshot must include "Bottom line".')
 ad=au(body)
 if ad:raise ValueError('Incomplete report structure: missing standard six-module heading '+' / '.join(ad)+'. Rewrite per WRITER_SYSTEM before finalize.')
 aB(body);bt=R(body)
 if bt:raise ValueError('Illegal report structure: the following ### sections have no substantive data (omit the whole section; do not pad with "data unavailable"):'+' / '.join(bt[:8])+(f' in total {len(bt)} items' if len(bt)>8 else ''))
 aJ(body)
bp=PhraseMatcher(('westock','neodata','finnhub','mcp','run_tool','run_phase','interface','api','tool','capability name','Baidu search'),case_sensitive=False)
def aR(body):
 aX=set(J)|M;aS=[]
 for section in MarkdownDocument(body or '').sections(3):
  name=section.heading.title
  if name not in aX:continue
  bz=section.body(body);e=I(bz)
  if v(e):continue
  aS.append((name,bz))
 return aS
def aJ(body):
 sections=aR(body)
 if not sections:return
 ad=[];aZ=[]
 for(name,n)in sections:
  a1=parse_inline_sources(n or '',max_label_length=60)
  if not a1:
   ad.append(f'### {name}');continue
  for W in a1:
   label=W.label.strip()
   if not label or bp.spans(label):aZ.append(f'### {name} → (Source: {label})')
 if ad:raise ValueError('Body missing a short source at paragraph end: the following substantive ### sections need at least one "…(Source: company filings)" or "(Source: company filings, public reporting)" (full-width parentheses, at the end of a paragraph):'+' / '.join(ad[:10])+(f' in total {len(ad)} sections' if len(ad)>10 else ''))
 if aZ:raise ValueError('Illegal source: tool/capability names must not appear in (Source: …); use company filings/public reporting/industry data etc.:'+' / '.join(aZ[:8]))
aW=('public reporting','press reports','news reports','public disclosure','financial press','public news')
def bM(label):
 s=(label or '').strip();return bool(s)and any((cv in s for cv in aW))
def required_public_web_refs(body='',*,cn=2):return cn
a7=frozenset({'','—','–','−','-','n/a','na','暂缺','未查得','数据暂缺','/','＼','－'})
def C(aq):return(aq or '').strip().casefold()in a7
def aw(b):return[c.strip()for c in b.strip().strip('|').split('|')]
def m(t):return '| '+' | '.join(t)+' |'
def ax(t):
 if not t:return False
 for aq in t:
  af=aq.replace(' ','')
  if af.startswith(':'):af=af[1:]
  if af.endswith(':'):af=af[:- 1]
  if len(af)<3 or any((aN!='-' for aN in af)):return False
 return True
al={'USD':1.0,'HKD':7.8,'CNY':7.25};bq={'usd':'USD','hkd':'HKD','cny':'CNY','rmb':'CNY','USD':'USD','HKD':'HKD','CNY':'CNY'};a8=(('100M USD','USD'),('trillion USD','USD'),('10K USD','USD'),('100M HKD','HKD'),('10K HKD','HKD'),('HKD','HKD'),('100M CNY','CNY'),('10K CNY','CNY'),('CNY','CNY'),('USD','USD'));a9=re.compile('^\\s*([+-]?(?:\\d+(?:\\.\\d+)?|\\.\\d+))\\s*(?:[\\(（]\\s*(港元|港币|美元|美金|人民币|元|USD|HKD|CNY|RMB)\\s*[\\)）]|(港元|港币|美元|美金|人民币))\\s*$',re.IGNORECASE)
def aE(raw):return bq.get((raw or '').strip().casefold())or bq.get((raw or '').strip(),'')
def G(y):
 text=(y or '').strip()
 if not text:return ''
 for(ah,co)in a8:
  if ah in text:return co
 return ''
def bn(bU,bB,ct):
 cg=al[bB];ci=al[ct];return bU/cg*ci
def X(bU):
 text=f'{bU:.2f}'
 if '.' in text:text=text.rstrip('0').rstrip('.')
 return text or '0'
def N(aq,ae):
 if not ae or not aq or C(aq):return aq
 match=a9.match(aq.strip())
 if not match:return aq
 bF=match.group(1);b9=match.group(2)or match.group(3)or '';bB=aE(b9)
 if not bB or bB==ae:
  if bB==ae:return X(float(bF))
  return aq
 if bB not in al or ae not in al:return aq
 bV=bn(float(bF),bB,ae);return X(bV)
def A(y,body):
 if not y or not body:return body
 bi=[G(h)for h in y]
 if not any(bi):return body
 aS=[]
 for bP in body:
  bl=list(bP)
  for(j,cc)in enumerate(bi):
   if not cc or j>=len(bl):continue
   bl[j]=N(bl[j],cc)
  aS.append(bl)
 return aS
def av(bj):
 aG=[]
 for b in bj:
  t=aw(b)
  if ax(t):continue
  aG.append(t)
 if len(aG)<2:return bj
 bJ=max((len(r)for r in aG));bQ=[r+['']*(bJ-len(r))for r in aG];(y,body)=(bQ[0],bQ[1:]);body=A(y,body);aL=[]
 for bP in body:
  o=['' if C(c)else c for c in bP]
  if any((not c.strip()for c in o)):continue
  aL.append(o)
 if not aL:return[]
 bc=[0]
 for j in range(1,bJ):
  if any((bP[j].strip()for bP in aL)):bc.append(j)
 def bN(bP):return[bP[j]if j<len(bP)else '' for j in bc]
 b5=bN(y);cj=[bN(r)for r in aL];cu=['---']*len(bc);return[m(b5),m(cu)]+[m(r)for r in cj]
def T(text):
 if not text:return text
 e=text.replace('\r\n','\n').split('\n');aS=[];i=0
 while i<len(e):
  b=e[i];u=b.strip()
  if u.startswith('|')and '|' in u[1:]:
   bf=[b];j=i+1
   while j<len(e):
    cd=e[j].strip()
    if cd.startswith('|')and '|' in cd[1:]:
     bf.append(e[j]);j+=1;continue
    break
   aG=[];b1=[]
   for(cp,raw)in enumerate(bf):
    t=aw(raw)
    if ax(t):
     b1.append(cp);aG.append(t)
    else:aG.append(t)
   ap=[r for(cp,r)in enumerate(aG)if cp not in b1]
   if len(ap)>=2:
    bJ=max((len(r)for r in ap));bQ=[r+['']*(bJ-len(r))for r in ap];(y,body)=(bQ[0],bQ[1:]);body=A(y,body);ar=[m(y)]
    if b1:ar.append(bf[b1[0]].rstrip('\n'))
    else:ar.append(m(['---']*len(y)))
    ar.extend((m(r)for r in body));aS.extend(ar)
   else:aS.extend(bf)
   i=j;continue
  aS.append(b);i+=1
 return '\n'.join(aS)
def O(text):
 if not text:return text
 def bO(aN):return aN=='_' or aN.isalnum()
 result=[];a=0;F=text.casefold()
 while a<len(text):
  ah=text[a:a+6];key=F[a:a+6];a3='';bZ=''
  if len(key)==6 and key.startswith('fy')and(key[2]in '1234')and(key[3]=='q')and key[4:].isdigit():(a3,bZ)=(ah[2],ah[4:])
  elif len(key)==6 and key[0]in '1234' and(key[1:4]=='qfy')and key[4:].isdigit():(a3,bZ)=(ah[0],ah[4:])
  elif len(key)==6 and key[0]=='q' and(key[1]in '1234')and(key[2:4]=='fy')and key[4:].isdigit():(a3,bZ)=(ah[1],ah[4:])
  bW=a==0 or not bO(text[a- 1]);b6=a+6>=len(text)or not bO(text[a+6])
  if a3 and bW and b6:
   result.append(f'FY{bZ}Q{a3}');a+=6
  else:
   result.append(text[a]);a+=1
 return ''.join(result)
def P(text):
 a0=text.split('\n\n')
 for(index,be)in enumerate(a0):
  e=[b.strip()for b in be.splitlines()if b.strip()]
  if not e or any((parse_heading_line(b)or b.startswith(('|','- ','* ','+ '))or(b[0].isdigit()and '. ' in b[:5])for b in e)):continue
  bA=parse_inline_sources(be,max_label_length=60)
  if len(bA)<=1:continue
  bv=[]
  for W in bA:
   normalized=W.label.replace('，','、').replace(',','、')
   for label in normalized.split('、'):
    label=label.strip()
    if label and label not in bv:bv.append(label)
  n=be
  for W in reversed(bA):
   n=n[:W.start]+n[W.end:]
  for bm in('。','，','；','：','！','？'):
   n=n.replace(' '+bm,bm)
  n=collapse_horizontal_whitespace(n).rstrip();a0[index]=f"{n}(Source: {', '.join(bv)})" if bv else n
 return '\n\n'.join(a0)
def Y(text):
 if not text:return text
 e=text.replace('\r\n','\n').split('\n');aS=[];i=0
 while i<len(e):
  b=e[i];u=b.strip()
  if is_horizontal_rule(u):
   i+=1;continue
  if u.startswith('|')and '|' in u[1:]:
   bf=[b];j=i+1
   while j<len(e):
    cd=e[j].strip()
    if cd.startswith('|')and '|' in cd[1:]:
     bf.append(e[j]);j+=1;continue
    break
   o=av(bf);aS.extend(o);i=j;continue
  aS.append(b);i+=1
 body=P('\n'.join(aS));body=l(body).strip();return O(body)
def aC(text):
 body=text.strip()
 if not body.startswith('```')or not body.endswith('```')or len(body)<6:return body
 a=3;F=body.casefold()
 for bG in('markdown','json','md'):
  if F.startswith(bG,a):
   a+=len(bG);break
 if a<len(body)- 3 and(not body[a].isspace()):return body
 while a<len(body)- 3 and body[a].isspace():
  a+=1
 return body[a:- 3].rstrip()
def ensure_markdown_report(text,query):
 body=str(text or '').strip();body=aC(body);body=an(body);body=T(body);_assert_writer_structure(body);(o,a1)=aA(body)
 if a1:print(f'[compliance] hits={a1}',file=sys.stderr)
 return Y(o)
def main():
 bu=argparse.ArgumentParser(description='Ensure deep-research markdown report');bu.add_argument('--query',required=True,help='Resolved research query');bu.add_argument('--input-file',default='',help='Raw writer output file');bu.add_argument('--text',default='',help='Raw writer output text');args=bu.parse_args()
 if args.input_file:
  with open(args.input_file,'r',encoding='utf-8')as f:
   raw=f.read()
 elif args.text:raw=args.text
 else:raw=sys.stdin.read()
 print(ensure_markdown_report(raw,args.query));return 0
if __name__=='__main__':sys.exit(main())
