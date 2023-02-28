from fastapi import (
    APIRouter,
    UploadFile,
    HTTPException,
    Body,
    Form,
    Depends,
    Request,
)
from fastapi.responses import FileResponse

from fbox import settings
from fbox.log import logger
from fbox.utils import get_now
from fbox.database import db
from fbox.cards.choices import LevelChoice
from fbox.cards.models import Card
from fbox.cards.depends import get_card
from fbox.files.models import Box, FileCreate, IPUser, File
from fbox.files.choices import UploadFailChoice, StatusChoice
from fbox.storage import storage, LocalStorage
from fbox.files.utils import (
    generate_code,
    get_ip,
    get_box_or_404,
    get_file_or_404,
    get_box_files,
    check_rate,
    update_rate,
)


router = APIRouter(tags=["Files"])


@router.get("/files/capacity")
async def get_capacity():
    count = await storage.get_capacity()
    return {"count": count}


@router.post("/files/", status_code=201)
async def post_box(
    files: list[FileCreate],
    card: Card = Depends(get_card),
    ip_user: IPUser = Depends(get_ip),
):
    now = int(get_now().timestamp())

    files_count_max = 5
    files_size_max = 100 * 1024 * 1024
    if card.level == LevelChoice.red:
        card.count -= 1
        await db.save_card(card)

        files_size_max = 1024 * 1024 * 1024

    check_rate(ip_user, "box")

    if not files:
        raise HTTPException(status_code=400, detail=f"{UploadFailChoice.empty_file}")
    if len(files) > files_count_max:
        raise HTTPException(status_code=400, detail=f"{UploadFailChoice.too_much_file}")

    files_size = 0
    file_names = set()
    for f in files:
        files_size += f.size
        if len(f.name) > 250 or f.name in file_names:
            raise HTTPException(
                status_code=400, detail=f"{UploadFailChoice.invalid_name}"
            )
        file_names.add(f.name)

    if files_size > files_size_max:
        raise HTTPException(
            status_code=400, detail=f"{UploadFailChoice.too_much_error}"
        )

    code = generate_code()

    box_files = {}
    uploads = {}
    for f in files:
        file = File(status=StatusChoice.waiting, filename=f.name, size=f.size)
        box_files[f.name] = file

        upload_urls = await storage.save_dummy_file(code, f.name, f.size)
        uploads[f.name] = upload_urls

    box = Box(
        code=code,
        status=StatusChoice.waiting,
        created=now,
        level=card.level,
        files=box_files,
    )
    await db.save_box(box)

    logger.info(f"Created box {box.code} with {len(files)} files")

    update_rate(ip_user, "box", 10)

    return {
        "code": code,
        "storage": settings.STORAGE_ENGINE,
        "uploads": uploads,
        "detail": "20101",
    }


@router.get("/files/{code}")
async def get_box(
    code: str,
    ip_user: IPUser = Depends(get_ip),
):
    box = get_box_or_404(ip_user, code)
    if box.status != StatusChoice.complete:
        raise HTTPException(status_code=404)

    files = get_box_files(code)
    r = []
    for f in files:
        url = await storage.get_url(code, f.filename)
        r.append({"name": f.filename, "size": f.size, "url": url})

    return {
        "count": len(files),
        "created": box.created,
        "level": box.level,
        "results": r,
    }


@router.patch("/files/{code}")
async def patch_box(
    request: Request,
    code: str,
    ip_user: IPUser = Depends(get_ip),
):
    now = int(get_now().timestamp())
    box = get_box_or_404(ip_user, code)
    if box.status != StatusChoice.waiting:
        raise HTTPException(status_code=404)

    files = get_box_files(code)
    for f in files:
        if f.status == StatusChoice.waiting:
            raise HTTPException(
                status_code=400, detail=f"{UploadFailChoice.invalid_file}"
            )

    box.status = StatusChoice.complete
    box.created = now
    await db.save_box(box)

    logger.info(f"Completed box {box.code}")

    await storage.save_log(code, request, now)

    return {"code": code, "detail": "20001"}


@router.get("/files/{code}/{filename}")
async def get_file(
    code: str,
    filename: str,
    ip_user: IPUser = Depends(get_ip),
):
    if not isinstance(storage, LocalStorage):
        raise HTTPException(status_code=400, detail=f"{UploadFailChoice.invalid_file}")

    box = get_box_or_404(ip_user, code)
    if box.status != StatusChoice.complete:
        raise HTTPException(status_code=404)

    file = get_file_or_404(ip_user, code, filename)
    if file and file.status == StatusChoice.complete:
        filepath = await storage.get_filepath(code, filename)
        path = settings.DATA_ROOT / filepath
        return FileResponse(path, filename=file.filename)

    raise HTTPException(status_code=404)


@router.post("/files/{code}/{filename}")
async def post_file(
    code: str,
    filename: str,
    file: UploadFile,
    offset: int = Form(),
    sha256: str = Form(),
    ip_user: IPUser = Depends(get_ip),
):
    if not isinstance(storage, LocalStorage):
        raise HTTPException(status_code=400, detail=f"{UploadFailChoice.invalid_file}")

    box = get_box_or_404(ip_user, code)
    if box.status != StatusChoice.waiting:
        raise HTTPException(status_code=404)

    box_file = get_file_or_404(ip_user, code, filename)
    if box_file.status != StatusChoice.waiting:
        raise HTTPException(status_code=404)

    file_size = await storage.get_size(file)
    if offset < 0 or (offset + file_size) > box_file.size:
        raise HTTPException(status_code=400, detail=f"{UploadFailChoice.invalid_file}")

    check_rate(ip_user, "file")

    file_sha256 = await storage.get_sha256(file.file)
    if file_sha256 != sha256:
        raise HTTPException(status_code=400, detail=f"UploadFailChoice.invalid_file")

    await storage.save_file_slice(code, filename, file, offset)

    update_rate(ip_user, "file", 10 * 1024 * 1024 * 1024, file_size)

    return {"code": code, "filename": filename, "detail": "20001"}


@router.patch("/files/{code}/{filename}")
async def patch_file(
    code: str,
    filename: str,
    extra: dict,
    sha256: str = Body(embed=True),
    ip_user: IPUser = Depends(get_ip),
):
    box = get_box_or_404(ip_user, code)
    if box.status != StatusChoice.waiting:
        raise HTTPException(status_code=404)

    box_file = get_file_or_404(ip_user, code, filename)
    if box_file.status != StatusChoice.waiting:
        raise HTTPException(status_code=404)

    extra["size"] = box_file.size
    file_completed = await storage.complete_file(code, filename, sha256, extra)
    if not file_completed:
        raise HTTPException(status_code=400, detail=f"{UploadFailChoice.invalid_file}")

    box_file.status = StatusChoice.complete
    box.files[filename] = box_file
    await db.save_box(box)

    logger.info(f"Completed box {box.code} file {filename}")

    return {"code": code, "filename": filename, "detail": "20001"}
