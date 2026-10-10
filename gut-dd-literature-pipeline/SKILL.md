---
name: gut-dd-literature-pipeline
description: 肠道靶向药物递送载体（drug delivery / drug carrier / nanocarrier / nanomedicine）领域文献检索-处理-归档全流程，重点方向：靶向肠道（gut/intestine/colon）的药物递送载体开发及其生物医学应用。触发词：药物递送文献检索、药物载体、给药系统、纳米药物、纳米载体、肠道靶向递送、gut-targeted delivery、colon-specific、口服递送文献、文献追踪、月度文献整理、回顾性检索过去N年文献、补齐领域核心文献、文献库、BibTeX、Zotero、手动下载checklist、上传GitHub文献库。覆盖 Europe PMC/arXiv/CrossRef 检索、DOI补全、规范化命名、PDF管理、三态checklist、月度摘要报告、TOP精读报告、GitHub归档。
---

# 肠道靶向药物递送载体 文献流水线（检索 → 处理 → 归档）

领域：药物递送载体（drug delivery carriers），聚焦**靶向肠道**（gut / intestine / colon）
的载体开发与生物医学应用。关键词四大块（2026-10-09 用户指定）——
① **核心主题词**：drug delivery / drug delivery system (DDS)、drug carrier / delivery vehicle /
nanocarrier、nanomedicine、nanoformulation、pharmaceutical formulation；
② **肠道词**：gut、intestin*、colon、colonic、colorectal、gastrointestin*、bowel、
ileum/jejunum/duodenum/cecum/rectum、enteral、colon-specific/colon-targeted/gut-targeted；
③ **载体类型**：nanoparticle*/liposome*/LNP/polymeric NP/micelle*/dendrimer*/hydrogel*/
exosome*/MOF/介孔硅/PLGA/壳聚糖等；④ **应用与策略**：靶向/控释/刺激响应/基因递送/
口服递送/肠道吸收/菌群/IBD/生物利用度等。
目标期刊**严格限定第一、第二梯队共 20 本**（见 references/workflow.md §8）：
第一梯队 Nature、Science、Nat Rev Drug Discov、Chem Rev、Chem Soc Rev、Nat Nanotechnol、
Nat Mater、Nat Biomed Eng、Adv Mater、Angew Chem；
第二梯队 J Control Release、Adv Drug Deliv Rev、ACS Nano、Nano Today、Biomaterials、
Matter、Nat Commun、Sci Adv、Nano Lett、JACS。**除此之外一律不检索**（白名单外记录仍会
存档进 literature_database_all.json 并计数入 exclusion_log，随时可放宽重刷）。
本 skill 于 2026-10-09 由 `elm-literature-pipeline` 派生（脚本同构，`gdd_` 前缀）；
等离激元/ELM 方向的查询与白名单保留在原 skill，可随时回切。

本 skill 有两种运行模式，由用户意图决定：

| 模式 | 触发 | 时间窗 | 产出侧重 |
|---|---|---|---|
| **月度追踪** | "整理上个月的文献" / 定时自动化 | 上次运行至今（约 1 个月） | 全套 6 项交付 |
| **回顾补齐** | "彻底检索过去 5 年文献" / "补齐领域发展历程" | 用户指定（如近 5 年） | 按年分批 + 年度综评 + 每年 TOP 精读 + 发展时间线 |

## 工作目录约定

每次运行建立/使用一个输出目录 `GDD-Literature-<YYYY-MM>/`（回顾模式用
`GDD-Retrospective-<起>-<止>/`）：

```
GDD-Literature-2026-10/
├── 01_PDF/            # PDF 存放（GitHub 永不上传，版权红线）
├── 02_BibTeX/         # GDD_<YYYY-MM>_library.bib + naming_manifest.csv
├── 03_Reports/        # 摘要报告、精读报告、手动下载Checklist.md
├── raw/               # epmc_raw.json / arxiv_raw.json
├── cn_titles.json     # 英文题名词头 → 中文译名（由你逐篇翻译填写）
├── literature_database.json  # 全量元数据库（唯一数据源）
└── tools/             # 本 skill scripts 拷贝（保证可复跑）
```

