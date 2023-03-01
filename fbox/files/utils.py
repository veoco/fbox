from random import randint

from fastapi import Request, HTTPException

from fbox import settings
from fbox.utils import get_now
from fbox.database import db
from fbox.files.models import IPUser, Box, File
from fbox.files.choices import UploadFailChoice


async def get_ip(request: Request) -> IPUser:
    x_real_ip = request.headers.get("X-Real-Ip")
    cf_connecting_ip = request.headers.get("CF-Connecting-IP")
    ip = cf_connecting_ip or x_real_ip or request.get("client")[0]

    ip_user = db.get_ip_user(ip)
    if ip_user is None:
        ip_user = IPUser(ip=ip)
        db.save_ip_user(ip_user)
    return ip_user


def generate_code() -> str:
    code = str(randint(1000_0000, 9999_9999))
    while db.check_box_by_code(code):
        code = str(randint(1000_0000, 9999_9999))
    return code


def check_rate(ip_user: IPUser, name: str) -> None:
    now = int(get_now().timestamp())
    name_count = f"{name}_count"
    name_from = f"{name}_from"

    count = getattr(ip_user, name_count)
    start = getattr(ip_user, name_from)
    if count > 0 and (now - start) < (3600):
        raise HTTPException(status_code=400, detail=f"{UploadFailChoice.too_fast}")
    else:
        setattr(ip_user, name_count, 0)
        setattr(ip_user, name_from, 0)
        db.save_ip_user(ip_user)


def update_rate(ip_user: IPUser, name: str, limit: int, step=1):
    name_count = f"{name}_count"
    name_from = f"{name}_from"

    count = getattr(ip_user, name_count) + step
    setattr(ip_user, name_count, count)
    if count > limit:
        setattr(ip_user, name_from, int(get_now().timestamp()))
    db.save_ip_user(ip_user)


def get_box_or_404(ip_user: IPUser, code) -> Box:
    check_rate(ip_user, "box")

    box = db.get_box(code)
    if box is None:
        update_rate(ip_user, "box", settings.RATE_BOX_ERROR_LIMIT)
        raise HTTPException(status_code=404)

    return box


def get_file_or_404(ip_user: IPUser, code: str, filename: str) -> File:
    check_rate(ip_user, "file")

    file = db.get_file(code, filename)
    if file is None:
        update_rate(ip_user, "file", settings.RATE_FILE_SIZE_LIMIT, settings.FILE_MAX_SIZE)
        raise HTTPException(status_code=404)

    return file


def get_box_files(code: str) -> list[File]:
    files = db.get_files(code)
    return files
