from pathlib import Path

from starlette.config import Config
from starlette.datastructures import Secret


BASE_DIR = Path(__file__).resolve().parent.parent

config = Config(BASE_DIR / ".env")

DEBUG = config("DEBUG", cast=bool, default=False)

DATA_ROOT = config("DATA_ROOT", cast=Path, default=Path("data"))

LOGS_ROOT = config("LOGS_ROOT", cast=Path, default=Path("logs"))

SECRET_KEY = config("SECRET_KEY", cast=Secret)

ALGORITHM = "HS256"

ADMIN_PASSWORD = config("ADMIN_PASSWORD", cast=str, default="password")
