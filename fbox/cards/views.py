from fastapi import (
    APIRouter,
    HTTPException,
    Body,
    Depends,
)

from fbox import settings
from fbox.log import logger
from fbox.database import db
from fbox.cards.models import Card
from fbox.cards.choices import LevelChoice
from fbox.cards.utils import generate_card_code, create_jwt
from fbox.cards.depends import get_card

router = APIRouter(tags=["Cards"])


@router.post("/cards/")
async def post_cards(password: str = Body(embed=True)):
    if password != settings.ADMIN_PASSWORD:
        raise HTTPException(400)

    code = generate_card_code()
    card = Card(code=code, level=LevelChoice.red, count=10, created=0)
    await db.save_card(card)

    logger.info(f"Generated card {card.code}")

    data = {"sub": code}
    token = create_jwt(data)
    return {"token": token}


@router.post("/cards/detail")
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
