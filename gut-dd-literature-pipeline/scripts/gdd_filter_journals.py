# -*- coding: utf-8 -*-
"""Journal whitelist filter (2026-10-09 肠道靶向药物递送方向，严格第一/第二梯队).

KEEP groups（期刊梯队见 references/workflow.md §8；用户 2026-10-09 明确：只收第一、第二
梯队，除此之外一律不检索）:
  T1-第一梯队（综合/综述顶刊）:
      Nature(主刊)、Science(主刊)、Nature Reviews Drug Discovery、Chemical Reviews、
      Chemical Society Reviews、Nature Nanotechnology、Nature Materials、
      Nature Biomedical Engineering、Advanced Materials、Angewandte Chemie(Int Ed 各版)
  T2-第二梯队（领域顶刊）:
      Journal of Controlled Release、Advanced Drug Delivery Reviews、ACS Nano、Nano Today、
      Biomaterials、Matter、Nature Communications、Science Advances、Nano Letters、JACS

严格匹配（exact/prefix + 伪刊拦截），不做 Nature/Science 全家族前缀收录——Nat Chem Biol、
Nat Biotechnol、Sci Transl Med、Adv Funct Mater、Small 等均不在清单内（如需扩展告知后重刷）。

Everything else -> literature_database_all.json archive + per-journal counts in
03_Reports/exclusion_log.md (nothing silently lost; user can widen the list later).

Usage:
  python gdd_filter_journals.py [--dir WORKDIR] [--stage first|final]
"""
import argparse, json, os, re
from collections import Counter


def strip_parens(s):
    return re.sub(r"\([^)]*\)", " ", s or "")


def norm(s):
    s = re.sub(r"[^a-z0-9]+", " ", strip_parens(s).lower()).strip()
    if s.startswith("the "):
        s = s[4:]
    return s


# ---- single-word keys: exact match only (prevents "Matter" matching "Biomaterials Science") ----
EXACT_KEYS = {
    # T1-第一梯队（综合/综述顶刊，2026-10-09 严格清单）
    "nature": "T1-第一梯队", "science": "T1-第一梯队",
    "chem rev": "T1-第一梯队", "chem soc rev": "T1-第一梯队",
    "nat rev drug discov": "T1-第一梯队",
    "nat nanotechnol": "T1-第一梯队", "nature nanotechnology": "T1-第一梯队",
    "nat mater": "T1-第一梯队", "nature materials": "T1-第一梯队",
    "nat biomed eng": "T1-第一梯队", "nature biomedical engineering": "T1-第一梯队",
    "adv mater": "T1-第一梯队", "angew chem": "T1-第一梯队",
    # T2-第二梯队（领域顶刊，2026-10-09 严格清单）
    "j control release": "T2-第二梯队", "adv drug deliv rev": "T2-第二梯队",
    "acs nano": "T2-第二梯队", "nano today": "T2-第二梯队",
    "biomaterials": "T2-第二梯队", "matter": "T2-第二梯队",
    "nat commun": "T2-第二梯队", "nature communications": "T2-第二梯队",
    "sci adv": "T2-第二梯队", "science advances": "T2-第二梯队",
    "nano lett": "T2-第二梯队", "nano letters": "T2-第二梯队",
    "j am chem soc": "T2-第二梯队", "jacs": "T2-第二梯队",
}

# ---- multi-word keys: prefix match, with lookalike blocklist ----
PREFIX_KEYS = {
    # T1
    "nature reviews drug discovery": "T1-第一梯队",
    "nature nanotechnology": "T1-第一梯队",
    "nature materials": "T1-第一梯队",
    "nature biomedical engineering": "T1-第一梯队",
    "chemical reviews": "T1-第一梯队",
    "chemical society reviews": "T1-第一梯队",
    "advanced materials": "T1-第一梯队",
    "angewandte chemie": "T1-第一梯队",
    "angew chem": "T1-第一梯队",
    # T2
    "journal of controlled release": "T2-第二梯队",
    "j control release": "T2-第二梯队",
    "advanced drug delivery reviews": "T2-第二梯队",
    "adv drug deliv rev": "T2-第二梯队",
    "journal of the american chemical society": "T2-第二梯队",
}

BLOCK_REMAINDER = {
    "advanced materials": ("interfaces", "technolog", "letters", "and processes",
                           "research", "for energy", "deutschland", "reports"),
    "chemical reviews": ("in ", "of "),
    "angewandte chemie": ("deutsch",),
    "advanced drug delivery reviews": ("x",),
    "journal of controlled release": ("x",),
    "j control release": ("x",),
}


def hit(s):
    if not s:
        return None
    if s in EXACT_KEYS:
        return EXACT_KEYS[s]
    for k, g in PREFIX_KEYS.items():
        if s == k or s.startswith(k + " "):
            rem = s[len(k):].strip()
            for b in BLOCK_REMAINDER.get(k, ()):
                if rem.startswith(b):
                    return None
            return g
    return None


