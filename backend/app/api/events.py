from fastapi import APIRouter, Query

from app.services.database import get_connection


router = APIRouter(
    prefix="/api/events",
    tags=["Events"],
)


@router.get("")
def get_events(
    equipment_id: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
):
    conn = get_connection()

    try:
        conditions = []
        parameters = []

        if equipment_id:
            conditions.append("equipment_id = %s")
            parameters.append(equipment_id)

        if event_type:
            conditions.append("event_type = %s")
            parameters.append(event_type)

        if severity:
            conditions.append("severity = %s")
            parameters.append(severity)

        query = """
            SELECT
                id,
                equipment_id,
                event_type,
                event_time,
                severity,
                source,
                message,
                metadata,
                created_at
            FROM equipment_events
        """

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += """
            ORDER BY event_time DESC
            LIMIT %s
        """

        parameters.append(limit)

        with conn.cursor() as cursor:
            cursor.execute(query, parameters)
            rows = cursor.fetchall()

        events = []

        for row in rows:
            events.append(
                {
                    "id": row[0],
                    "equipment_id": row[1],
                    "event_type": row[2],
                    "event_time": row[3],
                    "severity": row[4],
                    "source": row[5],
                    "message": row[6],
                    "metadata": row[7],
                    "created_at": row[8],
                }
            )

        return {
            "count": len(events),
            "events": events,
        }

    finally:
        conn.close()