#!/usr/bin/env python3
"""
LiuLab Pipeline - Relevance Filter (title + abstract dual review)
Usage: python liulab_relevance_filter.py --dir .
Applies drops from relevance_drops.json to literature_database.json
"""
import argparse, json, os, sys

# LiuLab relevance dimensions (abstract must hit at least one)
KEEP_DIMENSIONS = [
    "engineered bacteria", "probiotic", "live biotherapeutic", "bacterial therapy",
    "lactobacillus", "bifidobacterium", "e. coli nissle",
    "inflammatory bowel disease", "ibd", "colitis", "crohn", "dysbiosis",
    "non-alcoholic fatty liver", "nafld", "hepatic encephalopathy",
    "intestinal infection", "c. difficile", "clostridioides",
    "gut microbiome", "gut microbiota", "intestinal flora", "gut-liver axis", "gut-brain axis",
    "mucosal delivery", "oral delivery", "colon-targeted", "enteric", "mucoadhesive",
    "oral vaccine", "mucosal vaccination", "probiotic delivery",
    "hydrogel", "3d print", "bioprint", "nanoparticle", "biomaterial", "scaffold",
    "living material", "bacterial hydrogel", "living hydrogel", "living coating",
    "spatiotemporal", "stimuli-responsive", "ultrasound", "magnetic", "nir",
    "ph-responsive", "photothermal",
    "microbial metabolite", "scfa", "tryptophan", "bile acid", "indole",
    "intestinal barrier", "mucosal immunity",
    # === REGEN 维度（补漏：血凝块/止血/组织再生/类器官/干细胞）===
    "wound healing", "tissue regeneration", "tissue repair", "regenerative medicine",
    "haemostasis", "hemostasis", "blood clot", "blood-clot",
    "organoid", "stem cell", "cardiac repair", "heart repair",
    "corneal repair", "tissue engineering",
    # === 疫苗/肿瘤免疫维度（补漏：瘤内疫苗/检查点/抗原呈递/溶瘤）===
    "vaccination", "intratumoural", "intratumoral", "in situ vaccination",
    "cancer vaccine", "tumor vaccine", "tumour vaccine",
    "checkpoint degradation", "checkpoint", "antigen presentation",
    "antigen cross-presentation", "cross-presentation",
    "oncolytic", "antitumor immunity", "anti-tumor immunity", "antitumour immunity",
    "immunotherapy", "cancer immunotherapy", "tumor immunotherapy",
    # === OMV/灭活菌/NO/抗毒素维度（补漏：NBE OMV、灭活菌、NatBiotech NO、NatMicrobiol 抗毒素）===
    "outer membrane vesicle", "omv", "inactivated bacteria", "inactivated bacterial",
    "nitric oxide", "antitoxin", "colibactin",
    # === 其他金标准主题 ===
    "mitochondria", "mitochondrial",
    "protoplast",
    "catalase", "dry eye",
    "proteolysis-targeting", "targeting chimera", "protein degradation",
    "nanoparticle", "drug delivery",
    "immunological synapse", "immune synapse",
    "phenylketonuria", "pku", "synthetic biotic",
    "microalgae", "fungal", "fungus", "textile",
    "mycelium", "mycelial", "atmospheric water", "water capture",
    "water hyacinth", "photosynthetic",
    "mucosal vaccination", "respiratory",
    "biofilm",
    "atp", "endosymbiotic", "endosymbiosis",
    "bacteria-cancer", "bacterial- cancer", "bacteria and cancer",
    "skull", "brain delivery", "stroke",
    "lactococcus",
    "sprayable", "spray",
    "co2", "electrosynthesis", "lycopene",
    "microbial consortium", "microbial consortia", "wastewater",
]

DROP_DIMENSIONS = [
    "chromatin", "polymerase", "crystal structure", "structural biology",
    "cell-free", "cell free",
    "natural product",
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=".", help="Working directory")
    args = parser.parse_args()

    db_path = os.path.join(args.dir, "literature_database.json")
    drops_path = os.path.join(args.dir, "relevance_drops.json")

    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found", file=sys.stderr)
        sys.exit(1)

    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    records = data if isinstance(data, list) else data.get("records", data.get("papers", []))

    # Load drops
    drops = {"drop": {}, "flag": {}}
    if os.path.exists(drops_path):
        with open(drops_path, "r", encoding="utf-8") as f:
            drops = json.load(f)
        drops.setdefault("drop", {})
        drops.setdefault("flag", {})

    kept, dropped = [], []
    for rec in records:
        doi = rec.get("doi", "")
        title = rec.get("title", "").lower()
        abstract = rec.get("abstract", "").lower()
        text = f"{title} {abstract}"

        # Check explicit drops
        if doi in drops.get("drop", {}):
            dropped.append((rec, drops["drop"][doi]))
            continue

        # Check keep dimensions (abstract OR title must hit at least one)
        has_keep = any(dim in text for dim in KEEP_DIMENSIONS)

        # Check drop dimensions
        has_drop = any(dim in text for dim in DROP_DIMENSIONS)

        if has_keep and not has_drop:
            kept.append(rec)
        elif has_drop:
            reason = f"matched drop dimension"
            dropped.append((rec, reason))
            drops["drop"][doi] = reason
        elif not has_keep:
            reason = "no relevance dimension matched"
            dropped.append((rec, reason))
            drops["drop"][doi] = reason

    # Save updated drops
    with open(drops_path, "w", encoding="utf-8") as f:
        json.dump(drops, f, ensure_ascii=False, indent=2)

    # Save filtered DB
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(kept, f, ensure_ascii=False, indent=2)

    print(f"Kept: {len(kept)} | Dropped: {len(dropped)}")
    print(f"Drops saved to: {drops_path}")
    for rec, reason in dropped[:10]:
        print(f"  DROP: {rec.get('title', '')[:50]} ({reason})")

if __name__ == "__main__":
    main()
