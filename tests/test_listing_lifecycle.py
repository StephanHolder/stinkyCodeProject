from types import SimpleNamespace

import pytest

from app.models.listing_status import ListingStatus
from app.services.lifecycle import ACTIONS, apply_action
from app.states import InvalidTransition, state_for

ALLOWED_TRANSITIONS = {
    (ListingStatus.PENDING, "approve"): ListingStatus.APPROVED,
    (ListingStatus.PENDING, "provisionally_accept"): ListingStatus.PROVISIONAL,
    (ListingStatus.PENDING, "reject"): ListingStatus.REJECTED,
    (ListingStatus.PENDING, "withdraw"): ListingStatus.WITHDRAWN,
    (ListingStatus.PROVISIONAL, "approve"): ListingStatus.APPROVED,
    (ListingStatus.PROVISIONAL, "reject"): ListingStatus.REJECTED,
    (ListingStatus.PROVISIONAL, "resubmit"): ListingStatus.PENDING,
    (ListingStatus.PROVISIONAL, "withdraw"): ListingStatus.WITHDRAWN,
    (ListingStatus.APPROVED, "activate"): ListingStatus.ACTIVE,
    (ListingStatus.APPROVED, "force_deactivate"): ListingStatus.FORCE_DEACTIVATED,
    (ListingStatus.APPROVED, "withdraw"): ListingStatus.WITHDRAWN,
    (ListingStatus.REJECTED, "resubmit"): ListingStatus.PENDING,
    (ListingStatus.ACTIVE, "deactivate"): ListingStatus.INACTIVE,
    (ListingStatus.ACTIVE, "force_deactivate"): ListingStatus.FORCE_DEACTIVATED,
    (ListingStatus.ACTIVE, "withdraw"): ListingStatus.WITHDRAWN,
    (ListingStatus.INACTIVE, "activate"): ListingStatus.ACTIVE,
    (ListingStatus.INACTIVE, "withdraw"): ListingStatus.WITHDRAWN,
    (ListingStatus.FORCE_DEACTIVATED, "resubmit"): ListingStatus.PENDING,
}


@pytest.mark.parametrize(
    ("status", "action"),
    [
        (status, action)
        for status in ListingStatus
        for action in ACTIONS
    ],
    ids=lambda value: value.value if isinstance(value, ListingStatus) else value,
)
def test_listing_transition_is_allowed_only_when_defined(status, action):
    listing = SimpleNamespace(status=status)
    expected_status = ALLOWED_TRANSITIONS.get((status, action))

    if expected_status is None:
        with pytest.raises(InvalidTransition) as error:
            apply_action(listing, action)

        expected_action = {
            "provisionally_accept": "provisionally accept",
            "force_deactivate": "force-deactivate",
        }.get(action, action)
        assert error.value.action == expected_action
        assert error.value.status == status
        assert listing.status == status
    else:
        apply_action(listing, action)

        assert listing.status == expected_status


@pytest.mark.parametrize("status", list(ListingStatus))
def test_only_active_listings_are_visible_and_accept_messages(status):
    state = state_for(SimpleNamespace(status=status))
    expected = status is ListingStatus.ACTIVE

    assert state.is_visible_to_students() is expected
    assert state.accepts_messages() is expected
