---
name: plasmonics-literature-pipeline
description: 等离激元纳米材料（plasmonics/LSPR/SPR/金银纳米粒子）领域文献检索-处理-归档全流程，重点方向：新型等离激元纳米材料开发、生物医学应用（SERS/光热/传感诊疗）。触发词：等离激元文献检索、plasmonics、LSPR、SERS、金/银纳米材料文献、文献追踪、月度文献整理、回顾性检索过去N年文献、补齐领域核心文献、文献库、BibTeX、Zotero、手动下载checklist、上传GitHub文献库。覆盖 Europe PMC/arXiv/CrossRef 检索、DOI补全、规范化命名、PDF管理、三态checklist、月度摘要报告、TOP精读报告、GitHub归档。
---

# 等离激元纳米材料 文献流水线（检索 → 处理 → 归档）

领域：等离激元纳米材料（plasmonic nanomaterials）。关键词两大类——
核心概念（plasmonics、LSPR、SPR/SPP、gap plasmon）× 材料形貌（Au/Ag 纳米粒子、
nanorods/nanostars/nanocubes、core-shell、nanogap）。两个重点方向：
① 新型等离激元纳米材料的开发（合成/形貌调控/新结构/机理）；
② 生物医学中有应用的等离激元纳米材料（SERS 传感与成像、光热/光动力治疗、LSPR 诊断等）。
目标期刊按梯队 A-H 收录（见 references/workflow.md §8）：Nature/Science 家族及子刊
（Nat Photonics/Nat Nanotechnol/Nat Mater）、JACS、Angewandte、Adv Mater、ACS Nano、
Nano Lett 等顶刊次顶刊，及等离激元专业刊（J Phys Chem C、Plasmonics、Nanophotonics 等）、
bioRxiv、arXiv。
⚠️ 本 skill 由 `elm-literature-pipeline`（ELM 领域）派生为独立副本（2026-10-09），
查询与白名单为等离激元方向专用；原 ELM skill 保持原样，两者互不影响。

本 skill 有两种运行模式，由用户意图决定：

| 模式 | 触发 | 时间窗 | 产出侧重 |
|---|---|---|---|
| **月度追踪** | "整理上个月的文献" / 定时自动化 | 上次运行至今（约 1 个月） | 全套 6 项交付 |
| **回顾补齐** | "彻底检索过去 5 年文献" / "补齐领域发展历程" | 用户指定（如近 5 年） | 按年分批 + 年度综评 + 每年 TOP 精读 + 发展时间线 |

## 工作目录约定

每次运行建立/使用一个输出目录 `PLASMON-Literature-<YYYY-MM>/`（回顾模式用 `PLASMON-Retrospective-<起>-<止>/`）：

