from typing import TypeVar, overload, Generic
from collections.abc import Iterable, MutableSequence, Sequence

def project[T](original: Sequence[T]) -> Sequence[T]: ...

T_co = TypeVar("T_co", covariant=True)

class _Sequence(Sequence[T_co], Generic[T_co]):
    """
    As Sequence is an abstract base class, the type stubs need to explicitly annotate the overriden
    methods which can then be referenced for each optimized sequence type.
    """
    @overload
    def __getitem__(self, key: int) -> T_co: ...
    @overload
    def __getitem__(self, key: slice) -> Sequence[T_co]: ...
    def __len__(self) -> int: ...

class Size0Sequence(_Sequence[T_co]):
    def __init__(cls) -> None: ...

class Size1Sequence(_Sequence[T_co]):
    def __init__(cls, item1: T_co) -> None: ...

class Size2Sequence(_Sequence[T_co]):
    def __init__(cls, item1: T_co, item2: T_co) -> None: ...

class Size3Sequence(_Sequence[T_co]):
    def __init__(cls, item1: T_co, item2: T_co, item3: T_co) -> None: ...
