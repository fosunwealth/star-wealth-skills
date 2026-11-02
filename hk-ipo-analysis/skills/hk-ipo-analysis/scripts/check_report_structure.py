#!/usr/bin/env python3

from __future__ import annotations

import sys
from collections import Counter
from html.parser import HTMLParser
from typing import Dict, List, Optional, Tuple

FIXED = [
    "section.card", "header.hero", "nav.toc", "footer", "script",
    "div.facts",
    "div.gauges", "div.gauge", "div.kv-grid", "div.interp", "div.lottery-head",
    "div.hero-top", "div.rating-badge", "div.hero-reason",
    "table", "thead", "tbody", "meta", "span.idx", "h2",
]

VARY = [
    ("div.fact", ".facts > .fact"),
    ("div.kv", ".kv-grid > .kv"),
    ("p", ".interp > p"),
    ("li", "li"),
    ("div.kv-val", ".kv-val"),
    ("ul.mini-list", "ul.mini-list"),
    ("div.lot-card", ".lot-card"),
]

CHART_KEYS = frozenset({"div.chart", "div.radar-wrap"})

VARIABLE_KEYS = {
    "div.fact", "div.kv", "p", "li", "ul.mini-list", "div.kv-val", "div.stars",
} | set(CHART_KEYS)

NODEID = "data-page-node-id"
_NO_NODEID = ("title", "style", "script")
_NID_CHARS = frozenset("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")
_SPEC_ID_MARK = '"id": "'
_SPEC_HEIGHT_MARK = '", "height"'

def _nid_ok(value: str) -> bool:
    return len(value) == 22 and all(c in _NID_CHARS for c in value)

def _scan_spec_ids(path: str) -> List[str]:
    found: List[str] = []
    carry = ""
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        while True:
            chunk = handle.read(65536)
            if not chunk:
                break
            window = carry + chunk
            start = 0
            while True:
                i = window.find(_SPEC_ID_MARK, start)
                if i < 0:
                    break
                j = i + len(_SPEC_ID_MARK)
                k = window.find(_SPEC_HEIGHT_MARK, j)
                if k < 0:
                    break
                found.append(window[j:k])
                start = k + len(_SPEC_HEIGHT_MARK)
            carry = window[-80:]
    return found

class _Scanner(HTMLParser):

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: List[Tuple[str, str, Dict[str, int]]] = []
        self.nodes: Dict[str, dict] = {}
        self.order: List[str] = []
        self.nid_values: List[str] = []
        self.nid_problems: List[str] = []
        self.expect = 0
        self.got = 0
        self.nid_bad_last: List[str] = []
        self.nid_on_raw: List[str] = []
        self.nid_raw_hits = 0
        self.tag_census: Counter = Counter()
        self.tag_variants: Counter = Counter()
        self.ids: List[str] = []
        self.nav_toc_links = 0
        self.tables: List[List[int]] = []
        self.cur_tr_cols: Optional[int] = None

    def handle_starttag(self, tag: str, attrs) -> None:
        names = tuple(n for n, _ in attrs)
        d = dict(attrs)
        cls = d.get("class") or ""
        eid = d.get("id") or ""
        key = tag + ("." + " ".join(cls.split()) if cls else "") + ("#" + eid if eid else "")

        if not self.stack:
            path = key + "#0"
            var = key in VARIABLE_KEYS
        else:
            ppath, _, cnt = self.stack[-1]
            cnt[key] = cnt.get(key, 0) + 1
            path = "%s/%s#%s" % (ppath, key, "0" if cnt[key] == 1 else "*")
            var = self.nodes[ppath]["var"] or key in VARIABLE_KEYS

        sel = tag + ("." + cls if cls else "")
        self.tag_census[sel] += 1
        if eid:
            self.ids.append(eid)
        if tag == "a" and self.stack and self.stack[-1][1].startswith("nav.toc"):
            self.nav_toc_links += 1
        if tag == "span" and (cls == "tag" or cls.startswith("tag ")):
            self.tag_variants[cls] += 1

        if tag == "table":
            self.tables.append([0, 0])
            self.cur_tr_cols = None
        if tag == "tr" and self.tables and any(p[1] == "tbody" for p in self.stack):
            self.tables[-1][0] += 1
            self.cur_tr_cols = 0
        if tag in ("td", "th") and self.cur_tr_cols is not None and self.tables:
            self.cur_tr_cols += 1
            self.tables[-1][1] = max(self.tables[-1][1], self.cur_tr_cols)

        has = NODEID in d
        if tag in _NO_NODEID:
            if has:
                self.nid_on_raw.append(path)
        else:
            self.expect += 1
            if has:
                self.got += 1
                if names[-1] != NODEID:
                    self.nid_bad_last.append(path)
                self.nid_values.append(str(d[NODEID]))

        node = self.nodes.get(path)
        attrs_sig = names if NODEID not in names else names[:-1]
        if node is None:
            node = {"tag": tag, "class": cls, "attrs": attrs_sig, "children": {}, "var": var}
            self.nodes[path] = node
            self.order.append(path)
        elif node["attrs"] != attrs_sig:
            self.nid_problems.append("Same-path element attribute-name sequence mismatch: %s" % path)
        if self.stack:
            pnode = self.nodes[self.stack[-1][0]]
            pnode["children"][key] = pnode["children"].get(key, 0) + 1
        self.stack.append((path, key, {}))

    def handle_startendtag(self, tag: str, attrs) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag == "tr":
            self.cur_tr_cols = None
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][1].split(".")[0].split("#")[0] == tag:
                del self.stack[i:]
                break

