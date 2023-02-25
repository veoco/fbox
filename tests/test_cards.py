from httpx import Client

from tests.common import BASE_URL, ADMIN_PASSWORD


def test_create_card(client: Client):
    r = client.post(f"{BASE_URL}/api/cards/", headers={"Token": ADMIN_PASSWORD})
    assert r.status_code == 201

    res = r.json()
    token = res["token"]

    r = client.get(
        f"{BASE_URL}/api/cards/detail", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 200


def test_renew_card(client: Client):
    r = client.post(f"{BASE_URL}/api/cards/", headers={"Token": ADMIN_PASSWORD})
    res = r.json()
    token = res["token"]

    r = client.get(
        f"{BASE_URL}/api/cards/renew", headers={"Authorization": f"Bearer {token}"}
    )
    res = r.json()
    new_token = res["token"]

    r = client.get(
        f"{BASE_URL}/api/cards/detail", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 404

    r = client.get(
        f"{BASE_URL}/api/cards/detail", headers={"Authorization": f"Bearer {new_token}"}
    )
    assert r.status_code == 404
