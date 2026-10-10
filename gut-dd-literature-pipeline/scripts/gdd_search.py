# -*- coding: utf-8 -*-
"""Europe PMC + arXiv retrieval for gut-targeted drug delivery carriers (2026-10-09 新建).

Focus: (1) development of drug delivery carriers (nanocarriers/liposomes/LNPs/polymeric
nanoparticles/exosomes ...); (2) gut-targeted delivery (gut / intestine / colon) and its
biomedical applications. Keyword classes (user-specified 2026-10-09):
  CORE   - drug delivery / drug delivery system (DDS) / drug carrier / delivery vehicle /
           nanocarrier / nanomedicine / nanoformulation / pharmaceutical formulation
  GUT    - gut, intestine*, colon*, colonic, gastrointestinal, ileum/jejunum/duodenum ...
  CARRIER- nanoparticle*/liposome*/micelle*/hydrogel*/exosome* ... (载体总称)
  APP    - therapeutic / disease / bioavailability / microbiome / IBD ... (生物医学应用)
Derived from elm-literature-pipeline; plasmonics/ELM queries kept in that skill.

Usage:
  python gdd_search.py --from 2026-09-09 --to 2026-10-09 [--dir WORKDIR] [--max-pages 5]

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


# ---- 关键词块（2026-10-09 用户指定：核心主题词 + 肠道词；与 gdd_search_extra.py 保持一致）----
CORE = (
    '(TITLE_ABS:"drug delivery" OR TITLE_ABS:"drug delivery system*" '
    'OR TITLE_ABS:DDS OR TITLE_ABS:"drug carrier*" OR TITLE_ABS:"delivery vehicle*" '
    'OR TITLE_ABS:nanocarrier* OR TITLE_ABS:nanomedicine* OR TITLE_ABS:nanomedicinal '
    'OR TITLE_ABS:nanoformulation* OR TITLE_ABS:"pharmaceutical formulation*")'
)
CARRIER = (
    '(TITLE_ABS:nanocarrier* OR TITLE_ABS:nanoparticle* OR TITLE_ABS:liposome* '
    'OR TITLE_ABS:"lipid nanoparticle*" OR TITLE_ABS:"polymeric nanoparticle*" '
    'OR TITLE_ABS:micelle* OR TITLE_ABS:dendrimer* OR TITLE_ABS:hydrogel* '
    'OR TITLE_ABS:microsphere* OR TITLE_ABS:nanocrystal* OR TITLE_ABS:exosome* '
    'OR TITLE_ABS:"extracellular vesicle*")'
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
APP = (
    '(TITLE_ABS:therapeut* OR TITLE_ABS:treatment* OR TITLE_ABS:biomedic* '
    'OR TITLE_ABS:disease* OR TITLE_ABS:bioavailabilit* OR TITLE_ABS:absorption '
    'OR TITLE_ABS:microbiome OR TITLE_ABS:"gut microbiota" '
    'OR TITLE_ABS:"inflammatory bowel" OR TITLE_ABS:IBD OR TITLE_ABS:Crohn '
    'OR TITLE_ABS:"ulcerative colitis" OR TITLE_ABS:pharmacokinet* OR TITLE_ABS:diagnos*)'
)


def queries(date):
    return {
        # 核心主题词 x 载体总称 -> 药物递送载体开发（宽检索）
        "DD-CORE": f'{CORE} AND {CARRIER} AND (FIRST_PDATE:[{date}])',
        # 核心主题词 x 肠道词 -> 肠道靶向药物递送载体的开发（核心需求）
        "GUT-DD": f'{CORE} AND {GUT} AND (FIRST_PDATE:[{date}])',
        # 载体 x 肠道 x 生物医学应用词 -> 靶向肠道载体的生物医学应用
        "GUT-BIO": f'{CARRIER} AND {GUT} AND {APP} AND (FIRST_PDATE:[{date}])',
    }


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
    q = ('(all:"drug delivery" OR all:nanocarrier OR all:"drug carrier" '
         'OR all:nanomedicine OR all:nanoformulation OR all:"lipid nanoparticle") '
         'AND (all:gut OR all:intestine OR all:intestinal OR all:colon OR all:colonic '
         'OR all:gastrointestinal OR all:enteral)')
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
