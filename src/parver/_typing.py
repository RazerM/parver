from typing import Union

from typing_extensions import Literal

PreTag = Union[
    Literal["c"],
    Literal["rc"],
    Literal["alpha"],
    Literal["a"],
    Literal["beta"],
    Literal["b"],
    Literal["preview"],
    Literal["pre"],
]
NormalizedPreTag = Union[Literal["a"], Literal["b"], Literal["rc"]]

Separator = Union[Literal["."], Literal["-"], Literal["_"]]

PostTag = Union[Literal["post"], Literal["rev"], Literal["r"]]
