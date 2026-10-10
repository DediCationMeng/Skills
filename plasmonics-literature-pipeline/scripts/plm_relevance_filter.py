# -*- coding: utf-8 -*-
"""Relevance filter (journal tier x relevance, per workflow.md §7.2).

Broad keyword queries (PLASMON-CORE/EXOTIC-SHAPES) drag in top-journal papers that are
off-topic (e.g. plasmonic sensing with no nanomaterial dimension). This script drops
explicitly listed DOIs from the kept set and records reasons into 03_Reports/exclusion_log.md.

Drop/flag lists live in <WORKDIR>/relevance_drops.json:
  {"drop": {"<doi>": "<reason>", ...}, "flag": {"<doi>": "<note>"}}
Edit that file after reviewing each batch's new whitelist hits.

Usage:
  python plm_relevance_filter.py --dir WORKDIR
"""
import argparse, json, os

DROP, FLAG_NOTE = {}, {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.getcwd())
    args = ap.parse_args()

    drops_path = os.path.join(args.dir, "relevance_drops.json")
    if os.path.exists(drops_path):
        cfg = json.load(open(drops_path, encoding="utf-8"))
        DROP.update(cfg.get("drop") or {})
        FLAG_NOTE.update(cfg.get("flag") or {})
        print("loaded relevance_drops.json:", len(DROP), "drops /", len(FLAG_NOTE), "flags")
    else:
        print("WARNING: relevance_drops.json not found - nothing to drop")

    kept_path = os.path.join(args.dir, "literature_database.json")
    all_path = os.path.join(args.dir, "literature_database_all.json")
    kept = json.load(open(kept_path, encoding="utf-8"))
    all_db = json.load(open(all_path, encoding="utf-8"))

    kept2, dropped_rows = [], []
    for r in kept:
        d = (r.get("doi") or "").lower()
        if d in DROP:
            r["drop_reason"] = "弱相关/离题：" + DROP[d]
            dropped_rows.append(r)
        else:
            if d in FLAG_NOTE:
                r["relevance_note"] = FLAG_NOTE[d]
            kept2.append(r)
    json.dump(kept2, open(kept_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    idx = {(r.get("doi") or "").lower(): r for r in all_db}
    for r in dropped_rows:
        d = (r.get("doi") or "").lower()
        if d in idx:
            idx[d]["drop_reason"] = r["drop_reason"]
    for d, note in FLAG_NOTE.items():
        if d in idx:
            idx[d]["relevance_note"] = note
    json.dump(all_db, open(all_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    log_path = os.path.join(args.dir, "03_Reports", "exclusion_log.md")
    lines = ["", "## 相关度剔除（期刊达标但离题，关键词补检产生）", ""]
    for r in dropped_rows:
        lines.append(f"- **{r['title'][:90]}**（{(r.get('journal_abbrev') or '')}，{r.get('date')}）")
        lines.append(f"  - 剔除理由：{r['drop_reason'].split('：', 1)[-1]}｜DOI：{r.get('doi')}")
    for d, note in FLAG_NOTE.items():
        r = idx.get(d)
        if r:
            lines.append(f"- （保留并标注）**{r['title'][:90]}**（{(r.get('journal_abbrev') or '')}，{r.get('date')}）")
            lines.append(f"  - 备注：{note}｜DOI：{d}")
    if os.path.exists(log_path):
        open(log_path, "a", encoding="utf-8").write("\n".join(lines) + "\n")
    print("kept after relevance filter:", len(kept2), "| dropped:", len(dropped_rows))


if __name__ == "__main__":
    main()
