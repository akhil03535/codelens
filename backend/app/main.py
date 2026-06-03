import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth_routes import router as auth_router
from app.api.repository_routes import router as repo_router
from app.api.chat_routes import router as chat_router
from app.api.analysis_routes import router as analysis_router
from app.config.settings import settings
from app.database.session import create_tables

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting CodeLens AI API")
    await create_tables()
    # Warm up embedding model
    from app.rag.embeddings import get_model
    get_model()
    logger.info("Startup complete")
    yield
    from app.graph.neo4j_service import close_driver
    close_driver()
    logger.info("Shutdown complete")


app = FastAPI(
    title="CodeLens AI",
    description="AI-powered codebase understanding platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PREFIX = settings.API_PREFIX
app.include_router(auth_router, prefix=PREFIX)
app.include_router(repo_router, prefix=PREFIX)
app.include_router(chat_router, prefix=PREFIX)
app.include_router(analysis_router, prefix=PREFIX)


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}
