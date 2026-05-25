# Personal Skills Repository

这个仓库用于集中管理我本地使用的 `Codex` / `Claude` Skills，包括原创技能、定制化技能，以及基于公开仓库改写后的技能。

仓库目标：
- 统一存放可复用的 `SKILL.md`
- 让本地 Agent 能通过软链接直接发现这些技能
- 为技能附带脚本、参考文档、资源文件和第三方来源声明

## 目录结构

```text
.
├── skills/                     # 各个技能目录
│   ├── code-review-doc-generator/
│   ├── handoff/
│   ├── media-library-organizer/
│   └── skill-creator/
├── scripts/                    # 仓库辅助脚本
├── THIRD_PARTY.md              # 第三方来源与许可证说明
└── README.md
```

## 当前技能

| Skill | 路径 | 说明 |
| --- | --- | --- |
| `code-review-doc-generator` | [skills/code-review-doc-generator/SKILL.md](./skills/code-review-doc-generator/SKILL.md) | 面向 Git/SVN 变更或代码片段的代码评审工作流，生成结构化评审文档与效率指标。 |
| `handoff` | [skills/handoff/SKILL.md](./skills/handoff/SKILL.md) | 将当前会话压缩成可供下一位 Agent 接手的 handoff 文档。 |
| `media-library-organizer` | [skills/media-library-organizer/SKILL.md](./skills/media-library-organizer/SKILL.md) | 规范化影视库目录、文件名和季结构，清理杂项元数据。 |
| `skill-creator` | [skills/skill-creator/SKILL.md](./skills/skill-creator/SKILL.md) | 用于创建、测试、迭代和优化新技能。 |

## 使用方式

### 1. 浏览仓库中的技能

```bash
./scripts/list-skills.sh
```

这个脚本会列出仓库内所有 `SKILL.md` 文件。

### 2. 链接到本地技能目录

```bash
./scripts/link-skills.sh
```

这个脚本会把仓库中的技能链接到以下目录：
- `~/.claude/skills`
- `${CODEX_HOME:-~/.codex}/skills`

这样本地 Agent 就可以直接发现并使用这些技能。

### 3. 直接在仓库中引用技能

如果你在支持 Skills 的 Agent 环境里工作，可以直接引用对应目录下的 `SKILL.md`，或者让 Agent 根据任务自动触发。

## 编写约定

每个技能目录通常包含：
- `SKILL.md`：技能元数据和主说明
- `scripts/`：可执行辅助脚本
- `references/`：按需加载的参考资料
- `assets/`：模板、页面或其他资源文件

一个最小技能通常长这样：

```md
---
name: example-skill
description: 说明这个技能做什么，以及何时触发。
---

# Example Skill

这里写工作流、规则、输出格式和示例。
```

## 第三方来源

本仓库中的部分技能不是完全原创，而是基于公开项目进行适配、裁剪或扩展。

第三方来源、使用位置和许可证说明见：
- [THIRD_PARTY.md](./THIRD_PARTY.md)

如果某个技能目录内额外附带许可证文件，应一并保留，不要删除。

## 维护建议

新增或改写技能时，建议同步维护以下内容：
- 在对应 `SKILL.md` 中补充 `Attribution` 段落（如果引用了第三方内容）
- 在 `THIRD_PARTY.md` 中登记来源、作者、许可证和影响路径
- 如果带有脚本或模板，尽量与技能放在同一目录下
- 新增技能后可运行 `./scripts/link-skills.sh` 更新本地软链接
