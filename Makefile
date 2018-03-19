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

deb: source
	py2dsc-deb --with-python2=true --with-python3=false dist/$(MODNAME)-$(MODVERSION).tar.gz
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

$(VENV2):
	virtualenv -p python2 $@

$(VENV2_TEST_DEPS): $(VENV2)
	. $(VENV2_ACTIVATE); pip install $(@F)

$(VENV2_INSTALLED) : $(VENV2)
	. $(VENV2_ACTIVATE); pip install --process-dependency-links -e .

test2: $(VENV2_TEST_DEPS) $(VENV2_INSTALLED)
	. $(VENV2_ACTIVATE); $(PYTHON) -m unittest discover -s ./tests

$(VENV3):
	virtualenv -p python3 $@

$(VENV3_TEST_DEPS): $(VENV3)
	. $(VENV3_ACTIVATE); pip install $(@F)

$(VENV3_INSTALLED) : $(VENV3)
	. $(VENV3_ACTIVATE); pip install -e .

test3: $(VENV3_TEST_DEPS) $(VENV3_INSTALLED)
	. $(VENV3_ACTIVATE); $(PYTHON) -m nose2 --with-coverage --coverage-report=term --coverage-report=annotate --coverage=$(MODNAME)

test: test2

.PHONY: test clean deb install source all
