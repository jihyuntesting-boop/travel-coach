"""단위 테스트. 외부 AI 호출은 mock(가짜 함수)으로 대체한다. 실제 API 호출 테스트가 아니다."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))
import _core  # noqa: E402

GOOD = (
    '{"questions":[{"question":"Q1","why":"W1"},{"question":"Q2","why":"W2"},'
    '{"question":"Q3","why":"W3"}],"keywords":["a","b","c","d","e"],"caution":"C"}'
)
ENV = {"ANTHROPIC_API_KEY": "test-key-not-real"}


class ValidateTest(unittest.TestCase):
    def test_empty_input(self):
        err, _ = _core.validate({"field": "", "keywords": ""})
        self.assertIn("필수값", err)

    def test_missing_keywords(self):
        err, _ = _core.validate({"field": "교육공학", "keywords": "  "})
        self.assertIn("필수값", err)

    def test_too_long_field(self):
        err, _ = _core.validate({"field": "가" * 61, "keywords": "x"})
        self.assertIn("60자", err)

    def test_too_long_keywords(self):
        err, _ = _core.validate({"field": "a", "keywords": "가" * 201})
        self.assertIn("200자", err)

    def test_invalid_level_falls_back(self):
        err, data = _core.validate({"field": "a", "keywords": "b", "level": "???"})
        self.assertIsNone(err)
        self.assertEqual(data["level"], "석사")

    def test_not_dict(self):
        err, _ = _core.validate([1, 2])
        self.assertIn("형식", err)


class HandleTest(unittest.TestCase):
    def test_success(self):
        status, body = _core.handle(
            {"field": "교육공학", "keywords": "생성형 AI"}, caller=lambda *a: GOOD, env=ENV
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(body["questions"]), 3)
        self.assertEqual(body["keywords"][0], "a")

    def test_success_with_code_fence(self):
        status, body = _core.handle(
            {"field": "a", "keywords": "b"}, caller=lambda *a: "```json\n" + GOOD + "\n```", env=ENV
        )
        self.assertEqual(status, 200)

    def test_bad_input_returns_400_without_calling_ai(self):
        def boom(*a):
            raise AssertionError("호출되면 안 된다")

        status, _ = _core.handle({"field": "", "keywords": ""}, caller=boom, env=ENV)
        self.assertEqual(status, 400)

    def test_missing_key(self):
        status, body = _core.handle({"field": "a", "keywords": "b"}, caller=lambda *a: GOOD, env={})
        self.assertEqual(status, 500)
        self.assertNotIn("ANTHROPIC", body["error"])

    def test_upstream_error_hides_details(self):
        def fail(*a):
            raise RuntimeError("secret-detail sk-xxx")

        status, body = _core.handle({"field": "a", "keywords": "b"}, caller=fail, env=ENV)
        self.assertEqual(status, 502)
        self.assertNotIn("secret", body["error"])

    def test_unparseable_output(self):
        status, _ = _core.handle({"field": "a", "keywords": "b"}, caller=lambda *a: "죄송합니다", env=ENV)
        self.assertEqual(status, 502)


if __name__ == "__main__":
    unittest.main()
