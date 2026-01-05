"""Factory functions for generating optimized collection classes.

This module provides the core factory layer that generates optimized collection
classes of arbitrary sizes. Each factory function creates a class using the
appropriate metaclass (_sequence, _mapping, or _set metaclasses) with __slots__
optimized for the specified size.

The factory functions are cached to ensure that requesting the same size class
multiple times returns the same class object, avoiding duplicate class creation
and enabling type identity checks.
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
from typing import Optional

from opticol._mapping import OptimizedMappingMeta, OptimizedMutableMappingMeta
from opticol._sequence import OptimizedMutableSequenceMeta, OptimizedSequenceMeta
from opticol._set import OptimizedMutableSetMeta, OptimizedSetMeta


def cached(func):
    """Cache function results based on arguments to avoid duplicate work.

    This decorator caches function results using arguments and keyword arguments
    as the cache key. If arguments are not hashable, the function is called
    without caching. Used to ensure factory functions return the same class
    object for identical size/project parameters.

    Args:
        func: Function to cache.

    Returns:
        Wrapped function with caching behavior.
    """
    cache = {}

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            key = (args, tuple(sorted(kwargs.items())))
            hash(key)
        except TypeError:
            return func(*args, **kwargs)

        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]

    return wrapper


@cached
def create_seq_class(size: int, project: Optional[Callable[[Sequence], Sequence]] = None) -> type:
    """Create an optimized immutable Sequence class for the specified size.

    Args:
        size: Number of elements the sequence will hold.
        project: Optional function for recursively optimizing nested sequences.

    Returns:
        A Sequence class optimized for exactly 'size' elements.
    """
    return OptimizedSequenceMeta(
        f"_Size{size}Sequence",
        (Sequence,),
        {},
        internal_size=size,
        project=project,
    )


@cached
def create_mut_seq_class(
    size: int, project: Optional[Callable[[MutableSequence], MutableSequence]]
) -> type:
    """Create an optimized MutableSequence class for the specified size.

    The created class supports overflow to standard list when elements exceed
    the allocated slot count.

    Args:
        size: Number of slots to allocate for elements.
        project: Optional function for recursively optimizing nested sequences.

    Returns:
        A MutableSequence class optimized for up to 'size' elements.
    """
    return OptimizedMutableSequenceMeta(
        f"_Size{size}MutableSequence",
        (MutableSequence,),
        {},
        internal_size=size,
        project=project,
    )


@cached
def create_set_class(size: int, project: Optional[Callable[[Set], Set]] = None) -> type:
    """Create an optimized immutable Set class for the specified size.

    Args:
        size: Number of elements the set will hold.
        project: Optional function for recursively optimizing nested sets.

    Returns:
        A Set class optimized for exactly 'size' elements.
    """
    return OptimizedSetMeta(f"_Size{size}Set", (Set,), {}, internal_size=size, project=project)


@cached
def create_mut_set_class(
    size: int, project: Optional[Callable[[MutableSet], MutableSet]] = None
) -> type:
    """Create an optimized MutableSet class for the specified size.

    The created class supports overflow to standard set when elements exceed
    the allocated slot count.

    Args:
        size: Number of slots to allocate for elements.
        project: Optional function for recursively optimizing nested sets.

    Returns:
        A MutableSet class optimized for up to 'size' elements.
    """
    return OptimizedMutableSetMeta(
        f"_Size{size}MutableSet",
        (MutableSet,),
        {},
        internal_size=size,
        project=project,
    )


@cached
def create_mapping_class(size: int) -> type:
    """Create an optimized immutable Mapping class for the specified size.

    Args:
        size: Number of key-value pairs the mapping will hold.

    Returns:
        A Mapping class optimized for exactly 'size' key-value pairs.
    """
    return OptimizedMappingMeta(f"_Size{size}Mapping", (Mapping,), {}, internal_size=size)


@cached
def create_mut_mapping_class(size: int) -> type:
    """Create an optimized MutableMapping class for the specified size.

    The created class supports overflow to standard dict when key-value pairs
    exceed the allocated slot count.

    Args:
        size: Number of slots to allocate for key-value pairs.

    Returns:
        A MutableMapping class optimized for up to 'size' key-value pairs.
    """
    return OptimizedMutableMappingMeta(
        f"_Size{size}MutableMapping",
        (MutableMapping,),
        {},
        internal_size=size,
    )
