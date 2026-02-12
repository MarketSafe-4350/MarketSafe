from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="MarketSafe API")

    return app


app = create_app()
