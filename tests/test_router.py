# tests/test_router.py
import pytest
from fastapi.testclient import TestClient
from main import app
from app.config import get_settings

client = TestClient(app)

def test_verify_webhook_success():
    settings = get_settings()
    settings.META_VERIFY_TOKEN = "token_de_prueba"
    
    response = client.get("/webhook?hub.mode=subscribe&hub.verify_token=token_de_prueba&hub.challenge=123456")
    assert response.status_code == 200
    assert response.text == "123456"

def test_verify_webhook_fail():
    response = client.get("/webhook?hub.mode=subscribe&hub.verify_token=invalid_token&hub.challenge=123456")
    assert response.status_code == 403
