# PMC PoW 求解器：解析 "Preparing to download" 挑战页，算出 cookie 后直取 PDF
# 算法（来自 NCBI pow-o51sQKbL.js）：hash(challenge + str(nonce)).hex() 前 difficulty 位为 '0'
# cookie: cloudpmc-viewer-pow = "<challenge>,<nonce>"
import hashlib, http.cookiejar, re, sys, time, urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/155.0 Safari/537.36"}

def solve_pow(challenge, difficulty, algo):
    prefix = "0" * difficulty
    h = getattr(hashlib, algo)
    nonce = 0
    while nonce < 500000:
        if h((challenge + str(nonce)).encode()).hexdigest().startswith(prefix):
            return nonce
        nonce += 1
    return None

def fetch_pdf_with_pow(pdf_url, dest):
    for attempt in range(8):
        cj = http.cookiejar.CookieJar()
        op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        data = op.open(urllib.request.Request(pdf_url, headers=UA), timeout=60).read()
        if data.startswith(b"%PDF"):
            open(dest, "wb").write(data)
            return "direct", len(data)
        m = re.search(rb'POW_CHALLENGE\s*=\s*"([^"]+)"', data)
        md = re.search(rb'POW_DIFFICULTY\s*=\s*"(\d+)"', data)
        if not (m and md):
            # reCAPTCHA 限流页：退避后重试
            if b"reCAPTCHA" in data or b"Checking your browser" in data:
                time.sleep(15 + 5 * attempt)
            else:
                time.sleep(5)
            continue
        challenge, diff = m.group(1).decode(), int(md.group(1))
        for algo in ("sha256", "sha1", "md5"):
            nonce = solve_pow(challenge, diff, algo)
            if nonce is None:
                continue
            ck = http.cookiejar.Cookie(
                version=0, name="cloudpmc-viewer-pow", value=f"{challenge},{nonce}",
                port=None, port_specified=False, domain="pmc.ncbi.nlm.nih.gov",
                domain_specified=True, domain_initial_dot=False, path="/", path_specified=True,
                secure=False, expires=None, discard=True, comment=None, comment_url=None,
                rest={}, rfc2109=False)
            cj.set_cookie(ck)
            data = op.open(urllib.request.Request(pdf_url, headers=UA), timeout=60).read()
            if data.startswith(b"%PDF"):
                open(dest, "wb").write(data)
                return f"pow-ok({algo},nonce={nonce},attempt={attempt})", len(data)
        time.sleep(3)
    return "pow-exhausted", 0

if __name__ == "__main__":
    url, dest = sys.argv[1], sys.argv[2]
    status, size = fetch_pdf_with_pow(url, dest)
    print("==", status, size)
