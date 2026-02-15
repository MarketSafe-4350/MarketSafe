import re
from typing import Any

from src.utils import ValidationError

class Validation:
    """
    Centralized validation utilities.
    All methods are static because they do not depend on instance state.
    """

    @staticmethod
    def not_empty(value: str, field_name: str) -> str:
        if value is None or value.strip() == "":
            raise ValidationError(f"{field_name} cannot be empty.")
        return value

    @staticmethod
    def max_length(value: str, max_len: int, field_name: str) -> str:
        if value is None:
            raise ValidationError(f"{field_name} cannot be None.")
        if len(value) > max_len:
            raise ValidationError(f"{field_name} cannot exceed {max_len} characters.")
        return value

    @staticmethod
    def is_positive_number(value: Any, field_name: str) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError) as e:
            raise ValidationError(f"{field_name} must be a valid number.") from e

        if number <= 0:
            raise ValidationError(f"{field_name} must be positive.")

        return number

    @staticmethod
    def valid_email(email: str) -> str:
        if email is None:
            raise ValidationError("Email cannot be None.")

        email = email.strip().lower()
        if email == "":
            raise ValidationError("Email cannot be empty.")

        pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(pattern, email):
            raise ValidationError("Invalid email format.")

        return email

    @staticmethod
    def is_boolean(value: Any, field_name: str) -> bool:
        if value is None:
            raise ValidationError(f"{field_name} cannot be None.")
        if not isinstance(value, bool):
            raise ValidationError(f"{field_name} must be a boolean.")
        return value

    @staticmethod
    def require_str(value: Any, name: str) -> str:
        if value is None or not isinstance(value, str) or value.strip() == "":
            raise ValidationError(f"{name} is required and must be a non-empty string")
        return value.strip()

    @staticmethod
    def require_int(value: Any, name: str) -> int:
        if value is None or not isinstance(value, int):
            raise ValidationError(f"{name} is required and must be an int")
        return value

    @staticmethod
    def require_not_none(value: Any, name: str) -> Any:
        if value is None:
            raise ValidationError(f"{name} is required and cannot be None")
        return value