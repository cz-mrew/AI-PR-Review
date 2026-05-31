from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class FindingCategory(str, Enum):
    SECURITY = "security"
    LOGIC = "logic"
    PERFORMANCE = "performance"
    BREAKING = "breaking"


class FileStatus(str, Enum):
    ADDED = "added"
    MODIFIED = "modified"
    REMOVED = "removed"
    RENAMED = "renamed"


@dataclass
class DiffLine:
    type: str
    content: str
    old_lineno: int | None = None
    new_lineno: int | None = None


@dataclass
class DiffHunk:
    header: str
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: list[DiffLine] = field(default_factory=list)


@dataclass
class FileChange:
    filename: str
    status: FileStatus
    additions: int
    deletions: int
    changes: int
    patch: str
    language: str | None = None
    hunks: list[DiffHunk] = field(default_factory=list)
    is_binary: bool = False


@dataclass
class GitHubPRUrl:
    owner: str
    repo: str
    pull_number: int


@dataclass
class GitHubPRRef:
    owner: str
    repo: str
    pull_number: int


@dataclass
class GitHubUser:
    login: str
    html_url: str


@dataclass
class GitHubPullRequest:
    number: int
    title: str
    body: str | None
    state: str
    html_url: str
    user: GitHubUser
    base_branch: str
    head_branch: str
    head_sha: str
    created_at: str
    updated_at: str


@dataclass
class GitHubChangedFile:
    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    patch: str | None
    raw_url: str
    blob_url: str


@dataclass
class GitHubCommit:
    sha: str
    message: str
    author_name: str
    author_email: str


@dataclass
class PRInfo:
    title: str
    author: str
    head_sha: str
    base_sha: str
    files_changed: int
    additions: int
    deletions: int
    description: str
    repo_owner: str
    repo_name: str
    pr_number: int
    files: list[FileChange] = field(default_factory=list)


@dataclass
class Finding:
    id: str
    category: FindingCategory
    severity: Severity
    title: str
    file: str
    line_range: str
    description: str
    code_snippet: str
    confidence: float
    cwe_id: str | None = None


@dataclass
class Report:
    pr_url: str
    title: str
    author: str
    head_sha: str
    analyzed_at: str
    files_changed: int
    additions: int
    deletions: int
    summary: str
    risk_level: Severity
    components_affected: list[str] = field(default_factory=list)
    key_files: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    files_analyzed: int = 0
    files_skipped: int = 0
    stats: dict = field(default_factory=dict)
