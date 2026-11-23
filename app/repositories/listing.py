from typing import Optional 
from sqlmodel import Session, select
from app.models.listing import Listing, ListingStatus

import logging
logger = logging.getLogger(__name__)

class ListingRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, listing_id: int) -> Optional[Listing]:
        return self.db.get(Listing, listing_id)

    def save_listing(self, listing: Listing) -> Listing:
        try:
            self.db.add(listing)
            self.db.commit()
            self.db.refresh(listing)
            return listing
        except Exception as e:
            logger.error(f"An error occurred while saving listing: {e}")
            self.db.rollback()
            raise

    def get_active_listings(self) -> list[Listing]:
        statement = (
            select(Listing)
            .where(Listing.status == ListingStatus.ACTIVE)
            .order_by(Listing.id)
        )
        return list(self.db.exec(statement).all())

    def list_all(self, status: Optional[ListingStatus] = None) -> list[ListingStatus]:
        statement = select(Listing).order_by(Listing.id)
        if status is not None:
            statement = statement.where(Listing.status == status)
        return list(self.db.exec(statement).all())