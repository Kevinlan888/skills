# 项目类型识别映射表

> 此文件包含 Git/SVN 项目类型自动识别规则。在 Phase 1 环境检测时使用。

---

## 可选项目分类

```
[LP, DWSSDK, 读码门, 读码门SDK, 单间分离, 单间分离SDK, AA点胶, 落格追溯IPC, 落格追溯IPC前端, DFS, WPF公共控件, 3D线激光SDK, 其他]
```

---

## Git 项目判断

```bash
git remote show origin
```

| Git Remote URL 关键词 | 项目分类 |
|----------------------|---------|
| `lp-app.git` | LP |
| `dwssdk.git` | DWSSDK |
| `codereaderdoorapp.git` | 读码门 |
| `codereaderdoorsdk.git` | 读码门SDK |
| `divideapp.git` | 单间分离 |
| `dividesdk.git` | 单间分离SDK |
| `aadevice` | AA点胶 |
| `lgzs-app.git` | 落格追溯IPC |
| `lgzs-web.git` | 落格追溯IPC前端 |
| `dfs.git` | DFS |
| `commoncontrols.wpf.git` | WPF公共控件 |

---

## SVN 项目判断

```bash
svn info
```

| SVN URL 关键词 | 项目分类 |
|---------------|---------|
| `.../HighPrecision3DMeasure/Volume3D/` | 3D线激光SDK |
| `.../HighPrecision3DMeasure/ProfileViewer` | 3D线激光SDK |

---

## AI 智能判断规则（兜底）

当以上条件均无法匹配时，根据代码特征推断：

| 代码特征 | 推断分类 |
|---------|---------|
| 包含 QT/WPF/WinForms 界面代码 | 可能是客户端 |
| 包含 SDK/API 导出代码、无界面代码 | 可能是SDK |
| 包含测试框架代码 | 可能是测开 |

---

## VCS 检测

```bash
# 检测顺序
[ -d .git ] && echo "Git"    # 优先检测 Git
[ -d .svn ] && echo "SVN"    # 其次检测 SVN
# 两者都不存在 → 提示用户切换到项目根目录
```

## 发起人信息获取

**Git：**
```bash
git config user.name
git config user.email
```

**SVN：**
```bash
svn auth              # SVN 1.9+
# 或
svn log -l 1 --quiet  # 参考最近提交的作者
```
