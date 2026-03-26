from __future__ import annotations

import unittest

from src.utils.validation import Validation
from src.utils.errors import ValidationError


class TestValidation(unittest.TestCase):
    # -----------------------------
    # not_empty
    # -----------------------------
    def test_not_empty_returns_value_when_non_empty(self) -> None:
        out = Validation.not_empty(" hi ", "field")
        self.assertEqual(out, " hi ")

    def test_not_empty_raises_when_none(self) -> None:
        with self.assertRaises(ValidationError):
            Validation.not_empty(None, "field")

    def test_not_empty_raises_when_blank(self) -> None:
        with self.assertRaises(ValidationError):
            Validation.not_empty("   ", "field")

    # -----------------------------
    # max_length
    # -----------------------------
    def test_max_length_returns_value_when_within_limit(self) -> None:
        out = Validation.max_length("abc", 3, "field")
        self.assertEqual(out, "abc")

    def test_max_length_raises_when_none(self) -> None:
        with self.assertRaises(ValidationError):
            Validation.max_length(None, 3, "field")

    def test_max_length_raises_when_exceeds_limit(self) -> None:
        with self.assertRaises(ValidationError):
            Validation.max_length("abcd", 3, "field")

    # -----------------------------
    # is_positive_number
    # -----------------------------
    def test_is_positive_number_accepts_numeric_string(self) -> None:
        out = Validation.is_positive_number("3.5", "price")
        self.assertEqual(out, 3.5)

    def test_is_positive_number_accepts_int(self) -> None:
        out = Validation.is_positive_number(2, "price")
        self.assertEqual(out, 2.0)

    def test_is_positive_number_raises_when_not_number(self) -> None:
        with self.assertRaises(ValidationError):
            Validation.is_positive_number("abc", "price")

    def test_is_positive_number_raises_when_zero(self) -> None:
        with self.assertRaises(ValidationError):
            Validation.is_positive_number(0, "price")

    def test_is_positive_number_raises_when_negative(self) -> None:
        with self.assertRaises(ValidationError):
            Validation.is_positive_number(-1, "price")

    # -----------------------------
    # valid_email
    # -----------------------------
    def test_valid_email_strips_and_lowercases(self) -> None:
        out = Validation.valid_email("  TEST@Example.COM ")
        self.assertEqual(out, "test@example.com")

    def test_valid_email_raises_when_none(self) -> None:
        with self.assertRaises(ValidationError):
            Validation.valid_email(None)

    def test_valid_email_raises_when_empty(self) -> None:
        with self.assertRaises(ValidationError):
            Validation.valid_email("   ")

    def test_valid_email_raises_when_invalid_format(self) -> None:
        with self.assertRaises(ValidationError):
            Validation.valid_email("not-an-email")

    # -----------------------------
    # is_boolean
    # -----------------------------
    def test_is_boolean_returns_value_when_bool(self) -> None:
        out = Validation.is_boolean(True, "flag")
        self.assertTrue(out)

    def test_is_boolean_raises_when_none(self) -> None:
        with self.assertRaises(ValidationError):
            Validation.is_boolean(None, "flag")

    def test_is_boolean_raises_when_not_bool(self) -> None:
        with self.assertRaises(ValidationError):
            Validation.is_boolean("true", "flag")

    # -----------------------------
    # require_str
    # -----------------------------
    def test_require_str_strips(self) -> None:
        out = Validation.require_str("  hi  ", "name")
        self.assertEqual(out, "hi")

    def test_require_str_raises_when_none(self) -> None:
        with self.assertRaises(ValidationError):
            Validation.require_str(None, "name")

    def test_require_str_raises_when_not_str(self) -> None:
        with self.assertRaises(ValidationError):
            Validation.require_str(123, "name")

    def test_require_str_raises_when_blank(self) -> None:
        with self.assertRaises(ValidationError):
            Validation.require_str("   ", "name")

    # -----------------------------
    # require_int
    # -----------------------------
    def test_require_int_returns_int(self) -> None:
        out = Validation.require_int(5, "id")
        self.assertEqual(out, 5)

    def test_require_int_raises_when_none(self) -> None:
        with self.assertRaises(ValidationError):
            Validation.require_int(None, "id")

    def test_require_int_raises_when_not_int(self) -> None:
        with self.assertRaises(ValidationError):
            Validation.require_int("5", "id")

    # -----------------------------
    # require_positive_int
    # -----------------------------
    def test_require_positive_int_returns_when_positive(self) -> None:
        out = Validation.require_positive_int(1, "id")
        self.assertEqual(out, 1)

    def test_require_positive_int_raises_when_zero(self) -> None:
        with self.assertRaises(ValidationError):
            Validation.require_positive_int(0, "id")

    def test_require_positive_int_raises_when_negative(self) -> None:
        with self.assertRaises(ValidationError):
            Validation.require_positive_int(-1, "id")

    def test_require_positive_int_raises_when_not_int(self) -> None:
        with self.assertRaises(ValidationError):
            Validation.require_positive_int("1", "id")

    # -----------------------------
    # require_not_none
    # -----------------------------
    def test_require_not_none_returns_value(self) -> None:
        obj = object()
        out = Validation.require_not_none(obj, "obj")
        self.assertIs(out, obj)

    def test_require_not_none_raises_when_none(self) -> None:
        with self.assertRaises(ValidationError):
            Validation.require_not_none(None, "obj")

    # -----------------------------
    # rating_average
    # -----------------------------
    def test_rating_average_returns_none_when_none(self) -> None:
        out = Validation.rating_average(None)
        self.assertIsNone(out)

    def test_rating_average_accepts_float(self) -> None:
        out = Validation.rating_average(4.5)
        self.assertEqual(out, 4.5)

    def test_rating_average_raises_when_not_number(self) -> None:
        with self.assertRaises(ValidationError):
            Validation.rating_average("bad")

    def test_rating_average_raises_when_negative(self) -> None:
        with self.assertRaises(ValidationError):
            Validation.rating_average(-1.0)

    # -----------------------------
    # rating_sum
    # -----------------------------
    def test_rating_sum_returns_value_when_valid(self) -> None:
        out = Validation.rating_sum(5)
        self.assertEqual(out, 5)

    def test_rating_sum_raises_when_negative(self) -> None:
        with self.assertRaises(ValidationError):
            Validation.rating_sum(-1)

    # -----------------------------
    # rating_count
    # -----------------------------
    def test_rating_count_returns_value_when_valid(self) -> None:
        out = Validation.rating_count(5)
        self.assertEqual(out, 5)

    def test_rating_count_raises_when_negative(self) -> None:
        with self.assertRaises(ValidationError):
            Validation.rating_count(-1)
