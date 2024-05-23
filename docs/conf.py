"""Configuration file for the Sphinx documentation builder."""
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import datetime
import os
import sys

import tomli

sys.path.insert(0, os.path.abspath('../..'))


# -- Project information -----------------------------------------------------
def _get_project_meta():
	with open('../pyproject.toml', mode='rb') as pyproject:
		return tomli.load(pyproject)['tool']['poetry']


pkg_meta = _get_project_meta()
current_year = datetime.datetime.now().year
project = str(pkg_meta['name'])
copyright = f"{current_year}, {str(pkg_meta['authors'][0])}"
author = str(pkg_meta['authors'][0])

# The short X.Y version
version = str(pkg_meta['version'])
# The full version, including alpha/beta/rc tags
release = version

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
	'sphinx.ext.autodoc',
	'sphinx.ext.doctest',
	'sphinx.ext.todo',
	'sphinx.ext.coverage',
	'sphinx.ext.viewcode',
	'sphinx.ext.autosummary',
	# Used to write beautiful docstrings:
	'sphinx.ext.napoleon',
	# Used to include .md files:
	'm2r2',
	# Used to insert typehints into the final docs:
	'sphinx_autodoc_typehints',
	# Used to embed values from the source code into the docs:
	'added_value',
]

# Set `typing.TYPE_CHECKING` to `True`:
# https://pypi.org/project/sphinx-autodoc-typehints/
set_type_checking_flag = False
always_document_param_types = False

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:

source_suffix = ['.rst', '.md']

# The master toctree document.
master_doc = 'index'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = 'en'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path .
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'furo'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# -- Extension configuration -------------------------------------------------
napoleon_numpy_docstring = False

# -- Options for todo extension ----------------------------------------------

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True
