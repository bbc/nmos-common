PYTHON=`which python`
PIP=`which pip`
NOSE2=`which nose2`

DESTDIR=/
PROJECT=nmos-common
MODNAME=$(shell python3 ./setup.py --name)
MODVERSION=$(shell python3 ./setup.py --version)

all:
	@echo "make source  - Create source package"
	@echo "make install - Install on local system (only during development)"
	@echo "make deb     - Generate a deb package - for local testing"
	@echo "make rpm     - Generate an rpm package - for local testing"
	@echo "make wheel   - Generate a whl package - for local testing"
	@echo "make clean   - Get rid of scratch and byte files"
	@echo "make test    - Tests are nice"

source:
	$(PYTHON) setup.py sdist $(COMPILE)

rpm:
	$(PYTHON) setup.py bdist_rpm $(COMPILE)

wheel:
	$(PYTHON) setup.py bdist_wheel $(COMPILE)

install:
	$(PYTHON) setup.py install --root $(DESTDIR) $(COMPILE)

deb_dist: source
	py2dsc --with-python2=true --with-python3=true dist/$(MODNAME)-$(MODVERSION).tar.gz

deb_dist/$(MODNAME)-$(MODVERSION)/debian/pydist-overrides: debian/pydist-overrides deb_dist
	ln -s $< $@

deb_dist/$(MODNAME)-$(MODVERSION)/debian/py3dist-overrides: debian/py3dist-overrides deb_dist
	ln -s $< $@

deb: deb_dist/$(MODNAME)-$(MODVERSION)/debian/pydist-overrides deb_dist/$(MODNAME)-$(MODVERSION)/debian/py3dist-overrides
	cd deb_dist/$(MODNAME)-$(MODVERSION)/; DEB_BUILD_OPTIONS=nocheck debuild -uc -us
	cp deb_dist/*.deb dist

clean:
	$(PYTHON) setup.py clean || true
	rm -rf build/ MANIFEST
	rm -rf dist/
	rm -rf deb_dist rpm
	rm -rf .tox
	rm -rf *.egg-info
	find . -name '*.pyc' -delete
	find . -name '*.py,cover' -delete

test:
	tox

test-nocover:
	tox -e py27

nosetest:
	tox -e py27-nose-coverage -e py3-nose-coverage

nosetest-nocover:
	tox -e py27-nose -e py3-nose

.PHONY: test test-nocover nosetest nosetest-nocover clean deb install source all
