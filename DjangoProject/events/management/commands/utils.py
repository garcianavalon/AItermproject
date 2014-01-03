"""Provide some widely useful utilities. Safe for "from utils import *".

"""

from __future__ import generators
import operator, math, random, copy, sys, os.path, bisect

#______________________________________________________________________________
# Compatibility with Python 2.2 and 2.3

# The AIMA code is designed to run in Python 2.2 and up (at some point,
# support for 2.2 may go away; 2.2 was released in 2001, and so is over
# 3 years old). The first part of this file brings you up to 2.4
# compatibility if you are running in Python 2.2 or 2.3:

try: bool, True, False ## Introduced in 2.3
except NameError:
    class bool(int):
        "Simple implementation of Booleans, as in PEP 285"
        def __init__(self, val): self.val = val
        def __int__(self): return self.val
        def __repr__(self): return ('False', 'True')[self.val]

    True, False = bool(1), bool(0)

try: sum ## Introduced in 2.3
except NameError:
    def sum(seq, start=0):
        """Sum the elements of seq.
        >>> sum([1, 2, 3])
        6
        """
        return reduce(operator.add, seq, start)

try: enumerate  ## Introduced in 2.3
except NameError:
    def enumerate(collection):
        """Return an iterator that enumerates pairs of (i, c[i]). PEP 279.
        >>> list(enumerate('abc'))
        [(0, 'a'), (1, 'b'), (2, 'c')]
        """
        ## Copied from PEP 279
        i = 0
        it = iter(collection)
        while 1:
            yield (i, it.next())
            i += 1


try: reversed ## Introduced in 2.4
except NameError:
    def reversed(seq):
        """Iterate over x in reverse order.
        >>> list(reversed([1,2,3]))
        [3, 2, 1]
        """
        if hasattr(seq, 'keys'):
            raise ValueError("mappings do not support reverse iteration")
        i = len(seq)
        while i > 0:
            i -= 1
            yield seq[i]


try: sorted ## Introduced in 2.4
except NameError:
    def sorted(seq, cmp=None, key=None, reverse=False):
        """Copy seq and sort and return it.
        >>> sorted([3, 1, 2])
        [1, 2, 3]
        """
        seq2 = copy.copy(seq)
        if key:
            if cmp == None:
                cmp = __builtins__.cmp
            seq2.sort(lambda x,y: cmp(key(x), key(y)))
        else:
            if cmp == None:
                seq2.sort()
            else:
                seq2.sort(cmp)
        if reverse:
            seq2.reverse()
        return seq2

try:
    set, frozenset ## set builtin introduced in 2.4
except NameError:
    try:
        import sets ## sets module introduced in 2.3
        set, frozenset = sets.Set, sets.ImmutableSet
    except (NameError, ImportError):
        class BaseSet:
            "set type (see http://docs.python.org/lib/types-set.html)"


            def __init__(self, elements=[]):
                self.dict = {}
                for e in elements:
                    self.dict[e] = 1

            def __len__(self):
                return len(self.dict)

            def __iter__(self):
                for e in self.dict:
                    yield e

            def __contains__(self, element):
                return element in self.dict

            def issubset(self, other):
                for e in self.dict.keys():
                    if e not in other:
                        return False
                return True

            def issuperset(self, other):
                for e in other:
                    if e not in self:
                        return False
                return True


            def union(self, other):
                return type(self)(list(self) + list(other))

            def intersection(self, other):
                return type(self)([e for e in self.dict if e in other])

            def difference(self, other):
                return type(self)([e for e in self.dict if e not in other])

            def symmetric_difference(self, other):
                return type(self)([e for e in self.dict if e not in other] +
                                  [e for e in other if e not in self.dict])

            def copy(self):
                return type(self)(self.dict)

            def __repr__(self):
                elements = ", ".join(map(str, self.dict))
                return "%s([%s])" % (type(self).__name__, elements)

            __le__ = issubset
            __ge__ = issuperset
            __or__ = union
            __and__ = intersection
            __sub__ = difference
            __xor__ = symmetric_difference

        class frozenset(BaseSet):
            "A frozenset is a BaseSet that has a hash value and is immutable."

            def __init__(self, elements=[]):
                BaseSet.__init__(elements)
                self.hash = 0
                for e in self:
                    self.hash |= hash(e)

            def __hash__(self):
                return self.hash

        class set(BaseSet):
            "A set is a BaseSet that does not have a hash, but is mutable."

            def update(self, other):
                for e in other:
                    self.add(e)
                return self

            def intersection_update(self, other):
                for e in self.dict.keys():
                    if e not in other:
                        self.remove(e)
                return self

            def difference_update(self, other):
                for e in self.dict.keys():
                    if e in other:
                        self.remove(e)
                return self

            def symmetric_difference_update(self, other):
                to_remove1 = [e for e in self.dict if e in other]
                to_remove2 = [e for e in other if e in self.dict]
                self.difference_update(to_remove1)
                self.difference_update(to_remove2)
                return self

            def add(self, element):
                self.dict[element] = 1

            def remove(self, element):
                del self.dict[element]

            def discard(self, element):
                if element in self.dict:
                    del self.dict[element]

            def pop(self):
                key, val = self.dict.popitem()
                return key

            def clear(self):
                self.dict.clear()

            __ior__ = update
            __iand__ = intersection_update
            __isub__ = difference_update
            __ixor__ = symmetric_difference_update




