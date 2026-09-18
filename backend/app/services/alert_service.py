from typing import Any


# Initial operating thresholds for the simulated crane.
TEMPERATURE_WARNING = 65.0
VIBRATION_WARNING = 2.5
LOAD_WARNING = 90.0
MOTOR_CURRENT_WARNING = 25.0


def evaluate_telemetry(telemetry: dict[str, Any]) -> list[dict[str, Any]]:
    alerts = []

    if telemetry["temperature"] >= TEMPERATURE_WARNING:
        alerts.append(
            {
                "type": "HIGH_TEMPERATURE",
                "severity": "WARNING",
                "message": (
                    f"Temperature is {telemetry['temperature']}°C"
                ),
                "value": telemetry["temperature"],
                "threshold": TEMPERATURE_WARNING,
            }
        )

    if telemetry["vibration"] >= VIBRATION_WARNING:
        alerts.append(
            {
                "type": "HIGH_VIBRATION",
                "severity": "WARNING",
                "message": (
                    f"Vibration is {telemetry['vibration']} mm/s"
                ),
                "value": telemetry["vibration"],
                "threshold": VIBRATION_WARNING,
            }
        )

    if telemetry["load_percentage"] >= LOAD_WARNING:
        alerts.append(
            {
                "type": "HIGH_LOAD",
                "severity": "WARNING",
                "message": (
                    f"Equipment load is "
                    f"{telemetry['load_percentage']}%"
                ),
                "value": telemetry["load_percentage"],
                "threshold": LOAD_WARNING,
            }
        )

    if telemetry["motor_current"] >= MOTOR_CURRENT_WARNING:
        alerts.append(
            {
                "type": "HIGH_MOTOR_CURRENT",
                "severity": "WARNING",
                "message": (
                    f"Motor current is "
                    f"{telemetry['motor_current']} A"
                ),
                "value": telemetry["motor_current"],
                "threshold": MOTOR_CURRENT_WARNING,
            }
        )

    if telemetry["emergency_stop"]:
        alerts.append(
            {
                "type": "EMERGENCY_STOP",
                "severity": "CRITICAL",
                "message": "Emergency stop is active.",
                "value": True,
                "threshold": False,
            }
        )

    return alerts