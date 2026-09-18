from datetime import datetime

from pydantic import BaseModel


class TelemetryResponse(BaseModel):
    equipment_id: str
    timestamp: datetime
    temperature: float
    vibration: float
    load_percentage: float
    motor_current: float
    rpm: int
    operating_hours: float
    emergency_stop: bool