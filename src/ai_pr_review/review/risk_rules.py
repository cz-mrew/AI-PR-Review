from ..github.models import FileChange
from .models import Confidence, ReviewRisk, RiskCategory, RiskLevel, RiskSource

_PATH_RULES: list[tuple[str, RiskLevel, RiskCategory, str, str]] = [
    (
        "auth", RiskLevel.HIGH, RiskCategory.SECURITY,
        "认证/授权相关文件变更",
        "请重点检查认证逻辑的正确性和安全性，确保没有权限绕过或会话管理问题",
    ),
    (
        "authentication", RiskLevel.HIGH, RiskCategory.SECURITY,
        "认证模块文件变更",
        "请重点检查认证流程是否完整，防止未授权访问",
    ),
    (
        "permission", RiskLevel.HIGH, RiskCategory.SECURITY,
        "权限相关文件变更",
        "请检查权限控制的粒度和正确性，确保不存在水平或垂直越权",
    ),
    (
        "role", RiskLevel.HIGH, RiskCategory.SECURITY,
        "角色管理相关文件变更",
        "请检查角色分配和权限继承逻辑是否正确",
    ),
    (
        "config", RiskLevel.MEDIUM, RiskCategory.MAINTAINABILITY,
        "配置文件变更",
        "请确认配置项变更是否向后兼容，是否需要同步更新文档和部署脚本",
    ),
    (
        "settings", RiskLevel.MEDIUM, RiskCategory.MAINTAINABILITY,
        "设置文件变更",
        "请确认设置项是否存在环境差异，各环境是否需要同步更新",
    ),
    (
        "migration", RiskLevel.HIGH, RiskCategory.LOGIC,
        "数据库迁移文件变更",
        "请检查迁移脚本是否正确、是否可回滚、是否影响现有数据",
    ),
    (
        "migrate", RiskLevel.HIGH, RiskCategory.LOGIC,
        "数据库迁移相关文件变更",
        "请检查迁移操作对生产数据的影响，确保有回滚方案",
    ),
    (
        "payment", RiskLevel.HIGH, RiskCategory.LOGIC,
        "支付相关文件变更",
        "请重点检查金额计算、事务一致性和异常处理，建议增加测试覆盖",
    ),
    (
        "billing", RiskLevel.HIGH, RiskCategory.LOGIC,
        "账单相关文件变更",
        "请检查计费逻辑的准确性，确认边界条件处理正确",
    ),
    (
        "security", RiskLevel.HIGH, RiskCategory.SECURITY,
        "安全相关文件变更",
        "请全面审查安全实现，确认没有引入新的安全漏洞",
    ),
]


def detect_path_risks(files: list[FileChange]) -> list[ReviewRisk]:
    risks: list[ReviewRisk] = []
    for f in files:
        path_lower = f.filename.lower()
        for keyword, level, category, message, suggestion in _PATH_RULES:
            if keyword in path_lower:
                risks.append(ReviewRisk(
                    file=f.filename,
                    risk_level=level,
                    source=RiskSource.RULE,
                    category=category,
                    message=message,
                    suggestion=suggestion,
                ))
                break
    return risks


def detect_rule_based_risks(files: list[FileChange]) -> list[ReviewRisk]:
    all_risks = (
        detect_path_risks(files)
        + detect_keyword_risks(files)
        + detect_scale_risks(files)
    )

    seen: set[tuple[str, str, str]] = set()
    deduped: list[ReviewRisk] = []
    for r in all_risks:
        key = (r.file, r.category.value, r.message)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)

    return deduped


