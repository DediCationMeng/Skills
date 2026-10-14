# 解析 batch_download 输出 -> 更新 attempts/hold 状态 -> 输出判定
# 用法: python night_state.py <batch_output_file> <phase: ev|non_ev>
# 逻辑:
#   OK            -> 重置该 DOI 计数
#   SKIP 付费墙类  -> strikes+1，PAYWALL/ABS_ONLY 达 2 次、NOMATCH 达 3 次 => 搁置(hold)
#   SKIP 阻塞类   -> 不计数（CAPTCHA/限流/交互），整批阻塞时判 BLOCKED 让驱动冷却
#   非 Elsevier 批次整批 0 OK 且全付费墙类 -> 出版商前缀组计数，达 3 轮整组搁置
#   FAILED/dl_err -> 瞬态，自动留待下批重试
import json, os, re, sys

# BASE：环境变量 WORKDIR（工作目录），默认取脚本上一级（scripts/ 的父目录）
BASE = os.environ.get("WORKDIR") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(BASE, "tools")

out_file = sys.argv[1]
phase = sys.argv[2] if len(sys.argv) > 2 else "ev"

attempts_f = os.path.join(TOOLS, "night_attempts.json")
hold_f = os.path.join(TOOLS, "hold_dois.json")
groups_f = os.path.join(TOOLS, "night_groups.json")


def loadj(fn, default):
    try:
        return json.load(open(fn, encoding="utf-8"))
    except Exception:
        return default


attempts = loadj(attempts_f, {})
hold = set(x.lower() for x in loadj(hold_f, []))
groups = loadj(groups_f, {})
batch = loadj(os.path.join(TOOLS, "current_batch.json"), [])

ok, blocked, park_hit = [], [], {}
txt = open(out_file, encoding="utf-8", errors="replace").read()
for line in txt.splitlines():
    m = re.match(r"OK (\S+) ", line)
    if m:
        ok.append(m.group(1))
        continue
    m = re.match(r"SKIP (\S+) (\S+) (.*)", line)
    if m:
        doi, mode, sig = m.group(1), m.group(2), m.group(3).upper()
        if "PAYWALL" in sig or "ABS_ONLY" in sig:
            park_hit[doi] = 2      # 阈值 2
        elif mode == "NOMATCH":
            park_hit[doi] = 3      # 阈值 3
        else:
            blocked.append(doi)    # CAPTCHA/限流/未知交互 -> 冷却重试
        continue
    m = re.match(r"FAILED (\S+) (.*)", line)
    if m:
        doi, why = m.group(1), m.group(2)
        # 无权限/格式拦截类失败：epdf 弹回、fetch 拿到 HTML、文件过小
        if "ABS_BOUNCE" in why or "ERR:ct" in why or "ERR:small" in why:
            park_hit[doi] = 3      # 阈值 3
        # 其余 FAILED（超时/断连等）视为瞬态，自动留待下批重试
        continue

for doi in ok:
    attempts.pop(doi, None)

new_hold = []
for doi, thr in park_hit.items():
    n = attempts.get(doi, 0) + 1
    attempts[doi] = n
    if n >= thr and doi.lower() not in hold:
        hold.add(doi.lower())
        new_hold.append(doi)

# 出版商前缀组快速搁置（仅非 Elsevier 批次，整批 0 OK 且全为付费墙/失败/拦截类）
if phase == "non_ev" and batch and not ok and len(park_hit) + len(blocked) == len(batch):
    for pref in {doi.split("/")[0].lower() for doi in batch}:  # 每轮每前缀只计 1 次
        groups[pref] = groups.get(pref, 0) + 1
    for pref, n in list(groups.items()):
        if n >= 3:
            db = loadj(os.path.join(BASE, "literature_database.json"), [])
            for r in db:
                d = (r.get("doi") or "").lower()
                if d.startswith(pref + "/") and not r.get("pdf_downloaded") and d not in hold:
                    hold.add(d)
                    new_hold.append(r["doi"])
            groups[pref] = 0
else:
    for doi in batch:
        pref = doi.split("/")[0].lower()
        if pref in groups and (ok or phase == "ev"):
            groups[pref] = 0

json.dump(attempts, open(attempts_f, "w", encoding="utf-8"), ensure_ascii=False)
json.dump(sorted(hold), open(hold_f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(groups, open(groups_f, "w", encoding="utf-8"), ensure_ascii=False)

verdict = "OK"
if not ok and blocked and not park_hit:
    verdict = "BLOCKED"
elif not ok and park_hit:
    verdict = "PARKED_ONLY"
print("STATE ok=%d blocked=%d park=%d new_hold=%d verdict=%s"
      % (len(ok), len(blocked), len(park_hit), len(new_hold), verdict))
if new_hold:
    print("HELD:", ", ".join(new_hold[:12]), ("..." if len(new_hold) > 12 else ""))
