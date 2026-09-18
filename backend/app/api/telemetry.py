from fastapi import APIRouter, Query
from app.schemas.telemetry import TelemetryResponse
from app.services.database import get_connection

router = APIRouter(
    prefix="/api/telemetry",
    tags=["Telemetry"],
)


@router.get(
    "/latest",
    response_model=list[TelemetryResponse],
)
def get_latest_telemetry():
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    equipment_id,
                    timestamp,
                    temperature,
                    vibration,
                    load_percentage,
                    motor_current,
                    rpm,
                    operating_hours,
                    emergency_stop
                FROM telemetry
                ORDER BY timestamp DESC
                LIMIT 20
                """
            )

            rows = cursor.fetchall()

        return [
            {
                "equipment_id": row[0],
                "timestamp": row[1],
                "temperature": row[2],
                "vibration": row[3],
                "load_percentage": row[4],
                "motor_current": row[5],
                "rpm": row[6],
                "operating_hours": row[7],
                "emergency_stop": row[8],
            }
            for row in rows
        ]

    finally:
        conn.close()


@router.get(
    "/history",
    response_model=list[TelemetryResponse],
)
def get_telemetry_history(
    equipment_id: str = Query(
        ...,
        description="Equipment ID",
    ),
    minutes: int = Query(
        30,
        ge=1,
        le=1440,
        description="History window in minutes",
    ),
):
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    equipment_id,
                    timestamp,
                    temperature,
                    vibration,
                    load_percentage,
                    motor_current,
                    rpm,
                    operating_hours,
                    emergency_stop
                FROM telemetry
                WHERE equipment_id = %s
                  AND timestamp >= NOW() - (%s * INTERVAL '1 minute')
                ORDER BY timestamp ASC
                """,
                (
                    equipment_id,
                    minutes,
                ),
            )

            rows = cursor.fetchall()

        return [
            {
                "equipment_id": row[0],
                "timestamp": row[1],
                "temperature": row[2],
                "vibration": row[3],
                "load_percentage": row[4],
                "motor_current": row[5],
                "rpm": row[6],
                "operating_hours": row[7],
                "emergency_stop": row[8],
            }
            for row in rows
        ]

    finally:
        conn.close()