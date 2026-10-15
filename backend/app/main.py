import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.errors import LogSentinelException
from app.db.session import engine, SessionLocal
from app.api.v1.router import api_router
from app.models.user import User, UserRole
from app.security.hashing import hash_password

setup_logging()

# In-memory token bucket for simple IP rate limiting
IP_REQUEST_COUNTS: dict[str, list[float]] = {}

def check_rate_limit(client_ip: str) -> bool:
    """Simple rate limit check per minute."""
    now = time.time()
    window = 60.0
    history = IP_REQUEST_COUNTS.setdefault(client_ip, [])
    # keep timestamps within window
    history = [t for t in history if now - t < window]
    if len(history) >= settings.RATE_LIMIT_PER_MINUTE:
        return False
    history.append(now)
    IP_REQUEST_COUNTS[client_ip] = history
    return True

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure initial admin account exists
    logger.info("Initializing LogSentinel backend...")
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == settings.INITIAL_ADMIN_EMAIL.lower()).first()
        if not admin:
            logger.info(f"Bootstrapping initial Super Admin: {settings.INITIAL_ADMIN_EMAIL}")
            admin = User(
                email=settings.INITIAL_ADMIN_EMAIL.lower(),
                hashed_password=hash_password(settings.INITIAL_ADMIN_PASSWORD),
                full_name=settings.INITIAL_ADMIN_FULL_NAME,
                role=UserRole.SUPER_ADMIN,
                is_active=True
            )
            db.add(admin)
            db.commit()
    except Exception as e:
        logger.error(f"Error during admin bootstrap: {e}")
    finally:
        db.close()
    
    yield
    logger.info("Shutting down LogSentinel backend.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise Cloud Log Intelligence and Incident Detection Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS Configuration
origins = settings.BACKEND_CORS_ORIGINS if isinstance(settings.BACKEND_CORS_ORIGINS, list) else [str(settings.BACKEND_CORS_ORIGINS)]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware: Request timing, Correlation ID, and Rate Limiting
@app.middleware("http")
async def request_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", f"req-{uuid.uuid4().hex[:12]}")
    client_ip = request.client.host if request.client else "unknown"

    # Enforce Rate Limiting
    if not check_rate_limit(client_ip):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": {"message": "Rate limit exceeded. Please throttle requests.", "code": "RATE_LIMITED"}}
        )

    start_time = time.time()
    response: Response = await call_next(request)
    process_time = time.time() - start_time
    
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    return response

# Custom Exception Handler
@app.exception_handler(LogSentinelException)
async def logsentinel_exception_handler(request: Request, exc: LogSentinelException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Health Endpoints
@app.get("/health/live", tags=["Health"])
def health_live():
    """Liveness probe confirming the FastAPI process is alive."""
    return {"status": "ok", "service": "LogSentinel Backend", "timestamp": time.time()}

@app.get("/health/ready", tags=["Health"])
def health_ready():
    """Readiness probe verifying database connectivity."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected", "timestamp": time.time()}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "database": "disconnected", "error": str(e)}
        )

# Register Main API Router
app.include_router(api_router, prefix=settings.API_V1_STR)
