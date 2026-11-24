"""The eight lifecycle statuses a listing can be in."""

from enum import Enum


class ListingStatus(str, Enum):
    PENDING = "pending"
    PROVISIONAL = "provisional"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    INACTIVE = "inactive"
    FORCE_DEACTIVATED = "force_deactivated"
    WITHDRAWN = "withdrawn"