**运行方式**：把 `scripts/*.py` 拷贝到工作目录 `tools/` 下执行（脚本以自身目录为 BASE），
或传 `--dir` 指定工作目录。用管理版 Python 运行（见环境 binaries）。

## 标准流程

### 第 1 步：检索入库（6 组查询主题）
1. `python tools/gdd_search.py --from YYYY-MM-DD --to YYYY-MM-DD` → `raw/epmc_raw.json`、
   `raw/arxiv_raw.json`。标准 3 组（脚本内置）：
   - **DD-CORE**：核心主题词 × 载体总称（nanoparticle*/liposome*/micelle*/hydrogel*/exosome*…）
     —— 药物递送载体开发的宽检索；
   - **GUT-DD**：核心主题词 × 肠道词（gut/intestin*/colon/colonic/gastrointestin*/ileum…）
     —— **肠道靶向药物递送载体的开发（核心需求）**；
   - **GUT-BIO**：载体 × 肠道 × 生物医学应用词（therapeut*/disease*/bioavailabilit*/
     microbiome/IBD/Crohn/ulcerative colitis/pharmacokinet*…）—— 肠道递送载体的生物医学应用。
2. `python tools/gdd_search_extra.py --from ... --to ...`（补充 3 组）：
   - **DD-CARRIER**：核心主题词 × 具体载体类型（liposome/LNP/PLGA/chitosan/dendrimer/
     polymersome/MOF/介孔硅/细胞膜仿生/外泌体/白蛋白纳米粒/纳米晶/微球/乳剂）；
   - **GUT-ORAL**：肠道 × 口服/肠道递送策略（oral delivery、colon-specific、enteric、
     mucus、Peyer's patch、intestinal absorption/permeability、gut microbiota、bioavailability）
     × 递送载体词；
   - **DD-STRATEGY**：核心主题词 × 功能策略（targeting、controlled/sustained release、
     stimuli-responsive、gene delivery、siRNA/mRNA/CRISPR、theranostic、PEGylation）。
   ⚠️ `gdd_search.py` 会整体重写 raw/epmc_raw.json —— **必须先跑 gdd_search.py 再跑
   gdd_search_extra.py**（后者把 3 组合并进同一文件）。回顾模式按年分段跑（每年一次，断点续跑）。
   主题查询 503 失败：用 `gdd_refetch_topic.py --topic <名>` 单主题补抓合并，勿整库重跑覆盖。
3. 入库：首批 `gdd_build_db.py`；补检/后续合并用 `gdd_merge_raw.py --topics <...>`
   （保留人工修正，**勿全量重建**——会丢掉已修正的 pubtypes 与 Web 补录）。
   ⚠️ 绝不向记录 dict 写入 set 等不可 JSON 序列化的辅助字段（曾导致数据库截断损坏）。
4. **补漏双保险**（每批必做，标准关键词查询有系统性漏检）：
   WebSearch 核对目标期刊当期目录（尤其 J Control Release / Adv Drug Deliv Rev /
   ACS Nano / Nano Today / Biomaterials 的当期与 ASAP 目录）＋ 已知 DOI 直查；漏检文章用
   `gdd_fetch_by_doi.py --dois ...` 以 `source: "Web"` 补入 DB。

