from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from fbox import settings


router = APIRouter(include_in_schema=False)

templates = Jinja2Templates(directory=settings.WWW_ROOT)


@router.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    context = {
        "request": request,
        "settings": settings,
    }
    return templates.TemplateResponse("index.html", context)
