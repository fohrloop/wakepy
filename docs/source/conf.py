# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
#
# -- Project information -----------------------------------------------------

from wakepy import __version__

project = "wakepy"
copyright = "2023, Niko Föhr"
author = "Niko Föhr"

# The full version, including alpha/beta/rc tags
release = __version__


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "myst_parser",
    # TODO: Check also autodoc2
    # https://myst-parser.readthedocs.io/en/latest/syntax/code_and_apis.html#sphinx-autodoc2
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    # Sphinx Design adds some sphinx directives for UI components
    # See: https://sphinx-design.readthedocs.io/
    "sphinx_design",
    # Add copy button to code blocks
    # See: https://sphinx-copybutton.readthedocs.io/
    "sphinx_copybutton",
]

# Needed by sphinx_design
# See: https://sphinx-design.readthedocs.io/en/latest/get_started.html
myst_enable_extensions = [
    "attrs_inline",
    # Enable block attributes, like: {emphasize-lines="2,3"}
    # See: https://myst-parser.readthedocs.io/en/latest/syntax/optional.html#block-attributes
    "attrs_block",
    # Allow ::: in addition to ```
    # See: https://myst-parser.readthedocs.io/en/latest/syntax/optional.html#code-fences-using-colons
    "colon_fence",
    # Enable definition list syntax.
    # See: https://myst-parser.readthedocs.io/en/latest/syntax/optional.html#definition-lists
    "deflist",
]

# For supporting links to headers like:
# [](#auto-generated-header-anchors)
# See: https://myst-parser.readthedocs.io/en/latest/syntax/optional.html#auto-generated-header-anchors
myst_heading_anchors = 3

# Add a border around Examples. Might or might not look good, depending on the
# used theme.
# See: https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html#confval-napoleon_use_admonition_for_examples
napoleon_use_admonition_for_examples = True
napoleon_google_docstring = False

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "furo"

html_theme_options = {
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/fohrloop/wakepy",
            "html": """
                <svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"></path>
                </svg>
            """,  # noqa E501
            "class": "",
        },
    ],
}