### 第 2 步：期刊白名单 + 相关度筛选（优中选优）
1. `python tools/gdd_filter_journals.py --dir . --stage first|final`。白名单为
   **T1/T2 严格名单（2026-10-09 用户明确：只收第一、第二梯队，除此之外不需要检索）**：
   - **T1-第一梯队（综合/综述顶刊）**：Nature(主刊)、Science(主刊)、Nat Rev Drug Discov、
     Chem Rev、Chem Soc Rev、Nat Nanotechnol、Nat Mater、Nat Biomed Eng、Adv Mater、
     Angew Chem(Int Ed 各版)；
   - **T2-第二梯队（领域顶刊）**：J Control Release、Adv Drug Deliv Rev、ACS Nano、
     Nano Today、Biomaterials、Matter、Nat Commun、Sci Adv、Nano Lett、JACS。
   严格名单匹配（不做 Nature/Science 全家族前缀收录），伪刊拦截：Adv Mater 不含
   Interfaces/Reports、Chem Rev 不含 Acc 系、J Control Release 不含 J Control Release X、
   Biomaterials 不含 Biomaterials Science、Matter 不含同名词刊。
   被排除期刊按计数写 `03_Reports/exclusion_log.md`（含收录规则全文，可随时放宽/收紧重刷）。
   ⚠️ 白名单极严：Nat Chem Biol、Nat Biotechnol、Sci Transl Med、Adv Funct Mater、Small、
   Acta Biomater、Gut、Gastroenterology 等均不收——用户如需扩展某刊，告知后重刷即可。
2. **题名 + 摘要双重相关度审查（沿用 elm 流水线约定，勿只看题名）**：白名单保留后，
   对每条新命中的**题名＋在线摘要**（EPMC 有摘要字段，无摘要时才降级为仅题名并标注）
   逐条审查再定去留——题名常掩盖真实内容，仅凭题名易误杀漏检。摘要含以下维度即保留：
   ① 药物递送载体开发（新载体/新配方/新结构/载药与释药机制）；② 肠道靶向递送
   （gut/intestine/colon 靶向、口服递送、肠道屏障穿透、肠黏液/Peyer's patch/菌群互作）；
   ③ 生物医学应用（IBD/结肠癌/肠道感染/菌群调控/全身递送的肠道途径等治疗或诊断应用）。
   离题论文（无递送载体维度的纯临床/纯药理学研究、纯材料合成无递送应用、SPR 仅作商用
   仪器测量手段的分子互作研究、纯制剂工艺无载体新意）即使顶刊也剔除，逐条理由记 exclusion_log。
3. `python tools/gdd_relevance_filter.py --dir .` —— 应用剔除清单。清单存
   `<工作目录>/relevance_drops.json`（`{"drop": {doi: 理由}, "flag": {doi: 备注}}`）——
   每批审完新命中后追加，跨批累积。**drop 项在写入前必须经过摘要核实**（防止误杀漏检）；
   若发现误杀，从 drop 区移除并恢复入库。

### 第 3 步：DOI 全量补全（标准：0 缺失）
`python tools/gdd_fix_dois.py`，优先级链（每条规则均有真实教训）：
1. arXiv 记录 → `10.48550/arXiv.<id>`（标准 DOI，必有）。
2. CrossRef `query.bibliographic` 题名匹配：归一化词集 Jaccard ≥ 0.75 才采纳；429 时退避重试 8s/16s/24s。
3. PMC 页面 `<meta name="citation_doi">` 提取（题名被截断/预印本 DOI 错误时的权威来源）。
4. **剔除伪 DOI**：`.s001` 后缀（补充材料）、`10.2139/ssrn.*`（预印本，须换成正式期刊 DOI）。
5. CrossRef 命中时顺手校正 `journal`/`journal_abbrev`（API 期刊字段常错）。
DOI 是文章的必备标识，缺失说明检索策略有漏——优先修策略，修不到才保留英文原题供用户手动检索。

### 第 4 步：规范化命名 + BibTeX
1. 逐篇把英文题名译成中文，写入 `cn_titles.json`（键 = 题名前 25+ 字符词头）。
2. 中文译名可后补（回顾模式"全量清单优先"）：先用 `python tools/gdd_export_bib.py --prefix <年> --year <年>`
   产出按年 BibTeX（`GDD_<年>_library.bib`）+ `naming_manifest_<年>.csv`（中文名列占位"待译"）。
3. `python tools/gdd_build_outputs.py` →
   - 命名：`年月-期刊简写-论文中文名`（如 `2026-09-JControlRelease-结肠靶向壳聚糖微球的pH响应释药`）；
   - `02_BibTeX/GDD_<YYYY-MM>_library.bib`（Zotero 可直接导入：author/journal/year/doi/url，每月增量）；
   - `02_BibTeX/naming_manifest.csv`（含文献类型列：研究论文 / 综述·观点）；
   - `01_PDF/` 内 PDF 按规范化命名重命名。

