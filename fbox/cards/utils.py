from random import randint

from jose import jwt

from fbox import settings
from fbox.database import db


def create_jwt(data: dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(
        to_encode, str(settings.SECRET_KEY), algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def generate_card_code() -> str:
    code = str(randint(100_000_000, 999_999_999))
    while db.check_card_by_code(code):
        code = str(randint(100_000_000, 999_999_999))
    return code
