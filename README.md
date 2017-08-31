# NMOS Common Library Components

Common Python library for BBC reference implementations of NMOS APIs.

This package includes:
* agregator.py
* facade.py
* flask_cors.py
* httpserver.py
* ipc.py
* logger.py
* mdnsbridge.py
* nmoscommonconfig.py
* ptptime.py
* query.py
* timestamp.py
* utils.py
* webapi.py
* zmqserver.py

## Installing with Python

Install Python and Pip, following the relevent guides for your operating system, then:

```
pip install setuptools
sudo python setup.py install
```

## Debian Packaging

Debian packaging files are provided for internal BBC R&D use.
These packages depend on packages only available from BBC R&D internal mirrors, and will not build in other environments. For use outside the BBC please use python installation method.
