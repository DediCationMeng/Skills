# gut-dd-literature-pipeline — 肠道靶向药物递送载体文献流水线 说明文档

> 文献「检索 → 处理 → 归档」全流程自动化 skill，聚焦**靶向肠道的药物递送载体**。
> 2026-10-09 由 `elm-literature-pipeline` 派生（脚本同构，前缀 `gdd_`）。

## 一、功能描述

### 1.1 定位与目标领域

面向**药物递送载体（drug delivery carriers）**领域，聚焦**靶向肠道（gut / intestine / colon）**
的载体开发及其生物医学应用。检索关键词四大块（2026-10-09 用户指定）：

1. **核心主题词**：drug delivery / DDS、drug carrier / delivery vehicle、nanocarrier、
   nanomedicine、nanoformulation、pharmaceutical formulation；
2. **肠道词**：gut、intestin*、colon、colonic、colorectal、gastrointestin*、bowel、
   ileum/jejunum/duodenum/cecum/rectum、enteral、colon-specific/colon-targeted/gut-targeted；
3. **载体类型**：nanoparticle*/liposome*/LNP/polymeric NP/micelle*/dendrimer*/hydrogel*/
   exosome*/MOF/介孔硅/PLGA/壳聚糖等；
4. **应用与策略**：靶向/控释/刺激响应/基因递送/口服递送/肠道吸收/菌群/IBD/生物利用度等。

**目标期刊严格限定第一、第二梯队共 20 本**（白名单，除此之外一律不检索）：

- **T1 第一梯队（综合/综述顶刊）**：Nature(主刊)、Science(主刊)、Nat Rev Drug Discov、
  Chem Rev、Chem Soc Rev、Nat Nanotechnol、Nat Mater、Nat Biomed Eng、Adv Mater、Angew Chem(Int Ed)；
- **T2 第二梯队（领域顶刊）**：J Control Release、Adv Drug Deliv Rev、ACS Nano、Nano Today、
  Biomaterials、Matter、Nat Commun、Sci Adv、Nano Lett、JACS。

白名单外记录仍存档进 `literature_database_all.json` 并计数入 `exclusion_log.md`，随时可放宽重刷。

### 1.2 触发方式

触发词：药物递送文献检索、药物载体、给药系统、纳米药物、纳米载体、肠道靶向递送、
gut-targeted delivery、colon-specific、口服递送文献、文献追踪、月度文献整理、
回顾性检索过去 N 年文献、补齐领域核心文献、文献库、BibTeX、Zotero、手动下载 checklist、
上传 GitHub 文献库。

### 1.3 两种运行模式

| 模式 | 触发意图 | 时间窗 | 产出侧重 |
|---|---|---|---|
| **月度追踪** | "整理上个月的文献" / 定时自动化 | 上次运行至今（约 1 个月） | 全套 6 项交付 |
| **回顾补齐** | "彻底检索过去 5 年文献" / "补齐领域发展历程" | 用户指定（如近 5 年） | 按年分批 + 年度综评 + 每年 TOP 精读 + 跨年发展时间线 |

### 1.4 标准九步流程

1. **检索入库（6 组查询主题）**：`gdd_search.py`（标准 3 组：**DD-CORE** 载体开发宽检索、
   **GUT-DD** 肠道靶向递送载体开发（核心需求）、**GUT-BIO** 肠道递送载体的生物医学应用）
   → `gdd_search_extra.py`（补充 3 组：**DD-CARRIER** 具体载体类型、**GUT-ORAL** 口服/肠道递送
   策略、**DD-STRATEGY** 功能策略）→ `gdd_build_db.py` 建库，补检用 `gdd_merge_raw.py`；
   每批必做「补漏双保险」（WebSearch 核对 J Control Release / Adv Drug Deliv Rev / ACS Nano /
   Nano Today / Biomaterials 等当期与 ASAP 目录 ＋ `gdd_fetch_by_doi.py` DOI 直查）。
