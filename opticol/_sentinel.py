from dataclasses import dataclass
from typing import Any


class EndMarker: ...


END = EndMarker()


@dataclass(slots=True, frozen=True)
class Overflow:
    data: Any
