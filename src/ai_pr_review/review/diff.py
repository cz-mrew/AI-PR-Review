from ..config import get_settings
from ..github.models import FileChange


def build_diff_context(files: list[FileChange]) -> list[dict]:
    settings = get_settings()
    remaining_diff_chars = settings.max_diff_chars
    result: list[dict] = []
    for f in files:
        has_patch = bool(f.patch) and not f.is_binary
        patch = ""
        is_truncated = False

        if has_patch:
            patch_limit = min(settings.max_patch_chars_per_file, remaining_diff_chars)
            patch = f.patch[:patch_limit]
            remaining_diff_chars -= len(patch)
            is_truncated = len(f.patch) > len(patch)

        result.append({
            "filename": f.filename,
            "status": f.status.value,
            "additions": f.additions,
            "deletions": f.deletions,
            "changes": f.changes,
            "patch": patch,
            "is_analyzable": has_patch,
            "is_truncated": is_truncated,
            "skip_reason": None if has_patch else "empty_patch_or_binary_file",
        })
    return result
