import asyncio
import json

import websockets


async def test_websocket():
    uri = "ws://127.0.0.1:8000/ws"

    async with websockets.connect(uri) as websocket:
        print("WebSocket connected successfully.")
        print("Waiting for MQTT telemetry...\n")

        for _ in range(5):
            message = await websocket.recv()

            print("WebSocket message received:")
            print(json.dumps(
                json.loads(message),
                indent=2,
            ))
            print()


asyncio.run(test_websocket())