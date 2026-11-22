from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.models.message import Message
from app.repositories.listing import ListingRepository
from app.repositories.message import MessageRepository
from app.services.listing_service import _is_eligible_student
from app.states import state_for

def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def _error(message: str) -> dict[str, Any]:
    return {"ok": False, "error": message}

class MessageService:
    def __init__(self, listing_repo: ListingRepository, message_repo: MessageRepository):
        self.listing_repo = listing_repo
        self.message_repo = message_repo

    def send(self, student: dict | None, listing_id: int, body: str) -> dict[str, Any]:
        if not _is_eligible_student(student):
            return _error("student ID or provisional incoming access required")
        if not body.strip():
            return _error("body required")

        listing = self.listing_repo.get_by_id(listing_id)
        if listing is None:
            return _error("listing not found")
        if not state_for(listing).accepts_messages():
            return _error("messaging is closed for this listing")

        message = self.message_repo.save(
            Message(listing_id=listing_id, student_id=student["id"],
                    body=body, created_at=_now())
        )
        return {"ok": True, "message_id": message.id}
