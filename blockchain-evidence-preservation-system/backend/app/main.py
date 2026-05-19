"""
Blockchain Evidence Preservation System - FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import logging

from app.routes.evidence_router import router as evidence_router
from app.routes.auth_router     import router as auth_router
from app.routes.case_router     import router as case_router
from app.routes.report_router   import router as report_router
from app.routes.user_router     import router as user_router
from config.settings import settings
from core.infrastructure.database import Base, engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Blockchain Evidence Preservation System...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized.")
    yield
    logger.info("Shutting down application...")
    await engine.dispose()


app = FastAPI(
    title="Blockchain Evidence Preservation System",
    description="Tamper-proof digital evidence management with blockchain integrity.",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router,     prefix="/api/v1/auth",     tags=["Authentication"])
app.include_router(user_router,     prefix="/api/v1/users",    tags=["Users"])
app.include_router(case_router,     prefix="/api/v1/cases",    tags=["Cases"])
app.include_router(evidence_router, prefix="/api/v1/evidence", tags=["Evidence"])
app.include_router(report_router,   prefix="/api/v1",          tags=["Analysis Reports"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "version": "2.0.0", "service": "beps"}
