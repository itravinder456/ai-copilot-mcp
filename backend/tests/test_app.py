from fastapi.testclient import TestClient

from main import app


def test_app_has_expected_title():
    assert app.title == "AI Copilot API"


def test_chat_route_is_registered():
    client = TestClient(app)

    openapi = client.get("/openapi.json").json()

    assert "/chat/" in openapi["paths"]


def test_chat_route_requires_prompt_field():
    client = TestClient(app)

    response = client.post("/chat/", json={})

    assert response.status_code == 422
