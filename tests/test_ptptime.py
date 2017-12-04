import unittest
import time

from nmoscommon import ptptime


class PTPTest(unittest.TestCase):

    def test_ptp_detail(self):
        rv = ptptime.ptp_detail()
        self.assertEqual(2, len(rv))
        self.assertTrue(isinstance(rv[0], int))
        self.assertTrue(isinstance(rv[1], int))

    def test_fallback(self):
        """
        Fallback mechanism is close to PTP time.
        When the fallback mechanism for getting a current time is triggered,
        the returned time should be the same as the PTP time that *would*
        have been returned if the fallback wasn't triggered.
        """
        # In order to get this to work, we force ptp_detail to raise an exception
        # when accessing clock_gettime later.
        # The TAI/UTC time offset should already be included
        def throw(*args):
            raise Exception()

        ptp_sec, _ = ptptime.ptp_detail()
        ptptime.clock_gettime = throw
        fallback_sec, _ = ptptime.ptp_detail()
        self.assertEqual(ptp_sec, fallback_sec)
