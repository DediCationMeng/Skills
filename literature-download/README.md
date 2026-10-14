# literature-download — 学术文献 PDF 下载流水线 说明文档

> 「下载 → 校验 → 归档」全流程自动化 skill。通过 browser-use 接管 Chrome，按 DOI 批量下载
> 出版商 PDF 并规范化归档。与同系列**检索**类 skill（elm/liulab/gut-dd/plasmonics-literature-pipeline）
> 互相独立：本 skill 只管**全文获取**，不管检索/综述/报告。

## 一、功能描述

### 1.1 定位与目标领域

面向学术文献 PDF 的**批量获取与归档**，适用于任何文献库项目（如 ELM-References、LiuLab 文献库）的
PDF 获取环节。覆盖出版商：Springer Nature、Wiley、Elsevier/ScienceDirect、Cell Press、ACS、
Science/AAAS、RSC、BMJ 等（配方持续迭代积累）。

### 1.2 触发方式

触发词：下载论文/PDF、批量下载文献、按 DOI 下载、补全文献库 PDF、文献归档（如 01_PDF/）、
下载卡住了/下载被拦截、通宵下载。

### 1.3 核心流水线

```
DOI 解析 → 文章页 → PDF 链接发现（文本+图标双通道）→ 下载（三策略按平台）→ 校验 → 归档 → 复用标签
```

- **PDF 发现**：文本匹配 + Acrobat 图标匹配双通道启发（`scripts/pdf_link_finder.js`）
- **下载三策略**：A 同源 fetch→blob（首选）/ B 导航至 PDF 源站 fetch / C 导航原生下载
- **人机协作协议**：cookie 横幅自动点；CAPTCHA/登录墙**先替用户开好交互页**再醒目告警；绝不脚本绕过人机验证
- **质量门**：Content-Type/%PDF- 头校验、DOI 身份核验、SI 头部判据排除补充材料、md5 哈希核验、`X (1)` 冲突处理
- **归档匹配**：filename_doi > doi_in_text > 提取 DOI 精确互认 > 模糊（仅当提不出 DOI）；DOI 冲突转人工
- **批量执行**：错峰并行 8 篇/批、下载完一篇关一篇、慢页结转、质量异常跳过人工收尾
- **队列管理**：hold/deferred 双清单 + 出版商组搁置（每轮每前缀计 1 次）
- **通宵驱动**：`scripts/overnight_drive.sh` 组批→下载→判定→导入→清理→自适应冷却循环至队列空
- **开放取件备份**：`scripts/epmc_fetch.py` + `scripts/pmc_pow.py`（PMC OA/NIH 作者稿，礼貌限速）

### 1.4 脚本清单（scripts/）

| 脚本 | 功能 |
|---|---|
| `pdf_link_finder.js` | DOM 双通道 PDF 链接发现（注入文章页执行） |
| `batch_download.py` | 错峰并行批下载配方（browser-use 管道喂入；批次清单 `current_batch.json`） |
| `night_state.py` | 批输出解析 → hold/deferred 状态机 → 本轮判定（OK/BLOCKED） |
| `gen_batch_next.py` | 下一批组批（OA 优先→订阅→其他；排除 hold/deferred） |
| `epmc_fetch.py` | Europe PMC 开放取件（DOI→pmcid→PDF） |
| `pmc_pow.py` | NCBI PoW 挑战求解（sha256/sha1/md5 兜底） |
| `cleanup_once.py` | 下载残件小批量归位（md5 一致移 `_imported_src`，≤10/次，移动非删除） |
| `chrome_guard.sh` | Chrome CDP 9222 守护（掉线 5s 自动拉起） |
| `overnight_drive.sh` | 通宵无人值守驱动主循环 |

### 1.5 交付物

已归档 PDF 库（规范化命名）· 导入核验报告 · hold/deferred 队列清单 · 跳过清单（人工裁决）·
平台配方更新（`references/platform_recipes.md` 迭代积累）。

## 二、功能边界

### 2.1 做什么（In Scope）

- 机构订阅/OA 许可范围内的全文批量获取；出版商平台识别与下载配方迭代；
- 下载校验（防 HTML 伪装 PDF、防 SI 误收、防错配）；导入匹配与归档；
- 批队列状态管理（hold/deferred/组搁置）；通宵无人值守执行；人机协作交互页预备；
- 个人目录残件清理（**仅限用户逐次批准**，回收站+备份+分批协议）。

### 2.2 不做什么（Out of Scope）

- **不做**付费墙破解、无权内容获取、验证码/人机验证的脚本绕过；
- **不做**文献检索/筛选/综述报告（→ 检索类 pipeline skill）；
- **不做** PDF 文本编辑（→ pdf skill）；
- **默认不删**个人目录任何文件（清理需用户批准并走协议）；
- 不外传出版商 PDF。

### 2.3 硬性红线

1. 绝不脚本绕过人机验证（CAPTCHA/Cloudflare human check）；PoW 仅限 PMC 开放取件；
2. 绝不下载无权访问的内容（无订阅/付费墙 → 登记 checklist/deferred）；
3. 个人目录只读+复制；删除仅限用户批准 + 清理协议（备份→回收站→≤10/批→逐批核验）；
4. 下载完一篇关一篇；绝不关最后一个标签/未完成页；
5. SI/补充材料绝不入库当正文；
6. 导入 `--apply` 写库前停一切其他写者（DB 单写者）；
7. 出版商 PDF 永不外传；中文回答；脚本 UTF-8。

## 三、运行环境与依赖

- Chrome（专用 profile + CDP 9222，`chrome_guard.sh` 守护）；browser-use CLI；
- Python 3（管理版运行时优先）；依赖 pypdf（校验/导入）；
- 环境变量：`WORKDIR`（工作目录）、`DL_DIR`（下载目录）、`BATCH_FILE`、`IMPORT_TOOL`、
  `BU_BIN`/`PY_BIN`/`PYQ_BIN`、`CHROME_BIN`/`CHROME_PROFILE`（均有默认值）；
- 调用 browser-use 时带 `NO_PROXY="localhost,127.0.0.1,::1" BU_CDP_URL="http://127.0.0.1:9222"`。

## 四、目录结构

```
literature-download/
├── README.md                       # 本文档
├── SKILL.md                        # Skill 入口（完整流程与硬性红线）
├── references/platform_recipes.md  # 出版商下载配方 + 期刊 SOP 速查表（迭代积累）
└── scripts/                        # 下载栈脚本（见 1.4）
```

## 五、与同系列 skill 的关系

- 本 skill 独立于检索类文献流水线家族（`elm-`/`gut-dd-`/`plasmonics-`/`liulab-literature-pipeline`），
  **各自独立、互不覆盖**：那些 skill 负责检索→筛选→报告→元数据归档；本 skill 负责全文获取与 PDF 归档。
- 协作界面：本 skill 产出已归档 PDF + 队列清单；文献库 skill 提供 `literature_database.json` 元数据
  与项目归档工具（如 `elm_import_pdfs.py`，由 `IMPORT_TOOL` 指定）。
