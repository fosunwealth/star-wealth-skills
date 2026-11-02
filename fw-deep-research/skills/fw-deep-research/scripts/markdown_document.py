from dataclasses import dataclass;from enum import Enum;from typing import Iterator,Optional,Tuple
@dataclass(frozen=True)
class HeadingSpan:
 level:int;title:str;start:int;end:int;line_number:int
@dataclass(frozen=True)
class SectionSpan:
 heading:HeadingSpan;start:int;body_start:int;end:int
 def text(self,p):return p[self.start:self.end]
 def body(self,p):return p[self.body_start:self.end]
def c(b):
 if b.endswith('\n'):b=b[:- 1]
 if b.endswith('\r'):b=b[:- 1]
 return b
def j(b):
 count=0
 while count<len(b)and b[count]==' ':
  count+=1
 return count
def _fence_marker(b):
 b=c(b);indent=j(b)
 if indent>3 or indent==len(b):return None
 e=b[indent]
 if e not in('`','~'):return None
 end=indent
 while end<len(b)and b[end]==e:
  end+=1
 t=end-indent
 if t<3:return None
 return(e,t,not b[end:].strip())
def parse_heading_line(b):
 b=c(b);indent=j(b)
 if indent>3:return None
 a=indent
 while a<len(b)and b[a]=='#':
  a+=1
 level=a-indent
 if level not in(1,2,3):return None
 if a<len(b)and b[a]not in(' ','\t'):return None
 title=b[a:].strip();f=len(title)
 while f>0 and title[f- 1]=='#':
  f-=1
 if f<len(title)and f>0 and title[f- 1].isspace():title=title[:f].rstrip()
 return(level,title)
def list_item_prefix(b):
 raw=c(b);a=0
 while a<len(raw)and raw[a]in(' ','\t'):
  a+=1
 o=a
 if a<len(raw)and raw[a]in('-','*','+'):a+=1
 else:
  q=a
  while a<len(raw)and '0'<=raw[a]<='9':
   a+=1
  if a==q or a>=len(raw)or raw[a]not in('.',')'):return None
  a+=1
 if a>=len(raw)or raw[a]not in(' ','\t'):return None
 while a<len(raw)and raw[a]in(' ','\t'):
  a+=1
 if a==len(raw)and o==0:return raw
 return raw[:a]
def split_table_row(b):
 raw=c(b).strip()
 if raw.startswith('|'):raw=raw[1:]
 if raw.endswith('|'):raw=raw[:- 1]
 return[r.strip()for r in raw.split('|')]
def g(r):
 d=''.join((ch for ch in r if ch not in(' ','\t')))
 if d.startswith(':'):d=d[1:]
 if d.endswith(':'):d=d[:- 1]
 return len(d)>=3 and all((ch=='-' for ch in d))
def is_table_separator_line(b):
 v=split_table_row(b);return bool(v)and all((g(r)for r in v))
def is_horizontal_rule(b):
 d=''.join((ch for ch in c(b).strip()if ch not in(' ','\t')))
 if not d:return False
 if d[0]in('—','–'):return 1<=len(d)<=3 and all((ch==d[0]for ch in d))
 return len(d)>=3 and d[0]in('-','*','_')and all((ch==d[0]for ch in d))
def l(text):
 m=0;h=None;i=0
 for(line_number,b)in enumerate(text.splitlines(keepends=True),1):
  e=_fence_marker(b)
  if h is not None:
   if e and e[0]==h and(e[1]>=i)and e[2]:
    h=None;i=0
   m+=len(b);continue
  if e:
   (h,i,_)=e;m+=len(b);continue
  u=parse_heading_line(b)
  if u is not None:
   (level,title)=u;yield HeadingSpan(level,title,m,m+len(b),line_number)
  m+=len(b)
class MarkdownDocument:
 def __init__(self,text):
  self.text=text;self.headings=tuple(l(text))
 def heading_titles(self,level=None):return[heading.title for heading in self.headings if level is None or heading.level==level]
 def sections(self,level=None):
  result=[]
  for(index,heading)in enumerate(self.headings):
   if level is not None and heading.level!=level:continue
   end=len(self.text)
   for n in self.headings[index+1:]:
    if n.level<=heading.level:
     end=n.start;break
   result.append(SectionSpan(heading,heading.start,heading.end,end))
  return result
 def find_section(self,level,title,occurrence=0):
  s=[section for section in self.sections(level)if section.heading.title.strip()==title.strip()]
  if occurrence<0 or occurrence>=len(s):return None
  return s[occurrence]
 def split_sections(self,level):return self.sections(level)
 def replace_section(self,level,title,k,*,include_heading=True,occurrence=0):
  section=self.find_section(level,title,occurrence)
  if section is None:raise ValueError(f'section not found: H{level} {title}')
  start=section.start if include_heading else section.body_start;return self.text[:start]+k+self.text[section.end:]
 def remove_section(self,level,title,occurrence=0):
  section=self.find_section(level,title,occurrence)
  if section is None:return self.text
  return self.text[:section.start]+self.text[section.end:]
def heading_titles(text,level=None):return MarkdownDocument(text).heading_titles(level)
def find_section(text,level,title,occurrence=0):return MarkdownDocument(text).find_section(level,title,occurrence)
def split_sections(text,level):return MarkdownDocument(text).split_sections(level)
def replace_section(text,level,title,k,*,include_heading=True,occurrence=0):return MarkdownDocument(text).replace_section(level,title,k,include_heading=include_heading,occurrence=occurrence)
def remove_section(text,level,title,occurrence=0):return MarkdownDocument(text).remove_section(level,title,occurrence)
