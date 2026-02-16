import os

from fastapi import FastAPI

from src.api.errors.exception_handlers import api_error_handler
from src.api.routes.account_routes import router as account_router
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


    app = FastAPI(title="MarketSafe API")

    # routers
    app.include_router(account_router)

    # exception handlers
    app.add_exception_handler(ApiError, api_error_handler)

    return app


app = create_app()
