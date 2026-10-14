# EuropePMC 批量取件：对搁置 DOI 查 PMC 全文并直下 PDF（绕开出版商 Cloudflare/付费墙）
# 用法: python epmc_fetch.py [--limit N]   （处理 hold_dois.json 中全部可取 DOI）
# 产物: retrospective/_epmc_staging/<doi>.pdf + epmc_fetch.log
# PDF 取件走 pmc_pow.py（NCBI PoW 挑战求解，sha256(challenge+nonce) 前4位hex为0）
import json, os, time, urllib.request, urllib.parse, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pmc_pow import fetch_pdf_with_pow

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(BASE, "tools")
STAGING = os.path.join(BASE, "_epmc_staging")
os.makedirs(STAGING, exist_ok=True)

API = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
PDF_URL = "https://pmc.ncbi.nlm.nih.gov/articles/%s/pdf/"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/155.0 Safari/537.36"}

def fetch_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def main():
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    hold = json.load(open(os.path.join(TOOLS, "hold_dois.json"), encoding="utf-8"))
    db = json.load(open(os.path.join(BASE, "literature_database.json"), encoding="utf-8"))
    done = {(r.get("doi") or "").lower() for r in db if r.get("pdf_downloaded")}
    todo = [d for d in hold if d.lower() not in done]
    if limit:
        todo = todo[:limit]
    print(f"todo: {len(todo)} DOIs")

    log = open(os.path.join(TOOLS, "epmc_fetch.log"), "a", encoding="utf-8")
    def say(s):
        print(s)
        log.write(s + "\n")
        log.flush()

    got = miss = err = 0
    for i, doi in enumerate(todo):
        dest = os.path.join(STAGING, doi.replace("/", "_") + ".pdf")
        if os.path.exists(dest):
            continue
        try:
            q = urllib.parse.quote(f'DOI:"{doi}"', safe=":")
            d = fetch_json(f"{API}?query={q}&format=json&resultType=lite")
            rs = d.get("resultList", {}).get("result", [])
            if not rs:
                say(f"NOIDX {doi}")
                miss += 1
                time.sleep(0.4)
                continue
            r = rs[0]
            pmcid, haspdf, inepmc = r.get("pmcid"), r.get("hasPDF"), r.get("inEPMC")
            if pmcid and haspdf == "Y" and inepmc == "Y":
                status, sz = fetch_pdf_with_pow(PDF_URL % pmcid, dest)
                if sz:
                    say(f"GOT {doi} {pmcid} {sz}bytes {status}")
                    got += 1
                else:
                    say(f"DLFAIL {doi} {pmcid} {status}")
                    err += 1
            else:
                say(f"NOPDF {doi} pmcid={pmcid} hasPDF={haspdf} inEPMC={inepmc}")
                miss += 1
        except Exception as e:
            say(f"ERR {doi} {repr(e)[:80]}")
            err += 1
        time.sleep(2.5)
        if (i + 1) % 25 == 0:
            say(f"... progress {i+1}/{len(todo)} got={got} miss={miss} err={err}")

    say(f"=== EPMC FETCH DONE === got={got} miss={miss} err={err}")
    log.close()

if __name__ == "__main__":
    main()
