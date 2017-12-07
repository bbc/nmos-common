#! /usr/bin/python

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

from nmoscommon.webapi import *

from datetime import timedelta

import flask

class TestWebAPI(unittest.TestCase):

    @mock.patch("nmoscommon.webapi.Flask")
    @mock.patch("nmoscommon.webapi.Sockets")
    def initialise_webapi_with_method_using_decorator(self, mock_webapi_method, decorator, Sockets, Flask, oauth_userid=None):
        """Returns a pair of the wrapped function that would be sent to flask.app.route, and the parameters which would
        be passed to flask.app.route for it."""
        def TEST(self):
            return mock_webapi_method()

        class StubWebAPI(WebAPI):
            pass

        StubWebAPI.TEST = decorator(TEST)
        basemethod = StubWebAPI.TEST

        UUT = StubWebAPI()
        if oauth_userid is not None:
            UUT._oauth_config = { "loginserver" : "LOGINSERVER", "proxies" : { "http" : "HHTPPROXY", "https" : "HTTPSPROXY" }, 'access_whitelist' : [ oauth_userid, ] }
        Flask.assert_called_once_with('nmoscommon.webapi')
        app = Flask.return_value

        self.assertEqual(app.response_class, IppResponse)
        app.before_first_request.assert_called_once_with(mock.ANY)
        torun = app.before_first_request.call_args[0][0]
        Sockets.assert_called_once_with(app)
        app.route.assert_called_once_with('/',
                                              endpoint="_TEST",
                                              methods=basemethod.app_methods + ["OPTIONS"])
        app.route.return_value.assert_called_once_with(mock.ANY)
        return (app.route.return_value.call_args[0][0], UUT, app.route.call_args)

    @mock.patch('nmoscommon.webapi.http.urlopen')
    @mock.patch('nmoscommon.webapi.http.install_opener')
    @mock.patch('nmoscommon.flask_cors.make_response', side_effect=lambda x:x)
    @mock.patch('nmoscommon.flask_cors.request')
    def assert_wrapped_route_method_returns(self, f, expected, request, make_response, install_opener, urlopen, method="GET", args=[], kwargs={}, best_mimetype='application/json', request_headers=None, oauth_userid=None, oauth_token=None):
        with mock.patch('nmoscommon.webapi.request', request):
            if oauth_userid is not None:
                # this method is called by the default_authorizer when oauth credentials are checked
                urlopen.return_value.read.return_value = json.dumps({ 'userid' : oauth_userid, 'token' : oauth_token })
                urlopen.return_value.code = 200
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

            r = f(*args, **kwargs)

            self.assertEqual(r, expected, msg="""

Expected IppResponse(response=%r,\n status=%r,\n headers=%r,\n mimetype=%r,\n content_type=%r\n, direct_passthrough=%r)

Got IppResponse(response=%r,\n status=%r,\n headers=%r,\n mimetype=%r,\n content_type=%r,\n direct_passthrough=%r)""" % (expected.get_data(),
                                                                                                                             expected.status,
                                                                                                                             dict(expected.headers),
                                                                                                                             expected.mimetype,
                                                                                                                             expected.content_type,
                                                                                                                             expected.direct_passthrough,
                                                                                                                             r.get_data(),
                                                                                                                             r.status,
                                                                                                                             dict(r.headers),
                                                                                                                             r.mimetype,
                                                                                                                             r.content_type,
                                                                                                                             r.direct_passthrough))

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
                         any result will be acceptable.

        Optional Keys:

        'headers'         -- These headers will be included in the mock request when the wrapped method is called.
        'oauth_userid'    -- if present then the call will be performed in a mock Flask environment which implements oauth, and this value will be returned by the mock 
                             credentials server as an acceptable user id.
        'oauth_whitelist' -- if present when 'oauth_userid' is also specified then this value will be added to the mock whitelist of acceptable user ids. If not specified then
                             the value of 'oauth_userid' will be put on this whitelist instead.
        'oauth_token      -- if present when 'oauth_userid' is also specified then this value will be returned by the mock credentials server as an acceptable authorisation token.
        'best_type'       -- If the code attempts to determine what the best mime-type to use for a return format then it will be given this value,
                             alternatively set this to TypeError to mimick the behaviour when none of the acceptible types is available.
