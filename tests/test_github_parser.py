import pytest

from ai_pr_review.github.parser import parse_github_pr_url


def test_valid_pr_url_can_be_parsed():
    parsed = parse_github_pr_url("https://github.com/owner/repo/pull/123")

    assert parsed.owner == "owner"
    assert parsed.repo == "repo"
    assert parsed.pull_number == 123


@pytest.mark.parametrize(
    "url",
    [
        "",
        "not-a-url",
        "https://example.com/owner/repo/pull/123",
        "https://github.com/owner/repo/pull/not-a-number",
    ],
)
def test_invalid_url_raises_value_error(url):
    with pytest.raises(ValueError):
        parse_github_pr_url(url)


def test_non_pull_url_raises_value_error():
    with pytest.raises(ValueError):
        parse_github_pr_url("https://github.com/owner/repo/issues/123")


def test_pull_number_is_int():
    parsed = parse_github_pr_url("https://github.com/owner/repo/pull/123")

    assert isinstance(parsed.pull_number, int)
