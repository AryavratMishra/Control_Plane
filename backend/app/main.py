from __future__ import annotations

import logging
import structlog
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.session import engine, Base, AsyncSessionLocal
from app.api.routes_gateway import router as gateway_router
from app.api.routes_dashboard import router as dashboard_router, router_incidents
from app.api.routes_policies import router as policies_router
from app.api.routes_demo import router as demo_router
from app.api.routes_health import router as health_router
from app.api.routes_ws import router as ws_router

settings = get_settings()

# Configure structured logging
logging.basicConfig(level=getattr(logging, settings.log_level, logging.INFO))
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(
        getattr(logging, settings.log_level, logging.INFO)
    )
)
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle."""
    logger.info("ControlPlane.ai starting up...")
    # Create all DB tables (Alembic manages migrations in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized")

    # Load in-memory evidence for demo mode
    try:
        from app.seed.seed_demo_data import seed_in_memory_evidence, seed_demo_data
        await seed_in_memory_evidence()
        logger.info("Demo evidence loaded into memory")
        # Seed DB data (idempotent)
        async with AsyncSessionLocal() as db:
            await seed_demo_data(db)
    except Exception as e:
        logger.warning(f"Demo seed warning: {e}")

    yield

    logger.info("ControlPlane.ai shutting down...")
    await engine.dispose()


app = FastAPI(
    title="ControlPlane.ai",
    description="Real-time AI Governance & Control Layer",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server and any origin for demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(gateway_router, prefix="/api/v1/gateway", tags=["gateway"])
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(router_incidents, prefix="/api/v1/incidents", tags=["incidents"])
app.include_router(policies_router, prefix="/api/v1/policies", tags=["policies"])
app.include_router(demo_router, prefix="/api/v1/demo", tags=["demo"])
app.include_router(ws_router, prefix="/ws", tags=["websocket"])


@app.get("/")
async def root():
    return {
        "service": "ControlPlane.ai",
        "tagline": "Detect AI risk before it becomes a business incident",
        "docs": "/docs",
        "health": "/health",
    }
