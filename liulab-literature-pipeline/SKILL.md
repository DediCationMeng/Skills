---
name: liulab-literature-pipeline
description: LiuLab课题组方向文献检索-处理-归档全流程。领域：消化道疾病/肠道微生物组/工程化细菌与益生菌/微生物-材料交叉/口服递药/微生物活药。触发词：文献检索、文献追踪、月度文献整理、回顾性检索过去N年文献、补齐领域核心文献、文献库、BibTeX、Zotero、手动下载checklist、上传GitHub文献库、调研XX方向、帮我看XX方向的文献、最近有没有新文章。覆盖 Europe PMC/arXiv/CrossRef 检索、DOI补全、规范化命名、PDF管理、三态checklist、月度摘要报告、TOP精读报告、GitHub归档。
---

# LiuLab 文献流水线（检索 → 处理 → 归档）

领域：**消化道疾病**（IBD、糖尿病、菌群失调、NAFLD、肝性脑病、肠道感染）、**肠道微生物组与肠-器官轴**、
**工程化细菌/益生菌**（活体生物药 LBP、工程菌疗法）、**微生物-材料交叉**（水凝胶、3D打印、纳米杂合体、
活体材料）、**口服递药**（黏膜递送、结肠靶向、益生菌递药、口服疫苗）、**可控活体治疗**（光/磁/声/pH响应）。
次关注：肿瘤免疫治疗（仅 Nature/Science/Cell 主刊或重大机制突破才收录）。

> **设计原则**：检索主题/关键词/相关度判定针对 LiuLab 课题组偏好定制；
> **工作流程、报告模板、期刊白名单、筛选方法论、硬性红线** 均沿用用户已验证的探索习惯。

## 课题组研究画像（相关度判定基准）

| 维度 | 描述 | 权重 |
|------|------|------|
| **核心平台** | 工程化细菌 / 益生菌 / LBP / 肠道微生物 | ★★★★★ |
| **主攻疾病** | 消化道疾病（IBD、糖尿病、NAFLD、肝性脑病、肠道感染、菌群失调） | ★★★★★ |
| **技术特色** | 微生物×材料交叉、可控化/精准化、活体治疗 | ★★★★☆ |
| **口服递药** | 黏膜递送、结肠靶向、pH响应、益生菌口服递药、口服疫苗 | ★★★★☆ |
| **肠-器官轴** | 肠-脑轴、肠-肝轴、菌群-宿主互作、微生物代谢物 | ★★★★☆ |
| **转化导向** | 临床前→临床转化、机制+应用并重、大动物模型 | ★★★★☆ |
| **次攻方向** | 肿瘤免疫（仅顶级，Nature/Science/Cell 主刊或重大突破） | ★★☆☆☆ |
| **降权/排除** | 纯合成生物学（不涉消化道）、纯肿瘤（非顶级）、纯理论计算 | — |

## 两种运行模式

| 模式 | 触发 | 时间窗 | 产出侧重 |
|---|---|---|---|
| **月度追踪** | "整理上个月的文献" / 定时自动化 | 上次运行至今（约 1 个月） | 全套交付 |
| **回顾补齐** | "彻底检索过去 5 年文献" / "补齐领域发展历程" | 用户指定（如近 5 年） | 按年分批 + 年度综评 + 每年 TOP 精读 + 发展时间线 |
| **回顾审阅** | "回顾审阅/回顾综、Review、系统综述、Meta、PRISMA、领域回眸、系统回顾、发展脉络、历史演进、过去五年/近十年/十年历程"（任一命中即可能是该任务） | 用户指定 | `03_Reports/Retrospective_Review/` 专项成果 |

**回顾审阅判别门**：仅「整域/整方向回眸 + 系统综述体裁」才按本专项执行；聚焦单方向或多方向拼盘一律走标准月度管线。
**Stage A 数据源**：按白名单期刊 × 主题词检索；成果统一放 `03_Reports/Retrospective_Review/`。

## 工作目录约定

