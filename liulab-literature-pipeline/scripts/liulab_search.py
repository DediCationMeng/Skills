#!/usr/bin/env python3
"""
LiuLab Literature Pipeline - PubMed Search Script (7 Topic Groups)

Usage:
  python liulab_search.py --topic GUT --from 2026-01-01 --to 2026-10-01
  python liulab_search.py --topic PROBIO --from 2025-01-01 --to 2025-12-31
  python liulab_search.py --all-topics --from 2026-01-01 --to 2026-10-01
"""

import argparse
import json
import os
import ssl
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

NCBI_API_KEY = None
ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

# === 7 Topic Query Groups (LiuLab-specific) ===
TOPICS = {
    "GUT": (
        '("gut microbiome"[Title/Abstract] OR "gut microbiota"[Title/Abstract] OR '
        '"intestinal flora"[Title/Abstract] OR "gut microflora"[Title/Abstract] OR '
        '"inflammatory bowel disease"[Title/Abstract] OR "IBD"[Title/Abstract] OR '
        '"colitis"[Title/Abstract] OR "ulcerative colitis"[Title/Abstract] OR '
        '"Crohn*"[Title/Abstract] OR "dysbiosis"[Title/Abstract] OR '
        '"intestinal barrier"[Title/Abstract] OR "mucosal immunity"[Title/Abstract] OR '
        '"non-alcoholic fatty liver"[Title/Abstract] OR "NAFLD"[Title/Abstract] OR '
        '"hepatic encephalopathy"[Title/Abstract] OR "intestinal infection"[Title/Abstract] OR '
        '"C. difficile"[Title/Abstract] OR "Clostridioides difficile"[Title/Abstract] OR '
        '"gut-liver axis"[Title/Abstract] OR "gut-brain axis"[Title/Abstract])'
    ),
    "PROBIO": (
        '("engineered bacteria"[Title/Abstract] OR "engineered probiotic*"[Title/Abstract] OR '
        '"live biotherapeutic*"[Title/Abstract] OR "Lactobacillus"[Title/Abstract] OR '
        '"Lactiplantibacillus"[Title/Abstract] OR "Bifidobacterium"[Title/Abstract] OR '
        '"Escherichia coli Nissle"[Title/Abstract] OR "EcN"[Title/Abstract] OR '
        '"bacterial therapy"[Title/Abstract] OR "probiotic therapy"[Title/Abstract] OR '
        '"bacterial ghost"[Title/Abstract] OR "outer membrane vesicle"[Title/Abstract] OR '
        '"OMV"[Title/Abstract] OR "protoplast"[Title/Abstract] OR '
        '"genetically engineered bacteria"[Title/Abstract] OR "chassis bacteria"[Title/Abstract])'
    ),
    "DELIVERY": (
        '("oral delivery"[Title/Abstract] OR "mucosal delivery"[Title/Abstract] OR '
        '"colon-targeted"[Title/Abstract] OR "colon-specific"[Title/Abstract] OR '
        '"enteric"[Title/Abstract] OR "mucoadhesive"[Title/Abstract] OR '
        '"mucoadhesion"[Title/Abstract] OR "oral vaccine"[Title/Abstract] OR '
        '"mucosal vaccination"[Title/Abstract] OR "oral peptide delivery"[Title/Abstract] OR '
        '"probiotic delivery"[Title/Abstract] OR "pH-responsive"[Title/Abstract] OR '
        '"intestinal patch"[Title/Abstract] OR "gut-targeted"[Title/Abstract])'
    ),
    "BIOMAT": (
        '(("engineered bacteria"[Title/Abstract] OR "probiotic*"[Title/Abstract] OR '
        '"bacteria"[Title/Abstract] OR "microbial"[Title/Abstract]) AND '
        '("hydrogel"[Title/Abstract] OR "3D print*"[Title/Abstract] OR "bioprint*"[Title/Abstract] OR '
        '"nanoparticle*"[Title/Abstract] OR "biomaterial*"[Title/Abstract] OR "scaffold"[Title/Abstract] OR '
        '"living material*"[Title/Abstract] OR "biofilm"[Title/Abstract] OR '
        '"living hydrogel"[Title/Abstract] OR "bacterial hydrogel"[Title/Abstract] OR '
        '"living coating"[Title/Abstract] OR "living ink"[Title/Abstract]))'
    ),
    "GUTAXIS": (
        '("gut-brain axis"[Title/Abstract] OR "gut-liver axis"[Title/Abstract] OR '
        '"gut-skin axis"[Title/Abstract] OR "gut-eye axis"[Title/Abstract] OR '
        '"microbial metabolite*"[Title/Abstract] OR "short-chain fatty acid*"[Title/Abstract] OR '
        '"SCFA"[Title/Abstract] OR "tryptophan metabolism"[Title/Abstract] OR '
        '"bile acid*"[Title/Abstract] OR "indole"[Title/Abstract] OR '
        '"microbiota-gut-brain"[Title/Abstract] OR "gut permeability"[Title/Abstract] OR '
        '"intestinal permeability"[Title/Abstract])'
    ),
    "CONTROL": (
        '(("engineered bacteria"[Title/Abstract] OR "probiotic*"[Title/Abstract] OR '
        '"bacterial"[Title/Abstract]) AND '
        '("spatiotemporal"[Title/Abstract] OR "stimuli-responsive"[Title/Abstract] OR '
        '"ultrasound"[Title/Abstract] OR "magnetic"[Title/Abstract] OR "NIR"[Title/Abstract] OR '
        '"near-infrared"[Title/Abstract] OR "photothermal"[Title/Abstract] OR '
        '"light-triggered"[Title/Abstract] OR "pH-responsive"[Title/Abstract] OR '
        '"enzyme-responsive"[Title/Abstract] OR "thermo-responsive"[Title/Abstract]))'
    ),
    "TUMOR": (
        '((("engineered bacteria"[Title/Abstract] OR "bacterial therapy"[Title/Abstract] OR '
        '"probiotic*"[Title/Abstract] OR "bacteria-mediated"[Title/Abstract]) AND '
        '("tumor"[Title/Abstract] OR "cancer"[Title/Abstract] OR "immunotherapy"[Title/Abstract] OR '
        '"tumor microenvironment"[Title/Abstract] OR "antitumor"[Title/Abstract]))'
        ' OR '
        # 非细菌肿瘤免疫支路：瘤内疫苗/检查点/抗原呈递/溶瘤病毒（补漏 Nature 瘤内疫苗类工作）
        '(("intratumoural"[Title/Abstract] OR "intratumoral"[Title/Abstract] OR '
        '"in situ vaccination"[Title/Abstract] OR "cancer vaccin*"[Title/Abstract] OR '
        '"tumor vaccin*"[Title/Abstract] OR "tumour vaccin*"[Title/Abstract] OR '
        '"oncolytic"[Title/Abstract] OR "checkpoint degradation"[Title/Abstract] OR '
        '"antigen presentation"[Title/Abstract] OR "antigen cross-presentation"[Title/Abstract] OR '
        '"antitumor immunity"[Title/Abstract] OR "anti-tumor immunity"[Title/Abstract] OR '
        '"anti-tumour immunity"[Title/Abstract]) AND '
        '("tumor"[Title/Abstract] OR "tumour"[Title/Abstract] OR "cancer"[Title/Abstract])))'
    ),
    "REGEN": (
        '(("tissue regeneration"[Title/Abstract] OR "tissue repair"[Title/Abstract] OR '
        '"regenerative medicine"[Title/Abstract] OR "wound healing"[Title/Abstract] OR '
        '"haemostasis"[Title/Abstract] OR "hemostasis"[Title/Abstract] OR '
        '"blood clot"[Title/Abstract] OR "3D print*"[Title/Abstract] OR "bioprint*"[Title/Abstract] OR '
        '"hydrogel"[Title/Abstract] OR "scaffold"[Title/Abstract] OR '
        '"cardiac repair"[Title/Abstract] OR "heart repair"[Title/Abstract] OR '
        '"corneal repair"[Title/Abstract] OR "organ repair"[Title/Abstract] OR '
        '"biomaterial*"[Title/Abstract] OR "living material*"[Title/Abstract] OR '
        '"stem cell"[Title/Abstract] OR "organoid"[Title/Abstract]) AND '
        '("regeneration"[Title/Abstract] OR "repair"[Title/Abstract] OR "healing"[Title/Abstract] OR '
        '"engineering"[Title/Abstract] OR "biomaterial*"[Title/Abstract] OR "3D print*"[Title/Abstract] OR '
        '"bioprint*"[Title/Abstract] OR "scaffold"[Title/Abstract] OR "hydrogel"[Title/Abstract] OR '
        '"tissue engineering"[Title/Abstract] OR "living material*"[Title/Abstract]))'
    ),
    # TOPJ 顶级期刊兜底扫掠：白名单期刊 ISSN 精确匹配 × 宽方向关键词。
    # 动机（2026-10 复盘）：关键词组在海量结果里按相关度排序后截断（GUT 组 2026 窗口内 3.2 万篇），
    # 题名与查询词重合度低的顶级论文会被挤出 retmax 之外；另有非细菌肿瘤免疫等关键词盲区。
    # ISSN 匹配比 [Journal] 名称匹配精确（避免 Nature 扩展到子刊、Adv Mater 匹配失败两类坑）；
    # Nature Cancer / Cell Discovery 的 ISSN 未被 PubMed 索引，退化为刊名匹配。
    # 语法注意：PubMed 合法写法是 ("..." OR "...")[Title/Abstract]，不是 Title/Abstract:(...)。
    # 用法：--topic TOPJ --max 20000 分页全量拉取，再走白名单+相关度筛选。
    "TOPJ": (
        # ---- 白名单 50 刊（ISSN 优先 + 2 刊名兜底）----
        '(0028-0836[ISSN] OR 2041-1723[ISSN] OR 1087-0156[ISSN] OR 1078-8956[ISSN] OR '
        '1476-1122[ISSN] OR 2157-846X[ISSN] OR 2058-5276[ISSN] OR 1755-4330[ISSN] OR '
        '2522-5812[ISSN] OR 1548-7091[ISSN] OR 1529-2908[ISSN] OR 2662-1991[ISSN] OR '
        '"Nature cancer"[Journal] OR 1759-5045[ISSN] OR 1740-1526[ISSN] OR 1465-7392[ISSN] OR '
        '0036-8075[ISSN] OR 2375-2548[ISSN] OR 2470-9476[ISSN] OR 1946-6234[ISSN] OR '
        '2470-9468[ISSN] OR 2095-9273[ISSN] OR '
        '0092-8674[ISSN] OR 1550-4131[ISSN] OR 1931-3128[ISSN] OR 1934-5909[ISSN] OR '
        '1535-6108[ISSN] OR 1074-7613[ISSN] OR 0896-6273[ISSN] OR 1097-2765[ISSN] OR '
        '2451-9294[ISSN] OR 2590-2385[ISSN] OR 2666-3791[ISSN] OR 2451-9448[ISSN] OR '
        '"Cell discovery"[Journal] OR 2405-4712[ISSN] OR '
        '0935-9648[ISSN] OR 1616-301X[ISSN] OR 2198-3844[ISSN] OR 0002-7863[ISSN] OR '
        '1433-7851[ISSN] OR '
        '0017-5749[ISSN] OR 0016-5085[ISSN] OR 0270-9139[ISSN] OR 2049-2618[ISSN] OR '
        '2059-3635[ISSN] OR 1936-0851[ISSN] OR 1949-0976[ISSN] OR 2192-2640[ISSN]) '
        'AND '
        # ---- 宽方向关键词（LiuLab 维度全覆盖 + 非细菌肿瘤免疫）----
        '(("gut microbiome" OR "gut microbiota" OR "intestinal flora" OR '
        '"gut microflora" OR "dysbiosis" OR "intestinal barrier" OR "mucosal immunity" OR '
        '"inflammatory bowel disease" OR "IBD" OR "colitis" OR "Crohn*" OR '
        '"C. difficile" OR "Clostridioides" OR "gut-liver axis" OR "gut-brain axis" OR '
        '"non-alcoholic fatty liver" OR "NAFLD" OR "hepatic encephalopathy" OR '
        '"engineered bacteria" OR "engineered probiotic*" OR "live biotherapeutic*" OR '
        '"probiotic*" OR "Lactobacillus" OR "Lactiplantibacillus" OR "Bifidobacterium" OR '
        '"Escherichia coli Nissle" OR "EcN" OR "bacterial therapy" OR "bacteria-mediated" OR '
        '"bacterial ghost" OR "outer membrane vesicle" OR "OMV" OR "chassis bacteria" OR '
        '"oral delivery" OR "mucosal delivery" OR "colon-targeted" OR "colon-specific" OR '
        '"mucoadhesive" OR "oral vaccine" OR "mucosal vaccination" OR "probiotic delivery" OR '
        '"hydrogel" OR "3D print*" OR "bioprint*" OR "biomaterial*" OR "scaffold" OR '
        '"living material*" OR "living hydrogel" OR "bacterial hydrogel" OR "biofilm" OR '
        '"wound healing" OR "tissue regeneration" OR "tissue repair" OR "haemostasis" OR '
        '"hemostasis" OR "blood clot" OR "cardiac repair" OR "organoid" OR "regenerative medicine" OR '
        '"microbial metabolite*" OR "short-chain fatty acid*" OR "SCFA" OR "tryptophan metabolism" OR '
        '"bile acid*" OR "microbiota-gut-brain" OR "intestinal permeability" OR '
        '"spatiotemporal" OR "stimuli-responsive" OR "ultrasound" OR "magnetic" OR '
        '"near-infrared" OR "photothermal" OR "light-triggered" OR "pH-responsive" OR '
        '"enzyme-responsive" OR '
        '"tumor" OR "tumour" OR "cancer" OR "immunotherapy" OR "tumor microenvironment" OR '
        '"antitumor" OR "antitumour" OR '
        '"intratumoural" OR "intratumoral" OR "in situ vaccination" OR '
        '"cancer vaccin*" OR "tumor vaccin*" OR "tumour vaccin*" OR "oncolytic" OR '
        '"checkpoint degradation" OR "antigen presentation" OR "antigen cross-presentation" OR '
        '"antitumor immunity" OR "anti-tumor immunity" OR "anti-tumour immunity")[Title/Abstract])'
    ),
}

