---
name: literature-download
description: 学术文献 PDF 批量下载与归档流水线。当用户要求下载论文/PDF、批量获取文献、按 DOI 下载、补全文献库 PDF、文献归档（如 01_PDF/）时使用。覆盖出版商平台识别、PDF 链接发现（文本+图标双通道启发）、下载策略选择、登录墙/CAPTCHA 人机协作协议、下载后规范化归档、批量队列管理（hold/deferred）、通宵无人值守下载、PMC 开放取件备份通道、导入匹配核验与个人目录残留清理。
---

# Literature Download — 学术文献 PDF 下载流水线

通过 browser-use 接管 Chrome，按 DOI 批量下载出版商 PDF 并规范化归档。
平台配方见 `references/platform_recipes.md`；PDF 发现脚本见 `scripts/pdf_link_finder.js`。

## 何时使用

- "下载这篇/这批论文的 PDF"、"按 DOI 列表批量下载"、"补全文献库的 PDF"
- 文献库管理项目（如 ELM-References）的 PDF 获取环节
- 不适用：开放元数据检索（用 API）、PDF 文本提取/编辑（用 pdf skill）

## 核心流水线（每篇文献）

```
DOI 解析 → 文章页 → 发现 PDF 链接 → 下载 → 校验 → 归档 → 复用标签
```

### 1. DOI 解析
`goto_url("https://doi.org/<doi>")` → 跟随 302 到出版商文章页。等待 Cloudflare 挑战 ≤15s（"请稍候…"通常自行通过）。

### 2. PDF 链接发现（双通道启发，脚本见 scripts/pdf_link_finder.js）
人眼识别下载按钮的两个依据同样适用于 DOM 扫描：

**通道 A — 文本匹配**：链接/按钮文本含 "PDF"、"Download PDF"、"View PDF"、"PDF (N MB)" 等。

**通道 B — 图标匹配（关键）**：许多出版商用 Acrobat 风格图标而非文字标注下载入口：
- `<img>` 的 src/alt/class 含 `pdf`（如 `icon-pdf`、`pdf-download`、`acrobat`）
- 内嵌 `<svg>` 的 class/aria-label 含 `pdf`
- 按钮的 background-image CSS 引用 pdf 图标
- `aria-label`/`title` 属性含 "PDF"（图标按钮的无障碍标注）
- 图标+文字组合：图标所在 `<a>` 或其父级按钮是真正的下载入口

URL 模式辅助：`article-pdf`、`pdfdirect`、`pdfft`、`/pdf/`、`.pdf` 结尾。

**优先级**："Download PDF"（明确动词）> PDF 图标按钮 > "View PDF" > URL 模式 > 补充材料（suppl/si，仅在用户要求时下载）。

### 3. 下载执行（三策略按平台选，配方见 references/）
- **策略 A（首选，最快）**：文章页上下文同源 `fetch(pdfUrl)` → `blob` → `<a download>` 触发保存
- **策略 B（fetch 被反爬拦截时）**：完整导航到 PDF URL（执行 JS 通过挑战）→ 跳到 PDF 源站后同源 fetch → blob
- **策略 C（导航触发原生下载）**：导航到 PDF URL 附 `?download=true` 等参数，Chrome 原生下载

**防超时（重要）**：大文件 fetch 会超过 IPC 5s 限制。用异步任务+轮询：
```js
window.__dl = 'RUNNING';
(async () => { try { /* fetch + 保存 */ window.__dl = 'DOWNLOADED size=' + blob.size; }
catch(e) { window.__dl = 'ERR ' + e.message; } })();
// Python 侧每 3s 轮询 window.__dl 直到非 RUNNING
```

### 4. 校验（防"HTML 伪装 PDF"）
- 响应 `Content-Type` 必须含 `pdf`，否则是登录墙/挑战页 HTML（记录响应前 150 字符用于诊断）
- 归档工具校验文件头 `%PDF-`；不匹配的文件自动拒收

### 5. 归档
下载目录 → 项目归档工具（如 `elm_import_pdfs.py --downloads <dir> --since <date> --dir <工作目录> --apply`）匹配入库。

