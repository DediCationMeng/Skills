# -*- coding: utf-8 -*-
"""Journal whitelist filter (2026-10-09 等离激元方向微调，按期刊梯队 A-H 收录).

KEEP groups (期刊梯队见 references/workflow.md §8):
  A-Nature家族   : journal title starts with "nature" (Nature, Nature Communications,
                   Nature Photonics, Nature Nanotechnology, Nature Materials ...).
                   npj series NOT included.
  B-Science家族  : Science / Science Advances / Science Robotics /
                   Sci Transl Med / Sci Immunol (Science Signaling excluded)
  C-Cell家族     : Cell, Cell Stem Cell, Cell Metab, Cell Host Microbe, Cancer Cell,
                   Immunity, Neuron, Mol Cell, Chem, Joule, Matter, Cell Rep Med
                   (Cell Reports / iScience / Cell Systems / Current Biology excluded)
  D-用户点名     : Adv Mater / Adv Funct Mater / Adv Sci / JACS / Angew Chem(Int Ed) / Biomaterials
  E-学科顶刊     : 第二梯队 — ACS Nano, Nano Lett, Nano Today, Light Sci Appl, Phys Rev Lett,
                   Chem Rev, Chem Soc Rev, Acc Chem Res, Bioact Mater, Adv Drug Deliv Rev,
                   Trends Microbiol, Prog Mater Sci, Signal Transduct Target Ther 等
  F-用户补充     : ACS Synthetic Biology, Materials Today Bio, Advanced Healthcare Materials
  G-次顶刊       : 第三梯队 — Small, Chem Mater, Nanoscale, J Phys Chem Lett, ACS Photonics,
                   Adv Opt Mater, ACS Appl Mater Interfaces, Nano Energy, Appl Catal B,
                   Biosens Bioelectron, Theranostics
  H-专业刊       : 第四梯队（等离激元专业刊）— J Phys Chem C, Plasmonics, Nanophotonics,
                   Opt Express, ACS Appl Nano Mater, J Nanopart Res, Opt Mater Express
                   （收录偏宽，若要收紧"优中选优"可移除此组）

Everything else -> literature_database_all.json archive + per-journal counts in
03_Reports/exclusion_log.md (nothing silently lost; user can widen the list later).

Usage:
  python plm_filter_journals.py [--dir WORKDIR] [--stage first|final]
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


# ---- single-word keys: exact match only (prevents "Cell" matching "Cell Cycle") ----
EXACT_KEYS = {
    # B
    "science": "B-Science家族", "sci adv": "B-Science家族",
    "sci robot": "B-Science家族", "sci transl med": "B-Science家族",
    "sci immunol": "B-Science家族",
    # C
    "cell": "C-Cell家族", "cancer cell": "C-Cell家族", "immunity": "C-Cell家族",
    "neuron": "C-Cell家族", "mol cell": "C-Cell家族", "chem": "C-Cell家族",
    "joule": "C-Cell家族", "matter": "C-Cell家族",
    # D
    "adv mater": "D-用户点名", "adv funct mater": "D-用户点名", "adv sci": "D-用户点名",
    "adv sci weinh": "D-用户点名", "j am chem soc": "D-用户点名",
    "biomaterials": "D-用户点名",
    # E-学科顶刊（第二梯队，2026-10-09 等离激元微调：新增 nano lett / nano today /
    # light sci appl / phys rev lett）
    "acs nano": "E-学科顶刊", "nano lett": "E-学科顶刊", "nano letters": "E-学科顶刊",
    "nano today": "E-学科顶刊", "light sci appl": "E-学科顶刊",
    "phys rev lett": "E-学科顶刊", "bioact mater": "E-学科顶刊",
    "chem rev": "E-学科顶刊",
    "chem soc rev": "E-学科顶刊", "acc chem res": "E-学科顶刊",
    "adv drug deliv rev": "E-学科顶刊", "trends microbiol": "E-学科顶刊",
    "prog mater sci": "E-学科顶刊", "signal transduct target ther": "E-学科顶刊",
    "gut": "E-学科顶刊", "gastroenterology": "E-学科顶刊",
    "j hepatol": "E-学科顶刊", "lancet gastroenterol hepatol": "E-学科顶刊",
    "circ res": "E-学科顶刊", "trends cancer": "E-学科顶刊",
    # F) user-specified additions (2026-10-09): not low-tier by user's call
    "acs synthetic biology": "F-用户补充", "acs synth biol": "F-用户补充",
    "materials today bio": "F-用户补充", "mater today bio": "F-用户补充",
    "advanced healthcare materials": "F-用户补充", "adv healthc mater": "F-用户补充",
    # G-次顶刊（第三梯队，2026-10-09 等离激元微调新增）
    "small": "G-次顶刊", "nanoscale": "G-次顶刊", "nano energy": "G-次顶刊",
    "theranostics": "G-次顶刊", "biosens bioelectron": "G-次顶刊",
    "appl catal b": "G-次顶刊", "j phys chem lett": "G-次顶刊",
    "acs photonics": "G-次顶刊", "adv opt mater": "G-次顶刊",
    "acs appl mater interfaces": "G-次顶刊",
    # H-专业刊（第四梯队等离激元专业刊，2026-10-09 等离激元微调新增）
    "plasmonics": "H-专业刊", "nanophotonics": "H-专业刊",
    "opt express": "H-专业刊", "j phys chem c": "H-专业刊",
    "j nanopart res": "H-专业刊", "opt mater express": "H-专业刊",
    "acs appl nano mater": "H-专业刊",
}

# ---- multi-word keys: prefix match, with lookalike blocklist ----
PREFIX_KEYS = {
    "science advances": "B-Science家族", "science robotics": "B-Science家族",
    "science translational medicine": "B-Science家族", "science immunology": "B-Science家族",
    "science new york": "B-Science家族", "science american": "B-Science家族",
    "cell stem cell": "C-Cell家族", "cell metabolism": "C-Cell家族",
    "cell host microbe": "C-Cell家族", "cell host and microbe": "C-Cell家族",
    "cell reports medicine": "C-Cell家族", "molecular cell": "C-Cell家族",
    "advanced materials": "D-用户点名", "advanced functional materials": "D-用户点名",
    "advanced science": "D-用户点名", "journal of the american chemical society": "D-用户点名",
    "angewandte chemie": "D-用户点名", "angew chem int ed": "D-用户点名",
    "bioactive materials": "E-学科顶刊", "chemical reviews": "E-学科顶刊",
    "chemical society reviews": "E-学科顶刊", "accounts of chemical research": "E-学科顶刊",
    "advanced drug delivery reviews": "E-学科顶刊", "trends in microbiology": "E-学科顶刊",
    "progress in materials science": "E-学科顶刊",
    "signal transduction and targeted therapy": "E-学科顶刊",
    "journal of hepatology": "E-学科顶刊",
    "lancet gastroenterology hepatology": "E-学科顶刊",
    "circulation research": "E-学科顶刊", "trends in cancer": "E-学科顶刊",
    # G-次顶刊（第三梯队，2026-10-09 等离激元微调新增）
    "chemistry of materials": "G-次顶刊",
    "journal of physical chemistry letters": "G-次顶刊",
    "advanced optical materials": "G-次顶刊",
    "acs applied materials": "G-次顶刊",
    "biosensors and bioelectronics": "G-次顶刊",
    "applied catalysis b": "G-次顶刊",
    # H-专业刊（第四梯队，2026-10-09 等离激元微调新增）
    "journal of physical chemistry c": "H-专业刊",
    "journal of nanoparticle research": "H-专业刊",
    "optics express": "H-专业刊",
    "optical materials express": "H-专业刊",
    "acs applied nano materials": "H-专业刊",
}

BLOCK_REMAINDER = {
    "advanced materials": ("interfaces", "technolog", "letters", "and processes",
                           "research", "for energy", "deutschland", "reports"),
    "advanced science": ("engineering", "and ", "for "),
    "cancer cell": ("international", "reports"),
    "chemical reviews": ("in ", "of "),
}

NATURE_BLOCK = ("nature and science", "nature science", "nature precedings", "nature humanities")


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
    if jt.startswith("nature") and not any(b in jt for b in NATURE_BLOCK):
        return ("A-Nature家族", True, "")
    g = hit(jt) or hit(ja)
    if g:
        return (g, True, "")
    if not jt and not ja:
        return ("期刊未知", None, "期刊字段缺失，待 DOI 修复后复核")
    return ("低分期刊", False, "不在 A-H 收录清单（低于期刊梯队收录线 / 非目标期刊）")


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

    lines = ["# 排除日志 exclusion_log（2020 批次）", "",
             f"筛选阶段：{args.stage}｜保留 {len(kept)} 篇，排除 {len(dropped)} 篇（候选全库 {len(db)} 篇）", "",
             "## 保留分组", ""]
    for g, n in sorted(groups.items()):
        lines.append(f"- {g}: {n} 篇")
    lines += ["", "## 被排除期刊（按期刊计数）", "", "| 期刊（排除原因分组） | 篇数 |", "|---|---|"]
    for j, n in drop_journals.most_common():
        lines.append(f"| {j} | {n} |")
    lines += ["", "## 收录规则（2026-10-09 等离激元方向微调，按期刊梯队 A-H）", "",
              "1. A-Nature 全家族（含 Nat Commun / Nat Photonics / Nat Nanotechnol / Nat Mater /",
              "   Nat Rev X / Nat Chem Biol 等）；npj 系列不收。",
              "2. B-Science / Sci Adv / Sci Robot / Sci Transl Med / Sci Immunol（Science Signaling 不收）。",
              "3. C-Cell Press 高分刊：Cell、Cell Stem Cell、Cell Metab、Cell Host Microbe、Cancer Cell、",
              "   Immunity、Neuron、Mol Cell、Chem、Joule、Matter、Cell Rep Med（Cell Reports/iScience 等不收）。",
              "4. D-用户点名：Adv Mater、Adv Funct Mater、Adv Sci、JACS、Angew Chem(Int Ed)、Biomaterials。",
              "5. E-学科顶刊（第二梯队）：ACS Nano、Nano Lett、Nano Today、Light Sci Appl、Phys Rev Lett、",
              "   Chem Rev、Chem Soc Rev、Acc Chem Res、Bioact Mater、Adv Drug Deliv Rev、Trends Microbiol、",
              "   Prog Mater Sci、Signal Transduct Target Ther 等。",
              "6. F-用户补充（2026-10-09）：ACS Synthetic Biology、Materials Today Bio、",
              "   Advanced Healthcare Materials。",
              "7. G-次顶刊（第三梯队）：Small、Chem Mater、Nanoscale、J Phys Chem Lett、ACS Photonics、",
              "   Adv Opt Mater、ACS Appl Mater Interfaces、Nano Energy、Appl Catal B、Biosens Bioelectron、",
              "   Theranostics。",
              "8. H-专业刊（第四梯队等离激元专业刊）：J Phys Chem C、Plasmonics、Nanophotonics、",
              "   Opt Express、ACS Appl Nano Mater、J Nanopart Res、Opt Mater Express。",
              "   （H 组收录偏宽；若要收紧\"优中选优\"可移除该组后重刷。）",
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
