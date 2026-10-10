# -*- coding: utf-8 -*-
"""Supplementary EuropePMC queries for keywords the standard set misses:
  FUNGAL       - filamentous fungi ELM / mycelium materials / fungal 3D printing
  YEAST        - engineered yeast (S. cerevisiae / S. boulardii) ELM, bioprinting, LBP
  LIVINGFORMS  - living material forms (living hydrogels / fibers / films / coatings ...)

Merges results into raw/epmc_raw.json under these topic keys (idempotent overwrite per topic).

Usage:
  python elm_search_extra.py --dir WORKDIR --from 2020-01-01 --to 2020-12-31 [--max-pages 8]
"""
import argparse, json, os, ssl, time, urllib.parse, urllib.request

EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0 (research-literature-agent)"}


def queries(date):
    return {
        "FUNGAL": (
            '(((TITLE_ABS:"mycelium*" OR TITLE_ABS:"mycelial" OR TITLE_ABS:"hypha*") '
            'AND (TITLE_ABS:material* OR TITLE_ABS:print* OR TITLE_ABS:bioink OR TITLE_ABS:hydrogel* '
            'OR TITLE_ABS:film* OR TITLE_ABS:fiber* OR TITLE_ABS:fibre* OR TITLE_ABS:composite* '
            'OR TITLE_ABS:leather OR TITLE_ABS:scaffold* OR TITLE_ABS:living OR TITLE_ABS:engineer* '
            'OR TITLE_ABS:coating* OR TITLE_ABS:foam*)) '
            'OR (TITLE_ABS:"fungal material*" OR TITLE_ABS:"fungi-based" OR TITLE_ABS:"fungal-based" '
            'OR TITLE_ABS:"living fungal" OR TITLE_ABS:"engineered fungal" OR TITLE_ABS:"engineered fungi" '
            'OR TITLE_ABS:"fungal living material*" OR TITLE_ABS:"mycelium-based")) '
            f'AND (FIRST_PDATE:[{date}])'
        ),
        "YEAST": (
            '(TITLE_ABS:"Saccharomyces cerevisiae" OR TITLE_ABS:"Saccharomyces boulardii" '
            'OR TITLE_ABS:boulardii OR TITLE_ABS:"engineered yeast" OR TITLE_ABS:"yeast-based" '
            'OR TITLE_ABS:"synthetic yeast" OR TITLE_ABS:"yeast surface display") '
            'AND (TITLE_ABS:"living material*" OR TITLE_ABS:bioink OR TITLE_ABS:bioprint* '
            'OR TITLE_ABS:"3D print*" OR TITLE_ABS:hydrogel* OR TITLE_ABS:film* OR TITLE_ABS:fiber* '
            'OR TITLE_ABS:fibre* OR TITLE_ABS:material* OR TITLE_ABS:probiotic* '
            'OR TITLE_ABS:biotherapeut* OR TITLE_ABS:therapeut* OR TITLE_ABS:coating* '
            'OR TITLE_ABS:scaffold*) '
            f'AND (FIRST_PDATE:[{date}])'
        ),
        "LIVINGFORMS": (
            '(TITLE_ABS:"living hydrogel*" OR TITLE_ABS:"living fiber*" OR TITLE_ABS:"living fibre*" '
            'OR TITLE_ABS:"living film*" OR TITLE_ABS:"living coating*" OR TITLE_ABS:"living membrane*" '
            'OR TITLE_ABS:"living ink*" OR TITLE_ABS:"living textile*" OR TITLE_ABS:"living composite*" '
            'OR TITLE_ABS:"living fabric*" OR TITLE_ABS:"living scaffold*" OR TITLE_ABS:"living paint*" '
            'OR TITLE_ABS:"living foam*" OR TITLE_ABS:"living adhesive*") '
            f'AND (FIRST_PDATE:[{date}])'
        ),
    }


def fetch(url, tries=8, wait=6):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            print("  retry", i + 1, str(e)[:70])
            time.sleep(wait * (i // 2 + 1))
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.getcwd())
    ap.add_argument("--from", dest="dfrom", required=True)
    ap.add_argument("--to", dest="dto", required=True)
    ap.add_argument("--max-pages", type=int, default=8)
    args = ap.parse_args()

    date = f"{args.dfrom} TO {args.dto}"
    raw_path = os.path.join(args.dir, "raw", "epmc_raw.json")
    raw = json.load(open(raw_path, encoding="utf-8")) if os.path.exists(raw_path) else {}

    for name, q in queries(date).items():
        print(f"=== EPMC {name} ===")
        cursor, items = "*", []
        for page in range(args.max_pages):
            params = {"query": q, "format": "json", "pageSize": "100",
                      "resultType": "core", "cursorMark": cursor}
            data = fetch(EPMC + "?" + urllib.parse.urlencode(params))
            if not data:
                print("  page", page, "FAILED"); break
            res = data.get("resultList", {}).get("result", [])
            items.extend(res)
            print(f"  page {page}: {len(res)} hits (total {data.get('hitCount')})")
            nxt = data.get("nextCursorMark")
            if not nxt or nxt == cursor or not res:
                break
            cursor = nxt
            time.sleep(1.5)
        raw[name] = items
        print(f"{name}: {len(items)} records")
        time.sleep(1.5)

    json.dump(raw, open(raw_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("saved to", raw_path, "| topics:", {k: len(v) for k, v in raw.items()})


if __name__ == "__main__":
    main()
