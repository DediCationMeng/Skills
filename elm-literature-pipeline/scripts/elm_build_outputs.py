# -*- coding: utf-8 -*-
"""Generate outputs from literature_database.json:
  - normalized naming: 年月-期刊简写-论文中文名
  - 02_BibTeX/ELM_<prefix>_library.bib  (Zotero-importable)
  - 02_BibTeX/naming_manifest.csv       (with 文献类型 column)
  - rename PDFs in 01_PDF/ to normalized names

CN titles come from cn_titles.json ({"<title-prefix-25+ chars>": "中文译名"}).
Fill it by translating each English title yourself before running.

Usage:
  python elm_build_outputs.py [--dir WORKDIR] [--prefix 2026-09]
"""
import argparse, csv, json, os, re, shutil


def bibtex_escape(s):
    return (s or "").replace("&", r"\&").replace("%", r"\%").replace("_", r"\_").replace("#", r"\#")


def make_key(rec):
    au = (rec.get("authors") or ["anon"])[0]
    au = re.sub(r"[^A-Za-z]", "", au.split()[-1] if au else "anon") or "anon"
    yr = (rec.get("date") or "2026")[:4]
    kw = re.sub(r"[^A-Za-z]", "", rec["title"].split()[0])[:8] or "paper"
    return f"{au}{yr}{kw}"


def journal_token(rec):
    ja = (rec.get("journal_abbrev") or "Preprint").split("(")[0].strip()
    ja = re.sub(r"[^A-Za-z]", "", ja)[:12]
    return ja or "Preprint"


def art_type(rec):
    pts = [p.lower() for p in (rec.get("pubtypes") or [])]
    return "综述/观点" if "review" in pts else "研究论文"


def cn_title_of(rec, cn_map):
    t = rec["title"]
    for k, v in cn_map.items():
        if t.startswith(k):
            return v
    return "未命名文献"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.getcwd())
    ap.add_argument("--prefix", default=None, help="BibTeX filename prefix, default = max date YYYY-MM")
    args = ap.parse_args()
    base = args.dir

    db = json.load(open(os.path.join(base, "literature_database.json"), encoding="utf-8"))
    cn_map = {}
    cn_path = os.path.join(base, "cn_titles.json")
    if os.path.exists(cn_path):
        cn_map = json.load(open(cn_path, encoding="utf-8"))
    else:
        print("WARNING: cn_titles.json not found - titles become 未命名文献. Translate titles first!")

    bib_dir = os.path.join(base, "02_BibTeX")
    os.makedirs(bib_dir, exist_ok=True)
    os.makedirs(os.path.join(base, "01_PDF"), exist_ok=True)

    prefix = args.prefix
    if not prefix:
        dates = [r.get("date") or "" for r in db if r.get("date")]
        prefix = (max(dates)[:7] if dates else "unknown")

    rows, entries = [], []
    seen = set()
    for rec in db:
        t = rec["title"]
        if t in seen:
            continue
        seen.add(t)

        ym_fmt = ((rec.get("date") or prefix + "-01").replace("-", ""))[:6]
        ym_fmt = ym_fmt[:4] + "-" + ym_fmt[4:]
        cn = cn_title_of(rec, cn_map)
        normalized = f"{ym_fmt}-{journal_token(rec)}-{cn}"
        rec["cn_title"] = cn
        rec["normalized_name"] = normalized
        rec["key"] = make_key(rec)

        # BibTeX
        authors_bib = " and ".join(rec.get("authors") or [])
        year = (rec.get("date") or "2026")[:4]
        doi = rec.get("doi")
        jt = rec.get("journal") or "preprint"
        if rec.get("source") == "arXiv":
            bib = (f"@article{{{rec['key']},\n  title   = {{{bibtex_escape(t)}}},\n"
                   f"  author  = {{{bibtex_escape(authors_bib)}}},\n"
                   f"  journal = {{arXiv preprint arXiv:{rec.get('id','')}}},\n"
                   f"  year    = {{{year}}},\n"
                   f"  url     = {{https://arxiv.org/abs/{rec.get('id','')}}},\n}}")
        else:
            doi_line = f"  doi     = {{{doi}}},\n  url     = {{https://doi.org/{doi}}},\n" if doi else ""
            bib = (f"@article{{{rec['key']},\n  title   = {{{bibtex_escape(t)}}},\n"
                   f"  author  = {{{bibtex_escape(authors_bib)}}},\n"
                   f"  journal = {{{bibtex_escape(jt)}}},\n"
                   f"  year    = {{{year}}},\n{doi_line}}}")
        entries.append(bib)

        rows.append([normalized, t, art_type(rec), rec.get("journal_abbrev") or "Preprint",
                     rec.get("date"), rec.get("corresponding_author") or "-", doi or "-",
                     rec.get("pdf_downloaded"), rec.get("pdf_file") or "-"])

    open(os.path.join(bib_dir, f"ELM_{prefix}_library.bib"), "w", encoding="utf-8").write("\n\n".join(entries))
    with open(os.path.join(bib_dir, "naming_manifest.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["规范化命名", "英文原题", "文献类型", "期刊", "发表日期", "通讯作者(推定)", "DOI", "PDF已下载", "PDF文件"])
        w.writerows(rows)

    # rename downloaded PDFs to normalized naming
    pdf_dir = os.path.join(base, "01_PDF")
    for rec in db:
        if rec.get("pdf_downloaded") and rec.get("pdf_file"):
            src = os.path.join(pdf_dir, rec["pdf_file"])
            if os.path.exists(src):
                dst_name = re.sub(r'[<>:"/\\|?*]', "_", rec["normalized_name"]) + ".pdf"
                dst = os.path.join(pdf_dir, dst_name)
                if src != dst and not os.path.exists(dst):
                    shutil.move(src, dst)
                    rec["pdf_file"] = dst_name

    json.dump(db, open(os.path.join(base, "literature_database.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("bib entries:", len(entries), "->", f"ELM_{prefix}_library.bib")
    print("manifest rows:", len(rows))
    print("未命名文献 (fill cn_titles.json):", sum(1 for r in rows if "未命名" in r[0]))


if __name__ == "__main__":
    main()
