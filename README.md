## Opticol

Optimized collections (hence *opticol*) for Python. This package provides memory optimized versions of the base Python collection types which are:

* (Mutable)Sequence
* (Mutable)Mapping
* (Mutable)Set

The insight behind the package is the following: the size of an empty set is 216 bytes (on Python 3.14) but the size of an empty object with an empty __slots__ member is only 32 bytes. Python programs that hold large datasets in memory could benefit from using these optimized collections which fully implement the respective collection ABCs, but at a fraction of the runtime memory.

So for general users these optimizations will not be worth if if the dataset being used comfortably fits in memory, but applications which currently create tens or hundreds of thousand of Python objects could dramatically lower memory usage without API changes.

## Usage

The optimized classes could be used directly, by creating an EmptySequence directly for example, but the recommended usage is to use the collection level `project` method which tries to project a collection instance into the memory optimized variants automatically. Additionally, there is a factory interface that could be plugged in to allow for different strategies beyond the typical `project` logic.

Consider the following example:

```
import opticol

optimized_list = opticol.seq_project([]) # Actually an instance of EmptySequence
optimized_list_single = opticol.mut_seq_project(("MyString",)) # Actually an instance of Small1MutableSequence
```

A small note that in the current implementation, optimization is only in one direction. That is, if the MutableSequence type is optimized for collections of size 0, 1, 2, 3, then once an operation pushes it past into size 4, further decreasing of the size will not restore the optimization.