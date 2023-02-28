from abc import ABC, abstractmethod
from pathlib import PurePath
from typing import BinaryIO

from fastapi import UploadFile

from fbox.files.models import Box
from fbox.cards.models import Card


class RemoteStorage(ABC):
    @abstractmethod
    async def init(self) -> None:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass

    @abstractmethod
    async def save_dummy_file(self, code: str, filename: str, size: int) -> str:
        pass

    @abstractmethod
    async def complete_file(
        self, code: str, filename: str, sha256: str, extra: dict
    ) -> bool:
        pass

    @abstractmethod
    async def get_url(self, code: str, filename: str) -> str:
        pass

    @abstractmethod
    async def get_capacity(self) -> int:
        pass

    @abstractmethod
    async def get_dir_filenames(self, dirname: str) -> list[str]:
        pass

    @abstractmethod
    async def get_box(self, code: str) -> Box | None:
        pass

    @abstractmethod
    async def save_box(self, box: Box) -> None:
        pass

    @abstractmethod
    async def remove_box(self, code: str) -> None:
        pass

    @abstractmethod
    async def archive_box(self, box: Box) -> None:
        pass

    @abstractmethod
    async def get_card(self, code: str) -> Card | None:
        pass

    @abstractmethod
    async def save_card(self, card: Card) -> None:
        pass


class LocalStorage(RemoteStorage):
    @abstractmethod
    async def get_filepath(self, code: str, filename: str) -> PurePath:
        pass

    @abstractmethod
    async def save_file_slice(
        self, code: str, filename: str, file: UploadFile, offset: int
    ) -> None:
        pass

    @abstractmethod
    async def get_sha256(self, file: BinaryIO) -> str:
        pass

    @abstractmethod
    async def get_size(self, file: UploadFile) -> int:
        pass
