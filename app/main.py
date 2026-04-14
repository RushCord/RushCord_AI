import logging

from fastapi import FastAPI

from app.api.routes import router as api_router
from app.core.config import get_settings

settings = get_settings()
logging.basicConfig(level=settings.log_level)

app = FastAPI(title="MeCord AI Service", version="1.0.0")
app.include_router(api_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
