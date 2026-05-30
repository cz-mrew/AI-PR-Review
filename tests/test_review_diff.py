from ai_pr_review.github.models import FileChange, FileStatus
from ai_pr_review.review.diff import build_diff_context


class TestBuildDiffContext:
    def test_single_modified_file(self):
        files = [
            FileChange(
                filename="src/auth.py",
                status=FileStatus.MODIFIED,
                additions=10,
                deletions=2,
                changes=12,
                patch="@@ -1,3 +1,5 @@\n def foo():\n-    pass\n+    return True",
            )
        ]
        result = build_diff_context(files)
        assert len(result) == 1
        r = result[0]
        assert r["filename"] == "src/auth.py"
        assert r["status"] == "modified"
        assert r["additions"] == 10
        assert r["deletions"] == 2
        assert r["changes"] == 12
        assert r["is_analyzable"] is True
        assert r["skip_reason"] is None
        assert "def foo" in r["patch"]

    def test_binary_file_not_analyzable(self):
        files = [
            FileChange(
                filename="assets/logo.png",
                status=FileStatus.ADDED,
                additions=0,
                deletions=0,
                changes=0,
                patch="",
                is_binary=True,
            )
        ]
        result = build_diff_context(files)
        r = result[0]
        assert r["is_analyzable"] is False
        assert r["skip_reason"] == "empty_patch_or_binary_file"
        assert r["patch"] == ""

    def test_empty_patch_not_analyzable(self):
        files = [
            FileChange(
                filename="huge_file.py",
                status=FileStatus.MODIFIED,
                additions=500,
                deletions=300,
                changes=800,
                patch="",
            )
        ]
        result = build_diff_context(files)
        r = result[0]
        assert r["is_analyzable"] is False
        assert r["skip_reason"] == "empty_patch_or_binary_file"

    def test_multiple_files_mixed(self):
        files = [
            FileChange(
                filename="src/a.py",
                status=FileStatus.MODIFIED,
                additions=5,
                deletions=1,
                changes=6,
                patch="@@ -1 +1,2 @@\n+hello",
            ),
            FileChange(
                filename="img/b.png",
                status=FileStatus.ADDED,
                additions=0,
                deletions=0,
                changes=0,
                patch="",
                is_binary=True,
            ),
            FileChange(
                filename="src/c.py",
                status=FileStatus.REMOVED,
                additions=0,
                deletions=10,
                changes=10,
                patch="",
            ),
        ]
        result = build_diff_context(files)
        assert len(result) == 3
        assert result[0]["is_analyzable"] is True
        assert result[1]["is_analyzable"] is False
        assert result[2]["is_analyzable"] is False

    def test_added_file(self):
        files = [
            FileChange(
                filename="src/new_file.py",
                status=FileStatus.ADDED,
                additions=20,
                deletions=0,
                changes=20,
                patch="@@ -0,0 +1,20 @@\n+def new_func():\n+    pass",
            )
        ]
        result = build_diff_context(files)
        r = result[0]
        assert r["status"] == "added"
        assert r["is_analyzable"] is True

    def test_renamed_file(self):
        files = [
            FileChange(
                filename="src/renamed.py",
                status=FileStatus.RENAMED,
                additions=3,
                deletions=3,
                changes=6,
                patch="@@ -1,3 +1,3 @@\n-old\n+new",
            )
        ]
        result = build_diff_context(files)
        r = result[0]
        assert r["status"] == "renamed"
        assert r["is_analyzable"] is True
