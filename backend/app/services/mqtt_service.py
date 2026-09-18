import asyncio
import json

import paho.mqtt.client as mqtt

from app.core.config import settings
from app.services.alert_service import evaluate_telemetry
from app.services.database import get_connection
from app.services.event_service import create_event
from app.services.websocket_manager import manager


# =========================================================
# ASYNCIO EVENT LOOP
# =========================================================

event_loop = None

previous_equipment_states: dict[str, str] = {}


def set_event_loop(loop):
    global event_loop
    event_loop = loop


# =========================================================
# WEBSOCKET BROADCAST
# =========================================================

def broadcast_telemetry(payload: dict):
    if event_loop is None:
        print("WebSocket event loop not available.")
        return

    try:
        asyncio.run_coroutine_threadsafe(
            manager.broadcast(
                {
                    "type": "telemetry",
                    "data": payload,
                }
            ),
            event_loop,
        )

    except Exception as error:
        print(
            f"WebSocket broadcast error: {error}"
        )


# =========================================================
# EQUIPMENT EVENT PROCESSING
# =========================================================

def process_equipment_event(payload: dict):
    equipment_id = payload["equipment_id"]
    current_state = payload.get("state")

    if not current_state:
        return

    previous_state = previous_equipment_states.get(
        equipment_id
    )

    # First telemetry message establishes the
    # initial state. We don't create an event because
    # nothing has changed yet.
    if previous_state is None:
        previous_equipment_states[
            equipment_id
        ] = current_state

        return

    # No state change.
    if current_state == previous_state:
        return

    print(
        f"EVENT | {equipment_id}: "
        f"{previous_state} -> {current_state}"
    )

    # =====================================================
    # FAULT DETECTED
    # =====================================================

    if current_state == "FAULT":

        create_event(
            equipment_id=equipment_id,
            event_type="FAULT_DETECTED",
            event_time=payload["timestamp"],
            severity="CRITICAL",
            source="MQTT",
            message=(
                f"Equipment changed state from "
                f"{previous_state} to FAULT"
            ),
            metadata={
                "previous_state": previous_state,
                "current_state": current_state,
                "temperature": payload["temperature"],
                "vibration": payload["vibration"],
                "load_percentage": payload[
                    "load_percentage"
                ],
                "motor_current": payload[
                    "motor_current"
                ],
            },
        )

    # =====================================================
    # EMERGENCY STOP
    # =====================================================

    elif current_state == "EMERGENCY_STOP":

        create_event(
            equipment_id=equipment_id,
            event_type="EMERGENCY_STOP",
            event_time=payload["timestamp"],
            severity="CRITICAL",
            source="MQTT",
            message="Emergency stop activated.",
            metadata={
                "previous_state": previous_state,
                "current_state": current_state,
            },
        )

    # =====================================================
    # MAINTENANCE STARTED
    # =====================================================

    elif current_state == "MAINTENANCE":

        create_event(
            equipment_id=equipment_id,
            event_type="MAINTENANCE_STARTED",
            event_time=payload["timestamp"],
            severity="INFO",
            source="MQTT",
            message=(
                "Equipment entered maintenance state."
            ),
            metadata={
                "previous_state": previous_state,
                "current_state": current_state,
            },
        )

    # =====================================================
    # MAINTENANCE COMPLETED
    # =====================================================

    elif previous_state == "MAINTENANCE":

        create_event(
            equipment_id=equipment_id,
            event_type="MAINTENANCE_COMPLETED",
            event_time=payload["timestamp"],
            severity="INFO",
            source="MQTT",
            message=(
                "Equipment exited maintenance state."
            ),
            metadata={
                "previous_state": previous_state,
                "current_state": current_state,
            },
        )

    # =====================================================
    # NORMAL STATE CHANGE
    # =====================================================

    else:

        create_event(
            equipment_id=equipment_id,
            event_type="STATE_CHANGED",
            event_time=payload["timestamp"],
            severity="INFO",
            source="MQTT",
            message=(
                f"Equipment changed state from "
                f"{previous_state} to {current_state}"
            ),
            metadata={
                "previous_state": previous_state,
                "current_state": current_state,
            },
        )

    # Update state AFTER processing the event.
    previous_equipment_states[
        equipment_id
    ] = current_state


# =========================================================
# MQTT CONNECT
# =========================================================

def on_connect(
    client,
    userdata,
    flags,
    reason_code,
    properties,
):
    if reason_code == 0:

        print("Connected to MQTT broker")

        client.subscribe(
            settings.mqtt_topic
        )

        print(
            f"Subscribed to: "
            f"{settings.mqtt_topic}"
        )

    else:

        print(
            f"MQTT connection failed: "
            f"{reason_code}"
        )


# =========================================================
# MQTT MESSAGE
# =========================================================