**导入匹配优先级（2026-10-12 校准，防误绑）**——按序短路：
1. **filename_doi**：文件名本身编码 DOI（`10.1016_j.x.2024.12345.pdf` → 首个 `_` 换 `/`）与库内 DOI 精确互认——最高优先。防止 PDF 正文引用多篇文献时被"第一个匹配"抢绑。
2. **doi_in_text**：某库内记录的 DOI 直接出现在 PDF 文本里（抗提取顺序噪声）。
3. **提取 DOI 精确互认**：pypdf 提取的 DOI 与记录精确/前缀互认。
4. **模糊匹配仅当完全提不出 DOI 时才允许**（词重叠阈值 0.6）。**PDF 带 DOI 却对不上库 → 禁止模糊绑定，转人工**（真实事故：`adma.202201326` 误绑 `mtbio.2022.100435`）。

匹配分 <0.95 时列给用户裁决。

## 人机协作协议

**Cookie 同意横幅**：自动点击，不打扰用户。选择器：
`#onetrust-accept-btn-handler`, `.osano-cm-dialog__close`, `button[id*="accept"]`, `button[class*="accept"]`, `button[title*="Accept"]`（须 `offsetParent !== null` 可见性检查）。

**CAPTCHA / 登录墙**（分工协议）：
1. 先等 10-15s（自动挑战通常自行通过）
2. 仍卡住 → **先把交互页面替用户打开**：导航浏览器到确切的交互页面（文章页→点进 "Log in via your institution"
   →停在身份提供方选择/CARSI 认证入口；CAPTCHA 则停在验证页），用户**只需点击认证**即可，不要让用户自己找页面。
   交互页面保持打开不关（标签纪律例外），一次可备好几个待交互标签
3. 页面备好后**用最醒目方式提醒用户**（红色脉冲告警卡片 + 加粗标题；用户常在后台监测）：
   说明已打开的页面、用户要点击什么、一次通过可放行的后续篇数
4. 用户点击/登录 → cookie 持久化在专用 Chrome profile，后续同平台自动放行
5. **绝不脚本绕过 bot 检测**（违反站点 ToS 且会升级挑战）

## Chrome 会话管理（踩坑教训）

- 启动：专用 profile + 调试端口，**必须 run_in_background: true**（前台进程会在调用边界被回收）：
  ```
  chrome.exe --user-data-dir=<专用目录> --remote-debugging-port=9222 --remote-allow-origins=* --no-first-run --no-default-browser-check
  ```
- 调用 browser-use 时带 `NO_PROXY="localhost,127.0.0.1,::1" BU_CDP_URL="http://127.0.0.1:9222"`
- **标签纪律**：复用同一个工作标签顺序导航（`goto_url`），**绝不关闭最后一个标签**（Chrome 窗口关闭 → 进程退出 → 后台任务结束）
- **下载完一篇关一篇（用户红线）**：每篇结束（成功/SKIP/FAILED）立即 `_safe_close(tid)`——关标签 3 重试 + `list_tabs` 确认已关；SKIP/FAIL 页绝不滞留（曾积压 37 标签拖垮浏览器）；批末双清扫兜底。
- **Chrome 守护**：`scripts/chrome_guard.sh` 后台循环，CDP 9222 掉线 5s 内自动拉起（自动化 Chrome 会静默崩溃，无人值守必备）。
- 登录态/cookie 持久化在 profile 目录，Chrome 重启后自动复用（"迭代补全登录 cookie"机制）

## 期刊级 SOP 记忆（快速通道）

平台配方之外，按**期刊**粒度记住下载流程（`references/platform_recipes.md` 的 SOP 表）：
遇到期刊 SOP 表中已有的期刊，**直接套用对应 SOP**，跳过探测/试错环节，省去每篇 30-60s 的摸路时间。
SOP 表结构：`期刊缩写 | 出版商 | PDF 入口模式 | 下载策略 | 已知陷阱 | 验证日期`。
遇到新期刊 → 走通用诊断流程 → 成功后**立即追加到 SOP 表**（迭代积累）。

