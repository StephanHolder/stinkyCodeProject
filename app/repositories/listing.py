from typing import Optional 
from sqlmodel import Session, select
from app.models.listing import Listing, ListingStatus

class ListingRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, listing_id: int) -> Optional[Listing]:
        return self.db.get(Listing, listing_id)

    def make_listing(self, listing: Listing) -> Listing:
        self.db.add(listing)
        self.db.commit()
        self.db.refresh(listing)
        return listing

    def get_active_listings(self, limit: int = 100, offset: int = 0) -> list[Listing]:
        statement = (
            select(Listing)
            .where(Listing.status == ListingStatus.ACTIVE)
            .offset(offset)
            .limit(limit)
        )
        results = self.db.exec(statement).all()
        return results