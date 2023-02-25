from pydantic import BaseModel

from fbox.cards.choices import LevelChoice


class Card(BaseModel):
    code: str
    level: LevelChoice
    count: int
    created: int
