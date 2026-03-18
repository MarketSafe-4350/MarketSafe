from __future__ import annotations

import importlib
import os
import sys
import unittest
from unittest.mock import patch

from fastapi import FastAPI


class TestMainUnit(unittest.TestCase):
    def tearDown(self) -> None:
        sys.modules.pop("src.main", None)

    def test_main_create_app_smoke_for_coverage(self) -> None:
        test_env = {
            "DB_HOST": "test-host",
            "DB_PORT": "3306",
            "DB_NAME": "test-db",
            "DB_USER": "test-user",
            "DB_PASSWORD": "test-pass",
        }
        with patch.dict(os.environ, test_env, clear=False), patch(
            "src.main.DBUtility.initialize"
        ) as init_mock, patch("pathlib.Path.mkdir", autospec=True) as mkdir_mock:
            sys.modules.pop("src.main", None)
            mod = importlib.import_module("src.main")

            app = mod.app
            self.assertIsInstance(app, FastAPI)
            self.assertEqual(app.title, "MarketSafe API")

            init_mock.assert_called_once_with(
                host="test-host",
                port=3306,
                database="test-db",
                username="test-user",
                password="test-pass",
                driver="mysql+pymysql",
            )

            self.assertTrue(mkdir_mock.called)

            paths = [getattr(r, "path", "") for r in app.routes]
            self.assertTrue(any(p.startswith("/accounts") for p in paths))
            self.assertTrue(any(p.startswith("/listings") for p in paths))
            self.assertTrue(any(p.startswith("/offers") for p in paths))
            self.assertIn("/uploads", paths)

            from fastapi.exceptions import RequestValidationError
            from src.api.errors.api_error import ApiError
            from src.utils.errors import AppError

            self.assertIn(ApiError, app.exception_handlers)
            self.assertIn(AppError, app.exception_handlers)
            self.assertIn(RequestValidationError, app.exception_handlers)


if __name__ == "__main__":
    unittest.main(verbosity=2)