# Journal whitelist (A-F groups) for reference
TOP_JOURNALS = {
    "Nature", "Science", "Cell",
    "Nature Communications", "Nature Biotechnology", "Nature Medicine",
    "Nature Materials", "Nature Biomedical Engineering", "Nature Microbiology",
    "Nature Chemistry", "Nature Metabolism", "Nature Methods", "Nature Aging",
    "Nature Cancer", "Nature Immunology", "Nature Reviews Gastroenterology & Hepatology",
    "Nature Reviews Microbiology",
    "Science Translational Medicine", "Science Advances",
    "Cell Metabolism", "Cell Host & Microbe", "Cancer Cell", "Immunity",
    "Advanced Materials", "Advanced Functional Materials", "Advanced Science",
    "Journal of the American Chemical Society",
    "Angewandte Chemie International Edition",
    "Biomaterials", "Gut", "Gastroenterology", "Hepatology",
    "Journal of Clinical Investigation", "Microbiome",
}


def fetch_pubmed(query, max_results=100, date_from=None, date_to=None, sort="relevance"):
    """Search PubMed with date range and return structured results.
    支持分页拉取（每次 200 条），避免 retmax 截断漏检。sort=relevance|pub_date。
    """
    if date_from and date_to:
        query += f' AND ("{date_from}"[Date - Publication] : "{date_to}"[Date - Publication])'

    id_list = []
    count = "0"
    retstart = 0
    page = 200
    while len(id_list) < max_results:
        params = {
            "db": "pubmed", "term": query,
            "retmax": str(min(page, max_results - len(id_list))),
            "retstart": str(retstart), "retmode": "json", "sort": sort,
        }
        if NCBI_API_KEY:
            params["api_key"] = NCBI_API_KEY

        url = ESEARCH_URL + "?" + urllib.parse.urlencode(params)
        with urllib.request.urlopen(url, timeout=60) as resp:
            data = json.loads(resp.read().decode())

        batch = data.get("esearchresult", {}).get("idlist", [])
        count = data.get("esearchresult", {}).get("count", "0")
        id_list.extend(batch)
        if not batch or len(batch) < page:
            break
        retstart += len(batch)

    if not id_list:
        return {"total": int(count), "results": []}

    results = []
    uids_all = []
    # esummary 分批（每批 200 个 PMID），避免 URL 超长
    for i in range(0, len(id_list), 200):
        chunk = id_list[i:i + 200]
        params2 = {"db": "pubmed", "id": ",".join(chunk), "retmode": "json"}
        if NCBI_API_KEY:
            params2["api_key"] = NCBI_API_KEY
        url2 = ESUMMARY_URL + "?" + urllib.parse.urlencode(params2)
        with urllib.request.urlopen(url2, timeout=60) as resp:
            summaries = json.loads(resp.read().decode())
        uids_all.extend(summaries.get("result", {}).get("uids", []))
        # 暂存到 results 前先统一处理
        if "result" not in summaries:
            continue
        for uid in summaries["result"].get("uids", []):
            item = summaries["result"][uid]
            pubdate = item.get("pubdate", "")
            journal = item.get("fulljournalname", item.get("source", ""))
            title = item.get("title", "")
            doi = ""
            for aid in item.get("articleids", []):
                if aid.get("idtype") == "doi":
                    doi = aid.get("value", "")
                    break

            score = 1.5 if any(j.lower() in journal.lower() for j in TOP_JOURNALS) else 1.0

            results.append({
                "pmid": uid, "title": title, "journal": journal,
                "pubdate": pubdate, "doi": doi,
                "score": round(score, 2),
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return {"total": int(count), "results": results}


def main():
    parser = argparse.ArgumentParser(description="LiuLab Literature Pipeline - PubMed Search")
    parser.add_argument("--topic", choices=list(TOPICS.keys()), help="Topic group to search")
    parser.add_argument("--all-topics", action="store_true", help="Run all 7 topic groups")
    parser.add_argument("--from", dest="date_from", required=True, help="Start date YYYY-MM-DD")
    parser.add_argument("--to", dest="date_to", required=True, help="End date YYYY-MM-DD")
    parser.add_argument("--max", type=int, default=100, help="Max results per topic")
    parser.add_argument("--output", type=str, default="raw/epmc_raw.json", help="Output JSON path")
    args = parser.parse_args()

    topics_to_run = list(TOPICS.keys()) if args.all_topics else [args.topic]
    if not topics_to_run:
        print("Error: provide --topic or --all-topics", file=sys.stderr)
        sys.exit(1)

    all_results = []
    for topic in topics_to_run:
        query = TOPICS[topic]
        print(f"[{topic}] Searching...", file=sys.stderr)
        data = fetch_pubmed(query, max_results=args.max,
                           date_from=args.date_from, date_to=args.date_to)
        for r in data["results"]:
            r["topic"] = topic
        all_results.extend(data["results"])
        print(f"[{topic}] Found {data['total']} total, {len(data['results'])} retrieved", file=sys.stderr)

    # Deduplicate by PMID
    seen = set()
    unique = []
    for r in all_results:
        if r["pmid"] not in seen:
            seen.add(r["pmid"])
            unique.append(r)

    output = {
        "search_date": datetime.now().isoformat(),
        "date_range": f"{args.date_from} to {args.date_to}",
        "topics": topics_to_run,
        "total_unique": len(unique),
        "results": unique,
    }

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nTotal unique results: {len(unique)}")
    print(f"Saved to: {args.output}")


if __name__ == "__main__":
    main()
