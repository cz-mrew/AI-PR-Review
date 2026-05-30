from ai_pr_review.review.file_classifier import is_test_file


class TestIsTestFile:
    def test_test_py_prefix(self):
        assert is_test_file("tests/test_auth.py") is True

    def test_test_py_suffix(self):
        assert is_test_file("src/auth_test.py") is True

    def test_tests_dir(self):
        assert is_test_file("tests/unit/test_auth.py") is True

    def test_dunder_tests_dir(self):
        assert is_test_file("__tests__/auth.test.js") is True

    def test_test_js(self):
        assert is_test_file("src/auth.test.js") is True

    def test_spec_ts(self):
        assert is_test_file("src/auth.spec.ts") is True

    def test_regular_source_file(self):
        assert is_test_file("src/auth.py") is False

    def test_regular_js_file(self):
        assert is_test_file("src/utils.js") is False

    def test_file_in_nested_test_dir(self):
        assert is_test_file("project/tests/integration/test_db.py") is True

    def test_file_with_test_in_name_but_not_test(self):
        assert is_test_file("src/contest.py") is False

    def test_empty_filename(self):
        assert is_test_file("") is False
