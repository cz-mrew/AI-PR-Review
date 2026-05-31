import json
import re

from jinja2 import Template

from ..review.models import Confidence, ReviewRisk, RiskCategory, RiskLevel, RiskSource
from .client import AIClient
from .prompt_loader import load_prompt


class AIRiskAnalyzer:
    def __init__(self, client: AIClient) -> None:
        self._client = client

    def analyze(self, diff_context: list[dict]) -> list[ReviewRisk]:
        template = Template(load_prompt("detect_risks.txt"))
        diff_text = self._format_diff_context(diff_context)
        prompt = template.render(diff_context=diff_text)
        messages = [{"role": "user", "content": prompt}]
        response = self._client.chat(messages)
        return self._parse_response(response)

    def _parse_response(self, response: str) -> list[ReviewRisk]:
        json_str = self._extract_json(response)
        if not json_str:
            return []

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            return []

        risks: list[ReviewRisk] = []
        for item in data.get("risks", []):
            try:
                risks.append(ReviewRisk(
                    file=item.get("file", ""),
                    risk_level=RiskLevel(item.get("risk_level", "medium")),
                    source=RiskSource.AI,
                    category=RiskCategory(item.get("category", "maintainability")),
                    message=item.get("message", ""),
                    suggestion=item.get("suggestion", ""),
                    line=item.get("line"),
                    confidence=Confidence.MEDIUM,
                ))
            except (ValueError, TypeError):
                continue
        return risks

    def _extract_json(self, response: str) -> str | None:
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", response, re.DOTALL)
        if match:
            return match.group(1).strip()

        match = re.search(r"\{[\s\S]*\"risks\"[\s\S]*\}", response)
        if match:
            return match.group(0)

        return None

    def _format_diff_context(self, diff_context: list[dict]) -> str:
        lines: list[str] = []
        for f in diff_context:
            lines.append(f"\n### {f['filename']} ({f['status']}, +{f['additions']}/-{f['deletions']})")
            if f.get("is_analyzable") and f.get("patch"):
                lines.append(f["patch"])
            else:
                skip_reason = f.get("skip_reason", "unknown")
                lines.append(f"[跳过: {skip_reason}]")
        return "\n".join(lines)
