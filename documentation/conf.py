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

master_doc = "index"

# -- HTML output -------------------------------------------------------------

html_theme = "sphinx_rtd_theme"

html_static_path = ["_static"]

