from ai_pr_review.ai.client import AIClient
from ai_pr_review.ai.risk_analyzer import AIRiskAnalyzer
from ai_pr_review.review.models import ReviewRisk, RiskCategory, RiskLevel, RiskSource


class _CustomMockClient(AIClient):
    def __init__(self, response: str) -> None:
        self._response = response

    def chat(self, messages: list[dict]) -> str:
        return self._response


class TestAIRiskAnalyzer:
    def test_returns_review_risk_list(self):
        response = """```json
{
  "risks": [
    {
      "file": "src/auth.py",
      "line": 42,
      "risk_level": "high",
      "category": "security",
      "message": "Possible SQL injection",
      "suggestion": "Use parameterized queries"
    }
  ]
}
```"""
        client = _CustomMockClient(response)
        analyzer = AIRiskAnalyzer(client)
        risks = analyzer.analyze([
            {
                "filename": "src/auth.py",
                "status": "modified",
                "additions": 5, "deletions": 1,
                "is_analyzable": True,
                "patch": "dummy",
            }
        ])
        assert len(risks) == 1
        r = risks[0]
        assert isinstance(r, ReviewRisk)
        assert r.file == "src/auth.py"
        assert r.line == 42
        assert r.risk_level == RiskLevel.HIGH
        assert r.source == RiskSource.AI
        assert r.category == RiskCategory.SECURITY
        assert "SQL injection" in r.message

    def test_handles_json_without_code_block(self):
        response = '{"risks": [{"file": "x.py", "risk_level": "low", "category": "logic", "message": "unused var", "suggestion": "remove it"}]}'
        client = _CustomMockClient(response)
        analyzer = AIRiskAnalyzer(client)
        risks = analyzer.analyze([])
        assert len(risks) == 1

    def test_empty_risks_array(self):
        response = '{"risks": []}'
        client = _CustomMockClient(response)
        analyzer = AIRiskAnalyzer(client)
        risks = analyzer.analyze([])
        assert risks == []

    def test_invalid_json_returns_empty(self):
        client = _CustomMockClient("not valid json at all")
        analyzer = AIRiskAnalyzer(client)
        risks = analyzer.analyze([])
        assert risks == []

    def test_skips_invalid_risk_items(self):
        response = """```json
{
  "risks": [
    {"file": "ok.py", "risk_level": "medium", "category": "logic", "message": "ok", "suggestion": "fix"},
    {"file": "bad.py", "risk_level": "INVALID", "category": "logic", "message": "bad", "suggestion": "fix"}
  ]
}
```"""
        client = _CustomMockClient(response)
        analyzer = AIRiskAnalyzer(client)
        risks = analyzer.analyze([])
        assert len(risks) == 1
        assert risks[0].file == "ok.py"
