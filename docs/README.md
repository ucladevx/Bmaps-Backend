# Mappening-Backend Documentation

## Generating Documentation with Sphinx
- Make sure required packages are installed
  - If you have pip installed:
    - `make setup` or `make sudo-setup`
  - If this fails sorry
- Read Sphinx help information
  - `make sphinx-help`
- Generate Sphinx documentation
  - `make html`
  - TODO: Check this with Hannah. `make clean`?? 
- Set up Sphinx Autobuild
  - `sphinx-autobuild . ./_build/html` from Mappening-Backend
  - Navigate to `http://127.0.0.1:8000/`
  - `CTRL-C` to stop autobuilding
- Latest documentation is in the `_build` folder
- Minified js/css files in `_static`
- Manual Changes with [reST](http://www.sphinx-doc.org/en/stable/rest.html):
  - Manually changed "Classes" to "APIs" in `index.html`
  - Removed div.body max and min width in `basic.css`
  - Added min-width to .field-name in `basic.css`
