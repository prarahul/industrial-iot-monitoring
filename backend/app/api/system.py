from datetime import datetime, timezone

from fastapi import APIRouter
from app.core.config import settings
from app.services.database import get_connection

router = APIRouter(
    prefix="/api/system",
    tags=["System"],
)


@router.get("/health")
def system_health():
    database_status = "disconnected"

    try:
        conn = get_connection()

        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()

            database_status = "connected"
        finally:
            conn.close()

    except Exception:
        database_status = "disconnected"

    mqtt_status = "configured"

    status = (
        "healthy"
        if database_status == "connected"
        else "degraded"
    )

    return {
        "status": status,
        "database": database_status,
        "mqtt": mqtt_status,
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
    }