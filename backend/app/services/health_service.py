from typing import Any


TEMPERATURE_WARNING = 65.0
TEMPERATURE_CRITICAL = 80.0

VIBRATION_WARNING = 2.5
VIBRATION_CRITICAL = 4.0

LOAD_WARNING = 90.0
LOAD_CRITICAL = 98.0

MOTOR_CURRENT_WARNING = 25.0
MOTOR_CURRENT_CRITICAL = 30.0


def calculate_equipment_health(
    telemetry: dict[str, Any],
) -> dict[str, Any]:

    if telemetry["emergency_stop"]:
        return {
            "status": "CRITICAL",
            "health_score": 0,
            "reason": "Emergency stop is active.",
        }

    critical_conditions = 0
    warning_conditions = 0

    reasons = []

    temperature = telemetry["temperature"]
    vibration = telemetry["vibration"]
    load = telemetry["load_percentage"]
    motor_current = telemetry["motor_current"]

    if temperature >= TEMPERATURE_CRITICAL:
        critical_conditions += 1
        reasons.append("Critical temperature")

    elif temperature >= TEMPERATURE_WARNING:
        warning_conditions += 1
        reasons.append("High temperature")

    if vibration >= VIBRATION_CRITICAL:
        critical_conditions += 1
        reasons.append("Critical vibration")

    elif vibration >= VIBRATION_WARNING:
        warning_conditions += 1
        reasons.append("High vibration")

    if load >= LOAD_CRITICAL:
        critical_conditions += 1
        reasons.append("Critical equipment load")

    elif load >= LOAD_WARNING:
        warning_conditions += 1
        reasons.append("High equipment load")

    if motor_current >= MOTOR_CURRENT_CRITICAL:
        critical_conditions += 1
        reasons.append("Critical motor current")

    elif motor_current >= MOTOR_CURRENT_WARNING:
        warning_conditions += 1
        reasons.append("High motor current")

    if critical_conditions > 0:
        status = "CRITICAL"

    elif warning_conditions > 0:
        status = "WARNING"

    else:
        status = "NORMAL"

    if status == "NORMAL":
        health_score = 100

    elif status == "WARNING":
        health_score = max(
            70 - ((warning_conditions - 1) * 10),
            50,
        )

    else:
        health_score = max(
            40 - ((critical_conditions - 1) * 10),
            10,
        )

    return {
        "status": status,
        "health_score": health_score,
        "reason": (
            ", ".join(reasons)
            if reasons
            else "All monitored parameters are within normal limits."
        ),
    }