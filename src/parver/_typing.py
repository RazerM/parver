from typing import Literal, TypeAlias

PreTag: TypeAlias = Literal["c", "rc", "alpha", "a", "beta", "b", "preview", "pre"]
NormalizedPreTag: TypeAlias = Literal["a", "b", "rc"]
Separator: TypeAlias = Literal[".", "-", "_"]
PostTag: TypeAlias = Literal["post", "rev", "r"]

ImplicitZero: TypeAlias = Literal[""]
