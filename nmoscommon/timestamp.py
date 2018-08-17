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

from __future__ import print_function

from mediatimestamp import TsValueError, TimeOffset, Timestamp, TimeRange

__all__ = ["TsValueError", "TimeOffset", "Timestamp", "TimeRange"]


# These constants are not part of the library's public interface, but have
# been included because earlier versions made them available.
MAX_NANOSEC = TimeOffset.MAX_NANOSEC
MAX_SECONDS = TimeOffset.MAX_SECONDS


if __name__ == '__main__':  # pragma: no cover
    import sys

    arg = sys.argv[1]

    ts = Timestamp.from_str(arg)

    if ts is not None:
        print("ips-tai-nsec     {}".format(ts.to_tai_sec_nsec()))
        print("ips-tai-frac     {}".format(ts.to_tai_sec_frac()))
        print("utc              {}".format(ts.to_iso8601_utc()))
        print("utc-secs         {}".format(ts.to_utc()[0]))
        print("smpte time label {}".format(ts.to_smpte_timelabel(50, 1)))
        sys.exit(0)

    else:
        sys.exit(1)
