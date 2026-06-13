import pytest
from app.database import Base, engine, get_db
from app.models import Conversation, Message, WebhookLog
from sqlalchemy.orm import Session

@pytest.fixture(name="db_session")
def fixture_db_session():
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
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
