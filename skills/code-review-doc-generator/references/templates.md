# 评审文档模板

> 此文件包含评审文档的 YAML frontmatter 和 Markdown 正文模板。在 Phase 5 生成文档时使用。

---

## YAML 统计区块模板

文档开头必须包含以下 YAML frontmatter，使用 `---` 包裹：

```yaml
---
review_id: "CR-YYYYMMDD-NNN"
reviewer:
  name: "[自动获取]"
  email: "[自动获取]"
timestamp: "YYYY-MM-DDTHH:mm:ss+08:00"
vcs_type: "git|svn"
project: "[项目分类]"
module: "[功能模块]"

# 代码变更统计
code_changes:
  files: N
  additions: N
  deletions: N
  total_lines: N

# 评审轮次
review_rounds: N

# 多维效率指标
metrics:
  # 代码评审信息统计
  review_time_efficiency:
    change_size: "small|medium|large|xlarge"
    total_lines: N
    time_base_per_line: N           # 用时基数（分钟/行）
    estimated_manual_minutes: N      # 预估人工评审耗时
    ai_review_minutes: N             # AI实际评审耗时
    time_saved_minutes: N            # 节省时间
    efficiency_gain: "N%"            # 代码评审提效
  
  # 问题摘出数统计
  issues:
    total: N
    critical: N
    major: N
    minor: N
    suggestion: N
    density_per_100_lines: "N"
    fixed: N
    remaining: N
    fix_rate: "N%"
  
  # 代码质量维度
  quality:
    complexity_score: N        # 1-10分
    maintainability_score: N   # 1-10分
    security_score: N          # 1-10分
  
  # 开发效率（如适用）
  development:
    is_ai_assisted: true|false
    ai_dev_hours: N
    estimated_manual_dev_hours: N
    dev_efficiency_gain: "N%"

# 问题详细记录（用于后续分析）
issue_records:
  - id: 1
    severity: critical|major|minor|suggestion
    status: fixed|remaining
    description: "..."
    file: "..."
    line: N

# 扩展字段（预留）
extended:
  test_coverage_change: "N%"
  performance_impact: "positive|negative|neutral"
  breaking_changes: true|false
  dependencies_added: N
  dependencies_removed: N
---
```

### 字段约束说明

| 字段 | 约束 |
|------|------|
| `review_id` | 格式 `CR-YYYYMMDD-NNN`，NNN 为自增序号 |
| `change_size` | 枚举：`small`(<100行), `medium`(100-500), `large`(500-1000), `xlarge`(>1000) |
| `efficiency_gain` | 百分比字符串，如 `"85%"` |
| `complexity_score` | 整数 1-10，越高越简洁 |
| `maintainability_score` | 整数 1-10，越高越易维护 |
| `security_score` | 整数 1-10，越高越安全 |
| `severity` | 枚举：`critical`, `major`, `minor`, `suggestion` |
| `status` | 枚举：`fixed`, `remaining` |

---

## Markdown 正文模板

```markdown
# 代码评审 - {module} ({date})

**评审ID**: {review_id} | **评审人**: {name} | **时间**: {timestamp}
**VCS**: {vcs} | **评审轮次**: {rounds}

---

## 变更概览

**{files}** 个文件 | **+{add}** / **-{del}** 行

## 问题清单

### 严重问题 ({critical_count})

1. **{标题}**
   - 位置：`{file}:{line}`
   - 状态：{已修复/待修复}
   - 描述：{description}
   - 建议：{suggestion}

### 主要问题 ({major_count})
...

### 次要问题 ({minor_count})
...

### 改进建议 ({suggestion_count})
...

---

## 效率指标

### 代码评审信息统计

| 指标 | 数值 |
|-----|-----:|
| 代码规模 | {size_type}（{total_lines}行） |
| 用时基数 | {time_base} 分钟/行 |
| 人工评审耗时（代码规模*用时基数） | {manual_minutes} 分钟 |
| AI评审耗时 | {ai_minutes} 分钟 |
| 节省时间 | {saved_minutes} 分钟 |
| **代码评审提效** | **{time_gain}%** |

### 问题摘出数统计
| 指标 | 数值 |
|-----|-----:|
| AI问题摘出数 | {total} 个 |
| 问题密度 | {density}/100行 |
| 已采纳问题数 | {fixed} 个 |
| 已采纳问题率 | {fix_rate}% |

### 代码质量
| 指标 | 评分 |
|-----|-----:|
| 复杂度 | {complexity}/10 |
| 可维护性 | {maintainability}/10 |
| 安全性 | {security}/10 |

{AI开发效率区块（如适用）}

---

*文档由AI自动生成*
```

---

## 文档命名规则

```
存储目录：[项目根目录]/Review/
命名规则：Review/{项目}_AI代码评审_{评审人}.md
```

文件名仅包含三部分：`{项目}`、`AI代码评审`、`{评审人}`。不能添加模块名、函数名、评审轮次等额外信息。

**正确示例：**
- `Review/3DSDK_AI代码评审_张三.md`
- `Review/2D客户端_AI代码评审_李四.md`

**错误示例：**
- `Review/3DSDK_AI代码评审_张三_createBuffer函数.md`（含函数名）
- `Review/3DSDK_AI代码评审_张三_二次评审.md`（含评审轮次）
- `Review/2D客户端_AI代码评审_李四_登录模块.md`（含模块名）
