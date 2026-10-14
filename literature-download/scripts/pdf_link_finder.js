// pdf_link_finder.js — PDF 下载链接双通道发现（文本 + 图标启发）
// 用法：在出版商文章页上下文执行，返回按优先级排序的候选列表。
// browser-use: js("...") 包裹执行，或载入后调用 findPdfLinks()。
//
// 设计依据（人工识别下载按钮的两个线索）：
//   通道 A 文本匹配 — "Download PDF" / "View PDF" / "PDF (5.89 MB)" 等
//   通道 B 图标匹配 — Acrobat 风格图标：<img>/<svg>/background-image/aria-label 含 pdf
// 图标+文字组合（图标在链接内或链接是图标按钮的父级）置信度最高。

function findPdfLinks(doc) {
  doc = doc || document;
  const results = [];
  const seen = new Set();

  const URL_PAT = /(article-pdf|pdfdirect|pdfft|\/pdf\/|\.pdf($|\?))/i;
  const TEXT_PAT = /\bpdf\b/i;
  const ICON_PAT = /(icon[-_]?pdf|pdf[-_]?(icon|download|button|link)|acrobat|application\/pdf)/i;

  function push(el, channel, score) {
    const a = el.closest('a[href]') || (el.tagName === 'A' ? el : null);
    if (!a || !a.href || a.href.startsWith('javascript:')) return;
    if (seen.has(a.href)) return;
    seen.add(a.href);
    results.push({
      href: a.href,
      text: (a.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 60),
      channel,                       // 'text' | 'icon' | 'url'
      score,
    });
  }

  // 通道 A：文本匹配（明确动词优先）
  for (const a of doc.querySelectorAll('a[href]')) {
    const t = (a.textContent || '').trim();
    if (/download\s*pdf/i.test(t)) push(a, 'text', 100);
    else if (/\bpdf\b/i.test(t) && !/suppl|supporting|figure\s*s\d|table\s*s\d/i.test(t)) push(a, 'text', 80);
    else if (/\bpdf\b/i.test(t)) push(a, 'text', 40);   // 补充材料类文本
  }

  // 通道 B：图标匹配（img / svg / background-image / aria-label）
  for (const img of doc.querySelectorAll('img')) {
    const hay = [img.src, img.alt, img.className, img.id].join(' ');
    if (ICON_PAT.test(hay)) push(img, 'icon', 85);
  }
  for (const svg of doc.querySelectorAll('svg')) {
    const hay = [svg.className?.baseVal ?? svg.className, svg.getAttribute('aria-label') || '',
                 svg.getAttribute('title') || '', svg.parentElement?.className || ''].join(' ');
    if (ICON_PAT.test(hay)) push(svg, 'icon', 85);
  }
  for (const el of doc.querySelectorAll('[aria-label], [title]')) {
    const hay = (el.getAttribute('aria-label') || '') + ' ' + (el.getAttribute('title') || '');
    if (/\bpdf\b/i.test(hay)) push(el, 'icon', 75);
  }
  // background-image: url(...pdf...)
  for (const el of doc.querySelectorAll('*')) {
    const bg = getComputedStyle(el).backgroundImage || '';
    if (bg !== 'none' && /pdf|acrobat/i.test(bg)) push(el, 'icon', 70);
  }

  // URL 模式辅助（无文本无图标的裸链接）
  for (const a of doc.querySelectorAll('a[href]')) {
    if (URL_PAT.test(a.href) && !seen.has(a.href)) push(a, 'url', 60);
  }

  // 降权补充材料；升权正文 PDF
  for (const r of results) {
    if (/suppl|supporting|(^|[^a-z])si([^a-z]|$)/i.test(r.href)) r.score -= 30;
    if (/article-pdf|pdfdirect|pdfft/i.test(r.href)) r.score += 15;
  }

  results.sort((x, y) => y.score - x.score);
  return results;
}

// browser-use 直接调用：JSON.stringify(findPdfLinks())
