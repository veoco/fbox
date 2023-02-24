import hashlib
from io import BytesIO

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


def test_create_complete_file(client: Client):
    filename = "test-complete-file-1.jpg"
    data = [
        {"name": filename, "size": 4096},
    ]
    r = client.post(f"{BASE_URL}/api/files/", json=data)
    res = r.json()
    code = res["code"]

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
        r = client.post(
            f"{BASE_URL}/api/files/{code}/{filename}", files=files, data=data
        )
        print(r.text)
        assert r.status_code == 200

    r = client.patch(
        f"{BASE_URL}/api/files/{code}/{filename}", json={"sha256": m.hexdigest()}
    )
    assert r.status_code == 200
