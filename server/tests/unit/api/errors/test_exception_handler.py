from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.api.errors import exception_handlers
from src.utils.errors import AppError


class TestErrorHandlers(unittest.IsolatedAsyncioTestCase):

    async def test_api_error_handler_returns_expected_json(self) -> None:
        request = MagicMock()

        error = MagicMock()
        error.status_code = 400
        error.message = "Something went wrong"

        response: JSONResponse = await exception_handlers.api_error_handler(
            request, error
        )

        self.assertEqual(response.status_code, 400)
        payload = json.loads(response.body.decode())
        self.assertEqual(payload, {"error_message": "Something went wrong"})

    async def test_app_error_handler_without_details(self) -> None:
        request = MagicMock()

        error = AppError(
            message="App failure",
            code="APP_ERR",
            status_code=500,
            details=None,
        )

        response: JSONResponse = await exception_handlers.app_error_handler(
            request, error
        )

        self.assertEqual(response.status_code, 500)
        payload = json.loads(response.body.decode())
        self.assertEqual(
            payload, {"error_message": "App failure", "error_code": "APP_ERR"}
        )

    async def test_app_error_handler_with_details(self) -> None:
        request = MagicMock()

        error = AppError(
            message="App failure",
            code="APP_ERR",
            status_code=500,
            details={"field": "invalid"},
        )

        response: JSONResponse = await exception_handlers.app_error_handler(
            request, error
        )

        self.assertEqual(response.status_code, 500)
        payload = json.loads(response.body.decode())
        self.assertEqual(
            payload,
            {
                "error_message": "App failure",
                "error_code": "APP_ERR",
                "details": {"field": "invalid"},
            },
        )

    async def test_request_validation_error_handler(self) -> None:
        request = MagicMock()

        error = RequestValidationError(
            errors=[
                {
                    "loc": ["body", "email"],
                    "msg": "field required",
                    "type": "value_error",
                }
            ]
        )

        response: JSONResponse = (
            await exception_handlers.request_validation_error_handler(request, error)
        )

        self.assertEqual(response.status_code, 422)
        payload = json.loads(response.body.decode())
        self.assertEqual(payload["error_message"], "Request validation failed.")
        self.assertIsInstance(payload["details"], list)
