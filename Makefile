PYTHON=`which python`
DESTDIR=/
PROJECT=nmos-common
MODNAME=nmoscommon

TEST_DEPS=\
	mock

VENV=virtpython
VENV_ACTIVATE=$(VENV)/bin/activate
VENV_MODULE_DIR=$(VENV)/lib/python2.7/site-packages
VENV_TEST_DEPS=$(addprefix $(VENV_MODULE_DIR)/,$(TEST_DEPS))
VENV_INSTALLED=$(VENV_MODULE_DIR)/$(MODNAME).egg-link

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

deb:
	debuild -uc -us

clean:
	$(PYTHON) setup.py clean
	dh_clean
	rm -rf build/ MANIFEST
	rm -rf $(VENV)
	find . -name '*.pyc' -delete

$(VENV):
	virtualenv $@

$(VENV_TEST_DEPS): $(VENV)
	. $(VENV_ACTIVATE); pip install $(@F)

$(VENV_INSTALLED) : $(VENV)
	. $(VENV_ACTIVATE); pip install -e .

test: $(VENV_TEST_DEPS) $(VENV_INSTALLED)
	. $(VENV_ACTIVATE); $(PYTHON) -m unittest discover -s .

.PHONY: test clean deb install source all
