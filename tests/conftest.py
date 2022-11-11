import os

from hypothesis import Verbosity, settings

settings.register_profile("ci", max_examples=1000)
settings.register_profile("debug", verbosity=Verbosity.verbose)
settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "default"))
