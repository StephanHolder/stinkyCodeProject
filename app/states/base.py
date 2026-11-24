"""Abstract listing state: refuses every operation unless a subclass allows it."""

from __future__ import annotations

from typing import Any

from app.models.listing_status import ListingStatus


class InvalidTransition(Exception):
    """Raised when an operation is not permitted from the listing's current status."""

    def __init__(self, action: str, status: ListingStatus) -> None:
        self.action = action
        self.status = status
        super().__init__(f"cannot {action} a listing that is {status.value}")


class ListingState:
    """Common lifecycle interface.

    Each concrete state overrides only the operations it permits. Everything
    else falls through to the default here, which refuses the operation. A
    state changes the listing by setting ``listing.status`` and never touches
    the database session; saving is the service's job.
    """

    status: ListingStatus

    def __init__(self, listing: Any) -> None:
        self.listing = listing

    def _refuse(self, action: str) -> None:
        raise InvalidTransition(action, self.status)

    def _move_to(self, new_status: ListingStatus) -> None:
        self.listing.status = new_status

    # Admin operations
    def approve(self) -> None:
        self._refuse("approve")

    def provisionally_accept(self) -> None:
        self._refuse("provisionally accept")

    def reject(self) -> None:
        self._refuse("reject")

    def force_deactivate(self) -> None:
        self._refuse("force-deactivate")

    # Landlord operations
    def activate(self) -> None:
        self._refuse("activate")

    def deactivate(self) -> None:
        self._refuse("deactivate")

    def resubmit(self) -> None:
        self._refuse("resubmit")

    def withdraw(self) -> None:
        self._refuse("withdraw")

    # Visibility
    def is_visible_to_students(self) -> bool:
        return False

    def accepts_messages(self) -> bool:
        return self.is_visible_to_students()
