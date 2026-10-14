# workflow.md — 字段规范 · 报告模板 · GitHub 排错手册

> 本文档为 LiuLab 文献流水线的参考规范，沿用用户验证过的探索习惯与方法论。
> 检索主题和相关度判定维度已针对 LiuLab 课题组偏好定制。

## 1. literature_database.json 记录字段

```json
{
  "source": "EuropePMC | arXiv | Web",
  "id": "PMID/PPR/arXiv-id",
  "doi": "10.xxxx/xxxxx（必补全）",
  "pmid": "...", "pmcid": "PMC...",
  "title": "英文原标题（清洗 HTML 标签）",
  "cn_title": "中文译名",
  "normalized_name": "年月-期刊简写-中文名",
  "key": "BibTeX key（姓+年+题名首词）",
  "journal": "全称", "journal_abbrev": "NLM 简写",
  "date": "YYYY-MM-DD",
  "authors": ["..."], "corresponding_author": "推定=末位作者",
  "abstract": "...",
  "pubtypes": ["Review", "Journal Article", "Preprint"],
  "is_oa": true, "oa_status": "…", "pdf_url": "…",
  "pdf_downloaded": true, "pdf_file": "规范化命名.pdf", "pdf_manual": true,
  "topics": ["GUT", "PROBIO", "DELIVERY", "BIOMAT", "GUTAXIS", "CONTROL", "TUMOR"]
}
```

⚠️ **绝不**把 set / 函数 / 自定义对象写进记录 dict —— `json.dump` 会中途截断整个文件。
辅助索引（词集、DOI 索引）一律在 dict 外并行维护。

## 2. 文献类型判定

- Europe PMC `pubtypes` 含 `Review` → **综述/观点**；其余（含预印本）→ **研究论文**。
- checklist 与 naming_manifest.csv 必须标注类型，且 checklist 分两大节呈现。

## 3. 检索发展报告模板（每次检索必出）

```markdown
# LiuLab 检索发展报告（<起始月> — <截止月>）

## 一、检索概览
| 指标 | 数值 |
|------|------|
| 检索时间窗口 | YYYY-MM ~ YYYY-MM |
| 检索组数 | 8 组 |
| 总候选 | N 篇 |
| 白名单保留 | M 篇 |
| 补漏双保险 | 已执行/待执行 |

## 二、领域发展态势
（每个检索组的命中数、月度趋势、代表性论文、新趋势观察）

## 三、期刊生态
（顶刊产出、白名单组分布、高产期刊 Top10）

## 四、时间线热点
（月度热点事件、跨方向融合趋势）

## 五、值得关注的方向信号
（升温方向、稳定方向、对LiuLab的启示）
```

## 3b. 月度摘要报告模板（每篇一节）

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

## 4. TOP3 精读报告模板

排序依据：**影响因子 × 科学问题新颖性**。每篇结构：

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

回顾模式（5 年补齐）：每年产出
- **年度综评**：本年代表性论文 5-8 篇点评 + 年内技术/概念演进脉络；
- **每年 TOP2-3 精读**（同上模板）；
- 最后汇总一份**跨年发展时间线**（里程碑论文、方法突破、概念转折，按年月排列）。

## 5. GitHub 上传排错手册（均为实战结论）

| 症状 | 原因 | 解法 |
|---|---|---|
| git push 超时 / proxy 502 / schannel 断连 | `github.com` 出口被断 | 不用 git 协议，走 `api.github.com` REST（通常可达） |
| 连接器 `push_files` 403 "Resource not accessible by integration" | GitHub App 安装 token 缺 Contents:write | 用 fine-grained PAT（见下） |
| `git/blobs` 409 "Git Repository is empty" | 空仓库无 HEAD | 先 Contents API PUT README.md 引导初始提交 |
| `git/refs` 422 "not a fast forward" | 新提交没带 parent | `parents:[head_sha]`；仍失败则 PATCH ref 加 `force:true` |
| CrossRef 429 | 限流 | 退避 8s/16s/24s 重试，UA 带 mailto |

### fine-grained PAT 创建指引（给用户的操作步骤）
1. `github.com/settings/personal-access-tokens/new`（Fine-grained tokens → Generate new token）。
2. **Repository access**：Only select repositories → `LiuLab-References`。
3. **Permissions → Repository permissions → Contents**：Read and write（其余不动）。
4. 生成后把 token 交给本轮使用，**用完立即到同一页面 Revoke/Delete**（一次性使用，不留存）。

## 6. PDF 版权红线

