import unittest
from datetime import datetime
from .util import strptime_partial


class TestPartialStrptime(unittest.TestCase):

    def test_iso_format(self):

        self.assertEqual(strptime_partial('2009'), datetime(2009, 1, 1, 0, 0, 0))
        self.assertEqual(strptime_partial('2009-10'), datetime(2009, 10, 1, 0, 0, 0))
        self.assertEqual(strptime_partial('2009-10-12'), datetime(2009, 10, 12, 0, 0, 0))
        self.assertEqual(strptime_partial('2009-10-12T12'), datetime(2009, 10, 12, 12, 0, 0))
        self.assertEqual(strptime_partial('2009-10-12T12:01'), datetime(2009, 10, 12, 12, 1, 0))
        self.assertEqual(strptime_partial('2009-10-12T12:15:23'), datetime(2009, 10, 12, 12, 15, 23))
        self.assertEqual(strptime_partial('2009-10-12T12:15:23.12345'), datetime(2009, 10, 12, 12, 15, 23, 123450))
        self.assertEqual(strptime_partial('2009-10-12T12:15:23.12345Z'), datetime(2009, 10, 12, 12, 15, 23, 123450))

    def test_custom_format(self):
        self.assertEqual(strptime_partial('10:11', '%H:%M'), datetime(1900, 1, 1, hour=10, minute=11))
        self.assertEqual(strptime_partial('10', '%H:%M'), datetime(1900, 1, 1, hour=10, minute=0))

    def test_no_format(self):
        self.assertEqual(strptime_partial('', ''), datetime(1900, 1, 1))

if __name__ == '__main__':
    unittest.main()
