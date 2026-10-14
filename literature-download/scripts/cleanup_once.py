# Downloads 清理：md5 与 01_PDF 归档一致的 PDF 移入 _imported_src（移动非删除）
# 小批量：每次调用最多 10 个
import os, hashlib, shutil

# ROOT：环境变量 WORKDIR（工作目录），默认取脚本上一级；DL：环境变量 DL_DIR（下载目录）
ROOT = os.environ.get("WORKDIR") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DL = os.environ.get("DL_DIR") or os.path.expanduser("~/Downloads")
LIMIT = 10

def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

arch = {}
for fn in os.listdir(os.path.join(ROOT, "01_PDF")):
    try:
        arch[md5(os.path.join(ROOT, "01_PDF", fn))] = fn
    except Exception:
        pass

imp = os.path.join(ROOT, "_imported_src")
os.makedirs(imp, exist_ok=True)
moved = 0
for fn in os.listdir(DL):
    if moved >= LIMIT:
        break
    if not fn.lower().endswith(".pdf"):
        continue
    p = os.path.join(DL, fn)
    try:
        if md5(p) in arch:
            shutil.move(p, os.path.join(imp, fn))
            moved += 1
    except Exception as e:
        print("skip:", fn, e)
print("moved:", moved, "| archived hashes:", len(arch))
