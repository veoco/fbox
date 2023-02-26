import asyncio, os, hashlib, shutil
from typing import BinaryIO
from pathlib import PurePath
from shutil import disk_usage

from fastapi import UploadFile

from fbox import settings
from fbox.utils import get_now
from fbox.files.models import Box
from fbox.cards.models import Card
from fbox.storage.abc import LocalStorage


class FileSystemStorage(LocalStorage):
    CHUNK_SIZE = 256 * 1024

    async def init_root(self):
        data_root = settings.DATA_ROOT
        box_data = data_root / "box"
        card_data = data_root / "card"

        box_data.mkdir(parents=True, exist_ok=True)
        card_data.mkdir(parents=True, exist_ok=True)

        logs_root = settings.LOGS_ROOT
        box_logs = logs_root / "box"
        box_logs.mkdir(parents=True, exist_ok=True)

    async def get_filepath(self, code: str, filename: str) -> PurePath:
        return PurePath("box") / code / "files" / filename

    def _save_dummy(self, filepath: PurePath, size: int):
        path = settings.DATA_ROOT / filepath
        if not path.parent.exists():
            path.parent.mkdir(parents=True)
        with open(path, "wb") as f:
            f.truncate(size)

    async def save_dummy_file(self, code: str, filename: str, size: int) -> str:
        filepath = await self.get_filepath(code, filename)
        await asyncio.to_thread(self._save_dummy, filepath, size)
        return f"/api/files/{code}/{filename}"

    def _save_slice(self, filepath: PurePath, file: BinaryIO, offset: int):
        path = settings.DATA_ROOT / filepath
        with open(path, "r+b") as f:
            f.seek(offset)
            chunk = file.read(self.CHUNK_SIZE)
            while chunk:
                f.write(chunk)
                chunk = file.read(self.CHUNK_SIZE)

    async def save_file_slice(
        self, code: str, filename: str, file: UploadFile, offset: int
    ):
        filepath = await self.get_filepath(code, filename)
        await asyncio.to_thread(self._save_slice, filepath, file.file, offset)

    async def complete_file(self, code: str, filename: str, sha256: str) -> bool:
        file_sha256 = await self.get_file_sha256(code, filename)
        if file_sha256 == sha256:
            return True
        return False

    def _sha256(self, file: BinaryIO):
        m = hashlib.sha256()
        chunk = file.read(self.CHUNK_SIZE)
        while chunk:
            m.update(chunk)
            chunk = file.read(self.CHUNK_SIZE)
        file.seek(0, os.SEEK_SET)
        return m.hexdigest()

    async def get_sha256(self, file: BinaryIO):
        return await asyncio.to_thread(self._sha256, file)

    async def get_file_sha256(self, code: str, filename: str):
        path = settings.DATA_ROOT / await self.get_filepath(code, filename)
        with open(path, "rb") as f:
            return await asyncio.to_thread(self._sha256, f)

    async def get_size(self, file: UploadFile):
        f = file.file
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(0, os.SEEK_SET)
        return size

    async def get_capacity(self):
        total, used, free = await asyncio.to_thread(disk_usage, settings.DATA_ROOT)
        return int(used / total * 200)

    async def get_dir_filenames(self, dirname: str) -> list[str]:
        dirpath = settings.DATA_ROOT / dirname
        filenames = []
        for path in dirpath.iterdir():
            filename = path.name
            filenames.append(filename)
        return filenames

    def _get_box(self, code: str) -> Box | None:
        box_json = settings.DATA_ROOT / "box" / code / "box.json"
        if box_json.exists():
            box = Box.parse_file(box_json)
            return box
        return None

    async def get_box(self, code: str) -> Box | None:
        return await asyncio.to_thread(self._get_box, code)

    def _save_box(self, box: Box) -> None:
        box_file = settings.DATA_ROOT / "box" / box.code / "box.json"
        with open(box_file, "w") as f:
            f.write(box.json())

    async def save_box(self, box: Box) -> None:
        await asyncio.to_thread(self._save_box, box)

    def _remove_box(self, code: str) -> None:
        box_dir = settings.DATA_ROOT / "box" / code
        shutil.rmtree(box_dir)

    async def remove_box(self, code: str) -> None:
        await asyncio.to_thread(self._remove_box, code)

    def _archive_box(self, box: Box) -> None:
        now = get_now().date().isoformat()
        current = settings.DATA_ROOT / "box" / box.code
        target = settings.LOGS_ROOT / "box" / box.code / now
        target.mkdir(parents=True)

        for f in current.iterdir():
            shutil.move(f, target)
        current.rmdir()

    async def archive_box(self, box: Box) -> None:
        await asyncio.to_thread(self._archive_box, box)

    def _get_card(self, code: str) -> Card | None:
        card_json = settings.DATA_ROOT / "card" / f"{code}.json"
        if card_json.exists():
            card = Card.parse_file(card_json)
            return card
        return None

    async def get_card(self, code: str) -> Card | None:
        return await asyncio.to_thread(self._get_card, code)

    def _save_card(self, card: Card) -> None:
        card_json = settings.DATA_ROOT / "card" / f"{card.code}.json"
        with open(card_json, "w") as f:
            f.write(card.json())

    async def save_card(self, card: Card) -> None:
        await asyncio.to_thread(self._save_card, card)
