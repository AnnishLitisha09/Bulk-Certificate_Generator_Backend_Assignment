"""
Main FastAPI application entry point.
Initializes routes, database tables, middleware, static files, and exception handling.
"""

from contextlib import asynccontextmanager
import logging
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.config import get_settings
from app.database import init_db
from app.models import utc_now
from app.schemas import HealthResponse

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("bulk_certificate_generator")

settings = get_settings()
STATIC_DIR = Path("static").resolve()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle hook for startup and shutdown actions."""
    logger.info("Initializing database and storage directories...")
    init_db()
    settings.storage_path.mkdir(parents=True, exist_ok=True)
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Application ready to receive requests.")
    yield
    logger.info("Application shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Production-minded Bulk Certificate Generator backend API. "
        "Allows generating PDF certificates from bulk recipient requests, "
        "tracking job statuses, handling partial failures gracefully, "
        "and downloading generated PDF documents."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Enable CORS for frontend interoperability
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API endpoints
app.include_router(api_router)

# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Format request-level Pydantic validation errors with clear, consistent messages
    without exposing internal code details.
    """
    errors = []
    for err in exc.errors():
        field_path = " -> ".join(str(loc) for loc in err.get("loc", []))
        errors.append({
            "field": field_path,
            "message": err.get("msg", "Invalid value"),
            "type": err.get("type", "validation_error"),
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Request validation failed",
            "errors": errors,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Catch unhandled errors and return a clean 500 error response without
    leaking internal stack traces or filesystem paths to API consumers.
    """
    logger.exception("Unhandled server error processing request %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred while processing your request.",
        },
    )


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check endpoint",
    description="Returns current operational status of the service.",
)
def health_check() -> HealthResponse:
    """Check service health and uptime."""
    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        version="1.0.0",
        timestamp=utc_now(),
    )


@app.get(
    "/",
    tags=["Frontend"],
    include_in_schema=False,
)
def serve_frontend():
    """Serve the minimal studio frontend at root."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "documentation": "/docs",
        "health": "/health",
    }
