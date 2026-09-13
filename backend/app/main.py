from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.config import GENERATED_DIR

from app.api import (
    videos,
    analysis,
    events,
    alerts,
    live,
)


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="SentinelAI API",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# STATIC GENERATED FILES
# ============================================================

GENERATED_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

app.mount(
    "/generated",
    StaticFiles(
        directory=str(GENERATED_DIR)
    ),
    name="generated",
)


# ============================================================
# ROUTERS
# ============================================================

app.include_router(
    videos.router
)

app.include_router(
    analysis.router
)

app.include_router(
    events.router
)

app.include_router(
    alerts.router
)

app.include_router(
    live.router
)


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def on_startup():

    init_db()


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "status": "SentinelAI backend running"
    }