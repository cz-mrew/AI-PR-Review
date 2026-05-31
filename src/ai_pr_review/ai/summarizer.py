from jinja2 import Template

from .client import AIClient
from .prompt_loader import load_prompt


class PRSummarizer:
    def __init__(self, client: AIClient) -> None:
        self._client = client

    def summarize(self, pr_info: dict, diff_context: list[dict]) -> str:
        template = Template(load_prompt("summarize_pr.txt"))

        commit_messages = pr_info.get("commit_messages", "")
        if isinstance(commit_messages, list):
            commit_messages = "\n".join(f"- {m}" for m in commit_messages)

        diff_text = self._format_diff_context(diff_context)

        prompt = template.render(
            pr_title=pr_info.get("title", ""),
            pr_author=pr_info.get("author", ""),
            pr_description=pr_info.get("description", ""),
            files_changed=pr_info.get("files_changed", 0),
            additions=pr_info.get("additions", 0),
            deletions=pr_info.get("deletions", 0),
            commit_messages=commit_messages,
            diff_context=diff_text,
        )

        messages = [{"role": "user", "content": prompt}]
        return self._client.chat(messages)

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
