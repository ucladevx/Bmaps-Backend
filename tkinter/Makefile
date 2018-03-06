# Installs pip and selenium
# TODO: reorg Makefile and add checks to see if pip/package already exists before trying to install
tkinter-setup:
	curl -O http://python-distribute.org/distribute_setup.py
	python distribute_setup.py
	curl -O https://raw.github.com/pypa/pip/master/contrib/get-pip.py
	python get-pip.py
	rm distribute_setup.py get-pip.py

	sudo pip install selenium

# Check whether locations are in UCLA or not!
ucla:
	python tkinterUCLA.py

# Check whether location data is right!
unknown:
	python tkinterLocs.py

# Check whether event has free food!
food:
	python tkinterFood.py
