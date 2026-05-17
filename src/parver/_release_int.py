from __future__ import annotations

import sys
from math import floor, log10
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self


def intwidth(value: int | str) -> int:
    if isinstance(value, int):
        if value == 0:
            return 1
        return floor(log10(abs(value))) + 1
    else:
        return len(value.strip().lstrip("-+").replace("_", ""))


class ReleaseInt(int):
    _minimum_width: int

    def __new__(cls, value: int | str, *, width: int | None = None) -> Self:
        if width is not None:
            if isinstance(width, bool) or not isinstance(width, int):
                msg = "width must be an integer"
                raise TypeError(msg)
            if width < 1:
                msg = "width must be positive"
                raise ValueError(msg)

        if isinstance(value, str):
            parsed_value = int(value)
            obj = super().__new__(cls, parsed_value)
            obj._minimum_width = intwidth(value) if width is None else width
        elif isinstance(value, ReleaseInt):
            obj = super().__new__(cls, value)
            obj._minimum_width = value._minimum_width if width is None else width
        elif isinstance(value, int):
            obj = super().__new__(cls, value)
            obj._minimum_width = 1 if width is None else width
        else:
            msg = f"Unsupported type: {type(value)}"
            raise TypeError(msg)
        return obj

    @property
    def minimum_width(self) -> int:
        return self._minimum_width

    def zero_like(self) -> ReleaseInt:
        """Return a zero with the same width preference as this number."""
        return ReleaseInt(0, width=self.minimum_width)

    def __add__(self, other: object) -> ReleaseInt:
        if isinstance(other, int):
            result = int(self) + int(other)
            return ReleaseInt(result, width=self.minimum_width)
        return NotImplemented

    def __radd__(self, other: object) -> ReleaseInt:
        return self.__add__(other)

    def __sub__(self, other: object) -> ReleaseInt:
        if isinstance(other, int):
            result = int(self) - int(other)
            return ReleaseInt(result, width=self.minimum_width)
        return NotImplemented

    def __str__(self) -> str:
        value = int(self)
        if value < 0:
            return "-" + str(abs(value)).zfill(self.minimum_width)
        return str(value).zfill(self.minimum_width)

    def __repr__(self) -> str:
        if self._minimum_width <= intwidth(self):
            return int.__repr__(self)
        return f"ReleaseInt('{self}')"
