# -*- coding: utf-8 -*-
"""Rebuild 03_Reports/手动下载Checklist.md:
  - tri-state marks: [x] obtained / [ ] pending / [x]-variant = library-unsubscribed (×)
  - user-set marks (especially ×) PRESERVED across rebuilds (exact + fuzzy CN match)
  - research papers (incl. preprints) and reviews/opinions in SEPARATE sections
  - sorted: obtained first -> journal priority -> date

Usage:
  python gdd_rebuild_checklist.py [--dir WORKDIR] [--window "2026-09-09 至 2026-10-09"]
"""
import argparse, datetime, json, os, re

PUNCT = re.compile(r'[\s：:？?、，,。（）()《》“”"\'\-_/\\]')


def norm_cn(s):
    return PUNCT.sub('', s)


def art_type(rec):
    pts = [p.lower() for p in (rec.get('pubtypes') or [])]
    return 'review' if 'review' in pts else 'research'


# journal priority tiers (tier 1 = top journals first)
PRIO = {'Nat Microbiol': 1, 'Gut': 1, 'Cell Host Microbe': 1, 'Cell Rep Med': 1, 'Lancet Oncol': 1,
        'Nat Commun': 1, 'Adv Sci (Weinh)': 2, 'Bioact Mater': 2, 'Biomaterials': 2, 'Small': 2,
        'Adv Healthc Mater': 2, 'Mater Horiz': 2, 'Mater Today Bio': 2, 'J Control Release': 2,
        'Trends Biotechnol': 2, 'Acta Biomater': 2, 'Biofabrication': 2, 'Lab Chip': 2,
        'Nat Biomed Eng': 1, 'Sci Adv': 1, 'Cell': 1, 'Nature': 1, 'Science': 1}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.getcwd())
    ap.add_argument("--window", default=None, help="search window label for the title")
    args = ap.parse_args()
    base = args.dir

    db = json.load(open(os.path.join(base, 'literature_database.json'), encoding='utf-8'))
    rep_dir = os.path.join(base, '03_Reports')
    os.makedirs(rep_dir, exist_ok=True)
    old_path = os.path.join(rep_dir, '手动下载Checklist.md')
    old = open(old_path, encoding='utf-8').read() if os.path.exists(old_path) else ''

    # recover previous user marks: name -> 'x' / '×' / ' '
    prev_marks = {}
    for m in re.finditer(r'- \[([ x×X])\] \*\*(.+?)\*\*', old):
        mark, name = m.group(1), m.group(2)
        prev_marks[name] = mark.lower() if mark.lower() in ('x', '×') else ' '

    def prev_mark_for(rec):
        n = rec.get('normalized_name') or rec['title']
        if n in prev_marks:
            return prev_marks[n]
        cn = norm_cn(n.split('-', 3)[-1])
        for k, v in prev_marks.items():
            if norm_cn(k.split('-', 3)[-1]) == cn:
                return v
        return None

    def entry_lines(rec):
        mark = 'x' if rec.get('pdf_downloaded') else (prev_mark_for(rec) or ' ')
        disp = '×' if mark == '×' else mark
        doi = rec.get('doi')
        ja = rec.get('journal_abbrev') or rec.get('journal') or 'Preprint'
        name = rec.get('normalized_name') or rec['title']
        out = [f"- [{disp}] **{name}**"]
        out.append(f"  - 期刊：{ja}｜日期：{rec.get('date')}｜类型：{'综述/观点' if art_type(rec)=='review' else '研究论文'}｜通讯作者(推定)：{rec.get('corresponding_author') or '见原文'}")
        out.append(f"  - 英文原标题：{rec['title']}")
        out.append(f"  - 下载入口：<https://doi.org/{doi}>" if doi else "  - 下载入口：暂无 DOI，请按英文原题检索")
        if rec.get('pdf_downloaded'):
            out.append(f"  - 状态：已获取（01_PDF/{rec.get('pdf_file') or ''}）")
        else:
            out.append("  - 建议渠道：机构图书馆/校园网；若未订阅请将本条标记为 [×]")
        return out

    research = [r for r in db if art_type(r) == 'research']
    review = [r for r in db if art_type(r) == 'review']

    def sort_key(r):
        got = 0 if r.get('pdf_downloaded') else 1
        return (got, PRIO.get(r.get('journal_abbrev') or '', 4), r.get('date') or '')

    research.sort(key=sort_key)
    review.sort(key=sort_key)
    n_have = sum(1 for r in db if r.get('pdf_downloaded'))

    window = args.window or ('%s 至 %s' % (min((r.get('date') or '9999') for r in db),
                                           max((r.get('date') or '') for r in db)))
    lines = [f'# 论文获取 Checklist（{window} 检索窗口）', '',
             f'更新于 {datetime.date.today()}。', '',
             '**三态标记说明**：',
             '- `[x]` = 已获取 PDF（已按规范化命名存入 `01_PDF/`）',
             '- `[ ]` = 待下载（可通过 DOI 入口下载）',
             '- `[×]` = 高校图书馆机构未订阅、无法下载 —— 请手动把 `[ ]` 改为 `[×]` 以标记，后续不再追踪', '',
             f'**当前统计**：已获取 {n_have} 篇｜待获取 {len(db) - n_have} 篇（研究论文 {len(research)} 篇、综述/观点 {len(review)} 篇）', '']

    def emit(title, recs):
        lines.append(f'## {title}（{len(recs)} 篇）')
        lines.append('')
        for r in recs:
            lines.extend(entry_lines(r))
            lines.append('')

    emit('一、研究论文（含预印本）', research)
    emit('二、综述 / 观点', review)

    open(old_path, 'w', encoding='utf-8').write('\n'.join(lines))
    kept = sum(1 for r in db if not r.get('pdf_downloaded') and prev_mark_for(r) == '×')
    print('checklist rebuilt:', old_path)
    print('research:', len(research), '| review:', len(review), '| have:', n_have)
    print('preserved user [×] marks on missing items:', kept)


if __name__ == '__main__':
    main()
