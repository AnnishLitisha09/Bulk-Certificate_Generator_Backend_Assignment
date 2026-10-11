"""
API endpoints router definitions.
"""
from fastapi import APIRouter
from app.api.jobs import router as jobs_router
from app.api.recipients import router as recipients_router
from app.api.certificates import router as certificates_router

api_router = APIRouter()
api_router.include_router(jobs_router)
api_router.include_router(recipients_router)
api_router.include_router(certificates_router)

__all__ = ["api_router"]
