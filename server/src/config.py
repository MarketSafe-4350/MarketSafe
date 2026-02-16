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