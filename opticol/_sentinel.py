"""Sentinel values and overflow wrapper for mutable collections.

This module defines sentinel objects used to mark empty slots in mutable collections, and an
Overflow wrapper used when collections exceed their allocated slot capacity.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True, frozen=True)
class EndMarker:
    """Sentinel class marking the end of used slots in mutable collections.

    The only instance of this class is stored in unused slots to distinguish them from slots
    containing None or other falsy values.
    """


END = EndMarker()


@dataclass(slots=True, frozen=True)
class ENDWithLength:
    """Length marker stored only in the final slot of a mutable sequence's slot array.

    Replaces the old approach of filling every empty slot with a sentinel. Only the last
    slot is written; slots between the last valid element and the last slot are left
    unassigned, saving memory.

    Attributes:
        length: When >= 0, the number of elements stored in the leading slots. When < 0,
            the sequence is in overflow mode and the first slot holds an Overflow object.
    """

    length: int


@dataclass(slots=True, frozen=True)
class Overflow:
    """Wrapper for collections that exceed their optimized slot capacity.

    When a mutable collection grows beyond its allocated slots, the entire collection is stored in
    this wrapper's data attribute (as a standard list, set, or dict). This allows seamless fallback
    to standard Python types while maintaining the same interface.

    Attributes:
        data: The standard Python collection (list, set, or dict) holding all elements.
    """

    data: Any
