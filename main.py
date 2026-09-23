from contextlib import asynccontextmanager
import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import build_router
from app.core.config import settings
from app.db.history import HistoryStore

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "app" / "static"
store = HistoryStore()
logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    store.initialize()
    yield


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(build_router(store))
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="ui")


if __name__ == "__main__":
    # The UI and API are deliberately served by this one FastAPI process on port 3002.
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=settings.debug, log_level=settings.log_level.lower())
