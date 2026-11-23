from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.models.listing import Listing
from app.models.listing_status import ListingStatus
from app.repositories.listing import ListingRepository
from app.services.lifecycle import ACTIONS, ADMIN_ACTIONS, apply_action
from app.states import InvalidTransition


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def _error(message: str, code: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"ok": False, "error": message}
    if code:
        result["code"] = code
    return result

def _parse_amenities(raw: str) -> list[str]:
    return [a.strip().lower() for a in (raw or "").split(",") if a.strip()]

def _is_provisional_student(user: dict | None) -> bool:
    return (
        bool(user)
        and user["role"] == "student" 
        and bool(user.get("provisional"))
    ) 

def _is_registerd_student(user: dict | None) -> bool:
    return (
        bool(user)
        and user["role"] == "student"
        and bool(user.get("student_id"))
        and not user.get("provisional")
    )

def _is_eligible_student(user: dict | None) -> bool:
    return (
        _is_registerd_student(user)
        or
        _is_provisional_student(user)
    )

ALLOWED_AREAS = {"st_augustine", "mount_hope"}
CONTACT_FIELDS = {"contact_phone", "contact_email"}

class ListingService:
    def __init__(self, listing_repo: ListingRepository):
        self.listing_repo = listing_repo

    def submit(self, landlord: dict | None, **fields: Any) -> dict[str, Any]:
        if not landlord or landlord["role"] != "landlord":
            return _error("landlords only", "forbidden")
        if fields["area"] not in ALLOWED_AREAS:
            return _error("area must be st_augustine or mount_hope")
        if fields["price"] <= 0:
            return _error("price must be positive")
        amenities = _parse_amenities(fields["amenities"])
        if not amenities:
            return _error("at least one amenity is required")
        fields["amenities"] = ",".join(amenities)
        listing = Listing(
            landlord_id=landlord["id"],
            status=ListingStatus.PENDING,
            created_at=_now(),
            **fields,
        )
        saved = self.listing_repo.save_listing(listing)
        return {"ok": True, "listing": saved.model_dump()}

    def transition(self, actor: dict | None, listing_id: int, action: str) -> dict[str, Any]:
        if not actor:
            return _error("unknown user", "unknown_user")
        if action not in ACTIONS:
            return _error(f"action must be one of {ACTIONS}", "invalid_action")

        required_role = "admin" if action in ADMIN_ACTIONS else "landlord"
        if actor["role"] != required_role:
            return _error(f"{required_role} only", "forbidden")

        listing = self.listing_repo.get_by_id(listing_id)
        if listing is None:
            return _error("listing not found", "listing_not_found")
        if required_role == "landlord" and listing.landlord_id != actor["id"]:
            return _error("not your listing", "forbidden")

        try:
            apply_action(listing, action)
        except InvalidTransition as exc:
            return _error(str(exc), "invalid_transition")

        saved = self.listing_repo.save_listing(listing)
        return {"ok": True, "listing": saved.model_dump()}

    def browse_for_students(self, student: dict | None, *, area = None, 
                            max_price = None, amenity = None) -> dict[str, Any]:
        if not _is_eligible_student(student):
            return _error(
                "student ID or provisional incoming access required", "forbidden"
            )

        show_contact = _is_registerd_student(student)
        wanted_amenity = amenity.strip().lower() if amenity else None

        results = []
        for listing in self.listing_repo.get_active_listings():
            if area and listing.area != area:
                continue
            if max_price is not None and listing.price > max_price:
                continue
            if wanted_amenity and wanted_amenity not in _parse_amenities(listing.amenities):
                continue
            item = listing.model_dump()
            if not show_contact:
                for field in CONTACT_FIELDS:
                    item.pop(field, None)
            results.append(item)
        return {"ok": True, "listings": results}

    def list_all(self, status: str | None = None) -> list[dict[str, Any]]:
            wanted = ListingStatus(status) if status else None
            return [l.model_dump() for l in self.listing_repo.list_all(wanted)]