#______________________________________________________________________________
# Simple Data Structures: infinity, Dict, Struct

infinity = 1.0e400

def Dict(**entries):
    """Create a dict out of the argument=value arguments.
    >>> Dict(a=1, b=2, c=3)
    {'a': 1, 'c': 3, 'b': 2}
    """
    return entries

class DefaultDict(dict):
    """Dictionary with a default value for unknown keys."""
    def __init__(self, default):
        self.default = default

    def __getitem__(self, key):
        if key in self: return self.get(key)
        return self.setdefault(key, copy.deepcopy(self.default))

    def __copy__(self):
        copy = DefaultDict(self.default)
        copy.update(self)
        return copy

class Struct:
    """Create an instance with argument=value slots.
    This is for making a lightweight object whose class doesn't matter."""
    def __init__(self, **entries):
        self.__dict__.update(entries)

    def __cmp__(self, other):
        if isinstance(other, Struct):
            return cmp(self.__dict__, other.__dict__)
        else:
            return cmp(self.__dict__, other)

    def __repr__(self):
        args = ['%s=%s' % (k, repr(v)) for (k, v) in vars(self).items()]
        return 'Struct(%s)' % ', '.join(args)

def update(x, **entries):
    """Update a dict; or an object with slots; according to entries.
    >>> update({'a': 1}, a=10, b=20)
    {'a': 10, 'b': 20}
    >>> update(Struct(a=1), a=10, b=20)
    Struct(a=10, b=20)
    """
    if isinstance(x, dict):
        x.update(entries)
    else:
        x.__dict__.update(entries)
    return x

#______________________________________________________________________________
# Functions on Sequences (mostly inspired by Common Lisp)
# NOTE: Sequence functions (count_if, find_if, every, some) take function
# argument first (like reduce, filter, and map).

def removeall(item, seq):
    """Return a copy of seq (or string) with all occurences of item removed.
    >>> removeall(3, [1, 2, 3, 3, 2, 1, 3])
    [1, 2, 2, 1]
    >>> removeall(4, [1, 2, 3])
    [1, 2, 3]
    """
    if isinstance(seq, str):
      return seq.replace(item, '')
    else:
      return [x for x in seq if x != item]

def unique(seq):
    """Remove duplicate elements from seq. Assumes hashable elements.
    >>> unique([1, 2, 3, 2, 1])
    [1, 2, 3]
    """
    return list(set(seq))

def product(numbers):
    """Return the product of the numbers.
    >>> product([1,2,3,4])
    24
    """
    return reduce(operator.mul, numbers, 1)

def count_if(predicate, seq):
    """Count the number of elements of seq for which the predicate is true.
    >>> count_if(callable, [42, None, max, min])
    2
    """
    f = lambda count, x: count + (not not predicate(x))
    return reduce(f, seq, 0)

def find_if(predicate, seq):
    """If there is an element of seq that satisfies predicate; return it.
    >>> find_if(callable, [3, min, max])
    <built-in function min>
    >>> find_if(callable, [1, 2, 3])
    """
    for x in seq:
        if predicate(x): return x
    return None

def every(predicate, seq):
    """True if every element of seq satisfies predicate.
    >>> every(callable, [min, max])
    1
    >>> every(callable, [min, 3])
    0
    """
    for x in seq:
        if not predicate(x): return False
    return True

def some(predicate, seq):
    """If some element x of seq satisfies predicate(x), return predicate(x).
    >>> some(callable, [min, 3])
    1
    >>> some(callable, [2, 3])
    0
    """
    for x in seq:
        px = predicate(x)
        if  px: return px
    return False

def isin(elt, seq):
    """Like (elt in seq), but compares with is, not ==.
    >>> e = []; isin(e, [1, e, 3])
    True
    >>> isin(e, [1, [], 3])
    False
    """
    for x in seq:
        if elt is x: return True
    return False

#______________________________________________________________________________
