from fastapi import APIRouter, Query

from app.services.database import get_connection


router = APIRouter(
    prefix="/api/alerts",
    tags=["Alerts"],
)


@router.get("")
def get_alerts(
    equipment_id: str = Query(
        ...,
        description="Equipment ID",
    ),
    status: str | None = Query(
        None,
        description="Optional alert status filter",
    ),
    limit: int = Query(
        50,
        ge=1,
        le=500,
        description="Maximum number of alerts to return",
    ),
):
    conn = get_connection()

    try:
        with conn.cursor() as cursor:

            # -------------------------------------------------
            # Build query
            # -------------------------------------------------

            query = """
                SELECT
                    id,
                    equipment_id,
                    timestamp,
                    alert_type,
                    severity,
                    message,
                    value,
                    threshold,
                    status,
                    created_at
                FROM alerts
                WHERE equipment_id = %s
            """

            parameters = [
                equipment_id
            ]

            # -------------------------------------------------
            # Optional status filter
            # -------------------------------------------------

            if status:
                query += """
                    AND status = %s
                """

                parameters.append(
                    status.upper()
                )

            # -------------------------------------------------
            # Latest alerts first
            # -------------------------------------------------

            query += """
                ORDER BY timestamp DESC
                LIMIT %s
            """

            parameters.append(limit)

            cursor.execute(
                query,
                parameters,
            )

            rows = cursor.fetchall()

        # -----------------------------------------------------
        # Convert database rows to API response
        # -----------------------------------------------------

        return [
            {
                "id": row[0],
                "equipment_id": row[1],
                "timestamp": row[2],
                "type": row[3],
                "severity": row[4],
                "message": row[5],
                "value": row[6],
                "threshold": row[7],
                "status": row[8],
                "created_at": row[9],
            }
            for row in rows
        ]

    finally:
        conn.close()