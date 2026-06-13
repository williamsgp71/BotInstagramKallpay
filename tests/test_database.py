import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.database import Base
from app.models import Conversation, Message, WebhookLog

# Create a separate, isolated engine for testing in-memory
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

def test_create_and_retrieve_message(db_session: Session):
    conv = Conversation(id="user_123")
    db_session.add(conv)
    db_session.commit()

    msg = Message(conversation_id="user_123", sender_type="user", content="Hola")
    db_session.add(msg)
    db_session.commit()

    retrieved = db_session.query(Message).first()
    assert retrieved.content == "Hola"
    assert retrieved.sender_type == "user"

def test_create_and_retrieve_webhook_log(db_session: Session):
    log = WebhookLog(id="evt_123", event_type="messages")
    db_session.add(log)
    db_session.commit()

    retrieved = db_session.query(WebhookLog).first()
    assert retrieved is not None
    assert retrieved.id == "evt_123"
    assert retrieved.event_type == "messages"
    assert retrieved.processed_at is not None
