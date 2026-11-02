import json;from dataclasses import dataclass;from typing import Any,Iterable,Iterator,Optional,Sequence,Tuple;from urllib.parse import urlsplit
@dataclass(frozen=True)
class TextSpan:
 start:int;end:int;text:str
@dataclass(frozen=True)
class PhraseSpan(TextSpan):
 phrase:str
@dataclass(frozen=True)
class SourceSpan(TextSpan):
 label:str
def iter_json_values(text):
 I=json.JSONDecoder();a=0
 while a<len(text):
  if text[a]not in('{','['):
   a+=1;continue
  try:
   (f,end)=I.raw_decode(text,a)
  except json.JSONDecodeError:
   a+=1;continue
  yield(f,a,end);a=end
def iter_json_objects(text):
 for(f,P,Q)in iter_json_values(text):
  if isinstance(f,dict):yield f
  elif isinstance(f,list):
   for O in f:
    if isinstance(O,dict):yield O
def split_sentences(text,w='。！？；\n'):
 result=[];start=0
 for(index,h)in enumerate(text):
  if h in w:
   result.append(text[start:index+1]);start=index+1
 if start<len(text):result.append(text[start:])
 return result
class PhraseMatcher:
 _END=object()
 def __init__(self,K,*,case_sensitive=True):
  self.case_sensitive=case_sensitive;self._root={}
  for phrase in K:
   if not phrase:continue
   key=phrase if case_sensitive else phrase.casefold();v=self._root
   for h in key:
    v=v.setdefault(h,{})
   v[self._END]=phrase
 def _longest_at(self,s,start):
  v=self._root;N=None;a=start
  while a<len(s):
   h=s[a]if self.case_sensitive else s[a].casefold();M=v.get(h)
   if M is None:break
   v=M;a+=1;phrase=v.get(self._END)
   if phrase is not None:N=PhraseSpan(start,a,s[start:a],phrase)
  return N
 def iter_spans(self,text,*,overlapping=False):
  a=0
  while a<len(text):
   match=self._longest_at(text,a)
   if match is None:
    a+=1;continue
   yield match;a=match.start+1 if overlapping else match.end
 def spans(self,text,*,overlapping=False):return list(self.iter_spans(text,overlapping=overlapping))
 def count(self,text,*,overlapping=False):return sum((1 for _ in self.iter_spans(text,overlapping=overlapping)))
 def remove(self,text):
  spans=self.spans(text)
  if not spans:return(text,0)
  parts=[];a=0
  for E in spans:
   parts.append(text[a:E.start]);a=E.end
  parts.append(text[a:]);return(''.join(parts),len(spans))
q=frozenset(']>"\'<>，。；、（');i=frozenset('.,;，。；')
def p(f):
 try:
  G=urlsplit(f);return G.scheme.lower()in('http','https')and bool(G.hostname)
 except ValueError:
  return False
def iter_http_url_spans(text):
 lower=text.lower();a=0
 while a<len(text):
  if lower.startswith('https://',a):o=8
  elif lower.startswith('http://',a):o=7
  else:
   a+=1;continue
  end=a+o
  while end<len(text):
   h=text[end]
   if h.isspace()or h in q or h in(')','）'):break
   end+=1
  g=end
  while g>a and text[g- 1]in i:
   g-=1
  f=text[a:g]
  if p(f):yield TextSpan(a,g,f)
  a=max(end,a+1)
def iter_http_urls(text):
 for E in iter_http_url_spans(text):
  yield E.text
def parse_inline_sources(text,*,max_label_length=160):
 D={'（':'）','(':')'};result=[];a=0
 while a<len(text):
  l=text[a];m=D.get(l)
  if m is None:
   a+=1;continue
  k=1;end=a+1
  while end<len(text)and k:
   if text[end]==l:k+=1
   elif text[end]==m:k-=1
   end+=1
  if k:
   a+=1;continue
  n=text[a+1:end- 1];b=0
  while b<len(n)and n[b].isspace():
   b+=1
  L=('来源','Source');C=next((H for H in L if n.startswith(H,b)),None)
  if C is None:
   a=end;continue
  b+=len(C)
  while b<len(n)and n[b].isspace():
   b+=1
  if b>=len(n)or n[b]not in(':','：'):
   a=end;continue
  label=n[b+1:].strip()
  if label and len(label)<=max_label_length:result.append(SourceSpan(a,end,text[a:end],label))
  a=end
 return result
def parse_labeled_values(text,label,*,z='\n|;，,',A=80):
 if not text or not label:return[]
 result=[];a=0
 while a<len(text):
  start=text.find(label,a)
  if start<0:break
  c=start+len(label)
  while c<len(text)and text[c].isspace():
   c+=1
  if c>=len(text)or text[c]not in(':','：'):
   a=start+len(label);continue
  c+=1
  while c<len(text)and text[c].isspace():
   c+=1
  j=c
  while j<len(text)and text[j]not in z:
   j+=1
  f=text[c:j].strip()
  if f and len(f)<=A:result.append(f)
  a=max(j,start+len(label))
 return result
def strip_parenthetical_label(text,F):
 if not text or not F:return text
 D={'（':'）','(':')'};t=F.casefold();spans=[];a=0
 while a<len(text):
  l=text[a];m=D.get(l)
  if m is None:
   a+=1;continue
  k=1;end=a+1
  while end<len(text)and k:
   if text[end]==l:k+=1
   elif text[end]==m:k-=1
   end+=1
  if k:
   a+=1;continue
  if text[a+1:end- 1].strip().casefold().startswith(t):
   start=a
   while start>0 and text[start- 1]in(' ','\t'):
    start-=1
   while end<len(text)and text[end]in(' ','\t'):
    end+=1
   spans.append((start,end))
  a=end
 if not spans:return text
 parts=[];a=0
 for(start,end)in spans:
  parts.append(text[a:start]);a=end
 parts.append(text[a:]);return ''.join(parts)
def collapse_horizontal_whitespace(text):
 result=[];r=False
 for h in text:
  if h in(' ','\t'):
   if not r:result.append(' ')
   r=True
  else:
   result.append(h);r=False
 return ''.join(result)
def e(text,B,x):
 u=set(B);result=[];y=False
 for h in text:
  if h in u:
   if not y:result.append(x)
   y=True
  else:
   result.append(h);y=False
 return ''.join(result)
def cleanup_after_removal(text):
 d=collapse_horizontal_whitespace(text);d=e(d,('，','、'),'，');d=e(d,('。',),'。');J=frozenset('，、；:： \t');d=d.lstrip(''.join(J));result=[]
 for(index,h)in enumerate(d):
  if h in J:
   a=index
   while a<len(d)and d[a]in J:
    a+=1
   if a==len(d)or d[a]in '。！？\n':continue
  result.append(h)
 return ''.join(result)
