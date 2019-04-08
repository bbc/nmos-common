# Copyright 2017 British Broadcasting Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import print_function
import zmq.green as zmq
import uuid
import os
import os.path
import gevent
import traceback
import json
import stat
import warnings


class RemoteException(Exception):
    pass


class LocalException(Exception):
    pass


# Included for backward compatibility with previous typo'ed version
RemoteExcepton = RemoteException


class Host(object):
    """This class provides a server which can make a set of ipc commands available at a well known address.
    It provides a decorator, @ipcmethod which is used to decorate methods that are to be callable remotely.

    The server itself should be started with start and stopped with stop when no longer needed, though exiting
    the main application thread will also shut it down, this is not clean and not recommended."""
    def __init__(self, address, timeout=100):
        self.address = address
        ctx = zmq.Context.instance()

        self.timeout = timeout

        self.socket = ctx.socket(zmq.REP)
        self.socket.bind(self.address)
        self.socket.setsockopt(zmq.LINGER, 0)

        if address[:6] == "ipc://":
            os.chmod(address[6:], (stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR |
                                   stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP |
                                   stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH))

        self.thread = None
        self._stop = True

        self.methods = {}

        self.methods['getmethods'] = self.getmethods
        self.greenlet = None

    def start(self):
        if self._stop:
            self._stop = False
            self.greenlet = gevent.spawn(self._run)

    def stop(self):
        self._stop = True
        if self.greenlet is not None:
            self.greenlet.kill()
        self.greenlet = None
        if not self.socket.closed:
            self.socket.close()

    def _run(self):
        while not self._stop:
            r = self.socket.poll(timeout=self.timeout)
            if r != 0:
                msg = self.socket.recv_json()
                if ('function' not in msg or 'args' not in msg or 'kwargs' not in msg):
                    self.socket.send_json({})
                    continue

                if msg['function'] not in self.methods:
                    self.socket.send_json({'exc': 'AttributeError'})
                    continue

                try:
                    r = self.methods[msg['function']](*(msg['args']), **(msg['kwargs']))
                except Exception:
                    self.socket.send_json({'exc': traceback.format_exc()})
                    continue
                if r is not None:
                    self.socket.send_json({'ret': r})
                else:
                    self.socket.send_json({})

    def ipcmethod(self, name=None):
        def _inner(function):
            _name = name
            if _name is None:
                _name = function.__name__
            self.methods[_name] = function
            return function
        return _inner

    def getmethods(self):
        """Return a list of all methods available and their help text"""
        return dict(
            ((key, self.methods[key].__doc__ if self.methods[key].__doc__ is not None else "") for key in self.methods.keys())
        )


class Proxy(object):
    """This class provides a proxy to a remote ipc host which can be used to invoke methods on that host."""
    def __init__(self, address, timeout=100):
        self.address = address
        ctx = zmq.Context.instance()

        self.timeout = timeout

        if address[:6] == "ipc://":
            if not os.path.exists(address[6:]):
                raise RuntimeError

        self.socket = ctx.socket(zmq.REQ)
        self.socket.connect(self.address)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.setsockopt(zmq.SNDTIMEO, 0)
        self.socket.setsockopt(zmq.RCVTIMEO, 0)

    def invoke_named(self, name, *args, **kwargs):
        try:
            msg = {'function': name,
                   'args': args,
                   'kwargs': kwargs}
            gevent.sleep(0)
            self.socket.send_json(msg)
            gevent.sleep(0)

            if self.socket.poll(timeout=self.timeout) == 0:
                self.close()
                raise LocalException("Unconnected Socket")

            r = self.socket.recv_json()
            gevent.sleep(0)
            if 'exc' in r:
                raise RemoteException(r['exc'])
            if 'ret' in r:
                return r['ret']
        except Exception:
            gevent.sleep(0)
            raise

    def close(self):
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
            self.socket = None

    def __getattr__(self, name):
        def _invoke(*args, **kwargs):
            return self.invoke_named(name, *args, **kwargs)
        return _invoke


# This is deprecated
class Socket(object):  # pragma: no cover
    def __init__(self, name=None, rmethods=None):
        warnings.warn("The Socket Class is Deprecated and will be removed in future", DeprecationWarning, stacklevel=1)
        if rmethods is None:
            rmethods = []
        if name is None:
            name = '/tmp/nmoscommon_ipc_' + str(uuid.uuid4())
            self.side = "slave"
        else:
            self.side = "master"

        self.name = name
        ctx = zmq.Context.instance()
        if self.side == "master":
            self.socket = ctx.socket(zmq.REQ)
            self.socket.connect("ipc://" + self.name)
        else:
            self.socket = ctx.socket(zmq.REP)
            self.socket.bind("ipc://" + self.name)
        self.socket.setsockopt(zmq.LINGER, 0)

        self.greenlet = None
        self._stop = True

        self.lmethods = dict()
        self.rmethods = []
        for rmethod in rmethods:
            self.remote(rmethod)

    def start(self):
        if self.side == "slave":
            if self._stop:
                self._stop = False
                self.greenlet = gevent.spawn(self._run)

    def stop(self):
        self._stop = True
        if self.greenlet is not None:
            self.greenlet.kill()
        self.greenlet = None

    def _run(self):
        while not self._stop:
            r = self.socket.poll(timeout=100)
            if r != 0:
                msg = self.socket.recv_json()
                if msg["function"] not in self.lmethods:
                    rmsg = None
                else:
                    rmsg = self.lmethods[msg["function"]](*msg["args"], **msg["kwargs"])
                self.socket.send_json({"return": rmsg})

    def request(self, function, *args, **kwargs):
        self.socket.send_json({
            "function": function,
            "args": args,
            "kwargs": kwargs})
        self.socket.poll(timeout=100)
        rmsg = self.socket.recv_json()
        if "return" in rmsg:
            return rmsg["return"]

    def local(self, f):
        self.lmethods[f.__name__] = f
        return f

    def remote(self, funcname):
        self.rmethods.append(funcname)

    def __getattr__(self, name):
        def callremote(*args, **kwargs):
            return self.request(name, *args, **kwargs)

        try:
            return super(Socket, self).__getattr__(name)
        except AttributeError:
            if name in self.rmethods:
                return callremote
            raise


def main():
    import sys
    address = "ipc:///tmp/nmoscommon_test"
    if len(sys.argv) > 1:
        address = sys.argv[1]

    if len(sys.argv) > 2:
        p = Proxy(address)
        print(json.dumps(getattr(p, sys.argv[2])(*(sys.argv[3:]))))
    else:
        h = Host(address)

        @h.ipcmethod("hello")
        def hello(name="James"):
            return "Hello, {}".format(name)
        print("Listening on {}".format(address))
        h._stop = False
        h._run()


if __name__ == "__main__":  # pragma: no cover
    main()
