from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
)

from fbox import settings
from fbox.log import logger
from fbox.database import db
from fbox.cards.models import Card
from fbox.cards.choices import LevelChoice
from fbox.cards.utils import generate_card_code, create_jwt
from fbox.cards.depends import get_card
from fbox.admin.depends import token_required

router = APIRouter(tags=["Cards"])


@router.post("/cards/", status_code=201, dependencies=[Depends(token_required)])
async def post_cards():
    code = generate_card_code()
    card = Card(code=code, level=LevelChoice.red, count=settings.CARD_VALID_COUNT, created=0 if settings.CARD_EXPIRE <= 0 else settings.CARD_EXPIRE)
    await db.save_card(card)

    logger.info(f"Generated card {card.code}")

    data = {"sub": code}
    token = create_jwt(data)
    return {"token": token}


@router.get("/cards/detail")
async def card_detail(card: Card = Depends(get_card)):
    if card.count == 0:
        raise HTTPException(404)
    return card


@router.post("/cards/renew")
async def card_renew(card: Card = Depends(get_card)):
    if card.count == 0:
        raise HTTPException(404)

    code = generate_card_code()
    new_card = Card(
        level=card.level, count=card.count - 1, code=code, created=card.created
    )
    await db.save_card(new_card)
    db.expire_card(card)

    logger.info(f"Renew card {card.code} with card{new_card.code}")

    data = {"sub": code}
    token = create_jwt(data)
    return {"token": token}
