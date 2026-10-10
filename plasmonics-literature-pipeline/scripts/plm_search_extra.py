# -*- coding: utf-8 -*-
"""Supplementary EuropePMC queries for plasmonic nanomaterials (2026-10-09 起改为等离激元方向):
  EXOTIC-SHAPES - 扩展形貌：nanocage/nanoframe/nanoprism/nanodendrite/bimetallic 等
  BIO-APP       - 生物医学应用：SERS 成像、光热/光动力治疗、药物递送、抗菌等
  BIO-SENSING   - LSPR/SPR 生物传感与诊断

Derived from the elm-literature-pipeline skill (2026-10-09, independent copy).

Merges results into raw/epmc_raw.json under these topic keys (idempotent overwrite per topic).

Usage:
  python plm_search_extra.py --dir WORKDIR --from 2020-01-01 --to 2020-12-31 [--max-pages 8]
"""
import argparse, json, os, ssl, time, urllib.parse, urllib.request

EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0 (research-literature-agent)"}


def queries(date):
    return {
        # 核心概念 x 扩展形貌（PLASMON-SHAPE 之外的新结构/异质结构）
        "EXOTIC-SHAPES": (
            '(TITLE_ABS:plasmonic* OR TITLE_ABS:"localized surface plasmon" '
            'OR TITLE_ABS:"surface plasmon" OR TITLE_ABS:LSPR) '
            'AND (TITLE_ABS:nanocage* OR TITLE_ABS:nanoframe* OR TITLE_ABS:nanotriangle* '
            'OR TITLE_ABS:nanoprism* OR TITLE_ABS:nanodendrit* OR TITLE_ABS:nanourchin* '
            'OR TITLE_ABS:nanowire* OR TITLE_ABS:nanoantenna* OR TITLE_ABS:nanocone* '
            'OR TITLE_ABS:"hollow nanostructure*" OR TITLE_ABS:"yolk-shell" '
            'OR TITLE_ABS:"nanoparticle-on-mirror" OR TITLE_ABS:bimetallic '
            'OR TITLE_ABS:alloy* OR TITLE_ABS:nanocomposite*) '
            f'AND (FIRST_PDATE:[{date}])'
        ),
        # 生物医学应用扩展：SERS 成像/标签、光热光动力、声成像、递送、抗菌、神经调控
        "BIO-APP": (
            '(TITLE_ABS:plasmonic* OR TITLE_ABS:"gold nanoparticle*" '
            'OR TITLE_ABS:"silver nanoparticle*" OR TITLE_ABS:"gold nanorod*" '
            'OR TITLE_ABS:"surface-enhanced Raman" OR TITLE_ABS:SERS) '
            'AND (TITLE_ABS:"photothermal therap*" OR TITLE_ABS:"photodynamic" '
            'OR TITLE_ABS:photoacoustic OR TITLE_ABS:"SERS imaging" OR TITLE_ABS:"SERS tag*" '
            'OR TITLE_ABS:"cell imaging" OR TITLE_ABS:immunoassay OR TITLE_ABS:"drug deliver*" '
            'OR TITLE_ABS:antimicrobial OR TITLE_ABS:antibacterial OR TITLE_ABS:"wound healing" '
            'OR TITLE_ABS:neuromodulat* OR TITLE_ABS:neurostimulat* OR TITLE_ABS:theranostic*) '
            f'AND (FIRST_PDATE:[{date}])'
        ),
        # LSPR/SPR 生物传感与诊断（生物医学应用的传感侧）
        "BIO-SENSING": (
            '(TITLE_ABS:"localized surface plasmon resonance" OR TITLE_ABS:"surface plasmon resonance" '
            'OR TITLE_ABS:"plasmonic sensor*" OR TITLE_ABS:"plasmon sensing" OR TITLE_ABS:LSPR) '
            'AND (TITLE_ABS:biosensor* OR TITLE_ABS:sens* OR TITLE_ABS:detect* '
            'OR TITLE_ABS:diagnos* OR TITLE_ABS:assay OR TITLE_ABS:"refractive index" '
            'OR TITLE_ABS:imaging OR TITLE_ABS:biomedic*) '
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
