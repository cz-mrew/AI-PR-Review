import pytest

from ai_pr_review.ai.prompt_loader import load_prompt


class TestPromptLoader:
    def test_load_summarize_pr(self):
        content = load_prompt("summarize_pr.txt")
        assert "PR 信息" in content
        assert "Diff 内容" in content

    def test_load_detect_risks(self):
        content = load_prompt("detect_risks.txt")
        assert "security" in content.lower()
        assert "risks" in content.lower()

    def test_load_generate_review_suggestions(self):
        content = load_prompt("generate_review_suggestions.txt")
        assert "PR 总结" in content
        assert "审查优先级" in content

    def test_load_line_comments(self):
        content = load_prompt("line_comments.txt")
        assert "comments" in content.lower()
        assert "Patch" in content

    def test_load_nonexistent_prompt_raises(self):
        with pytest.raises(FileNotFoundError):
            load_prompt("nonexistent.txt")

    def test_prompt_content_is_string(self):
        content = load_prompt("summarize_pr.txt")
        assert isinstance(content, str)
        assert len(content) > 0