### 第 5 步：PDF 管理
- 自动下载开放获取 PDF（bioRxiv/arXiv 直链可用；Elsevier/ACS/Nature 等出版商反爬，会失败，属正常）。
- `python tools/gdd_import_pdfs.py --downloads <用户Downloads目录> --since YYYY-MM-DD`（dry-run 报告）
  → 确认匹配无误后加 `--apply`：pypdf 提取首页 DOI/题名，三级匹配（DOI 精确 > 题名词重叠 > 文件名词重叠，阈值 0.6），
  **复制**（不是移动）到 `01_PDF/` 并按规范化命名，置 `pdf_manual=True`。
  ⚠️ 涉及个人目录只复制不移动，绝不删除用户 Downloads 里的原文件。

### 第 6 步：三态 Checklist（`03_Reports/手动下载Checklist.md`）
`python tools/gdd_rebuild_checklist.py`，规范：
- 三态：`[x]` 已获取｜`[ ]` 待下载（附 DOI 入口）｜`[×]` 高校图书馆未订阅无法下载（用户手动标记，**重建时必须保留**，含模糊匹配保留）；
- **研究论文（含预印本）与综述/观点分两大节**（用户明确要求"综述和研究分开"）；
- 排序：已获取优先 → 期刊优先级（T1 在前）→ 日期；每条含期刊/日期/类型/通讯作者(推定)/英文原题/下载入口。

### 第 7 步：报告
- **月度摘要报告**（`03_Reports/`）：每篇含通讯作者、摘要、结论、创新点、科学问题、批判性思考。
- **TOP3 精读报告**：按 影响因子 × 科学问题新颖性 选 3 篇，带读式详细报告（模板见 references/workflow.md）。
- 回顾模式：改为**每年一份年度综评**（代表性论文 + 演进脉络）+ **每年 TOP2-3 精读** + **跨 5 年发展时间线**。

### 第 8 步：GitHub 归档（默认 `DediCationMeng/GDD-References`，`--owner/--repo` 可改）
`python tools/gdd_upload_github.py --root <项目目录>`（token 用 `GITHUB_TOKEN` 环境变量或 token 文件参数）。
- **版权红线：出版商 PDF 与 `01_PDF/` 永不上传**（`.gitignore` 已排除 `01_PDF/`、`*.pdf`）；只上传元数据/BibTeX/报告/checklist/脚本。
- 走 api.github.com 的 Git Data API 单原子提交（blobs→tree→commit→ref）；空仓库先用 Contents API 引导初始提交；
  422 not-fast-forward 时提交带 `parents:[head_sha]`，必要时 force-PATCH。
- 网络事实：`github.com` 直连/代理常不通，但 `api.github.com` 可达 → 不要依赖 git push，用 REST 上传。
- 连接器写入权限：GitHub App token 默认 403（Contents:write 缺失）→ 用 fine-grained PAT
  （Repository access 仅 GDD-References；Permissions → Contents: Read and write）。**提醒用户用完即删**。
- 首次使用需在 GitHub 建空仓库 `GDD-References`（或用 `--repo` 指定已有仓库）。

### 第 9 步：收尾
- 若是定时自动化，用 `automation_update` 把本期确定的约定写回自动化 prompt（保持自包含）。
- 把新约定/教训追加到工作区记忆 `MEMORY.md`。

## 硬性红线（不可协商）
1. 出版商 PDF 永不上 GitHub / 永不外传。
2. 个人目录（Downloads/Desktop/Documents）只读+复制，绝不移动/删除。
3. DOI 必全量补全；补不到就如实保留英文原题，不编造 DOI。
4. checklist 用户标记（尤其 `[×]`）必须在重建时保留。
5. 综述与研究论文分开呈现。
6. 中文回答；数据库/脚本一律 UTF-8。

详细字段规范、报告模板、GitHub 排错手册见 `references/workflow.md`。
