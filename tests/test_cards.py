from httpx import Client

from tests.common import BASE_URL, ADMIN_PASSWORD


def test_create_card(client: Client):
    r = client.post(f"{BASE_URL}/api/cards/", headers={"Token": ADMIN_PASSWORD})
    assert r.status_code == 201
