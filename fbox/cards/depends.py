from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from fbox import settings
from fbox.database import db
from fbox.cards.models import Card
from fbox.cards.choices import LevelChoice

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="card/token/", auto_error=False)


async def get_card(token: str | None = Depends(oauth2_scheme)):
    any_card = Card(code="", level=LevelChoice.visitor, count=0, created=0)
    if token is None:
        return any_card
    try:
        payload = jwt.decode(
            token, str(settings.SECRET_KEY), algorithms=[settings.ALGORITHM]
        )
        code: str = payload.get("sub")
        if code is None:
            return any_card

        card = db.get_card(code)
        if card is None:
            return any_card
        
        return card
    except JWTError as e:
        return any_card
