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
This module provides the same interface as mediajson for purposes
of backwards compatibility. It is recommended that new code uses
that library instead.
"""

from mediajson import dump, dumps, load, loads
from mediajson import encode_value, decode_value
from mediajson import JSONEncoder, JSONDecoder
from mediajson import NMOSJSONEncoder, NMOSJSONDecoder

__all__ = ["dump", "dumps", "load", "loads",
           "encode_value", "decode_value",
           "JSONEncoder", "JSONDecoder",
           "NMOSJSONEncoder", "NMOSJSONDecoder"]
