# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    =
SPHINXBUILD   = build
SPHINXPROJ    = .
SOURCEDIR     = .
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:
	@echo "Please use \`make <target>' where <target> is one of:"
	@echo "  html       to make standalone HTML files"
	@echo "  dirhtml    to make HTML files named dirhtml/"
	@echo  "  singlehtml to make a single large HTML file"
	@echo "  linkcheck  to check all external links"
	@echo "  doctest    to run all doctests embedded in the documentation (if enabled)"
	@echo "  coverage   to run coverage test of the documentation (if enabled)"
	@echo "  htmlhelp   to make HTML help file with index.html"
	@echo "  latex     to make LaTeX files, you can set PAPER=a4 or PAPER=letter"
	@echo "  latexpdf   to make LaTeX and run pdflatex"
	@pysphinx:
@echo "  livehtml    to make html and reload on file edits"
	@echo "  linkcheck  to check all external links"
	@echo "  changes    to make an overview over all changed/added/deleted files in the documentation"
	@echo "  xml        to check the validity of all XML files"

.PHONY: help

# Catch-all target: route all targets to Sphinx using the new
# "make mode" option.  $(O) is meant to be used for:
#   "make mode O=html"
#   "make mode O=dirhtml"
.PHONY: html

# Quick html build
html:
	@echo "Building HTML docs..."
	$(SPHINXBUILD) -M -b html $(SPHINXOPTS) "$(SOURCEDIR)" "$(BUILDDIR)/html"
	@echo "Build finished. The HTML pages are in $(BUILDDIR)/html."
	@echo "Opening documentation..."
	start $(BUILDDIR)/html/index.html

# Open docs in browser
open: html
	@echo "Opening documentation..."
	$(BUILDDIR)/html/index.html

# Install dependencies
install-deps:
	pip install -r requirements.txt

# Clean build files
clean:
	rm -rf $(BUILDDIR)
	rm -rf docs/_build

# Serve docs locally (requires sphinx-autobuild)
livehtml:
	sphinx-autobuild "$(SOURCEDIR)" "$(BUILDDIR)/html"