```
PLASMON-Literature-2026-09/
├── 01_PDF/            # PDF 存放（GitHub 永不上传，版权红线）
├── 02_BibTeX/         # PLASMON_<YYYY-MM>_library.bib + naming_manifest.csv
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
1. `python tools/plm_search.py --from YYYY-MM-DD --to YYYY-MM-DD` → `raw/epmc_raw.json`、`raw/arxiv_raw.json`。
   标准 3 组（脚本内置，2026-10-09 起为等离激元关键词）：
   - **PLASMON-CORE**：核心概念（plasmonic* / localized surface plasmon / surface plasmon
     resonance / surface plasmon polariton* / gap plasmon* / LSPR）× 纳米材料总称
     （nanoparticle* / nanostructure* / nanomaterial* / colloid* / nanocrystal*）
     —— 新型等离激元纳米材料开发的宽检索；
   - **PLASMON-SHAPE**：核心概念 × 材料形貌（gold/silver/Au/Ag nanoparticle*、nanorod*、
     nanostar*、nanocube*、nanoshell*、core-shell、nanogap）—— 形貌可控合成与新结构；
   - **PLASMON-BIO**：核心概念/金银纳米材料/SERS × 生物医学应用词（biomedic*、theranostic*、
     therapeut*、diagnos*、biosensor*、bioimaging、photothermal、cancer、tumor、
     drug deliver*、antibacterial、wound、implant*）。
2. `python tools/plm_search_extra.py --from ... --to ...`（补充 3 组，2026-10-09 起为等离激元方向）：
   - **EXOTIC-SHAPES**：核心概念 × 扩展形貌（nanocage/nanoframe/nanotriangle/nanoprism/
     nanodendrite/nanourchin/nanowire/nanoantenna/yolk-shell/nanoparticle-on-mirror/
     bimetallic/alloy*/nanocomposite*）—— 新型/异质等离激元纳米结构；
   - **BIO-APP**：生物医学应用扩展（photothermal therap*、photodynamic、photoacoustic、
     SERS imaging/tag*、cell imaging、immunoassay、drug deliver*、antimicrobial/antibacterial、
     wound healing、neuromodulat*、theranostic*）；
   - **BIO-SENSING**：LSPR/SPR 生物传感与诊断（biosensor*、sens*、detect*、diagnos*、
     assay、refractive index、imaging）。
   ⚠️ `plm_search.py` 会整体重写 raw/epmc_raw.json —— **必须先跑 plm_search.py 再跑
   plm_search_extra.py**（后者把 3 组合并进同一文件）。回顾模式按年分段跑（每年一次，断点续跑）。
   主题查询 503 失败：用 `plm_refetch_topic.py --topic <名>` 单主题补抓合并，勿整库重跑覆盖。
3. 入库：首批 `plm_build_db.py`；补检/后续合并用 `plm_merge_raw.py --topics <...>`
   （保留人工修正，**勿全量重建**——会丢掉已修正的 pubtypes 与 Web 补录）。
   ⚠️ 绝不向记录 dict 写入 set 等不可 JSON 序列化的辅助字段（曾导致数据库截断损坏）。
4. **补漏双保险**（每批必做，标准关键词查询有系统性漏检——曾漏掉题名含 "bioprinting" 的 NBME 论文）：
   WebSearch 核对顶级期刊当期目录 ＋ 已知 DOI 直查；漏检文章用
   `plm_fetch_by_doi.py --dois ...` 以 `source: "Web"` 补入 DB。

### 第 2 步：期刊白名单 + 相关度筛选（优中选优）
1. `python tools/plm_filter_journals.py --dir . --stage first|final`。白名单（A-H 组，2026-10-09 按期刊梯队微调）：
   - **A-Nature 家族**：题名以 nature 开头全收（Nat Commun、Nat Photonics、Nat Nanotechnol、
     Nat Mater、Nat Rev X、Nat Chem Biol 等）；npj 系列不收；
   - **B-Science 家族**：Science、Sci Adv、Sci Robot、Sci Transl Med、Sci Immunol（Science Signaling 不收）；
   - **C-Cell 家族**：Cell、Cell Stem Cell、Cell Metab、Cell Host Microbe、Cancer Cell、Immunity、
     Neuron、Mol Cell、Chem、Joule、Matter、Cell Rep Med（Cell Reports/iScience/Current Biology 等不收）；
     —— 生物医学应用方向可能命中 Chem/Matter/Joule，保留；
   - **D-用户点名**：Adv Mater、Adv Funct Mater、Adv Sci、JACS、Angew Chem(Int Ed)、Biomaterials；
   - **E-学科顶刊（第二梯队）**：ACS Nano、Nano Lett、Nano Today、Light Sci Appl、Phys Rev Lett、
     Chem Rev、Chem Soc Rev、Acc Chem Res、Bioact Mater、Adv Drug Deliv Rev、Trends Microbiol、
     Prog Mater Sci、Signal Transduct Target Ther 等；
   - **F-用户补充（2026-10-09）**：ACS Synthetic Biology、Materials Today Bio、Advanced Healthcare Materials；
   - **G-次顶刊（第三梯队）**：Small、Chem Mater、Nanoscale、J Phys Chem Lett、ACS Photonics、
     Adv Opt Mater、ACS Appl Mater Interfaces、Nano Energy、Appl Catal B、Biosens Bioelectron、Theranostics；
   - **H-专业刊（第四梯队等离激元专业刊）**：J Phys Chem C、Plasmonics、Nanophotonics、Opt Express、
     ACS Appl Nano Mater、J Nanopart Res、Opt Mater Express（收录偏宽，收紧时可移除该组重刷）。
   被排除期刊按计数写 `03_Reports/exclusion_log.md`（含收录规则全文，可随时放宽/收紧重刷）。
2. **题名 + 摘要双重相关度审查（用户 2026-10-09 明确要求，勿只看题名）**：白名单保留后，
   对每条新命中的**题名＋在线摘要**（EPMC 有摘要字段，无摘要时才降级为仅题名并标注）
   逐条审查再定去留——题名常掩盖真实内容，仅凭题名易误杀漏检。摘要含以下维度即保留：
   ① 新型等离激元纳米材料（新结构/形貌可控合成/新性质）；② LSPR/SPR/gap plasmon 机理
   且与纳米材料直接相关；③ 生物医学应用（SERS 传感与成像、光热/光动力治疗、LSPR 诊断、
   药物递送、抗菌/创伤、theranostic）。
   离题论文（无纳米材料维度的纯等离激元理论/光子器件、SPR 仅作商用仪器测量手段的分子互作
   研究、纯金属薄膜/光栅传感、纯临床或纯生物学研究）即使顶刊也剔除，逐条理由记 exclusion_log。
3. `python tools/plm_relevance_filter.py --dir .` —— 应用剔除清单。清单存
   `<工作目录>/relevance_drops.json`（`{"drop": {doi: 理由}, "flag": {doi: 备注}}`）——
   每批审完新命中后追加，跨批累积。**drop 项在写入前必须经过摘要核实**（防止误杀漏检）；
   若发现误杀，从 drop 区移除并恢复入库。

### 第 3 步：DOI 全量补全（标准：0 缺失）
`python tools/plm_fix_dois.py`，优先级链（每条规则均有真实教训）：
1. arXiv 记录 → `10.48550/arXiv.<id>`（标准 DOI，必有）。
2. CrossRef `query.bibliographic` 题名匹配：归一化词集 Jaccard ≥ 0.75 才采纳；429 时退避重试 8s/16s/24s。
3. PMC 页面 `<meta name="citation_doi">` 提取（题名被截断/预印本 DOI 错误时的权威来源）。
4. **剔除伪 DOI**：`.s001` 后缀（补充材料）、`10.2139/ssrn.*`（预印本，须换成正式期刊 DOI）。
5. CrossRef 命中时顺手校正 `journal`/`journal_abbrev`（API 期刊字段常错）。
DOI 是文章的必备标识，缺失说明检索策略有漏——优先修策略，修不到才保留英文原题供用户手动检索。

### 第 4 步：规范化命名 + BibTeX
1. 逐篇把英文题名译成中文，写入 `cn_titles.json`（键 = 题名前 25+ 字符词头）。
2. 中文译名可后补（回顾模式"全量清单优先"）：先用 `python tools/plm_export_bib.py --prefix <年> --year <年>`
   产出按年 BibTeX（`PLASMON_<年>_library.bib`）+ `naming_manifest_<年>.csv`（中文名列占位"待译"）。
3. `python tools/plm_build_outputs.py` →
   - 命名：`年月-期刊简写-论文中文名`（如 `2026-09-NatMicrobiol-编码前噬菌体的工程菌实现预防性裂解噬菌体疗法`）；
   - `02_BibTeX/PLASMON_<YYYY-MM>_library.bib`（Zotero 可直接导入：author/journal/year/doi/url，每月增量）；
   - `02_BibTeX/naming_manifest.csv`（含文献类型列：研究论文 / 综述·观点）；
   - `01_PDF/` 内 PDF 按规范化命名重命名。

### 第 5 步：PDF 管理
- 自动下载开放获取 PDF（bioRxiv/arXiv 直链可用；Elsevier/ACS/Nature 等出版商反爬，会失败，属正常）。
- `python tools/plm_import_pdfs.py --downloads <用户Downloads目录> --since YYYY-MM-DD`（dry-run 报告）
  → 确认匹配无误后加 `--apply`：pypdf 提取首页 DOI/题名，三级匹配（DOI 精确 > 题名词重叠 > 文件名词重叠，阈值 0.6），
  **复制**（不是移动）到 `01_PDF/` 并按规范化命名，置 `pdf_manual=True`。
  ⚠️ 涉及个人目录只复制不移动，绝不删除用户 Downloads 里的原文件。

### 第 6 步：三态 Checklist（`03_Reports/手动下载Checklist.md`）
`python tools/plm_rebuild_checklist.py`，规范：
- 三态（三个符号互不重复，2026-10-10 用户修正）：`[√]` 已获取（勾选头部方框）｜`[ ]` 待下载（附 DOI 入口）｜
  `[x]` 高校图书馆未订阅无法下载（勾选条目下「无法下载」方框，**重建时必须保留**，含模糊匹配保留）；
- **每条目两个可点选方框**（修 bug：单一方框只能表达"勾选"一种态，无法点选标记 `[x]`）：
  头部方框 `- [√] **name**` 勾选 = 已获取；子方框 `- [x] 无法下载（...）` 勾选 = 未订阅态。
  语义以**勾选了哪个方框**为准（不同编辑器勾选符号可能不同），重建时规范回标准三态符号；
- **研究论文（含预印本）与综述/观点分两大节**（用户明确要求"综述和研究分开"）；
- 排序：已获取优先 → 期刊优先级 → 日期；每条含期刊/日期/类型/通讯作者(推定)/英文原题/下载入口；
- **每条目只有两个勾选框**（头部「已获取」＋「无法下载」）；期刊/英文原标题/下载入口/建议渠道等
  信息行一律**缩进纯文本**（不加 `- ` 列表标记、不加勾选框），否则会被任务列表编辑器渲染成可勾选项
  （用户 2026-10-10 明确要求"信息行不要打上标记"）。

### 第 7 步：报告
- **月度摘要报告**（`03_Reports/`）：每篇含通讯作者、摘要、结论、创新点、科学问题、批判性思考。
- **TOP3 精读报告**：按 影响因子 × 科学问题新颖性 选 3 篇，带读式详细报告（模板见 references/workflow.md）。
- 回顾模式：改为**每年一份年度综评**（代表性论文 + 演进脉络）+ **每年 TOP2-3 精读** + **跨 5 年发展时间线**。

### 第 8 步：GitHub 归档（`DediCationMeng/Plasmon-References`）
`python tools/plm_upload_github.py --root <项目目录>`（token 用 `GITHUB_TOKEN` 环境变量或 token 文件参数）。
- **版权红线：出版商 PDF 与 `01_PDF/` 永不上传**（`.gitignore` 已排除 `01_PDF/`、`*.pdf`）；只上传元数据/BibTeX/报告/checklist/脚本。
- 走 api.github.com 的 Git Data API 单原子提交（blobs→tree→commit→ref）；空仓库先用 Contents API 引导初始提交；
  422 not-fast-forward 时提交带 `parents:[head_sha]`，必要时 force-PATCH。
- 网络事实：`github.com` 直连/代理常不通，但 `api.github.com` 可达 → 不要依赖 git push，用 REST 上传。
- 连接器写入权限：GitHub App token 默认 403（Contents:write 缺失）→ 用 fine-grained PAT
  （Repository access 仅 Plasmon-References；Permissions → Contents: Read and write）。**提醒用户用完即删**。

### 第 9 步：收尾
- 若是定时自动化，用 `automation_update` 把本期确定的约定写回自动化 prompt（保持自包含）。
- 把新约定/教训追加到工作区记忆 `MEMORY.md`。

## 硬性红线（不可协商）
1. 出版商 PDF 永不上 GitHub / 永不外传。
2. 个人目录（Downloads/Desktop/Documents）只读+复制，绝不移动/删除。
3. DOI 必全量补全；补不到就如实保留英文原题，不编造 DOI。
4. checklist 用户标记（尤其 `[x]` 未订阅态）必须在重建时保留。
5. 综述与研究论文分开呈现。
6. 中文回答；数据库/脚本一律 UTF-8。

详细字段规范、报告模板、GitHub 排错手册见 `references/workflow.md`。
