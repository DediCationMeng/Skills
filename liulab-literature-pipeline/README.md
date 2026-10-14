# liulab-literature-pipeline — LiuLab 文献流水线 说明文档

> 「检索 → 处理 → 归档」全流程自动化 skill，检索主题与相关度判定**针对 LiuLab 课题组偏好定制**
> （消化道疾病/肠道微生物组/工程化细菌/口服递药/微生物-材料交叉）。
> 与同系列 skill（elm/gut-dd/plasmonics-literature-pipeline）及下载域 skill（literature-download）
> **各自独立、互不混同**。

## 一、功能描述

### 1.1 定位与目标领域

面向 LiuLab 课题组方向的文献情报工作：消化道疾病（IBD、糖尿病、NAFLD、肝性脑病、肠道感染）、
肠道微生物组与肠-器官轴、工程化细菌/益生菌/LBP、微生物-材料交叉（水凝胶、3D打印、活体材料）、
口服递药、可控活体治疗；次关注肿瘤免疫（仅顶级）。期刊白名单 A-F 组（Nature/Science/Cell 家族 +
用户点名 + IF≥15 同类刊）。

### 1.2 触发方式

触发词：文献检索、文献追踪、月度文献整理、回顾性检索过去 N 年文献、补齐领域核心文献、文献库、
BibTeX、Zotero、手动下载 checklist、回顾审阅/系统综述/发展脉络。

### 1.3 三种运行模式

| 模式 | 触发 | 产出侧重 |
|---|---|---|
| **月度追踪** | "整理上个月的文献" | 全套交付（BibTeX/摘要报告/TOP 精读/checklist） |
| **回顾补齐** | "彻底检索过去 5 年文献" | 按年分批 + 年度综评 + 每年 TOP 精读 + 时间线 |
| **回顾审阅** | "回顾审阅/系统综述/Meta/PRISMA/领域回眸" | `03_Reports/Retrospective_Review/` 专项成果（整域回眸+综述体裁才走此门） |

### 1.4 标准流程

1. **检索入库（9 组主题）**：GUT/PROBIO/DELIVERY/BIOMAT/CONTROL/TUMOR/REGEN/GUTAXIS + TOPJ 顶级刊兜底扫掠；
   `liulab_search.py` 分页拉取；补漏双保险（当期目录核对 + DOI 直查）；金标准召回核对（62/62）。
2. **期刊白名单 + 相关度筛选**：题名+摘要双看防误杀；保留维度大扩充；DROP 维度收敛。
3. **DOI 全量补全**：arXiv 标准 DOI → CrossRef Jaccard ≥0.75 → PMC citation_doi → 剔伪 DOI；不编造。
4. **规范化命名 + BibTeX**：`年月-期刊简写-中文名`；`cn_titles.json`；Zotero 可导入 .bib + manifest。
5. **PDF 管理**：OA 自动下载；导入匹配（filename_doi > doi_in_text > DOI 互认 > 模糊）；SI 拦截；md5 核验。
   下载域细节 → 独立 skill `literature-download`。
6. **三态 Checklist**：`[x]`/`[ ]`/`[×]`（用户标记重建必须保留）；综述与研究分开。
7. **报告**：检索发展报告 + 月度摘要报告 + TOP3 精读 + 回顾模式年度综评/时间线。
8. **GitHub 归档**：REST 单原子提交；**出版商 PDF 永不上传**；PAT 用完即删。
9. **收尾**：约定写回自动化 prompt；教训入工作区记忆。

### 1.5 脚本清单（scripts/，前缀 `liulab_`）

| 脚本 | 功能 |
|---|---|
| `liulab_search.py` | 9 组主题检索（Europe PMC + arXiv + PubMed TOPJ） |
| `liulab_filter_journals.py` | 期刊白名单筛选（first/final 两阶段） |
| `liulab_relevance_filter.py` | 相关度剔除清单应用（题名+摘要双审） |
| `liulab_fix_dois.py` | DOI 全量补全（五级优先级链） |
| `liulab_build_outputs.py` | 规范化命名 + BibTeX + manifest + PDF 重命名 |

## 二、功能边界

### 2.1 做什么（In Scope）

文献元数据检索/入库/去重/合并；白名单与相关度筛选；DOI 补全；中文命名体系；BibTeX/清单产出；
三态 checklist；发展报告/摘要/精读/年度综评；元数据 GitHub 归档。

### 2.2 不做什么（Out of Scope）

- **不做出版商 PDF 下载攻坚**（→ 独立 skill `literature-download`，两 skill 独立不混同）；
- 不做付费墙破解；不做跨领域检索（其他领域走对应派生 skill）；不做全文逐句翻译；
- 不覆盖其他 skill 的数据库/工作目录。

### 2.3 硬性红线

1. 出版商 PDF 永不上 GitHub/永不外传；2. 个人目录只读+复制，绝不移动/删除（清理须用户逐次批准走协议）；
3. DOI 必全量补全，不编造；4. checklist 用户标记（尤其 `[×]`）重建必须保留；5. 综述与研究分开；
6. 中文回答；UTF-8；7. 相关度审查题名+摘要双看（防误杀）；8. 不向记录写不可序列化字段；
9. SI/补充材料绝不入库当正文（头部判据）；10. DB 单写者（导入写库前停其他写者）。

## 三、运行环境与依赖

Python 3（管理版运行时优先）；依赖 requests/pypdf；Europe PMC/arXiv/PubMed/CrossRef API；
GitHub 归档走 api.github.com（不依赖 git push）；脚本以自身目录为 BASE 或传 `--dir`。

## 四、目录结构

```
liulab-literature-pipeline/
├── README.md              # 本文档
├── SKILL.md               # Skill 入口（完整流程与硬性红线）
├── references/workflow.md # 字段规范、报告模板、GitHub 排错手册
├── assets/
└── scripts/liulab_*.py    # 5 个流程脚本
```

## 五、与同系列 skill 的关系

- 本 skill 为 **LiuLab 课题组定制版**；云端 `elm-`/`gut-dd-`/`plasmonics-literature-pipeline` 为
  另一独立家族（各自独立维护，勿相互覆盖或混同内容）。
- `literature-download`（下载域）与本 skill 各自独立，仅通过"文献库项目 + 元数据 + 归档工具"协作。
