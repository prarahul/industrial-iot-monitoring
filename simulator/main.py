import json
import random
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt


MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "industrial/equipment/telemetry"

EQUIPMENT_IDS = [
    "CRANE-001",
    "CRANE-002",
    "CRANE-003",
]

operating_hours = {
    equipment_id: 2500.0
    for equipment_id in EQUIPMENT_IDS
}

equipment_states = {
    equipment_id: "RUNNING"
    for equipment_id in EQUIPMENT_IDS
}

state_elapsed_seconds = {
    equipment_id: 0
    for equipment_id in EQUIPMENT_IDS
}

degradation_levels = {
    equipment_id: 0.0
    for equipment_id in EQUIPMENT_IDS
}


STATE_DURATIONS = {
    "RUNNING": 15,
    "HEAVY_LOAD": 10,
    "FAULT": 8,
    "MAINTENANCE": 10,
    "IDLE": 8,
    "EMERGENCY_STOP": 5,
}


def get_next_state(current_state: str) -> str:
    if current_state == "RUNNING":
        if random.random() < 0.45:
            return "HEAVY_LOAD"

        if random.random() < 0.10:
            return "IDLE"

        return "RUNNING"

    if current_state == "HEAVY_LOAD":
        if random.random() < 0.35:
            return "FAULT"

        return "RUNNING"

    if current_state == "FAULT":
        return "MAINTENANCE"

    if current_state == "MAINTENANCE":
        return "RUNNING"

    if current_state == "IDLE":
        return "RUNNING"

    if current_state == "EMERGENCY_STOP":
        return "MAINTENANCE"

    return "RUNNING"


def update_equipment_state(equipment_id: str):
    current_state = equipment_states[equipment_id]

    state_elapsed_seconds[equipment_id] += 3

    duration = STATE_DURATIONS[current_state]

    # Controlled emergency-stop injection.
    # Emergency stops can only occur while equipment
    # is operating or under heavy load.
    if current_state in {"RUNNING", "HEAVY_LOAD"}:
        if random.random() < 0.02:
            new_state = "EMERGENCY_STOP"

            print(
                f"\nEMERGENCY EVENT | "
                f"{equipment_id}: "
                f"{current_state} -> EMERGENCY_STOP\n"
            )

            equipment_states[equipment_id] = new_state
            state_elapsed_seconds[equipment_id] = 0
            return

    if state_elapsed_seconds[equipment_id] >= duration:
        new_state = get_next_state(current_state)

        if new_state != current_state:
            print(
                f"\nSTATE CHANGE | "
                f"{equipment_id}: "
                f"{current_state} -> {new_state}\n"
            )

        equipment_states[equipment_id] = new_state
        state_elapsed_seconds[equipment_id] = 0

        # Reset degradation after maintenance.
        if new_state == "MAINTENANCE":
            degradation_levels[equipment_id] = 0.0


def calculate_degradation(equipment_id: str) -> float:
    state = equipment_states[equipment_id]

    if state == "HEAVY_LOAD":
        degradation_levels[equipment_id] += 0.08

    elif state == "FAULT":
        degradation_levels[equipment_id] += 0.15

    elif state == "RUNNING":
        degradation_levels[equipment_id] += 0.01

    elif state == "MAINTENANCE":
        degradation_levels[equipment_id] = max(
            degradation_levels[equipment_id] - 0.5,
            0.0,
        )

    else:
        degradation_levels[equipment_id] = max(
            degradation_levels[equipment_id] - 0.02,
            0.0,
        )

    return degradation_levels[equipment_id]


