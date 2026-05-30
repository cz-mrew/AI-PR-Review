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
