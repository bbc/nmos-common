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

## Interaction with ipppython

When this library is used on a system where the BBC R&D internal ipppython is installed the following libraries will automatically revert to using their ipppython equivilants to ensure correct behaviour in house. These are:

* logger.py
  Uses ipppython IppLogger class instead so that underlying C logging libraries are still used in order to maintain a single log file for all of IP Studio.
* ptptime.py
  Will use ipppython to derive the time, so that time can be derived from a more precise PTP time source if present rather than using system time. Gracefully degrades to using system time converted to the TAI epoch otherwise.
* timestamp.py
  The get_time() method can only be used if ipppython is present.
