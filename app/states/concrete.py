"""The eight concrete listing states.

Each class implements only the operations that are allowed from that status.
Anything not overridden is refused by ``ListingState``.
"""

from __future__ import annotations

from app.models.listing_status import ListingStatus
from app.states.base import ListingState


class PendingState(ListingState):
    status = ListingStatus.PENDING

    def approve(self) -> None:
        self._move_to(ListingStatus.APPROVED)

    def provisionally_accept(self) -> None:
        self._move_to(ListingStatus.PROVISIONAL)

    def reject(self) -> None:
        self._move_to(ListingStatus.REJECTED)

    def withdraw(self) -> None:
        self._move_to(ListingStatus.WITHDRAWN)


class ProvisionalState(ListingState):
    status = ListingStatus.PROVISIONAL

    def approve(self) -> None:
        self._move_to(ListingStatus.APPROVED)

    def reject(self) -> None:
        self._move_to(ListingStatus.REJECTED)

    def resubmit(self) -> None:
        self._move_to(ListingStatus.PENDING)

    def withdraw(self) -> None:
        self._move_to(ListingStatus.WITHDRAWN)


class ApprovedState(ListingState):
    status = ListingStatus.APPROVED

    def activate(self) -> None:
        self._move_to(ListingStatus.ACTIVE)

    def force_deactivate(self) -> None:
        self._move_to(ListingStatus.FORCE_DEACTIVATED)

    def withdraw(self) -> None:
        self._move_to(ListingStatus.WITHDRAWN)


class RejectedState(ListingState):
    status = ListingStatus.REJECTED

    def resubmit(self) -> None:
        self._move_to(ListingStatus.PENDING)


class ActiveState(ListingState):
    status = ListingStatus.ACTIVE

    def deactivate(self) -> None:
        self._move_to(ListingStatus.INACTIVE)

    def force_deactivate(self) -> None:
        self._move_to(ListingStatus.FORCE_DEACTIVATED)

    def withdraw(self) -> None:
        self._move_to(ListingStatus.WITHDRAWN)

    def is_visible_to_students(self) -> bool:
        return True


class InactiveState(ListingState):
    status = ListingStatus.INACTIVE

    def activate(self) -> None:
        self._move_to(ListingStatus.ACTIVE)

    def withdraw(self) -> None:
        self._move_to(ListingStatus.WITHDRAWN)


class ForceDeactivatedState(ListingState):
    status = ListingStatus.FORCE_DEACTIVATED

    def resubmit(self) -> None:
        self._move_to(ListingStatus.PENDING)


class WithdrawnState(ListingState):
    """Terminal: every operation is refused."""

    status = ListingStatus.WITHDRAWN
