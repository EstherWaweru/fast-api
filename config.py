import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URI: str = os.getenv("DATABASE_URI")

    class Config:
        case_sensitive: bool = True
        env_file: str = ".env"


settings = Settings()
