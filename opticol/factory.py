"""Factory functions for generating optimized collection classes.

This module provides the core factory layer that generates optimized collection classes of arbitrary
sizes. Each factory function creates a class using the appropriate metaclass (_sequence, _mapping,
or _set metaclasses) with __slots__ optimized for the specified size.

The factory functions are cached to ensure that requesting the same size class
multiple times returns the same class object, avoiding duplicate class creation in the case of
further projector definitions.

All classes returned by these factory functions have a constructor that has a signature where C is
the collection type:

class _GeneratedCollection(C):
    def __init__(self, other: C) -> None: ...

That is, construction assumes that an instance of the collection (not an iterator), will be used as
an argument.
"""

from collections.abc import (
    Callable,
    Mapping,
    MutableMapping,
    MutableSequence,
    MutableSet,
    Sequence,
    Set,
)
import functools
from typing import Any, Optional, ParamSpec, Protocol, TypeVar, overload

from opticol._mapping import OptimizedMappingMeta, OptimizedMutableMappingMeta
from opticol._sequence import OptimizedMutableSequenceMeta, OptimizedSequenceMeta
from opticol._set import OptimizedMutableSetMeta, OptimizedSetMeta

P = ParamSpec("P")
R_co = TypeVar("R_co", covariant=True)


class _WithCounter(Protocol[P, R_co]):
    """
    Defines a callable object that includes a counter member, for use with the following decorator.
    """

    counter: int

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R_co: ...


def with_counter(func: Callable[P, R_co]) -> _WithCounter[P, R_co]:
    """Generic type-safe decorator that adds counter."""

    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        wrapped.counter += 1  # pylint: disable=no-member
        return func(*args, **kwargs)

    setattr(wrapped, "counter", 0)

    return wrapped  # type: ignore


@with_counter
def _unique_cls_name(name: str) -> str:
    """
    Create a guaranteed unique class name given the desired name.

    Args:
        name: The class name to transform to ensure uniqueness.

    Returns:
        The transformed unique class name.
    """
    return f"{name}_{_unique_cls_name.counter}"


@overload
def cached[F: Callable[..., Any]](func: F, *, skipped_by: Optional[str] = None) -> F: ...


@overload
def cached[F: Callable[..., Any]](
    func: None = None, *, skipped_by: Optional[str] = None
) -> Callable[[F], F]: ...


def cached[F: Callable[..., Any]](
    func: Optional[F] = None, *, skipped_by: Optional[str] = None
) -> F | Callable[[F], F]:
    """Cache function results based on arguments to avoid duplicate work.

    This decorator caches function results using arguments and keyword arguments as the cache key.
    If arguments are not hashable, the function is called without caching. Used to ensure factory
    functions return the same class object for identical size/project parameters and that
    non hashable instances can still be provided for arguments.

    Args:
        func: The function to apply this decorator to. If no such function is provided, then the
            decorator itself is returned. In terms of calling convention, this generally maps to:
            - @cached                 <- func is not None
            - @cached()               <- func is None
            - @cached(skipped_by=...) <- func is None
        skipped_by: The optional name of the boolean parameter on the decorated function which if
            set will skip the caching logic entirely. This must be a parameter provided keyword.

    Returns:
        The decorator (or possibly the applied result of it).
    """

    def decorator(inner_func: Callable):
        cache = {}

        @functools.wraps(inner_func)
        def wrapper(*args, **kwargs):
            if skipped_by in kwargs:
                skip_flag = kwargs[skipped_by]
                if isinstance(skip_flag, bool) and skip_flag:
                    return inner_func(*args, **kwargs)

            key = (args, tuple(sorted(kwargs.items())))
            try:
                hash(key)
            except TypeError:
                return inner_func(*args, **kwargs)

            if key not in cache:
                cache[key] = inner_func(*args, **kwargs)
            return cache[key]

        return wrapper

    if func is not None:
        return decorator(func)

    return decorator


