#!/usr/bin/env python3
"""
评审文档 YAML Frontmatter 校验脚本

用法:
    python validate_yaml.py <文档路径>          # 校验单个文档
    python validate_yaml.py --dir Review/       # 批量校验目录下所有文档
    python validate_yaml.py --all               # 校验 Review/ 下所有文档

退出码:
    0 - 全部通过
    1 - 存在校验错误
    2 - 文件不存在或无法读取
"""

import argparse
import os
import re
import sys
from datetime import datetime


# ─── 常量定义 ────────────────────────────────────────────────

VALID_CHANGE_SIZES = {"small", "medium", "large", "xlarge"}
VALID_SEVERITIES = {"critical", "major", "minor", "suggestion"}
VALID_STATUSES = {"fixed", "remaining"}
VALID_VCS_TYPES = {"git", "svn"}
VALID_PERFORMANCE_IMPACTS = {"positive", "negative", "neutral"}

SCORE_RANGE = range(1, 11)  # 1-10

REVIEW_ID_PATTERN = re.compile(r"^CR-\d{8}-\d{3}$")
TIMESTAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+08:00$")
FILENAME_PATTERN = re.compile(r"^Review/[^_]+_AI代码评审_[^_]+\.md$")


# ─── YAML 提取 ───────────────────────────────────────────────

def extract_yaml_frontmatter(filepath: str) -> tuple[str, int]:
    """从 Markdown 文件中提取 YAML frontmatter。

    Returns:
        (yaml_text, start_line) - YAML 文本和起始行号
    """
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if not lines or not lines[0].strip().startswith("---"):
        return ("", 0)

    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        return ("", 0)

    yaml_text = "".join(lines[1:end_idx])
    return (yaml_text, 2)  # YAML 内容从第2行开始


def parse_yaml_simple(yaml_text: str) -> dict:
    """简易 YAML 解析器，将 YAML 文本解析为嵌套字典。

    支持：标量、嵌套对象、对象列表（每项以 - 开头后跟缩进的键值对）。
    不依赖第三方库。

    列表检测策略：当 key: 后值为空时，先创建 dict 占位；后续遇到
    同缩进级别的 "- " 时，自动将占位 dict 转换为 list。
    """
    lines = yaml_text.split("\n")
    result: dict = {}
    stack: list[tuple[dict | list, int]] = [(result, -1)]

    for raw_line in lines:
        stripped = raw_line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))

        # ── 列表项：以 "- " 开头 ──
        if stripped.startswith("- "):
            # 弹出到列表项的父级
            while len(stack) > 1 and stack[-1][1] >= indent:
                stack.pop()

            container, container_indent = stack[-1]

            # 如果容器是 dict 占位，需要将其转换为 list
            if isinstance(container, dict) and len(stack) >= 2:
                parent_dict, _ = stack[-2]
                if isinstance(parent_dict, dict):
                    # 找到 parent 中指向此占位 dict 的 key
                    for k, v in parent_dict.items():
                        if v is container:
                            new_list: list = []
                            parent_dict[k] = new_list
                            container = new_list
                            stack[-1] = (new_list, container_indent)
                            break

            content = stripped[2:].strip()
            if "  #" in content:
                content = content[: content.index("  #")].strip()

            if not isinstance(container, list):
                continue

            if ":" in content:
                # 对象列表项: "- key: value"
                key, _, val = content.partition(":")
                key = key.strip()
                val = val.strip()
                new_obj: dict = {}
                if val:
                    new_obj[key] = _parse_scalar(val)
                container.append(new_obj)
                stack.append((new_obj, indent))
            else:
                # 标量列表项: "- value"
                container.append(_parse_scalar(content))
            continue

        # ── 键值对 ──
        if ":" not in stripped:
            continue

        # 弹出比当前缩进更深或同级的栈帧（列表内的对象延续除外）
        while len(stack) > 1 and stack[-1][1] >= indent:
            stack.pop()

        container, _ = stack[-1]

        # 确保容器是 dict
        if not isinstance(container, dict):
            for s, _ in reversed(stack):
                if isinstance(s, dict):
                    container = s
                    break
        if not isinstance(container, dict):
            continue

        # 移除行内注释
        if "  #" in stripped:
            comment_idx = stripped.find("  #")
            key_part = stripped[:comment_idx]
            if ":" not in key_part:
                stripped = key_part.rstrip() + ": ''"
            else:
                stripped = key_part.rstrip()

        key, _, val = stripped.partition(":")
        key = key.strip()
        val = val.strip()

        if val == "":
            # 空值：创建 dict 占位，后续遇到 "- " 时自动转为 list
            new_dict: dict = {}
            container[key] = new_dict
            stack.append((new_dict, indent))
        elif val.startswith("[") and val.endswith("]"):
            items = [x.strip().strip("'\"") for x in val[1:-1].split(",") if x.strip()]
            container[key] = [_parse_scalar(i) for i in items]
        else:
            container[key] = _parse_scalar(val)

    return result


