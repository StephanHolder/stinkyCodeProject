"""Listing CRUD, browse filters, messaging, and lifecycle transitions."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlmodel import Session

from app.database import engine
from app.models.listing import Listing
from app.models.message import Message
from app.repositories.listing import ListingRepository
from app.services.housing_auth import get_user
from app.services.listing_service import ListingService

def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def _service(session: Session) -> ListingService:
    return ListingService(ListingRepository(session))

def submit_listing(
    landlord_id: int,
    *,
    title: str,
    area: str,
    price: int,
    amenities: str,
    contact_phone: str,
    contact_email: str,
    photos: str = "",
) -> dict[str, Any]:
    with Session(engine) as session:
        return _service(session).submit(
            get_user(landlord_id),
            title=title,
            area=area,
            price=price,
            amenities=amenities,
            contact_phone=contact_phone,
            contact_email=contact_email,
            photos=photos,
        )


def transition(actor_id: int, listing_id: int, action: str) -> dict[str, Any]:
    with Session(engine) as session:
        return _service(session).transition(get_user(actor_id), listing_id, action)


def browse_for_students(
    student_id: int,
    *,
    area: str | None = None,
    max_price: int | None = None,
    amenity: str | None = None,
) -> dict[str, Any]:
    with Session(engine) as session:
        return _service(session).browse_for_students(
            get_user(student_id), area=area, max_price=max_price, amenity=amenity
        )


def list_all(*, status: str | None = None) -> list[dict[str, Any]]:
    with Session(engine) as session:
        return _service(session).list_all(status)

def send_message(student_id: int, listing_id: int, body: str) -> dict[str, Any]:
    student = get_user(student_id)
    if not student or student["role"] != "student":
        return {"ok": False, "error": "students only"}
    if not body.strip():
        return {"ok": False, "error": "body required"}
    with Session(engine) as session:
        listing = session.get(Listing, listing_id)
        if listing is None:
            return {"ok": False, "error": "listing not found"}
        # DEFECT: can message pending/rejected listings
        message = Message(
            listing_id=listing_id,
            student_id=student_id,
            body=body,
            created_at=_now(),
        )
        session.add(message)
        session.commit()
        session.refresh(message)
        return {"ok": True, "message_id": message.id}
