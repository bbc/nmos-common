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

## Configuration

This library provides a number of configuration options which are used by its own components and by services which depend upon the library. Configuration is provided by a JSON object within the file `/etc/nmoscommon/config.json`. The following attributes may be set in the object:

*   **priority:** Overrides the default behaviour for interaction with a Registration API, causing it to prefer a particular instance **if set to a value greater than or equal to 100**. Default: 0.
*   **https_mode:** Switches the library between HTTP and HTTPS operation. "disabled" indicates HTTP mode is in use, "enabled" indicates HTTPS mode is in use. Default: "disabled".
*   **prefer_ipv6:** A boolean parameter to switch the libary into IPv6 mode. Default: false.
*   **prefer_hostnames:** A boolean parameter to cause hostnames to be surfaced via APIs rather than IP addresses, and to cause any HTTP requests to use hostnames rather than IP addresses where possible. This is important when operating in HTTPS mode. Default: false.
*   **node_hostname:** Overrides the default fully qualified DNS name for the system. Default: null.
*   **fix_proxy:** Corrects the appearance of URLs and links (including some headers) returned by APIs when operating behind a reverse proxy. Default: "disabled".
*   **logging.level:** Sets the log level to one of "DEBUG", "INFO", "WARN", "ERROR" or "FATAL". Default: "DEBUG".
*   **logging.fileLocation:** The path to write the log file to. Default: "/var/log/nmos.log".
*   **logging.output:** An array of locations to write log messages to, which may include "file" and "stdout". Default: \["file", "stdout"\].
*   **nodefacade.NODE_REGVERSION:** Which Registration API version to look for when performing registrations from a Node API. Default: "v1.2".
*   **oauth_mode:** Boolean indicating whether use of JSON Web Tokens and OAuth authorisation is expected. Default: false.
*   **dns_discover:** A boolean parameter indicating whether browsing of DNS-SD via unicast DNS is enabled. Default: true.
*   **mdns_discover:** A boolean parameter indicating whether browsing of DNS-SD via multicast DNS is enabled. Default: true.
*   **interfaces:** An array containing network interfaces, via which mDNS announcements and browsing should be performed. Default: Not present (uses the default gateway interface).

An example configuration file is shown below:

```json
{
  "priority": 0,
  "https_mode": "disabled",
  "prefer_ipv6": false,
  "prefer_hostnames": false,
  "node_hostname": null,
  "fix_proxy": "disabled",
  "logging": {
    "level": "DEBUG",
    "fileLocation": "/var/log/nmos.log",
    "output": [
      "file",
      "stdout"
    ]
  },
  "nodefacade": {
    "NODE_REGVERSION": "v1.2"
  },
  "oauth_mode": false,
  "dns_discover": true,
  "mdns_discover": false,
  "interfaces": ["ens1f0", "eno1"]
}
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

*   json.py: Now provided by 'mediajson'
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
