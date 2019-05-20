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

# DEPRECATED - This class is deprecated - please use timestamp.py

from __future__ import print_function
from __future__ import absolute_import

import ctypes
from .timestamp import Timestamp

try:
    import ipppython.ptptime
    IPP_PYTHON = True
except ImportError:
    IPP_PYTHON = False

__all__ = ["ptp_time", "ptp_detail"]


class timespec(ctypes.Structure):
    _fields_ = [
        ('tv_sec', ctypes.c_long),
        ('tv_nsec', ctypes.c_long)
    ]


# This method is deprecated, use Timestamp.get_time()
def ptp_data():
    t = timespec()
    ts = Timestamp.get_time()
    t.tv_sec = int(ts.to_nanosec() * 1e-9)
    t.tv_nsec = int(ts.to_nanosec() - (t.tv_sec * 1e9))
    return t


# This method is deprecated, use Timestamp.get_time()
if IPP_PYTHON:
    ptp_data = ipppython.ptptime.ptp_data  # noqa F811
    FD_TO_CLOCKID = ipppython.ptptime.FD_TO_CLOCKID


def ptp_time():
    t = ptp_data()
    return t.tv_sec + t.tv_nsec * 1e-9


def ptp_detail():
    t = ptp_data()
    return [t.tv_sec, t.tv_nsec]


if __name__ == "__main__":  # pragma: no cover
    print(ptp_time())
    print(ptp_detail())
