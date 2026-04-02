"""
FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from config import settings
from database.connection import init_db, close_db
from routes import auth, campaigns, accounts, recommendations
from tasks.scheduler import start_scheduler, stop_scheduler

# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url=settings.API_DOCS_URL,
    redoc_url=settings.API_REDOC_URL,
    debug=settings.DEBUG,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(campaigns.router, prefix=settings.API_V1_PREFIX)
app.include_router(accounts.router, prefix=settings.API_V1_PREFIX)
app.include_router(recommendations.router, prefix=settings.API_V1_PREFIX)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Marketing Manager",
        "docs": f"{settings.API_DOCS_URL}",
        "version": settings.APP_VERSION,
    }


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'N/A'}")

    # Initialize database
    try:
        await init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.warning(f"⚠️ Database initialization: {str(e)}")

    # Start scheduler
    try:
        start_scheduler()
        logger.info("✅ Scheduler started successfully")
    except Exception as e:
        logger.warning(f"⚠️ Scheduler startup: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info(f"Shutting down {settings.APP_NAME}")

    # Stop scheduler
    try:
        stop_scheduler()
        logger.info("✅ Scheduler stopped")
    except Exception as e:
        logger.warning(f"⚠️ Error stopping scheduler: {str(e)}")

    # Close database
    try:
        await close_db()
        logger.info("✅ Database connection closed")
    except Exception as e:
        logger.warning(f"⚠️ Error closing database: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
