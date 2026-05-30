from ai_pr_review.github.models import (
    GitHubChangedFile,
    GitHubPRRef,
    GitHubPullRequest,
    GitHubUser,
)


def test_github_pr_ref_model_fields_have_expected_types():
    ref = GitHubPRRef(owner="owner", repo="repo", pull_number=123)

    assert ref.owner == "owner"
    assert ref.repo == "repo"
    assert ref.pull_number == 123
    assert isinstance(ref.owner, str)
    assert isinstance(ref.repo, str)
    assert isinstance(ref.pull_number, int)


def test_github_user_model_fields_have_expected_types():
    user = GitHubUser(login="octocat", html_url="https://github.com/octocat")

    assert user.login == "octocat"
    assert user.html_url == "https://github.com/octocat"
    assert isinstance(user.login, str)
    assert isinstance(user.html_url, str)


def test_github_pull_request_model_fields_have_expected_types():
    user = GitHubUser(login="octocat", html_url="https://github.com/octocat")
    pull_request = GitHubPullRequest(
        number=123,
        title="Add parser",
        body="Implements GitHub PR parsing.",
        state="open",
        html_url="https://github.com/owner/repo/pull/123",
        user=user,
        base_branch="main",
        head_branch="feature/parser",
        head_sha="abc123",
        created_at="2026-05-30T00:00:00Z",
        updated_at="2026-05-30T01:00:00Z",
    )

    assert pull_request.number == 123
    assert pull_request.title == "Add parser"
    assert pull_request.body == "Implements GitHub PR parsing."
    assert pull_request.state == "open"
    assert pull_request.html_url == "https://github.com/owner/repo/pull/123"
    assert pull_request.user is user
    assert pull_request.base_branch == "main"
    assert pull_request.head_branch == "feature/parser"
    assert pull_request.head_sha == "abc123"
    assert pull_request.created_at == "2026-05-30T00:00:00Z"
    assert pull_request.updated_at == "2026-05-30T01:00:00Z"

    assert isinstance(pull_request.number, int)
    assert isinstance(pull_request.title, str)
    assert isinstance(pull_request.body, str)
    assert isinstance(pull_request.state, str)
    assert isinstance(pull_request.html_url, str)
    assert isinstance(pull_request.user, GitHubUser)
    assert isinstance(pull_request.base_branch, str)
    assert isinstance(pull_request.head_branch, str)
    assert isinstance(pull_request.head_sha, str)
    assert isinstance(pull_request.created_at, str)
    assert isinstance(pull_request.updated_at, str)


def test_github_changed_file_model_fields_have_expected_types():
    changed_file_json = {
        "filename": "src/app.py",
        "status": "modified",
        "additions": 12,
        "deletions": 3,
        "changes": 15,
        "patch": "@@ -1,1 +1,1 @@\n-old\n+new",
        "raw_url": "https://github.com/owner/repo/raw/main/src/app.py",
        "blob_url": "https://github.com/owner/repo/blob/main/src/app.py",
    }

    changed_file = GitHubChangedFile(**changed_file_json)

    assert changed_file.filename == "src/app.py"
    assert changed_file.status == "modified"
    assert changed_file.additions == 12
    assert changed_file.deletions == 3
    assert changed_file.changes == 15
    assert changed_file.patch == "@@ -1,1 +1,1 @@\n-old\n+new"
    assert changed_file.raw_url == "https://github.com/owner/repo/raw/main/src/app.py"
    assert changed_file.blob_url == "https://github.com/owner/repo/blob/main/src/app.py"

    assert isinstance(changed_file.filename, str)
    assert isinstance(changed_file.status, str)
    assert isinstance(changed_file.additions, int)
    assert isinstance(changed_file.deletions, int)
    assert isinstance(changed_file.changes, int)
    assert isinstance(changed_file.patch, str)
    assert isinstance(changed_file.raw_url, str)
    assert isinstance(changed_file.blob_url, str)


def test_github_changed_file_patch_can_be_none():
    changed_file = GitHubChangedFile(
        filename="assets/logo.png",
        status="added",
        additions=0,
        deletions=0,
        changes=0,
        patch=None,
        raw_url="https://github.com/owner/repo/raw/main/assets/logo.png",
        blob_url="https://github.com/owner/repo/blob/main/assets/logo.png",
    )

    assert changed_file.patch is None
