from ._about import __author__, __email__, __version__  # noqa
from ._parse import ParseError
from ._version import Version

__all__ = ('Version', 'ParseError')

from ._helpers import fixup_module_metadata

fixup_module_metadata(__name__, globals())
del fixup_module_metadata