def scan(path: str) -> _Scanner:
    s = _Scanner()
    hits = 0
    tail = ""
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            hits += (tail + chunk).count(NODEID)
            tail = chunk[-(len(NODEID) - 1):]
            s.feed(chunk)
    s.close()
    s.nid_raw_hits = hits
    if s.nid_on_raw:
        s.nid_problems.append("<title>/<style>/<script> must not carry %s: %d place(s) (e.g. %s)"
                              % (NODEID, len(s.nid_on_raw), s.nid_on_raw[0]))
    if s.nid_bad_last:
        s.nid_problems.append("%s is not the last attribute: %d place(s) (e.g. %s)"
                              % (NODEID, len(s.nid_bad_last), s.nid_bad_last[0]))
    if s.got and s.got != s.expect:
        s.nid_problems.append("Incomplete coverage: %d/%d elements carry %s (the whole body subtree should carry it)"
                              % (s.got, s.expect, NODEID))
    if s.got:
        if hits != s.got:
            s.nid_problems.append("%s appears %d time(s) in the file and %d time(s) on open tags (the gap is on closing tags/comments)"
                                  % (NODEID, hits, s.got))
        dup = [v for v, n in Counter(s.nid_values).items() if n > 1]
        if dup:
            s.nid_problems.append("%s has %d duplicate value(s) (e.g. %s)" % (NODEID, len(dup), dup[0]))
        bad = [v for v in s.nid_values if not _nid_ok(v)]
        if bad:
            s.nid_problems.append("%s has %d value(s) that are not 22-character base62 (e.g. %r)"
                                  % (NODEID, len(bad), bad[0]))
    return s

