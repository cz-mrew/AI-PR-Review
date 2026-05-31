from ai_pr_review.github.models import FileChange, FileStatus
from ai_pr_review.review.models import RiskCategory, RiskLevel, RiskSource
from ai_pr_review.review.risk_rules import detect_keyword_risks, detect_path_risks, detect_scale_risks


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


class TestDetectKeywordRisks:
    def test_empty_files(self):
        assert detect_keyword_risks([]) == []

    def test_eval_detected(self):
        files = [
            FileChange(
                filename="src/calc.py",
                status=FileStatus.MODIFIED,
                additions=2, deletions=1, changes=3,
                patch="@@ -1,3 +1,4 @@\n import math\n+result = eval(user_input)\n-return 0\n+return result",
            )
        ]
        risks = detect_keyword_risks(files)
        assert len(risks) == 1
        r = risks[0]
        assert r.file == "src/calc.py"
        assert r.risk_level == RiskLevel.HIGH
        assert r.source == RiskSource.RULE
        assert r.category == RiskCategory.SECURITY
        assert "eval" in r.message

    def test_shell_true_detected(self):
        files = [
            FileChange(
                filename="src/runner.py",
                status=FileStatus.MODIFIED,
                additions=3, deletions=0, changes=3,
                patch="@@ -5,0 +5,3 @@\n+import subprocess\n+subprocess.call(cmd, shell=True)",
            )
        ]
        risks = detect_keyword_risks(files)
        assert len(risks) == 2  # subprocess + shell=True
        categories = {r.category for r in risks}
        assert categories == {RiskCategory.SECURITY}

    def test_secret_keyword(self):
        files = [
            FileChange(
                filename="config.py",
                status=FileStatus.MODIFIED,
                additions=1, deletions=0, changes=1,
                patch="@@ -1,3 +1,4 @@\n+API_SECRET = 'sk-abc123'",
            )
        ]
        risks = detect_keyword_risks(files)
        assert len(risks) == 1
        assert "secret" in risks[0].message.lower()

    def test_no_patch_skipped(self):
        files = [
            FileChange(
                filename="img/logo.png",
                status=FileStatus.ADDED,
                additions=0, deletions=0, changes=0,
                patch="",
                is_binary=True,
            )
        ]
        risks = detect_keyword_risks(files)
        assert len(risks) == 0

    def test_no_keywords_in_patch(self):
        files = [
            FileChange(
                filename="src/clean.py",
                status=FileStatus.MODIFIED,
                additions=2, deletions=1, changes=3,
                patch="@@ -1,3 +1,4 @@\n+def add(a, b):\n+    return a + b",
            )
        ]
        risks = detect_keyword_risks(files)
        assert len(risks) == 0

    def test_keyword_not_in_context_lines(self):
        files = [
            FileChange(
                filename="src/test.py",
                status=FileStatus.MODIFIED,
                additions=1, deletions=0, changes=1,
                patch="@@ -5,3 +5,4 @@\n import os\n os.getcwd()\n+new_code()",
            )
        ]
        risks = detect_keyword_risks(files)
        assert len(risks) == 0

    def test_chmod_777_detected(self):
        files = [
            FileChange(
                filename="deploy.sh",
                status=FileStatus.MODIFIED,
                additions=1, deletions=0, changes=1,
                patch="@@ -1,3 +1,4 @@\n+chmod 777 /var/www",
            )
        ]
        risks = detect_keyword_risks(files)
        assert len(risks) == 1
        assert risks[0].category == RiskCategory.SECURITY


class TestDetectScaleRisks:
    def _make_file(self, filename: str, changes: int) -> FileChange:
        return FileChange(
            filename=filename,
            status=FileStatus.MODIFIED,
            additions=changes, deletions=0, changes=changes,
            patch="dummy",
        )

    def test_empty_files(self):
        assert detect_scale_risks([]) == []

    def test_small_pr_no_risks(self):
        files = [self._make_file(f"src/f{i}.py", 10) for i in range(5)]
        risks = detect_scale_risks(files)
        assert len(risks) == 0

    def test_medium_file_count(self):
        files = [self._make_file(f"src/f{i}.py", 10) for i in range(25)]
        risks = detect_scale_risks(files)
        assert len(risks) == 1
        assert risks[0].risk_level == RiskLevel.MEDIUM
        assert risks[0].category == RiskCategory.SCALE

    def test_high_file_count(self):
        files = [self._make_file(f"src/f{i}.py", 10) for i in range(55)]
        risks = detect_scale_risks(files)
        assert any(r.risk_level == RiskLevel.HIGH for r in risks)

    def test_high_total_changes(self):
        files = [self._make_file(f"src/f{i}.py", 200) for i in range(6)]
        risks = detect_scale_risks(files)
        assert any("1000" in r.message for r in risks)

    def test_single_file_too_large(self):
        files = [
            FileChange(
                filename="src/big.py",
                status=FileStatus.MODIFIED,
                additions=350, deletions=0, changes=350,
                patch="dummy",
            )
        ]
        risks = detect_scale_risks(files)
        assert len(risks) == 1
        assert risks[0].risk_level == RiskLevel.HIGH
        assert "big.py" in risks[0].message

    def test_combined_risks(self):
        files = [self._make_file(f"src/f{i}.py", 50) for i in range(60)]
        risks = detect_scale_risks(files)
        # file_count > 50 (high) + total_changes > 1000 (high)
        assert len(risks) >= 2
