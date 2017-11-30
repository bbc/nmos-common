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
from nmoscommon.ipc import *

class TestHost(unittest.TestCase):
    def setUp(self):
        paths = ['nmoscommon.ipc.zmq',
                 'os.chmod', ]
        patchers = { name : mock.patch(name) for name in paths }
        self.mocks = { name : patcher.start() for (name, patcher) in patchers.iteritems() }
        for (name, patcher) in patchers.iteritems():
            self.addCleanup(patcher.stop)
        self.zmq = self.mocks['nmoscommon.ipc.zmq']

    def test_init(self):
        address = "ipc://dummy.test"
        UUT = Host(address)

        self.assertEqual(UUT.timeout, 100)
        self.zmq.Context.instance.assert_called_once_with()
        self.zmq.Context.instance.return_value.socket.assert_called_once_with(self.zmq.REP)
        self.zmq.Context.instance.return_value.socket.return_value.bind.assert_called_once_with(address)
        self.zmq.Context.instance.return_value.socket.return_value.setsockopt.assert_called_with(self.zmq.LINGER, 0)

        if address[:6] == "ipc://":
            self.mocks['os.chmod'].assert_called_with(address[6:], (stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR |
                                                                    stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP |
                                                                    stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH))

    def test_start_starts_a_greenlet_if_not_running(self):
        address = "ipc://dummy.test"
        UUT = Host(address)

        with mock.patch('gevent.spawn') as spawn:
            UUT.start()
            spawn.assert_called_once_with(mock.ANY)

    def test_start_does_nothing_if_already_running(self):
        address = "ipc://dummy.test"
        UUT = Host(address)

        with mock.patch('gevent.spawn') as spawn:
            UUT.start()
            spawn.assert_called_once_with(mock.ANY)
            spawn.reset_mock()

            UUT.start()
            spawn.assert_not_called()

    def test_stop_does_nothing_if_not_running(self):
        address = "ipc://dummy.test"
        UUT = Host(address)

        with mock.patch('gevent.spawn') as spawn:
            UUT.stop()
            spawn.return_value.kill.assert_not_called()

    def test_stop_kills_greenlet_if_already_running(self):
        address = "ipc://dummy.test"
        UUT = Host(address)

        with mock.patch('gevent.spawn') as spawn:
            UUT.start()
            UUT.stop()
            spawn.return_value.kill.assert_called_once_with()

    def test_start_restarts_greenlet_after_stopping(self):
        address = "ipc://dummy.test"
        UUT = Host(address)

        greenlets = [ mock.MagicMock(name="greenlet1"), mock.MagicMock(name="greenlet2") ]
        greenlet_queue = [ m for m in greenlets ] # Need a copy so that elements can be popped out
        with mock.patch('gevent.spawn', side_effect=lambda _ : greenlet_queue.pop(0)) as spawn:
            UUT.start()
            spawn.assert_called_once_with(mock.ANY)
            UUT.stop()
            greenlets[0].kill.assert_called_once_with()
            UUT.start()
            self.assertListEqual([ call for call in spawn.mock_calls if call[0] == "" ],
                                 [ mock.call(mock.ANY), mock.call(mock.ANY) ])
            UUT.stop()
            greenlets[1].kill.assert_called_once_with()

    def test_runloop_does_nothing_if_not_started(self):
        self.zmq.Context.instance.return_value.socket.return_value.poll.side_effect = Exception # This will throw an exception if the code gets as far as calling it
        

        address = "ipc://dummy.test"
        UUT = Host(address)

        # Make spawn just call the passed parameter, essentially a threadless launch
        def stop_then_call(UUT):
            def __inner(f):
                UUT.stop()
                return f()
            return __inner
            
        with mock.patch('gevent.spawn', side_effect=stop_then_call) as spawn:
            try:
                UUT.start()
            except:
                self.fail(msg="stop didn't prevent the runloop from running")

    def test_runloop_polls_for_messages_and_retries_on_timeout(self):
        def return_vals_then_raise(retvals, e=Exception):
            def __inner(*args, **kwargs):
                if len(retvals) > 0:
                    return retvals.pop(0)
                else:
                    raise e
            return __inner
        self.zmq.Context.instance.return_value.socket.return_value.poll.side_effect = return_vals_then_raise([ 0, 0, 0 ])

        address = "ipc://dummy.test"
        UUT = Host(address)

        # Make spawn just call the passed parameter, essentially a threadless launch
        with mock.patch('gevent.spawn', side_effect=lambda f : f()) as spawn:
            with self.assertRaises(Exception):
                UUT.start()
            self.assertListEqual(self.zmq.Context.instance.return_value.socket.return_value.poll.mock_calls,
                                 [ mock.call(timeout=UUT.timeout),
                                   mock.call(timeout=UUT.timeout),
                                   mock.call(timeout=UUT.timeout),
                                   mock.call(timeout=UUT.timeout) ])

    def test_runloop_sends_empty_reply_to_malformed_msg(self):
        def return_vals_then_raise(retvals, e=Exception):
            def __inner(*args, **kwargs):
                if len(retvals) > 0:
                    return retvals.pop(0)
                else:
                    raise e
            return __inner
        self.zmq.Context.instance.return_value.socket.return_value.poll.side_effect = return_vals_then_raise([ 1, ])
        self.zmq.Context.instance.return_value.socket.return_value.recv.return_value = """{"foo" : "bar"}"""

        address = "ipc://dummy.test"
        UUT = Host(address)

        # Make spawn just call the passed parameter, essentially a threadless launch
        with mock.patch('gevent.spawn', side_effect=lambda f : f()) as spawn:
            with self.assertRaises(Exception):
                UUT.start()
            self.assertListEqual(self.zmq.Context.instance.return_value.socket.return_value.poll.mock_calls,
                                 [ mock.call(timeout=UUT.timeout), mock.call(timeout=UUT.timeout) ])
            self.zmq.Context.instance.return_value.socket.return_value.recv.assert_called_once_with()
            self.zmq.Context.instance.return_value.socket.return_value.send.assert_called_once_with("{}")

    def test_runloop_sends_error_in_response_to_unknown_method_call(self):
        def return_vals_then_raise(retvals, e=Exception):
            def __inner(*args, **kwargs):
                if len(retvals) > 0:
                    return retvals.pop(0)
                else:
                    raise e
            return __inner
        self.zmq.Context.instance.return_value.socket.return_value.poll.side_effect = return_vals_then_raise([ 1, ])
        self.zmq.Context.instance.return_value.socket.return_value.recv.return_value = json.dumps({"function" : "unknown_function",
                                                                                                   "args" : [],
                                                                                                   "kwargs" : {} })

        address = "ipc://dummy.test"
        UUT = Host(address)

        # Make spawn just call the passed parameter, essentially a threadless launch
        with mock.patch('gevent.spawn', side_effect=lambda f : f()) as spawn:
            with self.assertRaises(Exception):
                UUT.start()
            self.assertListEqual(self.zmq.Context.instance.return_value.socket.return_value.poll.mock_calls,
                                 [ mock.call(timeout=UUT.timeout), mock.call(timeout=UUT.timeout) ])
            self.zmq.Context.instance.return_value.socket.return_value.recv.assert_called_once_with()
            self.zmq.Context.instance.return_value.socket.return_value.send.assert_called_once_with(json.dumps({ 'exc' : 'AttributeError'}))

    def test_runloop_sends_error_in_response_to_unknown_method_call(self):
        def return_vals_then_raise(retvals, e=Exception):
            def __inner(*args, **kwargs):
                if len(retvals) > 0:
                    return retvals.pop(0)
                else:
                    raise e
            return __inner
        self.zmq.Context.instance.return_value.socket.return_value.poll.side_effect = return_vals_then_raise([ 1, ])
        self.zmq.Context.instance.return_value.socket.return_value.recv.return_value = json.dumps({"function" : "unknown_function",
                                                                                                   "args" : [],
                                                                                                   "kwargs" : {} })

        address = "ipc://dummy.test"
        UUT = Host(address)

        # Make spawn just call the passed parameter, essentially a threadless launch
        with mock.patch('gevent.spawn', side_effect=lambda f : f()) as spawn:
            with self.assertRaises(Exception):
                UUT.start()
            self.assertListEqual(self.zmq.Context.instance.return_value.socket.return_value.poll.mock_calls,
                                 [ mock.call(timeout=UUT.timeout), mock.call(timeout=UUT.timeout) ])
            self.zmq.Context.instance.return_value.socket.return_value.recv.assert_called_once_with()
            self.zmq.Context.instance.return_value.socket.return_value.send.assert_called_once_with(json.dumps({ 'exc' : 'AttributeError'}))

    def test_runloop_passes_through_calls_to_known_method(self):
        def return_vals_then_raise(retvals, e=Exception):
            def __inner(*args, **kwargs):
                if len(retvals) > 0:
                    return retvals.pop(0)
                else:
                    raise e
            return __inner
        args = [ "foo", "bar" ]
        kwargs = { "baz" : "potato" }
        self.zmq.Context.instance.return_value.socket.return_value.poll.side_effect = return_vals_then_raise([ 1, ])
        self.zmq.Context.instance.return_value.socket.return_value.recv.return_value = json.dumps({"function" : "test_function",
                                                                                                   "args" : args,
                                                                                                   "kwargs" : kwargs })

        test_function_mock = mock.MagicMock(name="test_function_mock")
        def test_function(*args, **kwargs):
            return test_function_mock(*args, **kwargs)
        test_function_mock.return_value = None

        address = "ipc://dummy.test"
        UUT = Host(address)
        UUT.ipcmethod()(test_function)

        # Make spawn just call the passed parameter, essentially a threadless launch
        with mock.patch('gevent.spawn', side_effect=lambda f : f()) as spawn:
            with self.assertRaises(Exception):
                UUT.start()
            self.assertListEqual(self.zmq.Context.instance.return_value.socket.return_value.poll.mock_calls,
                                 [ mock.call(timeout=UUT.timeout), mock.call(timeout=UUT.timeout) ])
            self.zmq.Context.instance.return_value.socket.return_value.recv.assert_called_once_with()
            test_function_mock.assert_called_once_with(*args, **kwargs)
            self.zmq.Context.instance.return_value.socket.return_value.send.assert_called_once_with(json.dumps({}))

    def test_runloop_passes_through_calls_to_known_method_and_returns(self):
        def return_vals_then_raise(retvals, e=Exception):
            def __inner(*args, **kwargs):
                if len(retvals) > 0:
                    return retvals.pop(0)
                else:
                    raise e
            return __inner
        args = [ "foo", "bar" ]
        kwargs = { "baz" : "potato" }
        self.zmq.Context.instance.return_value.socket.return_value.poll.side_effect = return_vals_then_raise([ 1, ])
        self.zmq.Context.instance.return_value.socket.return_value.recv.return_value = json.dumps({"function" : "test_function",
                                                                                                   "args" : args,
                                                                                                   "kwargs" : kwargs })

        test_function_mock = mock.MagicMock(name="test_function_mock")
        def test_function(*args, **kwargs):
            return test_function_mock(*args, **kwargs)
        test_function_mock.return_value = "return_data"

        address = "ipc://dummy.test"
        UUT = Host(address)
        UUT.ipcmethod()(test_function)

        # Make spawn just call the passed parameter, essentially a threadless launch
        with mock.patch('gevent.spawn', side_effect=lambda f : f()) as spawn:
            with self.assertRaises(Exception):
                UUT.start()
            self.assertListEqual(self.zmq.Context.instance.return_value.socket.return_value.poll.mock_calls,
                                 [ mock.call(timeout=UUT.timeout), mock.call(timeout=UUT.timeout) ])
            self.zmq.Context.instance.return_value.socket.return_value.recv.assert_called_once_with()
            test_function_mock.assert_called_once_with(*args, **kwargs)
            self.zmq.Context.instance.return_value.socket.return_value.send.assert_called_once_with(json.dumps({ 'ret' : test_function_mock.return_value }))

    def test_runloop_passes_through_calls_to_known_method_and_sends_back_exception_when_one_is_raised(self):
        def return_vals_then_raise(retvals, e=Exception):
            def __inner(*args, **kwargs):
                if len(retvals) > 0:
                    return retvals.pop(0)
                else:
                    raise e
            return __inner
        args = [ "foo", "bar" ]
        kwargs = { "baz" : "potato" }
        self.zmq.Context.instance.return_value.socket.return_value.poll.side_effect = return_vals_then_raise([ 1, ])
        self.zmq.Context.instance.return_value.socket.return_value.recv.return_value = json.dumps({"function" : "test_function",
                                                                                                   "args" : args,
                                                                                                   "kwargs" : kwargs })

        test_function_mock = mock.MagicMock(name="test_function_mock")
        def test_function(*args, **kwargs):
            return test_function_mock(*args, **kwargs)
        test_function_mock.side_effect = Exception("This is a test Exception")

        address = "ipc://dummy.test"
        UUT = Host(address)
        UUT.ipcmethod()(test_function)

        # Make spawn just call the passed parameter, essentially a threadless launch
        with mock.patch('gevent.spawn', side_effect=lambda f : f()) as spawn:
            with self.assertRaises(Exception):
                UUT.start()
            self.assertListEqual(self.zmq.Context.instance.return_value.socket.return_value.poll.mock_calls,
                                 [ mock.call(timeout=UUT.timeout), mock.call(timeout=UUT.timeout) ])
            self.zmq.Context.instance.return_value.socket.return_value.recv.assert_called_once_with()
            test_function_mock.assert_called_once_with(*args, **kwargs)
            self.zmq.Context.instance.return_value.socket.return_value.send.assert_called_once_with(mock.ANY)
            sentval = self.zmq.Context.instance.return_value.socket.return_value.send.call_args[0][0]
            self.assertIsInstance(sentval, basestring)
            try:
                sentdict = json.loads(sentval)
            except:
                self.fail(msg="String sent back to remote client is not valid json")
            self.assertIn("exc", sentdict)
            self.assertIsInstance(sentdict["exc"], basestring)
            self.assertRegexpMatches(sentdict["exc"], r'Exception: This is a test Exception')

    def test_getmethods(self):
        methods = [ mock.MagicMock(__name__="foo", __doc__="foodoc"),
                    mock.MagicMock(__name__="bar", __doc__="bardoc"),
                    mock.MagicMock(__name__="baz", __doc__=None), ]
        address = "ipc://dummy.test"
        UUT = Host(address)
        for m in methods:
            UUT.ipcmethod()(m)
        self.assertEqual(UUT.getmethods(), dict([ (m.__name__, m.__doc__ if m.__doc__ is not None else "") for m in methods ] + [ ("getmethods", UUT.getmethods.__doc__) ]))
