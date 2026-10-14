from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.api.v1.endpoints.health import get_health

from contextlib import asynccontextmanager
from app.core.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database schema is initialized
    init_db()
    yield

# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AgriLink — Direct Agricultural Marketplace Backend API with AI & Blockchain support.",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Set all CORS enabled origins
cors_origins = [str(origin) for origin in settings.BACKEND_CORS_ORIGINS] if settings.BACKEND_CORS_ORIGINS else []
for fallback_origin in ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"]:
    if fallback_origin not in cors_origins:
        cors_origins.append(fallback_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Include Phase 3 Core Direct API Router (/api/listings, /api/orders, /api/seed)
from app.api.v1.endpoints import listings, ai, logistics_api, traceability_api
app.include_router(listings.router, prefix="/api", tags=["Marketplace Listings & Orders"])
app.include_router(listings.router, prefix=settings.API_V1_STR, tags=["Marketplace Listings & Orders"])

# Include Phase 4 AI Market Intelligence Router (/api/ai/forecast, /api/ai/price-intelligence, /api/ai/anomalies, /api/ai/advisory)
app.include_router(ai.router, prefix="/api/ai", tags=["AI Market Intelligence"])
app.include_router(ai.router, prefix=f"{settings.API_V1_STR}/ai", tags=["AI Market Intelligence"])

# Include Phase 5 Logistics & Multi-Farm Dispatch Router (/api/logistics, /api/logistics/calculate, /api/logistics/consolidate)
app.include_router(logistics_api.router, prefix="/api/logistics", tags=["Logistics & Fleet"])
app.include_router(logistics_api.router, prefix=f"{settings.API_V1_STR}/logistics", tags=["Logistics & Fleet"])

# Include Phase 6 Traceability & Blockchain Router (/api/traceability, /api/blockchain)
app.include_router(traceability_api.router, prefix="/api", tags=["Traceability & Blockchain"])
app.include_router(traceability_api.router, prefix=settings.API_V1_STR, tags=["Traceability & Blockchain"])


@app.get("/", summary="Root Index Endpoint")
def read_root():
    """Returns basic service information and links to API documentation."""
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "documentation": "/docs",
        "health_check": "/api/health",
    }


# Convenience /api/health and top-level /health endpoints
@app.get("/api/health", summary="API Health Check")
def api_health():
    """Direct /api/health status check endpoint."""
    return get_health()


@app.get("/health", summary="Top-Level Health Check")
def top_level_health():
    """Convenience alias for health check."""
    return get_health()
