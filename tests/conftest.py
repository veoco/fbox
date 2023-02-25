import pytest, httpx


@pytest.fixture()
def client():
    with httpx.Client() as client:
        yield client
