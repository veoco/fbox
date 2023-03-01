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

SITE_TITLE = config("SITE_TITLE", cast=str, default="DBox")

SITE_API_DOCS = config("SITE_API_DOCS", cast=bool, default=True)

RATE_BOX_COUNT_LIMIT = config("RATE_BOX_COUNT_LIMIT", cast=int, default=10)

RATE_BOX_ERROR_LIMIT = config("RATE_BOX_ERROR_LIMIT", cast=int, default=10)

RATE_FILE_SIZE_LIMIT = config("RATE_FILE_SIZE_LIMIT", cast=int, default=10 * 1024 * 1024 * 1024)

BOX_EXPIRE = config("BOX_EXPIRE", cast=int, default=24 * 3600)

BOX_CLEAN_PERIOD = config("BOX_CLEAN_PERIOD", cast=int, default=60)

FILE_MAX_COUNT = config("FILE_MAX_COUNT", cast=int, default=5)

FILE_MAX_SIZE = config("FILE_MAX_SIZE", cast=int, default=100 * 1000 * 1000)

FILE_RED_MAX_COUNT = config("FILE_RED_MAX_COUNT", cast=int, default=10)

FILE_RED_MAX_SIZE = config("FILE_RED_MAX_SIZE", cast=int, default=1000 * 1000 * 1000)

CARD_EXPIRE = config("CARD_EXPIRE", cast=int, default=0)

CARD_VALID_COUNT = config("CARD_VALID_COUNT", cast=int, default=10)

STORAGE_ENGINE = config("STORAGE_ENGINE", cast=str, default="filesystem")

S3_ENDPOINT_URL = config("S3_ENDPOINT_URL", cast=str, default="")

S3_ACCESS_KEY = config("S3_ACCESS_KEY", cast=str, default="")

S3_SECRET_KEY = config("S3_SECRET_KEY", cast=str, default="")

S3_DATA_BUCKET = config("S3_DATA_BUCKET", cast=str, default="data")

S3_LOGS_BUCKET = config("S3_LOGS_BUCKET", cast=str, default="logs")