def _parse_scalar(val: str):
    """解析 YAML 标量值。"""
    if not val:
        return val
    # 布尔
    if val.lower() in ("true", "yes"):
        return True
    if val.lower() in ("false", "no"):
        return False
    # null
    if val.lower() in ("null", "~", ""):
        return None
    # 整数
    try:
        return int(val)
    except ValueError:
        pass
    # 浮点数
    try:
        return float(val)
    except ValueError:
        pass
    # 字符串（去掉引号）
    if len(val) >= 2 and val[0] == val[-1] and val[0] in ('"', "'"):
        return val[1:-1]
    return val


# ─── 校验器 ──────────────────────────────────────────────────

class ValidationError:
    def __init__(self, field: str, message: str, line: int = 0):
        self.field = field
        self.message = message
        self.line = line

    def __str__(self):
        loc = f" (line ~{self.line})" if self.line else ""
        return f"  ✗ {self.field}: {self.message}{loc}"


class YamlValidator:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.errors: list[ValidationError] = []
        self.warnings: list[str] = []

    def validate(self) -> bool:
        """执行完整校验，返回是否通过。"""
        yaml_text, yaml_start = extract_yaml_frontmatter(self.filepath)

        if not yaml_text:
            self.errors.append(ValidationError(
                "frontmatter", "未找到 YAML frontmatter (文档开头缺少 --- 包裹)"
            ))
            return False

        try:
            data = parse_yaml_simple(yaml_text)
        except Exception as e:
            self.errors.append(ValidationError(
                "frontmatter", f"YAML 解析失败: {e}"
            ))
            return False

        # 逐项校验
        self._check_required_fields(data)
        self._check_review_id(data)
        self._check_reviewer(data)
        self._check_timestamp(data)
        self._check_vcs_type(data)
        self._check_project_and_module(data)
        self._check_code_changes(data)
        self._check_review_rounds(data)
        self._check_metrics(data.get("metrics", {}))
        self._check_issue_records(data.get("issue_records", []))
        self._check_extended(data.get("extended", {}))
        self._check_filename()

        return len(self.errors) == 0

    # ── 各字段校验 ──

    def _check_required_fields(self, data: dict):
        required = ["review_id", "reviewer", "timestamp", "vcs_type",
                    "project", "module", "code_changes", "review_rounds", "metrics"]
        for field in required:
            if field not in data:
                self.errors.append(ValidationError(field, "缺少必填字段"))

    def _check_review_id(self, data: dict):
        rid = data.get("review_id", "")
        if not rid:
            return
        if not REVIEW_ID_PATTERN.match(str(rid)):
            self.errors.append(ValidationError(
                "review_id",
                f"格式错误，应为 CR-YYYYMMDD-NNN，当前值: {rid}"
            ))
        else:
            # 校验日期是否合理
            date_part = str(rid)[3:11]
            try:
                dt = datetime.strptime(date_part, "%Y%m%d")
                if dt > datetime.now():
                    self.warnings.append(f"review_id 日期 {date_part} 在未来")
            except ValueError:
                self.errors.append(ValidationError(
                    "review_id", f"日期部分 {date_part} 无效"
                ))

    def _check_reviewer(self, data: dict):
        reviewer = data.get("reviewer", {})
        if not isinstance(reviewer, dict):
            self.errors.append(ValidationError("reviewer", "应为对象，包含 name 和 email"))
            return
        if "name" not in reviewer or not reviewer["name"]:
            self.errors.append(ValidationError("reviewer.name", "缺失或为空"))
        if "email" not in reviewer or not reviewer["email"]:
            self.errors.append(ValidationError("reviewer.email", "缺失或为空"))
        elif "@" not in str(reviewer.get("email", "")):
            self.errors.append(ValidationError(
                "reviewer.email", f"格式无效: {reviewer['email']}"
            ))

    def _check_timestamp(self, data: dict):
        ts = data.get("timestamp", "")
        if not ts:
            return
        if not TIMESTAMP_PATTERN.match(str(ts)):
            self.errors.append(ValidationError(
                "timestamp",
                f"格式错误，应为 YYYY-MM-DDTHH:mm:ss+08:00，当前值: {ts}"
            ))

    def _check_vcs_type(self, data: dict):
        vcs = data.get("vcs_type", "")
        if vcs and vcs not in VALID_VCS_TYPES:
            self.errors.append(ValidationError(
                "vcs_type", f"无效值 '{vcs}'，应为 git 或 svn"
            ))

    def _check_project_and_module(self, data: dict):
        for field in ("project", "module"):
            val = data.get(field, "")
            if not val:
                self.errors.append(ValidationError(field, "缺失或为空"))

    def _check_code_changes(self, data: dict):
        cc = data.get("code_changes", {})
        if not isinstance(cc, dict):
            self.errors.append(ValidationError("code_changes", "应为对象"))
            return
        for field in ("files", "additions", "deletions", "total_lines"):
            if field not in cc:
                self.errors.append(ValidationError(f"code_changes.{field}", "缺失"))
            elif not isinstance(cc[field], (int, float)):
                self.errors.append(ValidationError(
                    f"code_changes.{field}", f"应为数字，当前: {cc[field]}"
                ))
        # total_lines 应等于 additions + deletions
        if all(k in cc and isinstance(cc[k], (int, float))
               for k in ("additions", "deletions", "total_lines")):
            expected = cc["additions"] + cc["deletions"]
            if cc["total_lines"] != expected:
                self.warnings.append(
                    f"code_changes.total_lines ({cc['total_lines']}) "
                    f"不等于 additions + deletions ({expected})"
                )

    def _check_review_rounds(self, data: dict):
        rounds = data.get("review_rounds")
        if rounds is None:
            return
        if not isinstance(rounds, int) or rounds < 1:
            self.errors.append(ValidationError(
                "review_rounds", f"应为 >=1 的整数，当前: {rounds}"
            ))

    def _check_metrics(self, metrics: dict):
        if not metrics:
            self.errors.append(ValidationError("metrics", "缺失"))
            return

        # review_time_efficiency
        rte = metrics.get("review_time_efficiency", {})
        if rte:
            for field in ("change_size", "total_lines", "estimated_manual_minutes",
                          "ai_review_minutes", "time_saved_minutes", "efficiency_gain"):
                if field not in rte:
                    self.errors.append(ValidationError(
                        f"metrics.review_time_efficiency.{field}", "缺失"
                    ))
            if rte.get("change_size") not in VALID_CHANGE_SIZES:
                self.errors.append(ValidationError(
                    "metrics.review_time_efficiency.change_size",
                    f"无效值 '{rte.get('change_size')}'"
                ))
            gain = str(rte.get("efficiency_gain", ""))
            if gain:
                if not gain.endswith("%"):
                    self.errors.append(ValidationError(
                        "metrics.review_time_efficiency.efficiency_gain",
                        f"应以 % 结尾，当前: {gain}"
                    ))
                else:
                    # 校验 % 前是否为有效数字
                    num_part = gain[:-1]
                    try:
                        val = float(num_part)
                        if val < 0:
                            self.warnings.append(
                                f"metrics.review_time_efficiency.efficiency_gain "
                                f"为负值 ({gain})，请确认"
                            )
                    except ValueError:
                        self.errors.append(ValidationError(
                            "metrics.review_time_efficiency.efficiency_gain",
                            f"不是有效数字，当前: {gain}"
                        ))

        # issues
        issues = metrics.get("issues", {})
        if issues:
            for field in ("total", "critical", "major", "minor", "suggestion",
                          "fixed", "remaining"):
                if field not in issues:
                    self.errors.append(ValidationError(
                        f"metrics.issues.{field}", "缺失"
                    ))
            # 校验计数一致性
            sevs = ["critical", "major", "minor", "suggestion"]
            if all(k in issues for k in sevs + ["total"]):
                sev_sum = sum(issues.get(s, 0) for s in sevs)
                if issues["total"] != sev_sum:
                    self.warnings.append(
                        f"metrics.issues.total ({issues['total']}) "
                        f"不等于严重级别之和 ({sev_sum})"
                    )
            if all(k in issues for k in ("fixed", "remaining", "total")):
                fr_sum = issues["fixed"] + issues["remaining"]
                if issues["total"] != fr_sum:
                    self.warnings.append(
                        f"metrics.issues.total ({issues['total']}) "
                        f"不等于 fixed + remaining ({fr_sum})"
                    )

        # quality
        quality = metrics.get("quality", {})
        if quality:
            for field in ("complexity_score", "maintainability_score", "security_score"):
                score = quality.get(field)
                if score is None:
                    self.errors.append(ValidationError(
                        f"metrics.quality.{field}", "缺失"
                    ))
                elif not isinstance(score, int) or score not in SCORE_RANGE:
                    self.errors.append(ValidationError(
                        f"metrics.quality.{field}",
                        f"应为 1-10 的整数，当前: {score}"
                    ))

        # development (可选)
        dev = metrics.get("development", {})
        if dev and dev.get("is_ai_assisted"):
            for field in ("ai_dev_hours", "estimated_manual_dev_hours", "dev_efficiency_gain"):
                if field not in dev:
                    self.errors.append(ValidationError(
                        f"metrics.development.{field}",
                        "AI辅助时此字段必填"
                    ))
            # 校验 dev_efficiency_gain 格式
            dev_gain = str(dev.get("dev_efficiency_gain", ""))
            if dev_gain:
                if not dev_gain.endswith("%"):
                    self.errors.append(ValidationError(
                        "metrics.development.dev_efficiency_gain",
                        f"应以 % 结尾，当前: {dev_gain}"
                    ))
                else:
                    try:
                        float(dev_gain[:-1])
                    except ValueError:
                        self.errors.append(ValidationError(
                            "metrics.development.dev_efficiency_gain",
                            f"不是有效数字，当前: {dev_gain}"
                        ))

    def _check_issue_records(self, records: list):
        if not records:
            return
        if not isinstance(records, list):
            self.errors.append(ValidationError("issue_records", "应为数组"))
            return
        for i, record in enumerate(records):
            prefix = f"issue_records[{i}]"
            if not isinstance(record, dict):
                self.errors.append(ValidationError(prefix, "应为对象"))
                continue
            for field in ("id", "severity", "status", "description", "file"):
                if field not in record:
                    self.errors.append(ValidationError(f"{prefix}.{field}", "缺失"))
            sev = record.get("severity")
            if sev and sev not in VALID_SEVERITIES:
                self.errors.append(ValidationError(
                    f"{prefix}.severity",
                    f"无效值 '{sev}'，应为 {VALID_SEVERITIES}"
                ))
            st = record.get("status")
            if st and st not in VALID_STATUSES:
                self.errors.append(ValidationError(
                    f"{prefix}.status",
                    f"无效值 '{st}'，应为 {VALID_STATUSES}"
                ))

    def _check_extended(self, extended: dict):
        if not extended:
            return
        pi = extended.get("performance_impact")
        if pi and pi not in VALID_PERFORMANCE_IMPACTS:
            self.errors.append(ValidationError(
                "extended.performance_impact",
                f"无效值 '{pi}'，应为 {VALID_PERFORMANCE_IMPACTS}"
            ))

    def _check_filename(self):
        """校验文档命名规范：文件名不含模块名/函数名/评审轮次。"""
        # 构建相对于项目根目录的路径
        # 简单策略：取路径中 Review/ 之后的部分
        path = self.filepath
        review_idx = path.find("Review/")
        if review_idx >= 0:
            rel = path[review_idx:]
        else:
            rel = self.filename

        # 检查是否包含多余的 _ 分段（正常只有 项目_AI代码评审_评审人.md）
        base = os.path.basename(rel)
        name_no_ext = base.replace(".md", "")

        # 预期格式: {项目}_AI代码评审_{评审人}
        # 所以应该有恰好 3 个部分，由 _AI代码评审_ 连接
        if "_AI代码评审_" not in name_no_ext:
            self.errors.append(ValidationError(
                "filename",
                f"命名格式错误，应为 {{项目}}_AI代码评审_{{评审人}}.md，当前: {base}"
            ))
            return

        # 记录已有的额外检查
        parts = name_no_ext.split("_AI代码评审_")
        if len(parts) != 2:
            self.errors.append(ValidationError(
                "filename",
                f"命名格式错误，'_AI代码评审_' 应恰好出现一次，当前: {base}"
            ))

    def print_report(self):
        """打印校验报告。"""
        print(f"\n{'='*60}")
        print(f"校验文件: {self.filepath}")
        print(f"{'='*60}")

        if not self.errors and not self.warnings:
            print("✅ 全部校验通过！")
            return

        if self.errors:
            print(f"\n❌ 发现 {len(self.errors)} 个错误:\n")
            for err in self.errors:
                print(err)

        if self.warnings:
            print(f"\n⚠️  发现 {len(self.warnings)} 个警告:\n")
            for w in self.warnings:
                print(f"  ⚠ {w}")

        print()


