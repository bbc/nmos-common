# NMOS Common Library Changelog

## 0.10.0
- Add Authlib dependency and error-handling. 'Authorization' added to CORS headers.

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
