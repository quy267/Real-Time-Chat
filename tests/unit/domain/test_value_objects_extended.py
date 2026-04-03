"""Extended unit tests for domain value objects — covers uncovered edge cases."""

import pytest

from src.domain.exceptions import ValidationError
from src.domain.value_objects.message_content import MessageContent


class TestMessageContentExtended:
    def test_repr_returns_expected_string(self):
        mc = MessageContent("hello")
        assert repr(mc) == "MessageContent('hello')"

    def test_equality_between_equal_instances(self):
        a = MessageContent("same text")
        b = MessageContent("same text")
        assert a == b

    def test_inequality_between_different_instances(self):
        a = MessageContent("foo")
        b = MessageContent("bar")
        assert a != b

    def test_eq_with_non_message_content_returns_not_implemented(self):
        mc = MessageContent("hello")
        result = mc.__eq__("hello")
        assert result is NotImplemented

    def test_hash_equal_for_same_value(self):
        a = MessageContent("hash-me")
        b = MessageContent("hash-me")
        assert hash(a) == hash(b)

    def test_hash_different_for_different_values(self):
        a = MessageContent("alpha")
        b = MessageContent("beta")
        assert hash(a) != hash(b)

    def test_usable_as_dict_key(self):
        mc = MessageContent("key")
        d = {mc: "value"}
        assert d[MessageContent("key")] == "value"

    def test_content_with_leading_trailing_whitespace_is_accepted(self):
        # The check strips for empty detection but stores original value
        mc = MessageContent("  hello  ")
        assert mc.value == "  hello  "

    def test_exactly_max_length_accepted(self):
        mc = MessageContent("x" * 4000)
        assert len(mc.value) == 4000

    def test_one_over_max_length_raises(self):
        with pytest.raises(ValidationError, match="4000"):
            MessageContent("x" * 4001)

    def test_single_char_is_valid(self):
        mc = MessageContent("a")
        assert mc.value == "a"

    def test_newlines_and_unicode_accepted(self):
        content = "Hello\nWorld\n\u2603"
        mc = MessageContent(content)
        assert mc.value == content
