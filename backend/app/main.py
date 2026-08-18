from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.db.database import init_sqlite_db_and_seed
from app.api import (
    dashboard, inventory, sales, purchases, advisor, reports, intelligence, analytics
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Only run auto-creation & seeding for local SQLite development/testing
    init_sqlite_db_and_seed()
    yield

app = FastAPI(
    title="MARUTHI — AI Retail Copilot for Small Retailers",
    description="MSME Business Intelligence & Demand Forecasting API",
    version="0.1.0",
    lifespan=lifespan
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core Health Endpoint (Constraint 1: GET /api/health)
@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "app": "MARUTHI",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT
    }

# Include target API routers
app.include_router(dashboard.router)
app.include_router(inventory.router)
app.include_router(sales.router)
app.include_router(purchases.router)
app.include_router(analytics.router)
app.include_router(advisor.router)
app.include_router(intelligence.router)
app.include_router(reports.router)
