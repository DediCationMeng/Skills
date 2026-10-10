# Skills — 自研 Agent Skill 仓库

本仓库存放**由用户带领 AI 从零定制创建**的 Agent Skill（区别于市场安装的现成技能）。
每个 skill 独占一个文件夹，文件夹内同时包含 skill 本体与一份详细说明文档。

## 仓库结构约定

```
Skills/
├── README.md                  # 本文件：仓库总览
├── .gitignore
└── <skill-name>/              # 一个 Skill 对应一个文件夹
    ├── README.md              # 该 Skill 的功能描述、功能边界等详细说明文档
    ├── SKILL.md               # Skill 本体（Agent 加载入口，含 frontmatter）
    ├── references/            # 补充规范（字段规范、报告模板、排错手册等）
    └── scripts/               # 可执行脚本（Python，UTF-8）
```

## Skill 清单

| Skill | 领域 | 创建时间 | 说明文档 |
|---|---|---|---|
| `elm-literature-pipeline` | 工程活体材料（ELMs）/ 生物3D打印 / 微生物活药 | 基准版（系列母本） | [elm-literature-pipeline/README.md](elm-literature-pipeline/README.md) |
| `gut-dd-literature-pipeline` | 肠道靶向药物递送载体 | 2026-10-09（由 ELM 版派生） | [gut-dd-literature-pipeline/README.md](gut-dd-literature-pipeline/README.md) |
| `plasmonics-literature-pipeline` | 等离激元纳米材料（LSPR/SERS/光热诊疗） | 2026-10-09（由 ELM 版派生） | [plasmonics-literature-pipeline/README.md](plasmonics-literature-pipeline/README.md) |

三者同属「文献检索 → 处理 → 归档」流水线家族，脚本同构（前缀 `elm_` / `gdd_` / `plm_`），
仅检索关键词、期刊白名单与归档仓库不同，互相独立、互不影响。

## 安装使用

把目标 skill 文件夹整体拷贝到 Agent 的用户级技能目录即可被识别加载：

```
<skill-name>/  →  ~/.workbuddy-ai/skills/<skill-name>/
```

## 维护约定

1. **一 skill 一文件夹**，文件夹内必须同时包含 `SKILL.md` 本体与 `README.md` 说明文档。
2. **改造文献流水线系列时一律新建派生 skill，不覆盖 `elm-literature-pipeline` 本体**（保持母本原样）。
3. 仓库只存 skill 源码与文档，**永不上传**：出版商 PDF、个人数据、token/密钥、`__pycache__`。
4. 说明文档须覆盖：功能描述（领域、触发词、运行模式、流程、交付物）与功能边界（做什么/不做什么/硬性红线）。
