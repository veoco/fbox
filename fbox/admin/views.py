from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
)

from fbox.database import db
from fbox.files.models import Box
from fbox.admin.depends import token_required

router = APIRouter(tags=["Admin"], dependencies=[Depends(token_required)])


@router.get("/admin/boxes/")
async def get_boxes(expired: bool = False) -> list[Box]:
    boxes = db.get_boxes(expired)
    if len(boxes) > 100:
        return boxes[:100]
    return boxes


@router.get("/admin/boxes/{code}")
async def get_box(code: str) -> Box:
    box = db.get_box(code)
    if box is None:
        raise HTTPException(status_code=404)
    return box