2. **期刊白名单 + 相关度筛选**：`gdd_filter_journals.py`（T1/T2 严格名单，含伪刊拦截：
   Adv Mater 不含 Interfaces/Reports、Chem Rev 不含 Acc 系、J Control Release 不含 J Control
   Release X、Biomaterials 不含 Biomaterials Science、Matter 不含同名词刊）→ **题名＋摘要双重
   审查**（保留维度：① 递送载体开发 ② 肠道靶向递送 ③ 生物医学应用）→ `gdd_relevance_filter.py`。
3. **DOI 全量补全（标准：0 缺失）**：`gdd_fix_dois.py`（五级优先级链，同系列通用规范）。
4. **规范化命名 + BibTeX**：命名格式 `年月-期刊简写-论文中文名`；`gdd_export_bib.py` /
   `gdd_build_outputs.py` 产出 `GDD_<YYYY-MM>_library.bib` + `naming_manifest.csv`。
5. **PDF 管理**：`gdd_import_pdfs.py`（dry-run → `--apply`，只复制不移动，三级匹配阈值 0.6）。
6. **三态 Checklist**：`gdd_rebuild_checklist.py`，`[x]` 已获取 ｜ `[ ]` 待下载 ｜ `[×]` 未订阅
   （重建必须保留）；综述与研究分开；排序为已获取优先 → 期刊优先级（T1 在前）→ 日期。
7. **报告**：月度摘要报告 + TOP3 精读报告；回顾模式为年度综评 + 每年 TOP2-3 精读 + 发展时间线。
8. **GitHub 归档**：`gdd_upload_github.py` 走 Git Data API 单原子提交，归档至
   `DediCationMeng/GDD-References`（首次使用需创建该空仓库，`--owner/--repo` 可改）；
   **出版商 PDF 与 01_PDF/ 永不上传**。
9. **收尾**：约定写回自动化 prompt；新约定/教训追加工作区记忆。

### 1.5 交付物（每期 6 项）

规范化命名的 PDF 库（`01_PDF/`）· BibTeX 库 + 命名清单（`02_BibTeX/`）· 月度摘要报告 ·
TOP 精读报告 · 三态手动下载 Checklist（`03_Reports/`）· GitHub 归档提交。

### 1.6 脚本清单（scripts/，前缀 `gdd_`）

| 脚本 | 功能 |
|---|---|
| `gdd_search.py` | 标准 3 组主题检索（Europe PMC + arXiv）→ `raw/epmc_raw.json`、`raw/arxiv_raw.json` |
| `gdd_search_extra.py` | 补充 3 组主题检索，合并进同一 raw 文件（**必须在 gdd_search.py 之后跑**） |
| `gdd_refetch_topic.py` | 单主题补抓（503 失败后定点重试） |
| `gdd_build_db.py` | 首批建库 `literature_database.json`（唯一数据源） |
| `gdd_merge_raw.py` | 补检/后续增量合并（保留人工修正，勿全量重建） |
| `gdd_filter_journals.py` | 期刊白名单筛选（T1/T2 严格名单 + 伪刊拦截） |
| `gdd_relevance_filter.py` | 应用相关度剔除清单 `relevance_drops.json` |
| `gdd_fix_dois.py` | DOI 全量补全（五级优先级链 + 伪 DOI 拦截） |
| `gdd_fetch_by_doi.py` | 已知 DOI 直查补录（`source: "Web"`） |
| `gdd_export_bib.py` | 按年/月导出 BibTeX（`GDD_<年>_library.bib`）+ 命名清单 |
| `gdd_build_outputs.py` | 规范化命名 + 增量 BibTeX + `naming_manifest.csv` + PDF 重命名 |
| `gdd_import_pdfs.py` | Downloads PDF 导入（dry-run → `--apply`，只复制不移动） |
| `gdd_rebuild_checklist.py` | 三态 Checklist 重建（模糊匹配保留用户标记） |
| `gdd_upload_github.py` | GitHub REST 归档（Git Data API 单原子提交） |

## 二、功能边界

### 2.1 做什么（In Scope）

- 药物递送载体领域**元数据**的检索、入库、去重、合并（保留人工修正）；
- T1/T2 20 本严格白名单筛选 + 题名/摘要双重相关度审查（三维度：载体开发/肠道靶向/生物医学应用）；
- DOI 全量补全（0 缺失标准）与期刊字段校正；
- 中文译名规范化命名、Zotero 可导入 BibTeX、命名清单；
- 开放获取 PDF 自动下载与本地 PDF 归集（只复制）；
- 三态手动下载 Checklist、月度摘要报告、TOP 精读报告、回顾模式年度综评/发展时间线；
- 元数据/报告/脚本的 GitHub REST 归档。

