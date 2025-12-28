from ._version import ParseError, Version

__all__ = ("ParseError", "Version")

from ._helpers import fixup_module_metadata

fixup_module_metadata(__name__, globals())
del fixup_module_metadata
