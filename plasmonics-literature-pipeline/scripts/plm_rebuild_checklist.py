# -*- coding: utf-8 -*-
"""Rebuild 03_Reports/手动下载Checklist.md:

  Tri-state marks (三个符号互不重复, 2026-10-10 用户修正):
    [√] = obtained PDF     -- 勾选条目头部方框
    [ ] = pending          -- 可经 DOI 入口下载
    [x] = library-unsubscribed / cannot obtain -- 勾选条目下"无法下载"方框

  TWO clickable boxes per entry (fix: single checkbox could only express the
  "checked" state, so [x] was unmarkable by clicking):
    header box  `- [ ] **name**`            -> click = obtained
    sub box     `- [ ] 无法下载（...）`      -> click = [x] 态

  Click-glyph robustness: editors may write different checked glyphs ([x] / [√]).
  Semantics are carried by WHICH box is checked, not the glyph:
    sub-box checked                          -> 'na'   (the ONLY authority for [x])
    header '×' (legacy mark, sub unchecked)  -> 'na'
    header non-empty (incl. [√] / [v])       -> 'got'
    header '[x]'/'[X]' with sub unchecked    -> 'pending'  (stale na-header after the
                                               user unchecks the sub box -> back to
                                               pending; the na box is authoritative)
    header empty                             -> 'pending'
  Rebuild normalises glyphs back to the canonical [√]/[ ]/[x] and preserves
  all user marks (exact + fuzzy CN match). Research papers (incl. preprints)
  and reviews/opinions in SEPARATE sections; sorted: obtained first ->
  unsubscribed last -> journal priority -> date.

Usage:
  python plm_rebuild_checklist.py [--dir WORKDIR] [--window "2026-09-09 至 2026-10-09"]
"""
import argparse, datetime, json, os, re

