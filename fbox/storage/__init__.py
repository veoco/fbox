from fbox import settings
from fbox.storage.filesystem import FileSystemStorage

storage_engines = {
    "filesystem": FileSystemStorage,
}

storage = storage_engines[settings.STORAGE_ENGINE]()
