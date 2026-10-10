# -*- coding: utf-8 -*-
"""Europe PMC + arXiv retrieval for plasmonic nanomaterials (2026-10-09 起改为等离激元方向).

Focus: (1) novel plasmonic nanomaterial development; (2) biomedical applications of
plasmonic nanomaterials. Keyword classes: core concepts (plasmonics / LSPR / SPR-SPP /
gap plasmon) x morphology (Au/Ag nanoparticles, nanorods/nanostars/nanocubes, core-shell,
nanogap). Derived from the elm-literature-pipeline skill (2026-10-09, independent copy).

Usage:
  python plm_search.py --from 2026-09-09 --to 2026-10-09 [--dir WORKDIR] [--max-pages 5]

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
        # 核心概念 x 纳米材料总称 -> 新型等离激元纳米材料开发（宽检索）
        "PLASMON-CORE": (
            '(TITLE_ABS:plasmonic* OR TITLE_ABS:"localized surface plasmon" '
            'OR TITLE_ABS:"surface plasmon resonance" OR TITLE_ABS:"surface plasmon polariton*" '
            'OR TITLE_ABS:"gap plasmon*" OR TITLE_ABS:"plasmon resonance" OR TITLE_ABS:LSPR) '
            'AND (TITLE_ABS:nanoparticle* OR TITLE_ABS:nanostructure* OR TITLE_ABS:"nanomaterial*" '
            'OR TITLE_ABS:colloid* OR TITLE_ABS:nanocrystal*) '
            f'AND (FIRST_PDATE:[{date}])'
        ),
        # 核心概念 x 材料形貌 -> Au/Ag 纳米粒子、nanorods/nanostars/nanocubes、core-shell、nanogap
        "PLASMON-SHAPE": (
            '(TITLE_ABS:plasmonic* OR TITLE_ABS:"localized surface plasmon" '
            'OR TITLE_ABS:"surface plasmon" OR TITLE_ABS:LSPR) '
            'AND (TITLE_ABS:"gold nanoparticle*" OR TITLE_ABS:"silver nanoparticle*" '
            'OR TITLE_ABS:"Au nanoparticle*" OR TITLE_ABS:"Ag nanoparticle*" '
            'OR TITLE_ABS:nanorod* OR TITLE_ABS:nanostar* OR TITLE_ABS:nanocube* '
            'OR TITLE_ABS:nanoshell* OR TITLE_ABS:"core-shell" OR TITLE_ABS:nanogap) '
            f'AND (FIRST_PDATE:[{date}])'
        ),
        # 生物医学应用方向 -> 诊疗/传感/成像
        "PLASMON-BIO": (
            '(TITLE_ABS:plasmonic* OR TITLE_ABS:"localized surface plasmon" '
            'OR TITLE_ABS:"surface plasmon" OR TITLE_ABS:"gold nanoparticle*" '
            'OR TITLE_ABS:"silver nanoparticle*" OR TITLE_ABS:"surface-enhanced Raman" OR TITLE_ABS:SERS) '
            'AND (TITLE_ABS:biomedic* OR TITLE_ABS:theranostic* OR TITLE_ABS:therapeut* '
            'OR TITLE_ABS:diagnos* OR TITLE_ABS:biosensor* OR TITLE_ABS:bioimaging '
            'OR TITLE_ABS:photothermal OR TITLE_ABS:cancer OR TITLE_ABS:tumor '
            'OR TITLE_ABS:"drug deliver*" OR TITLE_ABS:antibacterial OR TITLE_ABS:wound '
            'OR TITLE_ABS:implant*) '
            f'AND (FIRST_PDATE:[{date}])'
        ),
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
    q = ('(all:plasmonic OR all:"localized surface plasmon" OR all:"surface plasmon" '
         'OR all:"gap plasmon" OR all:LSPR) '
         'AND (all:nanoparticle OR all:nanostructure OR all:nanorod OR all:nanostar '
         'OR all:nanocube OR all:nanoshell OR all:"core-shell" OR all:nanogap '
         'OR all:nanomaterial)')
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
