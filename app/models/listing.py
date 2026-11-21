from typing import Optional

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel

from app.models.listing_status import ListingStatus


class Listing(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    landlord_id: int = Field(index=True)
    title: str
    area: str
    price: int
    amenities: str = ""
    contact_phone: str
    contact_email: str
    photos: str = ""
    # The single source of truth for where the listing is in its lifecycle.
    # Stored as the enum's value (e.g. "active") in a plain VARCHAR column.
    status: ListingStatus = Field(
        default=ListingStatus.PENDING,
        sa_column=Column(
            SAEnum(
                ListingStatus,
                native_enum=False,
                create_constraint=False,
                length=20,
                values_callable=lambda enum: [member.value for member in enum],
            ),
            nullable=False,
            index=True,
        ),
    )
    created_at: str
