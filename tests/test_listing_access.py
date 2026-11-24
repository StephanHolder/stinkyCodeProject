import pytest
from sqlmodel import Session, select

from app.models.listing import Listing
from app.models.listing_status import ListingStatus
from app.models.message import Message
from app.models.user import User


@pytest.fixture
def listing_api_data(test_engine):
    with Session(test_engine) as session:
        users = {
            "admin": User(
                username="admin",
                email="admin@example.com",
                password="unused",
                role="admin",
            ),
            "owner": User(
                username="owner",
                email="owner@example.com",
                password="unused",
                role="landlord",
            ),
            "other_landlord": User(
                username="other",
                email="other@example.com",
                password="unused",
                role="landlord",
            ),
            "registered": User(
                username="registered",
                email="registered@example.com",
                password="unused",
                role="student",
                student_id="202012345",
            ),
            "provisional": User(
                username="provisional",
                email="provisional@example.com",
                password="unused",
                role="student",
                provisional=1,
            ),
            "ineligible": User(
                username="ineligible",
                email="ineligible@example.com",
                password="unused",
                role="student",
            ),
        }
        session.add_all(users.values())
        session.commit()

        listings = {
            "pending": Listing(
                landlord_id=users["owner"].id,
                title="Pending home",
                area="st_augustine",
                price=3000,
                amenities="wifi",
                contact_phone="555-0101",
                contact_email="owner@example.com",
                status=ListingStatus.PENDING,
                created_at="2026-01-01T00:00:00+00:00",
            ),
            "active": Listing(
                landlord_id=users["owner"].id,
                title="Active home",
                area="st_augustine",
                price=3500,
                amenities="wifi,parking",
                contact_phone="555-0102",
                contact_email="owner@example.com",
                status=ListingStatus.ACTIVE,
                created_at="2026-01-02T00:00:00+00:00",
            ),
            "inactive": Listing(
                landlord_id=users["owner"].id,
                title="Inactive home",
                area="mount_hope",
                price=2800,
                amenities="wifi",
                contact_phone="555-0103",
                contact_email="owner@example.com",
                status=ListingStatus.INACTIVE,
                created_at="2026-01-03T00:00:00+00:00",
            ),
        }
        session.add_all(listings.values())
        session.commit()

        return {
            "users": {key: user.id for key, user in users.items()},
            "listings": {key: listing.id for key, listing in listings.items()},
        }


def _headers(user_id):
    return {"X-User-Id": str(user_id)}


def test_registered_students_browse_only_active_listings_with_contact(
    api_client, listing_api_data
):
    response = api_client.get(
        "/api/student/listings",
        headers=_headers(listing_api_data["users"]["registered"]),
    )

    assert response.status_code == 200
    result = response.json()["listings"]
    assert [listing["title"] for listing in result] == ["Active home"]
    assert result[0]["contact_phone"] == "555-0102"
    assert result[0]["contact_email"] == "owner@example.com"


def test_provisional_students_browse_active_listings_without_contact(
    api_client, listing_api_data
):
    response = api_client.get(
        "/api/student/listings",
        headers=_headers(listing_api_data["users"]["provisional"]),
    )

    assert response.status_code == 200
    result = response.json()["listings"]
    assert [listing["title"] for listing in result] == ["Active home"]
    assert "contact_phone" not in result[0]
    assert "contact_email" not in result[0]


def test_student_without_registered_or_provisional_eligibility_is_denied(
    api_client, listing_api_data
):
    response = api_client.get(
        "/api/student/listings",
        headers=_headers(listing_api_data["users"]["ineligible"]),
    )

    assert response.status_code == 403


def test_landlord_cannot_transition_another_landlords_listing(
    api_client, listing_api_data, test_engine
):
    listing_id = listing_api_data["listings"]["active"]
    response = api_client.post(
        f"/api/listings/{listing_id}/transition",
        headers=_headers(listing_api_data["users"]["other_landlord"]),
        json={"action": "deactivate"},
    )

    assert response.status_code == 403
    with Session(test_engine) as session:
        assert session.get(Listing, listing_id).status is ListingStatus.ACTIVE


def test_transition_route_reports_invalid_transition_and_missing_listing(
    api_client, listing_api_data
):
    pending_id = listing_api_data["listings"]["pending"]
    invalid_transition = api_client.post(
        f"/api/listings/{pending_id}/transition",
        headers=_headers(listing_api_data["users"]["owner"]),
        json={"action": "activate"},
    )
    missing_listing = api_client.post(
        "/api/listings/9999/transition",
        headers=_headers(listing_api_data["users"]["owner"]),
        json={"action": "activate"},
    )
    unknown_action = api_client.post(
        f"/api/listings/{pending_id}/transition",
        headers=_headers(listing_api_data["users"]["owner"]),
        json={"action": "publish"},
    )

    assert invalid_transition.status_code == 409
    assert invalid_transition.json()["detail"] == (
        "cannot activate a listing that is pending"
    )
    assert missing_listing.status_code == 404
    assert unknown_action.status_code == 400


def test_admin_approval_then_owner_activation_work_through_api(
    api_client, listing_api_data
):
    listing_id = listing_api_data["listings"]["pending"]
    approved = api_client.post(
        f"/api/listings/{listing_id}/transition",
        headers=_headers(listing_api_data["users"]["admin"]),
        json={"action": "approve"},
    )
    activated = api_client.post(
        f"/api/listings/{listing_id}/transition",
        headers=_headers(listing_api_data["users"]["owner"]),
        json={"action": "activate"},
    )

    assert approved.status_code == 200
    assert approved.json()["listing"]["status"] == ListingStatus.APPROVED.value
    assert activated.status_code == 200
    assert activated.json()["listing"]["status"] == ListingStatus.ACTIVE.value


def test_messages_require_eligibility_and_an_active_listing(
    api_client, listing_api_data, test_engine
):
    headers = _headers(listing_api_data["users"]["registered"])
    sent = api_client.post(
        "/api/student/messages",
        headers=headers,
        json={
            "listing_id": listing_api_data["listings"]["active"],
            "body": "Is this still available?",
        },
    )
    closed_listing = api_client.post(
        "/api/student/messages",
        headers=headers,
        json={
            "listing_id": listing_api_data["listings"]["pending"],
            "body": "Is this still available?",
        },
    )
    ineligible_student = api_client.post(
        "/api/student/messages",
        headers=_headers(listing_api_data["users"]["ineligible"]),
        json={
            "listing_id": listing_api_data["listings"]["active"],
            "body": "Is this still available?",
        },
    )

    assert sent.status_code == 200
    assert closed_listing.status_code == 409
    assert ineligible_student.status_code == 403
    with Session(test_engine) as session:
        messages = session.exec(select(Message)).all()
        assert len(messages) == 1
        assert messages[0].listing_id == listing_api_data["listings"]["active"]
