from jinja2 import Template

from ..review.models import ReviewRisk
from .client import AIClient
from .prompt_loader import load_prompt


class ReviewSuggestionGenerator:
    def __init__(self, client: AIClient) -> None:
        self._client = client

    def generate(self, summary: str, risks: list[ReviewRisk]) -> str:
        template = Template(load_prompt("generate_review_suggestions.txt"))
        prompt = template.render(
            pr_summary=summary,
            risks=self._format_risks(risks),
        )
        messages = [{"role": "user", "content": prompt}]
        return self._client.chat(messages)

    def _format_risks(self, risks: list[ReviewRisk]) -> str:
        if not risks:
            return "未发现风险项"

        lines: list[str] = []
        for i, r in enumerate(risks, 1):
            lines.append(
                f"{i}. [{r.risk_level.value}/{r.category.value}] {r.file}"
                f"{f':{r.line}' if r.line else ''} — {r.message}"
                f"\n   建议：{r.suggestion}"
            )
        return "\n".join(lines)
