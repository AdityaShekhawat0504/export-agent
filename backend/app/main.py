from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.database import engine, Base
from app.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            print("✅ DB ready")
    except Exception as e:
        print("❌ DB startup failed:", e)
        raise e

    yield

    # Optional shutdown logic later


app = FastAPI(lifespan=lifespan)


# 🔥 Health check (IMPORTANT)
@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(router)