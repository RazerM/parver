# coding: utf-8
from __future__ import absolute_import, division, print_function

from ._version import Version
from ._parse import ParseError

__all__ = ('Version', 'ParseError')

from ._helpers import fixup_module_metadata
fixup_module_metadata(__name__, globals())
del fixup_module_metadata
