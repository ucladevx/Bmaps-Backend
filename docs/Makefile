#######################       SPHINX DOCUMENTATION     ######################### 

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXPROJ    = Mappening
SOURCEDIR     = .
BUILDDIR      = _build

# Need pip to be installed
# TODO: test that this is all that must be installed
setup:
	pip install -r requirements.txt

sudo-setup:
	sudo pip install -r requirements.txt

# Help for sphinx usage (can also just do `make help`)
sphinx-help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  e.g. `make html`
# $(O) is meant as a shortcut for $(SPHINXOPTS).
%:
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
