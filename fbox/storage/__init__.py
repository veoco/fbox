from fbox import settings
from fbox.storage.abc import LocalStorage
from fbox.storage.filesystem import FileSystemStorage
from fbox.storage.s3_remote import S3RemoteStorage

storage_engines = {
    "filesystem": FileSystemStorage,
    "s3remote": S3RemoteStorage,
}

storage = storage_engines[settings.STORAGE_ENGINE]()