每次运行建立/使用一个输出目录 `LiuLab-Literature-<YYYY-MM>/`（回顾模式用 `LiuLab-Retrospective-<起>-<止>/`）：

```
LiuLab-Literature-2026-09/
├── 01_PDF/            # PDF 存放（GitHub 永不上传，版权红线）
├── 02_BibTeX/         # LiuLab_<YYYY-MM>_library.bib + naming_manifest.csv
├── 03_Reports/        # 摘要报告、精读报告、手动下载Checklist.md、exclusion_log.md
├── raw/               # epmc_raw.json / arxiv_raw.json
├── cn_titles.json     # 英文题名词头 → 中文译名
├── relevance_drops.json  # 相关度剔除清单（跨批累积）
├── literature_database.json  # 全量元数据库（唯一数据源）
└── tools/             # 本 skill scripts 拷贝（保证可复跑）
```

**运行方式**：把 `scripts/*.py` 拷贝到工作目录 `tools/` 下执行（脚本以自身目录为 BASE），
或传 `--dir` 指定工作目录。用管理版 Python 运行。

**数据库字段规范**：`literature_database.json` 每条记录须含 `category`（检索组/方向标签）与 `year_cn`（中文年份标识）；
PDF 下载状态统一标 `download_status`：`done`（PDF 归档=完成）/ `pending`（下载处理中/待下载）/ `HUMAN`（需人工复核）/ `deferred`（跳过/无权限）。
**skill 更新后必须重读磁盘版**（Skill 工具缓存可能仍是旧版）。

---

## 标准流程

### 第 1 步：检索入库（7 组查询主题）

**标准 4 组（核心方向）** — `liulab_search.py` 内置：

| 组名 | 主题 | 核心关键词 |
|------|------|-----------|
| **GUT** | 肠道微生物组+消化道疾病 | gut microbiome/microbiota, IBD, colitis, Crohn*, dysbiosis, mucosal, gut-liver/brain axis, intestinal barrier, NAFLD, hepatic encephalopathy, C. difficile |
| **PROBIO** | 工程菌/益生菌/LBP | engineered bacteria, probiotic, Lactobacillus, Bifidobacterium, E. coli Nissle, live biotherapeutic, bacterial therapy, OMV, protoplast, chassis bacteria |
| **DELIVERY** | 口服递药/黏膜给药 | oral delivery, mucosal delivery, colon-targeted, enteric, mucoadhesive, oral vaccine, mucosal vaccination, probiotic delivery, pH-responsive |
| **BIOMAT** | 微生物-材料交叉 | engineered bacteria + hydrogel/3D printing/nanoparticle/biomaterial/living material/bacterial hydrogel/living coating/living ink |

**补充 4 组（扩展方向）** — 已并入 `liulab_search.py`：

| 组名 | 主题 | 核心关键词 |
|------|------|-----------|
| **GUTAXIS** | 肠-器官轴+代谢物 | gut-brain/liver/skin/eye axis, microbial metabolites, SCFA, tryptophan, bile acids, indole, gut permeability |
| **CONTROL** | 可控/智能活体治疗 | engineered bacteria + stimuli-responsive/ultrasound/magnetic/NIR/photothermal/pH-responsive/enzyme-responsive, spatiotemporal |
| **TUMOR** | 肿瘤免疫 | 细菌支路：engineered bacteria/probiotic + tumor/cancer/immunotherapy；非细菌支路：intratumoural/in situ vaccination, cancer vaccine, oncolytic, checkpoint degradation, antigen presentation, antitumor immunity + tumor（2026-10 扩充，防漏检瘤内疫苗类工作） |
| **REGEN** | 组织工程/再生医学 | tissue regeneration/repair, wound healing, haemostasis, blood clot, 3D printing, bioprinting, hydrogel, scaffold, cardiac repair, corneal repair, organoid, stem cell, biomaterial |

**兜底组（必跑）**：

