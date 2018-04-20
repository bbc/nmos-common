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

import unittest
import mock
import json
from six import StringIO, PY2
from uuid import UUID
from nmoscommon.timestamp import Timestamp, TimeOffset
from fractions import Fraction

from nmoscommon import json as nmos_json


PURE_JSON_DATA = {
    "foo": "bar",
    "baz": ["boop", "beep"],
    "boggle": {"cat": u"\u732b",
               "kitten": u"\u5b50\u732b"},
    "numeric": 25,
    "boolean": True,
    "decimal": 0.44
}

PURE_JSON_STRING = '{"foo": "bar", "baz": ["boop", "beep"], "boggle": {"cat": "\\u732b", "kitten": "\\u5b50\\u732b"}, "numeric": 25, "boolean": true, "decimal": 0.44}'

NMOS_JSON_DATA = {
    "foo": "bar",
    "baz": ["boop", "beep"],
    "boggle": {"cat": u"\u732b",
               "kitten": u"\u5b50\u732b"},
    "numeric": 25,
    "boolean": True,
    "decimal": 0.44,
    "uuid": UUID("b8b4a34f-3293-11e8-89c0-acde48001122"),
    "rational": Fraction(30000,1001),
    "timestamp": Timestamp.from_sec_nsec("417798915:0"),
    "timeoffset": TimeOffset.from_sec_nsec("-13:0")
}

NMOS_JSON_STRING = '{"foo": "bar", "baz": ["boop", "beep"], "boggle": {"cat": "\\u732b", "kitten": "\\u5b50\\u732b"}, "numeric": 25, "boolean": true, "decimal": 0.44, "uuid": "b8b4a34f-3293-11e8-89c0-acde48001122", "rational": {"numerator": 30000, "denominator": 1001}, "timestamp": "417798915:0", "timeoffset": "-13:0"}'


class Unserialisable(object):
    pass


class TestJSON(unittest.TestCase):
    def test_dump_pure_json(self):
        fp = StringIO()

        nmos_json.dump(PURE_JSON_DATA, fp)

        decoded = json.loads(fp.getvalue())
        self.assertEqual(PURE_JSON_DATA, decoded)

    def test_dump_pure_json_with_positional_none(self):
        fp = StringIO()

        if PY2:
            nmos_json.dump(PURE_JSON_DATA, fp, False,
                           True, True, True, None, None,
                           None, "utf-8", None, False)
        else:
            nmos_json.dump(PURE_JSON_DATA, fp, False,
                           True, True, True, None, None,
                           None, None, False)

        decoded = json.loads(fp.getvalue())
        self.assertEqual(PURE_JSON_DATA, decoded)

    def test_dumps_pure_json(self):
        encoded = nmos_json.dumps(PURE_JSON_DATA)
        decoded = json.loads(encoded)

        self.assertEqual(PURE_JSON_DATA, decoded)

    def test_dumps_pure_json_with_positional_none(self):
        if PY2:
            encoded = nmos_json.dumps(PURE_JSON_DATA, False,
                                      True, True, True, None,
                                      None, None, "utf-8",
                                      None, False)
        else:
            encoded = nmos_json.dumps(PURE_JSON_DATA, False,
                                      True, True, True, None,
                                      None, None, None, False)
        decoded = json.loads(encoded)

        self.assertEqual(PURE_JSON_DATA, decoded)

    def test_load_pure_json(self):
        fp = StringIO(PURE_JSON_STRING)

        decoded = nmos_json.load(fp)

        self.assertEqual(PURE_JSON_DATA, decoded)

    def test_load_pure_json_with_positional_none(self):
        fp = StringIO(PURE_JSON_STRING)

        if PY2:
            decoded = nmos_json.load(fp, 'utf-8', None, None, None, None, None, None)
        else:
            decoded = nmos_json.load(fp, None, None, None, None, None, None)

        self.assertEqual(PURE_JSON_DATA, decoded)

    def test_loads_pure_json(self):
        decoded = nmos_json.loads(PURE_JSON_STRING)

        self.assertEqual(PURE_JSON_DATA, decoded)

    def test_loads_pure_json_with_positional_none(self):
        if PY2:
            decoded = nmos_json.loads(PURE_JSON_STRING, 'utf-8', None, None, None, None, None, None)
        else:
            decoded = nmos_json.loads(PURE_JSON_STRING, None, None, None, None, None, None)

        self.assertEqual(PURE_JSON_DATA, decoded)

    def test_dump_nmos_json(self):
        fp = StringIO()

        nmos_json.dump(NMOS_JSON_DATA, fp)

        decoded = nmos_json.loads(fp.getvalue())
        self.assertEqual(NMOS_JSON_DATA, decoded)

    def test_dump_nmos_json_with_positional_none(self):
        fp = StringIO()

        if PY2:
            nmos_json.dump(NMOS_JSON_DATA, fp, False,
                           True, True, True, None, None,
                           None, "utf-8", None, False)
        else:
            nmos_json.dump(NMOS_JSON_DATA, fp, False,
                           True, True, True, None, None,
                           None, None, False)

        decoded = nmos_json.loads(fp.getvalue())
        self.assertEqual(NMOS_JSON_DATA, decoded)

    def test_dumps_nmos_json(self):
        encoded = nmos_json.dumps(NMOS_JSON_DATA)
        decoded = nmos_json.loads(encoded)

        self.assertEqual(NMOS_JSON_DATA, decoded)

    def test_dumps_nmos_json_with_positional_none(self):
        if PY2:
            encoded = nmos_json.dumps(NMOS_JSON_DATA, False,
                                      True, True, True, None,
                                      None, None, "utf-8",
                                      None, False)
        else:
            encoded = nmos_json.dumps(NMOS_JSON_DATA, False,
                                      True, True, True, None,
                                      None, None, None, False)
        decoded = nmos_json.loads(encoded)

        self.assertEqual(NMOS_JSON_DATA, decoded)

    def test_load_nmos_json(self):
        fp = StringIO(NMOS_JSON_STRING)

        decoded = nmos_json.load(fp)

        self.assertEqual(NMOS_JSON_DATA, decoded)

    def test_load_nmos_json_with_positional_none(self):
        fp = StringIO(NMOS_JSON_STRING)

        if PY2:
            decoded = nmos_json.load(fp, 'utf-8', None, None, None, None, None, None)
        else:
            decoded = nmos_json.load(fp, None, None, None, None, None, None)

        self.assertEqual(NMOS_JSON_DATA, decoded)

    def test_loads_nmos_json(self):
        decoded = nmos_json.loads(NMOS_JSON_STRING)

        self.assertEqual(NMOS_JSON_DATA, decoded)

    def test_loads_nmos_json_with_positional_none(self):
        decoded = nmos_json.loads(NMOS_JSON_STRING, 'utf-8', None, None, None, None, None, None)

        self.assertEqual(NMOS_JSON_DATA, decoded)

    def test_dump_fails_to_serialise_non_serialisable(self):
        fp = StringIO()

        with self.assertRaises(TypeError):
            nmos_json.dump(Unserialisable(), fp)

    def test_dumps_fails_to_serialise_non_serialisable(self):
        with self.assertRaises(TypeError):
            nmos_json.dumps(Unserialisable())
