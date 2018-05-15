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

from six import PY2

import unittest
import mock

from datetime import datetime
from dateutil import tz

from nmoscommon.timestamp import Timestamp, TimeOffset, TsValueError

if PY2:
    BUILTINS = "__builtin__"
else:
    BUILTINS = "builtins"


class TestTimeOffset(unittest.TestCase):
    def test_from_timeoffset(self):
        """This tests that TimeOffsets can be created with a variety of values."""
        tests_ts = [
            (TimeOffset.from_timeoffset(TimeOffset(0, 0)), TimeOffset(0, 0)),
            (TimeOffset.from_timeoffset(TimeOffset(1001, 0)), TimeOffset(1001, 0)),
            (TimeOffset.from_timeoffset(TimeOffset(1001, 1001)), TimeOffset(1001, 1001)),
            ]

        for t in tests_ts:
            self.assertEqual(t[0], t[1])

    def test_normalise(self):
        tests_ts = [
            (TimeOffset(0, 0).normalise(30000, 1001), TimeOffset(0, 0)),
            (TimeOffset(1001, 0).normalise(30000, 1001), TimeOffset(1001, 0)),
            (TimeOffset(1001, 1001.0/30000/2*1000000000).normalise(30000, 1001), TimeOffset(1001, 0)),
            (TimeOffset(1001, 1001.0/30000/2*1000000000 + 1).normalise(30000, 1001), TimeOffset(1001, 1001.0/30000*1000000000)),
            (TimeOffset(1001, 1001.0/30000/2*1000000000, -1).normalise(30000, 1001), TimeOffset(1001, 0, -1)),
            (TimeOffset(1001, 1001.0/30000/2*1000000000 + 1, -1).normalise(30000, 1001), TimeOffset(1001, 1001.0/30000*1000000000, -1))
        ]

        for t in tests_ts:
            self.assertEqual(t[0], t[1])

    def test_hash(self):
        self.assertEqual(hash(TimeOffset(0,0)), hash(TimeOffset(0,0)))
        self.assertNotEqual(hash(TimeOffset(0,0)), hash(TimeOffset(0,1)))

    def test_subsec(self):
        """This tests that TimeOffsets can be converted to millisec, nanosec, and microsec values."""
        tests_ts = [
            (TimeOffset(1, 1000000).to_millisec(), 1001),
            (TimeOffset(1, 1000).to_microsec(), 1000001),
            (TimeOffset(1, 1).to_nanosec(), 1000000001),
            (TimeOffset.from_millisec(1001), TimeOffset(1, 1000000)),
            (TimeOffset.from_microsec(1000001), TimeOffset(1, 1000)),
            (TimeOffset.from_nanosec(1000000001), TimeOffset(1, 1)),
            (TimeOffset(1, 500000).to_millisec(TimeOffset.ROUND_DOWN), 1000),
            (TimeOffset(1, 500000).to_millisec(TimeOffset.ROUND_NEAREST), 1001),
            (TimeOffset(1, 499999).to_millisec(TimeOffset.ROUND_NEAREST), 1000),
            (TimeOffset(1, 500000).to_millisec(TimeOffset.ROUND_UP), 1001),
            (TimeOffset(1, 500000, -1).to_millisec(TimeOffset.ROUND_DOWN), -1001),
            (TimeOffset(1, 500000, -1).to_millisec(TimeOffset.ROUND_NEAREST), -1001),
            (TimeOffset(1, 499999, -1).to_millisec(TimeOffset.ROUND_NEAREST), -1000),
            (TimeOffset(1, 500000, -1).to_millisec(TimeOffset.ROUND_UP), -1000)
        ]

        for t in tests_ts:
            self.assertEqual(t[0], t[1])

    def test_interval_frac(self):
        """This tests that TimeOffsets can be converted to interval fractions."""
        tests_ts = [
            (TimeOffset.get_interval_fraction(50, 1, 1), TimeOffset(0, 20000000)),
            (TimeOffset.get_interval_fraction(50, 1, 2), TimeOffset(0, 10000000))
        ]

        for t in tests_ts:
            self.assertEqual(t[0], t[1])

        bad_params = [ (0, 1, 1),
                       (50, 0, 1),
                       (50, 1, 0) ]

        for params in bad_params:
            with self.assertRaises(TsValueError):
                TimeOffset.get_interval_fraction(*params)

    def test_from_sec_frac(self):
        """This tests that timeoffsets can be instantiated from fractional second values."""
        tests_ts = [
            (TimeOffset.from_sec_frac("1.000000001"), TimeOffset(1, 1)),
            (TimeOffset.from_sec_frac("-1.000000001"), TimeOffset(1, 1, sign=-1)),
            (TimeOffset.from_sec_frac("1.000001POTATO"), TimeOffset(1, 1000)),
            (TimeOffset.from_sec_frac("1"), TimeOffset(1, 0)),
        ]

        for t in tests_ts:
            self.assertEqual(t[0], t[1])

        bad_params = [ ("0.0.1",),
                        ]

        for params in bad_params:
            with self.assertRaises(TsValueError):
                TimeOffset.from_sec_frac(*params)

    def test_from_sec_nsec(self):
        """This tests that time offsets can be created from second:nanosecond pairs."""
        tests_ts = [
            (TimeOffset.from_sec_nsec("1:1"), TimeOffset(1, 1)),
            (TimeOffset.from_sec_nsec("-1:1"), TimeOffset(1, 1, sign=-1)),
            (TimeOffset.from_sec_nsec("1"), TimeOffset(1, 0)),
        ]

        for t in tests_ts:
            self.assertEqual(t[0], t[1])

        bad_params = [ ("0:0:1",), ]

        for params in bad_params:
            with self.assertRaises(TsValueError):
                TimeOffset.from_sec_nsec(*params)

    def test_from_count(self):
        """This tests that time offsets can be created from counts at a specified frequency."""
        tests_ts = [
            (TimeOffset.from_count(1, 50, 1), TimeOffset(0, 20000000)),
            (TimeOffset.from_count(75, 50, 1), TimeOffset(1, 500000000)),
            (TimeOffset.from_count(-75, 50, 1), TimeOffset(1, 500000000, -1))
        ]

        for t in tests_ts:
            self.assertEqual(t[0], t[1])

        bad_params = [ (1, 0, 1),
                       (1, 1, 0) ]

        for params in bad_params:
            with self.assertRaises(TsValueError):
                TimeOffset.from_count(*params)

    def test_from_millisec(self):
        """This tests that time offsets can be created from millisecond values."""
        tests_ts = [
            (TimeOffset.from_millisec(1), TimeOffset(0, 1000000)),
            (TimeOffset.from_millisec(1000), TimeOffset(1, 0)),
            (TimeOffset.from_millisec(-1), TimeOffset(0, 1000000, -1))
        ]

        for t in tests_ts:
            self.assertEqual(t[0], t[1])

    def test_from_microsec(self):
        """This tests that time offsets can be created from microsecond values."""
        tests_ts = [
            (TimeOffset.from_microsec(1), TimeOffset(0, 1000)),
            (TimeOffset.from_microsec(1000000), TimeOffset(1, 0)),
            (TimeOffset.from_microsec(-1), TimeOffset(0, 1000, -1))
        ]

        for t in tests_ts:
            self.assertEqual(t[0], t[1])

    def test_from_nanosec(self):
        """This tests that time offsets can be created from nanosecond values."""
        tests_ts = [
            (TimeOffset.from_nanosec(1), TimeOffset(0, 1)),
            (TimeOffset.from_nanosec(1000000000), TimeOffset(1, 0)),
            (TimeOffset.from_nanosec(-1), TimeOffset(0, 1, -1))
        ]

        for t in tests_ts:
            self.assertEqual(t[0], t[1])

    def test_set_value(self):
        """This tests that time offsets can have their value set."""
        tests_ts = [
            (TimeOffset(0,0), TimeOffset(0, 1), (0,1)),
            (TimeOffset(0,0), TimeOffset(1, 0), (1,0)),
            (TimeOffset(0,0), TimeOffset(0, 1,-1), (0,1,-1))
        ]

        for t in tests_ts:
            t[0].set_value(*t[2])
            self.assertEqual(t[0], t[1])

    def test_to_count(self):
        """This tests that time offsets can be converted to counts at particular frequencies."""
        tests_ts = [
            (TimeOffset(0, 20000000).to_count(50, 1), 1),
            (TimeOffset(1, 500000000).to_count(50, 1), 75),
            (TimeOffset(1, 500000000, -1).to_count(50, 1), -75),
            (TimeOffset(100, 29999999).to_count(50, 1), 100 * 50 + 1),  # below .5 frame
            (TimeOffset(100, 30000000).to_count(50, 1), 100 * 50 + 2),  # at .5 frame
            (TimeOffset(100, 30000001).to_count(50, 1), 100 * 50 + 2),  # above .5 frame
            (TimeOffset(100, 9999999).to_count(50, 1), 100 * 50),       # below negative .5 frame
            (TimeOffset(100, 10000000).to_count(50, 1), 100 * 50 + 1),  # at negative .5 frame
            (TimeOffset(100, 10000001).to_count(50, 1), 100 * 50 + 1),  # above negative .5 frame
            (TimeOffset(100, 29999999).to_count(50, 1, TimeOffset.ROUND_UP), 100 * 50 + 2),  # below .5 frame, round up
            (TimeOffset(100, 30000000).to_count(50, 1, TimeOffset.ROUND_DOWN), 100 * 50 + 1),  # at .5 frame, round down
            (TimeOffset(100, 30000001).to_count(50, 1, TimeOffset.ROUND_DOWN), 100 * 50 + 1),  # above .5 frame, round down
            (TimeOffset(100, 29999999, -1).to_count(50, 1, TimeOffset.ROUND_DOWN), -100 * 50 - 2),  # below .5 frame, round up
            (TimeOffset(100, 30000000, -1).to_count(50, 1, TimeOffset.ROUND_UP), -100 * 50 - 1),  # at .5 frame, round down
            (TimeOffset(100, 30000001, -1).to_count(50, 1, TimeOffset.ROUND_UP), -100 * 50 - 1),  # above .5 frame, round down
        ]

        for t in tests_ts:
            self.assertEqual(t[0], t[1])

        bad_params = [ (1, 0),
                       (0, 1) ]

        for params in bad_params:
            with self.assertRaises(TsValueError):
                TimeOffset(0,0).to_count(*params)

    def test_to_microsec(self):
        """This tests that time offsets can be converted to microsecond values."""
        tests_ts = [
            (TimeOffset(0, 1000).to_microsec(), 1),
            (TimeOffset(1, 1000000).to_microsec(), 1001000),
            (TimeOffset(1, 1000000, -1).to_microsec(), -1001000),
            (TimeOffset(100, 1499).to_microsec(), 100 * 1000000 + 1),  # below .5 us
            (TimeOffset(100, 1500).to_microsec(), 100 * 1000000 + 2),  # at .5 us
            (TimeOffset(100, 1501).to_microsec(), 100 * 1000000 + 2),  # above .5 us
            (TimeOffset(100, 1499).to_microsec(TimeOffset.ROUND_UP), 100 * 1000000 + 2),  # below .5 us, round up
            (TimeOffset(100, 1500).to_microsec(TimeOffset.ROUND_UP), 100 * 1000000 + 2),  # at .5 us, round up
            (TimeOffset(100, 1501).to_microsec(TimeOffset.ROUND_UP), 100 * 1000000 + 2),  # above .5 us, round up
            (TimeOffset(100, 1499).to_microsec(TimeOffset.ROUND_DOWN), 100 * 1000000 + 1),  # below .5 us, round down
            (TimeOffset(100, 1500).to_microsec(TimeOffset.ROUND_DOWN), 100 * 1000000 + 1),  # at .5 us, round down
            (TimeOffset(100, 1501).to_microsec(TimeOffset.ROUND_DOWN), 100 * 1000000 + 1),  # above .5 us, round down
            (TimeOffset(100, 1499, -1).to_microsec(TimeOffset.ROUND_DOWN), -100 * 1000000 - 2),  # below .5 us, round down
            (TimeOffset(100, 1500, -1).to_microsec(TimeOffset.ROUND_DOWN), -100 * 1000000 - 2),  # at .5 us, round down
            (TimeOffset(100, 1501, -1).to_microsec(TimeOffset.ROUND_DOWN), -100 * 1000000 - 2),  # above .5 us, round down
            (TimeOffset(100, 1499, -1).to_microsec(TimeOffset.ROUND_UP), -100 * 1000000 - 1),  # below .5 us, round up
            (TimeOffset(100, 1500, -1).to_microsec(TimeOffset.ROUND_UP), -100 * 1000000 - 1),  # at .5 us, round up
            (TimeOffset(100, 1501, -1).to_microsec(TimeOffset.ROUND_UP), -100 * 1000000 - 1),  # above .5 us, round up
        ]

        n = 0
        for t in tests_ts:
            self.assertEqual(t[0], t[1], msg="failed on check %d, %d != %d" % (n, t[0], t[1]))
            n += 1


    def test_abs(self):
        """This tests that negative time offsets can be converted to positive ones using abs."""
        tests_ts = [
            (abs(TimeOffset(10, 1)), TimeOffset(10, 1)),
            (abs(TimeOffset(10, 1, -1)), TimeOffset(10, 1))
        ]

        for t in tests_ts:
            self.assertEqual(t[0], t[1])

    def test_average(self):
        """This tests that time offsets can be averaged."""
        toff1 = TimeOffset(11, 976)
        toff2 = TimeOffset(21, 51)
        toff_avg = (toff1 * 49 + toff2) // 50
        avg = int((toff1.to_nanosec() * 49 + toff2.to_nanosec()) // 50)
        self.assertEqual(avg, toff_avg.to_nanosec())

    def test_cast(self):
        """This tests that addition and subtraction of TimeOffsets and integers or floats works as expected."""
        tests_ts = [
            (TimeOffset(10, 1) + 1, TimeOffset(11, 1)),
            (TimeOffset(10, 1) - 1, TimeOffset(9, 1)),
            (TimeOffset(10, 1) + 1.5, TimeOffset(11, 500000001)),
            (TimeOffset(10, 1) - 1.5, TimeOffset(8, 500000001)),
            (TimeOffset(8, 500000000) == 8.5, True),
            (TimeOffset(8, 500000000) > 8, True),
            (TimeOffset(8, 500000000) < 8.6, True),
            (TimeOffset(8, 500000000) != 8.6, True),
        ]

        for t in tests_ts:
            self.assertEqual(t[0], t[1])

    def test_repr(self):
        """This tests that the repr function turns time offsets into second:nanosecond pairs."""
        tests_ts = [
            (repr(TimeOffset(10, 1)), "10:1"),
            (repr(TimeOffset(10, 1, -1)), "-10:1"),
        ]

        for t in tests_ts:
            self.assertEqual(t[0], t[1])

class TestTimestamp(unittest.TestCase):
    def test_get_time_pythonic(self):
        """This tests that the fallback pure python implementation of get_time works as expected."""
        test_ts = [
            (1512489451.0, Timestamp(1512489451 + 37,0)),
            (1512489451.1, Timestamp(1512489451 + 37,100000000))
            ]

        for t in test_ts:
            with mock.patch("time.time") as time:
                time.return_value = t[0]
                gottime = Timestamp.get_time(force_pure_python=True)
                self.assertEqual(gottime, t[1], msg="Times not equal, expected: %r, got %r" % (t[1], gottime))

    def test_iaddsub(self):
        """This tests integer addition and subtraction on timestamps."""
        ts = Timestamp(10, 0)
        ts += TimeOffset(1, 2)
        self.assertEqual(ts, Timestamp(11, 2))
        ts -= TimeOffset(1, 2)
        self.assertEqual(ts, Timestamp(10, 0))
        ts -= TimeOffset(100, 5)
        self.assertTrue(ts.is_null())
        ts = Timestamp(281474976710655, 999999999)
        ts += TimeOffset(0, 1)
        self.assertEqual(ts, Timestamp(281474976710655, 999999999))
        toff = TimeOffset(10, 0)
        toff -= TimeOffset(100, 0)
        self.assertEqual(toff, TimeOffset(90, 0, -1))
        toff = TimeOffset(10, 0)
        toff -= TimeOffset(0, 1)
        self.assertEqual(toff, TimeOffset(9, 999999999))
        toff = TimeOffset(10, 500000000)
        toff += TimeOffset(0, 500000000)
        self.assertEqual(toff, TimeOffset(11, 0))
        toff = TimeOffset(10, 500000000, -1)
        toff -= TimeOffset(0, 500000000)
        self.assertEqual(toff, TimeOffset(11, 0, -1))
        toff = TimeOffset(10, 0, -1)
        toff += TimeOffset(0, 500000000)
        self.assertEqual(toff, TimeOffset(9, 500000000, -1))

    def test_addsub(self):
        """This tests addition and subtraction on timestamps."""

        tests_ts = [
            (Timestamp(10, 0)+TimeOffset(1, 2), Timestamp(11, 2)),
            (Timestamp(11, 2)-TimeOffset(1, 2), Timestamp(10, 0)),
            (TimeOffset(11, 2)-TimeOffset(1, 2), TimeOffset(10, 0)),
            (Timestamp(10, 0)-TimeOffset(11, 2), Timestamp(0, 0)),
            (TimeOffset(10, 0)-TimeOffset(11, 2), TimeOffset(1, 2, -1)),
            (TimeOffset(10, 0)-Timestamp(11, 2), TimeOffset(1, 2, -1)),
            (Timestamp(10, 0)-Timestamp(11, 2), TimeOffset(1, 2, -1)),
            (Timestamp(11, 2)-Timestamp(10, 0), TimeOffset(1, 2, 1)),
        ]

        for t in tests_ts:
            self.assertEqual(t[0], t[1])
            self.assertEqual(isinstance(t[0], Timestamp), isinstance(t[1], Timestamp))

    def test_multdiv(self):
        """This tests multiplication and division on timestamps."""

        tests_ts = [
            (TimeOffset(10, 10)*0, TimeOffset(0, 0)),
            (TimeOffset(10, 10)*10, TimeOffset(100, 100)),
            (10*TimeOffset(10, 10), TimeOffset(100, 100)),
            (TimeOffset(10, 10)*(-10), TimeOffset(100, 100, -1)),
            (TimeOffset(10, 10, -1)*10, TimeOffset(100, 100, -1)),
            (TimeOffset(100, 100)//10, TimeOffset(10, 10)),
            (TimeOffset(100, 100)//-10, TimeOffset(10, 10, -1)),
            (TimeOffset(100, 100, -1)//10, TimeOffset(10, 10, -1)),
            (TimeOffset(281474976710654, 0)//281474976710655, TimeOffset(0, 999999999)),
            (Timestamp(100, 100)//10, Timestamp(10, 10)),
            (Timestamp(10, 10)*10, Timestamp(100, 100)),
            (10*Timestamp(10, 10), Timestamp(100, 100)),
        ]

        count = 0
        for t in tests_ts:
            self.assertEqual(t[0], t[1])
            self.assertEqual(isinstance(t[0], Timestamp), isinstance(t[1], Timestamp),
                             "Failed on itteration {}, {}, {}".format(count, type(t[0]),type(t[1])))
            count = count + 1

    def test_compare(self):
        """This tests comparison of timestamps."""

        tests_ts = [
            (Timestamp(1, 2) == Timestamp(1, 2), True),
            (Timestamp(1, 2) != Timestamp(1, 3), True),
            (Timestamp(1, 0) < Timestamp(1, 2), True),
            (Timestamp(1, 2) <= Timestamp(1, 2), True),
            (Timestamp(2, 0) > Timestamp(1, 0), True),
            (Timestamp(2, 0) >= Timestamp(2, 0), True),
            (Timestamp(2, 0) < Timestamp(1, 0), False),
            (Timestamp(2, 0) == Timestamp(3, 0), False),
            (Timestamp(2, 0) == 2, True),
            (Timestamp(2, 0) > 1, True),
            (Timestamp(2, 0) < 3, True),
            (TimeOffset(2, 0) < 3, True),
            (TimeOffset(1,0,1) < TimeOffset(1,0,-1), False)
        ]

        for t in tests_ts:
            self.assertEqual(t[0], t[1])

    def test_invalid_str(self):
        """This tests that invalid strings fed into from_str raise exceptions."""

        tests_ts = [
            "a",
            "2015-02-17T12:53:48.5",
            "2015-02T12:53:48.5",
            "2015-02-17T12:53.5",
            "12:53:48.5"
        ]

        for t in tests_ts:
            try:
                Timestamp.from_str(t)
                self.assertTrue(False)
            except:
                pass

    def test_invalid_int(self):
        """This tests that invalid int values fed into timestamp constructor get normalised."""

        tests_ts = [
            (Timestamp(-1, 0), Timestamp()),
            (Timestamp(281474976710656, 0), Timestamp(281474976710655, 999999999)),
            (Timestamp(0, 1000000000), Timestamp(0, 999999999)),
            (Timestamp(0, -1), Timestamp(0, 0))
        ]

        for t in tests_ts:
            self.assertEqual(t[0], t[1])

    def test_convert_str(self):
        """This tests that various string formats can be converted to timestamps."""

        tests_ts = [
            ("1:2", Timestamp(1, 2)),
            ("1.2", Timestamp(1, 200000000)),
            ("1", Timestamp(1, 0)),
            ("2015-02-17T12:53:48.5Z", Timestamp(1424177663, 500000000)),
            ("2015-02-17T12:53:48.000102003Z", Timestamp(1424177663, 102003))
        ]

        for t in tests_ts:
            ts = Timestamp.from_str(t[0])
            self.assertTrue(isinstance(ts, Timestamp))
            self.assertEqual(ts, t[1])

    def test_convert_sec_nsec(self):
        """This tests that the conversion to and from TAI second:nanosecond pairs works as expected."""

        tests_ts = [
            ("0:0", TimeOffset(0, 0), "0:0"),
            ("0:1", TimeOffset(0, 1), "0:1"),
            ("-0:1", TimeOffset(0, 1, -1), "-0:1"),
            ("5", TimeOffset(5, 0), "5:0"),
            ("5:1", TimeOffset(5, 1), "5:1"),
            ("-5:1", TimeOffset(5, 1, -1), "-5:1"),
            ("5:999999999", TimeOffset(5, 999999999), "5:999999999")
        ]

        for t in tests_ts:
            ts = TimeOffset.from_sec_nsec(t[0])
            self.assertEqual(
                ts,
                t[1],
                msg="Called with {} {} {}".format(t[0], t[1], t[2]))
            ts_str = ts.to_sec_nsec()
            self.assertEqual(
                ts_str,
                t[2],
                msg="Called with {} {} {}".format(t[0], t[1], t[2]))

    def test_ts_convert_tai_sec_nsec(self):
        """This tests that the conversion to and from TAI second:nanosecond pairs works as expected."""

        tests_ts = [
            ("0:0", Timestamp(0, 0), "0:0"),
            ("0:1", Timestamp(0, 1), "0:1"),
            ("-0:1", Timestamp(0, 0), "0:0"),
            ("5", Timestamp(5, 0), "5:0"),
            ("5:1", Timestamp(5, 1), "5:1"),
            ("-5:1", Timestamp(0, 0), "0:0"),
            ("5:999999999", Timestamp(5, 999999999), "5:999999999")
        ]

        for t in tests_ts:
            ts = Timestamp.from_sec_nsec(t[0])
            self.assertTrue(
                isinstance(ts, Timestamp),
                msg="Called with {} {} {}".format(t[0], t[1], t[2]))
            self.assertEqual(
                ts,
                t[1],
                msg="Called with {} {} {}".format(t[0], t[1], t[2]))
            ts_str = ts.to_sec_nsec()
            self.assertEqual(
                ts_str,
                t[2],
                msg="Called with {} {} {}".format(t[0], t[1], t[2]))

    def test_convert_sec_frac(self):
        """This tests that the conversion to and from TAI seconds with fractional parts works as expected."""

        tests_ts = [
            ("0.0", TimeOffset(0, 0), "0.0"),
            ("0.1", TimeOffset(0, 1000000000 // 10), "0.1"),
            ("-0.1", TimeOffset(0, 1000000000 // 10, -1), "-0.1"),
            ("5", TimeOffset(5, 0), "5.0"),
            ("5.1", TimeOffset(5, 1000000000 // 10), "5.1"),
            ("-5.1", TimeOffset(5, 1000000000 // 10, -1), "-5.1"),
            ("5.10000000", TimeOffset(5, 1000000000 // 10), "5.1"),
            ("5.123456789", TimeOffset(5, 123456789), "5.123456789"),
            ("5.000000001", TimeOffset(5, 1), "5.000000001"),
            ("5.0000000001", TimeOffset(5, 0), "5.0")
        ]

        for t in tests_ts:
            ts = TimeOffset.from_sec_frac(t[0])
            self.assertEqual(
                ts,
                t[1],
                msg="Called with {} {} {}".format(t[0], t[1], t[2]))
            ts_str = ts.to_sec_frac()
            self.assertEqual(
                ts_str,
                t[2],
                msg="Called with {} {} {}".format(t[0], t[1], t[2]))

    def test_ts_convert_tai_sec_frac(self):
        """This tests that the conversion to and from TAI seconds with fractional parts works as expected."""

        tests_ts = [
            ("0.0", Timestamp(0, 0), "0.0"),
            ("0.1", Timestamp(0, 1000000000 // 10), "0.1"),
            ("-0.1", Timestamp(0, 0), "0.0"),
            ("5", Timestamp(5, 0), "5.0"),
            ("5.1", Timestamp(5, 1000000000 // 10), "5.1"),
            ("-5.1", Timestamp(0, 0), "0.0"),
            ("5.10000000", Timestamp(5, 1000000000 // 10), "5.1"),
            ("5.123456789", Timestamp(5, 123456789), "5.123456789"),
            ("5.000000001", Timestamp(5, 1), "5.000000001"),
            ("5.0000000001", Timestamp(5, 0), "5.0")
        ]

        for t in tests_ts:
            ts = Timestamp.from_sec_frac(t[0])
            self.assertTrue(
                isinstance(ts, Timestamp),
                msg="Called with {} {} {}".format(t[0], t[1], t[2]))
            self.assertEqual(
                ts,
                t[1],
                msg="Called with {} {} {}".format(t[0], t[1], t[2]))
            ts_str = ts.to_sec_frac()
            self.assertEqual(
                ts_str,
                t[2],
                msg="Called with {} {} {}".format(t[0], t[1], t[2]))

    def test_convert_iso_utc(self):
        """This tests that conversion to and from ISO date format UTC time works as expected."""

        tests = [
            (Timestamp(1424177663, 102003), "2015-02-17T12:53:48.000102003Z"),

            # the leap second is 23:59:60

            #   30 June 1972 23:59:59 (2287785599, first time): TAI= UTC + 10 seconds
            (Timestamp(78796809, 0), "1972-06-30T23:59:59.000000000Z"),

            #   30 June 1972 23:59:60 (2287785599,second time): TAI= UTC + 11 seconds
            (Timestamp(78796810, 0), "1972-06-30T23:59:60.000000000Z"),

            #   1  July 1972 00:00:00 (2287785600)      TAI= UTC + 11 seconds
            (Timestamp(78796811, 0), "1972-07-01T00:00:00.000000000Z"),

            (Timestamp(1341100833, 0), "2012-06-30T23:59:59.000000000Z"),
            (Timestamp(1341100834, 0), "2012-06-30T23:59:60.000000000Z"),
            (Timestamp(1341100835, 0), "2012-07-01T00:00:00.000000000Z"),

            (Timestamp(1341100835, 1), "2012-07-01T00:00:00.000000001Z"),
            (Timestamp(1341100835, 100000000), "2012-07-01T00:00:00.100000000Z"),
            (Timestamp(1341100835, 999999999), "2012-07-01T00:00:00.999999999Z"),

            (Timestamp(283996818, 0), "1979-01-01T00:00:00.000000000Z")  # 1979
        ]

        for t in tests:
            utc = t[0].to_iso8601_utc()
            self.assertEqual(utc, t[1])
            ts = Timestamp.from_iso8601_utc(t[1])
            self.assertEqual(ts, t[0])

        bad_params = [
            ("2012-07-01Y00:00:00.000000001Z",),
            ("2012-07~01T00:00:00.000000001Z",),
            ("2012-07-01T00:00:00.0000.0001Z",),
            ]

        for p in bad_params:
            with self.assertRaises(TsValueError):
                Timestamp.from_iso8601_utc(*p)

    def test_smpte_timelabel(self):
        """This tests that conversion to and from SMPTE time labels works correctly."""

        tests = [
            ("2015-01-23T12:34:56F00 30000/1001 UTC-05:00 TAI-35", 30000, 1001, -5*60*60),
            ("2015-01-23T12:34:56F01 30000/1001 UTC-05:00 TAI-35", 30000, 1001, -5*60*60),
            ("2015-01-23T12:34:56F02 30000/1001 UTC-05:00 TAI-35", 30000, 1001, -5*60*60),
            ("2015-01-23T12:34:56F28 30000/1001 UTC-05:00 TAI-35", 30000, 1001, -5*60*60),
            ("2015-01-23T12:34:56F29 30000/1001 UTC-05:00 TAI-35", 30000, 1001, -5*60*60),

            ("2015-07-01T00:59:59F00 30000/1001 UTC+01:00 TAI-35", 30000, 1001, 60*60),
            ("2015-07-01T00:59:59F01 30000/1001 UTC+01:00 TAI-35", 30000, 1001, 60*60),
            ("2015-07-01T00:59:59F29 30000/1001 UTC+01:00 TAI-35", 30000, 1001, 60*60),
            ("2015-07-01T00:59:60F00 30000/1001 UTC+01:00 TAI-35", 30000, 1001, 60*60),
            ("2015-07-01T00:59:60F29 30000/1001 UTC+01:00 TAI-35", 30000, 1001, 60*60),
            ("2015-07-01T01:00:00F00 30000/1001 UTC+01:00 TAI-36", 30000, 1001, 60*60),
            ("2015-06-30T18:59:59F29 30000/1001 UTC-05:00 TAI-35", 30000, 1001, -5*60*60),
            ("2015-06-30T18:59:60F00 30000/1001 UTC-05:00 TAI-35", 30000, 1001, -5*60*60),
            ("2015-06-30T18:59:60F29 30000/1001 UTC-05:00 TAI-35", 30000, 1001, -5*60*60),
            ("2015-06-30T19:00:00F00 30000/1001 UTC-05:00 TAI-36", 30000, 1001, -5*60*60)
        ]

        for t in tests:
            ts = Timestamp.from_smpte_timelabel(t[0])
            self.assertEqual(t[0], ts.to_smpte_timelabel(t[1], t[2], t[3]))

        bad_params = [
            ("potato",),
            ("the quick brown fox jumps over the lazy dog",),
            ("",),
            ('\u3069\u3082\u3042\u308a\u304c\u3068\u3046\u3001\u30df\u30b9\u30bf\u30fc\u30fb\u30ed\u30dc\u30c8\u30fc',),
            ("About half nine on tuesday",),
            ("0315-13~35T25:63:60F56 50000/1002 UTC-25:35 TAY-2",),
            ]
        for p in bad_params:
            with self.assertRaises(TsValueError):
                Timestamp.from_smpte_timelabel(*p)

        bad_params = [
            (0,1),
            (1,0),
            ]
        for p in bad_params:
            with self.assertRaises(TsValueError):
                Timestamp(0,0).to_smpte_timelabel(*p)

        with mock.patch("time.timezone", 0):
            with mock.patch("time.localtime") as localtime:
                localtime.return_value.tm_isdst = 1
                ts = Timestamp.from_smpte_timelabel("2015-07-01T00:59:59F00 30000/1001 UTC+01:00 TAI-35")
                self.assertEqual("2015-07-01T00:59:59F00 30000/1001 UTC+01:00 TAI-35", ts.to_smpte_timelabel(30000, 1001))


    def test_from_datetime(self):
        """Conversion from python's datetime object."""

        tests = [
            (datetime(1970, 1, 1, 0, 0, 0, 0, tz.gettz('UTC')), Timestamp(0,0)),
            (datetime(1983, 3, 29, 15, 45, 0, 0, tz.gettz('UTC')), Timestamp(417800721,0)),
            (datetime(2017, 12, 5, 16, 33, 12, 196, tz.gettz('UTC')), Timestamp(1512491629,196000)),
        ]

        for t in tests:
            self.assertEqual(Timestamp.from_datetime(t[0]), t[1])

    def test_to_datetime(self):
        """Conversion to python's datetime object."""

        tests = [
            (datetime(1970, 1, 1, 0, 0, 0, 0, tz.gettz('UTC')), Timestamp(0,0)),
            (datetime(1983, 3, 29, 15, 45, 0, 0, tz.gettz('UTC')), Timestamp(417800721,0)),
            (datetime(2017, 12, 5, 16, 33, 12, 196, tz.gettz('UTC')), Timestamp(1512491629,196000)),
        ]

        for t in tests:
            self.assertEqual(t[0], t[1].to_datetime())

    def test_from_str(self):
        """Conversion from string formats."""

        tests = [
            ("2015-01-23T12:34:56F00 30000/1001 UTC-05:00 TAI-35", Timestamp(1422034531,17100000)),
            ("2015-01-23T12:34:56.0Z", Timestamp(1422016531,0)),
            ("now", Timestamp(0,0)),
        ]

        for t in tests:
            with mock.patch("time.time", return_value=0.0):
                self.assertEqual(Timestamp.from_str(t[0], force_pure_python=True), t[1])

    def test_get_leap_seconds(self):
        """get_leap_seconds should return the correct number of leap seconds at any point in history."""

        tests = [
            (Timestamp(63072008,999999999), 0),
            (Timestamp(63072009,0), 10),
            (Timestamp(78796809,999999999), 10),
            (Timestamp(78796810,0), 11),
            (Timestamp(94694410,999999999), 11),
            (Timestamp(94694411,0), 12),
            (Timestamp(417800721,0), 21),
            (Timestamp(773020827,999999999), 28),
            (Timestamp(773020828,0), 29),
            (Timestamp(1512491629,0), 37),
        ]

        for t in tests:
            self.assertEqual(t[0].get_leap_seconds(), t[1])
