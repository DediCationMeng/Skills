# 并行批下载配方（2026-10-10 校准版）：错峰开页 -> 人机交互优先诊断 -> 严格PII匹配发现PDF
# -> 异步 fetch(window.__dl) -> 轮询 + 落盘确认后关页（绝不关未完成页/最后一个页）
# 用法: browser-use < batch_download.py   （DOIS 改为本批清单）
import time, json, os, re

import json as _json
# 批次清单：优先环境变量 BATCH_FILE，否则取当前目录 current_batch.json（驱动在 tools/ 下运行）
_BATCH_FILE = os.environ.get("BATCH_FILE") or os.path.join(os.getcwd(), "current_batch.json")
try:
    DOIS = _json.load(open(_BATCH_FILE, encoding="utf-8"))
except Exception:
    DOIS = []
DL_DIR = os.environ.get("DL_DIR") or os.path.expanduser("~/Downloads")
STAGGER = 5.0  # 批9 出现 CPE00002 限流后放宽

COOKIE_JS = """(() => {
  const sels = ['#onetrust-accept-btn-handler','#truste-consent-button',
    '.trustarc-agree-btn','button.osano-c-dialog__button--accept',
    'button#hs-eu-confirmation-button','[id*="accept-all" i]',
    'button[title*="Accept" i]','button[aria-label*="accept" i]'];
  for (const s of sels) {
    const b = document.querySelector(s);
    if (b && b.offsetParent !== null) { b.click(); return 'clicked:' + s; }
  }
  return 'none';
})()"""

DISCOVER_JS = """(() => {
  const out = {url: location.href, title: document.title, pdfs: [], signals: []};
  const txt = (document.body ? document.body.innerText : '').slice(0, 10000);
  if (/are you a robot|captcha|verify you are human|security check|安全验证|恶意自动程序|请稍候/i.test(txt + ' ' + document.title)) out.signals.push('CAPTCHA');
  if (/\\/abs\\/pii\\//.test(location.href)) out.signals.push('ABS_ONLY');
  if (/problem providing the content|CPE0000/i.test(txt)) out.signals.push('SERVER_ERR');
  for (const a of document.querySelectorAll('a[href]')) {
    const h = a.href;
    if (!/pdfft|\\.pdf|\\/pdf|showPdf|pdfdirect|\\/epdf\\//i.test(h)) continue;
    // 排除补充材料/图表等非正文 PDF（Springer ESM、Supplementary、cell.com attachment/pdfExtended、ACS/Wiley suppl_file/si_001）
    if (/\\/esm\\/|springer-static|supplementary|supplemental|moesm|figshare|\\/figures\\/|\\/attachment\\/|pdfExtended|\\/suppl\\/|suppl_file|downloadSupplement|supinfo|_si_/i.test(h)) continue;
    out.pdfs.push({
      href: h,
      text: (a.textContent || '').trim().slice(0, 60),
      cls: (a.className || '').toString().slice(0, 60),
      aria: a.getAttribute('aria-label') || '',
      title: a.getAttribute('title') || ''
    });
  }
  // 付费墙仅在无任何 PDF 入口时判定（Nature 订阅页在有权限时也显示 Buy 按钮）
  if (/get access|buy article|purchase pdf|access through your institution|log in through your institution|institutional access/i.test(txt) && out.pdfs.length === 0) out.signals.push('PAYWALL');
  return JSON.stringify(out);
})()"""

DL_JS = """(() => {
  try {
    window.__dl = 'RUNNING';
    fetch(location.href, {credentials: 'include'}).then(r => {
      window.__dlct = r.headers.get('content-type') || '';
      if (!r.ok) { window.__dl = 'ERR:http' + r.status; return null; }
      return r.blob();
    }).then(b => {
      if (!b) return;
      if (!/pdf/i.test(window.__dlct || '')) { window.__dl = 'ERR:ct:' + (window.__dlct || 'none'); return; }
      if (b.size < 30000) { window.__dl = 'ERR:small' + b.size; return; }
      const a = document.createElement('a');
      a.href = URL.createObjectURL(b);
      a.download = '%s';
      document.body.appendChild(a); a.click();
      window.__dlsize = b.size;
      window.__dl = 'DONE';
    }).catch(e => { window.__dl = 'ERR:' + ((e && e.message) || e); });
    return 'STARTED';
  } catch (e) { return 'THROW:' + e.message; }
})()"""

