from collections import deque
from collections.abc import Iterable


class UnsetType:
    def __repr__(self):
        return "UNSET"


UNSET = UnsetType()
del UnsetType


class Infinity:
    def __repr__(self):
        return "Infinity"

    def __hash__(self):
        return hash(repr(self))

    def __lt__(self, other):
        return False

    def __le__(self, other):
        return False

    def __eq__(self, other):
        return isinstance(other, self.__class__)

    def __ne__(self, other):
        return not isinstance(other, self.__class__)

    def __gt__(self, other):
        return True

    def __ge__(self, other):
        return True

    def __neg__(self):
        return NegativeInfinity


Infinity = Infinity()


class NegativeInfinity:
    def __repr__(self):
        return "-Infinity"

    def __hash__(self):
        return hash(repr(self))

    def __lt__(self, other):
        return True

    def __le__(self, other):
        return True

    def __eq__(self, other):
        return isinstance(other, self.__class__)

    def __ne__(self, other):
        return not isinstance(other, self.__class__)

    def __gt__(self, other):
        return False

    def __ge__(self, other):
        return False

    def __neg__(self):
        return Infinity


NegativeInfinity = NegativeInfinity()


def fixup_module_metadata(module_name, namespace):
    def fix_one(obj):
        mod = getattr(obj, "__module__", None)
        if mod is not None and mod.startswith("parver."):
            obj.__module__ = module_name
            if isinstance(obj, type):
                for attr_value in obj.__dict__.values():
                    fix_one(attr_value)

    for objname in namespace["__all__"]:
        obj = namespace[objname]
        fix_one(obj)


def force_tuple(n):
    if isinstance(n, str):
        raise TypeError("Expected an iterable or int.")
    if not isinstance(n, Iterable):
        return (n,)
    if not isinstance(n, tuple):
        return tuple(n)
    return n


def force_lower(s):
    # We only do this if it's a string, otherwise we let the wrong type pass
    # through and let the validator complain.
    if isinstance(s, str):
        return s.lower()
    return s


def last(iterable, *, default=UNSET):
    try:
        return deque(iterable, maxlen=1).pop()
    except IndexError:
        if default is UNSET:
            raise
        return default


IMPLICIT_ZERO = ""
