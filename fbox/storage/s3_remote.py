import asyncio, json, base64

from fastapi import Request
from botocore import session

from fbox import settings
from fbox.utils import get_now
from fbox.storage.abc import RemoteStorage
from fbox.files.models import Box
from fbox.cards.models import Card


class S3RemoteStorage(RemoteStorage):
    async def init(self) -> None:
        s = session.get_session()
        self.client = s.create_client(
            "s3",
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            endpoint_url=settings.S3_ENDPOINT_URL,
        )

    async def close(self) -> None:
        self.client.close()

    async def save_log(self, code: str, request: Request, now: int) -> None:
        await asyncio.to_thread(self._save_log, code, request, now)

    async def save_dummy_file(self, code: str, filename: str, size: int) -> list[str]:
        return await asyncio.to_thread(self._save_dummy_file, code, filename, size)

    async def complete_file(
        self, code: str, filename: str, sha256: str, extra: dict
    ) -> bool:
        return await asyncio.to_thread(
            self._complete_file, code, filename, sha256, extra
        )

    async def get_url(self, code: str, filename: str) -> str:
        return await asyncio.to_thread(self._get_url, code, filename)

    async def get_capacity(self) -> int:
        return 1

    async def get_dir_filenames(self, dirname: str) -> list[str]:
        return await asyncio.to_thread(self._get_dir_filenames, dirname)

    async def get_box(self, code: str) -> Box | None:
        return await asyncio.to_thread(self._get_box, code)

    async def save_box(self, box: Box) -> None:
        await asyncio.to_thread(self._save_box, box)

    async def remove_box(self, code: str) -> None:
        await asyncio.to_thread(self._remove_box, code)

    async def archive_box(self, box: Box) -> None:
        await asyncio.to_thread(self._archive_box, box)

    async def get_card(self, code: str) -> Card | None:
        await asyncio.to_thread(self._get_card, code)

    async def save_card(self, card: Card) -> None:
        await asyncio.to_thread(self._save_card, card)

    def _save_log(self, code: str, request: Request, now: int) -> None:
        key = f"box/{code}/user.json"
        r = {}
        r.update({"created": now})
        for k, v in request.headers.items():
            r.update({k: v})
        res = json.dumps(r)

        self.client.put_object(
            Body=res,
            Bucket=settings.S3_LOGS_BUCKET,
            Key=key,
        )

    def _save_dummy_file(self, code: str, filename: str, size: int) -> list[str]:
        key = f"box/{code}/{filename}"
        r = self.client.create_multipart_upload(
            Bucket=settings.S3_DATA_BUCKET,
            Key=key,
        )

        upload_id = r["UploadId"]
        max_count = int(size / 10_000_000) + 1
        expire = int(settings.BOX_EXPIRE / 10)
        urls = []

        for i in range(1, max_count + 1):
            url = self.client.generate_presigned_url(
                ClientMethod="uploadPart",
                Params={
                    "Bucket": settings.S3_DATA_BUCKET,
                    "Key": key,
                    "PartNumber": i,
                    "UploadId": upload_id,
                },
                ExpiresIn=expire,
            )
            urls.append(url)
        return urls

    def _complete_file(
        self, code: str, filename: str, sha256: str, extra: dict
    ) -> bool:
        key = f"box/{code}/{filename}"
        sha256_base64 = base64.b64encode(sha256.encode("utf-8")).decode("utf-8")

        try:
            self.client.complete_multipart_upload(
                Bucket=settings.S3_DATA_BUCKET,
                Key=key,
                MultipartUpload=extra["Parts"],
                UploadId=extra["UploadId"],
                ChecksumSHA256=sha256_base64,
            )
            return True
        except:
            return False

    def _get_url(self, code: str, filename: str) -> str:
        key = f"box/{code}/{filename}"
        expire = int(settings.BOX_EXPIRE / 10)
        url = self.client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": settings.S3_DATA_BUCKET, "Key": key},
            ExpiresIn=expire,
        )
        return url

    def _get_dir_filenames(self, dirname: str) -> list[str]:
        paginator = self.client.get_paginator("list_objects")
        page_iterator = paginator.paginate(
            Bucket=settings.S3_DATA_BUCKET, Prefix=dirname
        )

        filenames = set()
        for page in page_iterator:
            contents = page.get("Contents")
            if contents is None:
                break

            for content in contents:
                key = content["Key"]
                filename = key.split("/")[1]
                filenames.add(filename)
        return list(filenames)

    def _get_box(self, code: str) -> Box | None:
        key = f"box/{code}/box.json"
        try:
            r = self.client.get_object(
                Bucket=settings.S3_DATA_BUCKET,
                Key=key,
            )
            box_json = r["Body"].read()
            box = Box.parse_raw(box_json)
            return box
        except:
            return None

    def _save_box(self, box: Box) -> None:
        key = f"box/{box.code}/box.json"
        box_json = box.json()

        self.client.put_object(
            Body=box_json,
            Bucket=settings.S3_DATA_BUCKET,
            Key=key,
        )

    def _remove_box(self, code: str) -> None:
        box_key = f"box/{code}"

        paginator = self.client.get_paginator("list_objects")
        page_iterator = paginator.paginate(
            Bucket=settings.S3_DATA_BUCKET, Prefix=box_key
        )

        delete_objects = {
            "Objects": [],
            "Quiet": False,
        }
        for page in page_iterator:
            contents = page.get("Contents")
            if contents is None:
                break
            
            for content in contents:
                key = content["Key"]
                delete_objects["Objects"].append({"Key": key})

        self.client.delete_objects(
            Bucket=settings.S3_DATA_BUCKET, Delete=delete_objects
        )

    def _archive_box(self, box: Box) -> None:
        box_key = f"box/{box.code}"
        now = get_now().date().isoformat()

        paginator = self.client.get_paginator("list_objects")
        page_iterator = paginator.paginate(
            Bucket=settings.S3_DATA_BUCKET, Prefix=box_key
        )

        delete_objects = {
            "Objects": [],
            "Quiet": False,
        }
        for page in page_iterator:
            contents = page.get("Contents")
            if contents is None:
                break
            
            for content in contents:
                key = content["Key"]
                size = content["Size"]
                delete_objects["Objects"].append({"Key": key})
                
                key_parts = key.split("/")
                target_key_parts = ["box", key_parts[1], now]
                target_key_parts.extend(key_parts[2:])
                target_key = "/".join(target_key_parts)

                if size < 5_000_000_000:
                    self.client.copy_object(
                        Bucket=settings.S3_LOGS_BUCKET,
                        CopySource=key,
                        Key=target_key,
                    )
                else:
                    pass

        self.client.delete_objects(
            Bucket=settings.S3_DATA_BUCKET, Delete=delete_objects
        )

    def _get_card(self, code: str) -> Card | None:
        key = f"card/{code}.json"
        try:
            r = self.client.get_object(
                Bucket=settings.S3_DATA_BUCKET,
                Key=key,
            )
            card_json = r["Body"].read()
            card = Card.parse_raw(card_json)
            return card
        except:
            return None

    def _save_card(self, card: Card) -> None:
        key = f"card/{card.code}.json"
        card_json = card.json()

        self.client.put_object(
            Body=card_json,
            Bucket=settings.S3_DATA_BUCKET,
            Key=key,
        )
