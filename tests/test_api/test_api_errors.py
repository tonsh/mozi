from mozi.api import APIError
from . import client


def test_index():
    response = client.get("/demo/hello")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Hello Demo."
    }


def test_error():
    response = client.get("/demo/error")
    assert response.status_code == APIError.status_code

    data = response.json()
    data["error_code"] = APIError.error_code
