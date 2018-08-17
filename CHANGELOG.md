# NMOS Common Library Changelog

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
