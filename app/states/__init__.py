"""State pattern for the listing lifecycle."""

from __future__ import annotations

from typing import Any

from app.models.listing_status import ListingStatus
from app.states.base import InvalidTransition, ListingState
from app.states.concrete import (
    ActiveState,
    ApprovedState,
    ForceDeactivatedState,
    InactiveState,
    PendingState,
    ProvisionalState,
    RejectedState,
    WithdrawnState,
)

_STATES: dict[ListingStatus, type[ListingState]] = {
    ListingStatus.PENDING: PendingState,
    ListingStatus.PROVISIONAL: ProvisionalState,
    ListingStatus.APPROVED: ApprovedState,
    ListingStatus.REJECTED: RejectedState,
    ListingStatus.ACTIVE: ActiveState,
    ListingStatus.INACTIVE: InactiveState,
    ListingStatus.FORCE_DEACTIVATED: ForceDeactivatedState,
    ListingStatus.WITHDRAWN: WithdrawnState,
}


def state_for(listing: Any) -> ListingState:
    """Rebuild the state object that matches ``listing.status``."""
    return _STATES[ListingStatus(listing.status)](listing)


__all__ = ["InvalidTransition", "ListingState", "state_for"]
