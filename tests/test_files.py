import hashlib, base64
from io import BytesIO
from urllib.parse import urlparse, parse_qs

from httpx import Client

from tests.common import BASE_URL, ADMIN_PASSWORD


def test_create_waiting_box(client: Client):
    data = [
        {"name": "test-waiting-file-1.jpg", "size": 1024},
        {"name": "test-waiting-file-2.jpg", "size": 2048},
    ]
    r = client.post(f"{BASE_URL}/api/files/", json=data)
    assert r.status_code == 201

    res = r.json()
    code = res["code"]

    r = client.get(
        f"{BASE_URL}/api/admin/boxes/{code}", headers={"token": ADMIN_PASSWORD}
    )
    assert r.status_code == 200

    box = r.json()
    assert box["code"] == code
    assert box["status"] == 1

    files = box["files"]
    assert len(files) == 2

    for f in files.values():
        assert f["status"] == 1


def test_filesystem_create_complete_file(client: Client):
    filename = "test-complete-file-1.jpg"
    data = [
        {"name": filename, "size": 4096},
    ]
    r = client.post(f"{BASE_URL}/api/files/", json=data)
    res = r.json()
    code = res["code"]
    storage = res["storage"]
    upload_urls = res["uploads"][filename]

    if storage != "filesystem":
        return

    content = b"12345678" * 128
    content_hash = hashlib.sha256(content).hexdigest()
    content_bytes = BytesIO(content)
    files = {"file": (filename, content_bytes)}
    m = hashlib.sha256()

    for i in range(4):
        m.update(content)
        data = {
            "offset": i * 1024,
            "sha256": content_hash,
        }
        r = client.post(f"{BASE_URL}{upload_urls[0]}", files=files, data=data)
        print(r.text)
        assert r.status_code == 200

    r = client.patch(
        f"{BASE_URL}/api/files/{code}/{filename}",
        json={"sha256": m.hexdigest(), "extra": {}},
    )
    assert r.status_code == 200


def test_filesystem_create_complete_box(client: Client):
    filename = "test-complete-file-2.jpg"
    data = [
        {"name": filename, "size": 4096},
    ]
    r = client.post(f"{BASE_URL}/api/files/", json=data)
    res = r.json()
    code = res["code"]
    storage = res["storage"]

    if storage != "filesystem":
        return

    content = b"12345678" * 512
    content_hash = hashlib.sha256(content).hexdigest()
    content_bytes = BytesIO(content)
    files = {"file": (filename, content_bytes)}
    data = {
        "offset": 0,
        "sha256": content_hash,
    }

    r = client.post(f"{BASE_URL}/api/files/{code}/{filename}", files=files, data=data)
    r = client.patch(
        f"{BASE_URL}/api/files/{code}/{filename}",
        json={"sha256": content_hash, "extra": {}},
    )

    r = client.patch(f"{BASE_URL}/api/files/{code}")
    print(r.text)
    assert r.status_code == 200


def test_s3remote_create_complete_box(client: Client):
    filename = "test-complete-file-3.jpg"
    data = [
        {"name": filename, "size": 4096},
    ]
    r = client.post(f"{BASE_URL}/api/files/", json=data)
    res = r.json()
    code = res["code"]
    storage = res["storage"]
    upload_urls = res["uploads"][filename]
    print(upload_urls)

    if storage != "s3remote":
        return

    content = b"12345678" * 512
    content_hash = hashlib.md5(content).hexdigest()

    o = urlparse(upload_urls[0])
    qs = parse_qs(o.query)
    upload_ids = qs.get("uploadId", [])

    r = client.put(upload_urls[0], content=content)
    etag = r.headers.get("ETag").strip('"')
    assert etag == content_hash

    r = client.patch(
        f"{BASE_URL}/api/files/{code}/{filename}",
        json={
            "sha256": "",
            "extra": {
                "Parts": [
                    {
                        "ETag": etag,
                        "PartNumber": 1,
                    },
                ],
                "UploadId": upload_ids[0],
            },
        },
    )

    r = client.patch(f"{BASE_URL}/api/files/{code}")
    print(r.text)
    assert r.status_code == 200