### 2.2 不做什么（Out of Scope）

- **不做**出版商付费墙 PDF 的获取、破解或传播；
- **不做**白名单外期刊的收录（Nat Chem Biol、Nat Biotechnol、Sci Transl Med、Adv Funct Mater、
  Small、Acta Biomater、Gut、Gastroenterology 等均不收；用户如需扩展某刊，告知后重刷即可）；
- **不做**无递送载体维度的纯临床/纯药理研究、纯材料合成无递送应用、SPR 仅作商用仪器测量
  手段的分子互作研究、纯制剂工艺无载体新意的收录（即使顶刊也剔除，理由记 exclusion_log）；
- **不做**跨领域检索（ELM / 等离激元方向走各自 skill）；
- **不做** Zotero 云同步、全文翻译；
- **不覆盖** `elm-literature-pipeline` 本体或其他 skill 的数据库/工作目录；
- **不修改/不移动/不删除**用户个人目录中的任何原文件。

### 2.3 硬性红线（不可协商）

1. 出版商 PDF 永不上 GitHub / 永不外传；
2. 个人目录只读 + 复制，绝不移动/删除；
3. DOI 必全量补全，补不到如实保留英文原题，**不编造 DOI**；
4. Checklist 用户标记（尤其 `[×]`）重建时必须保留；
5. 综述与研究论文分开呈现；
6. 中文回答；数据库/脚本一律 UTF-8。

### 2.4 操作安全约定

- 个人目录相关操作先 dry-run 报告、确认后再 `--apply`，且只复制；
- 数据库记录 dict **绝不写入 set 等不可 JSON 序列化字段**；
- 补检合并用 `gdd_merge_raw.py`，勿全量重建；执行顺序必须 `gdd_search.py` → `gdd_search_extra.py`；
- `drop` 项写入 `relevance_drops.json` 前必须经摘要核实（防误杀漏检），误杀可移出恢复入库。

## 三、运行环境与依赖

- Python 3（优先管理版运行时）；依赖 `requests`、`pypdf`；
- 网络：Europe PMC / arXiv / CrossRef API；GitHub 上传走 `api.github.com`（不依赖 git push）；
- GitHub token：`GITHUB_TOKEN` 环境变量或 token 文件参数；fine-grained PAT（Contents: Read and
  write，Repository access 仅 GDD-References），**用完即删**；
- 脚本以自身目录为 BASE，拷贝至工作目录 `tools/` 下执行，或传 `--dir` 指定工作目录。

## 四、目录结构

Skill 本体：

```
gut-dd-literature-pipeline/
├── README.md            # 本文档
├── SKILL.md             # Skill 入口（完整流程与硬性红线）
├── references/workflow.md  # 字段规范、报告模板、GitHub 排错手册、白名单全文（§8）
└── scripts/gdd_*.py     # 14 个流程脚本
```

运行工作目录（每次运行建立）：

```
GDD-Literature-<YYYY-MM>/          # 回顾模式：GDD-Retrospective-<起>-<止>/
├── 01_PDF/        # PDF 库（GitHub 永不上传）
├── 02_BibTeX/     # GDD_<YYYY-MM>_library.bib + naming_manifest.csv
├── 03_Reports/    # 摘要报告、精读报告、手动下载Checklist.md、exclusion_log.md
├── raw/           # epmc_raw.json / arxiv_raw.json
├── cn_titles.json
├── literature_database.json
└── tools/         # scripts 拷贝（保证可复跑）
```

## 五、与同系列 skill 的关系

- 由 `elm-literature-pipeline` 于 2026-10-09 派生（脚本同构，仅关键词/白名单/归档仓库不同）；
- ELM / 等离激元方向的查询与白名单保留在各自 skill，可随时回切；
- **维护约定：改造文献流水线时一律新建派生 skill，不覆盖 `elm-literature-pipeline` 本体**。
