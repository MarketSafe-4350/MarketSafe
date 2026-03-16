import os
from src.utils import ConfigurationError

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ConfigurationError(
        message="SECRET_KEY environment variable is not set.",
        details={"variable": "SECRET_KEY"},
    )

FRONTEND_URL = os.getenv("FRONTEND_URL")
if not FRONTEND_URL:
    raise ConfigurationError(
        message="FRONTEND_URL environment variable is not set.",
        details={"variable": "FRONTEND_URL"},
    )

# Comma-separated list for CORS, e.g. "http://localhost:4200,https://myapp.com"
_cors_origins_raw = os.getenv("CORS_ALLOWED_ORIGINS", FRONTEND_URL)
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in _cors_origins_raw.split(",") if origin.strip()]
