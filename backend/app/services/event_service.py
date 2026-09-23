from typing import Any

from psycopg.types.json import Jsonb

from app.services.database import get_connection


def create_event(
    equipment_id: str,
    event_type: str,
    event_time,
    message: str,
    severity: str = "INFO",
    source: str = "SYSTEM",
    metadata: dict[str, Any] | None = None,
):
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO equipment_events (
                    equipment_id,
                    event_type,
                    event_time,
                    severity,
                    source,
                    message,
                    metadata
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    equipment_id,
                    event_type,
                    event_time,
                    severity,
                    source,
                    message,
                    Jsonb(metadata) if metadata is not None else None,
                ),
            )

        conn.commit()

    finally:
        conn.close()