def compare(a: str, b: str) -> int:
    sa, sb = scan(a), scan(b)
    fatal: List[str] = []
    info: List[str] = []

    only_a = [p for p in sa.order if p not in sb.nodes]
    only_b = [p for p in sb.order if p not in sa.nodes]
    var_only = [p for p in only_a + only_b
                if (p in sa.nodes and sa.nodes[p]["var"]) or (p in sb.nodes and sb.nodes[p]["var"])]
    only_a = [p for p in only_a if p not in var_only]
    only_b = [p for p in only_b if p not in var_only]
    if var_only:
        info.append("Variable subtree node differences: %d (data-driven, not a failure; e.g. %s)"
                    % (len(var_only), var_only[0]))
    if only_a or only_b:
        fatal.append("Node sets differ (A only %d, B only %d)" % (len(only_a), len(only_b)))
        for p in (only_a + only_b)[:10]:
            fatal.append("    %s: %s" % ("only A" if p in only_a else "only B", p))
        if len(only_a) + len(only_b) > 10:
            fatal.append("    ...(%d more omitted)" % (len(only_a) + len(only_b) - 10))

    n_attr = n_kids = 0
    for p in sa.order:
        if p not in sb.nodes:
            continue
        na, nb = sa.nodes[p], sb.nodes[p]
        if na["var"] or nb["var"]:
            continue
        if na["attrs"] != nb["attrs"]:
            n_attr += 1
            if n_attr <= 6:
                fatal.append("Attribute-name sequence differs %s: A=%s B=%s" % (p, na["attrs"], nb["attrs"]))
        ka = {k for k in na["children"] if k not in CHART_KEYS}
        kb = {k for k in nb["children"] if k not in CHART_KEYS}
        if ka != kb:
            n_kids += 1
            if n_kids <= 6:
                fatal.append("Child keys differ %s: onlyA=%s onlyB=%s"
                             % (p, sorted(ka - kb), sorted(kb - ka)))
        ma = {k: v for k, v in na["children"].items() if k not in CHART_KEYS}
        mb = {k: v for k, v in nb["children"].items() if k not in CHART_KEYS}
        if ma != mb and ka == kb:
            for k in sorted(ka):
                if (ma[k] > 1) != (mb[k] > 1):
                    info.append("Child multiplicities differ %s/%s: A=%d B=%d (data-driven, not a failure)"
                                % (p, k, ma[k], mb[k]))
    if n_attr > 6:
        fatal.append("    ...attribute-name sequence differences: %d" % n_attr)
    if n_kids > 6:
        fatal.append("    ...child-key differences: %d" % n_kids)

    for sel in FIXED:
        ca, cb = sa.tag_census.get(sel, 0), sb.tag_census.get(sel, 0)
        if ca != cb:
            fatal.append("Cardinality differs %s: A=%d B=%d" % (sel, ca, cb))
    if sa.nav_toc_links != sb.nav_toc_links:
        fatal.append("nav.toc link count differs: A=%d B=%d" % (sa.nav_toc_links, sb.nav_toc_links))

    ia, ib = set(sa.ids), set(sb.ids)
    sec_a = {i for i in ia if not i.startswith("chart-")}
    sec_b = {i for i in ib if not i.startswith("chart-")}
    if sec_a != sec_b:
        fatal.append("section id sets differ: onlyA=%s onlyB=%s" % (sorted(sec_a - sec_b), sorted(sec_b - sec_a)))
    for side, s in (("A", sa), ("B", sb)):
        dup = sorted(i for i, n in Counter(s.ids).items() if n > 1)
        if dup:
            fatal.append("Duplicate real id(s) [%s]: %s" % (side, dup))

    for side, s, path in (("A", sa, a), ("B", sb, b)):
        boxes = {i for i in s.ids if i.startswith("chart-")}
        specs = set(_scan_spec_ids(path))
        if boxes != specs:
            fatal.append("Chart self-inconsistency [%s]: only in DOM=%s only in specs=%s"
                         % (side, sorted(boxes - specs), sorted(specs - boxes)))
    charts_a = {i for i in ia if i.startswith("chart-")}
    charts_b = {i for i in ib if i.startswith("chart-")}
    if charts_a != charts_b:
        info.append("Chart sets differ (data-driven; fewer than 2 points means no chart): onlyA=%s onlyB=%s"
                    % (sorted(charts_a - charts_b), sorted(charts_b - charts_a)))
    for sel, label in (("div.chart", ".chart"), ("div.radar-wrap", ".radar-wrap"),
                       ("div.chart-title", ".chart-title"), ("div.chart-box", ".chart-box")):
        ca, cb = sa.tag_census.get(sel, 0), sb.tag_census.get(sel, 0)
        if ca != cb:
            info.append("Chart block count %s: A=%d B=%d (data-driven)" % (label, ca, cb))

    if sa.tables != sb.tables:
        fatal.append("Table structure differs (each table = rows x columns): A=%s B=%s"
                     % ([tuple(t) for t in sa.tables], [tuple(t) for t in sb.tables]))

    va, vb = set(sa.tag_variants), set(sb.tag_variants)
    if va != vb:
        fatal.append(".tag variant sets differ: onlyA=%s onlyB=%s" % (sorted(va - vb), sorted(vb - va)))

    for side, probs in (("A", sorted(set(sa.nid_problems))), ("B", sorted(set(sb.nid_problems)))):
        for q in probs[:6]:
            fatal.append("node-id contract [%s]: %s" % (side, q))
        if len(probs) > 6:
            fatal.append("    ...[%s] total %d" % (side, len(probs)))

    for sel, label in VARY:
        ca, cb = sa.tag_census.get(sel, 0), sb.tag_census.get(sel, 0)
        if ca != cb:
            info.append("Variable cardinality %s: A=%d B=%d" % (label, ca, cb))
    if sa.tag_variants != sb.tag_variants:
        info.append(".tag variant distribution: A=%s B=%s" % (dict(sa.tag_variants), dict(sb.tag_variants)))
    if sa.got != sb.got:
        info.append("%s usage: A=%d/%d elements carry it, B=%d/%d (existence is not compared)"
                    % (NODEID, sa.got, sa.expect, sb.got, sb.expect))

    print("A = %s  (%d nodes / %d real ids / %d with node-id)"
          % (a, len(sa.order), len(set(sa.ids)), len(sa.nid_values)))
    print("B = %s  (%d nodes / %d real ids / %d with node-id)"
          % (b, len(sb.order), len(set(sb.ids)), len(sb.nid_values)))
    if fatal:
        print("\n✗ Structure mismatch: %d problem class(es)" % len(fatal))
        for line in fatal:
            print("  [fatal] " + line)
        if info:
            print("\n(the differences below are not failures)")
            for line in info:
                print("  [info] " + line)
        return 1
    print("\n✓ Structure matches")
    for line in info:
        print("  [info] " + line)
    return 0

def main(argv: List[str]) -> int:
    args = [x for x in argv[1:] if not x.startswith("-")]
    if len(args) != 2:
        print("Structure differ for the hk-ipo-analysis rich-template report: compares tags, classes, ids,")
        print("attribute order, fixed counts, table shape and the data-page-node-id contract. Text is ignored.")
        print("\nusage: check_report_structure.py A.html B.html")
        return 2
    return compare(args[0], args[1])

if __name__ == "__main__":
    sys.exit(main(sys.argv))
