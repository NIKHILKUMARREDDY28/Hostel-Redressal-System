from fastapi import APIRouter

from api.endpoints import grievance

api_router = APIRouter()

api_router.include_router(grievance.router)