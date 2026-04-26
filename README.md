# Gemini CLI Personal Skills 🚀

这个仓库用于存储和管理我个人定制的 **Gemini CLI** 技能（Skills）。这些技能旨在扩展 Gemini CLI 的能力，通过预定义的专家级工作流来自动化复杂的开发、系统管理和媒体管理任务。

## 🛠 已包含的技能 (Available Skills)

| 技能名称 | 描述 | 适用场景 |
| :--- | :--- | :--- |
| [**Media Library Organizer**](./media-library-organizer/SKILL.md) | 深度清理并规范化影视库结构。 | 整理下载的电影/剧集，Plex/Jellyfin 适配。 |

---

## 🚀 如何使用 (How to Use)

### 1. 直接加载本地技能
在 Gemini CLI 任务中，你可以通过告知 Agent 查阅当前目录下的技能文件来激活它：

> "请按照当前目录下的 `media-library-organizer.md` 逻辑帮我检查文件夹。"

### 2. 作为全局技能引用
如果你希望在任何工作区都能调用，可以将这些技能文件放入你的 Gemini 配置目录或通过 GitHub URL 告知 Agent 阅读。

---

## 📂 技能详情 (Skill Details)

### 🎬 Media Library Organizer
这是影视库管理的“瑞士军刀”，主要解决以下痛点：
- **乱码修复**：通过 Python 稳健处理包含 `[]`、中文字符或特殊符号的文件名。
- **结构合并**：自动识别并将分散的 `Season X` 文件夹合并到统一的剧集主目录下。
- **OMDb 适配**：将文件名转换为标准的 `Name (Year)` 纯英文格式。
- **深度清理**：一键移除 `.torrent`、广告文本、分卷修复包等所有非媒体垃圾文件。

---

## ✍️ 贡献与开发 (Development)
每个技能文件都遵循以下标准格式：
```markdown
---
name: skill-name
description: 技能描述
---
# 技能指令
详细的工作流、准则和示例。
```

## 📜 许可证
MIT License
