## Opticol

Optimized collections (*opticol*) for Python. This package provides memory-efficient, slot-based implementations of Python's standard collection types:

* Mapping / MutableMapping
* Sequence / MutableSequence
* Set / MutableSet

An example of the insight behind the package: an empty set (on Python 3.14) uses 216 bytes, but an empty object with empty `__slots__` uses only 32 bytes. For applications creating thousands of small collections, *opticol* can dramatically reduce memory usage without API changes. The optimized types fully implement their respective collection ABCs.

## When to Use Opticol

Opticol is beneficial when your application:
- Creates many small collections (0-3 elements is the default optimization range)
- Has memory constraints or needs to reduce memory footprint
- Can benefit from transparent optimization without code changes

For general use cases where memory isn't constrained, standard Python collections are perfectly adequate.

## Usage

### Quick Start (Convenience API)

The simplest way to use opticol is via the convenience functions:

```python
import opticol

# Create optimized collections
optimized_list = opticol.seq([1, 2, 3])
optimized_set = opticol.set({1, 2, 3})
optimized_dict = opticol.mapping({'a': 1, 'b': 2})

# Mutable variants
mutable_list = opticol.mut_seq([1, 2])
mutable_set = opticol.mut_set({1, 2})
mutable_dict = opticol.mut_mapping({'a': 1})

# They implement standard ABCs
from collections.abc import Sequence, MutableSequence
assert isinstance(optimized_list, Sequence)
assert isinstance(mutable_list, MutableSequence)
```

By default, these functions optimize collections of size 0-3. Collections outside this range are returned unchanged as standard Python types. This method is useful for smaller scripts or applications.

### Advanced (Projector API)

For custom optimization strategies or more complex applications, use projectors:

```python
from opticol.projector import OptimizedCollectionProjector

# Create a projector with custom size range
projector = OptimizedCollectionProjector(min_size=0, max_size=5)

# Use it to optimize collections
optimized = projector.seq([1, 2, 3, 4, 5])
```

You can also create custom projectors by subclassing `Projector`. `PassThroughProjector` is a `Projector` implementation in the library that returns the argument as-is:

```python
from opticol.projector import PassThroughProjector
from collections.abc import Sequence

class SelectiveProjector(PassThroughProjector):
    """Only optimize sequences, pass through everything else."""

    def seq(self, seq):
        # Your custom optimization logic
        return optimized_version(seq)
```

Projectors are intended to be pluggable DI components which allow for flexible and dynamic policies. Rather than relying on the convenience methods, logic which can benefit from the optimizations can consume a Projector which could be anything from a `PassThroughProjector` (and falls back to Python defaults) to a custom policy which uses domain specific knowledge to improve memory consumption.

## Architecture

Opticol has a three-layer architecture:

1. **Factory Layer** (`opticol.factory`): Generates optimized collection classes of arbitrary sizes using metaclasses and `__slots__`
2. **Projector Layer** (`opticol.projector`): The main consumer API which acts as a pluggable policy pattern for different optimization strategies
3. **Convenience Layer** (`opticol`): Simple functions backed by a default projector instance

This design allows you to use opticol in two ways:
- **Quick start**: Use the convenience functions at the module level for immediate optimization with sensible defaults
- **Advanced**: Create custom projectors to fine-tune optimization behavior for your use case


## Details

### Immutable Collections

Immutable collections (Sequence, Set, Mapping) are optimized for exact sizes. Each element is stored in a dedicated slot:

```python
s = opticol.seq([1, 2])
# Internally: _item0 = 1, _item1 = 2, which is smaller than list([1, 2])
```

### Mutable Collections

Mutable collections support overflow to standard types when exceeding capacity:

```python
m = opticol.mut_seq([1, 2])  # Optimized, uses two slots to start
m.append(3)                  # Overflowed to use standard list internally
m.append(4)                  # Still uses standard list internally
m.pop()                      # Stays as list (no downgrade)
m.pop()                      # Reverts back to optimized storage
```

### Optimization Propagation

Some collection operations return new instances such as slicing or set intersection or union operations. The convenience layer at the module level will propgate the optimization structure by default as if it were passed through the original optimization function.

```python
seq = opticol.seq([1, 2, 3])
seq = seq[1:2]  # Has only one slot internally and technically an instance of a different class.

mut_seq = opticol.mut_seq([1, 2, 3])
mut_seq.extend([4, 5])  # Beyond optimization and overflowed into list internally
sub1 = mut_seq[3:4]  # Optimized instance with one slot.
sub2 = mut_seq[:]    # A simple list because the length is beyond the optimization point

mut_set = opticol.set({1, 2, 3})
bigger_set = mut_set | {4, 5, 6}  # Default python set
smaller_set = mut_set & {2, 3}    # Optimized python set for 2 elements
```

This decision was made so that optimizations are kept as much as possible. The alternative of always providing the python built-in is possible by creating a custom Projector, and may provide slightly better results for runtime and performance in specific applications.

## Memory Savings

Below is a table which outlines the memory consumption differences per collection instance. As can be seen, sequence types benefit the least, while mapping, and set types benefit the most. The threshold whereby the savings for each collection type is no longer valuable is quite different and different applications may find different thresholds than those assumed by the convenience functions.

|Collection Type|Length|Default (b)|Optimized (b)|Savings %|
|---------------|------|-----------|-------------|---------|
|List           |0     |56         |32           |43       |
|               |1     |64         |40           |38       |
|               |2     |72         |48           |33       |
|               |3     |88         |56           |30       |
|Dict           |0     |64         |32           |50       |
|               |1     |224        |40           |82       |
|               |2     |224        |48           |79       |
|               |3     |224        |56           |75       |
|Set            |0     |216        |32           |85       |
|               |1     |216        |40           |81       |
|               |2     |216        |48           |78       |
|               |3     |216        |56           |74       |