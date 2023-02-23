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

    for f in files:
        assert f["status"] == 1