PUNCT = re.compile(r'[\s：:？?、，,。（）()《》“”"\'\-_/\\]')
CHECKED = 'xXvV√×✓'


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

    # recover previous user states: name -> 'got' / 'pending' / 'na'
    # (sub "无法下载" box wins over header glyph; legacy '×' header = na)
    prev_states = {}
    cur = None
    for line in old.splitlines():
        m = re.match(r'- \[([^\]]*)\] \*\*(.+?)\*\*', line)
        if m:
            cur = m.group(2)
            h = m.group(1).strip()
            if h == '×':
                prev_states[cur] = 'na'          # legacy na mark
            elif h in ('x', 'X'):
                prev_states[cur] = 'pending'     # stale na-header; sub box is authoritative
            elif h:
                prev_states[cur] = 'got'
            else:
                prev_states[cur] = 'pending'
            continue
        m2 = re.match(r'\s+- \[([^\]]*)\] 无法下载', line)
        if m2 and cur:
            if m2.group(1).strip():
                prev_states[cur] = 'na'

    def prev_state_for(rec):
        n = rec.get('normalized_name') or rec['title']
        if n in prev_states:
            return prev_states[n]
        cn = norm_cn(n.split('-', 3)[-1])
        for k, v in prev_states.items():
            if norm_cn(k.split('-', 3)[-1]) == cn:
                return v
        return None

    def entry_lines(rec):
        if rec.get('pdf_downloaded'):
            state = 'got'
        else:
            state = prev_state_for(rec) or 'pending'
        head = {'got': '[√]', 'pending': '[ ]', 'na': '[x]'}[state]
        sub = '[x]' if state == 'na' else '[ ]'
        doi = rec.get('doi')
        ja = rec.get('journal_abbrev') or rec.get('journal') or 'Preprint'
        name = rec.get('normalized_name') or rec['title']
        out = [f"- {head} **{name}**"]
        out.append(f"  - {sub} 无法下载（机构未订阅、无法获取全文）—— 勾选此方框即标记 [x] 态，后续不再追踪")
        # info fields = plain indented text (NO '- ' list marks / NO checkboxes)，
        # 否则在任务列表编辑器里会被渲染成可勾选项（用户 2026-10-10 要求）。
        # 两空格硬换行保证渲染时各字段独立成行。
        br = '  '
        out.append(f"  期刊：{ja}｜日期：{rec.get('date')}｜类型：{'综述/观点' if art_type(rec)=='review' else '研究论文'}｜通讯作者(推定)：{rec.get('corresponding_author') or '见原文'}{br}")
        out.append(f"  英文原标题：{rec['title']}{br}")
        out.append(f"  下载入口：<https://doi.org/{doi}>{br}" if doi else f"  下载入口：暂无 DOI，请按英文原题检索{br}")
        if rec.get('pdf_downloaded'):
            out.append(f"  状态：已获取（01_PDF/{rec.get('pdf_file') or ''}）")
        else:
            out.append("  建议渠道：机构图书馆/校园网；若未订阅请勾选上方「无法下载」方框")
        return out

    research = [r for r in db if art_type(r) == 'research']
    review = [r for r in db if art_type(r) == 'review']

    def state_of(r):
        return 'got' if r.get('pdf_downloaded') else (prev_state_for(r) or 'pending')

    def sort_key(r):
        st = state_of(r)
        got = {'got': 0, 'pending': 1, 'na': 2}[st]
        return (got, PRIO.get(r.get('journal_abbrev') or '', 4), r.get('date') or '')

    research.sort(key=sort_key)
    review.sort(key=sort_key)
    n_have = sum(1 for r in db if state_of(r) == 'got')
    n_na = sum(1 for r in db if state_of(r) == 'na')
    n_pend = len(db) - n_have - n_na

    window = args.window or ('%s 至 %s' % (min((r.get('date') or '9999') for r in db),
                                           max((r.get('date') or '') for r in db)))
    lines = [f'# 论文获取 Checklist（{window} 检索窗口）', '',
             f'更新于 {datetime.date.today()}。', '',
             '**三态标记说明**（三个符号互不重复）：',
             '- `[√]` = 已获取 PDF（已按规范化命名存入 `01_PDF/`）—— 勾选条目**头部方框**即标记为此态',
             '- `[ ]` = 待下载（可通过 DOI 入口下载）',
             '- `[x]` = 机构未订阅、无法下载 —— 勾选条目下**「无法下载」方框**即标记为此态，后续不再追踪', '',
             '**点击说明**：每条目**只有两个**可点选方框（头部「已获取」＋「无法下载」），两种状态均可直接点选标记；',
             '期刊/英文原标题/下载入口/建议渠道等信息行为纯文本，不是勾选项。',
             '部分编辑器勾选后显示的符号可能不同（如 `[x]` 或 `[√]`），不影响语义——以**勾选了哪个方框**为准；',
             '取消同理：再次点击取消勾选即可（取消「无法下载」勾选 = 回到待下载，头部残留标记会被自动清理）。',
             '重跑 `plm_rebuild_checklist.py` 会自动规范回上述标准三态符号，并保留你的全部勾选记录。', '',
             f'**当前统计**：已获取 {n_have} 篇｜待下载 {n_pend} 篇｜未订阅 [x] {n_na} 篇'
             f'（研究论文 {len(research)} 篇、综述/观点 {len(review)} 篇）', '']

    def emit(title, recs):
        lines.append(f'## {title}（{len(recs)} 篇）')
        lines.append('')
        for r in recs:
            lines.extend(entry_lines(r))
            lines.append('')

    emit('一、研究论文（含预印本）', research)
    emit('二、综述 / 观点', review)

    open(old_path, 'w', encoding='utf-8').write('\n'.join(lines))
    print('checklist rebuilt:', old_path)
    print('research:', len(research), '| review:', len(review))
    print('states -> got:', n_have, '| pending:', n_pend, '| na:', n_na)
    print('preserved user marks (got/na) on missing items:', n_have - sum(1 for r in db if r.get('pdf_downloaded')) + n_na)


if __name__ == '__main__':
    main()
