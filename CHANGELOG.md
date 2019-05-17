# NMOS Common Library Changelog

## 0.19.0
- Add filters to mdnsbridge client for API versions and protocols
- Filter by api_ver and api_proto when selecting a Registration API

## 0.18.2
- Make wsaccel a recommended debian dependency when using python 2

## 0.18.1
- Removed wsaccel dependency when python version >= 3.6

## 0.18.0
- Addition of NMOS Auth Security files for resource endpoint protection. Changed error handler output for authlib errors

## 0.17.2
- Pin Werkzeug < 0.15 (along with >= 0.9.4) to avoid change to ProxyFix middleware incompatible with Debian version.

## 0.17.1
- Change variable naming and code layout for readability

## 0.17.0
- Fix heartbeat frequency. Requires use of 'stop' method in MDNSUpdater

## 0.16.0
- Add basic mechanism to discover current Registration API

## 0.15.0
- Add config option to allow selection of discover mechanism

## 0.14.1
- Fix bug in mDNS Listener causing KeyError on service removal

## 0.14.0
- Add config option to prefer hostnames to IP addresses

## 0.13.2
- Fix bug in IPC methods for managing clocks

## 0.13.1
- Handle case where mdns callback does not include hostname

## 0.13.0
- Add hostnames to mdns callback

## 0.12.0
- Expose parameter for modifying websocket SSL behaviour

## 0.11.2
- Require a version of `oauthlib` compatible with `flask-oauthlib` ([#75](https://github.com/bbc/nmos-common/issues/75))

## 0.11.1
- Modify construction of Depends lines in stdeb

## 0.11.0
- Add capability to set a custom domain for unicast DNS-SD

## 0.10.0
- Add Authlib dependency and error-handling. 'Authorization' added to CORS headers.

## 0.9.6
- Use NMOS JSON serialiser in webapi to serialise media-specific API responses

## 0.9.5
- Re-introduces helper functions in webapi for MIME type matching/selection

## 0.9.4
- Bugfix to prevent un-handled errors in unicast DNS dicovery when no PTR record is present

## 0.9.3
- Update import for internal logging library

## 0.9.2
- Correctly retry query API lookup on HTTP error

## 0.9.1
- Handle uncaught mDNS exceptions and manage double calls to start mDNSEngine

## 0.9.0
- Prefer new nmos-register mDNS type, with fallback to nmos-registration

## 0.8.0
- Switch to using Zeroconf for mDNS resolution and Python-DNS for unicast DNS discovery.

## 0.7.3
- Define config defaults in nmoscommonconfig

## 0.7.2
- Check http/https mode when retrieving mDNS bridge results

## 0.7.1
- Deep copy objects when registered using the Facade class

## 0.7.0
- Add mechanism to register clocks with the Node API via Facade class

## 0.6.9
- Resolve mismatch with schemas for webapi error responses

## 0.6.8
- Resolve issue where interactions of aggregator.py with Registration API
  failed to set Content-Type

## 0.6.7
- Updated stdeb.cfg to include dependencies on mediajson and mediatimestamp

## 0.6.6
- Moved json sublibrary out to mediajson and referenced it
  here for backwards compatibility.

## 0.6.5
- Added imports of some constants from mediatimestamp. These should
  not really be used, but some implementations erroneously rely on them

## 0.6.4
- Moved timestamp sublibrary out to mediatimestamp and referenced it
  here for backwards compatibility.

## 0.6.0
- Support for configuring logging

## 0.5.1
- Use cython acceleration for gevent-websocket

## 0.5.0
- Support for python3 in ipc

## 0.4.6
- BUGFIX: Handling of negative timeoffsets with 0 secs

## 0.4.5
- Relaxed dependancy version restrictions

## 0.4.4
- Switched to tox for testing

## 0.4.3
- Added hash implementation to TimeOffset

## 0.4.2
- Corrected timestamp.py tests to ensure that they work on systems with ipputils installed.

## 0.4.1
- Added py2dsc fix for python-websocket package name

## 0.4.0:
- Added py2dsc debian packaging

## 0.3.0:
- Added `fix_proxy` option to honour X-Fowarded-Proto in redirects.

## 0.2.1:
- Fixed dependency requirements in setup.py to specify a minimum version not an exact version.
