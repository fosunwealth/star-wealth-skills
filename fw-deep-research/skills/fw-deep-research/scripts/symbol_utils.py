from dataclasses import dataclass;from typing import Iterator;l=frozenset(('US','OQ','N','NYSE','NASDAQ'));j=frozenset(('SH','SZ','BJ'))
def a(f):return 'A'<=f<='Z' or 'a'<=f<='z'
def c(f):return '0'<=f<='9'
def _all_ascii_letters(e):return bool(e)and all((a(f)for f in e))
def _all_ascii_digits(e):return bool(e)and all((c(f)for f in e))
def d(e):return all((ord(f)<128 for f in e))
def normalize_westock_symbol(e):
 raw=str(e or '').strip()
 if not raw or not d(raw):return ''
 if raw.count('.')==1:
  (h,p)=raw.rsplit('.',1);k=p.upper()
  if k=='HK' and 3<=len(h)<=5 and _all_ascii_digits(h):return 'hk'+h.zfill(5)
  if k in j and len(h)==6 and _all_ascii_digits(h):return k.lower()+h
  if k in l:
   if h[:2].lower()=='us':h=h[2:]
   if 1<=len(h)<=5 and _all_ascii_letters(h):return 'us'+h.upper()
  return ''
 if '.' in raw:return ''
 lower=raw.lower()
 if lower.startswith('us'):
  n=raw[2:]
  if 1<=len(n)<=5 and _all_ascii_letters(n):return 'us'+n.upper()
  return ''
 if lower.startswith('hk'):
  g=raw[2:]
  if 3<=len(g)<=5 and _all_ascii_digits(g):return 'hk'+g.zfill(5)
  return ''
 o=lower[:2];g=raw[2:]
 if o in('sh','sz','bj')and len(g)==6 and _all_ascii_digits(g):return o+g
 if 1<=len(raw)<=5 and _all_ascii_letters(raw):return 'us'+raw.upper()
 return ''
def is_standard_symbol(e):
 raw=str(e or '')
 if not raw or raw!=raw.strip()or(not d(raw)):return False
 normalized=normalize_westock_symbol(raw);return bool(normalized)and normalized==raw
@dataclass(frozen=True)
class TickerCandidate:
 raw:str;normalized:str;start:int;end:int
def i(raw,normalized):
 if normalized:return True
 if 4<=len(raw)<=6 and _all_ascii_digits(raw):return True
 return False
def m(text):
 b=0
 while b<len(text):
  if not(a(text[b])or c(text[b])):
   b+=1;continue
  start=b
  while b<len(text):
   f=text[b]
   if a(f)or c(f):
    b+=1;continue
   if f=='.' and b+1<len(text)and(a(text[b+1])or c(text[b+1])):
    b+=1;continue
   break
  raw=text[start:b];normalized=normalize_westock_symbol(raw)
  if i(raw,normalized):yield TickerCandidate(raw,normalized,start,b)
