"""Sentinel values and overflow wrapper for mutable collections.

This module defines sentinel objects used to mark empty slots in mutable collections, and an
Overflow wrapper used when collections exceed their allocated slot capacity.
"""

from dataclasses import dataclass
from typing import Any


class EndMarker:
    """Sentinel class marking the end of used slots in mutable collections.

    The only instance of this class is stored in unused slots to distinguish them from slots
    containing None or other falsy values.
    """


END = EndMarker()


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
