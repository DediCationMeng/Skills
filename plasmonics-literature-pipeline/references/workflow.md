# workflow.md — 字段规范 · 报告模板 · GitHub 排错手册

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
  "topics": ["PLASMON-CORE", "PLASMON-SHAPE", "PLASMON-BIO"]
}
```

⚠️ **绝不**把 set / 函数 / 自定义对象写进记录 dict —— `json.dump` 会中途截断整个文件（真实事故，
66 条记录库整库损坏，需用 restore 管线重建）。辅助索引（词集、DOI 索引）一律在 dict 外并行维护。

## 2. 文献类型判定

- Europe PMC `pubtypes` 含 `Review` → **综述/观点**；其余（含预印本）→ **研究论文**。
- checklist 与 naming_manifest.csv 必须标注类型，且 checklist 分两大节呈现。

## 3. 月度摘要报告模板（每篇一节）

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
- **批判性思考**：局限性、可复现性疑点、与本课题组方向的关联/可借鉴处
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
7. 对本方向的启示：可复用方法、可延展假说、潜在合作点
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
2. **Repository access**：Only select repositories → `Plasmon-References`。
3. **Permissions → Repository permissions → Contents**：Read and write（其余不动）。
4. 生成后把 token 交给本轮使用，**用完立即到同一页面 Revoke/Delete**（一次性使用，不留存）。

## 6. PDF 版权红线（用户已认可的做法）

出版商 PDF 受版权保护，**永不上传 GitHub**。仓库 `.gitignore` 固定排除 `01_PDF/`、`*.pdf`；
上传脚本（plm_upload_github.py）层面也硬性跳过 PDF 与 `01_PDF/`、`raw/` 目录（双重保险）。
仓库只承载：元数据库、BibTeX、命名清单、报告、checklist、流水线脚本。

## 7. 回顾模式（5 年补齐）执行要点

1. **分段**：按年调用 `plm_search.py` + `plm_search_extra.py`（每年 6 组查询一次），新记录用
   `plm_merge_raw.py` 合并去重（保留人工修正；勿用 `plm_build_db.py` 全量重建）→ 断点续跑。
2. **量级预期**：每年 ≈ 300-900 条候选（等离激元方向偏宽检索时可能更多，必要时调大
   `--max-pages`）；**期刊层级 × 相关度 双重筛选**（`plm_filter_journals.py`
   ＋ `plm_relevance_filter.py`），剔除弱相关（如无纳米材料维度的纯理论/器件论文、
   SPR 仅作测量手段的分子互作研究等离题论文），逐条理由写入 `exclusion_log.md`。
3. **DOI 补全分批跑**（CrossRef 限流），跑完统计缺失率（标准 0 缺失）。
4. **中文翻译批量填** `cn_titles.json`；命名规则不变，年月用论文自身发表年月。
5. **报告**：按第 4 节"回顾模式"结构产出；TOP 精读按年覆盖 5 年演进，最后合成时间线。
6. **归档**：Plasmon-References 仓库下建 `YYYY/` 或 `retrospective/` 子目录存放，README 更新索引。

## 8. 期刊白名单（2026-10-09 等离激元方向微调，按期刊梯队 A-H）

收录分 A-H 八组（实现见 `plm_filter_journals.py`）：A-Nature 全家族（npj 不收，含
Nat Photonics/Nat Nanotechnol/Nat Mater）、B-Science/Sci Adv/Sci Robot/Sci Transl Med/Sci Immunol、
C-Cell Press 高分刊（Chem/Matter/Joule 对生物医学应用方向有用）、
D-Adv Mater/Adv Funct Mater/Adv Sci/JACS/Angew/Biomaterials、
E-学科顶刊·第二梯队（ACS Nano、Nano Lett、Nano Today、Light Sci Appl、Phys Rev Lett、
Chem Rev、Chem Soc Rev、Acc Chem Res 等）、
F-用户补充（ACS Synthetic Biology、Materials Today Bio、Advanced Healthcare Materials）、
G-次顶刊·第三梯队（Small、Chem Mater、Nanoscale、J Phys Chem Lett、ACS Photonics、
Adv Opt Mater、ACS Appl Mater Interfaces、Nano Energy、Appl Catal B、Biosens Bioelectron、
Theranostics）、
H-专业刊·第四梯队（J Phys Chem C、Plasmonics、Nanophotonics、Opt Express、ACS Appl Nano Mater、
J Nanopart Res、Opt Mater Express；收录偏宽，收紧"优中选优"时移除该组重刷）。
边缘未收（可再议）：Small Methods、Small Science、Nanoscale Horizons、Nanoscale Advances、
Mater Horiz、PNAS、Adv Mater Interfaces。**用户点名期刊优先于 IF 判断**（Biomaterials、JACS、
Angew 即使个别年份 IF<15 也收）。

## 9. 相关度剔除模式（relevance_drops.json）——题名 + 摘要双重审查

宽检索（尤其 PLASMON-CORE / EXOTIC-SHAPES）会把顶刊离题论文带进白名单。每批审一遍新命中，
**必须题名＋摘要一起看**（用户 2026-10-09 明确要求，勿只看题名）：

- 摘要来源：EPMC 记录的 `abstract` 字段；个别无摘要记录才降级仅题名判断并标注 `no-abstract`。
- **防误杀原则**：题名常掩盖真实内容（例：题名只写材料形貌但摘要才是生物医学应用主角、
  或题名无 plasmonic 词但摘要核心是 LSPR 纳米材料）→ 必须保留。凡准备写入 drop 的记录，
  先复读摘要再落笔；已 drop 的批次可回溯审计摘要，发现误杀即移出 drop 区恢复入库。
- 判定维度（摘要命中任一即保留）：① 新型等离激元纳米材料（新结构/形貌可控合成/新性质）；
  ② LSPR/SPR/gap plasmon 机理且与纳米材料直接相关；③ 生物医学应用（SERS 传感与成像、
  光热/光动力治疗、LSPR 诊断、药物递送、抗菌/创伤、theranostic）。
- 典型离题（直接剔除）：无纳米材料维度的纯等离激元理论/光子器件/波导通信、SPR 仅作商用
  仪器测量手段的分子互作与生物物理研究、纯金属薄膜/光栅传感（无纳米材料）、纯临床或纯
  生物学研究、纯催化能源工作（无等离激元纳米材料维度）。
- 把离题论文 DOI ＋理由写进 `<工作目录>/relevance_drops.json` 的 `drop` 组（可选 `flag` 组标注
  "使能工具，可删"类保留项），然后跑 `plm_relevance_filter.py`。清单跨批累积，重建不丢。

## 10. 批次边界事项登记

跨年论文按 FIRST_PDATE 归属批次；发现下批必收的里程碑论文记入年度统计报告"边界事项"节。
已登记：2021 批必收 Nat Mater《Living materials with programmable functionalities grown from
bacterial cellulose》（synSCOBY，2021-01-11）；2022 批必收 Nat Mater《Three-dimensional printing
of mycelium hydrogels into living materials》（2022-12-22，真菌方向里程碑）。
