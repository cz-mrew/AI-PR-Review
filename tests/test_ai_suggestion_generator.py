from ai_pr_review.ai.client import MockAIClient
from ai_pr_review.ai.suggestion_generator import ReviewSuggestionGenerator
from ai_pr_review.review.models import (
    Confidence,
    ReviewRisk,
    RiskCategory,
    RiskLevel,
    RiskSource,
)


class TestReviewSuggestionGenerator:
    def test_returns_string(self):
        gen = ReviewSuggestionGenerator(MockAIClient())
        result = gen.generate("A simple PR", [])
        assert isinstance(result, str)

    def test_calls_ai_client(self):
        gen = ReviewSuggestionGenerator(MockAIClient())
        result = gen.generate(
            "PR adds new auth module",
            [
                ReviewRisk(
                    file="src/auth.py",
                    risk_level=RiskLevel.HIGH,
                    source=RiskSource.AI,
                    category=RiskCategory.SECURITY,
                    message="Hardcoded secret",
                    suggestion="Use env variable",
                )
            ],
        )
        assert result == "mock response"

    def test_empty_risks(self):
        gen = ReviewSuggestionGenerator(MockAIClient())
        result = gen.generate("Simple refactor PR", [])
        assert isinstance(result, str)

    def test_multiple_risks_formatted(self):
        gen = ReviewSuggestionGenerator(MockAIClient())
        result = gen.generate(
            "Large PR with many changes",
            [
                ReviewRisk(
                    file="src/a.py",
                    risk_level=RiskLevel.HIGH,
                    source=RiskSource.AI,
                    category=RiskCategory.SECURITY,
                    message="Risk 1",
                    suggestion="Fix 1",
                    line=10,
                ),
                ReviewRisk(
                    file="src/b.py",
                    risk_level=RiskLevel.MEDIUM,
                    source=RiskSource.RULE,
                    category=RiskCategory.PERFORMANCE,
                    message="Risk 2",
                    suggestion="Fix 2",
                ),
            ],
        )
        assert isinstance(result, str)