出版商 PDF 受版权保护，**永不上传 GitHub**。仓库 `.gitignore` 固定排除 `01_PDF/`、`*.pdf`；
上传脚本层面也硬性跳过 PDF 与 `01_PDF/`、`raw/` 目录（双重保险）。
仓库只承载：元数据库、BibTeX、命名清单、报告、checklist、流水线脚本。

## 7. 回顾模式（5 年补齐）执行要点

1. **分段**：按年调用检索脚本（每年 7 组查询一次），新记录合并去重
   （保留人工修正；勿全量重建）→ 断点续跑。
2. **量级预期**：每年 ≈ 300-900 条候选；**期刊层级 × 相关度 双重筛选**
   剔除弱相关（如纯临床益生菌试验而无工程化/材料维度者、纯肿瘤非顶级论文、
   代谢工程合成天然产物等离题论文），逐条理由写入 `exclusion_log.md`。
3. **DOI 补全分批跑**（CrossRef 限流），跑完统计缺失率（标准 0 缺失）。
4. **中文翻译批量填** `cn_titles.json`；命名规则不变，年月用论文自身发表年月。
5. **报告**：按第 4 节"回顾模式"结构产出；TOP 精读按年覆盖 5 年演进，最后合成时间线。
6. **归档**：LiuLab-References 仓库下建 `YYYY/` 或 `retrospective/` 子目录存放，README 更新索引。

## 8. 期刊白名单（优中选优）

收录分 A-F 六组：
- **A-Nature 全家族**（npj 不收）：Nature、Nat Commun、Nat Biotechnol、Nat Med、Nat Mater、
  Nat Biomed Eng、Nat Microbiol、Nat Chem、Nat Metab、Nat Methods、Nat Immunol、Nat Aging、
  Nat Cancer、Nat Rev Gastroenterol Hepatol、Nat Rev Microbiol
- **B-Science 家族**：Science、Sci Adv、Sci Robot、Sci Transl Med、Sci Immunol
  （Science Signaling 不收）
- **C-Cell Press 高分刊**：Cell、Cell Metab、Cell Host Microbe、Cell Stem Cell、Cancer Cell、
  Immunity、Neuron、Mol Cell、Chem、Matter、Cell Rep Med、Cell Chem Biol、Cell Discovery
  （Cell Reports/iScience/Current Biology 不收）
- **D-用户点名**：Adv Mater、Adv Funct Mater、Adv Sci、JACS、Angew Chem(Int Ed)、Biomaterials
- **E-同类 IF≥15**：Gut、Gastroenterology、Hepatology、J Clin Invest、Microbiome、
  Signal Transduct Target Ther、ACS Nano、Bioact Mater、Adv Drug Deliv Rev、Trends Microbiol
- **F-用户补充**：ACS Synthetic Biology、Materials Today Bio、Advanced Healthcare Materials

低分一律不收；边缘未收（IF≈12-15）：Small、Mater Horiz、Trends Biotechnol、Theranostics、
Nano Lett、PNAS、Composites Part B 等。**用户点名期刊优先于 IF 判断**。

## 9. 相关度剔除模式（relevance_drops.json）——题名 + 摘要双重审查

宽检索会把顶刊离题论文带进白名单。每批审一遍新命中，
**必须题名＋摘要一起看**：

- 摘要来源：EPMC 记录的 `abstract` 字段；个别无摘要记录才降级仅题名判断并标注 `no-abstract`。
- **防误杀原则**：题名常掩盖真实内容。凡准备写入 drop 的记录，先复读摘要再落笔；
  已 drop 的批次可回溯审计摘要，发现误杀即移出 drop 区恢复入库。
- **LiuLab 判定维度（摘要命中任一即保留）**：
  - 工程菌/益生菌作为治疗载体或活体材料
  - 消化道疾病治疗（IBD、糖尿病、NAFLD、肝性脑病、肠道感染、菌群失调）
  - 肠道微生物组调控、肠-器官轴（肠-脑轴、肠-肝轴）
  - 口服递药/黏膜递送（pH响应、结肠靶向、益生菌递药）
  - 微生物-材料交叉（水凝胶、3D打印、纳米杂合体、活体材料）
  - 可控/智能活体治疗（光/磁/声/pH响应）
- **离题剔除示例**：纯临床益生菌试验（无工程/材料维度）、酵母/真菌结构生物学、
  代谢工程合成天然产物、无细胞体系、纯合成生物学（不涉消化道）、纯肿瘤（非顶级）。
- 离题论文 DOI + 理由写 `relevance_drops.json`，跨批累积。

## 10. 批次边界事项登记

跨年论文按 FIRST_PDATE 归属批次；发现下批必收的里程碑论文记入年度统计报告"边界事项"节。
（LiuLab 方向里程碑论文待回顾模式中持续登记补充。）
