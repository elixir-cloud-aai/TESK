# -- Project information -----------------------------------------------------

project = "TESK"
author = "TESK contributors"

# -- General configuration ---------------------------------------------------

extensions = [
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = []

# Markdown support
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# Root document (Sphinx 2.0+)
root_doc = "index"

# Backwards compatibility for older Sphinx versions
master_doc = root_doc

# -- HTML output -------------------------------------------------------------

html_theme = "sphinx_rtd_theme"

html_static_path = ["_static"]