_KEYWORD_RULES: list[tuple[str, RiskLevel, RiskCategory, str, str]] = [
    (
        "exec(", RiskLevel.HIGH, RiskCategory.SECURITY,
        "检测到 exec() 调用，存在代码注入风险",
        "避免使用 exec()，改用更安全的替代方案。如确需动态执行，请严格校验输入",
    ),
    (
        "eval(", RiskLevel.HIGH, RiskCategory.SECURITY,
        "检测到 eval() 调用，存在代码注入风险",
        "避免使用 eval()，改用 ast.literal_eval 或其他安全解析方式",
    ),
    (
        "shell=True", RiskLevel.HIGH, RiskCategory.SECURITY,
        "检测到 shell=True 参数，存在命令注入风险",
        "避免使用 shell=True，使用列表形式传递参数以减少注入风险",
    ),
    (
        "subprocess", RiskLevel.MEDIUM, RiskCategory.SECURITY,
        "检测到 subprocess 调用，需确认输入安全性",
        "请检查 subprocess 调用的参数是否来自外部输入，避免命令注入",
    ),
    (
        "password", RiskLevel.MEDIUM, RiskCategory.SECURITY,
        "检测到 password 关键词，需确认密码处理方式",
        "请检查密码是否被硬编码、是否使用安全存储、是否在日志中泄露",
    ),
    (
        "secret", RiskLevel.HIGH, RiskCategory.SECURITY,
        "检测到 secret 关键词，需确认密钥处理方式",
        "请检查密钥是否被硬编码，应使用环境变量或密钥管理服务",
    ),
    (
        "token", RiskLevel.MEDIUM, RiskCategory.SECURITY,
        "检测到 token 关键词，需确认令牌处理方式",
        "请检查令牌是否安全存储和传输，避免在日志或错误信息中泄露",
    ),
    (
        "drop table", RiskLevel.HIGH, RiskCategory.LOGIC,
        "检测到 DROP TABLE 语句，存在数据破坏风险",
        "请确认该操作是否为预期行为，是否在事务中执行，是否有备份和回滚方案",
    ),
    (
        "delete from", RiskLevel.MEDIUM, RiskCategory.LOGIC,
        "检测到 DELETE FROM 语句，需确认删除逻辑",
        "请检查删除条件是否正确，是否可能导致意外数据丢失",
    ),
    (
        "chmod 777", RiskLevel.HIGH, RiskCategory.SECURITY,
        "检测到 chmod 777，存在权限过度开放风险",
        "避免使用 777 权限，使用最小必要权限原则（如 644 或 755）",
    ),
]


def detect_keyword_risks(files: list[FileChange]) -> list[ReviewRisk]:
    risks: list[ReviewRisk] = []
    for f in files:
        patch = f.patch
        if not patch:
            continue

        added_lines = _extract_added_lines(patch)
        if not added_lines:
            continue

        matched_keywords: set[str] = set()
        for keyword, level, category, message, suggestion in _KEYWORD_RULES:
            if keyword in matched_keywords:
                continue
            kw_lower = keyword.lower()
            for line in added_lines:
                if kw_lower in line.lower():
                    matched_keywords.add(keyword)
                    risks.append(ReviewRisk(
                        file=f.filename,
                        risk_level=level,
                        source=RiskSource.RULE,
                        category=category,
                        message=f"{message}（命中关键词：{keyword}）",
                        suggestion=suggestion,
                    ))
                    break

    return risks


def _extract_added_lines(patch: str) -> list[str]:
    return [line[1:] for line in patch.split("\n") if line.startswith("+") and not line.startswith("+++")]


def detect_scale_risks(files: list[FileChange]) -> list[ReviewRisk]:
    risks: list[ReviewRisk] = []

    if not files:
        return risks

    total_changes = sum(f.changes for f in files)
    file_count = len(files)

    if file_count > 50:
        risks.append(ReviewRisk(
            file="",
            risk_level=RiskLevel.HIGH,
            source=RiskSource.RULE,
            category=RiskCategory.SCALE,
            message=f"PR 变更文件数 ({file_count}) 超过 50 个，Review 成本高",
            suggestion="强烈建议将 PR 拆分为多个较小的、功能独立的 PR，降低回归风险",
            confidence=Confidence.HIGH,
        ))
    elif file_count > 20:
        risks.append(ReviewRisk(
            file="",
            risk_level=RiskLevel.MEDIUM,
            source=RiskSource.RULE,
            category=RiskCategory.SCALE,
            message=f"PR 变更文件数 ({file_count}) 超过 20 个，建议关注 Review 范围",
            suggestion="建议考虑是否可以拆分为多个 PR，以便更专注地审查每个变更",
            confidence=Confidence.MEDIUM,
        ))

    if total_changes > 1000:
        risks.append(ReviewRisk(
            file="",
            risk_level=RiskLevel.HIGH,
            source=RiskSource.RULE,
            category=RiskCategory.SCALE,
            message=f"PR 总变更行数 ({total_changes}) 超过 1000 行，回归风险较高",
            suggestion="强烈建议将 PR 拆分为多个较小的提交，降低测试和审查难度",
            confidence=Confidence.HIGH,
        ))

    for f in files:
        if f.changes > 300:
            risks.append(ReviewRisk(
                file=f.filename,
                risk_level=RiskLevel.HIGH,
                source=RiskSource.RULE,
                category=RiskCategory.SCALE,
                message=f"文件 {f.filename} 变更行数 ({f.changes}) 超过 300 行",
                suggestion="建议将大文件的变更拆分为多次提交，或说明为何需要一次性修改大量代码",
                confidence=Confidence.HIGH,
            ))

    return risks
