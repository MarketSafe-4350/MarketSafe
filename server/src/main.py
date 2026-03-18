import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.minio import MediaStorageUtility
from src.utils.errors import AppError
from src.config import CORS_ALLOWED_ORIGINS
from src.api.errors.exception_handlers import (
    api_error_handler,
    app_error_handler,
    request_validation_error_handler,
)
from src.api.routes.listing_routes import router as listing_router
from src.api.routes.account_routes import router as account_router
from src.business_logic.services.account_service import AccountService
from src.business_logic.services.listing_service import ListingService

from src.api.errors.api_error import ApiError
from src.business_logic.managers.account import AccountManager
from src.db import DBUtility
from src.db.account.mysql import MySQLAccountDB
from src.business_logic.services import AccountService


def create_app() -> FastAPI:
    """Creates and configures the FastAPI application.

    Returns:
        FastAPI: The configured FastAPI application instance.
    """
    print("Initializing DBUtility...")
    host = os.getenv("DB_HOST", "127.0.0.1")

    DBUtility.initialize(
        host=host,
        port=int(os.getenv("DB_PORT", 3306)),
        database=os.getenv("DB_NAME"),
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        driver="mysql+pymysql",
    )
    app = FastAPI(title="MarketSafe API")

    uploads_dir = Path(__file__).resolve().parents[1] / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # routers
    app.include_router(account_router)
    app.include_router(listing_router)
    app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

    # exception handlers
    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)

    # app.state.media_storage = MediaStorageUtility(
    #     endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
    #     access_key=os.getenv("MINIO_ROOT_USER", "minioadmin"),
    #     secret_key=os.getenv("MINIO_ROOT_PASSWORD", "minioadmin123"),
    #     secure=os.getenv("MINIO_SECURE", "false").lower() == "true",
    #     public_base_url=os.getenv("MINIO_PUBLIC_BASE_URL", "http://localhost:9000"),
    #     ensure_bucket_on_startup=True,
    #     make_bucket_public_on_startup=True,
    # )

    return app


app = create_app()
