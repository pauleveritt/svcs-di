# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "svcs-di"
copyright = "2025, svcs-di contributors"
author = "svcs-di contributors"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# Add any Sphinx extension module names here, as strings
extensions = [
    "myst_parser",  # MyST Markdown support
    "sphinx.ext.autodoc",  # API documentation from docstrings
    "sphinx.ext.viewcode",  # Add links to source code
    "sphinx.ext.todo",  # Support for to do items
    "sphinx.ext.napoleon",  # Support for NumPy and Google style docstrings
    # "sphinxcontrib.mermaid",  # Mermaid diagram support - commented out, not in dependencies
]

# MyST configuration for Markdown support
myst_enable_extensions = [
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "fieldlist",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "strikethrough",
    "substitution",
    "tasklist",
]

pygments_style = "sphinx"  # or 'default', 'monokai', etc.
pygments_dark_style = "monokai"  # for dark mode (Sphinx 5.0+)

# Disable Pygments highlighting for mermaid code blocks
myst_fence_as_directive = ["mermaid"]

# Napoleon settings for docstring parsing
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "functions.md",  # Internal development notes
    "initial_spec.md",  # Internal development notes
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# Use Furo theme
html_theme = "furo"
html_title = "svcs-di"
html_static_path = ["_static"]

# Theme options
html_theme_options = {
    "light_logo": None,
    "dark_logo": None,
}

# Favicon
html_favicon = "_static/favicon.svg"


# -- Todo extension configuration --------------------------------------------

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True
