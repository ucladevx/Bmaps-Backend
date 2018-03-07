# Installs pip and beautiful soup
# TODO: reorg Makefile and add checks to see if pip/package already exists before trying to install
soup-setup:
	curl -O http://python-distribute.org/distribute_setup.py
	python distribute_setup.py
	curl -O https://raw.github.com/pypa/pip/master/contrib/get-pip.py
	python get-pip.py
	rm distribute_setup.py get-pip.py

	sudo pip install BeautifulSoup4

# Scrape http://feeds.feedburner.com/uclahappenings-all-alldays aka http://happenings.ucla.edu/
happenings:
	python ./happenings/happenings.py