"""
        method = mock.MagicMock(name="webapi", return_value=data['return_data'])

        (f, UUT, (args, kwargs)) = self.initialise_webapi_with_method_using_decorator(method, data['decorator'], oauth_userid=data.get('oauth_whitelist',data.get('oauth_userid', None)))
         # Check that flask was given through the expected commands
        self.assertEqual(args[0], data['path'])
        self.assertEqual(kwargs['endpoint'], "_TEST")
        self.assertEqual(kwargs['methods'], data['methods'] + ["OPTIONS"])

        self.assert_wrapped_route_method_returns(f, data['expected'],
                                                     method=data.get('method',"GET"),
                                                     best_mimetype=data.get('best_type',None),
                                                     request_headers=data.get('headers',None),
                                                     oauth_userid=data.get('oauth_userid', None),
                                                     oauth_token=data.get('oauth_token',None))

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
                'expected'    : IppResponse(response=u'<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN"\n   "http://www.w3.org/TR/html4/strict.dtd">\n\n<html>\n<head>\n  <title><a href="://example.com/">://example.com</a></title>\n  <meta http-equiv="content-type" content="text/html; charset=None">\n  <style type="text/css">\ntd.linenos { background-color: #f0f0f0; padding-right: 10px; }\nspan.lineno { background-color: #f0f0f0; padding: 0 5px 0 5px; }\npre { line-height: 125%; }\nbody .hll { background-color: #ffffcc }\nbody  { background: #f8f8f8; }\nbody .c { color: #408080; font-style: italic } /* Comment */\nbody .err { border: 1px solid #FF0000 } /* Error */\nbody .k { color: #008000; font-weight: bold } /* Keyword */\nbody .o { color: #666666 } /* Operator */\nbody .ch { color: #408080; font-style: italic } /* Comment.Hashbang */\nbody .cm { color: #408080; font-style: italic } /* Comment.Multiline */\nbody .cp { color: #BC7A00 } /* Comment.Preproc */\nbody .cpf { color: #408080; font-style: italic } /* Comment.PreprocFile */\nbody .c1 { color: #408080; font-style: italic } /* Comment.Single */\nbody .cs { color: #408080; font-style: italic } /* Comment.Special */\nbody .gd { color: #A00000 } /* Generic.Deleted */\nbody .ge { font-style: italic } /* Generic.Emph */\nbody .gr { color: #FF0000 } /* Generic.Error */\nbody .gh { color: #000080; font-weight: bold } /* Generic.Heading */\nbody .gi { color: #00A000 } /* Generic.Inserted */\nbody .go { color: #888888 } /* Generic.Output */\nbody .gp { color: #000080; font-weight: bold } /* Generic.Prompt */\nbody .gs { font-weight: bold } /* Generic.Strong */\nbody .gu { color: #800080; font-weight: bold } /* Generic.Subheading */\nbody .gt { color: #0044DD } /* Generic.Traceback */\nbody .kc { color: #008000; font-weight: bold } /* Keyword.Constant */\nbody .kd { color: #008000; font-weight: bold } /* Keyword.Declaration */\nbody .kn { color: #008000; font-weight: bold } /* Keyword.Namespace */\nbody .kp { color: #008000 } /* Keyword.Pseudo */\nbody .kr { color: #008000; font-weight: bold } /* Keyword.Reserved */\nbody .kt { color: #B00040 } /* Keyword.Type */\nbody .m { color: #666666 } /* Literal.Number */\nbody .s { color: #BA2121 } /* Literal.String */\nbody .na { color: #7D9029 } /* Name.Attribute */\nbody .nb { color: #008000 } /* Name.Builtin */\nbody .nc { color: #0000FF; font-weight: bold } /* Name.Class */\nbody .no { color: #880000 } /* Name.Constant */\nbody .nd { color: #AA22FF } /* Name.Decorator */\nbody .ni { color: #999999; font-weight: bold } /* Name.Entity */\nbody .ne { color: #D2413A; font-weight: bold } /* Name.Exception */\nbody .nf { color: #0000FF } /* Name.Function */\nbody .nl { color: #A0A000 } /* Name.Label */\nbody .nn { color: #0000FF; font-weight: bold } /* Name.Namespace */\nbody .nt { color: #008000; font-weight: bold } /* Name.Tag */\nbody .nv { color: #19177C } /* Name.Variable */\nbody .ow { color: #AA22FF; font-weight: bold } /* Operator.Word */\nbody .w { color: #bbbbbb } /* Text.Whitespace */\nbody .mb { color: #666666 } /* Literal.Number.Bin */\nbody .mf { color: #666666 } /* Literal.Number.Float */\nbody .mh { color: #666666 } /* Literal.Number.Hex */\nbody .mi { color: #666666 } /* Literal.Number.Integer */\nbody .mo { color: #666666 } /* Literal.Number.Oct */\nbody .sb { color: #BA2121 } /* Literal.String.Backtick */\nbody .sc { color: #BA2121 } /* Literal.String.Char */\nbody .sd { color: #BA2121; font-style: italic } /* Literal.String.Doc */\nbody .s2 { color: #BA2121 } /* Literal.String.Double */\nbody .se { color: #BB6622; font-weight: bold } /* Literal.String.Escape */\nbody .sh { color: #BA2121 } /* Literal.String.Heredoc */\nbody .si { color: #BB6688; font-weight: bold } /* Literal.String.Interpol */\nbody .sx { color: #008000 } /* Literal.String.Other */\nbody .sr { color: #BB6688 } /* Literal.String.Regex */\nbody .s1 { color: #BA2121 } /* Literal.String.Single */\nbody .ss { color: #19177C } /* Literal.String.Symbol */\nbody .bp { color: #008000 } /* Name.Builtin.Pseudo */\nbody .vc { color: #19177C } /* Name.Variable.Class */\nbody .vg { color: #19177C } /* Name.Variable.Global */\nbody .vi { color: #19177C } /* Name.Variable.Instance */\nbody .il { color: #666666 } /* Literal.Number.Integer.Long */\n\n  </style>\n</head>\n<body>\n<h2><a href="://example.com/">://example.com</a></h2>\n\n<table class="highlighttable"><tr><td class="linenos"><div class="linenodiv"><pre>1\n2\n3\n4\n5\n6</pre></div></td><td class="code"><div class="highlight"><pre><span class="p">{</span>\n    <span class="nt">&quot;foo&quot;</span><span class="p">:</span> <span class="s2">&quot;bar&quot;</span><span class="p">,</span> \n    <span class="nt">&quot;baz&quot;</span><span class="p">:</span> <span class="p">[</span>\n        <span class="s2">&quot;boop&quot;</span>\n    <span class="p">]</span>\n<span class="p">}</span>\n</pre></div>\n</td></tr></table></body>\n</html>\n',
                                                status=200,
                                                headers={'Content-Length': u'4956',
                                                             'Access-Control-Allow-Headers': u'X-NOT-A-REAL-HEADER, CONTENT-TYPE, TOKEN',
                                                             'Access-Control-Max-Age': u'21600',
                                                             'Cache-Control': u'no-cache, must-revalidate, no-store',
                                                             'Access-Control-Allow-Origin': u'example.com',
                                                             'Access-Control-Allow-Methods': u'GET, POST, POTATO',
                                                             'Content-Type': u'text/html; charset=utf-8'},
                                                mimetype=u'text/html',
                                                content_type=u'text/html; charset=utf-8',
                                                direct_passthrough=False)
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
