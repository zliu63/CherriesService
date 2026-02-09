from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time

from app.core.config import settings
from app.core.logging import logger
from app.api.routes import auth_router, quests_router, checkins_router, profile_router, connection_router


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        docs_url=f"{settings.API_PREFIX}/docs",
        redoc_url=f"{settings.API_PREFIX}/redoc",
        openapi_url=f"{settings.API_PREFIX}/openapi.json"
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(auth_router, prefix=settings.API_PREFIX)
    app.include_router(quests_router, prefix=settings.API_PREFIX)
    app.include_router(checkins_router, prefix=settings.API_PREFIX)
    app.include_router(profile_router, prefix=settings.API_PREFIX)
    app.include_router(connection_router, prefix=settings.API_PREFIX)

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %d (%.1fms)",
            request.method, request.url.path, response.status_code, elapsed_ms,
        )
        return response

    @app.get("/")
    async def root():
        return {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "running"
        }

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    logger.info("CherriesService %s started (debug=%s)", settings.APP_VERSION, settings.DEBUG)
    return app


app = create_app()
