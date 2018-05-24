# Mappening-Backend Documentation

## Overview
Autodocumentation through Sphinx for Mappening's APIs. Hosted on GitHub Pages at http://ucladevx.com/Mappening-Backend/

## Setting Up the Environment
- Clone this repository 
  - `git clone https://github.com/ucladevx/Mappening-Backend.git`
- Make sure required packages are installed
  - If you have pip installed:
    - `make setup` or `make sudo-setup`
    - This basically just installs packages from `requirements.txt`
      - Use Sphinx v1.7.0 to keep things uniform
  - If this fails keep debugging
- Read Sphinx help information
  - `make sphinx-help` or `make help`

## Generating Documentation with Sphinx
- `cd docs` from the main Mappening-Backend repo
- Single-time generation of documentation
  - `make html`
  - Overwrites current `_build/` folder
  - To update GitHub Pages documentation do `make docs`
- Sphinx Autobuild for continuous building of documentation
  - `sphinx-autobuild . ./_build/html` from `Mappening-Backend/docs/`
  - Navigate to `http://127.0.0.1:8000/`
  - `CTRL-C` to stop autobuilding

## Static Files
- `_static/` folder contains the minified css/js/static files for v1.7.0
  - Overwrites auto-generated static files so we don't add 30k lines of css/js
  - Manual Changes with [reST](http://www.sphinx-doc.org/en/stable/rest.html)
    - `p.first{width:50vw;word-wrap:break-word;}` in `theme.css`
