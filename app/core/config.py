from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    PROJECT_NAME: str = "REsQue"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./sql_app.db"
    TEST_DATABASE_URL: str = "sqlite:///./sql_app.db"
    WELCOME_MESSAGE: str = "Hello, World!"
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    PROJECT_ROOT: str = str(Path(__file__).parents[2])

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
