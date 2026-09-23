import logging

from fastapi import WebSocket


logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(
        self,
        websocket: WebSocket,
    ):
        await websocket.accept()

        self.active_connections.append(
            websocket
        )

        logger.warning(
            "WEBSOCKET CONNECTED | active_clients=%s",
            len(self.active_connections),
        )

    def disconnect(
        self,
        websocket: WebSocket,
    ):
        if websocket in self.active_connections:
            self.active_connections.remove(
                websocket
            )

        logger.warning(
            "WEBSOCKET DISCONNECTED | active_clients=%s",
            len(self.active_connections),
        )

    async def broadcast(
        self,
        message: dict,
    ):
        logger.warning(
            "WEBSOCKET BROADCAST | active_clients=%s",
            len(self.active_connections),
        )

        disconnected = []

        for websocket in self.active_connections:
            try:
                await websocket.send_json(
                    message
                )

                logger.warning(
                    "WEBSOCKET SEND SUCCESS"
                )

            except Exception as error:
                logger.exception(
                    "WEBSOCKET SEND FAILED: %s",
                    error,
                )

                disconnected.append(
                    websocket
                )

        for websocket in disconnected:
            self.disconnect(websocket)


manager = ConnectionManager()