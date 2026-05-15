# 项目类型识别映射表

> 此文件包含 Git/SVN 项目类型自动识别规则。在 Phase 1 环境检测时使用。

---

## 可选项目分类

```
[2D客户端, 2DSDK, 3D线激光客户端, 3D线激光SDK, 3D双目SDK, 3D双目客户端, 智能机, 视觉工具, 测开, 其他]
```

---

## Git 项目判断

```bash
git remote show origin
```

| Git Remote URL 关键词 | 项目分类 |
|----------------------|---------|
| `Laser3DSDK.git` | 3D线激光SDK |
| `Laser3DClient.git` | 3D线激光客户端 |
| `MVClient.git` | 2D客户端 |
| `MVSDK.git` | 2DSDK |

---

## SVN 项目判断

```bash
svn info
```

| SVN URL 关键词 | 项目分类 |
|---------------|---------|
| `.../HighPrecision3DMeasure/Volume3D/` | 3D线激光SDK |
| `.../HighPrecision3DMeasure/ProfileViewer` | 3D线激光SDK |
| `.../HighPrecision3DMeasure/StereoCamera/` | 需进一步判断（见下方） |

### SVN 双目项目特殊判断（StereoCamera 仓库）

当 SVN URL 包含 `StereoCamera` 时，按以下规则判断：

1. 检查是否存在 `.ui` 文件或 `QMainWindow`、`QWidget` 等 QT 相关代码 → **3D双目客户端**
2. 否则（纯 SDK/API 导出代码，无 QT 界面代码） → **3D双目SDK**

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
