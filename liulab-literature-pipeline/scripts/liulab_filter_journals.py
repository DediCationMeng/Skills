#!/usr/bin/env python3
"""
LiuLab Pipeline - Journal Whitelist Filter v2 (EXACT matching)
Usage: python liulab_filter_journals.py --dir . --stage first|final
"""
import argparse, json, os, sys

# Journal whitelist A-F groups - EXACT name matching only
WHITELIST = {
    "A_nature": [
        "nature", "nature communications", "nature biotechnology", "nature medicine",
        "nature materials", "nature biomedical engineering", "nature microbiology",
        "nature chemistry", "nature metabolism", "nature methods", "nature immunology",
        "nature aging", "nature cancer", "nature reviews gastroenterology & hepatology",
        "nature reviews gastroenterology and hepatology",
        "nature reviews microbiology", "nature cell biology",
        "nature water", "nature food", "nature sustainability",
    ],
    "B_science": [
        "science", "science advances", "science robotics",
        "science translational medicine", "science immunology",
        "science bulletin",
    ],
    "C_cell": [
        "cell", "cell metabolism", "cell host & microbe", "cell host and microbe",
        "cell stem cell", "cancer cell", "immunity", "neuron", "molecular cell",
        "chem", "matter", "cell reports", "cell reports medicine",
        "cell chemical biology", "cell discovery", "cell systems",
        "cell biomaterials",
    ],
    "D_user_pinned": [
        "advanced materials", "advanced functional materials", "advanced science",
        "journal of the american chemical society", "jacs",
        "angewandte chemie",
    ],
    "E_high_if": [
        "gut", "gastroenterology", "hepatology",
        "microbiome",
        "signal transduction and targeted therapy",
        "acs nano",
        "gut microbes",
        "pnas",
        "proceedings of the national academy of sciences of the united states of america",
    ],
    "F_user_add": [
        "advanced healthcare materials",
        "med",
    ],
}

# Strict exclusions - these never match even if substring matches a whitelist name
EXCLUDED_EXACT = [
    "nature protocols", "nature methods",  # keep methods actually
]

EXCLUDED_PATTERNS = [
    "npj", "frontiers", "iscience", "current biology",
    "science signaling",
    "scientific reports", "methods in molecular biology",
    "int j mol sci", "international journal of molecular sciences",
    "nutrients", "polymers", "foods",
]

def _norm(s):
    """Normalize journal name: lowercase, dots->space, collapse whitespace."""
    import re
    s = (s or "").lower().strip()
    s = re.sub(r"[.\u00b7]+", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def _name_matches(jn, name):
    """Boundary-aware prefix match on normalized strings.
    'nature' matches 'nature', 'nature (2024)', but NOT 'nature water'.
    """
    n = _norm(name)
    if jn == n:
        return True
    if jn.startswith(n):
        rest = jn[len(n):].lstrip()
        if not rest or not rest[0].isalpha():
            return True
    return False

def matches_whitelist(journal):
    """Returns (matched, group) or (False, None).
    Whitelist match takes priority over EXCLUDED_PATTERNS
    (so 'cell reports medicine' beats the 'cell reports' family exclusion).
    """
    jn = _norm(journal)

    # 1) Whitelist (boundary-aware; kills the 'nature water' prefix loophole)
    for group, names in WHITELIST.items():
        for name in names:
            if _name_matches(jn, name):
                return True, group
            if name == "jacs" and ("journal of the american chemical society" in jn or jn == "jacs"):
                return True, group

    # 2) Exclusions (only apply to non-whitelisted journals)
    for excl in EXCLUDED_PATTERNS:
        if _norm(excl) in jn:
            return False, None

    return False, None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=".")
    parser.add_argument("--stage", choices=["first", "final"], default="first")
    args = parser.parse_args()

    db_path = os.path.join(args.dir, "literature_database.json")
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found", file=sys.stderr)
        sys.exit(1)

    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    records = data if isinstance(data, list) else data.get("records", data.get("papers", []))

    kept, excluded_log = [], []
    for rec in records:
        journal = rec.get("journal", "")
        ok, group = matches_whitelist(journal)
        if ok:
            rec["journal_group"] = group
            kept.append(rec)
        else:
            excluded_log.append(f"- [{journal}] {rec.get('title', '')[:60]}")

    log_path = os.path.join(args.dir, "03_Reports", "exclusion_log.md")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"\n## Stage: {args.stage} v2-exact | Excluded: {len(excluded_log)} | Kept: {len(kept)}\n")
        f.write("\n".join(excluded_log) + "\n")

    out_path = os.path.join(args.dir, "literature_database.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(kept, f, ensure_ascii=False, indent=2)

    print(f"Kept: {len(kept)} | Excluded: {len(excluded_log)}")

    # Group summary
    from collections import Counter
    groups = Counter(r.get("journal_group", "?") for r in kept)
    for g in ["A_nature", "B_science", "C_cell", "D_user_pinned", "E_high_if", "F_user_add"]:
        print(f"  {g}: {groups.get(g, 0)}")

if __name__ == "__main__":
    main()
