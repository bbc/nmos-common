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

from six import PY2

import unittest
import mock

from nmoscommon.webapi import *

from datetime import timedelta
import re

import flask

def diff_ippresponse(self, other):
    result = []
    if self.headers != other.headers:
        result.append("HEADERS DIFFER")
        for (key, value) in self.headers:
            if key not in other.headers:
                result.append("  %r in self, but not other" % (key,))
            elif self.headers[key] != other.headers[key]:
                result.append("  %r : %r != %r" % (key, self.headers[key], other.headers[key]))
        for (key, value) in other.headers:
            if key not in self.headers:
                result.append("  %r in other but not self" % (key,))
        if self.get_data() != other.get_data():
            result.append("DATA DIFFERS")
            result.append("  " + repr(self.get_data()) + " != " + repr(other.get_data()))
        if self.status != other.status:
            result.append("STATUS DIFFERS")
            result.append("  " + repr(self.status) + " != " + repr(other.status))
        if self.mimetype != other.mimetype:
            result.append("MIMETYPE DIFFERS")
            result.append("  " + repr(self.mimetype) + " != " + repr(other.mimetype))
        if self.content_type != other.content_type:
            result.append("CONTENT TYPE DIFFERS")
            result.append("  " + repr(self.content_type) + " != " + repr(other.content_type))
        if self.direct_passthrough != other.direct_passthrough:
            result.append("PASSTHROUGH DIFFERS")
            result.append("  " + repr(self.direct_passthrough) + " != " + repr(other.direct_passthrough))
        return '\n'.join(result) + '\n'