| 组名 | 主题 | 说明 |
|------|------|------|
| **TOPJ** | 顶级期刊扫掠 | 按期刊维度直查 Nature/Science/Cell 家族 26 种顶级刊，**不依赖任何关键词**，彻底绕开截断与关键词盲区。2026-10 复盘证实：3/5 漏检 Nature 均可被 TOPJ 召回 |

**执行顺序**：
1. `python liulab_search.py --all-topics --from YYYY-MM-DD --to YYYY-MM-DD` → `raw/epmc_raw.json`（TOPJ 用 `--topic TOPJ --max 12000` 单独全量拉取后合并）
2. ⚠️ **关键词组已改为分页拉取（每页200条循环），TOPJ 组务必给足 --max**，勿用小 retmax 截断
3. ⚠️ **esearch 万条截断（2026-10 确认）**：PubMed esearch 无 history server 时 retstart+retmax 上限约 10000 条。TOPJ 总量 16669 但只拉回 9958，导致 27 篇金标准漏检。**解法**：按期刊/月拆分子查询，或直接用 DOI 直查补漏（见第 5 条）
4. 主题查询 503 失败：用 `--topic <名>` 单主题补抓合并，勿整库重跑覆盖
5. **补漏双保险**（每批必做）：WebSearch 核对顶级期刊当期目录 + 已知 DOI 直查
6. **金标准召回核对**（2026-10 新增，每批必做）：用已积累的金标准文献（如用户62篇分享文献）DOI 清单对本批结果做召回核对，逐篇诊断 miss 原因（窗口外/截断/关键词盲区），miss 即补入并修检索式。**2026-10 修复后已达 62/62 = 100% 召回**（3 个重复 PDF 对应 59 篇独立论文）
7. **中文文件名→英文 DOI/PMID 解析**（金标准核对前置）：用户分享 PDF 文件名为中文标题，无法直接匹配 PubMed 英文题名。需先用 `tools/gold_resolve*.py` 按"期刊 + 英文关键词"查 PubMed/CrossRef 解析真实 DOI/PMID，**必须加标题短语校验防止误命中**（如 `phrase_ok()` 检查题名含关键短语）
8. 回顾模式按年分段跑（每年一次，断点续跑）
9. 合并去重用 `liulab_merge_raw.py`（保留人工修正，**勿全量重建**）

### 第 2 步：期刊白名单 + 相关度筛选（优中选优）

**期刊白名单（A-F 组）**：

| 组 | 期刊 | 说明 |
|----|------|------|
| **A-Nature 家族** | Nature、Nat Commun、Nat Biotechnol、Nat Med、Nat Mater、Nat Biomed Eng、Nat Microbiol、Nat Chem、Nat Metab、Nat Methods、Nat Immunol、Nat Aging、Nat Cancer、Nat Rev Gastroenterol Hepatol、Nat Rev Microbiol、**Nat Water、Nat Food、Nat Sustainability**（2026-10 扩充） | npj 系列不收 |
| **B-Science 家族** | Science、Sci Adv、Sci Robot、Sci Transl Med、Sci Immunol、**Science Bulletin**（2026-10 扩充） | Science Signaling 不收 |
| **C-Cell 家族** | Cell、Cell Metab、Cell Host Microbe、Cell Stem Cell、Cancer Cell、Immunity、Neuron、Mol Cell、Chem、Matter、**Cell Reports、Cell Rep Med、Cell Chem Biol、Cell Discovery、Cell Biomaterials**（2026-10 扩充） | iScience/Current Biology 不收；**Cell Reports Medicine 不能被 "cell reports" 家族排除模式误杀** |
| **D-用户点名** | Adv Mater、Adv Funct Mater、Adv Sci、JACS、Angew Chem(Int Ed) | 即使个别年份 IF<15 也收 |
| **E-同类 IF≥15** | Gut、Gastroenterology、Hepatology、Microbiome、Signal Transduct Target Ther、ACS Nano、Gut Microbes、**PNAS**（2026-10 扩充） | |
| **F-用户补充** | Adv Healthc Mater、**Med**（2026-10 扩充） | |

