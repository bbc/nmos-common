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

"""
This module contains methods and classes to extend json encoding and decoding
to cover timestamps, uuids, and fractions.

To make use of it either use the dumps, loads, dump, and load functions in
place of the versions from the standard json module, or use the classes
NMOSJSONEncoder and NMOSJSONDecoder as your encoder and decoder classes.
"""

import uuid
import json
from json import JSONEncoder, JSONDecoder
from fractions import Fraction
from six import string_types
import re

from .timestamp import Timestamp, TimeOffset

__all__ = ["dump", "dumps", "load", "loads",
           "JSONEncoder", "JSONDecoder",
           "NMOSJSONEncoder", "NMOSJSONDecoder"]


UUID_REGEX = re.compile(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}')


def dump(*args, **kwargs):
    if 'cls' not in kwargs and len(args) < 7:
        kwargs['cls'] = NMOSJSONEncoder
    elif len(args) >= 7 and args[6] is None:
        args = args[0:6] + [NMOSJSONEncoder] + args[7:]
    return json.dump(*args, **kwargs)


def dumps(*args, **kwargs):
    if 'cls' not in kwargs and len(args) < 6:
        kwargs['cls'] = NMOSJSONEncoder
    elif len(args) >= 6 and args[5] is None:
        args = args[0:5] + [NMOSJSONEncoder] + args[6:]
    return json.dumps(*args, **kwargs)


def load(*args, **kwargs):
    if 'cls' not in kwargs and len(args) < 3:
        kwargs['cls'] = NMOSJSONDecoder
    elif len(args) >= 3 and args[2] is None:
        args = args[0:2] + [NMOSJSONDecoder] + args[3:]
    return json.load(*args, **kwargs)


def loads(*args, **kwargs):
    if 'cls' not in kwargs and len(args) < 3:
        kwargs['cls'] = NMOSJSONDecoder
    elif len(args) >= 3 and args[2] is None:
        args = args[0:2] + [NMOSJSONDecoder] + args[3:]
    return json.loads(*args, **kwargs)


class NMOSJSONEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, uuid.UUID):
            return str(o)
        elif isinstance(o, Timestamp):
            return o.to_tai_sec_nsec()
        elif isinstance(o, TimeOffset):
            return o.to_sec_nsec()
        elif isinstance(o, Fraction):
            return {"numerator": o.numerator,
                    "denominator": o.denominator}
        else:
            return super(NMOSJSONEncoder, self).default(o)


class NMOSJSONDecoder(JSONDecoder):
    def raw_decode(self, s, *args, **kwargs):
        (value, offset) = super(NMOSJSONDecoder, self).raw_decode(s,
                                                                  *args,
                                                                  **kwargs)
        value = self._reinterpret_object(value)
        return (value, offset)

    def _reinterpret_object(self, o):
        if isinstance(o, dict):
            if len(o.keys()) == 2 and "numerator" in o and "denominator" in o:
                return Fraction(o['numerator'], o['denominator'])
            else:
                for key in o:
                    o[key] = self._reinterpret_object(o[key])
        elif isinstance(o, list):
            return [self._reinterpret_object(v) for v in o]
        elif isinstance(o, string_types):
            if re.match(UUID_REGEX,
                        o):
                return uuid.UUID(o)
            elif re.match(r'\d+:\d+',o):
                return Timestamp.from_tai_sec_nsec(o)
            elif re.match(r'(\+|-)\d+:\d+',o):
                return TimeOffset.from_sec_nsec(o)
        return o
