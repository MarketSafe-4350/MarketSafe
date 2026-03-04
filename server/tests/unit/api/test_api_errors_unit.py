import unittest
import json
from fastapi.responses import JSONResponse
from unittest.mock import MagicMock

from src.api.errors.api_error import ApiError
from src.api.errors.exception_handlers import api_error_handler, app_error_handler
from src.utils.errors import AppError


class TestAPIError(unittest.IsolatedAsyncioTestCase):

    def test_init_sets_status_code_and_message(self):
        err = ApiError(status_code=401, message="Nope")
        self.assertEqual(err.status_code, 401)
        self.assertEqual(err.message, 401)
        self.assertEqual(err._message, "Nope")

    def test_status_code_cannot_be_none(self):
        with self.assertRaises(ValueError):
            ApiError(status_code=None, message="x")

    def test_message_none_does_not_raise_bug(self):
        err = ApiError(status_code=400, message=None)
        self.assertFalse(hasattr(err, "_message"))

    async def test_api_error_handler_returns_json_response(self):
        request = MagicMock()
        err = ApiError(status_code=401, message="Token has expired")
        response = await api_error_handler(request, err)

        self.assertIsInstance(response, JSONResponse)
        self.assertEqual(response.status_code, 401)

        body = json.loads(response.body.decode("utf-8"))
        self.assertEqual(body, {"error_message": 401})

    async def test_app_error_handler_without_details(self):
        request = MagicMock()
        err = AppError(status_code=400, message="Bad request", code="BAD_REQUEST", details=None)

        response = await app_error_handler(request, err)

        self.assertIsInstance(response, JSONResponse)
        self.assertEqual(response.status_code, 400)

        body = json.loads(response.body.decode("utf-8"))
        self.assertEqual(body, {
            "error_message": "Bad request",
            "error_code": "BAD_REQUEST",
        })
        self.assertNotIn("details", body)

    async def test_app_error_handler_with_details(self):
        request = MagicMock()
        details = {"field": "title", "reason": "required"}
        err = AppError(status_code=422, message="Validation failed", code="VALIDATION_ERROR", details=details)

        response = await app_error_handler(request, err)

        self.assertIsInstance(response, JSONResponse)
        self.assertEqual(response.status_code, 422)

        body = json.loads(response.body.decode("utf-8"))
        self.assertEqual(body, {
            "error_message": "Validation failed",
            "error_code": "VALIDATION_ERROR",
            "details": details,
        })


if __name__ == "__main__":
    unittest.main()