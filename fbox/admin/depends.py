from fastapi import Header, HTTPException

from fbox import settings


async def token_required(token: str = Header()):
    if token != settings.ADMIN_PASSWORD:
        raise HTTPException(400)
