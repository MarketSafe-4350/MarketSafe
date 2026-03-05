from __future__ import annotations

import importlib
import os
import sys
import unittest
from unittest.mock import patch

from src.utils import ConfigurationError


MODULE_PATH = "src.config"


def reload_config():
    if MODULE_PATH in sys.modules:
        del sys.modules[MODULE_PATH]
    return importlib.import_module(MODULE_PATH)


class TestConfig(unittest.TestCase):
    def test_missing_secret_key_raises_configuration_error(self) -> None:
        env = dict(os.environ)
        env.pop("SECRET_KEY", None)

        with patch.dict(os.environ, env, clear=True):
            with patch("dotenv.load_dotenv", return_value=None):
                with self.assertRaises(ConfigurationError):
                    reload_config()

    def test_frontend_url_defaults_when_missing(self) -> None:
        env = dict(os.environ)
        env["SECRET_KEY"] = "abc"
        env.pop("FRONTEND_URL", None)
        env.pop("CORS_ALLOWED_ORIGINS", None)

        with patch.dict(os.environ, env, clear=True):
            with patch("dotenv.load_dotenv", return_value=None):
                m = reload_config()
                self.assertEqual(m.FRONTEND_URL, "http://localhost:4200")

    def test_frontend_url_uses_env_when_set(self) -> None:
        env = dict(os.environ)
        env["SECRET_KEY"] = "abc"
        env["FRONTEND_URL"] = "http://frontend:4200"
        env.pop("CORS_ALLOWED_ORIGINS", None)

        with patch.dict(os.environ, env, clear=True):
            with patch("dotenv.load_dotenv", return_value=None):
                m = reload_config()
                self.assertEqual(m.FRONTEND_URL, "http://frontend:4200")

    def test_cors_defaults_to_frontend_and_local3000(self) -> None:
        env = dict(os.environ)
        env["SECRET_KEY"] = "abc"
        env.pop("FRONTEND_URL", None)
        env.pop("CORS_ALLOWED_ORIGINS", None)

        with patch.dict(os.environ, env, clear=True):
            with patch("dotenv.load_dotenv", return_value=None):
                m = reload_config()
                self.assertEqual(
                    m.CORS_ALLOWED_ORIGINS,
                    ["http://localhost:4200", "http://localhost:3000"],
                )

    def test_cors_default_uses_custom_frontend_url(self) -> None:
        env = dict(os.environ)
        env["SECRET_KEY"] = "abc"
        env["FRONTEND_URL"] = "http://x"
        env.pop("CORS_ALLOWED_ORIGINS", None)

        with patch.dict(os.environ, env, clear=True):
            with patch("dotenv.load_dotenv", return_value=None):
                m = reload_config()
                self.assertEqual(
                    m.CORS_ALLOWED_ORIGINS,
                    ["http://x", "http://localhost:3000"],
                )

    def test_cors_allowed_origins_parses_strips_and_drops_empty(self) -> None:
        env = dict(os.environ)
        env["SECRET_KEY"] = "abc"
        env["CORS_ALLOWED_ORIGINS"] = " http://a.com , ,http://b.com,   "
        env.pop("FRONTEND_URL", None)

        with patch.dict(os.environ, env, clear=True):
            with patch("dotenv.load_dotenv", return_value=None):
                m = reload_config()
                self.assertEqual(
                    m.CORS_ALLOWED_ORIGINS, ["http://a.com", "http://b.com"]
                )
