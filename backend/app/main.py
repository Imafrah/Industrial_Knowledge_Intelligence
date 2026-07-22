"""
FastAPI application entry point.

Unified Asset & Operations Brain — AI-powered Industrial Knowledge Intelligence.

On startup:
  1. Initializes database (creates tables, enables pgvector)
  2. Auto-seeds with mock industrial documents if DB is empty
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db, async_session
from app.seed import run_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init DB + auto-seed. Shutdown: cleanup."""
    logger.info("Starting Unified Asset & Operations Brain...")

    # Initialize database
    await init_db()
    logger.info("Database initialized.")

    # Auto-seed if empty
    async with async_session() as db:
        try:
            await run_seed(db)
        except Exception as e:
            logger.error(f"Seed error (non-fatal): {e}")

    logger.info("Backend ready.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Unified Asset & Operations Brain",
    description="AI-powered Industrial Knowledge Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from app.routers import documents, chat, maintenance, dashboard, graph, compliance, search  # noqa: E402

app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(maintenance.router)
app.include_router(dashboard.router)
app.include_router(graph.router)
app.include_router(compliance.router)
app.include_router(search.router)


@app.get("/api/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "service": "Unified Asset & Operations Brain"}
