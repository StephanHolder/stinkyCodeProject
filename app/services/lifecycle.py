"""
Listing lifecycle tracker — procedural flag soup.

Intended flow: pending → verified → active|inactive, or pending → rejected.
Landlord may toggle active/inactive only after verification.

This module mixes a status string with four boolean flags updated through
nested conditionals. Invalid jumps are allowed; flags and status drift.

Ideal fix: State pattern (one state object per status with allowed transitions).
"""

from __future__ import annotations
from typing import Any
from app.states import state_for

ADMIN_ACTIONS = ("approve", "provisionally_accept", "reject", "force_deactivate")
LANDLORD_ACTIONS = ("activate", "deactivate", "resubmit", "withdraw")
ACTIONS = ADMIN_ACTIONS + LANDLORD_ACTIONS

def apply_action(listing: Any, action: str) -> None:
    getattr(state_for(listing), action)()

def visible_to_students(listing: Any) -> bool:
    return state_for(listing).is_visible_to_students()