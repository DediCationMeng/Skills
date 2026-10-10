# elm-literature-pipeline — ELM 文献流水线 说明文档

> 文献「检索 → 处理 → 归档」全流程自动化 skill。本系列（文献流水线家族）的**基准母本**，
> `gut-dd-` / `plasmonics-` 两个派生 skill 均由此派生。

## 一、功能描述

### 1.1 定位与目标领域

面向**工程活体材料（Engineered Living Materials, ELMs）**及其紧密相关领域的文献情报工作，覆盖：

- 工程活体材料（ELMs）、活体生物界面；
- 3D 生物打印（bioprinting / bioink）；
- 微生物活药（live biotherapeutics, LBP）、工程化益生菌；
- 扩展方向：丝状真菌/菌丝材料（FUNGAL）、工程化酵母（YEAST）、活体材料形态（LIVINGFORMS）。

目标期刊：Nature/Science/Cell 及子刊、Wiley、Elsevier、生物材料期刊、bioRxiv、arXiv。

### 1.2 触发方式

触发词：ELM 文献检索、文献追踪、月度文献整理、回顾性检索过去 N 年文献、补齐领域核心文献、
文献库、BibTeX、Zotero、手动下载 checklist、上传 GitHub 文献库。

### 1.3 两种运行模式

| 模式 | 触发意图 | 时间窗 | 产出侧重 |
|---|---|---|---|
| **月度追踪** | "整理上个月的文献" / 定时自动化 | 上次运行至今（约 1 个月） | 全套 6 项交付 |
| **回顾补齐** | "彻底检索过去 5 年文献" / "补齐领域发展历程" | 用户指定（如近 5 年） | 按年分批 + 年度综评 + 每年 TOP 精读 + 跨年发展时间线 |

### 1.4 标准九步流程

1. **检索入库（7 组查询主题）**：`elm_search.py`（标准 4 组：ELM / Bioprinting / LBP / Probiotics）
   → `elm_search_extra.py`（补充 3 组：FUNGAL / YEAST / LIVINGFORMS）→ `elm_build_db.py` 建库，
   补检用 `elm_merge_raw.py` 增量合并；每批必做「补漏双保险」（WebSearch 核对顶级期刊当期目录
   ＋ `elm_fetch_by_doi.py` 已知 DOI 直查补录）。
2. **期刊白名单 + 相关度筛选**：`elm_filter_journals.py`（白名单 A-F 组）→ **题名＋摘要双重
   人工级审查**（勿只看题名）→ `elm_relevance_filter.py` 应用剔除清单（`relevance_drops.json` 跨批累积）。
3. **DOI 全量补全（标准：0 缺失）**：`elm_fix_dois.py`，五级优先级链（arXiv 标准 DOI → CrossRef
   题名 Jaccard ≥ 0.75 → PMC citation_doi → 剔除伪 DOI → 顺手校正期刊字段）。
4. **规范化命名 + BibTeX**：英文题名逐篇译中文入 `cn_titles.json`；命名格式
   `年月-期刊简写-论文中文名`；`elm_export_bib.py` / `elm_build_outputs.py` 产出 Zotero 可导入的
   `.bib` 与 `naming_manifest.csv`。
5. **PDF 管理**：开放获取 PDF 自动下载；`elm_import_pdfs.py` 从用户 Downloads **复制**（不移动）
   并按 pypdf 三级匹配（DOI 精确 > 题名词重叠 > 文件名词重叠，阈值 0.6）规范化命名。
6. **三态 Checklist**：`elm_rebuild_checklist.py` 重建 `手动下载Checklist.md`，
   `[x]` 已获取 ｜ `[ ]` 待下载（附 DOI 入口）｜ `[×]` 高校图书馆未订阅（用户手动标记，重建必须保留）；
   研究论文与综述/观点**分两大节**。
7. **报告**：月度摘要报告（每篇含通讯作者/摘要/结论/创新点/科学问题/批判性思考）+ TOP3 精读报告
   （按影响因子 × 科学问题新颖性遴选）；回顾模式为年度综评 + 每年 TOP2-3 精读 + 发展时间线。
8. **GitHub 归档**：`elm_upload_github.py` 走 api.github.com 的 Git Data API 单原子提交，
   归档至 `DediCationMeng/ELM-References`；**出版商 PDF 与 01_PDF/ 永不上传**。
9. **收尾**：约定写回自动化 prompt；新约定/教训追加工作区记忆。

### 1.5 交付物（每期 6 项）

规范化命名的 PDF 库（`01_PDF/`）· BibTeX 库 + 命名清单（`02_BibTeX/`）· 月度摘要报告 ·
TOP 精读报告 · 三态手动下载 Checklist（`03_Reports/`）· GitHub 归档提交（元数据/BibTeX/报告/脚本）。

### 1.6 脚本清单（scripts/，前缀 `elm_`）

