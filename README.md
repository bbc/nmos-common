# NMOS Common Library Components

Common Python library for BBC reference implementations of NMOS APIs.

## Introduction

This library provides common components required by NMOS API implementations. Additionally, it provides SDK components for interacting with the nmos-node, nmos-registration and nmos-query implementations.

## Installation

### Requirements

*   Linux (untested on Windows and Mac)
*   Python 2.7 or 3.3+
*   Python Pip

### Steps

```bash
# Install Python setuptools
$ pip install setuptools

# Install the library
$ sudo python setup.py install
```

## Usage

The following code snippet demonstrates registering a service and its resources with the Node API.

```python
from nmoscommon.facade import Facade

# Initialise service name to use for Node API interactions
nodeapi = Facade("myservice/v1.0")

# Register the service with the Node API including its own API endpoint
nodeapi.register_service("http://127.0.0.1", "myservice/v1.0")

# Heartbeat with the Node API - You'll need to call this every 5 seconds from another thread
nodeapi.heartbeat_service()

# Register your resources with the Node API
nodeapi.addResource("device", "my-device-uuid", "my-device-json-here")
```

## Documentation

### Time

This library contains the Timestamp class, which may be used to get the current TAI time. The system will provide the time in UTC. As TAI does not account for leap seconds it maintains an offset from UTC that changes every time a leap second occurs[1][1]. The class contains a table of leap seconds, which is up to date as of the end of 2017. Users of this library should ensure this table is up to date by checking with [the IERS](https://www.iers.org) who are responsible for the scheduling of leap seconds and publish decisions in their Bulletin C.

[1]: https://www.timeanddate.com/time/international-atomic-time.html

### Interaction with ipppython

When this library is used on a system where the BBC R&amp;D internal ipppython is installed the following libraries will automatically revert to using their ipppython equivalents to ensure correct behaviour in house. These are:

*   logger.py
    Uses ipppython IppLogger class instead so that underlying C logging libraries are still used in order to maintain a single log file for all of IP Studio.
*   ptptime.py
    This class has been deprecated in nmos-common - timestamp should be used instead
*   timestamp.py
    The Timestamp.get_time method will use ipppython if it is available to try and derive a accurate time from a PTP clock if available. If not it falls back to using the system time in pure Python which will be less accurate in most cases.

## Development

### Testing

```bash
# Run the tests
$ make test
```

### Packaging

```bash
# Debian packaging
$ make deb

# RPM packaging
$ make rpm
```

## Versioning

We use [Semantic Versioning](https://semver.org/) for this repository

## Changelog

See [CHANGELOG.md](CHANGELOG.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

Please ensure you have run the test suite before submitting a Pull Request, and include a version bump in line with our [Versioning](#versioning) policy.

## License

See [LICENSE.md](LICENSE.md)
