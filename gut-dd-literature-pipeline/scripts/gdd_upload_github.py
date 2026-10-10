# -*- coding: utf-8 -*-
"""Upload a literature project directory to GitHub via REST (api.github.com).
Single atomic commit: Git Data API (blobs -> tree -> commit -> ref).

Facts learned the hard way:
- github.com (git protocol/web) is often unreachable; api.github.com works -> use REST.
- Empty repo rejects git/blobs (409) -> bootstrap initial commit via Contents API.
- 422 "not a fast forward": commit must carry parents:[head_sha]; force-PATCH fallback.
- COPYRIGHT: publisher PDFs are NEVER uploaded. 01_PDF/ and *.pdf are always skipped.

Usage:
  python gdd_upload_github.py --root PROJECT_DIR --owner OWNER --repo REPO
      [--branch main] [--message "commit msg"] [--token-file path]
Token: env GITHUB_TOKEN or --token-file (fine-grained PAT, Contents: Read and write).
"""
import argparse, base64, json, os, sys, time, urllib.request

API = 'https://api.github.com'
ALWAYS_SKIP_FILES = {'gdd_upload_github.py', 'upload_rest.py', 'push_via_connector.py', 'probe_write.py'}


def get_token(args):
    t = os.environ.get('GITHUB_TOKEN')
    if t:
        return t.strip()
    if args.token_file and os.path.exists(args.token_file):
        return open(args.token_file, encoding='utf-8').read().strip()
    sys.exit('missing token: set GITHUB_TOKEN or pass --token-file')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    ap.add_argument('--owner', default='DediCationMeng')
    ap.add_argument('--repo', default='GDD-References')
    ap.add_argument('--branch', default='main')
    ap.add_argument('--message', default='GDD literature library update')
    ap.add_argument('--token-file', default=None)
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    token = get_token(args)

    def api(method, path, payload=None):
        data = json.dumps(payload).encode('utf-8') if payload is not None else None
        req = urllib.request.Request(API + path, data=data, method=method, headers={
            'Authorization': 'Bearer ' + token,
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
            'Content-Type': 'application/json',
            'User-Agent': 'gdd-uploader',
        })
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    return json.loads(r.read() or b'{}')
            except urllib.error.HTTPError as e:
                body = e.read().decode('utf-8', 'ignore')[:300]
                if e.code in (429, 502, 503) and attempt < 3:
                    time.sleep(3 * (attempt + 1))
                    continue
                raise RuntimeError(f'{e.code} {method} {path}: {body}')
            except urllib.error.URLError:
                if attempt < 3:
                    time.sleep(3 * (attempt + 1))
                    continue
                raise

    # collect files; COPYRIGHT RED LINE: never upload PDFs / 01_PDF
    files = []
    skip_dirs = {'.git', '__pycache__', '01_PDF', 'raw'}
    for r, dirs, fs in os.walk(root):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for f in sorted(fs):
            if f in ALWAYS_SKIP_FILES or f.lower().endswith('.pdf') or f == '.gitignore':
                continue
            p = os.path.join(r, f)
            files.append((os.path.relpath(p, root).replace('\\', '/'), p))
    files.sort()
    print(f'uploading {len(files)} files to {args.owner}/{args.repo}@{args.branch} (PDFs excluded by policy)')

    # empty-repo bootstrap
    try:
        ref = api('GET', f'/repos/{args.owner}/{args.repo}/git/ref/heads/{args.branch}')
        head_sha = ref['object']['sha']
        empty = False
    except RuntimeError:
        empty, head_sha = True, None

    if empty:
        readme = os.path.join(root, 'README.md')
        content = open(readme, 'rb').read() if os.path.exists(readme) else b'# GDD References\n'
        res = api('PUT', f'/repos/{args.owner}/{args.repo}/contents/README.md',
                  {'message': 'Initialize repository', 'content': base64.b64encode(content).decode('ascii'),
                   'branch': args.branch})
        head_sha = res['commit']['sha']
        print('initial commit created (empty repo bootstrap)')

    tree = []
    for rel, p in files:
        with open(p, 'rb') as fh:
            b64 = base64.b64encode(fh.read()).decode('ascii')
        blob = api('POST', f'/repos/{args.owner}/{args.repo}/git/blobs', {'content': b64, 'encoding': 'base64'})
        tree.append({'path': rel, 'mode': '100644', 'type': 'blob', 'sha': blob['sha']})
        print('  blob ok:', rel)

    tr = api('POST', f'/repos/{args.owner}/{args.repo}/git/trees', {'tree': tree})
    commit = api('POST', f'/repos/{args.owner}/{args.repo}/git/commits', {
        'message': args.message, 'tree': tr['sha'],
        'parents': [head_sha] if head_sha else [],
    })
    try:
        api('POST', f'/repos/{args.owner}/{args.repo}/git/refs',
            {'ref': f'refs/heads/{args.branch}', 'sha': commit['sha']})
        print('branch created')
    except RuntimeError as e:
        if '422' in str(e):
            try:
                api('PATCH', f'/repos/{args.owner}/{args.repo}/git/refs/heads/{args.branch}',
                    {'sha': commit['sha']})
            except RuntimeError as e2:
                if 'fast forward' in str(e2):
                    api('PATCH', f'/repos/{args.owner}/{args.repo}/git/refs/heads/{args.branch}',
                        {'sha': commit['sha'], 'force': True})
                else:
                    raise
            print('branch updated')
        else:
            raise
    print('DONE ->', f'https://github.com/{args.owner}/{args.repo}')


if __name__ == '__main__':
    main()
