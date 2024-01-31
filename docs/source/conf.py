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

# For numbered figures. Sphinx feature.
# Ref: https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-numfig
# Enables {numref} role in MyST.
# Ref2: https://jupyterbook.org/en/stable/content/figures.html#numbered-references
numfig = True


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
html_theme = "sphinx_book_theme"

html_theme_options = {
    "repository_url": "https://github.com/fohrloop/wakepy",
    "use_repository_button": True,
    # Shows the landing page in the sidebar
    # See: https://sphinx-book-theme.readthedocs.io/en/stable/sections/sidebar-primary.html#add-the-home-page-to-your-table-of-contents
    "home_page_in_toc": True,
}