class TestWebAPI(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestWebAPI, self).__init__(*args, **kwargs)
        if PY2:
            self.assertCountEqual = self.assertItemsEqual

    @mock.patch("nmoscommon.webapi.Flask")
    @mock.patch("nmoscommon.webapi.Sockets")
    def test_init(self, Sockets, Flask):
        _torun = mock.MagicMock(name="torun")
        class StubWebAPI(WebAPI):
            def torun(self):
                return _torun()

        UUT = StubWebAPI()

        self.assertEqual(UUT.app, Flask.return_value)
        self.assertEqual(UUT.app.response_class, IppResponse)
        UUT.app.before_first_request.assert_called_once_with(mock.ANY)
        installed_torun = UUT.app.before_first_request.call_args[0][0]
        self.assertEqual(UUT.sockets, Sockets.return_value)

        _torun.assert_not_called()
        installed_torun()
        _torun.assert_called_once_with()

    @mock.patch("nmoscommon.webapi.Flask")
    @mock.patch("nmoscommon.webapi.Sockets")
    def initialise_webapi_with_method_using_decorator(self, mock_webapi_method, decorator, Sockets, Flask, oauth_userid=None, expect_paths_below=False, is_socket=False, on_websocket_connect=None):
        """Returns a pair of the wrapped function that would be sent to flask.app.route, and the parameters which would
        be passed to flask.app.route for it."""
        def TEST(self, *args, **kwargs):
            return mock_webapi_method(*args, **kwargs)

        class StubWebAPI(WebAPI):
            pass

        if on_websocket_connect is not None:
            def _on_websocket_connect(*args, **kwargs):
                return on_websocket_connect(*args, **kwargs)
            StubWebAPI.on_websocket_connect = _on_websocket_connect

        StubWebAPI.TEST = decorator(TEST)
        basemethod = StubWebAPI.TEST

        UUT = StubWebAPI()
        if oauth_userid is not None:
            UUT._oauth_config = { "loginserver" : "http://example.com/loginserver", "proxies" : { "http" : "http://httpproxy.example", "https" : "http://httpsproxy.example" }, 'access_whitelist' : [ oauth_userid, ] }
        Flask.assert_called_once_with('nmoscommon.webapi')
        app = Flask.return_value

        self.assertEqual(app.response_class, IppResponse)
        app.before_first_request.assert_called_once_with(mock.ANY)
        torun = app.before_first_request.call_args[0][0]
        Sockets.assert_called_once_with(app)

        if is_socket:
            Sockets.return_value.route.assert_called_once_with('/', endpoint="_TEST")
            Sockets.return_value.route.return_value.assert_called_once_with(mock.ANY)
            return (Sockets.return_value.route.return_value.call_args[0][0], UUT, [ (call[1], call[2]) for call in Sockets.return_value.route.mock_calls if call[0] == '' ])
        elif not expect_paths_below:
            app.route.assert_called_once_with('/',
                                            endpoint="_TEST",
                                            methods=mock.ANY)
            app.route.return_value.assert_called_once_with(mock.ANY)
        else:
            self.assertCountEqual((call for call in app.route.mock_calls if call[0] == ''), [
                mock.call('/', endpoint="_TEST", methods=mock.ANY),
                mock.call('/<path:path>/', endpoint="_TEST_path", methods=mock.ANY), ])
            self.assertCountEqual((call for call in app.route.return_value.mock_calls if call[0] == ''), [
                mock.call(mock.ANY),
                mock.call(mock.ANY), ])
        return (app.route.return_value.call_args[0][0], UUT, [ (call[1], call[2]) for call in app.route.mock_calls if call[0] == '' ])

    @mock.patch('nmoscommon.webapi.http.urlopen')
    @mock.patch('nmoscommon.webapi.http.install_opener')
    @mock.patch('nmoscommon.flask_cors.make_response', side_effect=lambda x:x)
    @mock.patch('nmoscommon.flask_cors.request')
    def assert_wrapped_route_method_returns(self, f, expected, request, make_response, install_opener, urlopen, method="GET", args=[], kwargs={}, best_mimetype='application/json', request_headers=None, oauth_userid=None, oauth_token=None, ignore_body=False, urlopen_side_effect=None):
        if urlopen_side_effect is not None:
            urlopen.side_effect = urlopen_side_effect
        with mock.patch('nmoscommon.webapi.request', request):
            if oauth_userid is not None:
                # this method is called by the default_authorizer when oauth credentials are checked
                urlopen.return_value.read.return_value = json.dumps({ 'userid' : oauth_userid, 'token' : oauth_token })
                urlopen.return_value.code = 200
                request.url = "https://example.com/"
            else:
                request.url = "http://example.com/"
            request.method = method
            request.host = "example.com"
            if best_mimetype == TypeError:
                request.accept_mimetypes.best_match.side_effect = best_mimetype
            else:
                request.accept_mimetypes.best_match.return_value = best_mimetype
            if request_headers is not None:
                request.headers = request_headers
            else:
                request.headers = {}

            class TESTABORT(Exception):
                def __init__(self, code):
                    self.code = code
                    super(TESTABORT, self).__init__()

            def raise_code(n):
                raise TESTABORT(n)
            with mock.patch('nmoscommon.webapi.abort', side_effect=raise_code):
                try:
                    r = f(*args, **kwargs)
                except TESTABORT as e:
                    if isinstance(expected, int):
                        self.assertEqual(e.code,expected, msg="Expected abort with code %d, got abort with code %d" % (expected, e.code))
                    else:
                        self.fail(msg="Got unexpected abort with code %d when expecting a returned Response" % (e.code,))
                else:
                    if isinstance(expected, int):
                        self.fail(msg="Got unexpected Response object when expecting an abort with code %d" % (expected, ))
                    else:
                        if ignore_body:
                            expected.set_data(r.get_data())
                        if not isinstance(r, IppResponse):
                            r = IppResponse(r)
                        if not isinstance(expected, IppResponse):
                            expected = IppResponse(expected)
                        self.assertEqual(r, expected, msg="""

Expected %s(response=%r,\n status=%r,\n headers=%r,\n mimetype=%r,\n content_type=%r\n, direct_passthrough=%r)

Got %s(response=%r,\n status=%r,\n headers=%r,\n mimetype=%r,\n content_type=%r,\n direct_passthrough=%r)

Differences: 

%s""" % (type(expected).__name__,
         expected.get_data(),
                                                                                                                             expected.status,
                                                                                                                             dict(expected.headers),
                                                                                                                             expected.mimetype,
                                                                                                                             expected.content_type,
                                                                                                                             expected.direct_passthrough,
                                                                                                                             type(r).__name__,
                                                                                                                             r.get_data(),
                                                                                                                             r.status,
                                                                                                                             dict(r.headers),
                                                                                                                             r.mimetype,
                                                                                                                             r.content_type,
                                                                                                                             r.direct_passthrough,
                          diff_ippresponse(expected, r)))

    def perform_test_on_decorator(self, data):
        """This method will take a mock method and wrap it with a specified decorator, then create a webapi class instance with that method as a member.
        It will check that the object automatically registers the 

        The format of the input is as dictionary, with several keys which must be provided, and many which may:

        Mandatory keys:

        'methods'     -- This is a list of strings which are the HTTP methods with which the route is expected to be registered with Flask.
        'path'        -- This is the path that is expected to be passed to Flask when the method is registered.
        'return_data' -- This is the value that will be returned by the wrapped method when it is called.
        'method'      -- This is the HTTP method which will be provided in the call that is made to the wrapped function for testing.
        'decorator'   -- This is the decorator we are testing, it must be a callable object which takes a single function as a parameter and returns a callable
        'expected'    -- This is the expected response which will be sent to the Flask subsystem for output by the wrapped method when it is called. If set to mock.ANY then
                         any result will be acceptable, if it is set to an integer then we expect 'abort' to be called with that status code.

        Optional Keys:

        'headers'         -- These headers will be included in the mock request when the wrapped method is called.
        'oauth_userid'    -- if present then the call will be performed in a mock Flask environment which implements oauth, and this value will be returned by the mock 
                             credentials server as an acceptable user id.
        'oauth_whitelist' -- if present when 'oauth_userid' is also specified then this value will be added to the mock whitelist of acceptable user ids. If not specified then
                             the value of 'oauth_userid' will be put on this whitelist instead.
        'oauth_token      -- if present when 'oauth_userid' is also specified then this value will be returned by the mock credentials server as an acceptable authorisation token.
        'best_type'       -- If the code attempts to determine what the best mime-type to use for a return format then it will be given this value,
                             alternatively set this to TypeError to mimick the behaviour when none of the acceptible types is available.
        'extract_path'    -- If this is included and set to true then the wrapped function will be called with this value as a parameter as if it were a path
        'ignore_body'     -- If this is set to true then the contents of the body of the 'expected' request will be forced to the same value as the body of the returned response
                             before a comparison is performed. Metadata, headers, etc ... are still compared.
        'authenticate'    -- a custom callable for the oauth authenticate method
        'authorize'       -- a custom callable for the oauth autorize method
        'urlopen'         -- a side effect which will be hooked into the urlopen function, pass an exception to make it fail!
"""
        method = mock.MagicMock(name="webapi", return_value=data['return_data'])

        (f, UUT, calls) = self.initialise_webapi_with_method_using_decorator(method, data['decorator'], oauth_userid=data.get('oauth_whitelist',data.get('oauth_userid', None)), expect_paths_below=('extract_path' in data))
        self.assertIn("_TEST", (kwargs['endpoint'] for (args, kwargs) in calls))
        self.assertTrue(all((kwargs['endpoint'].startswith("_TEST") for (args, kwargs) in calls)))
        for (args, kwargs) in calls:
            # Check that flask was given through the expected commands
            self.assertEqual(kwargs['methods'], data['methods'] + ["OPTIONS"])

        if 'authenticate' in data:
            UUT.authenticate(data['authenticate'])
        if 'authorize' in data:
            UUT.authorize(data['authorize'])

        kwargs = {}
        if 'extract_path' in data:
            kwargs = { 'path' : data['extract_path'] }
        self.assert_wrapped_route_method_returns(f, data['expected'],
                                                     method=data.get('method',"GET"),
                                                     best_mimetype=data.get('best_type',None),
                                                     request_headers=data.get('headers',None),
                                                     oauth_userid=data.get('oauth_userid', None),
                                                     oauth_token=data.get('oauth_token',None),
                                                     kwargs=kwargs,
                                                     ignore_body=data.get('ignore_body', False),
                                                     urlopen_side_effect=data.get('urlopen', None))

    def test_secure_route__GET__json(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO"],
                'path'        : '/',
                'return_data' : { 'foo' : 'bar', 'baz' : ['boop',] },
                'method'      : "GET",
                'best_type'   : 'application/json',
                'decorator'   : secure_route('/', methods=["GET", "POST", "POTATO"], auto_json=True, headers=["x-not-a-real-header",], origin="example.com"),
                'expected'    : IppResponse(response=json.dumps({ 'foo' : 'bar', 'baz' : ['boop',] }, indent=4),
                                                                    status=200,
                                                                    headers={ 'Access-Control-Allow-Methods'     : u'GET, POST, POTATO',
                                                                              'Access-Control-Max-Age'           : u'21600',
                                                                              'Cache-Control'                    : u'no-cache, must-revalidate, no-store',
                                                                              'Access-Control-Allow-Credentials' : u'true',
                                                                              'Access-Control-Allow-Origin'      : u'example.com',
                                                                              'Access-Control-Allow-Headers'     : u'X-NOT-A-REAL-HEADER, CONTENT-TYPE, TOKEN',
                                                                              'Content-Type'                     : u'application/json',
                                                                              'Content-Length'                   : 56 },
                                                                    mimetype=u'application/json',
                                                                    content_type=u'application/json'),
            })

    def test_secure_route__GET__without_specified_methods(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "HEAD"],
                'path'        : '/',
                'return_data' : { 'foo' : 'bar', 'baz' : ['boop',] },
                'method'      : "GET",
                'best_type'   : 'application/json',
                'decorator'   : secure_route('/', auto_json=True, headers=["x-not-a-real-header",], origin="example.com"),
                'expected'    : IppResponse(response=json.dumps({ 'foo' : 'bar', 'baz' : ['boop',] }, indent=4),
                                                                    status=200,
                                                                    headers={ 'Access-Control-Allow-Methods'     : u'GET, HEAD',
                                                                              'Access-Control-Max-Age'           : u'21600',
                                                                              'Cache-Control'                    : u'no-cache, must-revalidate, no-store',
                                                                              'Access-Control-Allow-Credentials' : u'true',
                                                                              'Access-Control-Allow-Origin'      : u'example.com',
                                                                              'Access-Control-Allow-Headers'     : u'X-NOT-A-REAL-HEADER, CONTENT-TYPE, TOKEN',
                                                                              'Content-Type'                     : u'application/json',
                                                                              'Content-Length'                   : 56 },
                                                                    mimetype=u'application/json',
                                                                    content_type=u'application/json'),
            })

    def test_secure_route__GET__without_specified_headers(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO"],
                'path'        : '/',
                'return_data' : { 'foo' : 'bar', 'baz' : ['boop',] },
                'method'      : "GET",
                'best_type'   : 'application/json',
                'decorator'   : secure_route('/', methods=["GET", "POST", "POTATO"], auto_json=True, origin="example.com"),
                'expected'    : IppResponse(response=json.dumps({ 'foo' : 'bar', 'baz' : ['boop',] }, indent=4),
                                                                    status=200,
                                                                    headers={ 'Access-Control-Allow-Methods'     : u'GET, POST, POTATO',
                                                                              'Access-Control-Max-Age'           : u'21600',
                                                                              'Cache-Control'                    : u'no-cache, must-revalidate, no-store',
                                                                              'Access-Control-Allow-Credentials' : u'true',
                                                                              'Access-Control-Allow-Origin'      : u'example.com',
                                                                              'Access-Control-Allow-Headers'     : u'CONTENT-TYPE, TOKEN',
                                                                              'Content-Type'                     : u'application/json',
                                                                              'Content-Length'                   : 56 },
                                                                    mimetype=u'application/json',
                                                                    content_type=u'application/json'),
            })

    def test_secure_route__GET__with_TypeError_when_checking_best_mime_type(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO"],
                'path'        : '/',
                'return_data' : { 'foo' : 'bar', 'baz' : ['boop',] },
                'method'      : "GET",
                'best_type'   : TypeError,
                'decorator'   : secure_route('/', methods=["GET", "POST", "POTATO"], auto_json=True, headers=["x-not-a-real-header",], origin="example.com"),
                'expected'    : IppResponse(status=204,
                                            headers={'Access-Control-Allow-Headers': u'X-NOT-A-REAL-HEADER, CONTENT-TYPE, TOKEN',
                                                     'Access-Control-Max-Age'      : u'21600',
                                                     'Cache-Control'               : u'no-cache, must-revalidate, no-store',
                                                     'Access-Control-Allow-Origin' : u'example.com',
                                                     'Access-Control-Allow-Methods': u'GET, POST, POTATO',
                                                     'Content-Type'                : u'text/html; charset=utf-8'},
                                            mimetype=u'text/html',
                                            content_type=u'text/html; charset=utf-8',
                                            direct_passthrough=False),
            })

    def test_secure_route__GET__with_string_data(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO"],
                'path'        : '/',
                'return_data' : "POTATO",
                'method'      : "GET",
                'decorator'   : secure_route('/', methods=["GET", "POST", "POTATO"], auto_json=True, headers=["x-not-a-real-header",], origin="example.com"),
                'expected'    : IppResponse(response="POTATO",
                                            status=200,
                                            headers={'Content-Length': u'6',
                                                     'Access-Control-Allow-Headers': u'X-NOT-A-REAL-HEADER, CONTENT-TYPE, TOKEN',
                                                     'Access-Control-Max-Age': u'21600',
                                                     'Cache-Control': u'no-cache, must-revalidate, no-store',
                                                     'Access-Control-Allow-Credentials': u'true',
                                                     'Access-Control-Allow-Origin': u'example.com',
                                                     'Access-Control-Allow-Methods': u'GET, POST, POTATO',
                                                     'Content-Type': u'text/html; charset=utf-8'}),
            })

    def test_secure_route__GET__with_wrapped_method_returning_IppResponse(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO"],
                'path'        : '/',
                'return_data' : IppResponse(response="POTATO",
                                            status=200,
                                            headers={'Content-Length': u'6',
                                                     'Access-Control-Allow-Headers': u'X-NOT-A-REAL-HEADER, CONTENT-TYPE, TOKEN',
                                                     'Access-Control-Max-Age': u'21600',
                                                     'Cache-Control': u'no-cache, must-revalidate, no-store',
                                                     'Access-Control-Allow-Credentials': u'true',
                                                     'Access-Control-Allow-Origin': u'example.com',
                                                     'Access-Control-Allow-Methods': u'GET, POST, POTATO',
                                                     'Content-Type': u'text/html; charset=utf-8'}),
                'method'      : "GET",
                'decorator'   : secure_route('/', methods=["GET", "POST", "POTATO"], auto_json=True, headers=["x-not-a-real-header",], origin="example.com"),
                'expected'    : IppResponse(response="POTATO",
                                            status=200,
                                            headers={'Content-Length': u'6',
                                                     'Access-Control-Allow-Headers': u'X-NOT-A-REAL-HEADER, CONTENT-TYPE, TOKEN',
                                                     'Access-Control-Max-Age': u'21600',
                                                     'Cache-Control': u'no-cache, must-revalidate, no-store',
                                                     'Access-Control-Allow-Credentials': u'true',
                                                     'Access-Control-Allow-Origin': u'example.com',
                                                     'Access-Control-Allow-Methods': u'GET, POST, POTATO',
                                                     'Content-Type': u'text/html; charset=utf-8'}),
            })

    def test_secure_route__GET__with_wrapped_method_returning_Response(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO"],
                'path'        : '/',
                'return_data' : Response(response="POTATO",
                                            status=200,
                                            headers={'Content-Length': u'6',
                                                     'Access-Control-Allow-Headers': u'X-NOT-A-REAL-HEADER, CONTENT-TYPE, TOKEN',
                                                     'Access-Control-Max-Age': u'21600',
                                                     'Cache-Control': u'no-cache, must-revalidate, no-store',
                                                     'Access-Control-Allow-Credentials': u'true',
                                                     'Access-Control-Allow-Origin': u'example.com',
                                                     'Access-Control-Allow-Methods': u'GET, POST, POTATO',
                                                     'Content-Type': u'text/html; charset=utf-8'}),
                'method'      : "GET",
                'decorator'   : secure_route('/', methods=["GET", "POST", "POTATO"], auto_json=True, headers=["x-not-a-real-header",], origin="example.com"),
                'expected'    : IppResponse(response="POTATO",
                                            status=200,
                                            headers={'Content-Length': u'6',
                                                     'Access-Control-Allow-Headers': u'X-NOT-A-REAL-HEADER, CONTENT-TYPE, TOKEN',
                                                     'Access-Control-Max-Age': u'21600',
                                                     'Cache-Control': u'no-cache, must-revalidate, no-store',
                                                     'Access-Control-Allow-Credentials': u'true',
                                                     'Access-Control-Allow-Origin': u'example.com',
                                                     'Access-Control-Allow-Methods': u'GET, POST, POTATO',
                                                     'Content-Type': u'text/html; charset=utf-8'}),
            })

    def test_secure_route__GET__html(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO"],
                'path'        : '/',
                'return_data' : { 'foo' : 'bar', 'baz' : ['boop',] },
                'method'      : "GET",
                'best_type'   : 'text/html',
                'decorator'   : secure_route('/', methods=["GET", "POST", "POTATO"], auto_json=True, headers=["x-not-a-real-header",], origin="example.com"),
                'expected'    : IppResponse(    status=200,
                                                headers={    'Access-Control-Allow-Headers': u'X-NOT-A-REAL-HEADER, CONTENT-TYPE, TOKEN',
                                                             'Access-Control-Max-Age': u'21600',
                                                             'Cache-Control': u'no-cache, must-revalidate, no-store',
                                                             'Access-Control-Allow-Origin': u'example.com',
                                                             'Access-Control-Allow-Methods': u'GET, POST, POTATO',
                                                             'Content-Type': u'text/html; charset=utf-8'},
                                                mimetype=u'text/html',
                                                content_type=u'text/html; charset=utf-8',
                                                direct_passthrough=False),
                'ignore_body' : True
            })

    def test_secure_route__GET__with_wrapped_method_returning_list(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO"],
                'path'        : '/',
                'return_data' : [ 'foo', 'bar', 'baz', 'boop',],
                'method'      : "GET",
                'best_type'   : 'application/json',
                'decorator'   : secure_route('/', methods=["GET", "POST", "POTATO"], auto_json=True, headers=["x-not-a-real-header",], origin="example.com"),
                'expected'    : IppResponse(response=json.dumps([ 'foo', 'bar', 'baz', 'boop',], indent=4),
                                                                    status=200,
                                                                    headers={ 'Access-Control-Allow-Methods'     : u'GET, POST, POTATO',
                                                                              'Access-Control-Max-Age'           : u'21600',
                                                                              'Cache-Control'                    : u'no-cache, must-revalidate, no-store',
                                                                              'Access-Control-Allow-Credentials' : u'true',
                                                                              'Access-Control-Allow-Origin'      : u'example.com',
                                                                              'Access-Control-Allow-Headers'     : u'X-NOT-A-REAL-HEADER, CONTENT-TYPE, TOKEN',
                                                                              'Content-Type'                     : u'application/json',
                                                                              'Content-Length'                   : 56 },
                                                                    mimetype=u'application/json',
                                                                    content_type=u'application/json'),
            })

    def test_secure_route__GET__with_good_userid_and_no_token(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO"],
                'path'        : '/',
                'return_data' : { 'foo' : 'bar', 'baz' : ['boop',] },
                'method'      : "GET",
                'best_type'   : 'application/json',
                'decorator'   : secure_route('/', methods=["GET", "POST", "POTATO"], auto_json=True, headers=["x-not-a-real-header",], origin="example.com"),
                'oauth_userid': "FAKE_USER_ID",
                'expected'    : IppResponse(status=401,
                                            headers={ 'Access-Control-Allow-Origin' : u'example.com',
                                                      'Access-Control-Allow-Methods': u'GET, POST, POTATO',
                                                      'Access-Control-Allow-Headers': u'X-NOT-A-REAL-HEADER, CONTENT-TYPE, TOKEN',
                                                      'Access-Control-Max-Age'      : u'21600',
                                                      'Cache-Control'               : u'no-cache, must-revalidate, no-store',
                                                      'Content-Type'                : u'text/html; charset=utf-8' }),
            })

    def test_secure_route__GET__with_good_userid_and_bad_token(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO"],
                'path'        : '/',
                'return_data' : { 'foo' : 'bar', 'baz' : ['boop',] },
                'method'      : "GET",
                'headers'     : { 'token' : "jkhndgkjsj.jkuhjhn" },
                'best_type'   : 'application/json',
                'decorator'   : secure_route('/', methods=["GET", "POST", "POTATO"], auto_json=True, headers=["x-not-a-real-header",], origin="example.com"),
                'oauth_userid': "FAKE_USER_ID",
                'oauth_token' : None,
                'expected'    : IppResponse(status=401,
                                            headers={ 'Access-Control-Allow-Origin' : u'example.com',
                                                      'Access-Control-Allow-Methods': u'GET, POST, POTATO',
                                                      'Access-Control-Allow-Headers': u'X-NOT-A-REAL-HEADER, CONTENT-TYPE, TOKEN',
                                                      'Access-Control-Max-Age'      : u'21600',
                                                      'Cache-Control'               : u'no-cache, must-revalidate, no-store',
                                                      'Content-Type'                : u'text/html; charset=utf-8' }),
            })

    def test_secure_route__GET__with_bad_userid_and_good_token(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO"],
                'path'        : '/',
                'return_data' : { 'foo' : 'bar', 'baz' : ['boop',] },
                'method'      : "GET",
                'headers'     : { 'token' : "jkhndgkjsj.jkuhjhn" },
                'best_type'   : 'application/json',
                'decorator'   : secure_route('/', methods=["GET", "POST", "POTATO"], auto_json=True, headers=["x-not-a-real-header",], origin="example.com"),
                'oauth_userid': "FAKE_USER_ID",
                'oauth_whitelist' : "OTHER_USER_ID",
                'oauth_token' : "jkhndgkjsj.jkuhjhn",
                'expected'    : IppResponse(status=401,
                                            headers={ 'Access-Control-Allow-Origin' : u'example.com',
                                                      'Access-Control-Allow-Methods': u'GET, POST, POTATO',
                                                      'Access-Control-Allow-Headers': u'X-NOT-A-REAL-HEADER, CONTENT-TYPE, TOKEN',
                                                      'Access-Control-Max-Age'      : u'21600',
                                                      'Cache-Control'               : u'no-cache, must-revalidate, no-store',
                                                      'Content-Type'                : u'text/html; charset=utf-8' }),
            })

    def test_secure_route__GET__with_good_userid_and_good_token(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO"],
                'path'        : '/',
                'return_data' : { 'foo' : 'bar', 'baz' : ['boop',] },
                'method'      : "GET",
                'headers'     : { 'token' : "jkhndgkjsj.jkuhjhn" },
                'best_type'   : 'application/json',
                'decorator'   : secure_route('/', methods=["GET", "POST", "POTATO"], auto_json=True, headers=["x-not-a-real-header",], origin="example.com"),
                'oauth_userid': "FAKE_USER_ID",
                'oauth_token' : "jkhndgkjsj.jkuhjhn",
                'expected'    : IppResponse(response=json.dumps({ 'foo' : 'bar', 'baz' : ['boop',] }, indent=4),
                                            status=200,
                                            headers= {'Content-Length': u'56',
                                                          'Access-Control-Allow-Headers': u'X-NOT-A-REAL-HEADER, CONTENT-TYPE, TOKEN',
                                                          'Access-Control-Max-Age': u'21600',
                                                          'Cache-Control': u'no-cache, must-revalidate, no-store',
                                                          'Access-Control-Allow-Credentials': u'true',
                                                          'Access-Control-Allow-Origin': u'example.com',
                                                          'Access-Control-Allow-Methods': u'GET, POST, POTATO',
                                                          'Content-Type': u'application/json'},
                                            mimetype=u'application/json',
                                            content_type=u'application/json',
                                            direct_passthrough=False),
            })

    def test_secure_route__GET__with_custom_authenticate_and_authorize_methods(self):
        custom_authenticate = mock.MagicMock(name='custom_authenticate', return_value=True)
        custom_authorize    = mock.MagicMock(name='custom_authorize',    return_value=True)
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO"],
                'path'        : '/',
                'return_data' : { 'foo' : 'bar', 'baz' : ['boop',] },
                'method'      : "GET",
                'headers'     : { 'token' : "jkhndgkjsj.jkuhjhn" },
                'best_type'   : 'application/json',
                'decorator'   : secure_route('/', methods=["GET", "POST", "POTATO"], auto_json=True, headers=["x-not-a-real-header",], origin="example.com"),
                'oauth_userid': "FAKE_USER_ID",
                'oauth_token' : "jkhndgkjsj.jkuhjhn",
                'authenticate': custom_authenticate,
                'authorize'   : custom_authorize,
                'expected'    : IppResponse(response=json.dumps({ 'foo' : 'bar', 'baz' : ['boop',] }, indent=4),
                                            status=200,
                                            headers= {'Content-Length': u'56',
                                                          'Access-Control-Allow-Headers': u'X-NOT-A-REAL-HEADER, CONTENT-TYPE, TOKEN',
                                                          'Access-Control-Max-Age': u'21600',
                                                          'Cache-Control': u'no-cache, must-revalidate, no-store',
                                                          'Access-Control-Allow-Credentials': u'true',
                                                          'Access-Control-Allow-Origin': u'example.com',
                                                          'Access-Control-Allow-Methods': u'GET, POST, POTATO',
                                                          'Content-Type': u'application/json'},
                                            mimetype=u'application/json',
                                            content_type=u'application/json',
                                            direct_passthrough=False),
            })
        custom_authenticate.assert_called_once_with("jkhndgkjsj.jkuhjhn")
        custom_authorize.assert_called_once_with("jkhndgkjsj.jkuhjhn")

    def test_secure_route__GET__can_handle_an_exception_in_proxied_request(self):
        fp = mock.MagicMock(name="fp")
        e = http.HTTPError("http://example.com", 404, "Coulds Not Finded", {}, fp)
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO"],
                'path'        : '/',
                'return_data' : { 'foo' : 'bar', 'baz' : ['boop',] },
                'method'      : "GET",
                'headers'     : { 'token' : "jkhndgkjsj.jkuhjhn" },
                'best_type'   : 'application/json',
                'decorator'   : secure_route('/', methods=["GET", "POST", "POTATO"], auto_json=True, headers=["x-not-a-real-header",], origin="example.com"),
                'oauth_userid': "FAKE_USER_ID",
                'oauth_token' : "jkhndgkjsj.jkuhjhn",
                'urlopen'     : e,
                'expected'    : IppResponse(status=401,
                                            headers= {    'Access-Control-Allow-Headers': u'X-NOT-A-REAL-HEADER, CONTENT-TYPE, TOKEN',
                                                          'Access-Control-Max-Age': u'21600',
                                                          'Cache-Control': u'no-cache, must-revalidate, no-store',
                                                          'Access-Control-Allow-Origin': u'example.com',
                                                          'Access-Control-Allow-Methods': u'GET, POST, POTATO'},
                                            content_type=u'text/html; charset=utf-8'),
            })

    def test_secure_route__GET__with_wrapped_method_returning_status_code(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO"],
                'path'        : '/',
                'return_data' : (201, { 'foo' : 'bar', 'baz' : ['boop',] }),
                'method'      : "GET",
                'best_type'   : 'application/json',
                'decorator'   : secure_route('/', methods=["GET", "POST", "POTATO"], auto_json=True, headers=["x-not-a-real-header",], origin="example.com"),
                'expected'    : IppResponse(response=json.dumps({ 'foo' : 'bar', 'baz' : ['boop',] }, indent=4),
                                                                    status=201,
                                                                    headers={ 'Access-Control-Allow-Methods'     : u'GET, POST, POTATO',
                                                                              'Access-Control-Max-Age'           : u'21600',
                                                                              'Cache-Control'                    : u'no-cache, must-revalidate, no-store',
                                                                              'Access-Control-Allow-Credentials' : u'true',
                                                                              'Access-Control-Allow-Origin'      : u'example.com',
                                                                              'Access-Control-Allow-Headers'     : u'X-NOT-A-REAL-HEADER, CONTENT-TYPE, TOKEN',
                                                                              'Content-Type'                     : u'application/json',
                                                                              'Content-Length'                   : 56 },
                                                                    mimetype=u'application/json',
                                                                    content_type=u'application/json'),
            })

    def test_secure_route__GET__with_wrapped_method_returning_status_code_and_headers(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO"],
                'path'        : '/',
                'return_data' : (201, { 'foo' : 'bar', 'baz' : ['boop',] }, {'X-A-HEADER' : 'AVALUE'}),
                'method'      : "GET",
                'best_type'   : 'application/json',
                'decorator'   : secure_route('/', methods=["GET", "POST", "POTATO"], auto_json=True, headers=["x-not-a-real-header",], origin="example.com"),
                'expected'    : IppResponse(response=json.dumps({ 'foo' : 'bar', 'baz' : ['boop',] }, indent=4),
                                                                    status=201,
                                                                    headers={ 'Access-Control-Allow-Methods'     : u'GET, POST, POTATO',
                                                                              'Access-Control-Max-Age'           : u'21600',
                                                                              'Cache-Control'                    : u'no-cache, must-revalidate, no-store',
                                                                              'Access-Control-Allow-Credentials' : u'true',
                                                                              'Access-Control-Allow-Origin'      : u'example.com',
                                                                              'Access-Control-Allow-Headers'     : u'X-NOT-A-REAL-HEADER, CONTENT-TYPE, TOKEN',
                                                                              'Content-Type'                     : u'application/json',
                                                                              'Content-Length'                   : 56,
                                                                              'X-A-HEADER'                       : 'AVALUE'},
                                                                    mimetype=u'application/json',
                                                                    content_type=u'application/json'),
            })


    def test_route__GET__json(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO"],
                'path'        : '/',
                'return_data' : { 'foo' : 'bar', 'baz' : ['boop',] },
                'method'      : "GET",
                'best_type'   : 'application/json',
                'decorator'   : route('/', methods=["GET", "POST", "POTATO"], auto_json=True, headers=["x-not-a-real-header",], origin="example.com"),
                'expected'    : IppResponse(response=json.dumps({ 'foo' : 'bar', 'baz' : ['boop',] }, indent=4),
                                                                    status=200,
                                                                    headers={ 'Access-Control-Allow-Methods'     : u'GET, POST, POTATO',
                                                                              'Access-Control-Max-Age'           : u'21600',
                                                                              'Cache-Control'                    : u'no-cache, must-revalidate, no-store',
                                                                              'Access-Control-Allow-Origin'      : u'example.com',
                                                                              'Access-Control-Allow-Headers'     : u'X-NOT-A-REAL-HEADER, CONTENT-TYPE',
                                                                              'Content-Type'                     : u'application/json',
                                                                              'Content-Length'                   : 56 },
                                                                    mimetype=u'application/json',
                                                                    content_type=u'application/json'),
            })

    def test_route__GET__without_autojson(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO"],
                'path'        : '/',
                'return_data' : IppResponse(response=json.dumps({ 'foo' : 'bar', 'baz' : ['boop',] }, indent=4),
                                                                status=200,
                                                                content_type=u'application/json'),
                'method'      : "GET",
                'best_type'   : 'application/json',
                'decorator'   : route('/', methods=["GET", "POST", "POTATO"], auto_json=False, origin="example.com"),
                'expected'    : IppResponse(response=json.dumps({ 'foo' : 'bar', 'baz' : ['boop',] }, indent=4),
                                                                    status=200,
                                                                    headers={ 'Access-Control-Allow-Methods'     : u'GET, POST, POTATO',
                                                                              'Access-Control-Max-Age'           : u'21600',
                                                                              'Cache-Control'                    : u'no-cache, must-revalidate, no-store',
                                                                              'Access-Control-Allow-Origin'      : u'example.com',
                                                                              'Access-Control-Allow-Headers'     : u'CONTENT-TYPE',
                                                                              'Content-Type'                     : u'application/json',
                                                                              'Content-Length'                   : 56 },
                                                                    mimetype=u'application/json',
                                                                    content_type=u'application/json'),
            })

    def test_route__GET__without_autojson_or_methods(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "HEAD"],
                'path'        : '/',
                'return_data' : IppResponse(response=json.dumps({ 'foo' : 'bar', 'baz' : ['boop',] }, indent=4),
                                                                status=200,
                                                                content_type=u'application/json'),
                'method'      : "GET",
                'best_type'   : 'application/json',
                'decorator'   : route('/', auto_json=False, origin="example.com"),
                'expected'    : IppResponse(response=json.dumps({ 'foo' : 'bar', 'baz' : ['boop',] }, indent=4),
                                                                    status=200,
                                                                    headers={ 'Access-Control-Allow-Methods'     : u'GET, HEAD',
                                                                              'Access-Control-Max-Age'           : u'21600',
                                                                              'Cache-Control'                    : u'no-cache, must-revalidate, no-store',
                                                                              'Access-Control-Allow-Origin'      : u'example.com',
                                                                              'Access-Control-Allow-Headers'     : u'CONTENT-TYPE',
                                                                              'Content-Type'                     : u'application/json',
                                                                              'Content-Length'                   : 56 },
                                                                    mimetype=u'application/json',
                                                                    content_type=u'application/json'),
            })

    def test_route__GET__without_methods(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "HEAD"],
                'path'        : '/',
                'return_data' : { 'foo' : 'bar', 'baz' : ['boop',] },
                'method'      : "GET",
                'best_type'   : 'application/json',
                'decorator'   : route('/', auto_json=True, headers=["x-not-a-real-header",], origin="example.com"),
                'expected'    : IppResponse(response=json.dumps({ 'foo' : 'bar', 'baz' : ['boop',] }, indent=4),
                                                                    status=200,
                                                                    headers={ 'Access-Control-Allow-Methods'     : u'GET, HEAD',
                                                                              'Access-Control-Max-Age'           : u'21600',
                                                                              'Cache-Control'                    : u'no-cache, must-revalidate, no-store',
                                                                              'Access-Control-Allow-Origin'      : u'example.com',
                                                                              'Access-Control-Allow-Headers'     : u'X-NOT-A-REAL-HEADER, CONTENT-TYPE',
                                                                              'Content-Type'                     : u'application/json',
                                                                              'Content-Length'                   : 56 },
                                                                    mimetype=u'application/json',
                                                                    content_type=u'application/json'),
            })

    def test_route__GET__without_headers(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO"],
                'path'        : '/',
                'return_data' : { 'foo' : 'bar', 'baz' : ['boop',] },
                'method'      : "GET",
                'best_type'   : 'application/json',
                'decorator'   : route('/', methods=["GET", "POST", "POTATO"], auto_json=True, origin="example.com"),
                'expected'    : IppResponse(response=json.dumps({ 'foo' : 'bar', 'baz' : ['boop',] }, indent=4),
                                                                    status=200,
                                                                    headers={ 'Access-Control-Allow-Methods'     : u'GET, POST, POTATO',
                                                                              'Access-Control-Max-Age'           : u'21600',
                                                                              'Cache-Control'                    : u'no-cache, must-revalidate, no-store',
                                                                              'Access-Control-Allow-Origin'      : u'example.com',
                                                                              'Access-Control-Allow-Headers'     : u'CONTENT-TYPE',
                                                                              'Content-Type'                     : u'application/json',
                                                                              'Content-Length'                   : 56 },
                                                                    mimetype=u'application/json',
                                                                    content_type=u'application/json'),
            })

    def test_route__GET__with_wrapped_method_returning_status(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO"],
                'path'        : '/',
                'return_data' : (201, { 'foo' : 'bar', 'baz' : ['boop',] }),
                'method'      : "GET",
                'best_type'   : 'application/json',
                'decorator'   : route('/', methods=["GET", "POST", "POTATO"], auto_json=True, origin="example.com"),
                'expected'    : IppResponse(response=json.dumps({ 'foo' : 'bar', 'baz' : ['boop',] }, indent=4),
                                                                    status=201,
                                                                    headers={ 'Access-Control-Allow-Methods'     : u'GET, POST, POTATO',
                                                                              'Access-Control-Max-Age'           : u'21600',
                                                                              'Cache-Control'                    : u'no-cache, must-revalidate, no-store',
                                                                              'Access-Control-Allow-Origin'      : u'example.com',
                                                                              'Access-Control-Allow-Headers'     : u'CONTENT-TYPE',
                                                                              'Content-Type'                     : u'application/json',
                                                                              'Content-Length'                   : 56 },
                                                                    mimetype=u'application/json',
                                                                    content_type=u'application/json'),
            })

    def test_route__GET__with_wrapped_method_returning_status_and_headers(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO"],
                'path'        : '/',
                'return_data' : (201, { 'foo' : 'bar', 'baz' : ['boop',] }, {'X-A-HEADER' : 'AVALUE'}),
                'method'      : "GET",
                'best_type'   : 'application/json',
                'decorator'   : route('/', methods=["GET", "POST", "POTATO"], auto_json=True, origin="example.com"),
                'expected'    : IppResponse(response=json.dumps({ 'foo' : 'bar', 'baz' : ['boop',] }, indent=4),
                                                                    status=201,
                                                                    headers={ 'Access-Control-Allow-Methods'     : u'GET, POST, POTATO',
                                                                              'Access-Control-Max-Age'           : u'21600',
                                                                              'Cache-Control'                    : u'no-cache, must-revalidate, no-store',
                                                                              'Access-Control-Allow-Origin'      : u'example.com',
                                                                              'Access-Control-Allow-Headers'     : u'CONTENT-TYPE',
                                                                              'Content-Type'                     : u'application/json',
                                                                              'X-A-HEADER'                       : u'AVALUE',
                                                                              'Content-Length'                   : 56 },
                                                                    mimetype=u'application/json',
                                                                    content_type=u'application/json'),
            })

    def test_route__GET__with_wrapped_method_returning_list(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO"],
                'path'        : '/',
                'return_data' : [ 'foo' , 'bar', 'baz' , 'boop', ],
                'method'      : "GET",
                'best_type'   : 'application/json',
                'decorator'   : route('/', methods=["GET", "POST", "POTATO"], auto_json=True, origin="example.com"),
                'expected'    : IppResponse(response=json.dumps([ 'foo' , 'bar', 'baz' , 'boop', ], indent=4),
                                                                    status=200,
                                                                    headers={ 'Access-Control-Allow-Methods'     : u'GET, POST, POTATO',
                                                                              'Access-Control-Max-Age'           : u'21600',
                                                                              'Cache-Control'                    : u'no-cache, must-revalidate, no-store',
                                                                              'Access-Control-Allow-Origin'      : u'example.com',
                                                                              'Access-Control-Allow-Headers'     : u'CONTENT-TYPE',
                                                                              'Content-Type'                     : u'application/json',
                                                                              'Content-Length'                   : 56 },
                                                                    mimetype=u'application/json',
                                                                    content_type=u'application/json'),
            })

    def test_route__GET__html(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO"],
                'path'        : '/',
                'return_data' : { 'foo' : 'bar', 'baz' : ['boop',] },
                'method'      : "GET",
                'best_type'   : 'text/html',
                'decorator'   : route('/', methods=["GET", "POST", "POTATO"], auto_json=True, headers=["x-not-a-real-header",], origin="example.com"),
                'expected'    : IppResponse(    status=200,
                                                headers={    'Access-Control-Allow-Headers': u'X-NOT-A-REAL-HEADER, CONTENT-TYPE',
                                                             'Access-Control-Max-Age': u'21600',
                                                             'Cache-Control': u'no-cache, must-revalidate, no-store',
                                                             'Access-Control-Allow-Origin': u'example.com',
                                                             'Access-Control-Allow-Methods': u'GET, POST, POTATO',
                                                             'Content-Type': u'text/html; charset=utf-8'},
                                                mimetype=u'text/html',
                                                content_type=u'text/html; charset=utf-8',
                                                direct_passthrough=False),
                'ignore_body' : True
            })

    def test_route__GET__without_matching_type(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO"],
                'path'        : '/',
                'return_data' : { 'foo' : 'bar', 'baz' : ['boop',] },
                'method'      : "GET",
                'best_type'   : TypeError,
                'decorator'   : route('/', methods=["GET", "POST", "POTATO"], auto_json=True, headers=["x-not-a-real-header",], origin="example.com"),
                'expected'    : IppResponse(status=204,
                                            headers={'Access-Control-Allow-Headers': u'X-NOT-A-REAL-HEADER, CONTENT-TYPE',
                                                     'Access-Control-Max-Age': u'21600',
                                                     'Cache-Control': u'no-cache, must-revalidate, no-store',
                                                     'Access-Control-Allow-Origin': u'example.com',
                                                     'Access-Control-Allow-Methods': u'GET, POST, POTATO',
                                                     'Content-Type': u'text/html; charset=utf-8'},
                                            direct_passthrough=False)
            })

    def test_route__GET__with_string_data(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO"],
                'path'        : '/',
                'return_data' : "POTATO",
                'method'      : "GET",
                'decorator'   : route('/', methods=["GET", "POST", "POTATO"], auto_json=True, headers=["x-not-a-real-header",], origin="example.com"),
                'expected'    : IppResponse(response="POTATO",
                                            status=200,
                                            headers={'Content-Length': u'6',
                                                     'Access-Control-Allow-Headers': u'X-NOT-A-REAL-HEADER, CONTENT-TYPE',
                                                     'Access-Control-Max-Age': u'21600',
                                                     'Cache-Control': u'no-cache, must-revalidate, no-store',
                                                     'Access-Control-Allow-Origin': u'example.com',
                                                     'Access-Control-Allow-Methods': u'GET, POST, POTATO',
                                                     'Content-Type': u'text/html; charset=utf-8'}),
            })

    def test_basic_route__GET(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "HEAD"],
                'path'        : '/',
                'return_data' : Response(response=json.dumps({ 'foo' : 'bar', 'baz' : ['boop',] }, indent=4),
                                         status=200,
                                         mimetype=u'application/json',
                                         content_type=u'application/json'),
                'method'      : "GET",
                'decorator'   : basic_route('/'),
                'expected'    : IppResponse(response=json.dumps({ 'foo' : 'bar', 'baz' : ['boop',] }, indent=4),
                                                                    status=200,
                                                                    headers={ 'Access-Control-Allow-Methods'     : u'GET, HEAD, POST',
                                                                              'Access-Control-Max-Age'           : u'21600',
                                                                              'Cache-Control'                    : u'no-cache, must-revalidate, no-store',
                                                                              'Access-Control-Allow-Origin'      : u'*',
                                                                              'Access-Control-Allow-Headers'     : u'CONTENT-TYPE',
                                                                              'Content-Type'                     : u'application/json',
                                                                              'Content-Length'                   : 56 },
                                                                    mimetype=u'application/json',
                                                                    content_type=u'application/json',
                                                                    direct_passthrough=True),
            })

    def test_file_route__GET(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO",],
                'path'        : '/',
                'return_data' : { 'content' : "POJNDCJSL", 'filename' : "afile", "type" : 'zog' },
                'method'      : "GET",
                'best_type'   : 'application/json',
                'decorator'   : file_route('/', methods=["GET", "POST", "POTATO"], headers=["x-not-a-real-header",]),
                'expected'    : IppResponse(response="POJNDCJSL",
                                                                    status=200,
                                                                    headers={ 'Access-Control-Allow-Methods'     : u'GET, POST, POTATO',
                                                                              'Access-Control-Max-Age'           : u'21600',
                                                                              'Cache-Control'                    : u'no-cache, must-revalidate, no-store',
                                                                              'Access-Control-Allow-Origin'      : u'*',
                                                                              'Access-Control-Allow-Headers'     : u'X-NOT-A-REAL-HEADER, CONTENT-TYPE',
                                                                              'Content-Disposition'              : u'attachment; filename=afile.zog' }),
            })

    def test_file_route__GET_with_content_type(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO",],
                'path'        : '/',
                'return_data' : { 'content' : "POJNDCJSL", 'filename' : "afile", "type" : 'zog', "content-type" : "application/zog" },
                'method'      : "GET",
                'best_type'   : 'application/json',
                'decorator'   : file_route('/', methods=["GET", "POST", "POTATO"], headers=["x-not-a-real-header",]),
                'expected'    : IppResponse(response="POJNDCJSL",
                                                                    status=200,
                                                                    headers={ 'Access-Control-Allow-Methods'     : u'GET, POST, POTATO',
                                                                              'Access-Control-Max-Age'           : u'21600',
                                                                              'Cache-Control'                    : u'no-cache, must-revalidate, no-store',
                                                                              'Access-Control-Allow-Origin'      : u'*',
                                                                              'Access-Control-Allow-Headers'     : u'X-NOT-A-REAL-HEADER, CONTENT-TYPE',
                                                                              'Content-Disposition'              : u'attachment; filename=afile.zog',
                                                                              'Content-Type'                     : u'application/zog' }),
            })

    def test_file_route__GET_without_methods(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "HEAD",],
                'path'        : '/',
                'return_data' : { 'content' : "POJNDCJSL", 'filename' : "afile", "type" : 'zog' },
                'method'      : "GET",
                'best_type'   : 'application/json',
                'decorator'   : file_route('/'),
                'expected'    : IppResponse(response="POJNDCJSL",
                                                                    status=200,
                                                                    headers={ 'Access-Control-Allow-Methods'     : u'GET, HEAD',
                                                                              'Access-Control-Max-Age'           : u'21600',
                                                                              'Cache-Control'                    : u'no-cache, must-revalidate, no-store',
                                                                              'Access-Control-Allow-Origin'      : u'*',
                                                                              'Access-Control-Allow-Headers'     : u'CONTENT-TYPE',
                                                                              'Content-Disposition'              : u'attachment; filename=afile.zog' }),
            })

    def test_file_route__GET_without_headers(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO",],
                'path'        : '/',
                'return_data' : { 'content' : "POJNDCJSL", 'filename' : "afile", "type" : 'zog' },
                'method'      : "GET",
                'best_type'   : 'application/json',
                'decorator'   : file_route('/', methods=["GET", "POST", "POTATO"]),
                'expected'    : IppResponse(response="POJNDCJSL",
                                                                    status=200,
                                                                    headers={ 'Access-Control-Allow-Methods'     : u'GET, POST, POTATO',
                                                                              'Access-Control-Max-Age'           : u'21600',
                                                                              'Cache-Control'                    : u'no-cache, must-revalidate, no-store',
                                                                              'Access-Control-Allow-Origin'      : u'*',
                                                                              'Access-Control-Allow-Headers'     : u'CONTENT-TYPE',
                                                                              'Content-Disposition'              : u'attachment; filename=afile.zog' }),
            })

    def test_resource_route__GET(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO",],
                'path'        : '/',
                'return_data' : { 'foo' : 'bar', 'baz' : ['boop',] },
                'method'      : "GET",
                'extract_path': "",
                'decorator'   : resource_route('/', methods=["GET", "POST", "POTATO"]),
                'expected'    : IppResponse(response=json.dumps({ 'foo' : 'bar', 'baz' : ['boop',] }, indent=4),
                                            status=200,
                                            headers={
                                                'Access-Control-Allow-Headers': u'CONTENT-TYPE, API-KEY',
                                                'Access-Control-Max-Age': u'21600',
                                                'Cache-Control': u'no-cache, must-revalidate, no-store',
                                                'Access-Control-Allow-Origin': u'*',
                                                'Access-Control-Allow-Methods': u'GET, POST, POTATO'},
                                            content_type=u'application/json'),
            })

    def test_resource_route__GET_subpath(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO",],
                'path'        : '/',
                'return_data' : { 'foo' : 'bar', 'baz' : ['boop',] },
                'method'      : "GET",
                'extract_path': "foo",
                'decorator'   : resource_route('/', methods=["GET", "POST", "POTATO"]),
                'expected'    : IppResponse(response='"bar"',
                                            status=200,
                                            headers={
                                                'Access-Control-Allow-Headers': u'CONTENT-TYPE, API-KEY',
                                                'Access-Control-Max-Age': u'21600',
                                                'Cache-Control': u'no-cache, must-revalidate, no-store',
                                                'Access-Control-Allow-Origin': u'*',
                                                'Access-Control-Allow-Methods': u'GET, POST, POTATO'},
                                            content_type=u'application/json'),
            })

    def test_resource_route__GET_subpath_with_list(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO",],
                'path'        : '/',
                'return_data' : { 'foo' : 'bar', 'baz' : ['boop',] },
                'method'      : "GET",
                'extract_path': "baz",
                'decorator'   : resource_route('/', methods=["GET", "POST", "POTATO"]),
                'expected'    : IppResponse(response=json.dumps([ "boop" ], indent=4),
                                            status=200,
                                            headers={
                                                'Access-Control-Allow-Headers': u'CONTENT-TYPE, API-KEY',
                                                'Access-Control-Max-Age': u'21600',
                                                'Cache-Control': u'no-cache, must-revalidate, no-store',
                                                'Access-Control-Allow-Origin': u'*',
                                                'Access-Control-Allow-Methods': u'GET, POST, POTATO'},
                                            content_type=u'application/json'),
            })

    def test_resource_route__GET_subpath_with_list_and_subpath(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO",],
                'path'        : '/',
                'return_data' : { 'foo' : 'bar', 'baz' : ['boop',] },
                'method'      : "GET",
                'extract_path': "baz/0",
                'decorator'   : resource_route('/', methods=["GET", "POST", "POTATO"]),
                'expected'    : IppResponse(response=json.dumps("boop", indent=4),
                                            status=200,
                                            headers={
                                                'Access-Control-Allow-Headers': u'CONTENT-TYPE, API-KEY',
                                                'Access-Control-Max-Age': u'21600',
                                                'Cache-Control': u'no-cache, must-revalidate, no-store',
                                                'Access-Control-Allow-Origin': u'*',
                                                'Access-Control-Allow-Methods': u'GET, POST, POTATO'},
                                            content_type=u'application/json'),
            })

    def test_resource_route__GET_subpath_with_unknown_subpath(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO",],
                'path'        : '/',
                'return_data' : { 'foo' : 'bar', 'baz' : ['boop',] },
                'method'      : "GET",
                'extract_path': "tubular",
                'decorator'   : resource_route('/', methods=["GET", "POST", "POTATO"]),
                'expected'    : 404,
            })

    def test_resource_route__GET_subpath_with_unknown_subpath(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO",],
                'path'        : '/',
                'return_data' : { 'foo' : 'bar', 'baz' : ['boop',] },
                'method'      : "GET",
                'extract_path': "tubular",
                'decorator'   : resource_route('/', methods=["GET", "POST", "POTATO"]),
                'expected'    : 404,
            })

    def test_resource_route__GET_subpath_with_unknown_noninteger_list_index(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO",],
                'path'        : '/',
                'return_data' : { 'foo' : 'bar', 'baz' : ['boop',] },
                'method'      : "GET",
                'extract_path': "baz/coop",
                'decorator'   : resource_route('/', methods=["GET", "POST", "POTATO"]),
                'expected'    : 404,
            })

    def test_resource_route__GET_subpath_with_list_index_too_large(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO",],
                'path'        : '/',
                'return_data' : { 'foo' : 'bar', 'baz' : ['boop',] },
                'method'      : "GET",
                'extract_path': "baz/1",
                'decorator'   : resource_route('/', methods=["GET", "POST", "POTATO"]),
                'expected'    : 404,
            })
        
    def test_resource_route__GET_subpath_with_non_jsonic_data(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO",],
                'path'        : '/',
                'return_data' : { 'foo' : 'bar', 'baz' : ['boop', mock.sentinel.BAD_PARAM ] },
                'method'      : "GET",
                'extract_path': "baz/1",
                'decorator'   : resource_route('/', methods=["GET", "POST", "POTATO"]),
                'expected'    : 404,
            })

    def test_resource_route__GET_subpath_with_non_jsonic_data_and_subindex(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO",],
                'path'        : '/',
                'return_data' : { 'foo' : 'bar', 'baz' : ['boop', mock.sentinel.BAD_PARAM ] },
                'method'      : "GET",
                'extract_path': "baz/1/tree",
                'decorator'   : resource_route('/', methods=["GET", "POST", "POTATO"]),
                'expected'    : 404,
            })

    def test_resource_route__GET_subpath_with_empty_object(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO",],
                'path'        : '/',
                'return_data' : { 'foo' : 'bar', 'baz' : ['boop', {} ] },
                'method'      : "GET",
                'extract_path': "baz/1",
                'decorator'   : resource_route('/', methods=["GET", "POST", "POTATO"]),
                'expected'    : IppResponse(response=json.dumps([], indent=4),
                                            status=200,
                                            headers={
                                                'Access-Control-Allow-Headers': u'CONTENT-TYPE, API-KEY',
                                                'Access-Control-Max-Age': u'21600',
                                                'Cache-Control': u'no-cache, must-revalidate, no-store',
                                                'Access-Control-Allow-Origin': u'*',
                                                'Access-Control-Allow-Methods': u'GET, POST, POTATO'},
                                            content_type=u'application/json'),
            })

    def test_resource_route__PUT(self):
        self.perform_test_on_decorator({
                'methods'     : ["GET", "POST", "POTATO",],
                'path'        : '/',
                'return_data' : { 'foo' : 'bar', 'baz' : ['boop', {} ] },
                'method'      : "PUT",
                'extract_path': "baz/1",
                'decorator'   : resource_route('/', methods=["GET", "POST", "POTATO"]),
                'expected'    : IppResponse(response=json.dumps({ 'foo' : 'bar', 'baz' : ['boop', {} ] }, indent=4),
                                            status=200,
                                            headers={
                                                'Access-Control-Allow-Headers': u'CONTENT-TYPE, API-KEY',
                                                'Access-Control-Max-Age': u'21600',
                                                'Cache-Control': u'no-cache, must-revalidate, no-store',
                                                'Access-Control-Allow-Origin': u'*',
                                                'Access-Control-Allow-Methods': u'GET, POST, POTATO'},
                                            content_type=u'application/json'),
            })

    def test_on_json(self):
        """This tests the on_json decorator which is used for websocket end-points and so has a slightly different
        structure from that of the other decorators."""
        m = mock.MagicMock(name="webapi")
        (f, UUT, calls) = self.initialise_webapi_with_method_using_decorator(m, on_json('/'), is_socket=True)

        socket_uuid = "05f1c8da-dc36-11e7-af05-7fe527dcf7ab"
        with mock.patch("uuid.uuid4", return_value=socket_uuid):
            m.side_effect = lambda ws,msg : self.assertIn(socket_uuid, UUT.socks)
            ws = mock.MagicMock(name="ws")
            ws.receive.side_effect = [ json.dumps({ "foo" : "bar", "baz" : [ "boop", ] }), Exception ]

            f(ws)

            self.assertListEqual(ws.receive.mock_calls, [ mock.call(), mock.call() ])

            m.assert_called_once_with(ws, { "foo" : "bar", "baz" : [ "boop", ] })

    def test_on_json_with_on_websocket_connect(self):
        """This tests the on_json decorator which is used for websocket end-points and so has a slightly different
        structure from that of the other decorators, it checks the behaviour when an alternative on_websocket_connect
        method is specified in the class."""
        m = mock.MagicMock(name="webapi")
        on_websocket_connect = mock.MagicMock(name="on_websocket_connect")
        (f, UUT, calls) = self.initialise_webapi_with_method_using_decorator(m, on_json('/'), is_socket=True, on_websocket_connect=on_websocket_connect)

        on_websocket_connect.assert_called_once_with(UUT, mock.ANY)
        self.assertEqual(f, on_websocket_connect.return_value)
        f = on_websocket_connect.call_args[0][1]

        socket_uuid = "05f1c8da-dc36-11e7-af05-7fe527dcf7ab"
        with mock.patch("uuid.uuid4", return_value=socket_uuid):
            ws = mock.MagicMock(name="ws")

            f(ws, json.dumps({ "foo" : "bar", "baz" : [ "boop", ] }))

            m.assert_called_once_with(ws, { "foo" : "bar", "baz" : [ "boop", ] })

    def test_on_json_with_grain_event_wrapper(self):
        """This tests the on_json decorator which is used for websocket end-points and so has a slightly different
        structure from that of the other decorators."""
        m = mock.MagicMock(name="webapi", __name__="webapi")
        (f, UUT, calls) = self.initialise_webapi_with_method_using_decorator(grain_event_wrapper(m), on_json('/'), is_socket=True)

        socket_uuid = "05f1c8da-dc36-11e7-af05-7fe527dcf7ab"
        with mock.patch("uuid.uuid4", return_value=socket_uuid):
            m.side_effect = lambda ws,msg : msg
            ws = mock.MagicMock(name="ws")
            ws.receive.side_effect = [ json.dumps({ "grain" : { "event_payload" : { "data" : [ {"post" : { "foo" : "bar", "baz" : [ "boop", ] } } ] } } }), Exception ]

            f(ws)

            self.assertListEqual(ws.receive.mock_calls, [ mock.call(), mock.call() ])

            m.assert_called_once_with(ws, { "foo" : "bar", "baz" : [ "boop", ] })
            print(ws.receive.send.mock_calls)

    @mock.patch("nmoscommon.webapi.Flask")
    @mock.patch("nmoscommon.webapi.Sockets")
    def assert_default_errorhandler_handles(self, Sockets, Flask, exc=None, status_code=404, description="", expected=None, method="GET", expect_html=False):
        """The method error is the default error handler. It's not a route decorator so we can't use the fixtures we set up for those."""
        self.maxDiff = None
        class StubWebAPI(WebAPI):
            pass
        app = Flask.return_value
        app.errorhandler.side_effect = lambda n : getattr(app, 'error_handler_for_' + str(n))
        UUT = StubWebAPI()
        Flask.assert_called_once_with('nmoscommon.webapi')
        expected_calls = [ mock.call(n) for n in range(400, 600) ]
        # This checks that all expected elements are in the list, but doesn't mind if the list has extra elements
        self.assertCountEqual([ call for call in app.errorhandler.mock_calls if call[0] == '' and call in expected_calls ],  expected_calls)
        f = getattr(app, 'error_handler_for_' + str(status_code)).call_args[0][0]
        for n in range(400, 600):
            getattr(app, 'error_handler_for_' + str(n)).assert_called_once_with(mock.ANY)
            self.assertEqual(getattr(app, 'error_handler_for_' + str(n)).call_args[0][0].__name__, f.__name__)

        if exc is None:
            exc = HTTPException()
            exc.code = status_code
            exc.description = description
        try:
            raise exc
        except Exception as e:
            t, v, tb = sys.exc_info()
            if expected is None:
                if method == 'HEAD' and isinstance(e, HTTPException):
                    expected = IppResponse('', status=e.code, headers={'Access-Control-Allow-Methods': u'DELETE, GET, HEAD, OPTIONS, POST, PUT'})
                elif method == 'HEAD':
                    expected = IppResponse('', status=500, headers={'Access-Control-Allow-Methods': u'DELETE, GET, HEAD, OPTIONS, POST, PUT'})
                elif expect_html and isinstance(e, HTTPException) and status_code != 400:
                    expected = e.get_response()
                    expected.headers['Access-Control-Allow-Methods'] = u'DELETE, GET, HEAD, OPTIONS, POST, PUT'
                    expected.headers['Access-Control-Allow-Origin']  = u'*'
                    expected.headers['Access-Control-Max-Age']       = u'21600'
                elif expect_html:
                    expected = IppResponse(response='',
                                            status=status_code,
                                            headers={'Access-Control-Allow-Methods': u'DELETE, GET, HEAD, OPTIONS, POST, PUT'},
                                            content_type=u'text/html; charset=utf-8')
                else:
                    expected = IppResponse(response=json.dumps({
                        "debug" : {
                            'traceback': [str(x) for x in traceback.extract_tb(tb)],
                            'exception': [str(x) for x in traceback.format_exception_only(t, v)]
                        },
                        "code" : status_code,
                        "error" : description
                        }),
                        status=status_code,
                        headers={'Access-Control-Allow-Methods': u'DELETE, GET, HEAD, OPTIONS, POST, PUT'},
                        content_type=u'application/json')
            self.assert_wrapped_route_method_returns(f,
                                                    expected,
                                                    method=method,
                                                    args=[e,],
                                                    best_mimetype="application/json" if not expect_html else "text/html",
                                                    ignore_body=True)

    def test_default_errorhandler__404(self):
        self.assert_default_errorhandler_handles(status_code=404, description="Not Found", method="GET")

    def test_default_errorhandler__HEAD(self):
        self.assert_default_errorhandler_handles(status_code=404, description="Not Found", method="HEAD")

    def test_default_errorhandler__Exception_triggers_500(self):
        self.assert_default_errorhandler_handles(exc=Exception("Uncaught Exception"), status_code=500, description="Internal Error", method="GET")

    def test_default_errorhandler__Exception_triggers_500__HEAD(self):
        self.assert_default_errorhandler_handles(exc=Exception("Uncaught Exception"), status_code=500, description="Internal Error", method="HEAD")

    def test_default_errorhandler__Exception_triggers_500_expecting_html(self):
        self.assert_default_errorhandler_handles(exc=Exception("Uncaught Exception"), status_code=500, description="Internal Error", method="GET", expect_html=True)

    def test_default_errorhandler__404_expecting_html(self):
        self.assert_default_errorhandler_handles(status_code=404, description="Not Found", method="GET", expect_html=True)

    def test_default_errorhandler__400_expecting_html(self):
        self.assert_default_errorhandler_handles(status_code=400, description="User Error", method="GET", expect_html=True)

    def test_default_authorize_falls_back_when_no_oauth_set(self):
        """In point of fact it should never even be called under this circumstance, but belt and braces isn't bad."""
        class StubWebAPI(WebAPI):
            def __init__(self, *args, **kwargs):
                super(StubWebAPI, self).__init__(*args, **kwargs)
                self._oauth_config = None
        UUT = StubWebAPI()
        self.assertTrue(UUT.default_authorize(mock.sentinel.token))

    def test_default_authenticate_falls_back_when_no_oauth_set(self):
        """In point of fact it should never even be called under this circumstance, but belt and braces isn't bad."""
        class StubWebAPI(WebAPI):
            def __init__(self, *args, **kwargs):
                super(StubWebAPI, self).__init__(*args, **kwargs)
                self._oauth_config = None
        UUT = StubWebAPI()
        self.assertTrue(UUT.default_authenticate(mock.sentinel.token))

    def test_default_authenticate_fails_on_null_token(self):
        """In point of fact it should never even be called under this circumstance, but belt and braces isn't bad."""
        class StubWebAPI(WebAPI):
            def __init__(self, *args, **kwargs):
                super(StubWebAPI, self).__init__(*args, **kwargs)
                self._oauth_config = { 'loginserver' : mock.sentinel.loginserver,
                                           'proxies' : mock.sentinel.proxies }
        UUT = StubWebAPI()
        self.assertFalse(UUT.default_authenticate(None))

    @mock.patch('nmoscommon.flask_cors.make_response')
    @mock.patch('nmoscommon.webapi.request')
    @mock.patch("nmoscommon.webapi.Flask")
    @mock.patch("nmoscommon.webapi.Sockets")
    def test_default_301_handler_redirects(self, Sockets, Flask, request, make_response):
        """The method __redirect is the default 301 handler."""
        self.maxDiff = None
        class StubWebAPI(WebAPI):
            pass
        app = Flask.return_value
        app.errorhandler.side_effect = lambda n : getattr(app, 'error_handler_for_' + str(n))
        UUT = StubWebAPI()
        Flask.assert_called_once_with('nmoscommon.webapi')
        f = app.error_handler_for_301.call_args[0][0]

        with mock.patch('nmoscommon.flask_cors.request', request):
            e = mock.MagicMock(name="301Error")
            f(e)
            make_response.assert_called_once_with(e.get_response.return_value)
            e.get_response.assert_called_once_with(request.environ)

    @mock.patch('nmoscommon.webapi.config', {'node_hostname' : 'example.com', 'https_mode' : 'enabled'})
    @mock.patch('nmoscommon.webapi.request', headers={ 'X-Forwarded-Path' : '/dummy/path', 'X-Forwarded-Proto' : 'ftp' }, url="ntp://potato.xxx/hot/potatoes/")
    def test_htmlify(self, request):
        """The method htmlify should covert json into html."""
        r = [ 'foo/', 'bar/', 'baz/', "boop" ]
        resp = htmlify(r, 'application/json')
        self.assertEqual(resp.status_code, 200)
        html = str(resp.get_data())

        base_url = "https://example.com"

        self.assertRegexpMatches(html, r'<h2><a href="' + re.escape(base_url + '/') + r'">' + re.escape(base_url) + r'</a>/<a href="' + re.escape(base_url + '/dummy') + r'">dummy</a>/<a href="' + re.escape(base_url + '/dummy/path') + r'">path</a></h2>',
                                     msg="html output does not contain the expected h2 element for the title")
        self.assertRegexpMatches(html, r'<a href="\./foo/?">foo/?</a>',
                                     msg="html output has not converted a list entry with a trailing slash into a link")
        self.assertNotRegexpMatches(html, r'<a href="\./boop/?">boop/?</a>',
                                     msg="html output contains a link for an entry that lacked a trailing slash, this is wrong")
