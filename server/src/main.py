import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.errors.exception_handlers import api_error_handler
from src.api.routes.account_routes import create_account_router
from src.business_logic.services.account_service import AccountService
from src.api.errors.api_error import ApiError
from src.business_logic.managers.account import AccountManager
from src.db import DBUtility
from src.db.account.mysql import MySQLAccountDB


def create_app() -> FastAPI:
    """Creates and configures the FastAPI application.

    Returns:
        FastAPI: The configured FastAPI application instance.
    """
    print("Initializing DBUtility...")
    host = os.getenv("DB_HOST", "127.0.0.1")

    DBUtility.initialize(
        host=host,  # because you're running this on your Mac
        port=3306,
        database="marketsafe",
        username="marketsafe",
        password="marketsafe",
        driver="mysql+pymysql",
    )

    db = DBUtility.instance()

    account_db = MySQLAccountDB(db=db)

    """
    AccountManager is the sole gateway to the account table.

    All account-related operations must go through this manager.
    Direct database access outside this layer is prohibited.

    This centralizes validation, business rules, and error handling,
    and keeps the architecture clean and testable.
    
    pass it to wherever you need it
    """
    acc_db_manager = AccountManager(account_db=account_db)

    # build service that uses the manager
    account_service = AccountService(account_manager=acc_db_manager)

    # create router bound to that service and include it
    account_router = create_account_router(account_service)

    app = FastAPI(title="MarketSafe API")

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:4200", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # routers
    app.include_router(account_router)

    # exception handlers
    app.add_exception_handler(ApiError, api_error_handler)

    return app


app = create_app()
