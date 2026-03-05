import os
from dotenv import load_dotenv
from src.utils import ConfigurationError

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise ConfigurationError(
        message="SECRET_KEY environment variable is not set.",
        details={"variable": "SECRET_KEY"},
    )

# Frontend URL for verification links
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:4200")

# Comma-separated list for CORS, e.g. "http://localhost:4200,http://localhost:3000"
_cors_origins_raw = os.getenv(
    "CORS_ALLOWED_ORIGINS", f"{FRONTEND_URL},http://localhost:3000"
)
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in _cors_origins_raw.split(",") if origin.strip()]
