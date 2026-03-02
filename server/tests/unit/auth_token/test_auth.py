from __future__ import annotations

import os
os.environ.setdefault("SECRET_KEY", "test-secret")

import unittest
import jwt as pyjwt
import datetime
from unittest.mock import patch, MagicMock

from src.auth.jwt import get_user_id_from_token
from src.api.errors.api_error import ApiError
from src.auth.dependencies import get_current_user_id
from src.config import SECRET_KEY 


class TestJWTAuth(unittest.TestCase):

    # -----------------------------
    # get_user_id_from_token
    # -----------------------------
    
    def test_get_user_id_from_token_valid(self) -> None:
        # Create a real JWT with sub=1
        expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
        token = pyjwt.encode(
            {"sub": "1", "exp": expiration},
            SECRET_KEY,
            algorithm="HS256",
        )

        user_id = get_user_id_from_token(token)

        self.assertEqual(user_id, 1)

    def test_get_user_id_from_token_missing_token_raises_401(self) -> None:
        # Empty auth_token should fail immediately
        with self.assertRaises(ApiError) as ctx:
            get_user_id_from_token("")

        self.assertEqual(ctx.exception.status_code, 401)

    def test_get_user_id_from_token_invalid_token_raises_401(self) -> None:
        # Completely invalid auth_token string
        with self.assertRaises(ApiError) as ctx:
            get_user_id_from_token("invalid.auth_token.value")

        self.assertEqual(ctx.exception.status_code, 401)

    def test_get_user_id_from_token_missing_sub_raises_401(self) -> None:
        # Token without "sub"
        expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
        token = pyjwt.encode(
            {"exp": expiration},
            SECRET_KEY,
            algorithm="HS256",
        )

        with self.assertRaises(ApiError) as ctx:
            get_user_id_from_token(token)

        self.assertEqual(ctx.exception.status_code, 401)

    def test_get_user_id_from_token_non_int_sub_raises_401(self) -> None:
        # "sub" not convertible to int
        expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
        token = pyjwt.encode(
            {"sub": "abc", "exp": expiration},
            SECRET_KEY,
            algorithm="HS256",
        )

        with self.assertRaises(ApiError) as ctx:
            get_user_id_from_token(token)

        self.assertEqual(ctx.exception.status_code, 401)

    # -----------------------------
    # get_current_user_id (dependency)
    # -----------------------------

    @patch("src.auth.dependencies.jwt.get_user_id_from_token")
    def test_get_current_user_id_delegates_to_jwt(self, mock_get_user_id) -> None:
        # Mock JWT extraction
        mock_get_user_id.return_value = 5

        # Fake credentials object
        credentials = MagicMock()
        credentials.credentials = "valid.auth_token"

        result = get_current_user_id(credentials)

        self.assertEqual(result, 5)
        mock_get_user_id.assert_called_once_with("valid.auth_token")