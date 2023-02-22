from pydantic import BaseModel

from fbox.files.choices import StatusChoice
from fbox.cards.choices import LevelChoice


class File(BaseModel):
    status: StatusChoice
    filename: str
    size: int

class FileCreate(BaseModel):
    name: str
    size: int


class Box(BaseModel):
    code: str
    status: StatusChoice
    level: LevelChoice
    created: int
    files: dict[str, File]


class IPUser(BaseModel):
    ip: str
    error_count: int = 0
    error_from: int = 0
    box_count: int = 0
    box_from: int = 0
    file_count: int = 0
    file_from: int = 0