## 出版商陷阱库（2026-10 实战校准，先查表再动手）

| 陷阱 | 信号 | 判定与处理 |
|------|------|-----------|
| **Wiley SAML 属性缺失** | `/doi/epdf/` 反弹回 `/abs/`（ABS_BOUNCE）；页面无 "Access provided by <机构>" 横幅 | 机构会话无效的客户端**无解**（IdP 属性释放/Shibboleth 合同问题）。登记 hold、转 IT 工单；PMC NIH 作者稿可救约 60% |
| **SD 限流** | 整页 "There was a problem…CPE00002" | 停止该平台 → 换出版商队列 → 10-15min 后 2-3 篇试探（详见 platform_recipes） |
| **SD 会话丢失** | 文章页出现 "Sign in" 按钮（平时隐藏） | 机构会话掉了 → 告警请用户重登；别当限流处理 |
| **ABS_BOUNCE 无权限** | epdf/pdfdirect URL 弹回 abstract 页 | **下载前拦截**（发起下载前先查 bounce），无权限直接 hold，别浪费下载 |
| **ACS CAPTCHA 升级** | 连续批量后出 CAPTCHA | 标 INTERACTION 跳过 + 入 hold；用户交互通过一次可放行后续。顽固篇（如 Chem Rev）单独 hold 人工 |
| **Science 无订阅** | 下载物是 HTML 非 PDF | 归 deferred（无订阅清单），不重试 |
| **CF "Just a moment"** | Cloudflare 挑战 | 等 10-15s 自行通过；人验证则走人机协作协议 |

## 开放获取备份取件（Europe PMC / PMC 通道，scripts/epmc_fetch.py）

订阅墙论文常有 **NIH 作者稿/OA 版**托管在 PMC，可绕开出版商侧的会话/挑战问题（2026-10 实测救回 185 篇，Wiley 占 141）：
1. Europe PMC REST 按 DOI 查 `pmcid/hasPDF/inEPMC`（三者齐备 = OA 全文在库）
2. PDF 直链：`https://pmc.ncbi.nlm.nih.gov/articles/<PMC>/pdf/`
3. **NCBI PoW 挑战**（`scripts/pmc_pow.py`）：页面给 `challenge`+`POW_DIFFICULTY`(4)，求 `sha256(challenge+str(nonce)).hex()` 前 4 位为 0 的 nonce，回填 cookie `cloudpmc-viewer-pow="challenge,nonce"` 后同会话取件（sha256/sha1/md5 三算法兜底）
4. **礼貌限速**：2.5s/篇；遇 reCAPTCHA 限速页退避 15s 重试
5. 取回文件落暂存区（`_epmc_staging/<doi>.pdf`），走统一导入核验入库

**边界（不可越）**：此通道仅用于 PMC **开放获取**内容（`inEPMC=Y`）的合法取件；PoW 是设计供客户端求解的算力门槛 ≠ 人机验证。**绝不用于绕过付费墙或 CAPTCHA 人机验证**。

## 批量执行（错峰并行 + 完成即关）

**架构：错峰并行批**（8 篇/批，允许结转页叠加后暂时 >8）：
```
Phase A  错峰开标签（间隔 3-4s，防 burst 触发风控）→ 各页后台并行加载
Phase B  逐标签：就绪检测 + cookie 横幅 + PDF URL 发现（按期刊 SOP 快速定位）
Phase C  批量发起 PDF 导航/下载（各标签并行重叠准备时间）
Phase D  轮询下载状态直到完成
```
实测：8 篇并行约 170-210s，串行需 320s+。

**标签纪律（关键，两条铁律）**：
1. **完成即关**：每篇确认下载结束（`window.__dl` 显示 `DOWNLOADED` 且文件落盘）后**立即关闭该标签**，
   不要等整批结束——避免同时挂着大量网页导致浏览器卡顿
2. **未完不关**：下载仍在 `RUNNING` 的标签**绝不关闭**——刚触发下载就关页面会杀死下载任务（miss）。
   超时未完的标记 CARRYOVER 保留标签，下一批先回收其结果，再开新 8 篇（用户授权暂时 >8 并发）
