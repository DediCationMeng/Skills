# plasmonics-literature-pipeline — 等离激元纳米材料文献流水线 说明文档

> 文献「检索 → 处理 → 归档」全流程自动化 skill，聚焦**等离激元纳米材料**。
> 2026-10-09 由 `elm-literature-pipeline` 派生为独立副本（脚本同构，前缀 `plm_`）。

## 一、功能描述

### 1.1 定位与目标领域

面向**等离激元纳米材料（plasmonic nanomaterials）**领域。关键词两大类：
核心概念（plasmonics、LSPR、SPR/SPP、gap plasmon）× 材料形貌（Au/Ag 纳米粒子、
nanorods/nanostars/nanocubes、core-shell、nanogap）。两个重点方向：

1. **新型等离激元纳米材料的开发**：合成、形貌调控、新结构、新性质、机理；
2. **生物医学应用**：SERS 传感与成像、光热/光动力治疗、LSPR 诊断、药物递送、抗菌/创伤、theranostic。

目标期刊按梯队 A-H 收录：Nature/Science 家族及子刊（Nat Photonics/Nat Nanotechnol/Nat Mater）、
JACS、Angewandte、Adv Mater、ACS Nano、Nano Lett 等顶刊次顶刊（A-E），
次顶刊第三梯队（G：Small、Chem Mater、ACS Photonics、Biosens Bioelectron、Theranostics 等），
等离激元专业刊第四梯队（H：J Phys Chem C、Plasmonics、Nanophotonics、Opt Express 等，
收录偏宽，收紧时可移除该组重刷），及 bioRxiv、arXiv。

### 1.2 触发方式

触发词：等离激元文献检索、plasmonics、LSPR、SERS、金/银纳米材料文献、文献追踪、
月度文献整理、回顾性检索过去 N 年文献、补齐领域核心文献、文献库、BibTeX、Zotero、
手动下载 checklist、上传 GitHub 文献库。

### 1.3 两种运行模式

| 模式 | 触发意图 | 时间窗 | 产出侧重 |
|---|---|---|---|
| **月度追踪** | "整理上个月的文献" / 定时自动化 | 上次运行至今（约 1 个月） | 全套 6 项交付 |
| **回顾补齐** | "彻底检索过去 5 年文献" / "补齐领域发展历程" | 用户指定（如近 5 年） | 按年分批 + 年度综评 + 每年 TOP 精读 + 跨年发展时间线 |

### 1.4 标准九步流程

1. **检索入库（6 组查询主题）**：`plm_search.py`（标准 3 组：**PLASMON-CORE** 核心概念 ×
   纳米材料总称宽检索、**PLASMON-SHAPE** 核心概念 × 材料形貌、**PLASMON-BIO** 等离激元 ×
   生物医学应用）→ `plm_search_extra.py`（补充 3 组：**EXOTIC-SHAPES** 新型/异质结构
   （nanocage/nanoframe/nanoantenna/yolk-shell/nanoparticle-on-mirror 等）、**BIO-APP**
   生物医学应用扩展、**BIO-SENSING** LSPR/SPR 生物传感与诊断）→ `plm_build_db.py` 建库，
   补检用 `plm_merge_raw.py`；每批必做「补漏双保险」（WebSearch 核对顶级期刊当期目录
   ＋ `plm_fetch_by_doi.py` DOI 直查）。
2. **期刊白名单 + 相关度筛选**：`plm_filter_journals.py`（A-H 八组梯队）→ **题名＋摘要双重
   审查**（保留维度：① 新型等离激元纳米材料 ② LSPR/SPR/gap plasmon 机理且与纳米材料直接
   相关 ③ 生物医学应用）→ `plm_relevance_filter.py`。