@cached(skipped_by="skip_cache")
def create_seq_class(
    size: int,
    project: Optional[Callable[[Sequence], Sequence]] = None,
    *,
    skip_cache: bool = False,  # pylint: disable=unused-argument
) -> type:
    """Create an optimized immutable Sequence class for the specified size.

    Args:
        size: Number of elements the sequence will hold.
        project: Optional function for recursively optimizing nested sequences.
        skip_cache: Flag if the module level cache should be bypassed.

    Returns:
        A Sequence class optimized for exactly 'size' elements.
    """
    return OptimizedSequenceMeta(
        _unique_cls_name(f"_Size{size}Sequence"),
        (Sequence,),
        {},
        internal_size=size,
        project=project,
    )


@cached(skipped_by="skip_cache")
def create_mut_seq_class(
    size: int,
    project: Optional[Callable[[MutableSequence], MutableSequence]] = None,
    *,
    skip_cache: bool = False,  # pylint: disable=unused-argument
) -> type:
    """Create an optimized MutableSequence class for the specified size.

    The created class supports overflow to standard list when elements exceed
    the allocated slot count.

    Args:
        size: Number of slots to allocate for elements.
        project: Optional function for recursively optimizing nested sequences.
        skip_cache: Flag if the module level cache should be bypassed.

    Returns:
        A MutableSequence class optimized for up to 'size' elements.
    """
    return OptimizedMutableSequenceMeta(
        _unique_cls_name(f"_Size{size}MutableSequence"),
        (MutableSequence,),
        {},
        internal_size=size,
        project=project,
    )


@cached(skipped_by="skip_cache")
def create_set_class(
    size: int,
    project: Optional[Callable[[Set], Set]] = None,
    *,
    skip_cache: bool = False,  # pylint: disable=unused-argument
) -> type:
    """Create an optimized immutable Set class for the specified size.

    Args:
        size: Number of elements the set will hold.
        project: Optional function for recursively optimizing nested sets.
        skip_cache: Flag if the module level cache should be bypassed.

    Returns:
        A Set class optimized for exactly 'size' elements.
    """
    return OptimizedSetMeta(
        _unique_cls_name(f"_Size{size}Set"), (Set,), {}, internal_size=size, project=project
    )


@cached(skipped_by="skip_cache")
def create_mut_set_class(
    size: int,
    project: Optional[Callable[[MutableSet], MutableSet]] = None,
    *,
    skip_cache: bool = False,  # pylint: disable=unused-argument
) -> type:
    """Create an optimized MutableSet class for the specified size.

    The created class supports overflow to standard set when elements exceed
    the allocated slot count.

    Args:
        size: Number of slots to allocate for elements.
        project: Optional function for recursively optimizing nested sets.
        skip_cache: Flag if the module level cache should be bypassed.

    Returns:
        A MutableSet class optimized for up to 'size' elements.
    """
    return OptimizedMutableSetMeta(
        _unique_cls_name(f"_Size{size}MutableSet"),
        (MutableSet,),
        {},
        internal_size=size,
        project=project,
    )


@cached(skipped_by="skip_cache")
def create_mapping_class(
    size: int,
    *,
    skip_cache: bool = False,  # pylint: disable=unused-argument
) -> type:
    """Create an optimized immutable Mapping class for the specified size.

    Args:
        size: Number of key-value pairs the mapping will hold.
        skip_cache: Flag if the module level cache should be bypassed.

    Returns:
        A Mapping class optimized for exactly 'size' key-value pairs.
    """
    return OptimizedMappingMeta(
        _unique_cls_name(f"_Size{size}Mapping"), (Mapping,), {}, internal_size=size
    )


@cached(skipped_by="skip_cache")
def create_mut_mapping_class(
    size: int,
    *,
    skip_cache: bool = False,  # pylint: disable=unused-argument
) -> type:
    """Create an optimized MutableMapping class for the specified size.

    The created class supports overflow to standard dict when key-value pairs
    exceed the allocated slot count.

    Args:
        size: Number of slots to allocate for key-value pairs.
        skip_cache: Flag if the module level cache should be bypassed.

    Returns:
        A MutableMapping class optimized for up to 'size' key-value pairs.
    """
    return OptimizedMutableMappingMeta(
        _unique_cls_name(f"_Size{size}MutableMapping"),
        (MutableMapping,),
        {},
        internal_size=size,
    )