**排除**：低分刊、npj 系列、iScience、Science Signaling。
**用户点名期刊优先于 IF 判断**（Biomaterials、JACS、Angew 即使个别年份 IF<15 也收）。
被排除期刊按计数写 `03_Reports/exclusion_log.md`（含收录规则全文）。

**白名单匹配规则（2026-10 修复）**：
- 用 `_norm()` 归一化（小写、`.`→空格、折叠空白），再用 `_name_matches()` 边界匹配
- **前缀漏洞修复**："nature" 不能误收 "nature water"（remainder 非字母开头才匹配）
- **排除模式优先级修复**：白名单先查，命中即保留，再查 EXCLUDED_PATTERNS（"cell reports medicine" 不被 "cell reports" 家族排除模式误杀）
- **PNAS/Med/Science Bulletin/Cell Reports 等已加入白名单**（2026-10 扩充）

**题名 + 摘要双重相关度审查（防误杀原则）**：

- 必须**题名+摘要一起看**（勿只看题名）。摘要来源：EPMC `abstract` 字段；无摘要才降级仅题名判断并标注 `no-abstract`。
- **防误杀**：题名常掩盖真实内容。凡准备写入 drop 的记录先复读摘要再落笔；
  已 drop 的可回溯审计，发现误杀即移出 drop 区恢复入库。
- **LiuLab 保留维度（摘要命中任一即保留，2026-10 大扩充）**：
  - 工程菌/益生菌作为治疗载体或活体材料
  - 消化道疾病治疗（IBD、糖尿病、NAFLD、肝性脑病、肠道感染、菌群失调）
  - 肠道微生物组调控、肠-器官轴（肠-脑轴、肠-肝轴）
  - 口服递药/黏膜递送（pH响应、结肠靶向、益生菌递药、口服疫苗）
  - 微生物-材料交叉（水凝胶、3D打印、纳米杂合体、活体材料）
  - 可控/智能活体治疗（光/磁/声/pH响应）
  - **REGEN 维度（2026-10 补漏）**：wound healing、tissue regeneration、haemostasis、blood clot、organoid、stem cell、cardiac repair、corneal repair
  - **疫苗/肿瘤免疫维度（2026-10 补漏）**：vaccination、intratumoural、checkpoint degradation、antigen presentation、oncolytic、cancer vaccine、immunotherapy
  - **OMV/灭活菌/NO/抗毒素维度（2026-10 补漏）**：outer membrane vesicle、OMV、inactivated bacteria、nitric oxide、antitoxin、colibactin
  - **其他金标准主题（2026-10 补漏）**：mitochondria、protoplast、catalase、protein degradation、immunological synapse、phenylketonuria、microalgae、mycelium、sprayable、endosymbiotic 等
- **离题剔除（即使顶刊）**：纯临床益生菌试验（无工程/材料维度）、酵母/真菌结构生物学、
  代谢工程合成天然产物、无细胞体系、纯合成生物学（不涉消化道）、纯肿瘤（非顶级）。
- **DROP 维度收敛（2026-10 修复）**：移除 "surface display"（误杀抗毒素论文）、"metabolic engineering"（误杀工程益生菌代谢重编程）、"biosynthesis"（过宽）、"clinical trial"（金标准 PKU 论文是二期临床）、"randomized/phase iii"。现仅保留：chromatin、polymerase、crystal structure、structural biology、cell-free、natural product。
- 离题论文 DOI + 理由写 `relevance_drops.json`，跨批累积，重建不丢。

### 第 3 步：DOI 全量补全（标准：0 缺失）

优先级链（每条规则均有真实教训）：
1. arXiv 记录 → `10.48550/arXiv.<id>`（标准 DOI，必有）
2. CrossRef `query.bibliographic` 题名匹配：归一化词集 Jaccard ≥ 0.75 才采纳；429 退避 8s/16s/24s
3. PMC 页面 `<meta name="citation_doi">` 提取（题名被截断/预印本 DOI 错误时的权威来源）
4. **剔除伪 DOI**：`.s001` 后缀（补充材料）、`10.2139/ssrn.*`（预印本，须换成正式期刊 DOI）
5. CrossRef 命中时顺手校正 `journal`/`journal_abbrev`（API 期刊字段常错）

