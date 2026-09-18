import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from app.api.alerts import router as alerts_router
from app.api.equipment import router as equipment_router
from app.api.health import router as health_router
from app.api.fleet_health import router as fleet_health_router
from app.api.telemetry import router as telemetry_router
from app.services.mqtt_service import (
    set_event_loop,
    start_mqtt,
)
from app.services.websocket_manager import manager


mqtt_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global mqtt_client

    # Give the MQTT service access to FastAPI's
    # asyncio event loop so it can broadcast
    # telemetry to WebSocket clients.
    set_event_loop(
        asyncio.get_running_loop()
    )

    mqtt_client = start_mqtt()
    mqtt_client.loop_start()

    print("MQTT service started")

    yield

    mqtt_client.loop_stop()
    mqtt_client.disconnect()

    print("MQTT service stopped")


app = FastAPI(
    title="Industrial IoT Monitoring API",
    description="Backend API for industrial equipment monitoring",
    version="0.1.0",
    lifespan=lifespan,
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# API ROUTERS
# =========================================================

app.include_router(telemetry_router)
app.include_router(equipment_router)
app.include_router(alerts_router)
app.include_router(health_router)
app.include_router(fleet_health_router)


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "industrial-iot-monitoring-api",
    }


# =========================================================
# WEBSOCKET
# =========================================================

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
):
    await manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()

    except Exception:
        manager.disconnect(websocket)