| 脚本 | 功能 |
|---|---|
| `elm_search.py` | 标准 4 组主题检索（Europe PMC + arXiv）→ `raw/epmc_raw.json`、`raw/arxiv_raw.json` |
| `elm_search_extra.py` | 补充 3 组主题检索，合并进同一 raw 文件（**必须在 elm_search.py 之后跑**） |
| `elm_refetch_topic.py` | 单主题补抓（503 失败后定点重试，勿整库重跑覆盖） |
| `elm_build_db.py` | 首批建库 `literature_database.json`（唯一数据源） |
| `elm_merge_raw.py` | 补检/后续增量合并（保留人工修正，勿全量重建） |
| `elm_filter_journals.py` | 期刊白名单筛选（`--stage first\|final`），排除计数写 `exclusion_log.md` |
| `elm_relevance_filter.py` | 应用相关度剔除清单 `relevance_drops.json` |
| `elm_fix_dois.py` | DOI 全量补全（五级优先级链 + 伪 DOI 拦截） |
| `elm_fetch_by_doi.py` | 已知 DOI 直查补录（`source: "Web"`，补漏双保险） |
| `elm_export_bib.py` | 按年/月导出 BibTeX（`ELM_<年>_library.bib`）+ 命名清单 |
| `elm_build_outputs.py` | 规范化命名 + 增量 BibTeX + `naming_manifest.csv` + PDF 重命名 |
| `elm_import_pdfs.py` | Downloads PDF 导入（dry-run → `--apply`，只复制不移动） |
| `elm_rebuild_checklist.py` | 三态 Checklist 重建（模糊匹配保留用户标记） |
| `elm_upload_github.py` | GitHub REST 归档（Git Data API 单原子提交，`GITHUB_TOKEN` 环境变量） |

## 二、功能边界

### 2.1 做什么（In Scope）

- 文献**元数据**的检索、入库、去重、合并与人工修正保留；
- 期刊白名单筛选 + 题名/摘要双重相关度审查；
- DOI 全量补全与期刊字段校正；
- 英文题名→中文译名的规范化命名体系（`年月-期刊简写-论文中文名`）；
- Zotero 可导入 BibTeX 与命名清单产出；
- 开放获取 PDF 自动下载、本地已下载 PDF 的归集整理（只复制）；
- 三态手动下载 Checklist 生成与维护；
- 月度摘要报告、TOP 精读报告、回顾模式年度综评与发展时间线；
- 元数据/报告/脚本的 GitHub 归档（REST API）。

### 2.2 不做什么（Out of Scope）

- **不做**出版商付费墙 PDF 的获取、破解或传播（仅登记 DOI 供用户经高校图书馆合法获取）；
- **不做** Zotero 云同步（只产出可导入的 `.bib`，导入动作由用户完成）；
- **不做**跨领域检索——查询关键词与白名单为 ELM 专属，其他领域走对应派生 skill；
- **不做**全文翻译、全文逐句精读（精读报告为带读式要点报告）；
- **不覆盖**其他 skill 的数据库或工作目录；不对 `elm_` 以外的脚本改名复用；
- **不修改/不移动/不删除**用户个人目录（Downloads/Desktop/Documents）中的任何原文件。

### 2.3 硬性红线（不可协商）

1. 出版商 PDF 永不上 GitHub / 永不外传；
2. 个人目录只读 + 复制，绝不移动/删除；
3. DOI 必全量补全，补不到如实保留英文原题，**不编造 DOI**；
4. Checklist 用户标记（尤其 `[×]`）重建时必须保留；
5. 综述与研究论文分开呈现；
6. 中文回答；数据库/脚本一律 UTF-8。

### 2.4 操作安全约定

- 个人目录相关操作一律先 dry-run 报告、确认后再 `--apply`，且只复制；
- 数据库记录 dict **绝不写入 set 等不可 JSON 序列化字段**（曾导致数据库截断损坏）；
- 补检合并用 `elm_merge_raw.py`，**勿全量重建**（会丢掉已修正的 pubtypes 与 Web 补录）；
- `elm_search.py` 整体重写 raw 文件，执行顺序必须是 `elm_search.py` → `elm_search_extra.py`。

## 三、运行环境与依赖

- Python 3（优先管理版运行时）；依赖 `requests`、`pypdf`（PDF 导入）；
- 网络：Europe PMC / arXiv / CrossRef API；GitHub 上传走 `api.github.com`（不依赖 git push）；
- GitHub token：`GITHUB_TOKEN` 环境变量或 token 文件参数；fine-grained PAT
  （Repository access 仅目标归档仓库；Permissions → Contents: Read and write），**用完即删**；
- 脚本以自身目录为 BASE，拷贝至工作目录 `tools/` 下执行，或传 `--dir` 指定工作目录。

## 四、目录结构

Skill 本体：

```
elm-literature-pipeline/
├── README.md            # 本文档
├── SKILL.md             # Skill 入口（完整流程与硬性红线）
├── references/workflow.md  # 字段规范、报告模板、GitHub 排错手册
└── scripts/elm_*.py     # 14 个流程脚本
```

运行工作目录（每次运行建立）：

```
ELM-Literature-<YYYY-MM>/          # 回顾模式：ELM-Retrospective-<起>-<止>/
├── 01_PDF/        # PDF 库（GitHub 永不上传）
├── 02_BibTeX/     # ELM_<YYYY-MM>_library.bib + naming_manifest.csv
├── 03_Reports/    # 摘要报告、精读报告、手动下载Checklist.md、exclusion_log.md
├── raw/           # epmc_raw.json / arxiv_raw.json
├── cn_titles.json
├── literature_database.json
└── tools/         # scripts 拷贝（保证可复跑）
```

## 五、与同系列 skill 的关系

- 本 skill 为**基准母本**；`gut-dd-literature-pipeline`、`plasmonics-literature-pipeline`
  于 2026-10-09 由此派生为独立副本（脚本同构，仅换前缀/关键词/白名单）。
- **维护约定：改造文献流水线时一律新建派生 skill，不覆盖本体**，三者互不影响、可随时回切。
