from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import auth, compliance

from app.core.config import settings
from app.api.v1 import auth
from app.utils.logger import logger


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description="Automated Microsoft 365 compliance assessment tool",
        version=settings.VERSION,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    configure_middleware(app, settings)
    configure_routing(app, settings)
    configure_exception_handlers(app)
    configure_endpoints(app)

    return app


def configure_middleware(app: FastAPI, settings):
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )

    # GZip compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)


def configure_routing(app: FastAPI, settings):
    # Import the v1 router
    from app.api.v1 import router as v1_router
    # Mount the v1 router with the API prefix
    app.include_router(
        v1_router,
        prefix=settings.API_PREFIX
    )

###############################################################################
    #debugging routes cos idk why they aint working
    #useful if anyone forgets routes for different endpoints...check terminal
    #delete this if unnecessary
    for route in app.routes:
        print(f"Route: {route.path}")
###############################################################################

    # Authentication endpoints
    app.include_router(
        auth.router,
        prefix=f"{settings.API_PREFIX}/auth",
        tags=["Authentication"],
        responses={404: {"description": "Not found"}},
    )

    # Compliance endpoints 
    app.include_router(
        compliance.router,
        prefix=f"{settings.API_PREFIX}/compliance/security",
        tags=["Security Compliance"],
        responses={404: {"description": "Not found"}},
    )


def configure_exception_handlers(app: FastAPI):
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions."""
        logger.warning(
            "HTTP exception occurred",
            path=request.url.path,
            method=request.method,
            status_code=exc.status_code,
            detail=exc.detail,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail, "status_code": exc.status_code},
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle global exceptions."""
        logger.error(
            "Unhandled exception occurred",
            path=request.url.path,
            method=request.method,
            error=str(exc),
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "status_code": 500},
        )


def configure_endpoints(app: FastAPI):
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "AutoAudit API",
            "version": settings.VERSION,
            "docs": "/docs" if settings.DEBUG else None,
        }

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "version": settings.VERSION,
        }


app = create_app()
