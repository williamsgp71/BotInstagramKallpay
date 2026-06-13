import pytest
from unittest.mock import AsyncMock, patch
from app.llm.client import get_llm_response

@pytest.mark.asyncio
@patch("app.llm.client.AsyncOpenAI")
async def test_get_llm_response(mock_openai):
    # Configurar mock de respuesta
    mock_client = AsyncMock()
    mock_openai.return_value = mock_client
    
    mock_response = AsyncMock()
    mock_response.choices = [
        AsyncMock(message=AsyncMock(content="Respuesta simulada"))
    ]
    mock_client.chat.completions.create.return_value = mock_response

    response = await get_llm_response(
        prompt_system="Eres un experto",
        prompt_user="Hola",
        history=[]
    )
    assert response == "Respuesta simulada"
