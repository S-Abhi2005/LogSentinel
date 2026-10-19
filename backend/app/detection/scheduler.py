import asyncio
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.db.session import SessionLocal
from app.detection.engine import detection_engine
from app.models.incident import Incident

INACTIVITY_LOCK_ID = 849201982  # Deterministic 32-bit advisory lock ID for PostgreSQL

def run_inactivity_check_sync(reference_time: Optional[datetime] = None) -> List[Incident]:
    """
    Executes a single inactivity check cycle synchronously with database session safety
    and cross-worker PostgreSQL advisory locking.
    """
    db: Session = SessionLocal()
    has_lock = False
    try:
        # Check dialect for PostgreSQL advisory lock coordination
        if db.bind and db.bind.dialect.name == "postgresql":
            try:
                acquired = db.execute(
                    text("SELECT pg_try_advisory_lock(:lock_id)"),
                    {"lock_id": INACTIVITY_LOCK_ID}
                ).scalar()
                if not acquired:
                    logger.debug("Inactivity check skipped: another worker holds advisory lock.")
                    return []
                has_lock = True
            except Exception as lock_err:
                logger.warning(f"Advisory lock check skipped: {lock_err}")

        triggered = detection_engine.check_service_inactivity(db, reference_time=reference_time)
        return triggered
    except Exception as e:
        logger.error(f"Error during service inactivity check: {e}", exc_info=True)
        return []
    finally:
        if has_lock:
            try:
                db.execute(
                    text("SELECT pg_advisory_unlock(:lock_id)"),
                    {"lock_id": INACTIVITY_LOCK_ID}
                )
                db.commit()
            except Exception as e:
                logger.error(f"Error releasing advisory lock: {e}")
        db.close()


async def inactivity_scheduler_loop(interval_seconds: Optional[int] = None):
    """
    Lifecycle-managed background loop that runs inactivity checks periodically
    without blocking the FastAPI event loop.
    """
    interval = interval_seconds or settings.INACTIVITY_CHECK_INTERVAL_SECONDS
    logger.info(f"Service inactivity scheduler started (interval: {interval}s).")
    try:
        while True:
            await asyncio.sleep(interval)
            try:
                # Run sync DB logic in worker thread to prevent event loop blocking
                await asyncio.to_thread(run_inactivity_check_sync)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"Unexpected error in inactivity scheduler worker: {e}", exc_info=True)
    except asyncio.CancelledError:
        logger.info("Service inactivity scheduler loop cancelled cleanly.")
        raise
