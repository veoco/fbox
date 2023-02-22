import asyncio, os, hashlib
from typing import BinaryIO
from pathlib import Path
from shutil import disk_usage

from fastapi import UploadFile

from fbox import settings


class FileSystemStorage:
    CHUNK_SIZE = 256 * 1024

    async def get_filepath(self, code: str, filename: str):
        filepath = settings.DATA_ROOT / "box" / code / "files" / filename
        exist = True

        if filepath.exists():
            return filepath, exist
        else:
            exist = False

        if not filepath.parent.exists():
            filepath.parent.mkdir(parents=True)
        return filepath, exist

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

    async def get_file_sha256(self, filepath: Path):
        with open(filepath, "rb") as f:
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

    def _save_dummy(self, filepath: Path, size: int):
        with open(filepath, "wb") as f:
            f.truncate(size)

    async def save_dummy_file(self, filepath: Path, size: int):
        await asyncio.to_thread(self._save_dummy, filepath, size)

    def _save_slice(self, filepath: Path, file: BinaryIO, offset: int):
        with open(filepath, "r+b") as f:
            f.seek(offset)
            chunk = file.read(self.CHUNK_SIZE)
            while chunk:
                f.write(chunk)
                chunk = file.read(self.CHUNK_SIZE)

    async def save_file_slice(self, filepath: Path, file: UploadFile, offset: int):
        await asyncio.to_thread(self._save_slice, filepath, file.file, offset)

    async def delete_file(self, filepath: Path):
        await asyncio.to_thread(os.remove, filepath)

    async def delete_files(self, filepaths: list[Path]):
        tasks = [self.delete_file(filepath) for filepath in filepaths]
        await asyncio.gather(*tasks)