# ---------- 域名白名单：防参考文献外链污染（如 Thermo Fisher 说明书被当正文） ----------
from urllib.parse import urlparse
def _host_ok(page_url, href):
    try:
        ph = urlparse(page_url).hostname or ""
        hh = urlparse(href).hostname or ""
    except Exception:
        return False
    if not hh:
        return False
    def base(h):
        parts = h.split(".")
        return ".".join(parts[-2:]) if len(parts) >= 2 else h
    pb, hb = base(ph), base(hh)
    if pb == hb:
        return True
    pairs = {
        "sciencedirect.com": ("sciencedirectassets.com",),
        "nature.com": ("springernature.com", "nature.com"),
        "science.org": ("science.org",),
        "cell.com": ("cell.com",),
        "wiley.com": ("wiley.com", "onlinelibrary.wiley.com"),
        "acs.org": ("acs.org", "pubs.acs.org"),
    }
    allowed = pairs.get(pb, ())
    return any(hb == a or hh.endswith("." + a) for a in allowed)

# ---------- 统一关页：带重试+落盘确认，杜绝标签页堆积 ----------
def _safe_close(tid):
    if not tid:
        return
    try:
        if len(list_tabs()) <= 1:
            return  # 绝不关最后一个页
    except Exception:
        pass
    for _ in range(3):
        try:
            close_tab(tid)
        except Exception as e:
            print("close_err", repr(e)[:50])
        time.sleep(0.8)
        try:
            if all(t.get("targetId") != tid for t in list_tabs()):
                return  # 已确认关闭
        except Exception:
            return

# ---------- Phase A: 错峰开页 ----------
tabs = {}
print("=== PHASE A: staggered open ===")
for doi in DOIS:
    try:
        tid = new_tab("https://doi.org/" + doi)
        tabs[doi] = tid
        print("open", doi, tid)
    except Exception as e:
        print("open_err", doi, repr(e)[:100])
    time.sleep(STAGGER)

print("=== settle + cookie ===")
for doi, tid in tabs.items():
    try:
        switch_tab(tid)
        wait_for_load(timeout=25)
    except Exception as e:
        print("wait_err", doi, repr(e)[:80])
    time.sleep(1.0)
    try:
        c = js(COOKIE_JS, target_id=tid)
        if c and c != "none":
            print("cookie", doi, c)
    except Exception as e:
        print("cookie_err", doi, repr(e)[:60])

# ---------- Phase B: 人机交互优先诊断 + 严格PII的PDF发现 ----------
plan = {}
for doi, tid in tabs.items():
    try:
        info = json.loads(js(DISCOVER_JS, target_id=tid))
    except Exception as e:
        info = {"url": "", "title": "", "pdfs": [], "signals": ["ERR:" + repr(e)[:40]]}
    url = info.get("url", "")
    print("page", doi, "|", url[:85], "| signals:", info.get("signals"), "| pdfs:", len(info.get("pdfs", [])))
    # 诊断顺序铁律：先判人机/机构交互需求，再谈下载
    if info.get("signals"):
        plan[doi] = {"mode": "INTERACTION", "signals": info["signals"], "url": url}
        continue
    m = re.search(r"/pii/([A-Za-z0-9]+)", url)
    pii = m.group(1) if m else None
    # 通用文章 ID（Nature 型 /articles/<id>）：必须出现在 PDF 链接中，防图表/推荐位污染
    m2 = re.search(r"/articles/([a-z0-9-]+)", url)
    art_id = m2.group(1) if m2 else None
    name = doi.replace("/", "_") + ".pdf"
    def _ok(h):
        # 域名白名单：PDF 必须与文章同站/同出版商资产域
        if not _host_ok(url, h):
            return False
        # cell.com 正文只认 showPdf（pdfExtended/attachment 是 SI，发现端已滤）
        if "cell.com" in (urlparse(url).hostname or "") and "showPdf" not in h and "/pdf" not in h:
            return False
        # Wiley epdf 是阅读器页：无权限时弹回 /abs/，且不直接给 PDF
        if "/epdf/" in h:
            return False
        # 严格 PII：ScienceDirect pdfft/直链必须携带本文 PII，防推荐位污染
        if pii and "sciencedirectassets" not in h and "sciencedirect" in h:
            if pii not in h:
                return False
        if pii and "/pdfft" in h and pii not in h:
            return False
        if art_id and art_id not in h:
            return False
        return True
    # 两轮筛选：先挑正文 PDF 强模式，没有才退回裸 .pdf 链接
    strong = re.compile(r"/pdfft|showPdf|pdfdirect|/doi/pdf/|/articles/", re.I)
    cands = [p["href"] for p in info.get("pdfs", []) if _ok(p["href"])]
    pick = next((h for h in cands if strong.search(h)), None) or (cands[0] if cands else None)
    plan[doi] = {"mode": "DL", "pdf": pick, "name": name, "pii": pii} if pick else {"mode": "NOMATCH"}