def on_message(
    client,
    userdata,
    message,
):
    try:

        payload = json.loads(
            message.payload.decode()
        )

        print("Telemetry received:")
        print(payload)

        # =================================================
        # PROCESS EQUIPMENT EVENTS
        # =================================================

        process_equipment_event(
            payload
        )

        # =================================================
        # BROADCAST TELEMETRY TO WEBSOCKET CLIENTS
        # =================================================

        broadcast_telemetry(
            payload
        )

        # =================================================
        # EVALUATE ALERTS
        # =================================================

        alerts = evaluate_telemetry(
            payload
        )

        conn = get_connection()

        try:

            with conn.cursor() as cursor:

                # =================================================
                # STORE TELEMETRY
                # =================================================

                cursor.execute(
                    """
                    INSERT INTO telemetry (
                        equipment_id,
                        timestamp,
                        temperature,
                        vibration,
                        load_percentage,
                        motor_current,
                        rpm,
                        operating_hours,
                        emergency_stop
                    )
                    VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s
                    )
                    """,
                    (
                        payload["equipment_id"],
                        payload["timestamp"],
                        payload["temperature"],
                        payload["vibration"],
                        payload["load_percentage"],
                        payload["motor_current"],
                        payload["rpm"],
                        payload["operating_hours"],
                        payload["emergency_stop"],
                    ),
                )

                print(
                    "Telemetry stored in PostgreSQL"
                )

                # =================================================
                # CURRENT ALERT TYPES
                # =================================================

                current_alert_types = {
                    alert["type"]
                    for alert in alerts
                }

                # =================================================
                # PROCESS CURRENT ALERTS
                # =================================================

                for alert in alerts:

                    print(
                        f"ALERT [{alert['severity']}] "
                        f"{alert['type']}: "
                        f"{alert['message']}"
                    )

                    alert_value = alert[
                        "value"
                    ]

                    alert_threshold = alert[
                        "threshold"
                    ]

                    # Emergency stop values are boolean.
                    # Database value and threshold
                    # columns are numeric.

                    if isinstance(
                        alert_value,
                        bool,
                    ):
                        alert_value = None

                    if isinstance(
                        alert_threshold,
                        bool,
                    ):
                        alert_threshold = None

                    # =================================================
                    # CHECK EXISTING ACTIVE ALERT
                    # =================================================

                    cursor.execute(
                        """
                        SELECT id
                        FROM alerts
                        WHERE equipment_id = %s
                          AND alert_type = %s
                          AND status = 'ACTIVE'
                        LIMIT 1
                        """,
                        (
                            payload[
                                "equipment_id"
                            ],
                            alert["type"],
                        ),
                    )

                    existing_alert = (
                        cursor.fetchone()
                    )

                    if existing_alert:

                        print(
                            f"Existing active alert "
                            f"found for "
                            f"{payload['equipment_id']} "
                            f"- {alert['type']}. "
                            f"Skipping duplicate."
                        )

                        continue

                    # =================================================
                    # CREATE NEW ACTIVE ALERT
                    # =================================================

                    cursor.execute(
                        """
                        INSERT INTO alerts (
                            equipment_id,
                            timestamp,
                            alert_type,
                            severity,
                            message,
                            value,
                            threshold,
                            status
                        )
                        VALUES (
                            %s, %s, %s, %s,
                            %s, %s, %s, %s
                        )
                        """,
                        (
                            payload[
                                "equipment_id"
                            ],
                            payload[
                                "timestamp"
                            ],
                            alert["type"],
                            alert["severity"],
                            alert["message"],
                            alert_value,
                            alert_threshold,
                            "ACTIVE",
                        ),
                    )

                    print(
                        "New alert stored in PostgreSQL"
                    )

                # =================================================
                # RESOLVE CLEARED ALERTS
                # =================================================

                cursor.execute(
                    """
                    SELECT
                        id,
                        alert_type
                    FROM alerts
                    WHERE equipment_id = %s
                      AND status = 'ACTIVE'
                    """,
                    (
                        payload[
                            "equipment_id"
                        ],
                    ),
                )

                active_alerts = (
                    cursor.fetchall()
                )

                for (
                    alert_id,
                    alert_type,
                ) in active_alerts:

                    if (
                        alert_type
                        not in current_alert_types
                    ):

                        cursor.execute(
                            """
                            UPDATE alerts
                            SET
                                status = 'RESOLVED'
                            WHERE id = %s
                            """,
                            (
                                alert_id,
                            ),
                        )

                        print(
                            f"Alert resolved: "
                            f"{payload['equipment_id']} "
                            f"- {alert_type}"
                        )

            conn.commit()

        finally:

            conn.close()

    except json.JSONDecodeError:

        print(
            "Invalid JSON received from MQTT"
        )

    except KeyError as error:

        print(
            f"Missing telemetry field: "
            f"{error}"
        )

    except Exception as error:

        print(
            f"Database error: "
            f"{error}"
        )


# =========================================================
# START MQTT
# =========================================================

def start_mqtt():

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="industrial-iot-backend",
    )

    client.on_connect = on_connect

    client.on_message = on_message

    client.connect(
        settings.mqtt_broker,
        settings.mqtt_port,
        60,
    )

    return client