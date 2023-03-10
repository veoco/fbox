import asyncio, os, hashlib, shutil, json
from typing import BinaryIO
from pathlib import PurePath
from shutil import disk_usage

from fastapi import UploadFile, Request

from fbox import settings
from fbox.utils import get_now
from fbox.files.models import Box
from fbox.cards.models import Card
from fbox.storage.abc import LocalStorage


class FileSystemStorage(LocalStorage):
    CHUNK_SIZE = 256 * 1024

    async def init(self) -> None:
        data_root = settings.DATA_ROOT
        box_data = data_root / "box"
        card_data = data_root / "card"

        box_data.mkdir(parents=True, exist_ok=True)
        card_data.mkdir(parents=True, exist_ok=True)

        logs_root = settings.LOGS_ROOT
        box_logs = logs_root / "box"
        box_logs.mkdir(parents=True, exist_ok=True)

    async def close(self) -> None:
        pass

    async def save_log(self, code: str, request: Request, now: int) -> None:
        await asyncio.to_thread(self._save_log, code, request, now)

    async def save_dummy_file(self, code: str, filename: str, size: int) -> list[str]:
        filepath = await self.get_filepath(code, filename)
        await asyncio.to_thread(self._save_dummy, filepath, size)
        return [
            f"/api/files/{code}/{filename}",
        ]

    async def complete_file(
        self, code: str, filename: str, sha256: str, extra: dict
    ) -> bool:
        file_sha256 = await self._get_file_sha256(code, filename)
        if file_sha256 == sha256:
            return True
        return False

    async def get_url(self, code: str, filename: str) -> str:
        return f"/api/files/{code}/{filename}"

    async def get_capacity(self) -> int:
        total, used, free = await asyncio.to_thread(disk_usage, settings.DATA_ROOT)
        return int(used / total * 200)

    async def get_dir_filenames(self, dirname: str) -> list[str]:
        dirpath = settings.DATA_ROOT / dirname
        filenames = []
        for path in dirpath.iterdir():
            filename = path.name
            filenames.append(filename)
        return filenames

    async def get_box(self, code: str) -> Box | None:
        return await asyncio.to_thread(self._get_box, code)

    async def save_box(self, box: Box) -> None:
        await asyncio.to_thread(self._save_box, box)

    async def remove_box(self, code: str) -> None:
        await asyncio.to_thread(self._remove_box, code)

    async def archive_box(self, box: Box) -> None:
        await asyncio.to_thread(self._archive_box, box)

    async def get_card(self, code: str) -> Card | None:
        return await asyncio.to_thread(self._get_card, code)

    async def save_card(self, card: Card) -> None:
        await asyncio.to_thread(self._save_card, card)

    async def get_filepath(self, code: str, filename: str) -> PurePath:
        return PurePath("box") / code / "files" / filename

    async def save_file_slice(
        self, code: str, filename: str, file: UploadFile, offset: int
    ) -> None:
        filepath = await self.get_filepath(code, filename)
        await asyncio.to_thread(self._save_slice, filepath, file.file, offset)

    async def get_sha256(self, file: BinaryIO) -> str:
        return await asyncio.to_thread(self._sha256, file)

    async def get_size(self, file: UploadFile) -> int:
        f = file.file
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(0, os.SEEK_SET)
        return size

    async def _get_file_sha256(self, code: str, filename: str) -> str:
        path = settings.DATA_ROOT / await self.get_filepath(code, filename)
        with open(path, "rb") as f:
            return await asyncio.to_thread(self._sha256, f)

    def _save_log(self, code: str, request: Request, now: int) -> None:
        r = {}
        r.update({"created": now})
        for k, v in request.headers.items():
            r.update({k: v})
        res = json.dumps(r)

        filepath = settings.DATA_ROOT / "box" / code / f"user.json"
        if not filepath.parent.exists():
            filepath.parent.mkdir(parents=True)

        with open(filepath, "w") as f:
            f.write(res)

    def _save_dummy(self, filepath: PurePath, size: int):
        path = settings.DATA_ROOT / filepath
        if not path.parent.exists():
            path.parent.mkdir(parents=True)
        with open(path, "wb") as f:
            f.truncate(size)

    def _save_slice(self, filepath: PurePath, file: BinaryIO, offset: int):
        path = settings.DATA_ROOT / filepath
        with open(path, "r+b") as f:
            f.seek(offset)
            chunk = file.read(self.CHUNK_SIZE)
            while chunk:
                f.write(chunk)
                chunk = file.read(self.CHUNK_SIZE)

    def _sha256(self, file: BinaryIO):
        m = hashlib.sha256()
        chunk = file.read(self.CHUNK_SIZE)
        while chunk:
            m.update(chunk)
            chunk = file.read(self.CHUNK_SIZE)
        file.seek(0, os.SEEK_SET)
        return m.hexdigest()

    def _get_box(self, code: str) -> Box | None:
        box_json = settings.DATA_ROOT / "box" / code / "box.json"
        if box_json.exists():
            box = Box.parse_file(box_json)
            return box
        return None

    def _save_box(self, box: Box) -> None:
        box_file = settings.DATA_ROOT / "box" / box.code / "box.json"
        with open(box_file, "w") as f:
            f.write(box.json())

    def _remove_box(self, code: str) -> None:
        box_dir = settings.DATA_ROOT / "box" / code
        shutil.rmtree(box_dir)

    def _archive_box(self, box: Box) -> None:
        now = get_now().date().isoformat()
        current = settings.DATA_ROOT / "box" / box.code
        target = settings.LOGS_ROOT / "box" / box.code / now
        target.mkdir(parents=True)

        for f in current.iterdir():
            shutil.move(f, target)
        current.rmdir()

    def _get_card(self, code: str) -> Card | None:
        card_json = settings.DATA_ROOT / "card" / f"{code}.json"
        if card_json.exists():
            card = Card.parse_file(card_json)
            return card
        return None

    def _save_card(self, card: Card) -> None:
        card_json = settings.DATA_ROOT / "card" / f"{card.code}.json"
        with open(card_json, "w") as f:
            f.write(card.json())
