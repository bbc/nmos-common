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

### Deprecated Components

The following components are deprecated and are maintained here as a compatibility interface to alternative underlying libraries. New code should make direct use of the underlying libraries as opposed to the classes and functions provided here.

*   json.py: Now provideded by 'mediajson'
*   ptptime.py: Now provided by 'mediatimestamp'
*   timestamp.py: Now provided by 'mediatimestamp'

### Time

This library makes use of the underlying 'mediatimestamp' library, which may be used to get the current TAI time. The system will provide the time in UTC. As TAI does not account for leap seconds it maintains an offset from UTC that changes every time a leap second occurs[1][1]. The library contains a table of leap seconds, which is up to date as of the end of 2017. Users of this library should ensure this table is up to date by checking with [the IERS](https://www.iers.org) who are responsible for the scheduling of leap seconds and publish decisions in their Bulletin C.

[1]: https://www.timeanddate.com/time/international-atomic-time.html

### Interaction with pyipputils

When this library is used on a system where the BBC R&amp;D internal pyipputils is installed the following libraries will automatically revert to using their pyipputils equivalents to ensure correct behaviour in house. These are:

*   logger.py
    Uses pyipputils IppLogger class instead so that underlying C logging libraries are still used in order to maintain a single log file for all of IP Studio.

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
