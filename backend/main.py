"""JAL-RAKSHA AI backend — FastAPI entrypoint.

Run:  uvicorn main:app --reload --port 8000   (from backend/)
"""
from __future__ import annotations
import os
# Load .env before anything else (API keys, CORS)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

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
        print(f"[warn] dataset preload issue: {e}")
    try:
        ml_model.get_bundle()
        print("[ok] ML model ready")
    except Exception as e:
        print(f"[warn] ML model unavailable at startup: {e}")
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
app.include_router(routes.router)


@app.get("/")
def root():
    return {"service": "JAL-RAKSHA AI backend",
            "docs": "/docs", "health": "/api/health",
            "disclaimer": "Prototype Decision-Support Estimate"}
