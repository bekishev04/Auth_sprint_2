import json
import os

from flask import cli
from loguru import logger
from pydantic import PostgresDsn, Field, BaseSettings
from pydantic.json import pydantic_encoder

cli.load_dotenv()


class Settings(BaseSettings):
    """Settings Application"""

    basedir: str = os.path.abspath(os.path.dirname(__file__))

    SECRET_KEY: str
    FLASK_APP: str
    FLASK_DEBUG: bool

    CORS: bool

    # Default version api
    API_VERSION: float = 1.0

    # database
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_DATABASE_URI: PostgresDsn = Field(..., env="POSTGRES_URI")
    SQLALCHEMY_ENGINE_OPTIONS: dict = dict(
        json_serializer=lambda o: json.dumps(o, default=pydantic_encoder),
        # echo=True,
    )

    JWT_SECRET: str

    DEFAULT_PASSWORD: str = os.environ.get("DEFAULT_PASSWORD")

    REFRESH_TOKEN_TTL: int = 20160  # two weeks
    ACCESS_TOKEN_TTL: int = 60

    JAEGER_PORT: int
    VK_APP_ID: str
    VK_REDIRECT_URI: str
    VK_CLIENT_SECRET: str

    YANDEX_APP_ID: str
    YANDEX_REDIRECT_URI: str
    YANDEX_CLIENT_SECRET: str


cfg = Settings()

logger.add(
    os.path.join(os.path.dirname(cfg.basedir), "logs", "app.log"),
    level="DEBUG" if cfg.FLASK_DEBUG else "ERROR",
)
