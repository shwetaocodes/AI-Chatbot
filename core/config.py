from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SYNC_DATABASE_URL: str
    REDIS_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Test DB
    TEST_DATABASE_URL: str = ""
    TEST_SYNC_DATABASE_URL: str = ""

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
