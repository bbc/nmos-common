PYTHON=`which python`
PIP=`which pip`
NOSE2=`which nose2`

DESTDIR=/
PROJECT=nmos-common
MODNAME=nmoscommon

TEST_DEPS=\
	mock \
	nose2

VENV2=virtpython2
VENV2_ACTIVATE=$(VENV2)/bin/activate
VENV2_MODULE_DIR=$(VENV2)/lib/python2.7/site-packages
VENV2_TEST_DEPS=$(addprefix $(VENV2_MODULE_DIR)/,$(TEST_DEPS))
VENV2_INSTALLED=$(VENV2_MODULE_DIR)/$(MODNAME).egg-link

VENV3=virtpython3
VENV3_ACTIVATE=$(VENV3)/bin/activate
VENV3_MODULE_DIR=$(VENV3)/lib/python3.5/site-packages
VENV3_TEST_DEPS=$(addprefix $(VENV3_MODULE_DIR)/,$(TEST_DEPS))
VENV3_INSTALLED=$(VENV3_MODULE_DIR)/$(MODNAME).egg-link

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
	$(PYTHON) setup.py clean || true
	dh_clean || true
	rm -rf build/ MANIFEST
	rm -rf $(VENV2)
	rm -rf $(VENV3)
	find . -name '*.pyc' -delete

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

.PHONY: test test2 test3 clean deb install source all
