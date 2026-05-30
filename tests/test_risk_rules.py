from ai_pr_review.github.models import FileChange, FileStatus
from ai_pr_review.review.models import RiskCategory, RiskLevel, RiskSource
from ai_pr_review.review.risk_rules import detect_path_risks


class TestDetectPathRisks:
    def test_empty_files(self):
        assert detect_path_risks([]) == []

    def test_auth_file_flagged(self):
        files = [
            FileChange(
                filename="src/auth/login.py",
                status=FileStatus.MODIFIED,
                additions=5, deletions=1, changes=6, patch="dummy",
            )
        ]
        risks = detect_path_risks(files)
        assert len(risks) == 1
        r = risks[0]
        assert r.file == "src/auth/login.py"
        assert r.risk_level == RiskLevel.HIGH
        assert r.source == RiskSource.RULE
        assert r.category == RiskCategory.SECURITY

    def test_config_file_medium(self):
        files = [
            FileChange(
                filename="config/settings.yaml",
                status=FileStatus.MODIFIED,
                additions=3, deletions=1, changes=4, patch="dummy",
            )
        ]
        risks = detect_path_risks(files)
        assert len(risks) == 1  # first keyword match per file

    def test_migration_file_high(self):
        files = [
            FileChange(
                filename="migrations/001_add_users.py",
                status=FileStatus.ADDED,
                additions=20, deletions=0, changes=20, patch="dummy",
            )
        ]
        risks = detect_path_risks(files)
        assert len(risks) == 1
        assert risks[0].category == RiskCategory.LOGIC
        assert risks[0].risk_level == RiskLevel.HIGH

    def test_payment_file_flagged(self):
        files = [
            FileChange(
                filename="src/billing/payment.py",
                status=FileStatus.MODIFIED,
                additions=10, deletions=2, changes=12, patch="dummy",
            )
        ]
        risks = detect_path_risks(files)
        assert len(risks) == 1  # first keyword match per file

    def test_no_match_file(self):
        files = [
            FileChange(
                filename="src/utils/helpers.py",
                status=FileStatus.MODIFIED,
                additions=1, deletions=1, changes=2, patch="dummy",
            )
        ]
        risks = detect_path_risks(files)
        assert len(risks) == 0

    def test_security_keyword_match(self):
        files = [
            FileChange(
                filename="middleware/security_middleware.py",
                status=FileStatus.MODIFIED,
                additions=5, deletions=0, changes=5, patch="dummy",
            )
        ]
        risks = detect_path_risks(files)
        assert len(risks) == 1
        assert risks[0].risk_level == RiskLevel.HIGH

    def test_case_insensitive(self):
        files = [
            FileChange(
                filename="src/Auth/Login.py",
                status=FileStatus.MODIFIED,
                additions=5, deletions=1, changes=6, patch="dummy",
            )
        ]
        risks = detect_path_risks(files)
        assert len(risks) == 1
