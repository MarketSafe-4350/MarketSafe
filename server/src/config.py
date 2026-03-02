import os
from dotenv import load_dotenv
from src.utils import ConfigurationError

APP_ENV = os.getenv("APP_ENV", "dev").lower()

if APP_ENV == "dev":
    # load env
    load_dotenv()


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ConfigurationError(
            message=f"{name} environment variable is not set.",
            details={"variable": name},
        )
    return value


def _get_list(name: str, default: str = "") -> list[str]:
    raw = os.getenv(name, default)
    return [x.strip() for x in raw.split(",") if x.strip()]


SECRET_KEY = _require("SECRET_KEY")

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:4200" if APP_ENV == "dev" else "",
)
if APP_ENV != "dev" and not FRONTEND_URL:
    # require if we run the env in "prod", since we have email link verification
    raise ConfigurationError(
        message="FRONTEND_URL environment variable is not set for prod.",
        details={"variable": "FRONTEND_URL"},
    )

if APP_ENV == "dev":
    # default for dev env
    CORS_ALLOWED_ORIGINS = _get_list(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:4200,http://localhost:3000",
    )
else:
    # prod env require correct env variables
    CORS_ALLOWED_ORIGINS = _get_list("CORS_ALLOWED_ORIGINS")
    if not CORS_ALLOWED_ORIGINS:
        raise ConfigurationError(
            message="CORS_ALLOWED_ORIGINS must be set in prod (comma-separated).",
            details={"variable": "CORS_ALLOWED_ORIGINS"},
        )
