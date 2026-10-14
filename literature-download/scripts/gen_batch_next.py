# 生成下一批：Elsevier 优先（OA 刊在前）-> 其他出版商；排除 deferred + hold
# 输出: current_batch.json + 打印 "PHASE=ev|non_ev|none"
import json, os

# BASE：环境变量 WORKDIR（工作目录），默认取脚本上一级（scripts/ 的父目录）
BASE = os.environ.get("WORKDIR") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(BASE, "tools")


def load_list(fn):
    try:
        d = json.load(open(os.path.join(TOOLS, fn), encoding="utf-8"))
        return [x.lower() for x in (d if isinstance(d, list) else d.get("dois", []))]
    except Exception:
        return []


db = json.load(open(os.path.join(BASE, "literature_database.json"), encoding="utf-8"))
excl = set(load_list("deferred_dois.json")) | set(load_list("hold_dois.json"))

pend = [r for r in db if not r.get("pdf_downloaded") and r.get("doi")
        and r["doi"].lower() not in excl]

OA_PREFIX = ("10.1016/j.mtbio", "10.1016/j.bioactmat")
ev_oa = [r for r in pend if r["doi"].lower().startswith(OA_PREFIX)]
ev_sub = [r for r in pend if r["doi"].lower().startswith("10.1016")
          and r not in ev_oa]
other = [r for r in pend if not r["doi"].lower().startswith("10.1016")]

if ev_oa:
    batch = [r["doi"] for r in ev_oa[:8]]
    phase = "ev"
elif ev_sub:
    batch = [r["doi"] for r in ev_sub[:8]]
    phase = "ev"
elif other:
    batch = [r["doi"] for r in other[:8]]
    phase = "non_ev"
else:
    batch, phase = [], "none"

# Elsevier 不足 8 篇时用其他出版商补位，避免驱动为单篇反复冷却空转
if batch and phase == "ev" and len(batch) < 8 and other:
    batch += [r["doi"] for r in other[:8 - len(batch)]]

json.dump(batch, open(os.path.join(TOOLS, "current_batch.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("PHASE=" + phase)
print("batch size:", len(batch))
for d in batch:
    print(" ", d)
print("remaining | ev_oa:", len(ev_oa), "ev_sub:", len(ev_sub), "other:", len(other))
