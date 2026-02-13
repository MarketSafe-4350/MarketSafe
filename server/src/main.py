from fastapi import FastAPI

from src.api.routes.account_routes import router as account_router


def create_app() -> FastAPI:
    app = FastAPI(title="MarketSafe API")

    # routers
    app.include_router(account_router)

    return app


app = create_app()
