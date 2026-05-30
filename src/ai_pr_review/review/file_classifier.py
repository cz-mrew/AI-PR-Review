from pathlib import PurePosixPath

_TEST_PATTERNS: list[tuple[str, bool]] = [
    ("tests/", True),
    ("__tests__/", True),
    ("test_", False),
    ("_test.", False),
    (".test.", False),
    (".spec.", False),
]


def is_test_file(filename: str) -> bool:
    path = PurePosixPath(filename)
    parts = path.parts
    name = path.name

    for pattern, is_dir in _TEST_PATTERNS:
        if is_dir:
            for part in parts:
                if part == pattern.rstrip("/"):
                    return True
        else:
            if pattern.startswith("."):
                if pattern in name:
                    return True
            elif name.startswith(pattern) or pattern in name:
                return True

    return False