def classify(rec):
    raw_j = (rec.get("journal") or "").strip().lower()
    raw_ja = (rec.get("journal_abbrev") or "").strip().lower()
    PRE = {"preprint", "arxiv preprint", "arxiv", "biorxiv", "medrxiv",
           "research square", "ssrn electronic journal"}
    if raw_j in PRE or raw_ja in PRE or raw_j.startswith("biorxiv") or raw_j.startswith("arxiv"):
        return ("预印本", False, "预印本/非期刊，不计入期刊统计")
    jt, ja = norm(raw_j), norm(raw_ja)
    # 严格清单：不再做 Nature/Science 全家族前缀收录，只按 T1/T2 精确名单匹配
    g = hit(jt) or hit(ja)
    if g:
        return (g, True, "")
    if not jt and not ja:
        return ("期刊未知", None, "期刊字段缺失，待 DOI 修复后复核")
    return ("非白名单期刊", False, "不在 T1/T2 严格白名单（第一/第二梯队之外，用户 2026-10-09 要求不检索）")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.getcwd())
    ap.add_argument("--stage", default="first", choices=["first", "final"])
    args = ap.parse_args()
    base = args.dir
    db_path = os.path.join(base, "literature_database.json")
    all_path = os.path.join(base, "literature_database_all.json")

    src_path = all_path if os.path.exists(all_path) else db_path
    db = json.load(open(src_path, encoding="utf-8"))

    kept, dropped = [], []
    drop_journals, groups = Counter(), Counter()
    for r in db:
        group, keep, note = classify(r)
        r["journal_group"] = group
        if keep is None and args.stage == "first":
            groups["期刊未知(暂留)"] += 1
            kept.append(r)
            continue
        if keep:
            kept.append(r)
            groups[group] += 1
        else:
            r["drop_reason"] = note
            dropped.append(r)
            key = (r.get("journal") or r.get("journal_abbrev") or "?")
            drop_journals[f'{key} [{group}]'] += 1

    json.dump(db, open(all_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    kept.sort(key=lambda r: r.get("date") or "")
    json.dump(kept, open(db_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    lines = ["# 排除日志 exclusion_log（肠道靶向药物递送批次）", "",
             f"筛选阶段：{args.stage}｜保留 {len(kept)} 篇，排除 {len(dropped)} 篇（候选全库 {len(db)} 篇）", "",
             "## 保留分组", ""]
    for g, n in sorted(groups.items()):
        lines.append(f"- {g}: {n} 篇")
    lines += ["", "## 被排除期刊（按期刊计数）", "", "| 期刊（排除原因分组） | 篇数 |", "|---|---|"]
    for j, n in drop_journals.most_common():
        lines.append(f"| {j} | {n} |")
    lines += ["", "## 收录规则（2026-10-09 肠道靶向药物递送方向，严格第一/第二梯队）", "",
              "1. T1-第一梯队（综合/综述顶刊）：Nature(主刊)、Science(主刊)、",
              "   Nat Rev Drug Discov、Chem Rev、Chem Soc Rev、Nat Nanotechnol、Nat Mater、",
              "   Nat Biomed Eng、Adv Mater、Angew Chem(Int Ed 各版)。",
              "2. T2-第二梯队（领域顶刊）：J Control Release、Adv Drug Deliv Rev、ACS Nano、",
              "   Nano Today、Biomaterials、Matter、Nat Commun、Sci Adv、Nano Lett、JACS。",
              "3. 严格名单匹配：不做 Nature/Science 全家族前缀收录；Nat Chem Biol、Nat Biotechnol、",
              "   Sci Transl Med、Adv Funct Mater、Adv Sci、Small、Acta Biomater 等均不收。",
              "4. 伪刊拦截：Adv Mater 不含 Interfaces/Reports 等衍生刊；Chem Rev 不含 Acc 系；",
              "   J Control Release 不含 J Control Release X；Biomaterials 不含 Biomaterials Science；",
              "   Matter 不含其他同名词刊。",
              "5. 预印本（bioRxiv/medRxiv/arXiv/SSRN 等）不计期刊统计；期刊未知暂留待 DOI 修复复核。",
              "",
              "> 若需追加/剔除某期刊，告知后可重跑本脚本即时刷新清单。"]
    os.makedirs(os.path.join(base, "03_Reports"), exist_ok=True)
    open(os.path.join(base, "03_Reports", "exclusion_log.md"), "w", encoding="utf-8").write("\n".join(lines))

    print("kept:", len(kept), "| dropped:", len(dropped))
    for g, n in sorted(groups.items()):
        print("  ", g, n)
    print("top excluded journals:")
    for j, n in drop_journals.most_common(15):
        print("   ", j, n)


if __name__ == "__main__":
    main()
