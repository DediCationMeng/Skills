# -*- coding: utf-8 -*-
"""Europe PMC + arXiv retrieval for ELMs / bioprinting / live biotherapeutics / engineered probiotics.

Usage:
  python elm_search.py --from 2026-09-09 --to 2026-10-09 [--dir WORKDIR] [--max-pages 5]

Writes raw/epmc_raw.json and raw/arxiv_raw.json inside WORKDIR (default: cwd).
For 5-year retrospective: run once per year segment (keeps result sets manageable, resumable).
"""
import argparse, json, os, ssl, sys, time, urllib.parse, urllib.request

EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
ARXIV = "http://export.arxiv.org/api/query"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0 (research-literature-agent)"}


def fetch(url, tries=3, wait=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            print("  retry", i + 1, str(e)[:60])
            time.sleep(wait * (i + 1))
    return None


def queries(date):
    return {
        "ELM": f'(TITLE_ABS:"engineered living material*" OR TITLE_ABS:"living materials") AND (FIRST_PDATE:[{date}])',
        "Bioprinting": f'(TITLE_ABS:"bioprint*" OR TITLE_ABS:"3D print*" OR TITLE_ABS:"bioink" OR TITLE_ABS:"bio-ink" OR TITLE_ABS:"extrusion printing") AND (TITLE_ABS:cell* OR TITLE_ABS:bioink OR TITLE_ABS:tissue OR TITLE_ABS:hydrogel) AND (FIRST_PDATE:[{date}])',
        "LBP": f'(TITLE_ABS:"live biotherapeutic*" OR TITLE_ABS:"live bacterial therapeut*" OR TITLE_ABS:"microbial therapeut*" OR TITLE_ABS:"cell-based therap*" OR TITLE_ABS:"bacterial therap*") AND (FIRST_PDATE:[{date}])',
        "Probiotics": f'(TITLE_ABS:"engineered probiotic*" OR TITLE_ABS:"programmed bacteria" OR TITLE_ABS:"synthetic probiotic*" OR TITLE_ABS:"engineered bacteria" OR TITLE_ABS:"chassis organism" OR TITLE_ABS:"bacterial circuit") AND (TITLE_ABS:gut OR TITLE_ABS:therapeut* OR TITLE_ABS:probiotic* OR TITLE_ABS:microbiome OR TITLE_ABS:tumor OR TITLE_ABS:disease) AND (FIRST_PDATE:[{date}])',
    }


def search_epmc(date, max_pages):
    out = {}
    for name, q in queries(date).items():
        print(f"=== EPMC {name} ===")
        cursor, items = "*", []
        for page in range(max_pages):
            params = {"query": q, "format": "json", "pageSize": "100",
                      "resultType": "core", "cursorMark": cursor}
            data = fetch(EPMC + "?" + urllib.parse.urlencode(params))
            if not data:
                break
            res = data.get("resultList", {}).get("result", [])
            items.extend(res)
            print(f"  page {page}: {len(res)} hits (total {data.get('hitCount')})")
            nxt = data.get("nextCursorMark")
            if not nxt or nxt == cursor or not res:
                break
            cursor = nxt
            time.sleep(1.5)
        out[name] = items
        time.sleep(1.5)
    return out


def search_arxiv(date):
    # arXiv API: submittedDate range in search_query
    a, b = date.split(" TO ")
    d1 = a.replace("-", "") + "0000"
    d2 = b.replace("-", "") + "2359"
    q = ('all:"engineered living material" OR all:bioink OR all:bioprinting '
         f'OR all:"engineered probiotic" OR all:"live biotherapeutic"')
    url = (ARXIV + "?" + urllib.parse.urlencode({
        "search_query": f"({q}) AND submittedDate:[{d1} TO {d2}]",
        "start": 0, "max_results": 100, "sortBy": "submittedDate", "sortOrder": "descending",
    }))
    print("=== arXiv ===")
    xml = None
    for i in range(3):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
                xml = r.read().decode("utf-8", "ignore")
            break
        except Exception as e:
            print("  retry", i + 1, str(e)[:60])
            time.sleep(4)
    items = []
    if xml:
        import re
        for m in re.finditer(r"<entry>(.*?)</entry>", xml, re.S):
            e = m.group(1)
            def tag(t):
                mm = re.search(rf"<{t}[^>]*>(.*?)</{t}>", e, re.S)
                return " ".join((mm.group(1) if mm else "").split())
            idm = re.search(r"<id>(.*?)</id>", e)
            items.append({
                "id": (idm.group(1) if idm else "").split("/abs/")[-1],
                "title": tag("title"),
                "summary": tag("summary"),
                "published": tag("published")[:10],
                "authors": re.findall(r"<name>(.*?)</name>", e),
            })
    print(f"  {len(items)} arXiv entries")
    return {"arXiv": items}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="dfrom", required=True)
    ap.add_argument("--to", dest="dto", required=True)
    ap.add_argument("--dir", default=os.getcwd())
    ap.add_argument("--max-pages", type=int, default=5)
    args = ap.parse_args()

    raw = os.path.join(args.dir, "raw")
    os.makedirs(raw, exist_ok=True)
    date = f"{args.dfrom} TO {args.dto}"

    epmc = search_epmc(date, args.max_pages)
    with open(os.path.join(raw, "epmc_raw.json"), "w", encoding="utf-8") as f:
        json.dump(epmc, f, ensure_ascii=False, indent=1)

    arx = search_arxiv(date)
    with open(os.path.join(raw, "arxiv_raw.json"), "w", encoding="utf-8") as f:
        json.dump(arx, f, ensure_ascii=False, indent=1)

    for n, its in epmc.items():
        print(n, len(its))
    print("saved to", raw)


if __name__ == "__main__":
    main()
