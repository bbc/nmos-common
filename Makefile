PYTHON=`which python`
PIP=`which pip`
NOSE2=`which nose2`

DESTDIR=/
PROJECT=nmos-common
MODNAME=`python3 ./setup.py --name`
MODVERSION=`python3 ./setup.py --version`

all:
	@echo "make source  - Create source package"
	@echo "make install - Install on local system (only during development)"
	@echo "make deb     - Generate a deb package - for local testing"
	@echo "make clean   - Get rid of scratch and byte files"
	@echo "make test    - Tests are nice"

source:
	$(PYTHON) setup.py sdist $(COMPILE)

install:
	$(PYTHON) setup.py install --root $(DESTDIR) $(COMPILE)

deb: source
	py2dsc-deb --with-python2=true --with-python3=false dist/$(MODNAME)-$(MODVERSION).tar.gz
	cp deb_dist/*.deb dist

clean:
	$(PYTHON) setup.py clean || true
	dh_clean || true
	rm -rf build/ MANIFEST
	rm -rf dist/
	rm -rf deb_dist
	rm -rf .tox
	find . -name '*.pyc' -delete
	find . -name '*.py,cover' -delete

test:
	tox

.PHONY: test clean deb install source all
