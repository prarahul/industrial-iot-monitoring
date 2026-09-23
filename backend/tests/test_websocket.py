import asyncio
import json

import websockets


WS_URL = "ws://127.0.0.1:8000/ws"


def test_websocket_receives_telemetry():
    async def run_test():
        async with websockets.connect(
            WS_URL,
            open_timeout=5,
            close_timeout=5,
        ) as websocket:

            message = await asyncio.wait_for(
                websocket.recv(),
                timeout=10,
            )

            data = json.loads(message)

            assert data["type"] == "telemetry"
            assert "data" in data

            telemetry = data["data"]

            assert "equipment_id" in telemetry
            assert "timestamp" in telemetry
            assert "temperature" in telemetry
            assert "vibration" in telemetry
            assert "load_percentage" in telemetry
            assert "motor_current" in telemetry
            assert "rpm" in telemetry

    asyncio.run(run_test())