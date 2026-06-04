# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import os
from importlib.metadata import distribution
from pathlib import Path

os.environ["PARVER_SPHINX_BUILD"] = "1"
PROJECT_ROOT_DIR = Path(__file__).parents[1].resolve()

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "parver"
copyright = "2018, Frazer McLean"
author = "Frazer McLean"
release = distribution("parver").version


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinxcontrib.towncrier.ext",
    "sphinx_inline_tabs",
    "sphinx_autodoc_typehints",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
pygments_style = "tango"


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_title = f"parver documentation v{release}"
html_static_path = []


# -- Extension configuration -------------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_typehints_description_target = "documented"

towncrier_draft_autoversion_mode = "draft"
towncrier_draft_include_empty = False
towncrier_draft_working_directory = PROJECT_ROOT_DIR


def typehints_formatter(annotation, config):
    from parver._helpers import UnsetType

    if annotation is UnsetType:
        return "``UNSET``"
    return None