3. 仍绝不关闭最后一个标签（保留 1 个常驻空白标签）

**批次收尾**：运行归档工具核对计数（DB 待下载计数单调递减）；网络异常/平台改版 → 更新 `references/platform_recipes.md`。

**队列状态管理（hold/deferred 双清单，scripts/night_state.py）**：
- **hold_dois.json**（可重试搁置）：PAYWALL/ABS_ONLY 累计×2、NOMATCH×3、ERR:ct/ABS_BOUNCE/ERR:small×3 → hold；
- **deferred_dois.json**（不重试）：无订阅（如 Science 家族）、用户指定跳过；
- **出版商组 hold**：同一 DOI 前缀连续失败达阈值后整组暂缓——**每轮每前缀只计 1 次**（按篇计数曾一轮误伤 ACS 90+Science 33 共 124 篇，教训：组计数先按前缀去重再累加；误伤须回滚）；
- 重试成功即出列；DB 缺失数是唯一进度真理。

**通宵无人值守驱动（scripts/overnight_drive.sh）**：`gen_batch_next`（Elsevier OA→订阅→其他优先组批）→ `batch_download` → `night_state` 判定 → 导入 `--apply` → 清理×2 → 自适应冷却（BLOCKED×1 冷 600s、连×3 冷 1800s）；队列空（PHASE=none）自动退出。CDP 掉线等守护拉起后继续。

## 诊断顺序（必须严格按此顺序，勿把登录墙当"慢速"）

**第 0 步（最先）：判定是否需要人工交互**——在做任何"慢速/异常"分类之前：
1. **防人机验证**：标题含 robot/请稍候/Just a moment，或页面出现 CAPTCHA → 人工告警
2. **机构登录/付费墙**：找不到 PDF 入口时**先怀疑登录墙而非慢速**。信号：
   - 页面有 "Get access" / "Buy article" / "Log in via your institution" / "Access through your institution"
   - 文章页 DOM 无任何 PDF 链接/图标（未登录时出版商直接不渲染下载入口）
   - 期刊页面结构与 SOP 不符（"期刊变了"往往是未登录的精简版页面）
   → 人工告警请用户机构登录（凭据用户输入），登录后 cookie 持久化放行同平台
3. 交互需求判定完毕后，剩余问题才分：**慢速**（保留重试）vs **质量异常**（人工收尾）

## 异常处理原则：区分"质量异常"与"速度慢"（效率第一）

**质量异常（真异常）→ 标记跳过，人工统一收尾**：下载后发现不匹配——错配 PDF（PII/标题对不上）、
匹配分 <0.95、抓到推荐文列表的无关文章等。做法：
1. 在跳过清单记录 `DOI | 异常类型 | 现象摘要 | 尝试过的策略`
2. 立即继续批量主流程；绝不纠缠单篇（人处理一篇 1min vs 机器纠缠 5-10min）
3. 批次全部完成后把跳过清单一次性交给用户裁决

**速度慢（不是异常）→ 保留下载，开下一批**：页面加载慢、PDF 传输慢、落地超时等纯时间问题，
一律不跳过：**保留对应标签让下载继续**，同时新开下一批 8 篇（用户授权暂时 >8 并发），
下批开始时先回收慢页的完成结果。绝不用"超时"当理由放弃一篇文献。

**服务器错误页（SERVER_ERR）→ 冷却换战线，不硬磕**：页面正文 "There was a problem providing the
content you requested"（ScienceDirect CPE00002 等）= 反爬/限流瞬时拒绝。信号已在发现脚本中识别。
处理：停止向该平台发新请求 → **切换到其他出版商队列继续推进**（Nature/ACS/Science 交叉冷却）→
10-15 分钟后小批量（2-3 篇、更长错峰）试探恢复。同批部分成功+部分 CPE = 平台开始限流的前兆，立即收手。

## 质量门：下载后身份核验（每批必做）

用 pypdf 提取前两页文本，**三查**：
1. **DOI 在文中**（或文章号命中）——注意 Nature Reviews 系版式不印可提取 DOI，此时以
   下载 URL 精确匹配 + 标题/主题吻合为准（"0123456789();:" 开头是 Nature Reviews 正文特征）
