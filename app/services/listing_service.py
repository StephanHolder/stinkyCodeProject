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

def _error(message: str) -> dict[str, Any]:
    return {"ok": False, "error": message}

class ListingService:
    def __init__(self, listing_repo: ListingRepository):
        self.listing_repo = listing_repo

    def submit(self, landlord: dict | None, **fields: Any) -> dict[str, Any]:
        if not landlord or landlord["role"] != "landlord":
            return _error("landlords only")
        if fields["price"] <= 0:
            return _error("price must be positive")
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
            return _error("unknown user")
        if action not in ACTIONS:
            return _error(f"action must be one of {ACTIONS}")

        required_role = "admin" if action in ADMIN_ACTIONS else "landlord"
        if actor["role"] != required_role:
            return _error(f"{required_role} only")

        listing = self.listing_repo.get_by_id(listing_id)
        if listing is None:
            return _error("listing not found")
        if required_role == "landlord" and listing.landlord_id != actor["id"]:
            return _error("not your listing")

        try:
            apply_action(listing, action)
        except InvalidTransition as exc:
            return _error(str(exc))

        saved = self.listing_repo.save_listing(listing)
        return {"ok": True, "listing": saved.model_dump()}

    def browse_for_students(self, student: dict | None, *, area = None, 
                            max_price = None, amenity = None) -> dict[str, Any]:
        if not student or student["role"] != student:
            return _error("student only")
        results = []
        for listing in self.listing_repo.get_active_listings():
            if area and listing.area != area:
                continue
            if max_price is not None and listing.price > max_price:
                continue
            if amenity and amenity not in listing.amenties:
                continue
            results.append(listing.model_dump())
        return {"ok": True, "listings": results}

    def list_all(self, status: str | None = None) -> list[dict[str, Any]]:
            wanted = ListingStatus(status) if status else None
            return [l.model_dump() for l in self.listings.list_all(wanted)]