DOI 是文章的必备标识，缺失说明检索策略有漏——优先修策略，修不到才保留英文原题供用户手动检索。
**不编造 DOI**。

### 第 4 步：规范化命名 + BibTeX

1. 逐篇把英文题名译成中文，写入 `cn_titles.json`（键 = 题名前 25+ 字符词头）。
2. 命名规则：`年月-期刊简写-论文中文名`
   （如 `2026-09-NatMicrobiol-编码前噬菌体的工程菌实现预防性裂解噬菌体疗法`）。
3. `02_BibTeX/LiuLab_<YYYY-MM>_library.bib`（Zotero 可直接导入：author/journal/year/doi/url）。
4. `02_BibTeX/naming_manifest.csv`（含文献类型列：研究论文 / 综述·观点）。
5. `01_PDF/` 内 PDF 按规范化命名重命名。

### 第 5 步：PDF 管理

- 自动下载开放获取 PDF（bioRxiv/arXiv 直链可用；Elsevier/ACS/Nature 等出版商反爬，会失败，属正常）。
  **批量下载获取环节详见独立 skill `literature-download`**（出版商配方/人机协作/通宵驱动等下载域知识都在那边，两 skill 独立不混同）。
- `liulab_import_pdfs.py --downloads <用户Downloads目录> --since YYYY-MM-DD`（dry-run 报告）
  → 确认匹配无误后加 `--apply`：pypdf 提取首页 DOI/题名，匹配优先级
  **filename_doi（文件名即 DOI）> doi_in_text > 提取 DOI 精确互认 > 模糊（仅当提不出 DOI，阈值 0.6）**；
  PDF 带 DOI 却对不上库 → 转人工，**绝不模糊绑定**（误绑事故教训）。
  **复制**（不是移动）到 `01_PDF/` 并按规范化命名，置 `pdf_manual=True`。
- 导入后 md5 哈希核验：与库逐字节相同=残留副本；异版式保留出版版；SI 用头部判据拦截（见红线 9）。
- ⚠️ 涉及个人目录只复制不移动，绝不删除用户 Downloads 里的原文件（清理须用户逐次批准，
  走"备份→回收站→≤10/批→逐批核验"协议，详见 literature-download skill）。

### 第 6 步：三态 Checklist（`03_Reports/手动下载Checklist.md`）

规范：
- 三态：`[x]` 已获取｜`[ ]` 待下载（附 DOI 入口）｜`[×]` 高校图书馆未订阅无法下载（用户手动标记，**重建时必须保留**）。
- **研究论文（含预印本）与综述/观点分两大节**（用户明确要求"综述和研究分开"）。
- 排序：已获取优先 → 期刊优先级 → 日期；每条含期刊/日期/类型/通讯作者(推定)/英文原题/下载入口。

### 第 7 步：报告

**检索发展报告（每次检索必出）**（`03_Reports/检索发展报告_<时间范围>.md`）：
> 这是一份**面向用户的领域发展概览**，帮助用户了解该时间段内各研究方向的动态。

```markdown
# LiuLab 检索发展报告（<起始月> — <截止月>）

## 一、检索概览
- 检索时间窗口 / 检索组数 / 总候选数 / 白名单保留数
- 补漏双保险执行情况

## 二、领域发展态势（按 8 大检索组）
对每个方向（GUT/PROBIO/DELIVERY/BIOMAT/GUTAXIS/CONTROL/TUMOR/REGEN）：
- 命中数量与占比
- 月度发表趋势（是否集中爆发/平稳）
- 代表性高影响力论文（≥3篇一句话点评）
- 新趋势/新概念/新方法观察

## 三、期刊生态
- 顶刊（Nature/Science/Cell家族）产出概览
- 各白名单组篇数分布
- 高产期刊 Top10

## 四、时间线热点
- 月度热点事件（重要论文集中出现的月份）
- 跨方向融合趋势（哪些交叉组合增多）

## 五、值得关注的方向信号
- 哪些方向正在升温（新增论文集中、顶刊密度高）
- 哪些方向相对稳定
- 对LiuLab的启示：哪些值得跟进、哪些可做差异化
```

