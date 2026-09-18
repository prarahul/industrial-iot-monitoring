from fastapi import APIRouter, Query

from app.services.database import get_connection
from app.services.health_service import calculate_equipment_health


router = APIRouter(
    prefix="/api/health",
    tags=["Health"],
)


def row_to_telemetry(row):
    return {
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


@router.get("")
def get_equipment_health(
    equipment_id: str = Query(
        ...,
        description="Equipment ID",
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
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                (equipment_id,),
            )

            row = cursor.fetchone()

        if not row:
            return {
                "equipment_id": equipment_id,
                "status": "UNKNOWN",
                "health_score": 0,
                "reason": (
                    "No telemetry data available "
                    "for this equipment."
                ),
            }

        telemetry = row_to_telemetry(row)
        health = calculate_equipment_health(
            telemetry
        )

        return {
            "equipment_id": telemetry[
                "equipment_id"
            ],
            "timestamp": telemetry[
                "timestamp"
            ],
            **health,
        }

    finally:
        conn.close()


@router.get("/fleet")
def get_fleet_health():
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT DISTINCT ON (equipment_id)
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
                ORDER BY
                    equipment_id,
                    timestamp DESC
                """
            )

            rows = cursor.fetchall()

        fleet_health = []

        for row in rows:
            telemetry = row_to_telemetry(row)

            health = calculate_equipment_health(
                telemetry
            )

            fleet_health.append(
                {
                    "equipment_id": telemetry[
                        "equipment_id"
                    ],
                    "timestamp": telemetry[
                        "timestamp"
                    ],
                    **health,
                }
            )

        fleet_health.sort(
            key=lambda item: item["equipment_id"]
        )

        return fleet_health

    finally:
        conn.close()