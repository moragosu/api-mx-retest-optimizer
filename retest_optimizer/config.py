import os
from pydantic_settings import BaseSettings, SettingsConfigDict

fct_name = os.getenv("FCT_NAME")
env_file = ".env.dev" if fct_name is None else ".env.{}".format(fct_name)

class Settings(BaseSettings):
    """애플리케이션 설정을 관리하는 클래스입니다."""
    
    model_config = SettingsConfigDict(
        env_file=env_file,
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Redis Settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None

    # Uvicorn Server Settings
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_RELOAD: bool = False


settings = Settings()