# ---------- Phase C: 发起下载（导航 -> 同源异步 fetch） ----------
started = {}
for doi, p in plan.items():
    if p.get("mode") != "DL":
        print("SKIP", doi, p.get("mode"), p.get("signals", ""))
        # 修复：SKIP 页处理完立即关（此前漏关导致标签页堆积）
        _safe_close(tabs[doi])
        continue
    tid = tabs[doi]
    pdf, name = p["pdf"], p["name"]
    try:
        switch_tab(tid)
        goto_url(pdf)
        wait_for_load(timeout=25)
        # 等待落定最终 PDF host（sciencedirectassets）再注入，防后续跳转抹掉 window.__dl
        for _ in range(8):
            time.sleep(1.5)
            h = js("location.host", target_id=tid) or ""
            if "sciencedirectassets" in h or "pdfft" not in (pdf or ""):
                break
        time.sleep(1.0)
        # 权限弹回检测：PDF 链接落回 /abs/ 摘要页 = 无下载权限（Wiley epdf 典型表现）
        final_url = js("location.href", target_id=tid) or ""
        if "/abs/" in final_url and "/pdf" in (pdf or ""):
            print("FAILED", doi, "ABS_BOUNCE:no-access")
            _safe_close(tid)
            continue
        st = js(DL_JS % name, target_id=tid)
        print("dl_start", doi, "|", st, "|", js("location.href", target_id=tid)[:70])
        started[doi] = (tid, name)
    except Exception as e:
        print("dl_err", doi, repr(e)[:100])

# ---------- Phase D: 轮询 + 落盘确认后关页 ----------
deadline = time.time() + 300
while started and time.time() < deadline:
    time.sleep(6)
    for doi in list(started):
        tid, name = started[doi]
        try:
            st = js("window.__dl || 'PENDING'", target_id=tid)
        except Exception as e:
            st = "ERR:js:" + repr(e)[:40]
        fp = os.path.join(DL_DIR, name)
        # Chrome 同名冲突会加 " (1)" 后缀
        fp_alt = os.path.join(DL_DIR, name[:-4] + " (1).pdf")
        if st == "DONE":
            use = fp if os.path.exists(fp) else (fp_alt if os.path.exists(fp_alt) else None)
            if use:
                sz = os.path.getsize(use)
                time.sleep(1.5)
                sz2 = os.path.getsize(use)
                if sz == sz2 and sz > 30000:
                    print("OK", doi, sz2, "bytes", os.path.basename(use))
                    started.pop(doi)
                    _safe_close(tid)
        elif st.startswith("ERR"):
            print("FAILED", doi, st)
            started.pop(doi)
            _safe_close(tid)
        else:
            print("poll", doi, st)

for doi, (tid, name) in started.items():
    print("CARRYOVER(保留页面，加入下一批):", doi)

# ---------- 批尾清扫：本批所有已完结页面必须关闭（下载完一篇关一篇） ----------
keep = {tid for tid, _ in started.values()}
for doi, tid in tabs.items():
    if tid not in keep:
        _safe_close(tid)
# 再扫一遍全局：清掉历史残留页（只留最后一页）
_seen = set()
for t in list_tabs():
    tid = t.get("targetId")
    if tid in keep or tid in _seen:
        continue
    _seen.add(tid)
    if len(list_tabs()) > 1:
        _safe_close(tid)

print("=== SUMMARY ===")
for doi, p in plan.items():
    print(doi, "->", p.get("mode"), p.get("signals", ""))
print("done. tabs now:", len(list_tabs()))
