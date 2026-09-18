from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mqtt_broker: str = "localhost"
    mqtt_port: int = 1883
    mqtt_topic: str = "industrial/equipment/telemetry"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "industrial_iot"
    postgres_user: str = "iot_user"
    postgres_password: str = "iot_password"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()