3. **DOI 全量补全（标准：0 缺失）**：`plm_fix_dois.py`（五级优先级链，同系列通用规范）。
4. **规范化命名 + BibTeX**：命名格式 `年月-期刊简写-论文中文名`；`plm_export_bib.py` /
   `plm_build_outputs.py` 产出 `PLASMON_<YYYY-MM>_library.bib` + `naming_manifest.csv`。
5. **PDF 管理**：`plm_import_pdfs.py`（dry-run → `--apply`，只复制不移动，三级匹配阈值 0.6）。
6. **三态 Checklist（双勾选框设计，2026-10-10 用户修正）**：`plm_rebuild_checklist.py`，
   每条目两个可点选方框——头部方框 `[√]` 勾选 = 已获取；子方框「无法下载」`[x]` 勾选 =
   高校图书馆未订阅（**重建时必须保留**）；语义以勾选了哪个方框为准，重建时规范回标准三态符号；
   研究论文与综述/观点分两大节；**信息行一律缩进纯文本**（不加列表标记/勾选框）。
7. **报告**：月度摘要报告 + TOP3 精读报告；回顾模式为年度综评 + 每年 TOP2-3 精读 + 发展时间线。
8. **GitHub 归档**：`plm_upload_github.py` 走 Git Data API 单原子提交，归档至
   `DediCationMeng/Plasmon-References`；**出版商 PDF 与 01_PDF/ 永不上传**。
9. **收尾**：约定写回自动化 prompt；新约定/教训追加工作区记忆。

### 1.5 交付物（每期 6 项）

规范化命名的 PDF 库（`01_PDF/`）· BibTeX 库 + 命名清单（`02_BibTeX/`）· 月度摘要报告 ·
TOP 精读报告 · 三态手动下载 Checklist（`03_Reports/`）· GitHub 归档提交。

### 1.6 脚本清单（scripts/，前缀 `plm_`）

| 脚本 | 功能 |
|---|---|
| `plm_search.py` | 标准 3 组主题检索（Europe PMC + arXiv）→ `raw/epmc_raw.json`、`raw/arxiv_raw.json` |
| `plm_search_extra.py` | 补充 3 组主题检索，合并进同一 raw 文件（**必须在 plm_search.py 之后跑**） |
| `plm_refetch_topic.py` | 单主题补抓（503 失败后定点重试） |
| `plm_build_db.py` | 首批建库 `literature_database.json`（唯一数据源） |
| `plm_merge_raw.py` | 补检/后续增量合并（保留人工修正，勿全量重建） |
| `plm_filter_journals.py` | 期刊白名单筛选（A-H 八组梯队） |
| `plm_relevance_filter.py` | 应用相关度剔除清单 `relevance_drops.json` |
| `plm_fix_dois.py` | DOI 全量补全（五级优先级链 + 伪 DOI 拦截） |
| `plm_fetch_by_doi.py` | 已知 DOI 直查补录（`source: "Web"`） |
| `plm_export_bib.py` | 按年/月导出 BibTeX（`PLASMON_<年>_library.bib`）+ 命名清单 |
| `plm_build_outputs.py` | 规范化命名 + 增量 BibTeX + `naming_manifest.csv` + PDF 重命名 |
| `plm_import_pdfs.py` | Downloads PDF 导入（dry-run → `--apply`，只复制不移动） |
| `plm_rebuild_checklist.py` | 三态 Checklist 重建（双勾选框语义，模糊匹配保留用户标记） |
| `plm_upload_github.py` | GitHub REST 归档（Git Data API 单原子提交） |

## 二、功能边界

### 2.1 做什么（In Scope）

- 等离激元纳米材料领域**元数据**的检索、入库、去重、合并（保留人工修正）；
- A-H 八组梯队期刊白名单筛选 + 题名/摘要双重相关度审查（三维度：新材料/机理/生物医学应用）；
- DOI 全量补全（0 缺失标准）与期刊字段校正；
- 中文译名规范化命名、Zotero 可导入 BibTeX、命名清单；
- 开放获取 PDF 自动下载与本地 PDF 归集（只复制）；
- 三态手动下载 Checklist（双勾选框）、月度摘要报告、TOP 精读报告、回顾模式年度综评/发展时间线；
- 元数据/报告/脚本的 GitHub REST 归档。

