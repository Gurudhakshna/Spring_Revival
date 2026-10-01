"""JAL-RAKSHA AI backend — FastAPI entrypoint.

Run:  uvicorn main:app --reload --port 8000   (from backend/)
"""
from __future__ import annotations
import logging
import os
# Load .env before anything else (API keys, CORS)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("jal-raksha")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import api.routes as routes
from ml import model as ml_model
from services.data_provider import DemoDataProvider

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
# Secure CORS: env or fallback to localhost only (never "*" with credentials)
_cors_env = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
_cors_origins = [o.strip() for o in _cors_env.split(",") if o.strip()]

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cache static datasets in memory + train/load ML model once.
    try:
        provider.get_springs(); provider.get_villages()
        provider.get_wells(); provider.get_intervention_costs()
    except Exception as e:
        logger.warning("dataset preload issue: %s", e)
    try:
        ml_model.get_bundle()
        logger.info("ML model ready")
    except Exception as e:
        logger.warning("ML model unavailable at startup: %s", e)
    # Pre-warm early warning cache to avoid 5-10s delay on first request.
    try:
        from services import early_warning as ew_svc
        ew_svc.all_warnings(min_level="WATCH", limit=200)
        logger.info("Early-warning cache warmed")
    except Exception as e:
        logger.warning("Early-warning cache warm skipped: %s", e)
    yield

app = FastAPI(title="JAL-RAKSHA AI",
              description="AI-powered spring revival & recharge planning (prototype decision support)",
              version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

provider = DemoDataProvider(DATA_DIR)
routes.provider = provider
routes.ml = ml_model
routes.ADMIN_KEY = os.getenv("ADMIN_KEY") or None
app.include_router(routes.router)


@app.get("/")
def root():
    return {"service": "JAL-RAKSHA AI backend",
            "docs": "/docs", "health": "/api/health",
            "disclaimer": "Prototype Decision-Support Estimate"}
