from ..github.models import FileChange


def build_diff_context(files: list[FileChange]) -> list[dict]:
    result: list[dict] = []
    for f in files:
        has_patch = bool(f.patch) and not f.is_binary
        result.append({
            "filename": f.filename,
            "status": f.status.value,
            "additions": f.additions,
            "deletions": f.deletions,
            "changes": f.changes,
            "patch": f.patch if has_patch else "",
            "is_analyzable": has_patch,
            "skip_reason": None if has_patch else "empty_patch_or_binary_file",
        })
    return result
