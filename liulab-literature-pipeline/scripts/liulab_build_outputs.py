#!/usr/bin/env python3
"""
LiuLab Pipeline - Build Outputs (BibTeX + Naming Manifest + Checklist)
Usage: python liulab_build_outputs.py --dir . [--year YYYY]
"""
import argparse, csv, json, os, sys
from datetime import datetime

JOURNAL_ABBREV = {
    "Nature": "Nature", "Nature Communications": "Nat Commun",
    "Nature Biotechnology": "Nat Biotechnol", "Nature Medicine": "Nat Med",
    "Nature Materials": "Nat Mater", "Nature Biomedical Engineering": "Nat Biomed Eng",
    "Nature Microbiology": "Nat Microbiol", "Nature Chemistry": "Nat Chem",
    "Nature Metabolism": "Nat Metab", "Nature Methods": "Nat Methods",
    "Science": "Science", "Science Advances": "Sci Adv",
    "Science Translational Medicine": "Sci Transl Med",
    "Cell": "Cell", "Cell Metabolism": "Cell Metab",
    "Cell Host & Microbe": "Cell Host Microbe", "Immunity": "Immunity",
    "Advanced Materials": "Adv Mater", "Advanced Functional Materials": "Adv Funct Mater",
    "Journal of the American Chemical Society": "JACS",
    "Angewandte Chemie International Edition": "Angew Chem Int Ed",
    "Biomaterials": "Biomaterials", "Gut": "Gut", "Gastroenterology": "Gastroenterology",
    "Hepatology": "Hepatology", "Microbiome": "Microbiome",
    "PNAS": "Proc Natl Acad Sci", "JACS": "JACS",
}

def get_abbrev(journal):
    for full, abbr in JOURNAL_ABBREV.items():
        if full.lower() in journal.lower() or journal.lower() in full.lower():
            return abbr
    return journal[:20]

def make_bibtex_key(rec):
    authors = rec.get("authors", [])
    surname = authors[0].split()[-1] if authors else "Unknown"
    year = rec.get("date", "0000")[:4]
    title_word = rec.get("title", "").split()[0] if rec.get("title") else "untitled"
    return f"{surname}{year}{title_word[:4]}"

def normalized_name(rec):
    date = rec.get("date", "")
    if len(date) >= 7:
        ym = date[:7]  # YYYY-MM
    else:
        ym = "unknown"
    abbrev = get_abbrev(rec.get("journal", ""))
    cn = rec.get("cn_title", rec.get("title", ""))[:30]
    return f"{ym}-{abbrev}-{cn}"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=".")
    parser.add_argument("--year", type=str, help="Filter by year for retrospective mode")
    args = parser.parse_args()

    db_path = os.path.join(args.dir, "literature_database.json")
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found", file=sys.stderr)
        sys.exit(1)

    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    records = data if isinstance(data, list) else data.get("records", data.get("papers", []))

    if args.year:
        records = [r for r in records if r.get("date", "").startswith(args.year)]

    # Directories
    bib_dir = os.path.join(args.dir, "02_BibTeX")
    report_dir = os.path.join(args.dir, "03_Reports")
    os.makedirs(bib_dir, exist_ok=True)
    os.makedirs(report_dir, exist_ok=True)

    # 1. BibTeX
    prefix = args.year if args.year else datetime.now().strftime("%Y-%m")
    bib_path = os.path.join(bib_dir, f"LiuLab_{prefix}_library.bib")
    with open(bib_path, "w", encoding="utf-8") as f:
        for rec in records:
            key = rec.get("key", "") or make_bibtex_key(rec)
            authors = " and ".join(rec.get("authors", [])[:5])
            journal = rec.get("journal", "")
            year = rec.get("date", "")[:4]
            doi = rec.get("doi", "")
            url = f"https://doi.org/{doi}" if doi else rec.get("url", "")
            f.write(f"@article{{{key},\n")
            f.write(f"  author = {{{authors}}},\n")
            f.write(f"  title = {{{rec.get('title', '')}}},\n")
            f.write(f"  journal = {{{journal}}},\n")
            f.write(f"  year = {{{year}}},\n")
            if doi:
                f.write(f"  doi = {{{doi}}},\n")
            if url:
                f.write(f"  url = {{{url}}},\n")
            f.write(f"}}\n\n")
    print(f"BibTeX: {bib_path} ({len(records)} entries)")

    # 2. Naming Manifest CSV
    manifest_path = os.path.join(bib_dir, f"naming_manifest_{prefix}.csv")
    with open(manifest_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["序号", "规范化命名", "英文原标题", "中文译名", "期刊", "日期",
                         "文献类型", "通讯作者", "DOI", "PMID"])
        for i, rec in enumerate(records, 1):
            pubtypes = rec.get("pubtypes", [])
            doc_type = "综述·观点" if "Review" in pubtypes else "研究论文"
            normalized = normalized_name(rec)
            rec["normalized_name"] = normalized
            writer.writerow([
                i, normalized, rec.get("title", ""),
                rec.get("cn_title", "待译"), rec.get("journal", ""),
                rec.get("date", ""), doc_type,
                rec.get("corresponding_author", ""), rec.get("doi", ""),
                rec.get("pmid", ""),
            ])
    print(f"Manifest: {manifest_path}")

    # 3. Three-state Checklist
    checklist_path = os.path.join(report_dir, "手动下载Checklist.md")
    research = [r for r in records if "Review" not in r.get("pubtypes", [])]
    reviews = [r for r in records if "Review" in r.get("pubtypes", [])]

    with open(checklist_path, "w", encoding="utf-8") as f:
        f.write(f"# 手动下载 Checklist（{prefix}）\n\n")
        f.write(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write("## 研究论文（含预印本）\n\n")
        for rec in sorted(research, key=lambda x: x.get("date", ""), reverse=True):
            status = "x" if rec.get("pdf_downloaded") else " "
            doi = rec.get("doi", "")
            doi_link = f"https://doi.org/{doi}" if doi else "待补"
            f.write(f"- [{status}] {rec.get('normalized_name', '')} | {rec.get('journal', '')} | "
                    f"{rec.get('date', '')} | {rec.get('corresponding_author', '')} | "
                    f"[{doi_link}]({doi_link})\n")
        f.write(f"\n## 综述/观点\n\n")
        for rec in sorted(reviews, key=lambda x: x.get("date", ""), reverse=True):
            status = "x" if rec.get("pdf_downloaded") else " "
            doi = rec.get("doi", "")
            doi_link = f"https://doi.org/{doi}" if doi else "待补"
            f.write(f"- [{status}] {rec.get('normalized_name', '')} | {rec.get('journal', '')} | "
                    f"{rec.get('date', '')} | {rec.get('corresponding_author', '')} | "
                    f"[{doi_link}]({doi_link})\n")
    print(f"Checklist: {checklist_path}")

    # 4. Save updated DB with normalized names
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"\nTotal: {len(records)} records | Research: {len(research)} | Reviews: {len(reviews)}")

if __name__ == "__main__":
    main()
