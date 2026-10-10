# -*- coding: utf-8 -*-
"""Export BibTeX + manifest for the CURRENT batch (CN titles optional/deferred).

Usage:
  python elm_export_bib.py --dir WORKDIR --prefix 2020
Writes:
  02_BibTeX/ELM_<prefix>_library.bib
  02_BibTeX/naming_manifest_<prefix>.csv
"""
import argparse, csv, json, os, re


def bibtex_escape(s):
    return (s or "").replace("&", r"\&").replace("%", r"\%").replace("_", r"\_").replace("#", r"\#")


def make_key(rec):
    au = (rec.get("authors") or ["anon"])[0]
    au = re.sub(r"[^A-Za-z]", "", au.split()[-1] if au else "anon") or "anon"
    yr = (rec.get("date") or "2020")[:4]
    kw = re.sub(r"[^A-Za-z]", "", rec["title"].split()[0])[:8] or "paper"
    return f"{au}{yr}{kw}"


def art_type(rec):
    pts = [p.lower() for p in (rec.get("pubtypes") or [])]
    return "综述/观点" if any("review" in p for p in pts) else "研究论文"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.getcwd())
    ap.add_argument("--prefix", default="2020")
    ap.add_argument("--year", default=None, help="only export records whose date starts with this year")
    args = ap.parse_args()
    base = args.dir
    db = json.load(open(os.path.join(base, "literature_database.json"), encoding="utf-8"))
    if args.year:
        db = [r for r in db if (r.get("date") or "").startswith(args.year)]
        print("year filter", args.year, "->", len(db), "records")

    cn_map = {}
    cn_path = os.path.join(base, "cn_titles.json")
    if os.path.exists(cn_path):
        cn_map = json.load(open(cn_path, encoding="utf-8"))

    def cn_of(title):
        for k, v in cn_map.items():
            if title.startswith(k):
                return v
        return "待译"

    bib_dir = os.path.join(base, "02_BibTeX")
    os.makedirs(bib_dir, exist_ok=True)

    seen, entries, rows = set(), [], []
    for rec in db:
        t = rec["title"]
        if t in seen:
            continue
        seen.add(t)
        key = make_key(rec)
        yr = (rec.get("date") or "2020")[:4]
        doi = rec.get("doi")
        authors_bib = " and ".join(rec.get("authors") or [])
        jt = rec.get("journal") or "preprint"
        doi_line = f"  doi     = {{{doi}}},\n  url     = {{https://doi.org/{doi}}},\n" if doi else ""
        entries.append(f"@article{{{key},\n  title   = {{{bibtex_escape(t)}}},\n"
                       f"  author  = {{{bibtex_escape(authors_bib)}}},\n"
                       f"  journal = {{{bibtex_escape(jt)}}},\n  year    = {{{yr}}},\n"
                       f"{doi_line}}}")
        rows.append([args.prefix, rec.get("date"), rec.get("journal_abbrev") or rec.get("journal") or "?",
                     rec.get("journal_group", ""), art_type(rec), cn_of(t), t,
                     rec.get("corresponding_author") or "-", doi or "-", (rec.get("authors") or [""])[0] or "-"])

    open(os.path.join(bib_dir, f"ELM_{args.prefix}_library.bib"), "w", encoding="utf-8").write("\n\n".join(entries))
    with open(os.path.join(bib_dir, f"naming_manifest_{args.prefix}.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["批次", "发表日期", "期刊", "期刊分组", "文献类型", "中文名(待译)", "英文原题",
                    "通讯作者(推定)", "DOI", "第一作者"])
        w.writerows(rows)
    print("bib entries:", len(entries), "| manifest rows:", len(rows))
    print("research:", sum(1 for r in rows if r[4] == "研究论文"), "| review:", sum(1 for r in rows if r[4] == "综述/观点"))


if __name__ == "__main__":
    main()
