import asyncio
import json
import websockets


async def main():
    uri = "ws://localhost:8000/ws"

    async with websockets.connect(uri) as websocket:
        print("WebSocket connected successfully.\n")

        for _ in range(5):
            message = await websocket.recv()
            data = json.loads(message)

            print("Received:")
            print(json.dumps(data, indent=2))
            print("-" * 60)


if __name__ == "__main__":
    asyncio.run(main())