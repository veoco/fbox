from pathlib import Path, PurePath

from starlette.config import Config
from starlette.datastructures import Secret


BASE_DIR = Path(__file__).resolve().parent.parent

config = Config(BASE_DIR / ".env")

DEBUG = config("DEBUG", cast=bool, default=False)

DATA_ROOT = config("DATA_ROOT", cast=Path, default=Path("data"))

LOGS_ROOT = config("LOGS_ROOT", cast=Path, default=Path("logs"))

WWW_ROOT = config("WWW_ROOT", cast=Path, default=Path("www"))

SECRET_KEY = config("SECRET_KEY", cast=Secret)

ALGORITHM = "HS256"

ADMIN_PASSWORD = config("ADMIN_PASSWORD", cast=str, default="password")

BOX_EXPIRE = config("BOX_EXPIRE", cast=int, default=24 * 3600)

STORAGE_ENGINE = config("STORAGE_ENGINE", cast=str, default="filesystem")

S3_ENDPOINT_URL = config("S3_ENDPOINT_URL", cast=str, default="")

S3_ACCESS_KEY = config("S3_ACCESS_KEY", cast=str, default="")

S3_SECRET_KEY = config("S3_SECRET_KEY", cast=str, default="")

S3_DATA_BUCKET = config("S3_DATA_BUCKET", cast=str, default="data")

S3_LOGS_BUCKET = config("S3_LOGS_BUCKET", cast=str, default="logs")
