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

from six import string_types
from six import PY2
from flask import Flask
from datetime import timedelta

import unittest
import mock
from nmoscommon.flask_cors import crossdomain


class TestCrossDomain(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestCrossDomain, self).__init__(*args, **kwargs)
        self.app = Flask(__name__)
        if PY2:
            self.assertCountEqual = self.assertItemsEqual

    def assert_crossdomain_call_correct(self, method, methods=None, headers=None,
                                        max_age=21600, attach_to_all=True,
                                        origin="localhost", automatic_options=True):
        args = [mock.sentinel.arg1, mock.sentinel.arg2]
        kwargs = {
            "kw1": mock.sentinel.kwarg1,
            "kw2": mock.sentinel.kwarg2
        }

        F = mock.MagicMock()

        def test_function(*args, **kwargs):
            return F(*args, **kwargs)

        wrapped = crossdomain(methods=methods, headers=headers,
                              max_age=max_age, attach_to_all=attach_to_all,
                              origin=origin, automatic_options=automatic_options)(test_function)

        with self.app.test_request_context('/', base_url=None, headers=headers, method=method):
            with mock.patch('nmoscommon.flask_cors.make_response') as make_response:
                with mock.patch.object(self.app, 'make_default_options_response') as mock_default_options_response:

                    # This makes the headers entry behave like a dict, but
                    # returning new MagicMocks whenever an empry entry is needed
                    resp_headers = {}
                    def_opt_headers = {}

                    def getitem(d):
                        def __inner(key):
                            if key not in d:
                                d.__setitem__(key, mock.MagicMock(name="resp_headers[" + repr(key) + "]"))
                            return d.__getitem__(key)
                        return __inner

                    def setitem(d):
                        def __inner(key, value):
                            d.__setitem__(key, value)
                        return __inner

                    mock_default_options_response.return_value.headers.__getitem__.side_effect = getitem(def_opt_headers)
                    mock_default_options_response.return_value.headers.__setitem__.side_effect = setitem(def_opt_headers)

                    make_response.return_value.headers.__getitem__.side_effect = getitem(resp_headers)
                    make_response.return_value.headers.__setitem__.side_effect = setitem(resp_headers)

                    resp = wrapped(*args, **kwargs)

                    if methods is not None:
                        methods = ', '.join(sorted(x.upper() for x in methods))
                    if headers is not None and not isinstance(headers, string_types):
                        headers = ', '.join(x.upper() for x in headers)
                    if not isinstance(origin, string_types):
                        origin = ', '.join(origin)
                    if isinstance(max_age, timedelta):
                        max_age = max_age.total_seconds()

                    if methods is None:
                        methods = mock_default_options_response.return_value.headers["allow"]

                    if automatic_options and method == "OPTIONS":
                        self.assertEqual(resp, mock_default_options_response.return_value)
                        h = def_opt_headers
                    else:
                        self.assertEqual(resp, make_response.return_value)
                        make_response.assert_called_once_with(F.return_value)
                        F.assert_called_once_with(*args, **kwargs)
                        h = resp_headers

                    if not attach_to_all and method != "OPTIONS":
                        self.assertCountEqual(h.keys(), [])
                    else:
                        self.assertEqual(h['Access-Control-Allow-Origin'], origin)
                        self.assertEqual(h['Access-Control-Allow-Methods'], methods)
                        self.assertEqual(h['Access-Control-Max-Age'], str(max_age))
                        if headers is not None:
                            self.assertEqual(h['Access-Control-Allow-Headers'], headers)

    def test_automatic_options(self):
        self.assert_crossdomain_call_correct("OPTIONS", automatic_options=True)

    def test_methods_overrides_automatic_options(self):
        self.assert_crossdomain_call_correct(
            "OPTIONS", automatic_options=True, methods=["GET", "PUT", "POTATO"])

    def test_headers_passed_through_in_automatic_options(self):
        self.assert_crossdomain_call_correct("OPTIONS", automatic_options=True, headers={"foo": "bar"})

    def test_options_without_automatic_options(self):
        self.assert_crossdomain_call_correct("OPTIONS", automatic_options=False)

    def test_get(self):
        self.assert_crossdomain_call_correct("GET")

    def test_methods_overrides_get(self):
        self.assert_crossdomain_call_correct("GET", methods=["GET", "PUT", "POTATO"])

    def test_headers_passed_through_in_get(self):
        self.assert_crossdomain_call_correct("GET", headers={"foo": "bar"})

    def test_get_not_modified_unless_attach_to_all_set(self):
        self.assert_crossdomain_call_correct("GET", attach_to_all=False)

    def test_can_handle_list_origin(self):
        self.assert_crossdomain_call_correct("GET", origin=["foo", "bar"])

    def test_can_handle_timedelta_max_age(self):
        self.assert_crossdomain_call_correct("GET", max_age=timedelta(20))
