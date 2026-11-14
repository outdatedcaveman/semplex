"""Free literature search with no account: Crossref (journals, books, proceedings) and the arXiv API.

  python -m cerp.litsearch "formal concept analysis lattice" [--n 15] [--source crossref|arxiv|both] [--from 1980]

Prints one markdown row per hit: year, citations (Crossref only), title, authors, venue, link.
A hit is a lead, not a reading: nothing found here may be cited until it is opened (AGENTS.md rule 7).

OpenAlex and Semantic Scholar are also free but need a personal key from this network (their keyless
budgets are shared per IP). If OPENALEX_API_KEY is set, OpenAlex is queried too.
No user data is sent: the client identifies itself only as "semplex-litsearch".
"""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

UA = {"User-Agent": "semplex-litsearch/0.1"}


def _get(url, timeout=40):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def crossref(q, n=15, year_from=None):
    p = {"query.bibliographic": q, "rows": n, "select": "title,author,issued,container-title,DOI,is-referenced-by-count,type"}
    if year_from:
        p["filter"] = f"from-pub-date:{year_from}"
    items = json.loads(_get("https://api.crossref.org/works?" + urllib.parse.urlencode(p)))["message"]["items"]
    out = []
    for it in items:
        au = it.get("author", [])
        out.append({"source": "crossref", "year": (it.get("issued", {}).get("date-parts") or [[None]])[0][0],
                    "cites": it.get("is-referenced-by-count"), "title": " ".join(it.get("title") or ["?"]),
                    "authors": ", ".join(a.get("family", "?") for a in au[:3]) + (" et al." if len(au) > 3 else ""),
                    "venue": " ".join(it.get("container-title") or [it.get("type", "")]), "link": "https://doi.org/" + it["DOI"]})
    return out


def arxiv(q, n=15):
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode({"search_query": f"all:{q}", "max_results": n, "sortBy": "relevance"})
    ns = {"a": "http://www.w3.org/2005/Atom"}
    out = []
    for e in ET.fromstring(_get(url)).findall("a:entry", ns):
        au = [x.findtext("a:name", "", ns) for x in e.findall("a:author", ns)]
        out.append({"source": "arxiv", "year": int(e.findtext("a:published", "0000", ns)[:4]), "cites": None,
                    "title": re.sub(r"\s+", " ", e.findtext("a:title", "?", ns)).strip(),
                    "authors": ", ".join(a.split()[-1] for a in au[:3]) + (" et al." if len(au) > 3 else ""),
                    "venue": "arXiv", "link": e.findtext("a:id", "", ns)})
    return out


def openalex(q, n=15, year_from=None):
    key = os.environ.get("OPENALEX_API_KEY")
    if not key:
        return []
    p = {"search": q, "per-page": n, "select": "title,publication_year,cited_by_count,doi,authorships,primary_location", "api_key": key}
    if year_from:
        p["filter"] = f"from_publication_date:{year_from}-01-01"
    out = []
    for it in json.loads(_get("https://api.openalex.org/works?" + urllib.parse.urlencode(p)))["results"]:
        au = [a["author"]["display_name"].split()[-1] for a in it.get("authorships", [])]
        src = ((it.get("primary_location") or {}).get("source") or {}).get("display_name", "")
        out.append({"source": "openalex", "year": it.get("publication_year"), "cites": it.get("cited_by_count"), "title": it.get("title") or "?",
                    "authors": ", ".join(au[:3]) + (" et al." if len(au) > 3 else ""), "venue": src, "link": it.get("doi") or ""})
    return out


def search(q, n=15, source="both", year_from=None):
    hits = []
    if source in ("crossref", "both"):
        hits += crossref(q, n, year_from)
    if source in ("arxiv", "both"):
        hits += arxiv(q, n)
    hits += openalex(q, n, year_from)
    seen, out = set(), []
    for h in hits:
        k = re.sub(r"\W+", "", h["title"].lower())[:60]
        if k not in seen:
            seen.add(k); out.append(h)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("query"); ap.add_argument("--n", type=int, default=15)
    ap.add_argument("--source", default="both", choices=["crossref", "arxiv", "both"]); ap.add_argument("--from", dest="year_from", type=int)
    a = ap.parse_args(argv)
    print("| Year | Cites | Title | Authors | Venue | Link |\n|---|---|---|---|---|---|")
    for h in search(a.query, a.n, a.source, a.year_from):
        print(f"| {h['year'] or ''} | {'' if h['cites'] is None else h['cites']} | {h['title'][:110]} | {h['authors']} | {h['venue'][:40]} | {h['link']} |")


if __name__ == "__main__":
    main()