2. **排除补充材料（ESM/SI 陷阱）**：首页含 "Supplementary information" 或 "In the format
   provided by the authors and unedited" = 作者稿补充材料，**不是正文**。Springer Nature 的
   ESM 链接形如 `media.springernature.com/original/springer-static/esm/art%3A...`，且 URL 内含
   文章 ID 会骗过严格匹配——发现阶段必须排除 `/esm/|springer-static|supplementary|moesm` href。
   **SI 文本头部判据（2026-10-12，防误收）**：剥掉开头 URL/DOI 行后，文本开头是
   `supplement…/supporting information…`，或含 `supplementary materials for`/`major resources table`/
   `in the format provided by the authors` 才判 SI（正文常在文中引用 "see supplementary information"，不能误杀）。
   曾有 18 个 SI 文件（DC1/Major Resources Table）被当正文入库，全库审计后隔离
3. **文件名冲突**：Chrome 对重名下载自动加 " (1)" 后缀；核验时同时检查 `X.pdf` 与 `X (1).pdf`，
   确认新件后替换旧件（旧件移隔离区而非删除）。下载命名一律用 `DOI 下划线化.pdf`，
   让归档工具走 DOI 精确匹配，杜绝标题误配
4. **哈希核验（导入后必做）**：对下载目录残件与 `01_PDF/` 逐字节 md5 比对——相同=残留副本（可走清理协议）；
   不同版式（录用稿 vs 出版版）保留出版商版并核验标题/页数一致；**内容不符才是错配**（曾靠文件大小相等揪出错路由下载）
5. **DB 单写者**：批量导入 `--apply` 写 `literature_database.json` 前必须停下载驱动/其他写者（并发写曾致库截断损坏）

## Nature/Springer 机构登录（WAYF 流，一次放行全平台）

1. 文章页点 "Access through your institution" → 跳 `wayf.springernature.com`
2. 机构搜索框**必须输入完整名** "Shanghai Jiao Tong University"（只输入前缀会 "No matching institutions"）
3. 点联想项（叶子节点，可能是 `<strong>`）→ 提交 "Access through your institution"
4. 若 SSO 会话仍有效则直接弹回文章页并带权限（PDF 链接出现、付费墙文案消失即生效）；
   否则停在 SJTU IdP 登录页交用户输入凭据
5. 验证生效：文章页出现 `/articles/<id>.pdf` 链接 + 无 "Access through your institution" 文案
6. 生效后 Nature 订阅刊走 `fetch('https://www.nature.com/articles/<id>.pdf')` 同源直取（策略 A）

## 个人目录残留清理协议（Downloads 残件，需用户逐次批准）

默认红线是**个人目录只读+复制、绝不删除**。仅当用户**明确批准清理**时按此协议执行：
1. 先备份：与库不一致的文件（异版式/SI 等）复制进项目隔离区（`_human_review/<日期>/`）；逐字节重复件以库内副本为备份（md5 已证一致）
2. 移入**回收站**（Windows Recycle Bin API），**永不永久删除**（`rm`/`del /F` 禁用）
3. **每批 ≤10 个**，逐批核验回收结果后再下一批；任何失败立即停
4. 无关文件（如其他项目/游戏文件夹）绝对不动，只处理已核验清单内的文件

## 硬性红线（不可协商）

1. **绝不脚本绕过人机验证**（CAPTCHA/Cloudflare human check——违反站点 ToS 且会升级挑战）；PoW 算力挑战仅限 PMC 开放取件（见边界说明）
2. **绝不下载无权访问的内容**：付费墙/无订阅 → 登记 checklist/deferred，走图书馆合法途径
3. **个人目录只读+复制**；删除仅限用户批准 + 上述清理协议
4. **下载完一篇关一篇**；绝不关最后一个标签/未完成页
5. **SI/补充材料绝不入库当正文**
6. **DB 单写者**：导入写库前停一切其他写者
7. 出版商 PDF 永不外传；中文回答；脚本/数据库 UTF-8