def generate_telemetry(equipment_id: str):
    state = equipment_states[equipment_id]

    degradation = calculate_degradation(
        equipment_id
    )

    if state == "IDLE":
        load_percentage = random.uniform(0, 10)
        temperature = random.uniform(35, 45)
        motor_current = random.uniform(2, 5)
        vibration = random.uniform(0.2, 0.5)
        rpm = random.randint(0, 300)

    elif state == "RUNNING":
        load_percentage = random.uniform(20, 90)

        temperature = (
            45
            + (load_percentage * 0.22)
            + degradation * 0.15
            + random.uniform(-3, 3)
        )

        motor_current = (
            8
            + (load_percentage * 0.18)
            + degradation * 0.08
            + random.uniform(-1.5, 1.5)
        )

        vibration = (
            0.8
            + (load_percentage * 0.015)
            + degradation * 0.015
            + random.uniform(-0.25, 0.25)
        )

        rpm = random.randint(1000, 1600)

    elif state == "HEAVY_LOAD":
        load_percentage = random.uniform(85, 98)

        temperature = (
            62
            + (load_percentage * 0.12)
            + degradation * 0.20
            + random.uniform(-2, 2)
        )

        motor_current = (
            20
            + (load_percentage * 0.08)
            + degradation * 0.10
            + random.uniform(-1, 1)
        )

        vibration = (
            1.5
            + (load_percentage * 0.008)
            + degradation * 0.02
            + random.uniform(-0.15, 0.15)
        )

        rpm = random.randint(900, 1400)

    elif state == "FAULT":
        load_percentage = random.uniform(70, 100)

        temperature = (
            random.uniform(75, 95)
            + degradation * 0.10
        )

        motor_current = (
            random.uniform(28, 35)
            + degradation * 0.05
        )

        vibration = (
            random.uniform(3.5, 5.5)
            + degradation * 0.01
        )

        rpm = random.randint(500, 1000)

    elif state == "MAINTENANCE":
        load_percentage = 0
        temperature = random.uniform(30, 40)
        motor_current = random.uniform(0, 2)
        vibration = random.uniform(0.1, 0.3)
        rpm = 0

    elif state == "EMERGENCY_STOP":
        load_percentage = 0
        temperature = random.uniform(40, 55)
        motor_current = 0
        vibration = random.uniform(0, 0.2)
        rpm = 0

    else:
        load_percentage = 0
        temperature = 40
        motor_current = 0
        vibration = 0
        rpm = 0

    if state in {"RUNNING", "HEAVY_LOAD", "FAULT"}:
        operating_hours[equipment_id] += 2 / 3600

    return {
        "equipment_id": equipment_id,
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "state": state,
        "temperature": round(
            temperature,
            2,
        ),
        "vibration": round(
            max(vibration, 0),
            2,
        ),
        "load_percentage": round(
            load_percentage,
            2,
        ),
        "motor_current": round(
            max(motor_current, 0),
            2,
        ),
        "rpm": rpm,
        "operating_hours": round(
            operating_hours[equipment_id],
            4,
        ),
        "degradation_level": round(
            degradation,
            2,
        ),
        "emergency_stop": (
            state == "EMERGENCY_STOP"
        ),
    }


def main():
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="industrial-sensor-simulator",
    )

    client.connect(
        MQTT_BROKER,
        MQTT_PORT,
        60,
    )

    print(
        f"Connected to MQTT broker at "
        f"{MQTT_BROKER}:{MQTT_PORT}"
    )

    print(
        f"Publishing telemetry to: "
        f"{MQTT_TOPIC}"
    )

    print(
        f"Simulating equipment: "
        f"{', '.join(EQUIPMENT_IDS)}"
    )

    print("\nEquipment states:")

    for equipment_id in EQUIPMENT_IDS:
        print(
            f"  {equipment_id}: "
            f"{equipment_states[equipment_id]}"
        )

    print("\nStarting telemetry stream...\n")

    try:
        while True:
            for equipment_id in EQUIPMENT_IDS:

                update_equipment_state(
                    equipment_id
                )

                telemetry = generate_telemetry(
                    equipment_id
                )

                payload = json.dumps(
                    telemetry
                )

                result = client.publish(
                    MQTT_TOPIC,
                    payload,
                )

                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    print(payload)

                else:
                    print(
                        f"Failed to publish telemetry "
                        f"for {equipment_id}"
                    )

                time.sleep(1)

    except KeyboardInterrupt:
        print("\nSimulator stopped.")

    finally:
        client.disconnect()


if __name__ == "__main__":
    main()