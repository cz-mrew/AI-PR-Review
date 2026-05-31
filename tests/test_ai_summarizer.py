from ai_pr_review.ai.client import MockAIClient
from ai_pr_review.ai.summarizer import PRSummarizer


class TestPRSummarizer:
    def _make_client(self, response: str = "AI generated summary") -> MockAIClient:
        return MockAIClient()

    def test_returns_string(self):
        summarizer = PRSummarizer(MockAIClient())
        result = summarizer.summarize(
            pr_info={"title": "Add login", "author": "dev"},
            diff_context=[],
        )
        assert isinstance(result, str)

    def test_calls_ai_client(self):
        client = MockAIClient()
        summarizer = PRSummarizer(client)
        result = summarizer.summarize(
            pr_info={
                "title": "Fix auth bug",
                "author": "alice",
                "description": "Fixes a critical auth bypass",
                "files_changed": 3,
                "additions": 50,
                "deletions": 10,
            },
            diff_context=[
                {
                    "filename": "src/auth.py",
                    "status": "modified",
                    "additions": 20,
                    "deletions": 5,
                    "is_analyzable": True,
                    "patch": "@@ -1,3 +1,5 @@\n def login():\n+    validate()",
                }
            ],
        )
        assert result == "mock response"

    def test_handles_empty_diff_context(self):
        summarizer = PRSummarizer(MockAIClient())
        result = summarizer.summarize(
            pr_info={"title": "Empty PR"},
            diff_context=[],
        )
        assert isinstance(result, str)

    def test_skips_non_analyzable_files(self):
        summarizer = PRSummarizer(MockAIClient())
        result = summarizer.summarize(
            pr_info={"title": "Binary change"},
            diff_context=[
                {
                    "filename": "img/logo.png",
                    "status": "added",
                    "additions": 0,
                    "deletions": 0,
                    "is_analyzable": False,
                    "skip_reason": "empty_patch_or_binary_file",
                }
            ],
        )
        assert isinstance(result, str)

    def test_handles_list_commit_messages(self):
        summarizer = PRSummarizer(MockAIClient())
        result = summarizer.summarize(
            pr_info={
                "title": "Multi commit PR",
                "commit_messages": ["fix: auth bug", "feat: add tests"],
            },
            diff_context=[],
        )
        assert isinstance(result, str)
