# -*- coding: utf-8 -*-
"""Supplementary EuropePMC queries for gut-targeted drug delivery (2026-10-09 新建):
  DD-CARRIER  - 具体载体类型细化：脂质体/LNP/PLGA/壳聚糖/树状大分子/MOF/介孔硅/外泌体等
  GUT-ORAL    - 口服与肠道递送策略：colon-specific、enteric、mucus、Peyer's patch、菌群等
  DD-STRATEGY - 功能策略与前沿：靶向/控释/刺激响应/基因递送/PEG 化/诊疗一体化

关键词块 CORE/GUT 与 gdd_search.py 保持一致（用户 2026-10-09 指定：核心主题词 + 肠道词）。
Merges results into raw/epmc_raw.json under these topic keys (idempotent overwrite per topic).

Usage:
  python gdd_search_extra.py --dir WORKDIR --from 2020-01-01 --to 2020-12-31 [--max-pages 8]
"""
import argparse, json, os, ssl, time, urllib.parse, urllib.request

EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0 (research-literature-agent)"}

# ---- 关键词块（与 gdd_search.py 保持一致）----
CORE = (
    '(TITLE_ABS:"drug delivery" OR TITLE_ABS:"drug delivery system*" '
    'OR TITLE_ABS:DDS OR TITLE_ABS:"drug carrier*" OR TITLE_ABS:"delivery vehicle*" '
    'OR TITLE_ABS:nanocarrier* OR TITLE_ABS:nanomedicine* OR TITLE_ABS:nanomedicinal '
    'OR TITLE_ABS:nanoformulation* OR TITLE_ABS:"pharmaceutical formulation*")'
)
GUT = (
    '(TITLE_ABS:gut OR TITLE_ABS:gastrointestin* OR TITLE_ABS:intestin* '
    'OR TITLE_ABS:colon OR TITLE_ABS:colonic OR TITLE_ABS:colorectal '
    'OR TITLE_ABS:"colon-specific" OR TITLE_ABS:"colon-target*" OR TITLE_ABS:"gut-target*" '
    'OR TITLE_ABS:bowel OR TITLE_ABS:ileum OR TITLE_ABS:ileal OR TITLE_ABS:jejunum '
    'OR TITLE_ABS:jejunal OR TITLE_ABS:duodenum OR TITLE_ABS:duodenal '
    'OR TITLE_ABS:cecum OR TITLE_ABS:caecum OR TITLE_ABS:rectum OR TITLE_ABS:enteral '
    'OR TITLE_ABS:"gastrointestinal tract" OR TITLE_ABS:"GI tract")'
)
CARRIER_DETAIL = (
    '(TITLE_ABS:liposome* OR TITLE_ABS:"lipid nanoparticle*" '
    'OR TITLE_ABS:"solid lipid nanoparticle*" OR TITLE_ABS:PLGA OR TITLE_ABS:chitosan '
    'OR TITLE_ABS:dendrimer* OR TITLE_ABS:polymersome* OR TITLE_ABS:niosome* '
    'OR TITLE_ABS:"metal-organic framework*" OR TITLE_ABS:MOF '
    'OR TITLE_ABS:"mesoporous silica*" OR TITLE_ABS:"cell membrane-coated" '
    'OR TITLE_ABS:exosome* OR TITLE_ABS:"extracellular vesicle*" '
    'OR TITLE_ABS:"albumin nanoparticle*" OR TITLE_ABS:nanocrystal* '
    'OR TITLE_ABS:hydrogel* OR TITLE_ABS:microsphere* OR TITLE_ABS:emulsion*)'
)
GUT_STRATEGY = (
    '(TITLE_ABS:"oral delivery" OR TITLE_ABS:"oral drug delivery" OR TITLE_ABS:enteric '
    'OR TITLE_ABS:"colon-specific" OR TITLE_ABS:"colon-targeted" OR TITLE_ABS:"site-specific" '
    'OR TITLE_ABS:"mucus penetration" OR TITLE_ABS:"mucus-penetrating" OR TITLE_ABS:mucus '
    'OR TITLE_ABS:"Peyer\'s patch*" OR TITLE_ABS:"intestinal absorption" '
    'OR TITLE_ABS:"intestinal permeab*" OR TITLE_ABS:"gut microbiota" OR TITLE_ABS:microbiome '
    'OR TITLE_ABS:bioavailabilit*)'
)
DD_LITE = (
    '(TITLE_ABS:"drug deliver*" OR TITLE_ABS:nanocarrier* OR TITLE_ABS:"drug carrier*" '
    'OR TITLE_ABS:formulation* OR TITLE_ABS:liposome* OR TITLE_ABS:nanoparticle*)'
)
STRATEGY = (
    '(TITLE_ABS:targeting OR TITLE_ABS:"controlled release" OR TITLE_ABS:"sustained release" '
    'OR TITLE_ABS:"stimuli-responsive" OR TITLE_ABS:"pH-responsive" '
    'OR TITLE_ABS:"responsive release" OR TITLE_ABS:"gene delivery" '
    'OR TITLE_ABS:siRNA OR TITLE_ABS:mRNA OR TITLE_ABS:CRISPR '
    'OR TITLE_ABS:theranostic* OR TITLE_ABS:PEGylation OR TITLE_ABS:"oral delivery")'
)


def queries(date):
    return {
        # 核心主题词 x 具体载体类型（CARRIER 总称之外的细化）
        "DD-CARRIER": f'{CORE} AND {CARRIER_DETAIL} AND (FIRST_PDATE:[{date}])',
        # 肠道词 x 口服/肠道递送策略 x 递送载体 -> 肠道靶向递送的应用场景
        "GUT-ORAL": f'{GUT} AND {GUT_STRATEGY} AND {DD_LITE} AND (FIRST_PDATE:[{date}])',
        # 核心主题词 x 功能策略 -> 靶向/控释/刺激响应/基因递送/诊疗一体化
        "DD-STRATEGY": f'{CORE} AND {STRATEGY} AND (FIRST_PDATE:[{date}])',
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
