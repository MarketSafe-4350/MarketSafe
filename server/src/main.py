from fastapi import FastAPI

from src.api.errors.exception_handlers import api_error_handler
from src.api.routes.account_routes import router as account_router
from src.api.errors.api_error import ApiError


def create_app() -> FastAPI:
    """Creates and configures the FastAPI application.

    Returns:
        FastAPI: The configured FastAPI application instance.
    """
    app = FastAPI(title="MarketSafe API")

    # routers
    app.include_router(account_router)

    # exception handlers
    app.add_exception_handler(ApiError, api_error_handler)

    return app


app = create_app()
