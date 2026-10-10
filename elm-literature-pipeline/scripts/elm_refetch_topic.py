# -*- coding: utf-8 -*-
"""Re-fetch ONE EuropePMC topic that failed (e.g. 503) and MERGE into raw/epmc_raw.json.

Usage:
  python elm_refetch_topic.py --dir WORKDIR --topic ELM --from 2020-01-01 --to 2020-12-31 [--max-pages 8]
"""
import argparse, json, os, ssl, time, urllib.parse, urllib.request

EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0 (research-literature-agent)"}

QUERIES = {
    "ELM": '(TITLE_ABS:"engineered living material*" OR TITLE_ABS:"living materials") AND (FIRST_PDATE:[{d}])',
    "Bioprinting": '(TITLE_ABS:"bioprint*" OR TITLE_ABS:"3D print*" OR TITLE_ABS:"bioink" OR TITLE_ABS:"bio-ink" OR TITLE_ABS:"extrusion printing") AND (TITLE_ABS:cell* OR TITLE_ABS:bioink OR TITLE_ABS:tissue OR TITLE_ABS:hydrogel) AND (FIRST_PDATE:[{d}])',
    "LBP": '(TITLE_ABS:"live biotherapeutic*" OR TITLE_ABS:"live bacterial therapeut*" OR TITLE_ABS:"microbial therapeut*" OR TITLE_ABS:"cell-based therap*" OR TITLE_ABS:"bacterial therap*") AND (FIRST_PDATE:[{d}])',
    "Probiotics": '(TITLE_ABS:"engineered probiotic*" OR TITLE_ABS:"programmed bacteria" OR TITLE_ABS:"synthetic probiotic*" OR TITLE_ABS:"engineered bacteria" OR TITLE_ABS:"chassis organism" OR TITLE_ABS:"bacterial circuit") AND (TITLE_ABS:gut OR TITLE_ABS:therapeut* OR TITLE_ABS:probiotic* OR TITLE_ABS:microbiome OR TITLE_ABS:tumor OR TITLE_ABS:disease) AND (FIRST_PDATE:[{d}])',
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
    ap.add_argument("--topic", required=True, choices=list(QUERIES))
    ap.add_argument("--from", dest="dfrom", required=True)
    ap.add_argument("--to", dest="dto", required=True)
    ap.add_argument("--max-pages", type=int, default=8)
    args = ap.parse_args()

    date = f"{args.dfrom} TO {args.dto}"
    q = QUERIES[args.topic].format(d=date)
    cursor, items = "*", []
    for page in range(args.max_pages):
        params = {"query": q, "format": "json", "pageSize": "100",
                  "resultType": "core", "cursorMark": cursor}
        data = fetch(EPMC + "?" + urllib.parse.urlencode(params))
        if not data:
            print("page", page, "FAILED permanently")
            break
        res = data.get("resultList", {}).get("result", [])
        items.extend(res)
        print(f"  page {page}: {len(res)} hits (total {data.get('hitCount')})")
        nxt = data.get("nextCursorMark")
        if not nxt or nxt == cursor or not res:
            break
        cursor = nxt
        time.sleep(2)

    raw_path = os.path.join(args.dir, "raw", "epmc_raw.json")
    raw = json.load(open(raw_path, encoding="utf-8")) if os.path.exists(raw_path) else {}
    raw[args.topic] = items
    json.dump(raw, open(raw_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{args.topic}: {len(items)} records merged into {raw_path}")


if __name__ == "__main__":
    main()
