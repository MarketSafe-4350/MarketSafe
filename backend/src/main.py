from fastapi import FastAPI

# uvicorn app.main:app --reload --port 8000
# (app.main => python module path)
# (:app => app variable below)
app = FastAPI(title="test MarketSafe")


@app.get("/api/hello")
def read_root():
    return {"hello": "world"}


@app.get("/api/health")
async def health():
    return {"status": "ok"}
