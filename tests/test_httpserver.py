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

import unittest
import mock
from nmoscommon.httpserver import *
from nmoscommon.webapi import *
import traceback

from socket import error as socket_error

class TestExitLoop (Exception):
    pass

class TestHttpServer(unittest.TestCase):

    def test_init_sets_default_params(self):
        api_class = mock.MagicMock()
        api_instance = api_class.return_value
        UUT = HttpServer(api_class)

        self.assertEqual(UUT.api_args, [])
        self.assertEqual(UUT.api_kwargs, {})
        self.assertEqual(UUT.port, 0)
        self.assertEqual(UUT.host, '0.0.0.0')
        self.assertIsNone(UUT.ssl)

    def assert_run_operates(self,
                            host="0.0.0.0",
                            ports=[12345,],
                            port_errors=[],
                            send_port_at_start=False,
                            ssl=None,
                            api_class=None,
                            expect_failure=None):
        if api_class is None:
            api_class = mock.MagicMock()
        api_instance = api_class.return_value
        api_args   = [ mock.MagicMock(), ]
        api_kwargs = { "dummyparam" : mock.MagicMock() }
        initial_port = 0
        if send_port_at_start:
            initial_port = ports[0]

        UUT = HttpServer(api_class, host=host, port=initial_port, api_args=api_args, api_kwargs=api_kwargs, ssl=ssl)

        n_failures = 0
        unknown_socket_exception_expected = None
        if not send_port_at_start:
            for e in port_errors:
                if e.errno == 48:
                    n_failures += 1
                else:
                    unknown_socket_exception_expected = e
                    break

        if expect_failure is None:
            expect_failure = unknown_socket_exception_expected

        with mock.patch('nmoscommon.httpserver.WSGIServer') as WSGIServer:
            with mock.patch('socket.socket') as socket:
                def raise_port_errors(_port_errors):
                    error_list = [ e for e in _port_errors ]
                    def __inner(addr, *args, **kwargs):
                        if len(error_list) > 0:
                            raise error_list.pop(0)
                        else:
                            return WSGIServer.return_value
                    return __inner
                WSGIServer.side_effect = raise_port_errors(port_errors)
                def return_addrs(_ports):
                    portlist = [ p for p in _ports ]
                    def __inner():
                        if len(portlist) > 0:
                            return [ "localhost", portlist.pop(0) ]
                        else:
                            return [ "localhost", 0 ]
                    return __inner
                socket.return_value.getsockname.side_effect = return_addrs(ports)
                WSGIServer.return_value.serve_forever.side_effect = TestExitLoop

                raised = False

                try:
                    UUT.run()
                except:
                    self.fail(msg="run raised unexpected exception: %s" % (traceback.format_exc(),))

                if isinstance(UUT.failed, TestExitLoop):
                    if ports[0] == 0:
                        self.fail(msg="run didn't bail early when no port found")
                if isinstance(UUT.failed, socket_error):
                    if unknown_socket_exception_expected or (send_port_at_start and len(port_errors) > 0):
                        # It *should* fail in this case
                        raised = True
                    else:
                        self.fail(msg="run raised unexpected exception: %s" % (repr(UUT.failed),))

                if expect_failure:
                    self.assertEqual(UUT.failed, expect_failure)

                api_class.assert_called_once_with(*api_args, **api_kwargs)

                if send_port_at_start:
                    socket.return_value.getsockname.assert_not_called()
                    self.assertEqual(UUT.port, ports[0])
                else:
                    self.assertEqual(UUT.port, ports[n_failures])

                if UUT.port == 0:
                    # This means the code bailed early because no port could be found
                    WSGIServer.assert_not_called()
                else:
                    if ssl is not None:
                        expected_wsgiserver_calls = [ mock.call((host, ports[i]), api_instance.app, handler_class=WebSocketHandler, **ssl) for i in range(0,n_failures + 1) ]
                    else:
                        expected_wsgiserver_calls = [ mock.call((host, ports[i]), api_instance.app, handler_class=WebSocketHandler) for i in range(0,n_failures + 1) ]
                    self.assertListEqual([ call for call in WSGIServer.mock_calls if call[0] == '' ],
                                         expected_wsgiserver_calls)

                    if not raised and unknown_socket_exception_expected is None:
                        WSGIServer.return_value.start.assert_called_once_with()
                        self.assertTrue(UUT.started.is_set())
                        WSGIServer.return_value.serve_forever.assert_called_once_with()

                        UUT.stop()
                        api_instance.stop.assert_called_once_with()


    def test_run_starts_webserver(self):
        self.assert_run_operates()

    def test_run_starts_ssl_webserver(self):
        self.assert_run_operates(ssl={'dummykey' : 'dummyval'})

    def test_run_takes_port_from_parameters(self):
        self.assert_run_operates(send_port_at_start=True)

    def test_run_bails_when_port_is_still_zero(self):
        self.assert_run_operates(ports=[0,])

    def test_run_reruns_when_first_port_taken(self):
        e = socket_error()
        e.errno = 48
        self.assert_run_operates(ports=[12345,12346], port_errors=[e,])

    def test_run_fails_when_specified_port_taken(self):
        e = socket_error()
        e.errno = 48
        self.assert_run_operates(ports=[12345,12346], send_port_at_start=True, port_errors=[e,])

    def test_run_fails_on_unknown_errno_from_socket(self):
        e = socket_error()
        e.errno = 49
        self.assert_run_operates(ports=[12345,12346], port_errors=[e,])

    def test_run_fails_on_exception_from_api_class(self):
        e = Exception("Test Exception")
        def raise_test_exception(*args, **kwargs):
            raise e
        api_class = mock.MagicMock(side_effect=raise_test_exception)
        self.assert_run_operates(api_class=api_class, expect_failure=e, ports=[0,])
