from fastapi import APIRouter

from app.services.database import get_connection


router = APIRouter(
    prefix="/api/equipment",
    tags=["Equipment"],
)


@router.get("")
def get_equipment():
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
                ORDER BY equipment_id, timestamp DESC
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