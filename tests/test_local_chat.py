import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, AsyncMock

client = TestClient(app)

@pytest.mark.asyncio
@patch("app.webhook.service.get_llm_response", new_callable=AsyncMock)
async def test_local_chat_endpoint(mock_llm_response):
    mock_llm_response.return_value = "Hola desde el bot de prueba"
    
    response = client.post("/test-chat", json={"sender_id": "test_local_user", "message": "recomiéndame algo para dormir"})
    assert response.status_code == 200
    data = response.json()
    assert data["reply"] == "Hola desde el bot de prueba"
