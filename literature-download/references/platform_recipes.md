# 出版商平台下载配方（实测验证）

更新：2026-10-14（2026-10-10 初版 + 2026-10-12 回顾管线 747 篇实战校准）。每条配方均经真实下载验证。DOI 前缀 → 平台映射。

## 期刊 SOP 速查表（快速通道：命中即直用，跳过探测）

遇到下表期刊时直接套用对应 SOP，不再走通用诊断流程。新期刊验证成功后立即追加。

| 期刊缩写 | 出版商 | PDF 入口模式 | 下载策略 | 已知陷阱 | 验证日期 |
|----------|--------|--------------|----------|----------|----------|
| Nat Commun / Nat Biomed Eng / Nat Microbiol / Nat Chem Biol / Nat Rev 系 | Nature | `/articles/<id>.pdf` | A: fetch→blob | ESM 补充材料混链；订阅刊需 WAYF 机构登录；Nat Rev 版式无 DOI 印记 | 2026-10-10 |
| Adv Healthc Mater / Adv Mater / Adv Funct Mater | Wiley | `/doi/pdfdirect/<doi>` | A: fetch→blob | `/doi/pdf/` 是 HTML 陷阱；**SAML 属性缺失时 pdfdirect/epdf 全部反弹 /abs/**（见下） | 2026-10-12 |
| Biomaterials / Mater Today Bio / Bioact Mater / Adv Drug Deliv Rev / J Hepatol | Elsevier-SD | `pdfft?md5=<签名>` | B: 导航→源站 fetch | Craft 无 JS 挑战；PII 需核对 | 2026-10-10 |
| Cell Host Microbe / Cancer Cell / Trends Cancer / Matter | Cell Press | `/action/showPdf?pii=<PII>` | A: fetch→blob | 域名是 cell.com 非 sciencedirect | 2026-10-10 |
| J Hepatol | Elsevier-JHep 独立站 | fulltext 页 PDF 链→els-jbs-prod-cdn.literatumonline.com | A: fetch→blob | 独立站 journal-of-hepatology.eu；登录墙时页零 PDF 入口 | 2026-10-10 |
| ACS Synth Biol / ACS Nano | ACS | `/article-pdf/.../<doi>.pdf` | A: fetch→blob(异步) | 文件大，必须异步轮询 | 2026-10-10 |
| Science / Sci Adv / Sci Transl Med | Science | `/doi/pdf/<doi>?download=true` | C: 导航原生下载 | fetch 被 CF 拦截 | 2026-10-10 |
| Gut | BMJ | 待实测 | 待实测 | — | — |

## 10.1038 — Springer Nature（nature.com）

- 文章页：`https://www.nature.com/articles/<id>`
- **策略 A**：文章页同源 `fetch('/articles/<id>.pdf')` → blob → 触发保存
- PDF 直链：`https://www.nature.com/articles/<id>.pdf`
- 无反爬挑战；**陷阱：ESM 补充材料混链**——`media.springernature.com/original/springer-static/esm/art%3A10.1038%2F<id>/...`
  是作者稿补充材料（首页含 "Supplementary information / In the format provided by the authors"），
  且 URL 内含文章 ID 会骗过严格匹配，发现阶段必须过滤 `/esm/|springer-static|supplementary|moesm`
- **订阅刊（Nat Microbiol/Nat Chem Biol/Nat Biomed Eng/Nat Rev 系等）**：未登录时 `.pdf` 返回 HTML。
  走 WAYF 机构登录（见 SKILL.md "Nature/Springer 机构登录"）一次放行全平台；OA 刊（Nat Commun 等）无需登录
- **Nat Rev 系 / Research Briefing 版式**：PDF 可提取文本中不印 DOI（"0123456789();:" 开头是正文特征），
  身份核验以下载 URL 精确匹配 + 标题/主题吻合为准
- 适用期刊：Nat Commun、Nat Biomed Eng、Nat Microbiol、Nat Chem Biol、Nat Rev Mater/Chem/Bioeng 等

## 10.1002 — Wiley（onlinelibrary.wiley.com）

- 文章页：`https://<journal>.onlinelibrary.wiley.com/doi/<doi>`（首访有 Cloudflare 挑战，等 10-20s）
- **策略 A**：同源 `fetch('/doi/pdfdirect/<doi>')` → blob → 触发保存
- **陷阱**：`/doi/pdf/<doi>` 和 `/doi/epdf/<doi>` 都返回 HTML（即使文章标记 Open Access！）
- `/doi/pdfdirect/<doi>?download=true` 变体可用
- **SAML 属性释放故障（2026-10-12 大规模实测，影响 SJTU 全校）**：`epdf/pdfdirect` 一律反弹 `/abs/`
  （ABS_BOUNCE），页面无 "Access provided by Shanghai Jiao Tong University" 横幅——IdP 未向 Wiley
  释放 eduPersonScopedAffiliation 等属性/Shibboleth 合同未激活，**客户端无解**。处理：hold 登记 +
  向网络信息中心报修（属性释放/合同激活/IP 段放行三选一）；PMC NIH 作者稿可救约 60%
- 适用期刊：Adv Healthc Mater、Adv Mater、Adv Sci、Adv Funct Mater 等

## 10.1016 — Elsevier / ScienceDirect（sciencedirect.com）

- 文章页：`https://www.sciencedirect.com/science/article/pii/<PII>`（Cloudflare "Are you a robot?" 常见，走人机协议）
- PDF 链接：`/science/article/pii/<PII>/pdfft?md5=<签名令牌>`（页面 "View PDF" 按钮）
- **策略 B（fetch 必失败）**：fetch 被 Craft 反爬拦截（返回 `craft/challenge/pdf/trace` 无 JS 挑战页）。
  必须完整导航到 pdfft URL → 自动跳转 `pdf.sciencedirectassets.com/<...>` → 在该源站同源 fetch → blob
- **PII 校验（重要）**：发现 PDF 链接时必须核对 URL 中 PII 与本文一致（推荐文列表的 pdfft 会混入扫描结果）。
  PII 期刊代号应与 DOI 期刊匹配（如 Biomaterials=S01429612…）；不符说明抓错文章，弃用换链
- **CPE00002 限流（2026-10-10 实测）**：批量请求过密时文章页整页变成 "There was a problem providing
  the content you requested"（Reference number + CPE00002）。这是反爬限流而非文章失效。
  处理：立即停止向 SD 发新请求 → 换出版商队列推进 → 冷却 10-15 分钟后 2-3 篇小批量试探。
  错峰间隔从 3.5s 放宽到 5s 可降低触发频率；同批部分 CPE 是全面限流前兆
- **"Sign in" 按钮 = 机构会话丢失（2026-10-12）**：登录态正常时头栏无 Sign in；它一出现就是
  institutional session 掉了 → 告警请用户重新机构登录（勿误判为限流/慢速）
- **ABS_BOUNCE（下载前拦截）**：`/pdfft`/epdf URL 被弹回 `/abs/` = 无访问权限。发下载前先探 bounce，
  命中直接 hold，别浪费下载动作
- 适用期刊：Mater Today Bio、Biomaterials、Bioact Mater、Adv Drug Deliv Rev、J Hepatol 等

## 10.1016 子域 — Cell Press（cell.com）

- 文章页：`https://www.cell.com/<journal>/fulltext/<PII>`（与 ScienceDirect 同一 DOI 前缀但域名单独）
- PDF 直链：`https://www.cell.com/action/showPdf?pii=<URL编码PII>`（页面 "PDF" 按钮即此链接）
- **策略 A 可用**：导航到 showPdf 落地后同源 fetch → blob（实测无反爬，比 SD 更快）
- 适用期刊：Cell Host Microbe、Cancer Cell、Trends Cancer、Matter、Cell Metab 等

## 10.1021 — ACS（pubs.acs.org）

- 文章页：`https://pubs.acs.org/<journal>/article/<...>/<doi>`（通常无挑战）
- **策略 A**：同源 `fetch('/<journal>/article-pdf/.../<doi>.pdf')` → blob
- **注意**：PDF 文件常较大（>5MB），同步 fetch 会超 IPC 5s 限制 → 必须异步+轮询模式
- **CAPTCHA 升级（2026-10-12）**：连续批量后触发 CAPTCHA/人机验证（尤其 ACS Chem Rev 等老刊页面）。
  标 INTERACTION 跳过 + hold；用户交互登录一次可放行同平台后续批次；顽固篇单列人工
- 补充材料：`/article-supplement/<id>/pdf/<si_name>/`（`suppl_file/..._si_*.pdf` 链接在发现阶段排除）
- 适用期刊：ACS Synth Biol、ACS Nano 等

## 10.1126 — Science / AAAS（science.org）

- 文章页：`https://www.science.org/doi/<doi>`（Cloudflare 挑战常见）
- **策略 C**：fetch 会被 Cloudflare "Just a moment" 拦截；导航到
  `https://www.science.org/doi/pdf/<doi>?download=true` → 即使导航被重定向回文章页，Chrome 原生下载已被触发
- **策略 B 备选**：导航到 `/doi/pdf/<doi>`（无参数）→ 完整加载后同源 fetch
- **无订阅判定（2026-10-12）**：机构未订阅时"下载"得到 HTML 全文页而非 PDF——确认订阅状态后归
  deferred（无订阅清单），不重试；Sci Adv 等 OA 刊不受影响
- 适用期刊：Science、Sci Transl Med（订阅）；Sci Adv（OA）等

## 10.1039 — RSC（pubs.rsc.org）

- 机构会话有效（2026-10-12 用户交互验证通过）；入口模式待补测（文章页 PDF 按钮直链）
- 实测 3/3 成功（Chem Soc Rev）；连续下载注意错峰
- 适用期刊：Chem Soc Rev、Chem Sci 等

## 10.1136 — BMJ（bmj.com）

- Gut 等期刊；待实测补充配方

## 通用诊断流程（遇到新平台时）

1. 文章页 DOM 扫描（scripts/pdf_link_finder.js）找到候选链接
2. 先试策略 A（fetch+校验 Content-Type）
3. 若返回 HTML：读响应判断是登录墙（log in/purchase/institution）还是反爬挑战（craft/challenge/Just a moment）
4. 反爬挑战 → 策略 B（完整导航）；登录墙 → 人机协作协议（请用户机构登录）
5. 成功后把新配方追加到本文件

## 匹配与归档备注

- `elm_import_pdfs.py` 匹配优先级（2026-10-12 校准）：**filename_doi > doi_in_text > 提取 DOI 精确互认
  > 模糊（仅当提不出 DOI，阈值 0.6）**；PDF 带 DOI 但对不上库 → 人工，绝不模糊绑定（误绑事故教训）
- SI 头部判据：剥开头 URL 后 `supplement…/supporting information…` 起头，或含 `supplementary materials for`
  /`major resources table`/`in the format provided by the authors` 才判 SI
- 实测：Nature/Science PDF 内嵌 DOI 可精确匹配（1.00）；部分 Elsevier/ACS PDF 需标题匹配（0.92-1.00）
- 匹配分 0.90-0.95 之间建议人工确认后入库
- 导入后 md5 哈希核验（残留副本/异版式识别）；`--apply` 写库前停下载驱动（单写者）
