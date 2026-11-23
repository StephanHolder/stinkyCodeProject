from sqlmodel import Session
from app.models.message import Message

import logging
logger = logging.getLogger(__name__)

class MessageRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, message: Message) -> Message:
        try:
            self.db.add(message)
            self.db.commit()
            self.db.refresh(message)
            return message
        except Exception as e:
            logger.error(f"An error occurred while saving message: {e}")
            self.db.rollback()
            raise
