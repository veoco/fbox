from fastapi import (
    APIRouter,
    Depends,
)

from fbox.admin.depends import token_required

router = APIRouter(tags=["Admin"], dependencies=[Depends(token_required)])


@router.get("/admin/boxes/")
async def get_boxes():
    pass
