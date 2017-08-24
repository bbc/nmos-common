import ctypes, os, time
from subprocess import check_output
from timestamp import Timestamp

__all__ = ["ptp_time"]

class timespec(ctypes.Structure):
    _fields_ = [
        ('tv_sec', ctypes.c_long),
        ('tv_nsec', ctypes.c_long)
    ]

def FD_TO_CLOCKID(fd):
    return ctypes.c_int((((~(fd)) << 3) | CLOCKFD))

def ptp_data():
    t = timespec()
    utc_time = time.time()
    _ts = Timestamp(int(utc_time), int((utc_time % 1) * 1e9))
    nanosec = _ts.to_nanosec()
    t.tv_sec = int(nanosec * 1e-9)
    t.tv_nsec = int(nanosec - (t.tv_sec * 1e9))
    return t

def ptp_time():
    t = ptp_data()
    return t.tv_sec + t.tv_nsec * 1e-9

def ptp_detail():
    t = ptp_data()
    return [t.tv_sec, t.tv_nsec]

if __name__ == "__main__":
    print ptp_time()
    print ptp_detail()
