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


# This regular expression identifies a uuid.
UUID_REGEX = re.compile(r'[0-9a-fA-F]{8}-' +
                        r'[0-9a-fA-F]{4}-' +
                        r'[0-9a-fA-F]{4}-' +
                        r'[0-9a-fA-F]{4}-' +
                        r'[0-9a-fA-F]{12}')


def dump(*args, **kwargs):
    """This method passes through to the json.dump in the standard library,
    which has the following signature:

        json.dump(obj, fp, skipkeys=False, ensure_ascii=True,
                  check_circular=True, allow_nan=True, cls=None,
                  indent=None, separators=None, encoding="utf-8",
                  default=None, sort_keys=False, **kw)

    this method works identically to that method except that the deault for
    the cls parameter has been changed to nmoscommon.json.NMOSJSONEncoder
    """
    # 'cls' is the 7th positional argument to the underlying function
    # so either it will be in kwargs['cls'] or args[6]
    if 'cls' not in kwargs and len(args) < 7:
        kwargs['cls'] = NMOSJSONEncoder
    elif len(args) >= 7 and args[6] is None:
        # This accounts for someone calling this method with more than 5
        # positional arguments but where the 6th one is None. This makes
        # the behaviour be as expected (cls is set to the default)
        # Quite frankly why the hell would anyone call it this way?
        # Who knows, but they can if they want to
        args = args[0:6] + [NMOSJSONEncoder] + args[7:]
    return json.dump(*args, **kwargs)


def dumps(*args, **kwargs):
    """This method passes through to the json.dumps in the standard library,
    which has the following signature:

        json.dumps(obj, skipkeys=False, ensure_ascii=True, check_circular=True,
                   allow_nan=True, cls=None, indent=None, separators=None,
                   encoding="utf-8", default=None, sort_keys=False, **kw)

    this method works identically to that method except that the deault for
    the cls parameter has been changed to nmoscommon.json.NMOSJSONEncoder
    """
    # 'cls' is the 6th positional argument to the underlying function
    # so either it will be in kwargs['cls'] or args[5]
    if 'cls' not in kwargs and len(args) < 6:
        kwargs['cls'] = NMOSJSONEncoder
    elif len(args) >= 6 and args[5] is None:
        # This accounts for someone calling this method with more than 4
        # positional arguments but where the 5th one is None. This makes
        # the behaviour be as expected (cls is set to the default)
        # Quite frankly why the hell would anyone call it this way?
        # Who knows, but they can if they want to
        args = args[0:5] + [NMOSJSONEncoder] + args[6:]
    return json.dumps(*args, **kwargs)


def load(*args, **kwargs):
    """This method passes through to the json.load in the standard library,
    which has the following signature:

        json.load(fp[, encoding[, cls[, object_hook[, parse_float[,
                  parse_int[, parse_constant[, object_pairs_hook[,
                  **kw]]]]]]]])

    this method works identically to that method except that the deault for
    the cls parameter has been changed to nmoscommon.json.NMOSJSONDecoder
    """
    # 'cls' is the 3rd positional argument to the underlying function
    # so either it will be in kwargs['cls'] or args[2]
    if 'cls' not in kwargs and len(args) < 3:
        kwargs['cls'] = NMOSJSONDecoder
    elif len(args) >= 3 and args[2] is None:
        # This accounts for someone calling this method with more than 2
        # positional arguments but where the 3rd one is None. This makes
        # the behaviour be as expected (cls is set to the default)
        # Quite frankly why the hell would anyone call it this way?
        # Who knows, but they can if they want to
        args = args[0:2] + [NMOSJSONDecoder] + args[3:]
    return json.load(*args, **kwargs)


def loads(*args, **kwargs):
    """This method passes through to the json.loads in the standard library,
    which has the following signature:

        json.loads(s[, encoding[, cls[, object_hook[, parse_float[, parse_int[,
                   parse_constant[, object_pairs_hook[, **kw]]]]]]]])

    this method works identically to that method except that the deault for
    the cls parameter has been changed to nmoscommon.json.NMOSJSONDecoder
    """
    # 'cls' is the 3rd positional argument to the underlying function
    # so either it will be in kwargs['cls'] or args[2]
    if 'cls' not in kwargs and len(args) < 3:
        kwargs['cls'] = NMOSJSONDecoder
    elif len(args) >= 3 and args[2] is None:
        # This accounts for someone calling this method with more than 2
        # positional arguments but where the 3rd one is None. This makes
        # the behaviour be as expected (cls is set to the default)
        # Quite frankly why the hell would anyone call it this way?
        # Who knows, but they can if they want to
        args = args[0:2] + [NMOSJSONDecoder] + args[3:]
    return json.loads(*args, **kwargs)


class NMOSJSONEncoder(JSONEncoder):
    """This is a specialised version of json.JSONEncoder from the standard library
    adjusted so that the following types are also recognised as json
    serialisable:

        uuid.UUID
        fractions.Fraction
        nmoscommon.timestamps.Timestamp
        nmoscommon.timestamps.TimeOffset

    uuids are rendered in standard string format, timestamps and time offsets
    are rendered as "secs:nanosecs" strings, and fractions are represented as
    dictionaries of the form:

        {"numerator": numerator,
         "denominator": denominator}

    """
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
    """This is a specialised version of json.JSONDecoder from the standard library
    adjusted so that any object of the form:

        {"numerator": n, "denominator", d}

    will be reinterpreted as a fractions.Fraction, any string that matches the
    format of a uuid will be reinterpreted as a uuid.UUID, any string of the
    form "secs:nanosecs" with no sign for secs will be reinterpreted as an
    nmoscommon.timestamps.Timestamp and any such string with a +/- in front of
    it will be reinterpreted as an nmoscommon.timestamps.TimeOffset.
    """
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
