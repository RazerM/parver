# coding: utf-8
from __future__ import absolute_import, division, print_function

import os

from hypothesis import settings, Verbosity

settings.register_profile('ci', max_examples=1000)
settings.register_profile('debug', verbosity=Verbosity.verbose)
settings.load_profile(os.getenv('HYPOTHESIS_PROFILE', 'default'))