**月度摘要报告**（`03_Reports/`，每篇一节）：
```markdown
### <序号>. <年月-期刊简写-中文名>
- **英文原标题**：…
- **DOI**：10.xxxx/xxxxx
- **文献类型**：研究论文 / 综述·观点
- **通讯作者**：…（单位）
- **摘要**：（中文转述，200 字内）
- **研究结论**：…
- **创新点**：…
- **科学问题**：该文回答了什么问题、为什么重要
- **批判性思考**：局限性、可复现性疑点、与LiuLab方向的关联/可借鉴处
```

**TOP3 精读报告**（排序：**影响因子 × 科学问题新颖性**）：
```markdown
## TOP<N>：<中文名>（<期刊>, <年月>）
1. 研究背景与领域坐标（该文在 5 年演进中的位置）
2. 核心科学问题与假说
3. 实验设计拆解（模型/材料/表征/对照）
4. 关键结果逐图解读
5. 机制阐释深度评估（因果链完整度）
6. 局限与未解决问题
7. 对LiuLab方向的启示：可复用方法、可延展假说、潜在合作点
```

**回顾模式（5 年补齐）**：每年产出
- **年度综评**：本年代表性论文 5-8 篇点评 + 年内技术/概念演进脉络
- **每年 TOP2-3 精读**（同上模板）
- 最后汇总一份**跨年发展时间线**（里程碑论文、方法突破、概念转折，按年月排列）

### 第 8 步：GitHub 归档（`<用户名>/LiuLab-References`）

- **版权红线：出版商 PDF 与 `01_PDF/` 永不上传**（`.gitignore` 已排除）；只上传元数据/BibTeX/报告/checklist/脚本。
- 走 `api.github.com` Git Data API 单原子提交（blobs→tree→commit→ref）；空仓库先用 Contents API 引导初始提交。
- 网络事实：`github.com` 直连/代理常不通，`api.github.com` 可达 → 不要依赖 git push，用 REST 上传。
- 连接器写入权限：GitHub App token 默认 403 → 用 fine-grained PAT（Repository access 仅 LiuLab-References；
  Permissions → Contents: Read and write）。**提醒用户用完即删**。

### 第 9 步：收尾

- 若是定时自动化，用 `automation_update` 把本期确定的约定写回自动化 prompt（保持自包含）。
- 把新约定/教训追加到工作区记忆 `MEMORY.md`。

---

## 硬性红线（不可协商）

1. **出版商 PDF 永不上 GitHub / 永不外传。**
2. **个人目录（Downloads/Desktop/Documents）只读+复制，绝不移动/删除。**
3. **DOI 必全量补全**；补不到就如实保留英文原题，**不编造 DOI**。
4. **checklist 用户标记（尤其 `[×]`）必须在重建时保留。**
5. **综述与研究论文分开呈现。**
6. **中文回答；数据库/脚本一律 UTF-8。**
7. **相关度审查必须题名+摘要双看（防误杀）。**
8. **绝不向记录 dict 写入 set 等不可 JSON 序列化的辅助字段**（曾导致数据库截断损坏）。
9. **SI/补充材料绝不入库当正文**（头部判据：剥掉开头 URL/DOI 行后文本以 supplement/supporting information
   起头，或含 "supplementary materials for"/"major resources table"/"in the format provided by the authors"；
   曾 18 篇 SI 误绑入库后全库审计隔离）。
10. **DB 单写者**：批量导入 `--apply` 写 `literature_database.json` 前必须停下载驱动/其他写者（并发写曾致库截断）。

详细字段规范、报告模板、GitHub 排错手册见 `references/workflow.md`。
