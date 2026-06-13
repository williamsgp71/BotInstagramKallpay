import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.webhook.service import process_incoming_dm, process_incoming_comment

# Create an isolated test engine in-memory
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(name="db_session")
def fixture_db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.mark.asyncio
@patch("app.webhook.service.get_llm_response", new_callable=AsyncMock)
@patch("app.webhook.service.send_meta_dm", new_callable=AsyncMock)
async def test_process_incoming_dm(mock_send_dm, mock_llm_response, db_session):
    mock_llm_response.return_value = "Respuesta bot"
    
    await process_incoming_dm(
        sender_id="user_test",
        message_id="msg_123",
        text="¿Manzanilla?",
        db=db_session
    )
    
    mock_send_dm.assert_called_once_with("user_test", "Respuesta bot")
    mock_llm_response.assert_called_once()

@pytest.mark.asyncio
@patch("app.webhook.service.get_llm_response", new_callable=AsyncMock)
@patch("app.webhook.service.send_meta_comment_reply", new_callable=AsyncMock)
async def test_process_incoming_comment(mock_send_comment, mock_llm_response, db_session):
    mock_llm_response.return_value = "Respuesta bot comentario"
    
    await process_incoming_comment(
        comment_id="comment_123",
        text="¿Sirve para el dolor?",
        db=db_session
    )
    
    mock_send_comment.assert_called_once_with("comment_123", "Respuesta bot comentario")
    mock_llm_response.assert_called_once()
