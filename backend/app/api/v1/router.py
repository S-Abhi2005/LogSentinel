from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.services import router as services_router
from app.api.v1.logs import router as logs_router
from app.api.v1.rules import router as rules_router
from app.api.v1.incidents import router as incidents_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.audit import router as audit_router
from app.api.v1.dashboard import router as dashboard_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(services_router)
api_router.include_router(logs_router)
api_router.include_router(rules_router)
api_router.include_router(incidents_router)
api_router.include_router(alerts_router)
api_router.include_router(audit_router)
api_router.include_router(dashboard_router)
