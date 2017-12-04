import unittest
from nmoscommon.timestamp import Timestamp, TimeOffset

class TestTimestamp(unittest.TestCase):

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

    def test_subsec(self):
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
        tests_ts = [
            (TimeOffset.get_interval_fraction(50, 1, 1), TimeOffset(0, 20000000)),
            (TimeOffset.get_interval_fraction(50, 1, 2), TimeOffset(0, 10000000))
        ]

        for t in tests_ts:
            self.assertEqual(t[0], t[1])

    def test_from_count(self):
        tests_ts = [
            (TimeOffset.from_count(1, 50, 1), TimeOffset(0, 20000000)),
            (TimeOffset.from_count(75, 50, 1), TimeOffset(1, 500000000)),
            (TimeOffset.from_count(-75, 50, 1), TimeOffset(1, 500000000, -1))
        ]

        for t in tests_ts:
            self.assertEqual(t[0], t[1])

    def test_to_count(self):
        tests_ts = [
            (TimeOffset(0, 20000000).to_count(50, 1), 1),
            (TimeOffset(1, 500000000).to_count(50, 1), 75),
            (TimeOffset(1, 500000000, -1).to_count(50, 1), -75),
            (TimeOffset(100, 29999999).to_count(50, 1), 100 * 50 + 1),  # below .5 frame
            (TimeOffset(100, 30000000).to_count(50, 1), 100 * 50 + 2),  # at .5 frame
            (TimeOffset(100, 30000001).to_count(50, 1), 100 * 50 + 2),  # above .5 frame
            (TimeOffset(100, 9999999).to_count(50, 1), 100 * 50),       # below negative .5 frame
            (TimeOffset(100, 10000000).to_count(50, 1), 100 * 50 + 1),  # at negative .5 frame
            (TimeOffset(100, 10000001).to_count(50, 1), 100 * 50 + 1)   # above negative .5 frame
        ]

        for t in tests_ts:
            self.assertEqual(t[0], t[1])

    def test_abs(self):
        tests_ts = [
            (abs(TimeOffset(10, 1)), TimeOffset(10, 1)),
            (abs(TimeOffset(10, 1, -1)), TimeOffset(10, 1))
        ]

        for t in tests_ts:
            self.assertEqual(t[0], t[1])

    def test_iaddsub(self):
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

    def test_addsub(self):
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
        tests_ts = [
            (TimeOffset(10, 10)*0, TimeOffset(0, 0)),
            (TimeOffset(10, 10)*10, TimeOffset(100, 100)),
            (10*TimeOffset(10, 10), TimeOffset(100, 100)),
            (TimeOffset(10, 10)*(-10), TimeOffset(100, 100, -1)),
            (TimeOffset(10, 10, -1)*10, TimeOffset(100, 100, -1)),
            (TimeOffset(100, 100)/10, TimeOffset(10, 10)),
            (TimeOffset(100, 100, -1)/10, TimeOffset(10, 10, -1)),
            (TimeOffset(281474976710654, 0)/281474976710655, TimeOffset(0, 999999999)),
            (Timestamp(100, 100)/10, Timestamp(10, 10)),
            (Timestamp(10, 10)*10, Timestamp(100, 100)),
            (10*Timestamp(10, 10), Timestamp(100, 100)),
        ]

        count = 0
        for t in tests_ts:
            self.assertEqual(t[0], t[1])
            self.assertEqual(isinstance(t[0], Timestamp), isinstance(t[1], Timestamp),
                             "Failed on itteration {}, {}, {}".format(count, type(t[0]),type(t[1])))
            count = count + 1

    def test_average(self):
        toff1 = TimeOffset(11, 976)
        toff2 = TimeOffset(21, 51)
        toff_avg = (toff1 * 49 + toff2) / 50
        avg = int((toff1.to_nanosec() * 49 + toff2.to_nanosec()) / 50)
        self.assertEqual(avg, toff_avg.to_nanosec())

    def test_compare(self):
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
        ]

        for t in tests_ts:
            self.assertEqual(t[0], t[1])

    def test_cast(self):
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

    def test_invalid_str(self):
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
        tests_ts = [
            (Timestamp(-1, 0), Timestamp()),
            (Timestamp(281474976710656, 0), Timestamp(281474976710655, 999999999)),
            (Timestamp(0, 1000000000), Timestamp(0, 999999999)),
            (Timestamp(0, -1), Timestamp(0, 0))
        ]

        for t in tests_ts:
            self.assertEqual(t[0], t[1])

    def test_convert_str(self):
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

    def test_convert_tai_sec_nsec(self):
        tests_ts = [
            ("0:0", Timestamp(0, 0), "0:0"),
            ("5", Timestamp(5, 0), "5:0"),
            ("5:1", Timestamp(5, 1), "5:1"),
            ("5:999999999", Timestamp(5, 999999999), "5:999999999")
        ]

        for t in tests_ts:
            ts = Timestamp.from_tai_sec_nsec(t[0])
            self.assertTrue(isinstance(ts, Timestamp))
            self.assertEqual(ts, t[1])
            ts_str = ts.to_tai_sec_nsec()
            self.assertEqual(ts_str, t[2])

    def test_convert_tai_sec_frac(self):
        tests_ts = [
            ("0.0", Timestamp(0, 0), "0.0"),
            ("5", Timestamp(5, 0), "5.0"),
            ("5.1", Timestamp(5, 1000000000 / 10), "5.1"),
            ("5.10000000", Timestamp(5, 1000000000 / 10), "5.1"),
            ("5.123456789", Timestamp(5, 123456789), "5.123456789"),
            ("5.000000001", Timestamp(5, 1), "5.000000001"),
            ("5.0000000001", Timestamp(5, 0), "5.0")
        ]

        for t in tests_ts:
            ts = Timestamp.from_tai_sec_frac(t[0])
            self.assertEqual(ts, t[1])
            ts_str = ts.to_tai_sec_frac()
            self.assertEqual(ts_str, t[2])

    def test_convert_iso_utc(self):
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

    def test_smpte_timelabel(self):
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