# ─── 主入口 ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="评审文档 YAML Frontmatter 校验工具"
    )
    parser.add_argument(
        "path", nargs="?",
        help="要校验的文档路径"
    )
    parser.add_argument(
        "--dir", "-d",
        help="批量校验指定目录下所有 .md 文件"
    )
    parser.add_argument(
        "--all", "-a", action="store_true",
        help="校验 Review/ 目录下所有 .md 文件"
    )
    args = parser.parse_args()

    files = []

    if args.all:
        review_dir = "Review"
        if not os.path.isdir(review_dir):
            print(f"错误: Review/ 目录不存在", file=sys.stderr)
            sys.exit(2)
        files = sorted([
            os.path.join(review_dir, f)
            for f in os.listdir(review_dir)
            if f.endswith(".md")
        ])
    elif args.dir:
        if not os.path.isdir(args.dir):
            print(f"错误: 目录 '{args.dir}' 不存在", file=sys.stderr)
            sys.exit(2)
        files = sorted([
            os.path.join(args.dir, f)
            for f in os.listdir(args.dir)
            if f.endswith(".md")
        ])
    elif args.path:
        if not os.path.isfile(args.path):
            print(f"错误: 文件 '{args.path}' 不存在", file=sys.stderr)
            sys.exit(2)
        files = [args.path]
    else:
        # 默认校验 Review/ 目录
        review_dir = "Review"
        if not os.path.isdir(review_dir):
            print("用法: python validate_yaml.py <文档路径>", file=sys.stderr)
            print("      python validate_yaml.py --dir <目录>", file=sys.stderr)
            print("      python validate_yaml.py --all", file=sys.stderr)
            sys.exit(2)
        files = sorted([
            os.path.join(review_dir, f)
            for f in os.listdir(review_dir)
            if f.endswith(".md")
        ])

    if not files:
        print("未找到 .md 文档", file=sys.stderr)
        sys.exit(2)

    total_errors = 0
    total_passed = 0

    for filepath in files:
        validator = YamlValidator(filepath)
        if validator.validate():
            total_passed += 1
        else:
            total_errors += len(validator.errors)
        validator.print_report()

    # 汇总
    print(f"{'='*60}")
    print(f"汇总: {len(files)} 个文件, {total_passed} 通过, {total_errors} 个错误")
    print(f"{'='*60}")

    sys.exit(0 if total_errors == 0 else 1)


if __name__ == "__main__":
    main()
