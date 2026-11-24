"""Service-level rules around the lifecycle: submit validation, browse filters, errors."""

import pytest

from app.models.listing_status import ListingStatus
from app.repositories.listing import ListingRepository
from app.services.listing_service import ListingService

ADMIN = {"id": 1, "role": "admin"}
LANDLORD = {"id": 2, "role": "landlord"}
STUDENT = {"id": 4, "role": "student", "student_id": "816000001", "provisional": 0}

GOOD = dict(title="Room", area="st_augustine", price=1500, amenities="wifi,parking",
            contact_phone="1", contact_email="a@b.c")


@pytest.fixture
def service(test_session):
    return ListingService(ListingRepository(test_session))


def submit(service, **overrides):
    return service.submit(LANDLORD, **{**GOOD, **overrides})


def publish(service, **overrides):
    listing_id = submit(service, **overrides)["listing"]["id"]
    assert service.transition(ADMIN, listing_id, "approve")["ok"]
    assert service.transition(LANDLORD, listing_id, "activate")["ok"]
    return listing_id


def test_submit_starts_in_pending(service):
    result = submit(service)
    assert result["ok"] and result["listing"]["status"] == ListingStatus.PENDING


def test_only_landlords_can_submit(service):
    result = service.submit(STUDENT, **GOOD)
    assert not result["ok"] and result["code"] == "forbidden"


@pytest.mark.parametrize("overrides", [
    {"area": "port_of_spain"},
    {"price": 0},
    {"amenities": ""},
    {"amenities": " , ,"},
])
def test_submit_rejects_invalid_input(service, overrides):
    assert not submit(service, **overrides)["ok"]


def test_submit_normalises_amenities(service):
    listing = submit(service, amenities=" WiFi , Parking ")["listing"]
    assert listing["amenities"] == "wifi,parking"


def test_browse_filters_by_area_price_and_amenity(service):
    cheap = publish(service, price=1000, area="mount_hope", amenities="wifi")
    dear = publish(service, price=3000, area="st_augustine", amenities="wifi,parking")

    def ids(**filters):
        return [l["id"] for l in service.browse_for_students(STUDENT, **filters)["listings"]]

    assert ids() == [cheap, dear]
    assert ids(area="mount_hope") == [cheap]
    assert ids(max_price=1500) == [cheap]
    assert ids(amenity="WiFi") == [cheap, dear]       # case-insensitive
    assert ids(amenity="park") == []                  # whole item only
    assert ids(amenity="parking") == [dear]


def test_transition_rejects_unknown_user_and_unknown_action(service):
    listing_id = submit(service)["listing"]["id"]
    assert service.transition(None, listing_id, "approve")["code"] == "unknown_user"
    assert service.transition(ADMIN, listing_id, "verify")["code"] == "invalid_action"


def test_list_all_can_filter_by_status(service):
    pending = submit(service)["listing"]["id"]
    active = publish(service)
    assert [l["id"] for l in service.list_all("pending")] == [pending]
    assert [l["id"] for l in service.list_all("active")] == [active]
    assert len(service.list_all()) == 2


def test_list_all_rejects_unknown_status(service):
    with pytest.raises(ValueError):
        service.list_all("bogus")