### 2.2 不做什么（Out of Scope）

- **不做**出版商付费墙 PDF 的获取、破解或传播；
- **不做**无纳米材料维度的纯等离激元理论/光子器件研究、SPR 仅作商用仪器测量手段的分子互作
  研究、纯金属薄膜/光栅传感、纯临床或纯生物学研究的收录（即使顶刊也剔除，理由记 exclusion_log）；
- **不做**跨领域检索（ELM / 肠道递送方向走各自 skill）；
- **不做** Zotero 云同步、全文翻译；
- **不覆盖** `elm-literature-pipeline` 本体或其他 skill 的数据库/工作目录；
- **不修改/不移动/不删除**用户个人目录中的任何原文件。

### 2.3 硬性红线（不可协商）

1. 出版商 PDF 永不上 GitHub / 永不外传；
2. 个人目录只读 + 复制，绝不移动/删除；
3. DOI 必全量补全，补不到如实保留英文原题，**不编造 DOI**；
4. Checklist 用户标记（尤其 `[x]` 未订阅态）重建时必须保留；
5. 综述与研究论文分开呈现；
6. 中文回答；数据库/脚本一律 UTF-8。

### 2.4 操作安全约定

- 个人目录相关操作先 dry-run 报告、确认后再 `--apply`，且只复制；
- 数据库记录 dict **绝不写入 set 等不可 JSON 序列化字段**；
- 补检合并用 `plm_merge_raw.py`，勿全量重建；执行顺序必须 `plm_search.py` → `plm_search_extra.py`；
- Checklist 每条目**只有两个勾选框**（头部「已获取」＋「无法下载」），信息行缩进纯文本，
  否则会被任务列表编辑器渲染成可勾选项（用户 2026-10-10 明确要求）。

## 三、运行环境与依赖

- Python 3（优先管理版运行时）；依赖 `requests`、`pypdf`；
- 网络：Europe PMC / arXiv / CrossRef API；GitHub 上传走 `api.github.com`（不依赖 git push）；
- GitHub token：`GITHUB_TOKEN` 环境变量或 token 文件参数；fine-grained PAT（Contents: Read and
  write，Repository access 仅 Plasmon-References），**用完即删**；
- 脚本以自身目录为 BASE，拷贝至工作目录 `tools/` 下执行，或传 `--dir` 指定工作目录。

## 四、目录结构

Skill 本体：

```
plasmonics-literature-pipeline/
├── README.md            # 本文档
├── SKILL.md             # Skill 入口（完整流程与硬性红线）
├── references/workflow.md  # 字段规范、报告模板、GitHub 排错手册、白名单全文（§8）
└── scripts/plm_*.py     # 14 个流程脚本
```

运行工作目录（每次运行建立）：

```
PLASMON-Literature-<YYYY-MM>/          # 回顾模式：PLASMON-Retrospective-<起>-<止>/
├── 01_PDF/        # PDF 库（GitHub 永不上传）
├── 02_BibTeX/     # PLASMON_<YYYY-MM>_library.bib + naming_manifest.csv
├── 03_Reports/    # 摘要报告、精读报告、手动下载Checklist.md、exclusion_log.md
├── raw/           # epmc_raw.json / arxiv_raw.json
├── cn_titles.json
├── literature_database.json
└── tools/         # scripts 拷贝（保证可复跑）
```

## 五、与同系列 skill 的关系

- 由 `elm-literature-pipeline` 于 2026-10-09 派生为独立副本（查询与白名单为等离激元方向专用）；
- 原 ELM skill 保持原样，两者互不影响；
- **维护约定：改造文献流水线时一律新建派生 skill，不覆盖 `elm-literature-pipeline` 本体**。
