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

Install Python and Pip, following the relevant guides for your operating system, then:

```
pip install setuptools
sudo python setup.py install
```

## Debian Packaging

Debian packaging files are provided for internal BBC R&D use.
These packages depend on packages only available from BBC R&D internal mirrors, and will not build in other environments. For use outside the BBC please use python installation method.

## Time

This library contains the Timestamp class, which may be used to get the current TAI time. The system will provide the time in UTC. As TAI does not account for leap seconds it maintains an offset from UTC that changes every time a leap second occurs[1][1]. The class contains a table of leap seconds, which is up to date as of the end of 2017. Users of this library should ensure this table is up to date by checking with (the IERS)[https://www.iers.org] who are responsible for the scheduling of leap seconds and publish decisions in their Bulletin C.

[1]: https://www.timeanddate.com/time/international-atomic-time.html

## Interaction with ipppython

When this library is used on a system where the BBC R&D internal ipppython is installed the following libraries will automatically revert to using their ipppython equivalents to ensure correct behaviour in house. These are:

* logger.py
  Uses ipppython IppLogger class instead so that underlying C logging libraries are still used in order to maintain a single log file for all of IP Studio.
* ptptime.py
  This class has been deprecated in nmos-common - timestamp should be used instead
* timestamp.py
  The Timestamp.get_time method will use ipppython if it is available to try and derive a accurate time from a PTP clock if available. If not it falls back to using the system time in pure Python which will be less accurate in most cases.
